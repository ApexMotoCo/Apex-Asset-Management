from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional

class CategoryCreate(BaseModel):
    name: str
    description: Optional[str] = None

class CategoryResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    created_at: datetime
    class Config:
        from_attributes = True

class AssetCreate(BaseModel):
    name: str
    description: Optional[str] = None
    category_id: int
    serial_number: str
    purchase_date: datetime
    value: float
    location: str = "APEX HUB"
    status: str = "active"
    lifecycle_status: str = "In Stock"
    health_status: str = "Healthy"
    warranty_provider: Optional[str] = None
    warranty_start_date: Optional[datetime] = None
    warranty_expiry_date: Optional[datetime] = None
    warranty_reference: Optional[str] = None
    warranty_notes: Optional[str] = None
    expected_replacement_date: Optional[datetime] = None
    replacement_priority: str = "Normal"
    replacement_reason: Optional[str] = None
    estimated_replacement_cost: float = 0.0
    replacement_notes: Optional[str] = None

class AssetUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category_id: Optional[int] = None
    serial_number: Optional[str] = None
    purchase_date: Optional[datetime] = None
    value: Optional[float] = None
    location: Optional[str] = None
    status: Optional[str] = None
    lifecycle_status: Optional[str] = None
    health_status: Optional[str] = None
    warranty_provider: Optional[str] = None
    warranty_start_date: Optional[datetime] = None
    warranty_expiry_date: Optional[datetime] = None
    warranty_reference: Optional[str] = None
    warranty_notes: Optional[str] = None
    expected_replacement_date: Optional[datetime] = None
    replacement_priority: Optional[str] = None
    replacement_reason: Optional[str] = None
    estimated_replacement_cost: Optional[float] = None
    replacement_notes: Optional[str] = None
    assigned_user_id: Optional[int] = None

class UserSummary(BaseModel):
    id: int
    email: str
    full_name: str
    role: str
    is_active: bool
    location: Optional[str]
    class Config:
        from_attributes = True

class AssetResponse(BaseModel):
    id: int
    asset_tag: str
    qr_token: str
    name: str
    description: Optional[str]
    category_id: int
    serial_number: str
    purchase_date: datetime
    value: float
    location: str
    status: str
    lifecycle_status: str
    health_status: str
    warranty_provider: Optional[str]
    warranty_start_date: Optional[datetime]
    warranty_expiry_date: Optional[datetime]
    warranty_reference: Optional[str]
    warranty_notes: Optional[str]
    warranty_status: str
    expected_replacement_date: Optional[datetime]
    replacement_priority: str
    replacement_reason: Optional[str]
    estimated_replacement_cost: float
    replacement_notes: Optional[str]
    assigned_user_id: Optional[int]
    created_at: datetime
    updated_at: datetime
    category: CategoryResponse
    assigned_user: Optional[UserSummary]
    class Config:
        from_attributes = True

class AssignmentResponse(BaseModel):
    id: int
    asset_id: int
    user_id: Optional[int]
    action: str
    location: str
    assigned_at: datetime
    assigned_by: Optional[str]
    notes: Optional[str]
    user: Optional[UserSummary]
    class Config:
        from_attributes = True

class AssignAssetRequest(BaseModel):
    user_id: Optional[int] = None
    location: str = "APEX HUB"
    notes: Optional[str] = None

class AuditLogResponse(BaseModel):
    id: int
    email: str
    action: str
    resource_type: str
    resource_id: Optional[int]
    resource_name: str
    details: str
    created_at: datetime
    class Config:
        from_attributes = True

class UserCreate(BaseModel):
    email: EmailStr
    full_name: str
    phone: Optional[str] = None
    location: str = "APEX HUB"
    bike_interests: Optional[str] = None
    bio: Optional[str] = None
    role: str = "member"

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    bio: Optional[str] = None
    profile_image_url: Optional[str] = None
    location: Optional[str] = None
    bike_interests: Optional[str] = None
    membership_tier: Optional[str] = None

class UserAdminUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    bio: Optional[str] = None
    profile_image_url: Optional[str] = None
    location: Optional[str] = None
    bike_interests: Optional[str] = None
    membership_tier: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None

class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    phone: Optional[str]
    bio: Optional[str]
    profile_image_url: Optional[str]
    membership_tier: str
    role: str
    is_active: bool
    is_verified: bool
    location: Optional[str]
    bike_interests: Optional[str]
    join_date: datetime
    last_login: Optional[datetime]
    invited_at: Optional[datetime]
    invite_expires_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True

class UserPublicResponse(BaseModel):
    id: int
    full_name: str
    bio: Optional[str]
    profile_image_url: Optional[str]
    membership_tier: str
    location: Optional[str]
    bike_interests: Optional[str]
    join_date: datetime
    class Config:
        from_attributes = True

class LoginRequest(BaseModel):
    email: EmailStr
    password: Optional[str] = None

class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    email: str
    role: str

class AcceptInviteRequest(BaseModel):
    token: str
    password: str

class InviteResponse(BaseModel):
    message: str
    email: str
    invite_url: Optional[str] = None


class SupplierCreate(BaseModel):
    name: str
    contact_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    address: Optional[str] = None
    notes: Optional[str] = None
    is_active: bool = True

class SupplierUpdate(BaseModel):
    name: Optional[str] = None
    contact_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    address: Optional[str] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None

class PurchaseOrderCreate(BaseModel):
    order_number: str
    supplier_id: int
    status: str = "Draft"
    order_date: Optional[datetime] = None
    expected_date: Optional[datetime] = None
    received_date: Optional[datetime] = None
    notes: Optional[str] = None
    items: list[dict] = []

class PurchaseOrderUpdate(BaseModel):
    status: Optional[str] = None
    expected_date: Optional[datetime] = None
    received_date: Optional[datetime] = None
    notes: Optional[str] = None


class AssetDocumentCreate(BaseModel):
    asset_id: int
    title: str
    document_type: str = "Other"
    reference: Optional[str] = None
    issued_date: Optional[datetime] = None
    expiry_date: Optional[datetime] = None
    document_url: Optional[str] = None
    notes: Optional[str] = None

class AssetDocumentUpdate(BaseModel):
    title: Optional[str] = None
    document_type: Optional[str] = None
    reference: Optional[str] = None
    issued_date: Optional[datetime] = None
    expiry_date: Optional[datetime] = None
    document_url: Optional[str] = None
    notes: Optional[str] = None

class ComplianceRecordCreate(BaseModel):
    asset_id: int
    compliance_type: str = "Inspection"
    status: str = "Required"
    due_date: Optional[datetime] = None
    completed_date: Optional[datetime] = None
    reference: Optional[str] = None
    notes: Optional[str] = None

class ComplianceRecordUpdate(BaseModel):
    compliance_type: Optional[str] = None
    status: Optional[str] = None
    due_date: Optional[datetime] = None
    completed_date: Optional[datetime] = None
    reference: Optional[str] = None
    notes: Optional[str] = None


class ExpenseCreate(BaseModel):
    asset_id: Optional[int] = None
    supplier_id: Optional[int] = None
    category: str = "Other"
    description: str
    amount: float = Field(default=0.0, ge=0)
    expense_date: Optional[datetime] = None
    reference: Optional[str] = None
    notes: Optional[str] = None

class ExpenseUpdate(BaseModel):
    asset_id: Optional[int] = None
    supplier_id: Optional[int] = None
    category: Optional[str] = None
    description: Optional[str] = None
    amount: Optional[float] = Field(default=None, ge=0)
    expense_date: Optional[datetime] = None
    reference: Optional[str] = None
    notes: Optional[str] = None

class BudgetCreate(BaseModel):
    name: str
    category: str = "General"
    year: int
    month: Optional[int] = Field(default=None, ge=1, le=12)
    amount: float = Field(default=0.0, ge=0)
    notes: Optional[str] = None

class BudgetUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    year: Optional[int] = None
    month: Optional[int] = Field(default=None, ge=1, le=12)
    amount: Optional[float] = Field(default=None, ge=0)
    notes: Optional[str] = None
