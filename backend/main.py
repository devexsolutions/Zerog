import os
import shutil
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form, status
from fastapi.responses import StreamingResponse
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timedelta

from . import models, schemas
from .database import engine, get_db
from .services.ocr import analyze_document
from .services import calculator, distribution, document_generator, catastro, aeat
from . import auth

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Antigravity API", description="Inheritance Management Module MVP")

# Mount uploads directory to serve files
if not os.path.exists("backend/uploads"):
    os.makedirs("backend/uploads")
app.mount("/uploads", StaticFiles(directory="backend/uploads"), name="uploads")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # For development, allow all. In prod, restrict to frontend domain.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Welcome to Antigravity API"}

# --- Auth ---

@app.post("/auth/register", response_model=schemas.User)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_password = auth.get_password_hash(user.password)
    db_user = models.User(email=user.email, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.post("/auth/token", response_model=schemas.Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/auth/me", response_model=schemas.User)
def read_users_me(current_user: models.User = Depends(auth.get_current_user)):
    return current_user

# --- Cases ---

@app.post("/cases/", response_model=schemas.Case)
def create_case(case: schemas.CaseCreate, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    # Override user_id with logged in user
    db_case = models.Case(
        user_id=str(current_user.id), 
        status=case.status, 
        deadline=case.deadline,
        date_of_death=case.date_of_death,
        has_will=case.has_will
    )
    db.add(db_case)
    db.commit()
    db.refresh(db_case)
    return db_case

@app.get("/cases/", response_model=List[schemas.Case])
def read_cases(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    # Filter by user_id for Multi-tenancy
    cases = db.query(models.Case).filter(models.Case.user_id == str(current_user.id)).offset(skip).limit(limit).all()
    return cases

@app.get("/cases/{case_id}", response_model=schemas.Case)
def read_case(case_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    db_case = db.query(models.Case).filter(models.Case.id == case_id, models.Case.user_id == str(current_user.id)).first()
    if db_case is None:
        raise HTTPException(status_code=404, detail="Case not found")
    return db_case

# --- Heirs ---

@app.post("/cases/{case_id}/heirs/", response_model=schemas.Heir)
def create_heir_for_case(case_id: int, heir: schemas.HeirCreate, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    db_case = db.query(models.Case).filter(models.Case.id == case_id, models.Case.user_id == str(current_user.id)).first()
    if not db_case:
         raise HTTPException(status_code=404, detail="Case not found")
    db_heir = models.Heir(**heir.dict(), case_id=case_id)
    db.add(db_heir)
    db.commit()
    db.refresh(db_heir)
    return db_heir

# --- Assets ---

@app.post("/cases/{case_id}/assets/", response_model=schemas.Asset)
def create_asset_for_case(case_id: int, asset: schemas.AssetCreate, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    db_case = db.query(models.Case).filter(models.Case.id == case_id, models.Case.user_id == str(current_user.id)).first()
    if db_case is None:
        raise HTTPException(status_code=404, detail="Case not found")
    
    db_asset = models.Asset(
        **asset.dict(), 
        case_id=case_id
    )
    db.add(db_asset)
    db.commit()
    db.refresh(db_asset)
    return db_asset

@app.get("/cases/{case_id}/assets/", response_model=List[schemas.Asset])
def read_assets(case_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    db_case = db.query(models.Case).filter(models.Case.id == case_id, models.Case.user_id == str(current_user.id)).first()
    if db_case is None:
        raise HTTPException(status_code=404, detail="Case not found")
    return db_case.assets

# --- Docs ---
@app.post("/cases/{case_id}/upload-doc/", response_model=schemas.Doc)
def upload_doc_for_case(
    case_id: int, 
    file: UploadFile = File(...), 
    type: str = Form(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    db_case = db.query(models.Case).filter(models.Case.id == case_id, models.Case.user_id == str(current_user.id)).first()
    if not db_case:
        raise HTTPException(status_code=404, detail="Case not found")

    # Guardar archivo localmente
    file_location = f"backend/uploads/{case_id}_{file.filename}"
    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # URL accesible (en prod sería S3 URL)
    file_url = f"http://localhost:8000/uploads/{case_id}_{file.filename}"

    # Crear registro en BD
    db_doc = models.Doc(
        case_id=case_id,
        type=type,
        file_url=file_url,
        status=models.DocStatus.UPLOADED, # Se asume cargado al subir
        is_verified=False
    )
    db.add(db_doc)
    db.commit()
    db.refresh(db_doc)

    # Simular Extracción OCR
    # Para el MVP, ejecutamos OCR en todos los docs subidos para ver logs, pero solo procesamos lógica específica en algunos
    try:
        # Pasamos la ruta local del archivo (file_location) en lugar de la URL para que Tesseract pueda leerlo
        extracted = analyze_document(file_location, type)
        
        if type == models.DocType.DEATH_CERTIFICATE:
            if "date_of_death" in extracted:
                if not db_case.date_of_death:
                    db_case.date_of_death = datetime.fromisoformat(extracted["date_of_death"])
                    print(f"OCR: Fecha de defunción actualizada para el caso {case_id}")
            
            if "deceased_name" in extracted:
                if not db_case.deceased_name:
                    db_case.deceased_name = extracted["deceased_name"]
                    print(f"OCR: Nombre del fallecido actualizado: {extracted['deceased_name']}")
            
            if "dni" in extracted:
                if not db_case.deceased_dni:
                    db_case.deceased_dni = extracted["dni"]
                    print(f"OCR: DNI del fallecido actualizado: {extracted['dni']}")

            db.commit()
        
        elif type == models.DocType.DNI:
            if "dni" in extracted:
                if not db_case.deceased_dni:
                    db_case.deceased_dni = extracted["dni"]
                    db.commit()
                    print(f"OCR: DNI del fallecido actualizado desde documento DNI: {extracted['dni']}")
        
        elif type == models.DocType.BANK_CERTIFICATE:
            # Si encontramos IBAN y saldo, creamos un Asset automáticamente
            if "iban" in extracted and "amount" in extracted:
                description = f"Cuenta extraída OCR (IBAN: {extracted['iban']})"
                # Verificar si ya existe este asset para no duplicar
                existing_asset = db.query(models.Asset).filter(
                    models.Asset.case_id == case_id, 
                    models.Asset.description.contains(extracted['iban'])
                ).first()
                
                if not existing_asset:
                    new_asset = models.Asset(
                        case_id=case_id,
                        type=models.AssetType.BANK_ACCOUNT,
                        value=extracted["amount"],
                        description=description,
                        is_ganancial=False, # Por defecto
                        is_debt=False
                    )
                    db.add(new_asset)
                    db.commit()
                    print(f"OCR: Activo bancario creado automáticamente: {description} - {extracted['amount']}€")

    except Exception as e:
        print(f"Error procesando OCR: {e}")

    return db_doc

# --- Advanced Features ---

@app.get("/cases/{case_id}/checklist", response_model=List[dict])
def get_case_checklist(case_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    db_case = db.query(models.Case).filter(models.Case.id == case_id, models.Case.user_id == str(current_user.id)).first()
    if not db_case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    # Lógica de Checklist Dinámica
    required_docs = [
        {"type": models.DocType.DNI, "label": "DNI del Fallecido", "required": True},
        {"type": models.DocType.DEATH_CERTIFICATE, "label": "Certificado de Defunción", "required": True},
        {"type": models.DocType.LAST_WILL, "label": "Certificado de Últimas Voluntades", "required": True},
        {"type": models.DocType.INSURANCE, "label": "Certificado de Seguros", "required": True},
        {"type": models.DocType.BANK_CERTIFICATE, "label": "Certificados Bancarios", "required": True},
    ]

    if db_case.has_will:
        required_docs.append({"type": models.DocType.TESTAMENT, "label": "Copia Autorizada del Testamento", "required": True})
    else:
        required_docs.append({"type": models.DocType.DEED, "label": "Declaración de Herederos (Notarial)", "required": True})

    # Verificar estado actual
    checklist_status = []
    existing_docs = {doc.type: doc for doc in db_case.docs}

    for req in required_docs:
        doc = existing_docs.get(req["type"])
        status = doc.status if doc else "MISSING"
        checklist_status.append({
            "type": req["type"],
            "label": req["label"],
            "status": status,
            "file_url": doc.file_url if doc else None
        })
    
    return checklist_status

@app.get("/cases/{case_id}/calculate", response_model=schemas.CalculationResult)
def calculate_inheritance(case_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    db_case = db.query(models.Case).filter(models.Case.id == case_id, models.Case.user_id == str(current_user.id)).first()
    if not db_case:
        raise HTTPException(status_code=404, detail="Case not found")

    # Usar el motor de cálculo
    result = calculator.calculate_estate(db_case)
    return result

@app.get("/cases/{case_id}/distribution", response_model=schemas.DistributionResult)
def calculate_distribution(case_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    db_case = db.query(models.Case).filter(models.Case.id == case_id, models.Case.user_id == str(current_user.id)).first()
    if not db_case:
        raise HTTPException(status_code=404, detail="Case not found")

    result = distribution.calculate_distribution(db_case)
    return result

@app.get("/cases/{case_id}/report")
def generate_report(case_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    db_case = db.query(models.Case).filter(models.Case.id == case_id, models.Case.user_id == str(current_user.id)).first()
    if not db_case:
        raise HTTPException(status_code=404, detail="Case not found")

    pdf_buffer = document_generator.generate_pdf_report(db_case)
    
    return StreamingResponse(
        pdf_buffer, 
        media_type="application/pdf", 
        headers={"Content-Disposition": f"attachment; filename=report_case_{case_id}.pdf"}
    )

@app.get("/cases/{case_id}/model650")
def generate_model_650(case_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    db_case = db.query(models.Case).filter(models.Case.id == case_id, models.Case.user_id == str(current_user.id)).first()
    if not db_case:
        raise HTTPException(status_code=404, detail="Case not found")

    pdf_buffer = document_generator.generate_model_650_draft(db_case)
    
    return StreamingResponse(
        pdf_buffer, 
        media_type="application/pdf", 
        headers={"Content-Disposition": f"attachment; filename=modelo650_draft_case_{case_id}.pdf"}
    )

@app.get("/cases/{case_id}/model650/xml")
def generate_model_650_xml(case_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    db_case = db.query(models.Case).filter(models.Case.id == case_id, models.Case.user_id == str(current_user.id)).first()
    if not db_case:
        raise HTTPException(status_code=404, detail="Case not found")

    xml_buffer = aeat.generate_model_650_xml(db_case)
    
    return StreamingResponse(
        xml_buffer, 
        media_type="application/xml", 
        headers={"Content-Disposition": f"attachment; filename=modelo650_export_case_{case_id}.xml"}
    )

# --- Integrations ---

@app.get("/integrations/catastro/{ref}")
def get_catastro_data(ref: str, current_user: models.User = Depends(auth.get_current_user)):
    result = catastro.CatastroService.get_property_by_ref(ref)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result

@app.get("/integrations/catastro/value/{ref}")
def get_catastro_value_url(ref: str, current_user: models.User = Depends(auth.get_current_user)):
    """
    Retorna la URL para consultar el Valor de Referencia de Catastro.
    En el futuro, si se integra certificado, podría devolver el valor directamente.
    """
    url = catastro.CatastroService.get_reference_value_url(ref)
    return {"url": url, "reference": ref}
