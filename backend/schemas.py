from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from models import CaseStatus, DocStatus, DocType, AssetType

# --- Heir Schemas ---
class HeirBase(BaseModel):
    name: str
    relationship: Optional[str] = None # Coincide con relationship_degree en modelo
    share_percentage: float
    pre_existing_wealth: float = 0.0
    tax_percentage: Optional[float] = None
    fiscal_residence: Optional[str] = None

class HeirCreate(HeirBase):
    pass

class Heir(HeirBase):
    id: int
    case_id: int
    relationship_degree: Optional[str] = None # Added to map from DB model

    class Config:
        from_attributes = True

# --- Asset Schemas ---
class AssetBase(BaseModel):
    type: str # Changed from AssetType enum to str for flexibility, or keep AssetType if it covers REAL_ESTATE
    value: float
    is_ganancial: bool = False
    is_debt: bool = False
    is_funeral_expense: bool = False
    description: Optional[str] = None
    cadastral_reference: Optional[str] = None
    address: Optional[str] = None
    surface: Optional[float] = None
    usage: Optional[str] = None
    reference_value: Optional[float] = 0.0

class AssetCreate(AssetBase):
    pass

class Asset(AssetBase):
    id: int
    case_id: int

    class Config:
        from_attributes = True

# --- Doc Schemas ---
class DocBase(BaseModel):
    type: DocType = DocType.OTHER
    file_url: str
    status: DocStatus = DocStatus.PENDING
    is_verified: bool = False

class DocCreate(DocBase):
    pass

class Doc(DocBase):
    id: int
    case_id: int

    class Config:
        from_attributes = True

class DocUploadResponse(BaseModel):
    document: Doc
    assets_created: int = 0
    cadastral_references_found: int = 0
    message: str = ""

    class Config:
        from_attributes = True

# --- Case Schemas ---
class CaseBase(BaseModel):
    user_id: str
    status: CaseStatus = CaseStatus.PENDING
    deadline: Optional[datetime] = None
    has_will: bool = False
    deceased_name: Optional[str] = None
    deceased_dni: Optional[str] = None
    date_of_death: Optional[datetime] = None

class CaseCreate(CaseBase):
    pass

class Case(CaseBase):
    id: int
    created_at: datetime
    heirs: List[Heir] = []
    assets: List[Asset] = []
    docs: List[Doc] = []

    class Config:
        from_attributes = True

# --- Auth Schemas ---
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

class UserCreate(BaseModel):
    email: str
    password: str

class User(BaseModel):
    id: int
    email: str
    is_active: bool

    class Config:
        from_attributes = True

# --- Calculation Schemas ---
class CalculationResult(BaseModel):
    total_assets: float
    total_debts: float
    net_estate: float # Caudal Relicto
    household_goods: float # Ajuar (3%)
    taxable_base: float # Base Imponible Total

class HeirDistribution(BaseModel):
    heir_id: int
    name: str
    relationship: str
    share_percentage: float
    quota_value: float
    tax_base: float
    # Tax Fields
    reductions: float = 0.0
    tax_quota: float = 0.0
    total_to_pay: float = 0.0

class DistributionResult(BaseModel):
    estate_summary: CalculationResult
    heirs_distribution: List[HeirDistribution]
    total_distributed: float
    remainder: float
