from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Float, DateTime, Enum
from sqlalchemy.orm import relationship
import enum
from database import Base
from datetime import datetime

class CaseStatus(str, enum.Enum):
    PENDING = "PENDIENTE"
    OPEN = "ABIERTO"
    CLOSED = "CERRADO"

class DocStatus(str, enum.Enum):
    PENDING = "PENDIENTE"
    UPLOADED = "CARGADO"
    VALIDATED = "VALIDADO"
    REJECTED = "RECHAZADO"

class AssetType(str, enum.Enum):
    REAL_ESTATE = "inmueble"
    BANK_ACCOUNT = "cuenta"
    VEHICLE = "vehiculo"
    INSURANCE = "seguro"
    OTHER = "otro"

class DocType(str, enum.Enum):
    DNI = "DNI"
    DEATH_CERTIFICATE = "certificado_defuncion"
    LAST_WILL = "ultimas_voluntades"
    TESTAMENT = "testamento"
    INSURANCE = "seguros"
    BANK_CERTIFICATE = "certificado_bancario"
    DEED = "escritura"
    OTHER = "otro"
    # Legacy/Frontend compatibility
    BANCO = "banco"
    ESCRITURAS = "escrituras"

class Case(Base):
    __tablename__ = "cases"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True) # Auth0/Clerk ID
    status = Column(Enum(CaseStatus), default=CaseStatus.PENDING)
    deadline = Column(DateTime)
    deceased_name = Column(String, nullable=True) # Nombre del fallecido
    deceased_dni = Column(String, nullable=True) # DNI del fallecido
    date_of_death = Column(DateTime, nullable=True) # Fecha de defunción para plazos
    has_will = Column(Boolean, default=False) # ¿Tiene testamento?
    created_at = Column(DateTime, default=datetime.utcnow)

    heirs = relationship("Heir", back_populates="case")
    assets = relationship("Asset", back_populates="case")
    docs = relationship("Doc", back_populates="case")

class Heir(Base):
    __tablename__ = "heirs"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"))
    name = Column(String)
    relationship_degree = Column(String) # Grado de parentesco
    fiscal_residence = Column(String, nullable=True) # Residencia fiscal (CCAA)
    
    # Distribution
    share_percentage = Column(Float, default=0.0) # Porcentaje de participación (0-100)
    
    # Tax Calculation (Optional for now)
    tax_percentage = Column(Float, nullable=True) # Tipo impositivo aplicable
    pre_existing_wealth = Column(Float, default=0.0)

    case = relationship("Case", back_populates="heirs")

class Asset(Base):
    __tablename__ = "assets"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"))
    type = Column(String) # Changed from Enum to String for flexibility
    value = Column(Float)
    is_ganancial = Column(Boolean, default=False)
    is_debt = Column(Boolean, default=False) # ¿Es deuda/pasivo?
    is_funeral_expense = Column(Boolean, default=False) # ¿Es gasto de sepelio?
    description = Column(String, nullable=True)
    
    # Catastro fields
    cadastral_reference = Column(String, nullable=True)
    address = Column(String, nullable=True)
    surface = Column(Float, nullable=True)
    usage = Column(String, nullable=True)
    reference_value = Column(Float, nullable=True, default=0.0) # Valor de Referencia de Catastro

    case = relationship("Case", back_populates="assets")

class Doc(Base):
    __tablename__ = "docs"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"))
    type = Column(Enum(DocType), default=DocType.OTHER) # Tipo de documento para checklist
    file_url = Column(String)
    status = Column(Enum(DocStatus), default=DocStatus.PENDING)
    is_verified = Column(Boolean, default=False)
    
    case = relationship("Case", back_populates="docs")

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    
    # Para SaaS Multi-tenant, podríamos tener un tenant_id
    # Por ahora, user_id en Case es el link.

