from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    assets = relationship("Asset", back_populates="category")


class Asset(Base):
    __tablename__ = "assets"

    id = Column(Integer, primary_key=True, index=True)
    asset_tag = Column(String, unique=True, index=True, nullable=True)
    qr_token = Column(String, unique=True, index=True, nullable=True)
    name = Column(String, index=True)
    description = Column(String)
    category_id = Column(Integer, ForeignKey("categories.id"))
    serial_number = Column(String, unique=True, index=True)
    purchase_date = Column(DateTime)
    value = Column(Float)
    location = Column(String, default="APEX HUB")
    status = Column(String, default="active")
    lifecycle_status = Column(String, default="In Stock", index=True)
    health_status = Column(String, default="Healthy", index=True)
    warranty_provider = Column(String, nullable=True)
    warranty_start_date = Column(DateTime, nullable=True)
    warranty_expiry_date = Column(DateTime, nullable=True, index=True)
    warranty_reference = Column(String, nullable=True)
    warranty_notes = Column(Text, nullable=True)
    warranty_status = Column(String, default="Unknown", index=True)
    expected_replacement_date = Column(DateTime, nullable=True, index=True)
    replacement_priority = Column(String, default="Normal", index=True)
    replacement_reason = Column(String, nullable=True)
    estimated_replacement_cost = Column(Float, default=0.0)
    replacement_notes = Column(Text, nullable=True)
    assigned_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    category = relationship("Category", back_populates="assets")
    assigned_user = relationship("User", back_populates="assigned_assets", foreign_keys=[assigned_user_id])
    assignments = relationship("AssetAssignment", back_populates="asset", cascade="all, delete-orphan")
    lifecycle_events = relationship("AssetLifecycleEvent", back_populates="asset", cascade="all, delete-orphan")
    maintenance_records = relationship(
        "MaintenanceRecord",
        back_populates="asset",
        cascade="all, delete-orphan",
    )


class AssetLifecycleEvent(Base):
    __tablename__ = "asset_lifecycle_events"

    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False, index=True)
    from_status = Column(String, nullable=True)
    to_status = Column(String, nullable=False, index=True)
    reason = Column(Text, nullable=True)
    changed_by = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    asset = relationship("Asset", back_populates="lifecycle_events")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    full_name = Column(String, index=True)
    phone = Column(String, nullable=True)
    bio = Column(Text, nullable=True)
    profile_image_url = Column(String, nullable=True)
    membership_tier = Column(String, default="bronze")
    role = Column(String, default="member")
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    location = Column(String, default="APEX HUB")
    bike_interests = Column(Text, nullable=True)
    password_hash = Column(String, nullable=True)
    invite_token = Column(String, unique=True, nullable=True)
    invite_expires_at = Column(DateTime, nullable=True)
    invited_at = Column(DateTime, nullable=True)
    join_date = Column(DateTime, default=datetime.utcnow, index=True)
    last_login = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    assigned_assets = relationship(
        "Asset",
        back_populates="assigned_user",
        foreign_keys="Asset.assigned_user_id",
    )


class AssetAssignment(Base):
    __tablename__ = "asset_assignments"

    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    action = Column(String, default="ASSIGNED")
    location = Column(String, default="APEX HUB")
    assigned_at = Column(DateTime, default=datetime.utcnow, index=True)
    assigned_by = Column(String, nullable=True)
    notes = Column(Text, nullable=True)

    asset = relationship("Asset", back_populates="assignments")
    user = relationship("User", foreign_keys=[user_id])


class MaintenanceRecord(Base):
    __tablename__ = "maintenance_records"

    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False, index=True)

    maintenance_type = Column(String, default="Service", index=True)
    status = Column(String, default="Scheduled", index=True)

    scheduled_date = Column(DateTime, nullable=True, index=True)
    completed_date = Column(DateTime, nullable=True)
    next_service_date = Column(DateTime, nullable=True, index=True)

    assigned_user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)

    cost = Column(Float, default=0.0)
    notes = Column(Text, nullable=True)

    created_by = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    asset = relationship("Asset", back_populates="maintenance_records")
    assigned_user = relationship("User", foreign_keys=[assigned_user_id])


class AssetStockMovement(Base):
    __tablename__ = "asset_stock_movements"

    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False, index=True)
    action = Column(String, nullable=False, index=True)
    from_location = Column(String, nullable=True)
    to_location = Column(String, nullable=True)
    from_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    to_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    performed_by = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    asset = relationship("Asset", foreign_keys=[asset_id])
    from_user = relationship("User", foreign_keys=[from_user_id])
    to_user = relationship("User", foreign_keys=[to_user_id])


class AssetIssue(Base):
    __tablename__ = "asset_issues"

    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False, index=True)
    reported_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    assigned_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    priority = Column(String, default="Normal", index=True)
    status = Column(String, default="Reported", index=True)
    resolution = Column(Text, nullable=True)
    resolution_cost = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)

    asset = relationship("Asset", foreign_keys=[asset_id])
    reported_by = relationship("User", foreign_keys=[reported_by_user_id])
    assigned_user = relationship("User", foreign_keys=[assigned_user_id])


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    notification_type = Column(String, default="Info", index=True)
    resource_type = Column(String, nullable=True)
    resource_id = Column(Integer, nullable=True)
    is_read = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    user = relationship("User", foreign_keys=[user_id])


class SystemSetting(Base):
    __tablename__ = "system_settings"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, nullable=False, index=True)
    value = Column(Text, nullable=True)
    updated_by = Column(String, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Supplier(Base):
    __tablename__ = "suppliers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False, index=True)
    contact_name = Column(String, nullable=True)
    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    website = Column(String, nullable=True)
    address = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"

    id = Column(Integer, primary_key=True, index=True)
    order_number = Column(String, unique=True, nullable=False, index=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False, index=True)
    status = Column(String, default="Draft", index=True)
    order_date = Column(DateTime, nullable=True)
    expected_date = Column(DateTime, nullable=True)
    received_date = Column(DateTime, nullable=True)
    total_value = Column(Float, default=0.0)
    notes = Column(Text, nullable=True)
    created_by = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    supplier = relationship("Supplier", foreign_keys=[supplier_id])
    items = relationship("PurchaseOrderItem", back_populates="purchase_order", cascade="all, delete-orphan")


class PurchaseOrderItem(Base):
    __tablename__ = "purchase_order_items"

    id = Column(Integer, primary_key=True, index=True)
    purchase_order_id = Column(Integer, ForeignKey("purchase_orders.id"), nullable=False, index=True)
    description = Column(String, nullable=False)
    quantity = Column(Integer, default=1)
    unit_cost = Column(Float, default=0.0)
    received_quantity = Column(Integer, default=0)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=True, index=True)

    purchase_order = relationship("PurchaseOrder", back_populates="items")
    asset = relationship("Asset", foreign_keys=[asset_id])


class AssetDocument(Base):
    __tablename__ = "asset_documents"

    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False, index=True)
    title = Column(String, nullable=False)
    document_type = Column(String, default="Other", index=True)
    reference = Column(String, nullable=True)
    issued_date = Column(DateTime, nullable=True)
    expiry_date = Column(DateTime, nullable=True, index=True)
    document_url = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    created_by = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    asset = relationship("Asset", foreign_keys=[asset_id])


class ComplianceRecord(Base):
    __tablename__ = "compliance_records"

    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False, index=True)
    compliance_type = Column(String, default="Inspection", index=True)
    status = Column(String, default="Required", index=True)
    due_date = Column(DateTime, nullable=True, index=True)
    completed_date = Column(DateTime, nullable=True)
    reference = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    created_by = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    asset = relationship("Asset", foreign_keys=[asset_id])


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, index=True)
    action = Column(String, index=True)
    resource_type = Column(String)
    resource_id = Column(Integer, nullable=True)
    resource_name = Column(String)
    details = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class ExpenseRecord(Base):
    __tablename__ = "expense_records"

    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=True, index=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=True, index=True)
    category = Column(String, default="Other", index=True)
    description = Column(String, nullable=False)
    amount = Column(Float, default=0.0)
    expense_date = Column(DateTime, default=datetime.utcnow, index=True)
    reference = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    created_by = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    asset = relationship("Asset", foreign_keys=[asset_id])
    supplier = relationship("Supplier", foreign_keys=[supplier_id])


class Budget(Base):
    __tablename__ = "budgets"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    category = Column(String, default="General", index=True)
    year = Column(Integer, nullable=False, index=True)
    month = Column(Integer, nullable=True, index=True)
    amount = Column(Float, default=0.0)
    notes = Column(Text, nullable=True)
    created_by = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
