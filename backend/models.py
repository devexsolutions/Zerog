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
    user_id = Column(String, index=True)
    status = Column(Enum(CaseStatus), default=CaseStatus.PENDING)
    deadline = Column(DateTime)
    deceased_name = Column(String, nullable=True)
    deceased_dni = Column(String, nullable=True)
    date_of_death = Column(DateTime, nullable=True)
    has_will = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    heirs = relationship("Heir", back_populates="case", cascade="all, delete-orphan")
    assets = relationship("Asset", back_populates="case", cascade="all, delete-orphan")
    docs = relationship("Doc", back_populates="case", cascade="all, delete-orphan")

class Heir(Base):
    __tablename__ = "heirs"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"))
    name = Column(String)
    nif = Column(String, nullable=True)          # NIF del heredero
    age = Column(Integer, nullable=True)          # Edad (Grupo I si < 21)
    relationship_degree = Column(String)          # Grado de parentesco
    fiscal_residence = Column(String, nullable=True)  # CCAA de residencia fiscal

    # Distribution
    share_percentage = Column(Float, default=0.0)

    # Tax Calculation
    tax_percentage = Column(Float, nullable=True)
    pre_existing_wealth = Column(Float, default=0.0)

    case = relationship("Case", back_populates="heirs")

class Asset(Base):
    __tablename__ = "assets"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"))
    type = Column(String)
    value = Column(Float)
    is_ganancial = Column(Boolean, default=False)
    is_debt = Column(Boolean, default=False)
    is_funeral_expense = Column(Boolean, default=False)
    description = Column(String, nullable=True)

    # Catastro fields
    cadastral_reference = Column(String, nullable=True)
    address = Column(String, nullable=True)
    surface = Column(Float, nullable=True)
    usage = Column(String, nullable=True)
    reference_value = Column(Float, nullable=True, default=0.0)

    case = relationship("Case", back_populates="assets")

class Doc(Base):
    __tablename__ = "docs"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"))
    type = Column(Enum(DocType), default=DocType.OTHER)
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
