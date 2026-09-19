from .models import Invite
from .schemas import InviteCreate, InviteValidate, InviteAccept, InviteAcceptResponse
from passlib.context import CryptContext
import uuid
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)
from fastapi import FastAPI, HTTPException, Depends, status, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import List
from datetime import timedelta, date, datetime
import secrets
from .database import engine, SessionLocal, Base
from .models import (
    Asset, Category, Employee, AuditLog, AssetHandover,
    MaintenanceRecord, ITEquipmentSpec, VehicleSpec, User, UserRole, Invite
)
from .schemas import (
    AssetCreate, AssetUpdate, AssetResponse, CategoryCreate, CategoryResponse,
    EmployeeCreate, EmployeeResponse, EmployeeUpdate,
    AssetHandoverCreate, AssetHandoverReturn, AssetHandoverResponse,
    MaintenanceRecordCreate, MaintenanceRecordUpdate, MaintenanceRecordResponse,
    DashboardStats, AuditLogResponse, ITEquipmentSpecResponse,
    UserCreate, UserUpdate, UserResponse,
    InviteCreate, InviteAccept, InviteResponse, InviteAcceptResponse, InviteValidate
)
from .auth import create_access_token, verify_token
from .config import AUTHORIZED_ADMINS, ACCESS_TOKEN_EXPIRE_MINUTES, SUPER_USER_EMAIL
from .audit import log_audit
from .utils import generate_asset_id, generate_qr_code, calculate_depreciation, get_asset_age_years
from pydantic import BaseModel
import urllib.parse

Base.metadata.create_all(bind=engine)

app = FastAPI(title="APEX Asset Management System", description="Enterprise-grade asset tracking and management platform", version="2.0.0")

@app.on_event("startup")
def startup():
    db = SessionLocal()
    try:
        for email in AUTHORIZED_ADMINS:
            role = "super_admin" if email.lower() == SUPER_USER_EMAIL.lower() else "admin"
            existing = db.query(User).filter(User.email == email.lower()).first()
            if not existing:
                db.add(User(
                    email=email.lower(),
                    role=role,
                    can_view_dashboard=True,
                    can_manage_assets=True,
                    can_manage_employees=True,
                    can_manage_handovers=True,
                    can_manage_maintenance=True,
                    can_view_audit_logs=(role == "super_admin"),
                    can_manage_users=(role == "super_admin"),
                    is_active=True,
                    last_login=None,
                    disabled_at=None,
                    disabled_reason=None,
                ))
            else:
                existing.role = role
                existing.can_view_dashboard = True
                existing.can_manage_assets = True
                existing.can_manage_employees = True
                existing.can_manage_handovers = True
                existing.can_manage_maintenance = True
                existing.can_view_audit_logs = (role == "super_admin")
                existing.can_manage_users = (role == "super_admin")
                existing.is_active = True
                existing.disabled_at = None
                existing.disabled_reason = None
        db.commit()
    finally:
        db.close()

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()

class LoginRequest(BaseModel): email: str
class LoginResponse(BaseModel): access_token: str; token_type: str; email: str

@app.get("/health")
def health(): return {"status": "healthy"}

@app.post("/login", response_model=LoginResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    email = request.email.strip().lower()
    if email not in {allowed.lower() for allowed in AUTHORIZED_ADMINS}:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized email address")
    user = db.query(User).filter(User.email == email).first()
    if not user:
        role = "super_admin" if email == SUPER_USER_EMAIL.lower() else "admin"
        user = User(
            email=email,
            role=role,
            can_view_dashboard=True,
            can_manage_assets=True,
            can_manage_employees=True,
            can_manage_handovers=True,
            can_manage_maintenance=True,
            can_view_audit_logs=(role == "super_admin"),
            can_manage_users=(role == "super_admin"),
            is_active=True,
        )
        db.add(user)
        db.flush()
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This user account is disabled")
    user.last_login = datetime.utcnow()
    user.disabled_at = None
    user.disabled_reason = None
    db.commit()
    log_audit(db=db, email=email, action="LOGIN", resource_type="SYSTEM", resource_name="Admin Login", details="User logged in successfully")
    access_token = create_access_token(data={"sub": email}, expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    return {"access_token": access_token, "token_type": "bearer", "email": email}

@app.get("/dashboard", response_model=DashboardStats)
def get_dashboard(db: Session = Depends(get_db), current_user: str = Depends(verify_token)):
    assets = db.query(Asset).all()
    total_assets = len(assets)
    total_asset_value = sum((a.purchase_price or 0) for a in assets)
    book_value = sum((a.current_value or 0) for a in assets)
    today = date.today()
    warranty_expiring = db.query(func.count(Asset.id)).filter(and_(Asset.warranty_expiry.isnot(None), Asset.warranty_expiry <= today + timedelta(days=30), Asset.warranty_expiry >= today)).scalar()
    assets_in_repair = db.query(func.count(Asset.id)).filter(Asset.status.in_(["repair", "maintenance"])).scalar()
    assets_missing = db.query(func.count(Asset.id)).filter(Asset.status.in_(["lost", "missing"])).scalar()
    due_replacement = sum(1 for a in assets if a.purchase_date and get_asset_age_years(a.purchase_date) > 4)
    apex_assets = [a for a in assets if (a.location or "APEX HUB").strip().upper() == "APEX HUB"]
    assigned_assets = sum(1 for a in assets if a.assigned_employee_id is not None)
    available_assets = sum(1 for a in assets if a.status == "available")

    health = {"excellent": 0, "good": 0, "fair": 0, "poor": 0, "faulty": 0}
    for asset in assets:
        condition = (asset.condition or "good").lower()
        health[condition] = health.get(condition, 0) + 1

    recent_logs = db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(10).all()
    recent_activities = [{"time": log.created_at.strftime("%H:%M"), "description": log.details, "type": log.action, "action": log.action, "resource_name": log.resource_name, "created_at": log.created_at.isoformat()} for log in recent_logs]
    return {"total_assets": total_assets, "total_asset_value": total_asset_value, "book_value": book_value,
        "assets_due_replacement": due_replacement, "warranty_expiring_soon": warranty_expiring,
        "assets_in_repair": assets_in_repair, "assets_missing": assets_missing,
        "apex_hub_assets": len(apex_assets), "apex_hub_value": sum((a.current_value or 0) for a in apex_assets),
        "assigned_assets": assigned_assets, "available_assets": available_assets, "asset_health": health,
        "recent_activities": recent_activities}

# ============ EMPLOYEES ============
@app.post("/employees", response_model=EmployeeResponse)
def create_employee(employee: EmployeeCreate, db: Session = Depends(get_db), current_user: str = Depends(verify_token)):
    db_employee = Employee(**employee.dict()); db.add(db_employee); db.commit(); db.refresh(db_employee)
    log_audit(db=db, email=current_user, action="CREATE", resource_type="EMPLOYEE", resource_id=db_employee.id, resource_name=db_employee.name, details=f"Created employee: {employee.name}")
    return db_employee

@app.get("/employees", response_model=List[EmployeeResponse])
def list_employees(db: Session = Depends(get_db), current_user: str = Depends(verify_token), active_only: bool = Query(True)):
    return db.query(Employee).filter(Employee.is_active == active_only).all()

# ============ CATEGORIES ============
@app.post("/categories", response_model=CategoryResponse)
def create_category(category: CategoryCreate, db: Session = Depends(get_db), current_user: str = Depends(verify_token)):
    db_category = Category(**category.dict()); db.add(db_category); db.commit(); db.refresh(db_category); return db_category

@app.get("/categories", response_model=List[CategoryResponse])
def list_categories(db: Session = Depends(get_db), current_user: str = Depends(verify_token)): return db.query(Category).all()

# ============ ASSETS ============
@app.post("/assets", response_model=AssetResponse)
def create_asset(asset: AssetCreate, db: Session = Depends(get_db), current_user: str = Depends(verify_token)):
    data = asset.dict(exclude={"it_specs"}); data["location"] = (data.get("location") or "APEX HUB").strip() or "APEX HUB"
    data["asset_id"] = generate_asset_id(db)
    db_asset = Asset(**data); db.add(db_asset); db.commit(); db.refresh(db_asset)
    if asset.it_specs:
        spec = ITEquipmentSpec(asset_id=db_asset.id, **asset.it_specs.dict()); db.add(spec); db.commit()
    log_audit(db, current_user, "CREATE", "ASSET", db_asset.id, db_asset.name, f"Created asset {db_asset.asset_id} at {db_asset.location}")
    return db_asset

@app.get("/assets", response_model=List[AssetResponse])
def list_assets(db: Session = Depends(get_db), current_user: str = Depends(verify_token)): return db.query(Asset).order_by(Asset.created_at.desc()).all()

@app.get("/assets/{asset_id}", response_model=AssetResponse)
def get_asset(asset_id: int, db: Session = Depends(get_db), current_user: str = Depends(verify_token)):
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset: raise HTTPException(status_code=404, detail="Asset not found")
    return asset

@app.put("/assets/{asset_id}", response_model=AssetResponse)
def update_asset(asset_id: int, update_data: AssetUpdate, db: Session = Depends(get_db), current_user: str = Depends(verify_token)):
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset: raise HTTPException(status_code=404, detail="Asset not found")
    for field, value in update_data.dict(exclude_unset=True).items():
        if field == "location": value = (value or "APEX HUB").strip() or "APEX HUB"
        setattr(asset, field, value)
    db.commit(); db.refresh(asset); log_audit(db, current_user, "UPDATE", "ASSET", asset.id, asset.name, f"Updated asset {asset.asset_id}"); return asset

@app.delete("/assets/{asset_id}")
def delete_asset(asset_id: int, db: Session = Depends(get_db), current_user: str = Depends(verify_token)):
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset: raise HTTPException(status_code=404, detail="Asset not found")
    db.delete(asset); db.commit(); return {"status": "Asset deleted"}

# ============ HANDOVERS ============
@app.post("/handovers", response_model=AssetHandoverResponse)
def create_handover(handover: AssetHandoverCreate, db: Session = Depends(get_db), current_user: str = Depends(verify_token)):
    db_handover = AssetHandover(**handover.dict()); db.add(db_handover)
    asset = db.query(Asset).filter(Asset.id == handover.asset_id).first()
    if asset: asset.status = "in_use"; asset.assigned_employee_id = handover.employee_id
    db.commit(); db.refresh(db_handover); log_audit(db, current_user, "CREATE", "HANDOVER", db_handover.id, asset.name if asset else str(handover.asset_id), "Asset handed over"); return db_handover

@app.get("/handovers", response_model=List[AssetHandoverResponse])
def list_handovers(db: Session = Depends(get_db), current_user: str = Depends(verify_token)): return db.query(AssetHandover).order_by(AssetHandover.handover_date.desc()).all()

@app.put("/handovers/{handover_id}/return", response_model=AssetHandoverResponse)
def return_handover(handover_id: int, return_data: AssetHandoverReturn, db: Session = Depends(get_db), current_user: str = Depends(verify_token)):
    handover = db.query(AssetHandover).filter(AssetHandover.id == handover_id).first()
    if not handover: raise HTTPException(status_code=404, detail="Handover not found")
    handover.return_date = datetime.utcnow(); handover.is_active = False; handover.notes = return_data.notes or handover.notes
    asset = db.query(Asset).filter(Asset.id == handover.asset_id).first()
    if asset: asset.status = "available"; asset.assigned_employee_id = None; asset.condition = return_data.condition_at_return
    db.commit(); db.refresh(handover); return handover

# ============ MAINTENANCE ============
@app.post("/maintenance", response_model=MaintenanceRecordResponse)
def create_maintenance(record: MaintenanceRecordCreate, db: Session = Depends(get_db), current_user: str = Depends(verify_token)):
    db_record = MaintenanceRecord(**record.dict()); db.add(db_record); db.commit(); db.refresh(db_record)
    asset = db.query(Asset).filter(Asset.id == record.asset_id).first()
    if asset: asset.status = "repair"; db.commit()
    log_audit(db, current_user, "CREATE", "MAINTENANCE", db_record.id, asset.name if asset else str(record.asset_id), "Maintenance issue reported"); return db_record

@app.get("/maintenance", response_model=List[MaintenanceRecordResponse])
def list_maintenance(db: Session = Depends(get_db), current_user: str = Depends(verify_token), status: str = Query("open")): return db.query(MaintenanceRecord).filter(MaintenanceRecord.status == status).all()

@app.put("/maintenance/{maintenance_id}", response_model=MaintenanceRecordResponse)
def update_maintenance(maintenance_id: int, record: MaintenanceRecordUpdate, db: Session = Depends(get_db), current_user: str = Depends(verify_token)):
    db_record = db.query(MaintenanceRecord).filter(MaintenanceRecord.id == maintenance_id).first()
    if not db_record: raise HTTPException(status_code=404, detail="Maintenance record not found")
    for key, value in record.dict(exclude_unset=True).items(): setattr(db_record, key, value)
    if record.status == "completed":
        asset = db.query(Asset).filter(Asset.id == db_record.asset_id).first()
        if asset: asset.status = "available"
    db.commit(); db.refresh(db_record); return db_record

@app.get("/qr/{asset_id}")
def get_qr_code(asset_id: int, db: Session = Depends(get_db), current_user: str = Depends(verify_token)):
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset: raise HTTPException(status_code=404, detail="Asset not found")
    qr_data = f"APX://{asset.asset_id}"; return {"asset_id": asset.asset_id, "qr_code": generate_qr_code(qr_data), "data": qr_data}

# ============ USERS & PERMISSIONS ============
@app.post("/users", response_model=UserResponse)
def create_user(user: UserCreate, db: Session = Depends(get_db), current_user: str = Depends(verify_token)):
    existing_user = db.query(User).filter(User.email == current_user).first()
    if not existing_user or not existing_user.can_manage_users: raise HTTPException(status_code=403, detail="Insufficient permissions to manage users")
    if db.query(User).filter(User.email == user.email).first(): raise HTTPException(status_code=409, detail="User already exists")
    permissions = {"super_admin": True, "admin": True, "manager": True, "viewer": False}
    new_user = User(email=user.email.strip().lower(), role=user.role, can_view_dashboard=True, can_manage_assets=permissions.get(user.role, False), can_manage_employees=permissions.get(user.role, False), can_manage_handovers=permissions.get(user.role, False), can_manage_maintenance=permissions.get(user.role, False), can_view_audit_logs=(user.role == "super_admin"), can_manage_users=(user.role == "super_admin"))
    db.add(new_user); db.commit(); db.refresh(new_user); log_audit(db, current_user, "CREATE_USER", "USER", new_user.id, new_user.email, f"Created user with role {user.role}"); return new_user

@app.get("/users", response_model=List[UserResponse])
def get_users(db: Session = Depends(get_db), current_user: str = Depends(verify_token)):
    existing_user = db.query(User).filter(User.email == current_user).first()
    if not existing_user or not existing_user.can_manage_users: raise HTTPException(status_code=403, detail="Insufficient permissions")
    return db.query(User).order_by(User.created_at.desc()).all()

@app.get("/users/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db), current_user: str = Depends(verify_token)):
    existing_user = db.query(User).filter(User.email == current_user).first()
    if not existing_user or not existing_user.can_manage_users: raise HTTPException(status_code=403, detail="Insufficient permissions")
    user = db.query(User).filter(User.id == user_id).first()
    if not user: raise HTTPException(status_code=404, detail="User not found")
    return user

@app.put("/users/{user_id}", response_model=UserResponse)
def update_user(user_id: int, update_data: UserUpdate, db: Session = Depends(get_db), current_user: str = Depends(verify_token)):
    existing_user = db.query(User).filter(User.email == current_user).first()
    if not existing_user or not existing_user.can_manage_users: raise HTTPException(status_code=403, detail="Insufficient permissions")
    user = db.query(User).filter(User.id == user_id).first()
    if not user: raise HTTPException(status_code=404, detail="User not found")
    if user.email.lower() == SUPER_USER_EMAIL.lower() and update_data.is_active is False: raise HTTPException(status_code=400, detail="The super-admin account cannot be disabled")
    for field, value in update_data.dict(exclude_unset=True).items():
        if field == "is_active":
            user.is_active = value
            if value:
                user.disabled_at = None; user.disabled_reason = None
            else:
                user.disabled_at = datetime.utcnow(); user.disabled_reason = "Manually disabled by administrator"
        else: setattr(user, field, value)
    user.updated_at = datetime.utcnow(); db.commit(); db.refresh(user); log_audit(db, current_user, "UPDATE_USER", "USER", user.id, user.email, f"Updated user: {update_data.dict(exclude_unset=True)}"); return user

@app.delete("/users/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db), current_user: str = Depends(verify_token)):
    existing_user = db.query(User).filter(User.email == current_user).first()
    if not existing_user or not existing_user.can_manage_users: raise HTTPException(status_code=403, detail="Insufficient permissions")
    user = db.query(User).filter(User.id == user_id).first()
    if not user: raise HTTPException(status_code=404, detail="User not found")
    if user.email.lower() == SUPER_USER_EMAIL.lower(): raise HTTPException(status_code=400, detail="The super-admin account cannot be disabled")
    user.is_active = False; user.disabled_at = datetime.utcnow(); user.disabled_reason = "Manually disabled by administrator"; db.commit(); log_audit(db, current_user, "DELETE_USER", "USER", user.id, user.email, "User deactivated"); return {"status": "User deactivated"}

# ============ INVITES ============
@app.post("/invites", response_model=InviteResponse)
def create_invite(invite: InviteCreate, db: Session = Depends(get_db), current_user: str = Depends(verify_token)):
    existing_user = db.query(User).filter(User.email == current_user).first()
    if not existing_user or not existing_user.can_manage_users: raise HTTPException(status_code=403, detail="Insufficient permissions")
    email = invite.email.strip().lower()
    if db.query(User).filter(User.email == email).first(): raise HTTPException(status_code=409, detail="User already exists")
    if db.query(Invite).filter(Invite.email == email, Invite.is_used == False).first(): raise HTTPException(status_code=409, detail="Invite already sent to this email")
    token = secrets.token_urlsafe(32); expires_at = datetime.utcnow() + timedelta(days=7)
    new_invite = Invite(email=email, token=token, role=invite.role, invited_by=current_user, expires_at=expires_at)
    db.add(new_invite); db.commit(); db.refresh(new_invite); log_audit(db, current_user, "CREATE_INVITE", "INVITE", new_invite.id, email, f"Sent invite for role {invite.role}"); return new_invite

@app.get("/invites", response_model=List[InviteResponse])
def list_invites(db: Session = Depends(get_db), current_user: str = Depends(verify_token)):
    existing_user = db.query(User).filter(User.email == current_user).first()
    if not existing_user or not existing_user.can_manage_users: raise HTTPException(status_code=403, detail="Insufficient permissions")
    return db.query(Invite).filter(Invite.is_used == False, Invite.expires_at > datetime.utcnow()).order_by(Invite.created_at.desc()).all()

@app.get("/invites/validate/{token}")
def validate_invite(token: str, db: Session = Depends(get_db)):
    invite = db.query(Invite).filter(Invite.token == token, Invite.is_used == False).first()
    if not invite or invite.expires_at < datetime.utcnow(): raise HTTPException(status_code=400, detail="Invalid or expired invite")
    return {"valid": True, "email": invite.email, "role": invite.role}

@app.post("/invites/accept", response_model=InviteAcceptResponse)
def accept_invite(data: InviteAccept, db: Session = Depends(get_db)):
    invite = db.query(Invite).filter(Invite.token == data.token, Invite.is_used == False).first()
    if not invite or invite.expires_at < datetime.utcnow(): raise HTTPException(status_code=400, detail="Invalid or expired invite")
    if len(data.password) < 8: raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
    user = User(email=invite.email, password_hash=hash_password(data.password), role=invite.role, can_view_dashboard=True, can_manage_assets=invite.role != "viewer", can_manage_employees=invite.role in ["super_admin", "admin"], can_manage_handovers=invite.role != "viewer", can_manage_maintenance=invite.role != "viewer", can_view_audit_logs=invite.role == "super_admin", can_manage_users=invite.role == "super_admin", last_login=datetime.utcnow())
    db.add(user); invite.is_used = True; invite.accepted_at = datetime.utcnow(); db.commit(); db.refresh(user)
    token = create_access_token(data={"sub": invite.email}, expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    return {"status": "accepted", "access_token": token, "token_type": "bearer", "email": invite.email}

@app.get("/audit-logs", response_model=List[AuditLogResponse])
def get_audit_logs(db: Session = Depends(get_db), current_user: str = Depends(verify_token)):
    existing_user = db.query(User).filter(User.email == current_user).first()
    if not existing_user or not existing_user.can_view_audit_logs: raise HTTPException(status_code=403, detail="Insufficient permissions")
    return db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(200).all()

@app.get("/users/inactive", response_model=List[UserResponse])
def get_inactive_users(db: Session = Depends(get_db), current_user: str = Depends(verify_token)):
    existing_user = db.query(User).filter(User.email == current_user).first()
    if not existing_user or not existing_user.can_manage_users: raise HTTPException(status_code=403, detail="Insufficient permissions")
    return db.query(User).filter(User.is_active == False).order_by(User.disabled_at.desc()).all()
