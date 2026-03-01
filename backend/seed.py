import sys
import os

from sqlalchemy.orm import Session
from .database import SessionLocal, engine
from .models import Base, User, Case, Heir, Asset, CaseStatus, AssetType
from .auth import get_password_hash
from datetime import datetime, timedelta

def seed_data():
    db = SessionLocal()
    try:
        # 1. Create User
        user_email = "admin@zerog.com"
        user_password = "password123"
        user = db.query(User).filter(User.email == user_email).first()
        
        if not user:
            print(f"Creating user: {user_email}")
            hashed_password = get_password_hash(user_password)
            user = User(email=user_email, hashed_password=hashed_password)
            db.add(user)
            db.commit()
            db.refresh(user)
        else:
            print(f"User already exists: {user_email}")

        # 2. Create Case
        # We assume user.id is an integer but stored as string in Case.user_id
        case = db.query(Case).filter(Case.user_id == str(user.id), Case.status == CaseStatus.OPEN).first()
        
        if not case:
            print("Creating demo case...")
            case = Case(
                user_id=str(user.id),
                status=CaseStatus.OPEN,
                deadline=datetime.now() + timedelta(days=180),
                date_of_death=datetime.now() - timedelta(days=45),
                deceased_name="Juan Pérez García",
                deceased_dni="12345678Z",
                has_will=True
            )
            db.add(case)
            db.commit()
            db.refresh(case)
            
            # 3. Create Heirs
            print("Adding heirs...")
            heirs = [
                Heir(case_id=case.id, name="María López (Cónyuge)", relationship_degree="Cónyuge", share_percentage=33.3333, fiscal_residence="Madrid"),
                Heir(case_id=case.id, name="Pedro Pérez (Hijo)", relationship_degree="Hijo", share_percentage=33.3333, fiscal_residence="Madrid"),
                Heir(case_id=case.id, name="Ana Pérez (Hija)", relationship_degree="Hijo", share_percentage=33.3333, fiscal_residence="Madrid")
            ]
            db.add_all(heirs)

            # 4. Create Assets
            print("Adding assets...")
            assets = [
                Asset(case_id=case.id, type=AssetType.REAL_ESTATE.value, description="Vivienda Habitual Madrid", value=350000.0, is_ganancial=True, reference_value=300000.0),
                Asset(case_id=case.id, type=AssetType.BANK_ACCOUNT.value, description="Cuenta Corriente BBVA", value=120000.0, is_ganancial=True),
                Asset(case_id=case.id, type=AssetType.VEHICLE.value, description="Coche Toyota", value=15000.0, is_ganancial=False),
                Asset(case_id=case.id, type=AssetType.OTHER.value, description="Gastos Sepelio", value=5000.0, is_debt=False, is_funeral_expense=True),
                Asset(case_id=case.id, type=AssetType.OTHER.value, description="Deuda Tarjeta", value=2500.0, is_debt=True)
            ]
            db.add_all(assets)
            
            db.commit()
            print("Case populated successfully!")
            
        else:
             print("Open case already exists for user.")

        print("Seed completed successfully!")
        print(f"Login with: {user_email} / {user_password}")

    except Exception as e:
        print(f"Error seeding data: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    # Ensure tables exist
    Base.metadata.create_all(bind=engine)
    seed_data()
