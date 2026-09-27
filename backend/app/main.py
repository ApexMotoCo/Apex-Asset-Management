import os
import csv
import io
import secrets
from datetime import datetime, timedelta
from typing import List, Optional

from urllib.parse import quote

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import inspect, text, func
from sqlalchemy.orm import Session, joinedload
from pydantic import BaseModel, Field

from .database import engine, SessionLocal, Base
from .models import Asset, Category, AuditLog, User, AssetAssignment, MaintenanceRecord, AssetLifecycleEvent, AssetStockMovement, AssetIssue, Notification, SystemSetting, Supplier, PurchaseOrder, PurchaseOrderItem, AssetDocument, ComplianceRecord, ExpenseRecord, Budget
from .schemas import (
    AssetCreate, AssetUpdate, AssetResponse, CategoryCreate, CategoryResponse,
    AuditLogResponse, UserCreate, UserUpdate, UserAdminUpdate, UserResponse,
    UserPublicResponse, UserSummary, AssignmentResponse, AssignAssetRequest,
    LoginRequest, LoginResponse, AcceptInviteRequest, InviteResponse,
    SupplierCreate, SupplierUpdate, PurchaseOrderCreate, PurchaseOrderUpdate, AssetDocumentCreate, AssetDocumentUpdate, ComplianceRecordCreate, ComplianceRecordUpdate, ExpenseCreate, ExpenseUpdate, BudgetCreate, BudgetUpdate
)
from .auth import create_access_token, verify_token, verify_password, get_password_hash
from .config import AUTHORIZED_ADMINS, ACCESS_TOKEN_EXPIRE_MINUTES, SUPER_USER_EMAIL, USER_INACTIVITY_DAYS
from .audit import log_audit
from .email_service import send_invitation_email, APP_PUBLIC_URL

Base.metadata.create_all(bind=engine)

# ---------------------------------------------------------------------------
# Maintenance API models
# ---------------------------------------------------------------------------

class MaintenanceCreate(BaseModel):
    asset_id: int
    maintenance_type: str = "Service"
    status: str = "Scheduled"
    scheduled_date: Optional[datetime] = None
    completed_date: Optional[datetime] = None
    next_service_date: Optional[datetime] = None
    assigned_user_id: Optional[int] = None
    cost: float = Field(default=0.0, ge=0)
    notes: Optional[str] = None


class MaintenanceUpdate(BaseModel):
    asset_id: Optional[int] = None
    maintenance_type: Optional[str] = None
    status: Optional[str] = None
    scheduled_date: Optional[datetime] = None
    completed_date: Optional[datetime] = None
    next_service_date: Optional[datetime] = None
    assigned_user_id: Optional[int] = None
    cost: Optional[float] = Field(default=None, ge=0)
    notes: Optional[str] = None


class MaintenanceResponse(BaseModel):
    id: int
    asset_id: int
    asset_tag: Optional[str] = None
    asset_name: Optional[str] = None
    maintenance_type: str
    status: str
    scheduled_date: Optional[datetime] = None
    completed_date: Optional[datetime] = None
    next_service_date: Optional[datetime] = None
    assigned_user_id: Optional[int] = None
    assigned_user_name: Optional[str] = None
    assigned_user_email: Optional[str] = None
    cost: float
    notes: Optional[str] = None
    created_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    is_overdue: bool = False
    is_due_soon: bool = False


class MaintenanceSummaryResponse(BaseModel):
    overdue: int
    due_soon: int
    open_repairs: int
    completed: int
    total: int
    due_soon_days: int = 14


class DashboardSummaryResponse(BaseModel):
    total_assets: int
    total_asset_value: float
    assigned_assets: int
    hub_assets: int
    maintenance_assets: int
    open_repairs: int
    warranty_expiring: int
    warranty_expired: int
    replacements_due: int
    replacement_required: int
    unassigned_assets: int


class LifecycleUpdateRequest(BaseModel):
    status: str
    reason: Optional[str] = None


class StockActionRequest(BaseModel):
    user_id: Optional[int] = None
    location: str = "APEX HUB"
    notes: Optional[str] = None


class BulkAssignRequest(BaseModel):
    asset_ids: List[int]
    user_id: Optional[int] = None
    location: str = "APEX HUB"
    notes: Optional[str] = None


class IssueCreate(BaseModel):
    asset_id: int
    title: str
    description: str
    priority: str = "Normal"
    assigned_user_id: Optional[int] = None


class IssueUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    assigned_user_id: Optional[int] = None
    resolution: Optional[str] = None
    resolution_cost: Optional[float] = Field(default=None, ge=0)


class NotificationReadRequest(BaseModel):
    is_read: bool = True


ALLOWED_MAINTENANCE_TYPES = {"Service", "Repair", "Inspection", "Other"}
ALLOWED_MAINTENANCE_STATUSES = {"Scheduled", "In Progress", "Completed", "Cancelled"}

ALLOWED_LIFECYCLE_STATUSES = {"In Stock", "Assigned", "In Maintenance", "Returned", "Repaired", "Replacement Required", "Retired"}
ALLOWED_HEALTH_STATUSES = {"Healthy", "Due Maintenance", "Under Repair", "End of Life"}
ALLOWED_REPLACEMENT_PRIORITIES = {"Low", "Normal", "High", "Critical"}


def _warranty_status(asset: Asset, now: Optional[datetime] = None) -> str:
    now = now or datetime.utcnow()
    if not asset.warranty_expiry_date:
        return "Unknown"
    if asset.warranty_expiry_date < now:
        return "Expired"
    if asset.warranty_expiry_date <= now + timedelta(days=60):
        return "Expiring Soon"
    return "Active"


def _record_lifecycle(db: Session, asset: Asset, to_status: str, changed_by: str, reason: Optional[str] = None):
    if to_status not in ALLOWED_LIFECYCLE_STATUSES:
        raise HTTPException(status_code=400, detail=f"Invalid lifecycle status. Allowed: {', '.join(sorted(ALLOWED_LIFECYCLE_STATUSES))}")
    previous = asset.lifecycle_status or "In Stock"
    if previous == to_status:
        return False
    asset.lifecycle_status = to_status
    db.add(AssetLifecycleEvent(asset_id=asset.id, from_status=previous, to_status=to_status, reason=reason, changed_by=changed_by))
    return True


def _refresh_asset_health(asset: Asset):
    if asset.lifecycle_status == "Retired":
        asset.health_status = "End of Life"
    elif asset.lifecycle_status == "Replacement Required":
        asset.health_status = "End of Life"
    elif asset.lifecycle_status == "In Maintenance":
        asset.health_status = "Under Repair"
    elif asset.expected_replacement_date and asset.expected_replacement_date < datetime.utcnow():
        asset.health_status = "End of Life"
    elif asset.warranty_status == "Expired":
        asset.health_status = "Due Maintenance"
    else:
        asset.health_status = "Healthy"
    asset.warranty_status = _warranty_status(asset)


def _validate_maintenance_values(maintenance_type: str, status_value: str):
    if maintenance_type not in ALLOWED_MAINTENANCE_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid maintenance type. Allowed: {', '.join(sorted(ALLOWED_MAINTENANCE_TYPES))}",
        )
    if status_value not in ALLOWED_MAINTENANCE_STATUSES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid maintenance status. Allowed: {', '.join(sorted(ALLOWED_MAINTENANCE_STATUSES))}",
        )


def _maintenance_is_overdue(record: MaintenanceRecord, now: Optional[datetime] = None) -> bool:
    now = now or datetime.utcnow()
    return (
        record.status in {"Scheduled", "In Progress"}
        and record.scheduled_date is not None
        and record.scheduled_date < now
    )


def _maintenance_is_due_soon(
    record: MaintenanceRecord,
    days: int = 14,
    now: Optional[datetime] = None,
) -> bool:
    now = now or datetime.utcnow()
    if record.status not in {"Scheduled", "In Progress"} or record.scheduled_date is None:
        return False
    return now <= record.scheduled_date <= now + timedelta(days=days)


def _maintenance_response(record: MaintenanceRecord, due_soon_days: int = 14):
    return MaintenanceResponse(
        id=record.id,
        asset_id=record.asset_id,
        asset_tag=record.asset.asset_tag if record.asset else None,
        asset_name=record.asset.name if record.asset else None,
        maintenance_type=record.maintenance_type,
        status=record.status,
        scheduled_date=record.scheduled_date,
        completed_date=record.completed_date,
        next_service_date=record.next_service_date,
        assigned_user_id=record.assigned_user_id,
        assigned_user_name=record.assigned_user.full_name if record.assigned_user else None,
        assigned_user_email=record.assigned_user.email if record.assigned_user else None,
        cost=float(record.cost or 0),
        notes=record.notes,
        created_by=record.created_by,
        created_at=record.created_at,
        updated_at=record.updated_at,
        is_overdue=_maintenance_is_overdue(record),
        is_due_soon=_maintenance_is_due_soon(record, due_soon_days),
    )



def ensure_schema():
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    with engine.begin() as conn:
        if "assets" in tables:
            cols = {c["name"] for c in inspector.get_columns("assets")}
            additions = {
                "asset_tag": "VARCHAR",
                "qr_token": "VARCHAR",
                "assigned_user_id": "INTEGER",
                "lifecycle_status": "VARCHAR",
                "health_status": "VARCHAR",
                "warranty_provider": "VARCHAR",
                "warranty_start_date": "DATETIME",
                "warranty_expiry_date": "DATETIME",
                "warranty_reference": "VARCHAR",
                "warranty_notes": "TEXT",
                "warranty_status": "VARCHAR",
                "expected_replacement_date": "DATETIME",
                "replacement_priority": "VARCHAR",
                "replacement_reason": "VARCHAR",
                "estimated_replacement_cost": "FLOAT",
                "replacement_notes": "TEXT",
            }
            for name, sql_type in additions.items():
                if name not in cols:
                    conn.execute(text(f"ALTER TABLE assets ADD COLUMN {name} {sql_type}"))
        if "assets" in tables:
            conn.execute(text("UPDATE assets SET lifecycle_status='In Stock' WHERE lifecycle_status IS NULL OR TRIM(lifecycle_status)=''"))
            conn.execute(text("UPDATE assets SET health_status='Healthy' WHERE health_status IS NULL OR TRIM(health_status)=''"))
            conn.execute(text("UPDATE assets SET warranty_status='Unknown' WHERE warranty_status IS NULL OR TRIM(warranty_status)=''"))
            conn.execute(text("UPDATE assets SET replacement_priority='Normal' WHERE replacement_priority IS NULL OR TRIM(replacement_priority)=''"))
            conn.execute(text("UPDATE assets SET estimated_replacement_cost=0 WHERE estimated_replacement_cost IS NULL"))

        # New operational tables are created by SQLAlchemy below.

        if "users" in tables:
            cols = {c["name"] for c in inspector.get_columns("users")}
            additions = {
                "password_hash": "VARCHAR",
                "invite_token": "VARCHAR",
                "invite_expires_at": "DATETIME",
                "invited_at": "DATETIME",
            }
            for name, sql_type in additions.items():
                if name not in cols:
                    conn.execute(text(f"ALTER TABLE users ADD COLUMN {name} {sql_type}"))
        if "assets" in tables:
            rows = conn.execute(text("SELECT id, asset_tag, qr_token FROM assets")).fetchall()
            for row in rows:
                tag = row.asset_tag or f"APEX-{row.id:06d}"
                token = row.qr_token or secrets.token_urlsafe(18)
                conn.execute(
                    text("UPDATE assets SET asset_tag=:tag, qr_token=:token WHERE id=:id"),
                    {"tag": tag, "token": token, "id": row.id},
                )
        if "users" in tables:
            conn.execute(text("UPDATE users SET location='APEX HUB' WHERE location IS NULL OR TRIM(location)=''"))

ensure_schema()
Base.metadata.create_all(bind=engine)

# Seed configurable system defaults without overwriting administrator changes.
def _seed_system_settings():
    db = SessionLocal()
    try:
        defaults = {
            "organisation_name": "APEX",
            "default_location": "APEX HUB",
            "user_inactivity_days": "30",
            "maintenance_due_soon_days": "14",
        }
        for key, value in defaults.items():
            if not db.query(SystemSetting).filter(SystemSetting.key == key).first():
                db.add(SystemSetting(key=key, value=value))
        db.commit()
    finally:
        db.close()

_seed_system_settings()

app = FastAPI(
    title="APEX Asset Management System",
    description="Enterprise-grade asset tracking and management platform",
    version="3.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user_record(current_user: str, db: Session) -> User:
    user = db.query(User).filter(User.email == current_user).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=403, detail="User account is inactive or unavailable")
    return user

def require_admin(current_user: str, db: Session) -> User:
    user = get_current_user_record(current_user, db)
    if user.role not in ("admin", "super_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    return user

def require_super_admin(current_user: str, db: Session) -> User:
    user = get_current_user_record(current_user, db)
    if current_user != SUPER_USER_EMAIL and user.role != "super_admin":
        raise HTTPException(status_code=403, detail="Super admin access required")
    return user

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.post("/login", response_model=LoginResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    email = str(request.email).strip().lower()
    user = db.query(User).filter(User.email == email).first()

    # Preserve the existing admin login for the configured bootstrap administrators.
    if email in AUTHORIZED_ADMINS and not request.password:
        if not user:
            user = User(
                email=email,
                full_name=email.split("@")[0].replace(".", " ").title(),
                role="super_admin" if email == SUPER_USER_EMAIL else "admin",
                membership_tier="platinum",
                is_verified=True,
                is_active=True,
                location="APEX HUB",
            )
            db.add(user)
            db.commit()
            db.refresh(user)
    else:
        if not user or not user.password_hash:
            raise HTTPException(status_code=401, detail="Invalid email or password")
        if not user.is_active:
            raise HTTPException(status_code=403, detail="Your account has been deactivated")
        inactivity_days = USER_INACTIVITY_DAYS
        setting = db.query(SystemSetting).filter(SystemSetting.key == "user_inactivity_days").first()
        if setting and setting.value:
            try:
                inactivity_days = max(1, int(setting.value))
            except ValueError:
                pass
        if user.role == "member" and user.last_login and user.last_login < datetime.utcnow() - timedelta(days=inactivity_days):
            user.is_active = False
            db.commit()
            log_audit(db, email, "UPDATE", "USER", user.full_name, user.id, f"Account automatically deactivated after {inactivity_days} days of inactivity")
            raise HTTPException(status_code=403, detail=f"Your account was deactivated after {inactivity_days} days of inactivity. Contact an administrator.")
        if not request.password or not verify_password(request.password, user.password_hash):
            raise HTTPException(status_code=401, detail="Invalid email or password")

    user.last_login = datetime.utcnow()
    db.commit()
    log_audit(db, email, "LOGIN", "SYSTEM", "User Login", details="User logged in successfully")

    token = create_access_token(
        {"sub": email, "role": user.role},
        timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return {"access_token": token, "token_type": "bearer", "email": email, "role": user.role}

@app.post("/invitations/accept")
def accept_invitation(request: AcceptInviteRequest, db: Session = Depends(get_db)):
    if len(request.password) < 10:
        raise HTTPException(status_code=400, detail="Password must be at least 10 characters long")
    user = db.query(User).filter(User.invite_token == request.token).first()
    if not user or not user.invite_expires_at or user.invite_expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Invitation is invalid or has expired")
    user.password_hash = get_password_hash(request.password)
    user.is_verified = True
    user.is_active = True
    user.invite_token = None
    user.invite_expires_at = None
    user.updated_at = datetime.utcnow()
    db.commit()
    log_audit(db, user.email, "UPDATE", "USER", user.full_name, user.id, "Invitation accepted and account activated")
    return {"message": "Account activated successfully. You can now sign in."}


# ---------------------------------------------------------------------------
# Maintenance
# ---------------------------------------------------------------------------

@app.get("/maintenance/summary", response_model=MaintenanceSummaryResponse)
def maintenance_summary(
    due_soon_days: int = 14,
    db: Session = Depends(get_db),
    current_user: str = Depends(verify_token),
):
    get_current_user_record(current_user, db)

    if due_soon_days < 1 or due_soon_days > 365:
        raise HTTPException(status_code=400, detail="due_soon_days must be between 1 and 365")

    records = db.query(MaintenanceRecord).all()
    now = datetime.utcnow()

    overdue = sum(1 for record in records if _maintenance_is_overdue(record, now))
    due_soon = sum(1 for record in records if _maintenance_is_due_soon(record, due_soon_days, now))
    open_repairs = sum(
        1
        for record in records
        if record.maintenance_type == "Repair"
        and record.status in {"Scheduled", "In Progress"}
    )
    completed = sum(1 for record in records if record.status == "Completed")

    return MaintenanceSummaryResponse(
        overdue=overdue,
        due_soon=due_soon,
        open_repairs=open_repairs,
        completed=completed,
        total=len(records),
        due_soon_days=due_soon_days,
    )


@app.get("/maintenance", response_model=List[MaintenanceResponse])
def list_maintenance(
    status_filter: Optional[str] = None,
    maintenance_type: Optional[str] = None,
    asset_id: Optional[int] = None,
    assigned_user_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: str = Depends(verify_token),
):
    get_current_user_record(current_user, db)

    query = (
        db.query(MaintenanceRecord)
        .options(
            joinedload(MaintenanceRecord.asset),
            joinedload(MaintenanceRecord.assigned_user),
        )
    )

    if status_filter:
        query = query.filter(MaintenanceRecord.status == status_filter)

    if maintenance_type:
        query = query.filter(MaintenanceRecord.maintenance_type == maintenance_type)

    if asset_id is not None:
        query = query.filter(MaintenanceRecord.asset_id == asset_id)

    if assigned_user_id is not None:
        query = query.filter(MaintenanceRecord.assigned_user_id == assigned_user_id)

    records = query.order_by(
        MaintenanceRecord.scheduled_date.is_(None),
        MaintenanceRecord.scheduled_date.asc(),
        MaintenanceRecord.created_at.desc(),
    ).all()

    return [_maintenance_response(record) for record in records]


@app.get("/maintenance/{maintenance_id}", response_model=MaintenanceResponse)
def get_maintenance(
    maintenance_id: int,
    db: Session = Depends(get_db),
    current_user: str = Depends(verify_token),
):
    get_current_user_record(current_user, db)

    record = (
        db.query(MaintenanceRecord)
        .options(
            joinedload(MaintenanceRecord.asset),
            joinedload(MaintenanceRecord.assigned_user),
        )
        .filter(MaintenanceRecord.id == maintenance_id)
        .first()
    )

    if not record:
        raise HTTPException(status_code=404, detail="Maintenance record not found")

    return _maintenance_response(record)


@app.get("/assets/{asset_id}/maintenance", response_model=List[MaintenanceResponse])
def asset_maintenance_history(
    asset_id: int,
    db: Session = Depends(get_db),
    current_user: str = Depends(verify_token),
):
    get_current_user_record(current_user, db)

    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    records = (
        db.query(MaintenanceRecord)
        .options(
            joinedload(MaintenanceRecord.asset),
            joinedload(MaintenanceRecord.assigned_user),
        )
        .filter(MaintenanceRecord.asset_id == asset_id)
        .order_by(
            MaintenanceRecord.scheduled_date.is_(None),
            MaintenanceRecord.scheduled_date.desc(),
            MaintenanceRecord.created_at.desc(),
        )
        .all()
    )

    return [_maintenance_response(record) for record in records]


@app.post("/maintenance", response_model=MaintenanceResponse)
def create_maintenance(
    maintenance: MaintenanceCreate,
    db: Session = Depends(get_db),
    current_user: str = Depends(verify_token),
):
    require_admin(current_user, db)

    _validate_maintenance_values(maintenance.maintenance_type, maintenance.status)

    asset = db.query(Asset).filter(Asset.id == maintenance.asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    assigned_user = None
    if maintenance.assigned_user_id is not None:
        assigned_user = (
            db.query(User)
            .filter(User.id == maintenance.assigned_user_id, User.is_active == True)
            .first()
        )
        if not assigned_user:
            raise HTTPException(status_code=404, detail="Assigned employee not found or inactive")

    completed_date = maintenance.completed_date
    if maintenance.status == "Completed" and completed_date is None:
        completed_date = datetime.utcnow()

    record = MaintenanceRecord(
        asset_id=maintenance.asset_id,
        maintenance_type=maintenance.maintenance_type,
        status=maintenance.status,
        scheduled_date=maintenance.scheduled_date,
        completed_date=completed_date,
        next_service_date=maintenance.next_service_date,
        assigned_user_id=maintenance.assigned_user_id,
        cost=maintenance.cost,
        notes=maintenance.notes,
        created_by=current_user,
    )

    db.add(record)
    if maintenance.status == "In Progress" and asset.lifecycle_status != "Retired":
        _record_lifecycle(db, asset, "In Maintenance", current_user, "Maintenance started")
    elif maintenance.status == "Completed" and asset.lifecycle_status == "In Maintenance":
        _record_lifecycle(db, asset, "Repaired" if maintenance.maintenance_type == "Repair" else "Returned", current_user, "Maintenance completed")
    _refresh_asset_health(asset)
    db.commit()
    db.refresh(record)

    log_audit(
        db,
        current_user,
        "CREATE",
        "MAINTENANCE",
        asset.name,
        record.id,
        f"Created {maintenance.maintenance_type} maintenance record for {asset.asset_tag} with status {maintenance.status}",
    )

    record = (
        db.query(MaintenanceRecord)
        .options(
            joinedload(MaintenanceRecord.asset),
            joinedload(MaintenanceRecord.assigned_user),
        )
        .filter(MaintenanceRecord.id == record.id)
        .first()
    )

    return _maintenance_response(record)


@app.put("/maintenance/{maintenance_id}", response_model=MaintenanceResponse)
def update_maintenance(
    maintenance_id: int,
    maintenance: MaintenanceUpdate,
    db: Session = Depends(get_db),
    current_user: str = Depends(verify_token),
):
    require_admin(current_user, db)

    record = db.query(MaintenanceRecord).filter(MaintenanceRecord.id == maintenance_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Maintenance record not found")

    update_data = maintenance.model_dump(exclude_unset=True)

    new_type = update_data.get("maintenance_type", record.maintenance_type)
    new_status = update_data.get("status", record.status)
    _validate_maintenance_values(new_type, new_status)

    if "asset_id" in update_data:
        asset = db.query(Asset).filter(Asset.id == update_data["asset_id"]).first()
        if not asset:
            raise HTTPException(status_code=404, detail="Asset not found")

    if "assigned_user_id" in update_data and update_data["assigned_user_id"] is not None:
        assigned_user = (
            db.query(User)
            .filter(User.id == update_data["assigned_user_id"], User.is_active == True)
            .first()
        )
        if not assigned_user:
            raise HTTPException(status_code=404, detail="Assigned employee not found or inactive")

    for key, value in update_data.items():
        setattr(record, key, value)

    if record.status == "Completed" and record.completed_date is None:
        record.completed_date = datetime.utcnow()

    if record.status != "Completed" and "completed_date" not in update_data:
        record.completed_date = None

    record.updated_at = datetime.utcnow()
    asset = record.asset
    if asset and record.status == "In Progress" and asset.lifecycle_status != "Retired":
        _record_lifecycle(db, asset, "In Maintenance", current_user, "Maintenance started")
    elif asset and record.status == "Completed" and asset.lifecycle_status == "In Maintenance":
        _record_lifecycle(db, asset, "Repaired" if record.maintenance_type == "Repair" else "Returned", current_user, "Maintenance completed")
    if asset:
        _refresh_asset_health(asset)
    db.commit()
    db.refresh(record)

    log_audit(
        db,
        current_user,
        "UPDATE",
        "MAINTENANCE",
        record.asset.name if record.asset else f"Maintenance #{record.id}",
        record.id,
        f"Updated maintenance record fields: {', '.join(update_data.keys())}",
    )

    record = (
        db.query(MaintenanceRecord)
        .options(
            joinedload(MaintenanceRecord.asset),
            joinedload(MaintenanceRecord.assigned_user),
        )
        .filter(MaintenanceRecord.id == maintenance_id)
        .first()
    )

    return _maintenance_response(record)


@app.delete("/maintenance/{maintenance_id}")
def delete_maintenance(
    maintenance_id: int,
    db: Session = Depends(get_db),
    current_user: str = Depends(verify_token),
):
    require_admin(current_user, db)

    record = db.query(MaintenanceRecord).filter(MaintenanceRecord.id == maintenance_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Maintenance record not found")

    asset_name = record.asset.name if record.asset else f"Maintenance #{record.id}"
    asset_tag = record.asset.asset_tag if record.asset else "Unknown"

    db.delete(record)
    db.commit()

    log_audit(
        db,
        current_user,
        "DELETE",
        "MAINTENANCE",
        asset_name,
        maintenance_id,
        f"Deleted maintenance record for {asset_tag}",
    )

    return {"message": "Maintenance record deleted successfully"}


@app.get("/dashboard/summary", response_model=DashboardSummaryResponse)
def dashboard_summary(db: Session = Depends(get_db), current_user: str = Depends(verify_token)):
    get_current_user_record(current_user, db)
    assets = db.query(Asset).all()
    now = datetime.utcnow()
    for asset in assets:
        _refresh_asset_health(asset)
    db.commit()
    return {
        "total_assets": len(assets),
        "total_asset_value": sum(float(a.value or 0) for a in assets),
        "assigned_assets": sum(1 for a in assets if a.assigned_user_id is not None),
        "hub_assets": sum(1 for a in assets if (a.location or "APEX HUB").strip().upper() == "APEX HUB"),
        "maintenance_assets": sum(1 for a in assets if a.lifecycle_status == "In Maintenance"),
        "open_repairs": db.query(MaintenanceRecord).filter(MaintenanceRecord.maintenance_type == "Repair", MaintenanceRecord.status.in_(["Scheduled", "In Progress"])).count(),
        "warranty_expiring": sum(1 for a in assets if a.warranty_expiry_date and now <= a.warranty_expiry_date <= now + timedelta(days=60)),
        "warranty_expired": sum(1 for a in assets if a.warranty_expiry_date and a.warranty_expiry_date < now),
        "replacements_due": sum(1 for a in assets if a.expected_replacement_date and a.expected_replacement_date <= now),
        "replacement_required": sum(1 for a in assets if a.lifecycle_status == "Replacement Required"),
        "unassigned_assets": sum(1 for a in assets if a.assigned_user_id is None),
    }


@app.get("/assets/{asset_id}/lifecycle")
def asset_lifecycle_history(asset_id: int, db: Session = Depends(get_db), current_user: str = Depends(verify_token)):
    get_current_user_record(current_user, db)
    if not db.query(Asset).filter(Asset.id == asset_id).first():
        raise HTTPException(status_code=404, detail="Asset not found")
    return db.query(AssetLifecycleEvent).filter(AssetLifecycleEvent.asset_id == asset_id).order_by(AssetLifecycleEvent.created_at.desc()).all()


@app.post("/assets/{asset_id}/lifecycle")
def update_asset_lifecycle(asset_id: int, request: LifecycleUpdateRequest, db: Session = Depends(get_db), current_user: str = Depends(verify_token)):
    require_admin(current_user, db)
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    _record_lifecycle(db, asset, request.status, current_user, request.reason)
    _refresh_asset_health(asset)
    asset.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(asset)
    log_audit(db, current_user, "UPDATE", "ASSET_LIFECYCLE", asset.name, asset.id, f"Lifecycle changed to {asset.lifecycle_status}" + (f": {request.reason}" if request.reason else ""))
    return asset


def _csv_response(rows, filename: str):
    import csv
    from io import StringIO
    from fastapi.responses import StreamingResponse
    output = StringIO()
    writer = csv.writer(output)
    if rows:
        writer.writerow(list(rows[0].keys()))
        for row in rows:
            writer.writerow(list(row.values()))
    response = StreamingResponse(iter([output.getvalue()]), media_type="text/csv")
    response.headers["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


@app.get("/reports/assets.csv")
def report_assets(db: Session = Depends(get_db), current_user: str = Depends(verify_token)):
    require_admin(current_user, db)
    assets = db.query(Asset).order_by(Asset.asset_tag).all()
    rows = []
    for a in assets:
        rows.append({"Asset ID": a.asset_tag, "Name": a.name, "Serial": a.serial_number, "Category": a.category.name if a.category else "", "Location": a.location, "Assigned To": a.assigned_user.full_name if a.assigned_user else "", "Value": float(a.value or 0), "Lifecycle": a.lifecycle_status, "Health": a.health_status, "Warranty": _warranty_status(a), "Warranty Expiry": a.warranty_expiry_date or "", "Replacement Date": a.expected_replacement_date or "", "Replacement Priority": a.replacement_priority})
    return _csv_response(rows, "apex-assets.csv")


@app.get("/reports/maintenance.csv")
def report_maintenance(db: Session = Depends(get_db), current_user: str = Depends(verify_token)):
    require_admin(current_user, db)
    records = db.query(MaintenanceRecord).options(joinedload(MaintenanceRecord.asset), joinedload(MaintenanceRecord.assigned_user)).order_by(MaintenanceRecord.created_at.desc()).all()
    rows = [{"Asset ID": r.asset.asset_tag if r.asset else "", "Asset": r.asset.name if r.asset else "", "Type": r.maintenance_type, "Status": r.status, "Scheduled": r.scheduled_date or "", "Completed": r.completed_date or "", "Next Service": r.next_service_date or "", "Technician": r.assigned_user.full_name if r.assigned_user else "", "Cost": float(r.cost or 0), "Notes": r.notes or ""} for r in records]
    return _csv_response(rows, "apex-maintenance.csv")


@app.get("/reports/warranty.csv")
def report_warranty(db: Session = Depends(get_db), current_user: str = Depends(verify_token)):
    require_admin(current_user, db)
    assets = db.query(Asset).filter(Asset.warranty_expiry_date.isnot(None)).order_by(Asset.warranty_expiry_date).all()
    rows = [{"Asset ID": a.asset_tag, "Asset": a.name, "Provider": a.warranty_provider or "", "Reference": a.warranty_reference or "", "Start": a.warranty_start_date or "", "Expiry": a.warranty_expiry_date or "", "Status": _warranty_status(a), "Notes": a.warranty_notes or ""} for a in assets]
    return _csv_response(rows, "apex-warranty.csv")


@app.get("/reports/replacements.csv")
def report_replacements(db: Session = Depends(get_db), current_user: str = Depends(verify_token)):
    require_admin(current_user, db)
    assets = db.query(Asset).filter((Asset.expected_replacement_date.isnot(None)) | (Asset.lifecycle_status == "Replacement Required")).order_by(Asset.expected_replacement_date).all()
    rows = [{"Asset ID": a.asset_tag, "Asset": a.name, "Replacement Date": a.expected_replacement_date or "", "Priority": a.replacement_priority, "Reason": a.replacement_reason or "", "Estimated Cost": float(a.estimated_replacement_cost or 0), "Lifecycle": a.lifecycle_status, "Notes": a.replacement_notes or ""} for a in assets]
    return _csv_response(rows, "apex-replacements.csv")


@app.get("/reports/assignments.csv")
def report_assignments(db: Session = Depends(get_db), current_user: str = Depends(verify_token)):
    require_admin(current_user, db)
    records = db.query(AssetAssignment).options(joinedload(AssetAssignment.asset), joinedload(AssetAssignment.user)).order_by(AssetAssignment.assigned_at.desc()).all()
    rows = [{"Asset ID": r.asset.asset_tag if r.asset else "", "Asset": r.asset.name if r.asset else "", "Action": r.action, "Employee": r.user.full_name if r.user else "Unassigned", "Location": r.location, "Date": r.assigned_at, "Assigned By": r.assigned_by or "", "Notes": r.notes or ""} for r in records]
    return _csv_response(rows, "apex-assignments.csv")


# ---------------------------------------------------------------------------
# Batch 3 - Operations, stock, issues and notifications
# ---------------------------------------------------------------------------

@app.get("/stock/summary")
def stock_summary(db: Session = Depends(get_db), current_user: str = Depends(verify_token)):
    get_current_user_record(current_user, db)
    assets = db.query(Asset).all()
    return {
        "total": len(assets),
        "in_stock": sum(1 for a in assets if a.lifecycle_status == "In Stock"),
        "assigned": sum(1 for a in assets if a.assigned_user_id is not None or a.lifecycle_status == "Assigned"),
        "in_maintenance": sum(1 for a in assets if a.lifecycle_status == "In Maintenance"),
        "returned": sum(1 for a in assets if a.lifecycle_status == "Returned"),
        "repaired": sum(1 for a in assets if a.lifecycle_status == "Repaired"),
        "replacement_required": sum(1 for a in assets if a.lifecycle_status == "Replacement Required"),
        "retired": sum(1 for a in assets if a.lifecycle_status == "Retired"),
        "hub": sum(1 for a in assets if (a.location or "APEX HUB") == "APEX HUB"),
    }

@app.get("/stock/movements")
def stock_movements(limit: int = 200, db: Session = Depends(get_db), current_user: str = Depends(verify_token)):
    get_current_user_record(current_user, db)
    rows = db.query(AssetStockMovement).order_by(AssetStockMovement.created_at.desc()).limit(min(limit, 500)).all()
    return [{
        "id": r.id, "asset_id": r.asset_id, "asset_tag": r.asset.asset_tag if r.asset else None,
        "asset_name": r.asset.name if r.asset else None, "action": r.action,
        "from_location": r.from_location, "to_location": r.to_location,
        "from_user": r.from_user.full_name if r.from_user else None,
        "to_user": r.to_user.full_name if r.to_user else None,
        "performed_by": r.performed_by, "notes": r.notes, "created_at": r.created_at
    } for r in rows]

@app.post("/assets/{asset_id}/check-out", response_model=AssetResponse)
def check_out_asset(asset_id: int, request: StockActionRequest, db: Session = Depends(get_db), current_user: str = Depends(verify_token)):
    require_admin(current_user, db)
    if request.user_id is None:
        raise HTTPException(status_code=400, detail="A user is required to check an asset out")
    user = db.query(User).filter(User.id == request.user_id, User.is_active == True).first()
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset or not user:
        raise HTTPException(status_code=404, detail="Asset or user not found")
    old_location, old_user = asset.location or "APEX HUB", asset.assigned_user_id
    asset.assigned_user_id = user.id
    asset.location = request.location.strip() or "APEX HUB"
    _record_lifecycle(db, asset, "Assigned", current_user, "Asset checked out")
    db.add(AssetStockMovement(asset_id=asset.id, action="CHECK_OUT", from_location=old_location, to_location=asset.location, from_user_id=old_user, to_user_id=user.id, performed_by=current_user, notes=request.notes))
    db.commit(); db.refresh(asset)
    log_audit(db, current_user, "UPDATE", "ASSET_STOCK", asset.name, asset.id, f"Checked out {asset.asset_tag} to {user.full_name}")
    return db.query(Asset).options(joinedload(Asset.category), joinedload(Asset.assigned_user)).filter(Asset.id == asset.id).first()

@app.post("/assets/{asset_id}/check-in", response_model=AssetResponse)
def check_in_asset(asset_id: int, request: StockActionRequest, db: Session = Depends(get_db), current_user: str = Depends(verify_token)):
    require_admin(current_user, db)
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    old_location, old_user = asset.location or "APEX HUB", asset.assigned_user_id
    asset.assigned_user_id = None
    asset.location = request.location.strip() or "APEX HUB"
    _record_lifecycle(db, asset, "Returned", current_user, "Asset checked in")
    db.add(AssetStockMovement(asset_id=asset.id, action="CHECK_IN", from_location=old_location, to_location=asset.location, from_user_id=old_user, to_user_id=None, performed_by=current_user, notes=request.notes))
    db.commit(); db.refresh(asset)
    log_audit(db, current_user, "UPDATE", "ASSET_STOCK", asset.name, asset.id, f"Checked in {asset.asset_tag}")
    return db.query(Asset).options(joinedload(Asset.category), joinedload(Asset.assigned_user)).filter(Asset.id == asset.id).first()

@app.post("/assets/bulk-assign")
def bulk_assign_assets(request: BulkAssignRequest, db: Session = Depends(get_db), current_user: str = Depends(verify_token)):
    require_admin(current_user, db)
    if not request.asset_ids:
        raise HTTPException(status_code=400, detail="No assets supplied")
    user = None
    if request.user_id is not None:
        user = db.query(User).filter(User.id == request.user_id, User.is_active == True).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found or inactive")
    location = request.location.strip() or "APEX HUB"
    changed = 0
    for asset in db.query(Asset).filter(Asset.id.in_(request.asset_ids)).all():
        old_location, old_user = asset.location or "APEX HUB", asset.assigned_user_id
        asset.assigned_user_id = user.id if user else None
        asset.location = location
        _record_lifecycle(db, asset, "Assigned" if user else "In Stock", current_user, "Bulk stock movement")
        db.add(AssetStockMovement(asset_id=asset.id, action="BULK_ASSIGN" if user else "BULK_RETURN", from_location=old_location, to_location=location, from_user_id=old_user, to_user_id=user.id if user else None, performed_by=current_user, notes=request.notes))
        changed += 1
    db.commit()
    log_audit(db, current_user, "UPDATE", "ASSET_STOCK", "Bulk stock movement", None, f"Updated {changed} assets")
    return {"updated": changed}

@app.get("/issues")
def list_issues(status_filter: Optional[str] = None, priority: Optional[str] = None, asset_id: Optional[int] = None, db: Session = Depends(get_db), current_user: str = Depends(verify_token)):
    get_current_user_record(current_user, db)
    q = db.query(AssetIssue).options(joinedload(AssetIssue.asset), joinedload(AssetIssue.reported_by), joinedload(AssetIssue.assigned_user))
    if status_filter: q = q.filter(AssetIssue.status == status_filter)
    if priority: q = q.filter(AssetIssue.priority == priority)
    if asset_id is not None: q = q.filter(AssetIssue.asset_id == asset_id)
    rows = q.order_by(AssetIssue.created_at.desc()).all()
    return [{
        "id": r.id, "asset_id": r.asset_id, "asset_tag": r.asset.asset_tag if r.asset else None, "asset_name": r.asset.name if r.asset else None,
        "reported_by_user_id": r.reported_by_user_id, "reported_by": r.reported_by.full_name if r.reported_by else None,
        "assigned_user_id": r.assigned_user_id, "assigned_user": r.assigned_user.full_name if r.assigned_user else None,
        "title": r.title, "description": r.description, "priority": r.priority, "status": r.status,
        "resolution": r.resolution, "resolution_cost": r.resolution_cost, "created_at": r.created_at, "updated_at": r.updated_at, "resolved_at": r.resolved_at
    } for r in rows]

@app.post("/issues")
def create_issue(request: IssueCreate, db: Session = Depends(get_db), current_user: str = Depends(verify_token)):
    user = get_current_user_record(current_user, db)
    asset = db.query(Asset).filter(Asset.id == request.asset_id).first()
    if not asset: raise HTTPException(status_code=404, detail="Asset not found")
    if request.priority not in {"Low", "Normal", "High", "Critical"}: raise HTTPException(status_code=400, detail="Invalid priority")
    issue = AssetIssue(asset_id=asset.id, reported_by_user_id=user.id, assigned_user_id=request.assigned_user_id, title=request.title.strip(), description=request.description.strip(), priority=request.priority)
    db.add(issue)
    if asset.lifecycle_status != "Retired":
        _record_lifecycle(db, asset, "Replacement Required" if request.priority == "Critical" else "In Maintenance", current_user, "Fault reported")
    db.commit(); db.refresh(issue)
    log_audit(db, current_user, "CREATE", "ASSET_ISSUE", issue.title, issue.id, f"Fault reported for {asset.asset_tag}")
    return {"id": issue.id, "message": "Issue reported successfully"}

@app.put("/issues/{issue_id}")
def update_issue(issue_id: int, request: IssueUpdate, db: Session = Depends(get_db), current_user: str = Depends(verify_token)):
    require_admin(current_user, db)
    issue = db.query(AssetIssue).filter(AssetIssue.id == issue_id).first()
    if not issue: raise HTTPException(status_code=404, detail="Issue not found")
    data = request.model_dump(exclude_unset=True)
    if data.get("priority") and data["priority"] not in {"Low", "Normal", "High", "Critical"}: raise HTTPException(status_code=400, detail="Invalid priority")
    if data.get("status") and data["status"] not in {"Reported", "Investigating", "Repair Scheduled", "In Repair", "Fixed", "Returned", "Cancelled"}: raise HTTPException(status_code=400, detail="Invalid issue status")
    for key, value in data.items(): setattr(issue, key, value)
    if issue.status in {"Fixed", "Returned", "Cancelled"} and not issue.resolved_at: issue.resolved_at = datetime.utcnow()
    if issue.status == "In Repair" and issue.asset.lifecycle_status != "Retired": _record_lifecycle(db, issue.asset, "In Maintenance", current_user, "Issue moved to repair")
    if issue.status == "Returned" and issue.asset.lifecycle_status != "Retired": _record_lifecycle(db, issue.asset, "Returned", current_user, "Issue resolved and asset returned")
    issue.updated_at = datetime.utcnow()
    db.commit(); db.refresh(issue)
    log_audit(db, current_user, "UPDATE", "ASSET_ISSUE", issue.title, issue.id, f"Issue updated: {', '.join(data.keys())}")
    return {"id": issue.id, "message": "Issue updated successfully"}

def _setting_int(db, key, default):
    row = db.query(SystemSetting).filter(SystemSetting.key == key).first()
    try:
        return max(1, int(row.value)) if row and row.value else default
    except (ValueError, TypeError):
        return default


def _notification_exists(db, user_id, notification_type, resource_type, resource_id):
    q = db.query(Notification).filter(
        Notification.notification_type == notification_type,
        Notification.resource_type == resource_type,
        Notification.resource_id == resource_id,
        Notification.is_read == False,
    )
    if user_id is None:
        q = q.filter(Notification.user_id.is_(None))
    else:
        q = q.filter(Notification.user_id == user_id)
    return q.first() is not None


def run_automation(db: Session):
    now = datetime.utcnow()
    due_days = _setting_int(db, "maintenance_due_soon_days", 14)
    inactivity_days = _setting_int(db, "user_inactivity_days", 30)
    created = 0
    admins = db.query(User).filter(User.role.in_(["admin", "super_admin"]), User.is_active == True).all()

    def add(user_id, title, message, kind, rtype, rid):
        nonlocal created
        if _notification_exists(db, user_id, kind, rtype, rid): return
        db.add(Notification(user_id=user_id, title=title, message=message, notification_type=kind, resource_type=rtype, resource_id=rid))
        created += 1

    for asset in db.query(Asset).all():
        if asset.warranty_expiry_date:
            days=(asset.warranty_expiry_date-now).days
            if days < 0: title=f"Warranty expired: {asset.asset_tag}"; msg=f"{asset.name} warranty expired on {asset.warranty_expiry_date:%d %b %Y}."; kind="Critical"
            elif days <= 60: title=f"Warranty expiring: {asset.asset_tag}"; msg=f"{asset.name} warranty expires in {max(days,0)} days."; kind="Warning"
            else: title=msg=kind=None
            if kind:
                for a in admins: add(a.id,title,msg,kind,"ASSET_WARRANTY",asset.id)
                if asset.assigned_user_id: add(asset.assigned_user_id,title,msg,kind,"ASSET_WARRANTY",asset.id)
        if asset.expected_replacement_date:
            days=(asset.expected_replacement_date-now).days
            if days <= 30 or asset.lifecycle_status == "Replacement Required":
                kind="Critical" if asset.lifecycle_status == "Replacement Required" or days < 0 else "Warning"
                title=f"Replacement attention: {asset.asset_tag}"
                msg=f"{asset.name} is due for replacement" + (f" on {asset.expected_replacement_date:%d %b %Y}." if asset.expected_replacement_date else ".")
                for a in admins: add(a.id,title,msg,kind,"ASSET_REPLACEMENT",asset.id)
        if asset.assigned_user_id and asset.health_status in {"Faulty","Critical"}:
            add(asset.assigned_user_id,f"Asset health alert: {asset.asset_tag}",f"{asset.name} is marked {asset.health_status}.","Critical","ASSET_HEALTH",asset.id)

    for m in db.query(MaintenanceRecord).filter(MaintenanceRecord.status.in_(["Scheduled","In Progress"])).all():
        if m.scheduled_date and m.scheduled_date <= now + timedelta(days=due_days):
            kind="Critical" if m.scheduled_date < now else "Warning"
            title=f"Maintenance due: {m.asset.asset_tag if m.asset else m.asset_id}"
            msg=f"{m.maintenance_type} is due" + (f" on {m.scheduled_date:%d %b %Y}." if m.scheduled_date else ".")
            targets=admins + ([m.assigned_user] if m.assigned_user else [])
            seen=set()
            for u in targets:
                if u and u.id not in seen: add(u.id,title,msg,kind,"MAINTENANCE",m.id); seen.add(u.id)

    for issue in db.query(AssetIssue).filter(AssetIssue.status.notin_(["Fixed","Returned","Cancelled"])).all():
        if issue.priority in {"High","Critical"}:
            title=f"{issue.priority} issue: {issue.asset.asset_tag if issue.asset else issue.asset_id}"
            msg=issue.title
            for a in admins: add(a.id,title,msg,"Critical" if issue.priority=="Critical" else "Warning","ASSET_ISSUE",issue.id)
            if issue.assigned_user_id: add(issue.assigned_user_id,title,msg,"Warning","ASSET_ISSUE",issue.id)

    cutoff=now-timedelta(days=inactivity_days)
    for user in db.query(User).filter(User.is_active==True,User.role=="member",User.last_login.isnot(None),User.last_login < cutoff).all():
        add(user.id,"Account inactivity warning",f"Your account has not been used for {inactivity_days} days and may be deactivated.","Warning","USER_INACTIVITY",user.id)
        for a in admins: add(a.id,"Inactive employee approaching cutoff",f"{user.full_name} has not logged in for {inactivity_days} days.","Warning","USER_INACTIVITY",user.id)
    if created: db.commit()
    return created


@app.get("/notifications")
def notifications(db: Session = Depends(get_db), current_user: str = Depends(verify_token)):
    user=get_current_user_record(current_user, db)
    run_automation(db)
    q=db.query(Notification).filter((Notification.user_id == user.id) | (Notification.user_id.is_(None)))
    rows=q.order_by(Notification.is_read.asc(),Notification.created_at.desc()).limit(200).all()
    return [{"id":n.id,"title":n.title,"message":n.message,"notification_type":n.notification_type,"resource_type":n.resource_type,"resource_id":n.resource_id,"is_read":n.is_read,"created_at":n.created_at} for n in rows]


@app.post("/notifications/{notification_id}/read")
def mark_notification_read(notification_id:int,db:Session=Depends(get_db),current_user:str=Depends(verify_token)):
    user=get_current_user_record(current_user,db); n=db.query(Notification).filter(Notification.id==notification_id).first()
    if not n or (n.user_id is not None and n.user_id != user.id): raise HTTPException(status_code=404,detail="Notification not found")
    n.is_read=True; db.commit(); return {"message":"Notification marked as read"}


@app.post("/notifications/read-all")
def mark_all_notifications_read(db:Session=Depends(get_db),current_user:str=Depends(verify_token)):
    user=get_current_user_record(current_user,db)
    db.query(Notification).filter((Notification.user_id == user.id) | (Notification.user_id.is_(None)), Notification.is_read == False).update({Notification.is_read:True},synchronize_session=False)
    db.commit(); return {"message":"Notifications marked as read"}


@app.post("/admin/automation/run")
def admin_run_automation(db:Session=Depends(get_db),current_user:str=Depends(verify_token)):
    require_admin(current_user,db); created=run_automation(db); log_audit(db,current_user,"RUN","AUTOMATION","Daily housekeeping",None,f"Created {created} notification(s)"); return {"created":created}


@app.get("/users/me/assets")
def my_assets(db: Session = Depends(get_db), current_user: str = Depends(verify_token)):
    user = get_current_user_record(current_user, db)
    assets = db.query(Asset).options(joinedload(Asset.category)).filter(Asset.assigned_user_id == user.id).order_by(Asset.asset_tag).all()
    return assets

@app.get("/users/me/issues")
def my_issues(db: Session = Depends(get_db), current_user: str = Depends(verify_token)):
    user = get_current_user_record(current_user, db)
    rows = db.query(AssetIssue).options(joinedload(AssetIssue.asset)).filter(AssetIssue.reported_by_user_id == user.id).order_by(AssetIssue.created_at.desc()).all()
    return [{"id":r.id,"asset_id":r.asset_id,"asset_tag":r.asset.asset_tag if r.asset else None,"asset_name":r.asset.name if r.asset else None,"title":r.title,"description":r.description,"priority":r.priority,"status":r.status,"resolution":r.resolution,"created_at":r.created_at} for r in rows]


# ---------------------------------------------------------------------------
# Batch 7 - Documents and compliance
# ---------------------------------------------------------------------------

@app.get("/admin/compliance/summary")
def compliance_summary(db: Session = Depends(get_db), current_user: str = Depends(verify_token)):
    require_admin(current_user, db)
    today = datetime.utcnow()
    soon = today + timedelta(days=30)
    docs = db.query(AssetDocument).all()
    records = db.query(ComplianceRecord).all()
    return {
        "documents": len(docs),
        "expired_documents": sum(1 for d in docs if d.expiry_date and d.expiry_date < today),
        "documents_expiring_soon": sum(1 for d in docs if d.expiry_date and today <= d.expiry_date <= soon),
        "compliance_records": len(records),
        "overdue_compliance": sum(1 for r in records if r.status not in ("Completed", "Not Required") and r.due_date and r.due_date < today),
        "compliance_due_soon": sum(1 for r in records if r.status not in ("Completed", "Not Required") and r.due_date and today <= r.due_date <= soon),
    }

@app.get("/admin/documents")
def list_documents(db: Session = Depends(get_db), current_user: str = Depends(verify_token)):
    require_admin(current_user, db)
    rows = db.query(AssetDocument).options(joinedload(AssetDocument.asset)).order_by(AssetDocument.expiry_date.asc().nullslast(), AssetDocument.created_at.desc()).all()
    return [{
        "id": d.id, "asset_id": d.asset_id, "asset_tag": d.asset.asset_tag if d.asset else None, "asset_name": d.asset.name if d.asset else None,
        "title": d.title, "document_type": d.document_type, "reference": d.reference, "issued_date": d.issued_date, "expiry_date": d.expiry_date,
        "document_url": d.document_url, "notes": d.notes, "created_by": d.created_by, "created_at": d.created_at
    } for d in rows]

@app.post("/admin/documents")
def create_document(payload: AssetDocumentCreate, db: Session = Depends(get_db), current_user: str = Depends(verify_token)):
    require_admin(current_user, db)
    asset = db.query(Asset).filter(Asset.id == payload.asset_id).first()
    if not asset: raise HTTPException(status_code=404, detail="Asset not found")
    if not payload.title.strip(): raise HTTPException(status_code=400, detail="Document title is required")
    doc = AssetDocument(**payload.model_dump(), title=payload.title.strip(), created_by=current_user)
    db.add(doc); db.commit(); db.refresh(doc)
    log_audit(db, current_user, "CREATE", "ASSET_DOCUMENT", doc.title, doc.id, f"Added document to {asset.asset_tag}")
    return doc

@app.put("/admin/documents/{document_id}")
def update_document(document_id: int, payload: AssetDocumentUpdate, db: Session = Depends(get_db), current_user: str = Depends(verify_token)):
    require_admin(current_user, db)
    doc = db.query(AssetDocument).filter(AssetDocument.id == document_id).first()
    if not doc: raise HTTPException(status_code=404, detail="Document not found")
    data = payload.model_dump(exclude_unset=True)
    if "title" in data:
        data["title"] = data["title"].strip()
        if not data["title"]: raise HTTPException(status_code=400, detail="Document title is required")
    for k,v in data.items(): setattr(doc,k,v)
    db.commit(); db.refresh(doc)
    log_audit(db, current_user, "UPDATE", "ASSET_DOCUMENT", doc.title, doc.id, "Updated asset document")
    return doc

@app.delete("/admin/documents/{document_id}")
def delete_document(document_id: int, db: Session = Depends(get_db), current_user: str = Depends(verify_token)):
    require_admin(current_user, db)
    doc = db.query(AssetDocument).filter(AssetDocument.id == document_id).first()
    if not doc: raise HTTPException(status_code=404, detail="Document not found")
    title = doc.title; db.delete(doc); db.commit()
    log_audit(db, current_user, "DELETE", "ASSET_DOCUMENT", title, document_id, "Deleted asset document")
    return {"message":"Document deleted"}

@app.get("/admin/compliance")
def list_compliance(db: Session = Depends(get_db), current_user: str = Depends(verify_token)):
    require_admin(current_user, db)
    rows = db.query(ComplianceRecord).options(joinedload(ComplianceRecord.asset)).order_by(ComplianceRecord.due_date.asc().nullslast(), ComplianceRecord.created_at.desc()).all()
    return [{
        "id": r.id, "asset_id": r.asset_id, "asset_tag": r.asset.asset_tag if r.asset else None, "asset_name": r.asset.name if r.asset else None,
        "compliance_type": r.compliance_type, "status": r.status, "due_date": r.due_date, "completed_date": r.completed_date,
        "reference": r.reference, "notes": r.notes, "created_by": r.created_by, "created_at": r.created_at
    } for r in rows]

@app.post("/admin/compliance")
def create_compliance(payload: ComplianceRecordCreate, db: Session = Depends(get_db), current_user: str = Depends(verify_token)):
    require_admin(current_user, db)
    asset = db.query(Asset).filter(Asset.id == payload.asset_id).first()
    if not asset: raise HTTPException(status_code=404, detail="Asset not found")
    record = ComplianceRecord(**payload.model_dump(), created_by=current_user)
    db.add(record); db.commit(); db.refresh(record)
    log_audit(db, current_user, "CREATE", "COMPLIANCE", record.compliance_type, record.id, f"Added compliance record to {asset.asset_tag}")
    return record

@app.put("/admin/compliance/{record_id}")
def update_compliance(record_id: int, payload: ComplianceRecordUpdate, db: Session = Depends(get_db), current_user: str = Depends(verify_token)):
    require_admin(current_user, db)
    record = db.query(ComplianceRecord).filter(ComplianceRecord.id == record_id).first()
    if not record: raise HTTPException(status_code=404, detail="Compliance record not found")
    for k,v in payload.model_dump(exclude_unset=True).items(): setattr(record,k,v)
    db.commit(); db.refresh(record)
    log_audit(db, current_user, "UPDATE", "COMPLIANCE", record.compliance_type, record.id, "Updated compliance record")
    return record

@app.delete("/admin/compliance/{record_id}")
def delete_compliance(record_id: int, db: Session = Depends(get_db), current_user: str = Depends(verify_token)):
    require_admin(current_user, db)
    record = db.query(ComplianceRecord).filter(ComplianceRecord.id == record_id).first()
    if not record: raise HTTPException(status_code=404, detail="Compliance record not found")
    name = record.compliance_type; db.delete(record); db.commit()
    log_audit(db, current_user, "DELETE", "COMPLIANCE", name, record_id, "Deleted compliance record")
    return {"message":"Compliance record deleted"}


# ---------------------------------------------------------------------------
# Batch 6 - Suppliers and procurement
# ---------------------------------------------------------------------------

@app.get("/admin/suppliers")
def list_suppliers(db: Session = Depends(get_db), current_user: str = Depends(verify_token)):
    require_admin(current_user, db)
    suppliers = db.query(Supplier).order_by(Supplier.name.asc()).all()
    return [{
        "id": s.id, "name": s.name, "contact_name": s.contact_name, "email": s.email,
        "phone": s.phone, "website": s.website, "address": s.address, "notes": s.notes,
        "is_active": s.is_active, "created_at": s.created_at,
        "purchase_orders": db.query(PurchaseOrder).filter(PurchaseOrder.supplier_id == s.id).count()
    } for s in suppliers]

@app.post("/admin/suppliers")
def create_supplier(payload: SupplierCreate, db: Session = Depends(get_db), current_user: str = Depends(verify_token)):
    require_admin(current_user, db)
    name = payload.name.strip()
    if not name: raise HTTPException(status_code=400, detail="Supplier name is required")
    if db.query(Supplier).filter(Supplier.name.ilike(name)).first():
        raise HTTPException(status_code=400, detail="A supplier with this name already exists")
    supplier = Supplier(**payload.model_dump(), name=name)
    db.add(supplier); db.commit(); db.refresh(supplier)
    log_audit(db, current_user, "CREATE", "SUPPLIER", supplier.name, supplier.id, "Created supplier")
    return supplier

@app.put("/admin/suppliers/{supplier_id}")
def update_supplier(supplier_id: int, payload: SupplierUpdate, db: Session = Depends(get_db), current_user: str = Depends(verify_token)):
    require_admin(current_user, db)
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not supplier: raise HTTPException(status_code=404, detail="Supplier not found")
    data = payload.model_dump(exclude_unset=True)
    if "name" in data:
        data["name"] = data["name"].strip()
        duplicate = db.query(Supplier).filter(Supplier.name.ilike(data["name"]), Supplier.id != supplier_id).first()
        if duplicate: raise HTTPException(status_code=400, detail="A supplier with this name already exists")
    for k,v in data.items(): setattr(supplier,k,v)
    supplier.updated_at = datetime.utcnow(); db.commit(); db.refresh(supplier)
    log_audit(db, current_user, "UPDATE", "SUPPLIER", supplier.name, supplier.id, "Updated supplier")
    return supplier

@app.get("/admin/purchase-orders")
def list_purchase_orders(db: Session = Depends(get_db), current_user: str = Depends(verify_token)):
    require_admin(current_user, db)
    orders = db.query(PurchaseOrder).options(joinedload(PurchaseOrder.supplier), joinedload(PurchaseOrder.items)).order_by(PurchaseOrder.created_at.desc()).all()
    return [{
        "id": o.id, "order_number": o.order_number, "supplier_id": o.supplier_id,
        "supplier_name": o.supplier.name if o.supplier else "", "status": o.status,
        "order_date": o.order_date, "expected_date": o.expected_date, "received_date": o.received_date,
        "total_value": float(o.total_value or 0), "notes": o.notes, "created_by": o.created_by,
        "created_at": o.created_at,
        "items": [{"id":i.id,"description":i.description,"quantity":i.quantity,"unit_cost":float(i.unit_cost or 0),"received_quantity":i.received_quantity,"asset_id":i.asset_id} for i in o.items]
    } for o in orders]

@app.post("/admin/purchase-orders")
def create_purchase_order(payload: PurchaseOrderCreate, db: Session = Depends(get_db), current_user: str = Depends(verify_token)):
    require_admin(current_user, db)
    if payload.status not in {"Draft","Ordered","Partially Received","Received","Cancelled"}:
        raise HTTPException(status_code=400, detail="Invalid purchase order status")
    if not db.query(Supplier).filter(Supplier.id == payload.supplier_id, Supplier.is_active == True).first():
        raise HTTPException(status_code=404, detail="Active supplier not found")
    if db.query(PurchaseOrder).filter(PurchaseOrder.order_number == payload.order_number.strip()).first():
        raise HTTPException(status_code=400, detail="Purchase order number already exists")
    order = PurchaseOrder(order_number=payload.order_number.strip(), supplier_id=payload.supplier_id, status=payload.status,
                          order_date=payload.order_date, expected_date=payload.expected_date, received_date=payload.received_date,
                          notes=payload.notes, created_by=current_user)
    total=0.0
    for raw in payload.items:
        description=str(raw.get("description") or "").strip(); quantity=int(raw.get("quantity") or 1); unit=float(raw.get("unit_cost") or 0)
        if not description or quantity < 1 or unit < 0: raise HTTPException(status_code=400, detail="Invalid purchase order item")
        item=PurchaseOrderItem(description=description, quantity=quantity, unit_cost=unit, received_quantity=int(raw.get("received_quantity") or 0), asset_id=raw.get("asset_id"))
        order.items.append(item); total += quantity*unit
    order.total_value=total; db.add(order); db.commit(); db.refresh(order)
    log_audit(db,current_user,"CREATE","PURCHASE_ORDER",order.order_number,order.id,f"Created purchase order for {order.total_value:.2f}")
    return {"id":order.id,"order_number":order.order_number,"total_value":order.total_value}

@app.put("/admin/purchase-orders/{order_id}")
def update_purchase_order(order_id:int,payload:PurchaseOrderUpdate,db:Session=Depends(get_db),current_user:str=Depends(verify_token)):
    require_admin(current_user,db); order=db.query(PurchaseOrder).filter(PurchaseOrder.id==order_id).first()
    if not order: raise HTTPException(status_code=404,detail="Purchase order not found")
    data=payload.model_dump(exclude_unset=True)
    if data.get("status") and data["status"] not in {"Draft","Ordered","Partially Received","Received","Cancelled"}: raise HTTPException(status_code=400,detail="Invalid purchase order status")
    for k,v in data.items(): setattr(order,k,v)
    order.updated_at=datetime.utcnow(); db.commit(); db.refresh(order)
    log_audit(db,current_user,"UPDATE","PURCHASE_ORDER",order.order_number,order.id,"Updated purchase order")
    return {"message":"Purchase order updated"}

@app.get("/admin/procurement/summary")
def procurement_summary(db:Session=Depends(get_db),current_user:str=Depends(verify_token)):
    require_admin(current_user,db); orders=db.query(PurchaseOrder).all()
    return {"suppliers":db.query(Supplier).filter(Supplier.is_active==True).count(),"orders":len(orders),
            "draft":sum(o.status=="Draft" for o in orders),"ordered":sum(o.status=="Ordered" for o in orders),
            "partially_received":sum(o.status=="Partially Received" for o in orders),"received":sum(o.status=="Received" for o in orders),
            "open_value":sum(float(o.total_value or 0) for o in orders if o.status in {"Ordered","Partially Received"}),
            "lifetime_value":sum(float(o.total_value or 0) for o in orders if o.status != "Cancelled")}


# ---------------------------------------------------------------------------
# Batch 8-10 - Finance, analytics, security and system health
# ---------------------------------------------------------------------------

@app.get("/admin/finance/summary")
def finance_summary(db: Session = Depends(get_db), current_user: str = Depends(verify_token)):
    require_admin(current_user, db)
    now = datetime.utcnow()
    year = now.year
    month = now.month
    expenses = db.query(ExpenseRecord).all()
    budgets = db.query(Budget).filter(Budget.year == year).all()
    month_expenses = [e for e in expenses if e.expense_date and e.expense_date.year == year and e.expense_date.month == month]
    year_expenses = [e for e in expenses if e.expense_date and e.expense_date.year == year]
    month_budget = sum(float(b.amount or 0) for b in budgets if b.month in (None, month))
    year_budget = sum(float(b.amount or 0) for b in budgets)
    return {
        "year": year, "month": month,
        "month_spend": sum(float(e.amount or 0) for e in month_expenses),
        "year_spend": sum(float(e.amount or 0) for e in year_expenses),
        "lifetime_spend": sum(float(e.amount or 0) for e in expenses),
        "month_budget": month_budget, "year_budget": year_budget,
        "month_remaining": month_budget - sum(float(e.amount or 0) for e in month_expenses),
        "year_remaining": year_budget - sum(float(e.amount or 0) for e in year_expenses),
        "expense_count": len(expenses), "budget_count": db.query(Budget).count(),
    }

@app.get("/admin/expenses")
def list_expenses(db: Session = Depends(get_db), current_user: str = Depends(verify_token)):
    require_admin(current_user, db)
    rows = db.query(ExpenseRecord).order_by(ExpenseRecord.expense_date.desc(), ExpenseRecord.id.desc()).limit(1000).all()
    return [{"id":e.id,"asset_id":e.asset_id,"asset_tag":e.asset.asset_tag if e.asset else None,"supplier_id":e.supplier_id,
             "supplier_name":e.supplier.name if e.supplier else None,"category":e.category,"description":e.description,
             "amount":float(e.amount or 0),"expense_date":e.expense_date,"reference":e.reference,"notes":e.notes,
             "created_by":e.created_by,"created_at":e.created_at} for e in rows]

@app.post("/admin/expenses")
def create_expense(payload: ExpenseCreate, db: Session = Depends(get_db), current_user: str = Depends(verify_token)):
    require_admin(current_user, db)
    if payload.asset_id and not db.query(Asset).filter(Asset.id == payload.asset_id).first():
        raise HTTPException(status_code=404, detail="Asset not found")
    if payload.supplier_id and not db.query(Supplier).filter(Supplier.id == payload.supplier_id).first():
        raise HTTPException(status_code=404, detail="Supplier not found")
    expense = ExpenseRecord(**payload.model_dump(), expense_date=payload.expense_date or datetime.utcnow(), created_by=current_user)
    db.add(expense); db.commit(); db.refresh(expense)
    log_audit(db, current_user, "CREATE", "EXPENSE", expense.description, expense.id, f"Recorded expense of {float(expense.amount or 0):.2f}")
    return {"message":"Expense created", "id":expense.id}

@app.put("/admin/expenses/{expense_id}")
def update_expense(expense_id: int, payload: ExpenseUpdate, db: Session = Depends(get_db), current_user: str = Depends(verify_token)):
    require_admin(current_user, db)
    expense = db.query(ExpenseRecord).filter(ExpenseRecord.id == expense_id).first()
    if not expense: raise HTTPException(status_code=404, detail="Expense not found")
    for k,v in payload.model_dump(exclude_unset=True).items(): setattr(expense,k,v)
    expense.updated_at=datetime.utcnow(); db.commit(); db.refresh(expense)
    log_audit(db, current_user, "UPDATE", "EXPENSE", expense.description, expense.id, "Updated expense")
    return {"message":"Expense updated"}

@app.delete("/admin/expenses/{expense_id}")
def delete_expense(expense_id: int, db: Session = Depends(get_db), current_user: str = Depends(verify_token)):
    require_admin(current_user, db)
    expense = db.query(ExpenseRecord).filter(ExpenseRecord.id == expense_id).first()
    if not expense: raise HTTPException(status_code=404, detail="Expense not found")
    name=expense.description; db.delete(expense); db.commit()
    log_audit(db, current_user, "DELETE", "EXPENSE", name, expense_id, "Deleted expense")
    return {"message":"Expense deleted"}

@app.get("/admin/budgets")
def list_budgets(db: Session = Depends(get_db), current_user: str = Depends(verify_token)):
    require_admin(current_user, db)
    return [{"id":b.id,"name":b.name,"category":b.category,"year":b.year,"month":b.month,"amount":float(b.amount or 0),"notes":b.notes} for b in db.query(Budget).order_by(Budget.year.desc(), Budget.month.asc().nullsfirst(), Budget.name.asc()).all()]

@app.post("/admin/budgets")
def create_budget(payload: BudgetCreate, db: Session = Depends(get_db), current_user: str = Depends(verify_token)):
    require_admin(current_user, db)
    budget=Budget(**payload.model_dump(), created_by=current_user)
    db.add(budget); db.commit(); db.refresh(budget)
    log_audit(db,current_user,"CREATE","BUDGET",budget.name,budget.id,"Created budget")
    return {"message":"Budget created","id":budget.id}

@app.put("/admin/budgets/{budget_id}")
def update_budget(budget_id:int,payload:BudgetUpdate,db:Session=Depends(get_db),current_user:str=Depends(verify_token)):
    require_admin(current_user,db); budget=db.query(Budget).filter(Budget.id==budget_id).first()
    if not budget: raise HTTPException(status_code=404,detail="Budget not found")
    for k,v in payload.model_dump(exclude_unset=True).items(): setattr(budget,k,v)
    budget.updated_at=datetime.utcnow(); db.commit(); db.refresh(budget)
    log_audit(db,current_user,"UPDATE","BUDGET",budget.name,budget.id,"Updated budget")
    return {"message":"Budget updated"}

@app.delete("/admin/budgets/{budget_id}")
def delete_budget(budget_id:int,db:Session=Depends(get_db),current_user:str=Depends(verify_token)):
    require_admin(current_user,db); budget=db.query(Budget).filter(Budget.id==budget_id).first()
    if not budget: raise HTTPException(status_code=404,detail="Budget not found")
    name=budget.name; db.delete(budget); db.commit(); log_audit(db,current_user,"DELETE","BUDGET",name,budget_id,"Deleted budget")
    return {"message":"Budget deleted"}

@app.get("/admin/analytics/summary")
def analytics_summary(db: Session = Depends(get_db), current_user: str = Depends(verify_token)):
    require_admin(current_user, db)
    assets=db.query(Asset).all(); users=db.query(User).all(); maint=db.query(MaintenanceRecord).all(); issues=db.query(AssetIssue).all(); expenses=db.query(ExpenseRecord).all()
    by_location={}
    by_lifecycle={}
    by_health={}
    by_category={}
    for a in assets:
        by_location[a.location or "Unknown"]=by_location.get(a.location or "Unknown",0)+1
        by_lifecycle[a.lifecycle_status or "Unknown"]=by_lifecycle.get(a.lifecycle_status or "Unknown",0)+1
        by_health[a.health_status or "Unknown"]=by_health.get(a.health_status or "Unknown",0)+1
        cat=a.category.name if a.category else "Uncategorised"; by_category[cat]=by_category.get(cat,0)+1
    return {"assets":len(assets),"asset_value":sum(float(a.value or 0) for a in assets),"users":len(users),
            "active_users":sum(bool(u.is_active) for u in users),"maintenance_spend":sum(float(m.cost or 0) for m in maint),
            "expense_spend":sum(float(e.amount or 0) for e in expenses),"open_issues":sum(i.status not in {"Resolved","Closed"} for i in issues),
            "by_location":by_location,"by_lifecycle":by_lifecycle,"by_health":by_health,"by_category":by_category}

@app.get("/admin/analytics/export")
def analytics_export(db: Session = Depends(get_db), current_user: str = Depends(verify_token)):
    require_admin(current_user, db)
    rows=db.query(Asset).order_by(Asset.asset_tag.asc()).all()
    output=io.StringIO(); writer=csv.writer(output); writer.writerow(["Asset Tag","Asset","Category","Location","Lifecycle","Health","Assigned To","Value","Warranty Expiry","Replacement Date"])
    for a in rows: writer.writerow([a.asset_tag or "",a.name or "",a.category.name if a.category else "",a.location or "",a.lifecycle_status or "",a.health_status or "",a.assigned_user.full_name if a.assigned_user else "",float(a.value or 0),a.warranty_expiry_date or "",a.expected_replacement_date or ""])
    from fastapi.responses import StreamingResponse
    return StreamingResponse(iter([output.getvalue()]), media_type="text/csv", headers={"Content-Disposition":"attachment; filename=apex-asset-report.csv"})

@app.get("/admin/security/summary")
def security_summary(db: Session = Depends(get_db), current_user: str = Depends(verify_token)):
    require_super_admin(current_user, db)
    users=db.query(User).all(); now=datetime.utcnow()
    inactive_days=int((db.query(SystemSetting).filter(SystemSetting.key=="user_inactivity_days").first() or SystemSetting(value="30")).value or 30)
    stale_cutoff=now-timedelta(days=inactive_days)
    stale=[u for u in users if u.is_active and u.email != SUPER_USER_EMAIL and (u.last_login is None or u.last_login < stale_cutoff)]
    recent=db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(20).all()
    return {"users":len(users),"active_users":sum(bool(u.is_active) for u in users),"inactive_users":sum(not u.is_active for u in users),
            "unverified_users":sum(not u.is_verified for u in users),"stale_users":len(stale),"inactivity_days":inactive_days,
            "recent_admin_actions":[{"action":x.action,"resource_type":x.resource_type,"resource_name":x.resource_name,"email":x.email,"created_at":x.created_at} for x in recent]}

@app.get("/admin/system/health")
def system_health(db: Session = Depends(get_db), current_user: str = Depends(verify_token)):
    require_super_admin(current_user, db)
    checks={}
    try: db.execute(text("SELECT 1")); checks["database"]="healthy"
    except Exception as exc: checks["database"]=f"error: {exc}"
    checks["assets"]=db.query(Asset).count(); checks["users"]=db.query(User).count(); checks["notifications"]=db.query(Notification).count()
    checks["maintenance"]=db.query(MaintenanceRecord).count(); checks["documents"]=db.query(AssetDocument).count(); checks["compliance"]=db.query(ComplianceRecord).count()
    checks["suppliers"]=db.query(Supplier).count(); checks["purchase_orders"]=db.query(PurchaseOrder).count(); checks["expenses"]=db.query(ExpenseRecord).count(); checks["budgets"]=db.query(Budget).count()
    return {"status":"healthy" if checks["database"]=="healthy" else "degraded","version":app.version if "app" in globals() else "2.0.0","checked_at":datetime.utcnow(),"checks":checks}

@app.get("/audit-logs", response_model=List[AuditLogResponse])
def get_audit_logs(db: Session = Depends(get_db), current_user: str = Depends(verify_token)):
    require_super_admin(current_user, db)
    return db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(500).all()

@app.post("/users/me/change-password")
def change_password(payload: dict, db: Session = Depends(get_db), current_user: str = Depends(verify_token)):
    user = get_current_user_record(current_user, db)
    current_password = str(payload.get("current_password") or "")
    new_password = str(payload.get("new_password") or "")
    if not user.password_hash or not verify_password(current_password, user.password_hash):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    if len(new_password) < 10:
        raise HTTPException(status_code=400, detail="New password must be at least 10 characters")
    if current_password == new_password:
        raise HTTPException(status_code=400, detail="New password must be different from the current password")
    user.password_hash = get_password_hash(new_password)
    user.updated_at = datetime.utcnow()
    db.commit()
    log_audit(db, current_user, "UPDATE", "USER", user.full_name, user.id, "Changed account password")
    return {"message": "Password changed successfully"}

@app.get("/admin/settings")
def get_system_settings(db: Session = Depends(get_db), current_user: str = Depends(verify_token)):
    require_admin(current_user, db)
    rows = db.query(SystemSetting).all()
    return {r.key: r.value for r in rows}

@app.put("/admin/settings")
def update_system_settings(payload: dict, db: Session = Depends(get_db), current_user: str = Depends(verify_token)):
    require_admin(current_user, db)
    allowed = {"organisation_name", "default_location", "user_inactivity_days", "maintenance_due_soon_days"}
    for key, value in payload.items():
        if key not in allowed:
            continue
        if key.endswith("_days"):
            try:
                value = str(max(1, int(value)))
            except (TypeError, ValueError):
                raise HTTPException(status_code=400, detail=f"{key} must be a whole number")
        else:
            value = str(value).strip()
        row = db.query(SystemSetting).filter(SystemSetting.key == key).first()
        if row: row.value = value; row.updated_by = current_user; row.updated_at = datetime.utcnow()
        else: db.add(SystemSetting(key=key, value=value, updated_by=current_user))
    db.commit()
    log_audit(db, current_user, "UPDATE", "SYSTEM_SETTINGS", "System Settings", None, "Updated system configuration")
    return get_system_settings(db, current_user)

@app.post("/assets/import")
def import_assets(payload: dict, db: Session = Depends(get_db), current_user: str = Depends(verify_token)):
    require_admin(current_user, db)
    rows = payload.get("rows") if isinstance(payload, dict) else None
    if not isinstance(rows, list) or not rows:
        raise HTTPException(status_code=400, detail="No asset rows supplied")
    created, skipped, errors = 0, 0, []
    for index, row in enumerate(rows, start=2):
        if not isinstance(row, dict) or not str(row.get("name") or "").strip():
            errors.append({"row": index, "error": "Name is required"}); continue
        serial = str(row.get("serial_number") or "").strip() or None
        if serial and db.query(Asset).filter(Asset.serial_number == serial).first():
            skipped += 1; continue
        try:
            asset = Asset(name=str(row.get("name")).strip(), description=row.get("description"), serial_number=serial, value=float(row.get("value") or 0), location=str(row.get("location") or "APEX HUB"), status=str(row.get("status") or "active"), lifecycle_status=str(row.get("lifecycle_status") or "In Stock"), health_status=str(row.get("health_status") or "Healthy"))
            db.add(asset); db.flush()
            asset.asset_tag = f"APEX-{asset.id:06d}"; asset.qr_token = secrets.token_urlsafe(18)
            created += 1
        except Exception as exc:
            db.rollback(); errors.append({"row": index, "error": str(exc)})
    db.commit()
    log_audit(db, current_user, "IMPORT", "ASSET", "Asset Import", None, f"Imported {created} assets; skipped {skipped}; errors {len(errors)}")
    return {"created": created, "skipped": skipped, "errors": errors}

@app.post("/categories", response_model=CategoryResponse)
def create_category(category: CategoryCreate, db: Session = Depends(get_db), current_user: str = Depends(verify_token)):
    require_admin(current_user, db)
    db_category = Category(name=category.name.strip(), description=category.description)
    db.add(db_category)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=400, detail="Category already exists")
    db.refresh(db_category)
    log_audit(db, current_user, "CREATE", "CATEGORY", db_category.name, db_category.id, f"Created category: {db_category.name}")
    return db_category

@app.get("/categories", response_model=List[CategoryResponse])
def list_categories(db: Session = Depends(get_db), current_user: str = Depends(verify_token)):
    get_current_user_record(current_user, db)
    return db.query(Category).order_by(Category.name).all()

@app.post("/assets", response_model=AssetResponse)
def create_asset(asset: AssetCreate, db: Session = Depends(get_db), current_user: str = Depends(verify_token)):
    require_admin(current_user, db)
    if not asset.location.strip():
        location = "APEX HUB"
    else:
        location = asset.location.strip()
    db_asset = Asset(
        name=asset.name.strip(),
        description=asset.description,
        category_id=asset.category_id,
        serial_number=asset.serial_number.strip(),
        purchase_date=asset.purchase_date,
        value=asset.value,
        location=location,
        status=asset.status,
        lifecycle_status=asset.lifecycle_status,
        health_status=asset.health_status,
        warranty_provider=asset.warranty_provider,
        warranty_start_date=asset.warranty_start_date,
        warranty_expiry_date=asset.warranty_expiry_date,
        warranty_reference=asset.warranty_reference,
        warranty_notes=asset.warranty_notes,
        warranty_status="Unknown",
        expected_replacement_date=asset.expected_replacement_date,
        replacement_priority=asset.replacement_priority,
        replacement_reason=asset.replacement_reason,
        estimated_replacement_cost=asset.estimated_replacement_cost,
        replacement_notes=asset.replacement_notes,
        qr_token=secrets.token_urlsafe(18),
    )
    db.add(db_asset)
    db.flush()
    db_asset.asset_tag = f"APEX-{db_asset.id:06d}"
    _refresh_asset_health(db_asset)
    db.add(AssetLifecycleEvent(asset_id=db_asset.id, from_status=None, to_status=db_asset.lifecycle_status, reason="Asset created", changed_by=current_user))
    db.commit()
    db.refresh(db_asset)
    log_audit(db, current_user, "CREATE", "ASSET", db_asset.name, db_asset.id, f"Created {db_asset.asset_tag} (Serial: {db_asset.serial_number})")
    return db_asset

@app.get("/assets", response_model=List[AssetResponse])
def list_assets(db: Session = Depends(get_db), current_user: str = Depends(verify_token)):
    get_current_user_record(current_user, db)
    return db.query(Asset).options(joinedload(Asset.category), joinedload(Asset.assigned_user)).order_by(Asset.id.desc()).all()

@app.get("/assets/{asset_id}", response_model=AssetResponse)
def get_asset(asset_id: int, db: Session = Depends(get_db), current_user: str = Depends(verify_token)):
    get_current_user_record(current_user, db)
    asset = db.query(Asset).options(joinedload(Asset.category), joinedload(Asset.assigned_user)).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return asset

@app.get("/assets/qr/{qr_token}", response_model=AssetResponse)
def get_asset_by_qr(qr_token: str, db: Session = Depends(get_db), current_user: str = Depends(verify_token)):
    get_current_user_record(current_user, db)
    asset = db.query(Asset).options(joinedload(Asset.category), joinedload(Asset.assigned_user)).filter(Asset.qr_token == qr_token).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset QR code not recognised")
    return asset

@app.put("/assets/{asset_id}", response_model=AssetResponse)
def update_asset(asset_id: int, asset: AssetUpdate, db: Session = Depends(get_db), current_user: str = Depends(verify_token)):
    require_admin(current_user, db)
    db_asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not db_asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    changes = []
    update_data = asset.model_dump(exclude_unset=True)
    if "lifecycle_status" in update_data and update_data["lifecycle_status"] not in ALLOWED_LIFECYCLE_STATUSES:
        raise HTTPException(status_code=400, detail="Invalid lifecycle status")
    if "health_status" in update_data and update_data["health_status"] not in ALLOWED_HEALTH_STATUSES:
        raise HTTPException(status_code=400, detail="Invalid health status")
    if "replacement_priority" in update_data and update_data["replacement_priority"] not in ALLOWED_REPLACEMENT_PRIORITIES:
        raise HTTPException(status_code=400, detail="Invalid replacement priority")
    previous_lifecycle = db_asset.lifecycle_status or "In Stock"
    for key, value in update_data.items():
        if key == "location" and not value:
            value = "APEX HUB"
        setattr(db_asset, key, value)
        changes.append(key)
    if "lifecycle_status" in update_data and update_data["lifecycle_status"] != previous_lifecycle:
        db.add(AssetLifecycleEvent(asset_id=db_asset.id, from_status=previous_lifecycle, to_status=update_data["lifecycle_status"], reason="Asset lifecycle updated", changed_by=current_user))
    _refresh_asset_health(db_asset)
    db_asset.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_asset)
    log_audit(db, current_user, "UPDATE", "ASSET", db_asset.name, db_asset.id, f"Updated asset fields: {', '.join(changes)}")
    return db_asset

@app.delete("/assets/{asset_id}")
def delete_asset(asset_id: int, db: Session = Depends(get_db), current_user: str = Depends(verify_token)):
    require_super_admin(current_user, db)
    db_asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not db_asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    name, tag = db_asset.name, db_asset.asset_tag
    db.delete(db_asset)
    db.commit()
    log_audit(db, current_user, "DELETE", "ASSET", name, asset_id, f"Deleted asset {tag}")
    return {"message": "Asset deleted successfully"}

@app.post("/assets/{asset_id}/assign", response_model=AssetResponse)
def assign_asset(asset_id: int, request: AssignAssetRequest, db: Session = Depends(get_db), current_user: str = Depends(verify_token)):
    require_admin(current_user, db)
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    location = request.location.strip() if request.location and request.location.strip() else "APEX HUB"

    if request.user_id is not None:
        user = db.query(User).filter(User.id == request.user_id, User.is_active == True).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found or inactive")
        action = "ASSIGNED"
        details = f"Assigned {asset.asset_tag} to {user.full_name} ({user.email}) at {location}"
    else:
        user = None
        action = "UNASSIGNED"
        details = f"Unassigned {asset.asset_tag} at {location}"

    previous_user = asset.assigned_user.full_name if asset.assigned_user else "Unassigned"
    asset.assigned_user_id = request.user_id
    if asset.lifecycle_status != "Retired":
        _record_lifecycle(db, asset, "Assigned" if request.user_id is not None else "In Stock", current_user, "Asset assignment changed")
    asset.location = location
    asset.updated_at = datetime.utcnow()

    history = AssetAssignment(
        asset_id=asset.id,
        user_id=request.user_id,
        action=action,
        location=location,
        assigned_by=current_user,
        notes=request.notes,
    )
    db.add(history)
    db.commit()
    db.refresh(asset)

    log_audit(db, current_user, "UPDATE", "ASSET", asset.name, asset.id, f"{details}. Previous user: {previous_user}.")
    return db.query(Asset).options(joinedload(Asset.category), joinedload(Asset.assigned_user)).filter(Asset.id == asset_id).first()

@app.get("/assets/{asset_id}/assignments", response_model=List[AssignmentResponse])
def assignment_history(asset_id: int, db: Session = Depends(get_db), current_user: str = Depends(verify_token)):
    get_current_user_record(current_user, db)
    if not db.query(Asset).filter(Asset.id == asset_id).first():
        raise HTTPException(status_code=404, detail="Asset not found")
    return db.query(AssetAssignment).options(joinedload(AssetAssignment.user)).filter(AssetAssignment.asset_id == asset_id).order_by(AssetAssignment.assigned_at.desc()).all()

@app.get("/users/me", response_model=UserResponse)
def get_current_user(db: Session = Depends(get_db), current_user: str = Depends(verify_token)):
    return get_current_user_record(current_user, db)

@app.put("/users/me", response_model=UserResponse)
def update_current_user(user_data: UserUpdate, db: Session = Depends(get_db), current_user: str = Depends(verify_token)):
    user = get_current_user_record(current_user, db)
    for key, value in user_data.model_dump(exclude_unset=True).items():
        setattr(user, key, value)
    user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(user)
    log_audit(db, current_user, "UPDATE", "USER", user.full_name, user.id, f"Updated profile: {', '.join(user_data.model_dump(exclude_unset=True).keys())}")
    return user

@app.get("/users/{user_id}", response_model=UserPublicResponse)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.get("/admin/employees")
def admin_employees(db: Session = Depends(get_db), current_user: str = Depends(verify_token)):
    require_admin(current_user, db)
    users=db.query(User).order_by(User.full_name.asc()).all()
    return [{"id":u.id,"email":u.email,"full_name":u.full_name,"role":u.role,"is_active":u.is_active,"location":u.location,"last_login":u.last_login,"asset_count":db.query(Asset).filter(Asset.assigned_user_id==u.id).count()} for u in users]


@app.patch("/admin/users/{user_id}/status")
def update_user_status(user_id:int,payload:dict,db:Session=Depends(get_db),current_user:str=Depends(verify_token)):
    require_admin(current_user,db); user=db.query(User).filter(User.id==user_id).first()
    if not user: raise HTTPException(status_code=404,detail="User not found")
    if user.email == SUPER_USER_EMAIL: raise HTTPException(status_code=400,detail="The super admin cannot be deactivated")
    if "is_active" not in payload: raise HTTPException(status_code=400,detail="is_active is required")
    user.is_active=bool(payload["is_active"]); user.updated_at=datetime.utcnow(); db.commit(); log_audit(db,current_user,"UPDATE","USER",user.full_name,user.id,f"Set account active={user.is_active}"); return {"id":user.id,"is_active":user.is_active}


@app.get("/management/summary")
def management_summary(db:Session=Depends(get_db),current_user:str=Depends(verify_token)):
    require_admin(current_user,db); run_automation(db)
    now=datetime.utcnow(); due=_setting_int(db,"maintenance_due_soon_days",14)
    assets=db.query(Asset).all(); employees=db.query(User).all()
    overdue=db.query(MaintenanceRecord).filter(MaintenanceRecord.status.in_(["Scheduled","In Progress"]),MaintenanceRecord.scheduled_date < now).count()
    open_issues=db.query(AssetIssue).filter(AssetIssue.status.notin_(["Fixed","Returned","Cancelled"])).count()
    warranty=sum(1 for a in assets if a.warranty_expiry_date and now <= a.warranty_expiry_date <= now+timedelta(days=60) or a.warranty_expiry_date and a.warranty_expiry_date < now)
    replacement=sum(1 for a in assets if a.lifecycle_status=="Replacement Required" or (a.expected_replacement_date and a.expected_replacement_date<=now+timedelta(days=30)))
    unread=db.query(Notification).filter(Notification.is_read==False, (Notification.user_id==None) | (Notification.user_id==db.query(User.id).filter(User.email==current_user).scalar_subquery())).count()
    return {"employees":len(employees),"active_employees":sum(u.is_active for u in employees),"inactive_employees":sum(not u.is_active for u in employees),"assigned_assets":sum(a.assigned_user_id is not None for a in assets),"unassigned_assets":sum(a.assigned_user_id is None for a in assets),"open_issues":open_issues,"overdue_maintenance":overdue,"warranty_alerts":warranty,"replacement_alerts":replacement,"unread_notifications":unread,"asset_value":sum(float(a.value or 0) for a in assets),"maintenance_due_soon_days":due}


@app.get("/admin/users", response_model=List[UserResponse])
def list_users(skip: int = 0, limit: int = 200, search: str = None, membership_tier: str = None, role: str = None,
               db: Session = Depends(get_db), current_user: str = Depends(verify_token)):
    require_admin(current_user, db)
    query = db.query(User)
    if search:
        query = query.filter((User.full_name.ilike(f"%{search}%")) | (User.email.ilike(f"%{search}%")))
    if membership_tier:
        query = query.filter(User.membership_tier == membership_tier)
    if role:
        query = query.filter(User.role == role)
    return query.order_by(User.full_name).offset(skip).limit(limit).all()

@app.post("/admin/users/invite", response_model=InviteResponse)
def invite_user(user_data: UserCreate, db: Session = Depends(get_db), current_user: str = Depends(verify_token)):
    require_admin(current_user, db)
    email = str(user_data.email).lower()
    existing = db.query(User).filter(User.email == email).first()
    if existing and existing.is_active and existing.password_hash:
        raise HTTPException(status_code=400, detail="A user with this email already has an active account")

    if existing:
        user = existing
        user.full_name = user_data.full_name
        user.phone = user_data.phone
        user.location = user_data.location or "APEX HUB"
        user.role = user_data.role
        user.is_active = True
    else:
        user = User(
            email=email,
            full_name=user_data.full_name,
            phone=user_data.phone,
            location=user_data.location or "APEX HUB",
            bike_interests=user_data.bike_interests,
            bio=user_data.bio,
            role=user_data.role,
            membership_tier="bronze",
            is_active=True,
            is_verified=False,
        )
        db.add(user)
        db.flush()

    token = secrets.token_urlsafe(32)
    user.invite_token = token
    user.invite_expires_at = datetime.utcnow() + timedelta(hours=48)
    user.invited_at = datetime.utcnow()
    user.password_hash = None
    db.commit()

    invite_url = f"{APP_PUBLIC_URL}/invite/{quote(token)}"
    try:
        send_invitation_email(user.email, user.full_name, invite_url)
        message = "Invitation sent by email."
        returned_url = None
    except Exception as exc:
        message = f"User created, but email could not be sent: {exc}"
        returned_url = invite_url

    log_audit(db, current_user, "CREATE", "USER", user.full_name, user.id, f"Invited user {user.email}")
    return InviteResponse(message=message, email=user.email, invite_url=returned_url)

@app.post("/admin/users", response_model=UserResponse)
def create_user(user_data: UserCreate, db: Session = Depends(get_db), current_user: str = Depends(verify_token)):
    # Keep the existing endpoint compatible, but route new accounts through invitation.
    require_admin(current_user, db)
    email = str(user_data.email).lower()
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(email=email, full_name=user_data.full_name, phone=user_data.phone,
                location=user_data.location or "APEX HUB", bike_interests=user_data.bike_interests,
                bio=user_data.bio, role=user_data.role, membership_tier="bronze", is_active=True)
    db.add(user)
    db.commit()
    db.refresh(user)
    log_audit(db, current_user, "CREATE", "USER", user.full_name, user.id, f"Created user: {user.email}")
    return user

@app.put("/admin/users/{user_id}", response_model=UserResponse)
def update_user(user_id: int, user_data: UserAdminUpdate, db: Session = Depends(get_db), current_user: str = Depends(verify_token)):
    require_admin(current_user, db)
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    for key, value in user_data.model_dump(exclude_unset=True).items():
        setattr(user, key, value)
    user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(user)
    log_audit(db, current_user, "UPDATE", "USER", user.full_name, user.id, f"Admin updated user: {', '.join(user_data.model_dump(exclude_unset=True).keys())}")
    return user

@app.delete("/admin/users/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db), current_user: str = Depends(verify_token)):
    require_admin(current_user, db)
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.email == SUPER_USER_EMAIL:
        raise HTTPException(status_code=400, detail="The super admin cannot be deactivated")
    user.is_active = False
    user.updated_at = datetime.utcnow()
    db.commit()
    log_audit(db, current_user, "DELETE", "USER", user.full_name, user.id, "Deactivated user")
    return {"message": "User deactivated successfully"}

@app.post("/admin/users/{user_id}/resend-invite", response_model=InviteResponse)
def resend_invite(user_id: int, db: Session = Depends(get_db), current_user: str = Depends(verify_token)):
    require_admin(current_user, db)
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.password_hash and user.is_verified:
        raise HTTPException(status_code=400, detail="This user has already activated their account")
    token = secrets.token_urlsafe(32)
    user.invite_token = token
    user.invite_expires_at = datetime.utcnow() + timedelta(hours=48)
    user.invited_at = datetime.utcnow()
    db.commit()
    invite_url = f"{APP_PUBLIC_URL}/invite/{quote(token)}"
    try:
        send_invitation_email(user.email, user.full_name, invite_url)
        message = "Invitation resent by email."
        returned_url = None
    except Exception as exc:
        message = f"Email could not be sent: {exc}"
        returned_url = invite_url
    return InviteResponse(message=message, email=user.email, invite_url=returned_url)
