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

import models, schemas
from database import engine, get_db
from services.ocr import analyze_document
from services import calculator, distribution, document_generator, catastro, aeat, ai_extractor
import auth

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Antigravity API", description="Inheritance Management Module MVP")

# Mount uploads directory to serve files
if not os.path.exists("backend/uploads"):
    os.makedirs("backend/uploads")
app.mount("/uploads", StaticFiles(directory="backend/uploads"), name="uploads")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all origins for now to fix Easypanel connectivity
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Welcome to Antigravity API"}

@app.get("/debug/ocr")
def debug_ocr():
    import subprocess
    from PIL import Image, ImageDraw
    import pytesseract
    import sys
    
    logs = []
    logs.append(f"CWD: {os.getcwd()}")
    logs.append(f"Python: {sys.version}")
    
    # Check Tesseract binary
    try:
        result = subprocess.run(["tesseract", "--version"], capture_output=True, text=True)
        logs.append(f"Tesseract Version: {result.stdout.splitlines()[0] if result.stdout else 'Unknown'}")
    except Exception as e:
        logs.append(f"Tesseract Error: {e}")

    # Check Poppler (pdfinfo)
    try:
        result = subprocess.run(["pdfinfo", "-v"], capture_output=True, text=True)
        # pdfinfo prints to stderr usually
        logs.append(f"Poppler Version: {result.stderr.splitlines()[0] if result.stderr else 'Unknown'}")
    except Exception as e:
        logs.append(f"Poppler Error: {e}")

    # Test Image OCR
    try:
        img = Image.new('RGB', (100, 30), color = (255, 255, 255))
        d = ImageDraw.Draw(img)
        # Default font might be missing or small, but usually works
        d.text((10,10), "HOLA", fill=(0,0,0))
        
        UPLOAD_DIR = os.path.abspath("backend/uploads")
        if not os.path.exists(UPLOAD_DIR):
             os.makedirs(UPLOAD_DIR)
        img_path = os.path.join(UPLOAD_DIR, "debug_ocr.png")
        img.save(img_path)
        
        text = pytesseract.image_to_string(Image.open(img_path))
        logs.append(f"Image OCR Result: {text.strip()}")
    except Exception as e:
        logs.append(f"Image OCR Error: {e}")

    return {"logs": logs}

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
@app.post("/cases/{case_id}/upload-doc/", response_model=schemas.DocUploadResponse)
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

    # Guardar archivo localmente (Absolute path to be safe in Docker)
    UPLOAD_DIR = os.path.abspath("backend/uploads")
    if not os.path.exists(UPLOAD_DIR):
        os.makedirs(UPLOAD_DIR)
        
    file_location = os.path.join(UPLOAD_DIR, f"{case_id}_{file.filename}")
    
    # Use 'wb' mode and shutil to save upload file
    # Important: Reset file cursor if it was read before
    file.file.seek(0)
    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # URL accesible (en prod sería S3 URL o CDN)
    # Using relative path for URL if possible, or env var
    # For now keep localhost but client should use relative
    file_url = f"/uploads/{case_id}_{file.filename}"

    # Crear registro en BD
    db_doc = models.Doc(
        case_id=case_id,
        type=type,
        file_url=file_url,
        status=models.DocStatus.UPLOADED, 
        is_verified=False
    )
    db.add(db_doc)
    db.commit()
    db.refresh(db_doc)

    # Variables para contar activos creados y referencias encontradas
    assets_created = 0
    cadastral_references_found = 0
    processing_message = ""
    ai_data = None

    # Extracción OCR
    try:
        print(f"OCR: Iniciando análisis de {file_location} (Tipo: {type})")
        extracted = analyze_document(file_location, type)
        print(f"OCR: Datos extraídos: {extracted}")

        # --- AI Extraction (Mistral) ---
        # Only for complex documents that benefit from LLM
        if type in [models.DocType.TESTAMENT, models.DocType.DEED, models.DocType.LAST_WILL]:
            print(f"AI: Iniciando extracción inteligente para {type}...")
            # Obtener texto crudo, si no hay, intentar analizar de nuevo o usar vacío
            raw_text = extracted.get("raw_text", "")
            
            ai_extraction_result = ai_extractor.ai_extractor.extract_data_from_text(raw_text, type)
            print(f"AI: Resultado: {ai_extraction_result}")
            
            # Guardar resultado en variable para respuesta
            ai_data = ai_extraction_result

            # Merge AI findings with OCR findings (simple strategy for now)
            if ai_data and "cadastral_references" in ai_data and isinstance(ai_data["cadastral_references"], list):
                ocr_refs = extracted.get("cadastral_references") or []
                ai_refs = ai_data["cadastral_references"]
                # Normalize and merge unique
                # Filter both OCR and AI references for validity (length >= 18)
                valid_ocr = [r for r in ocr_refs if isinstance(r, str) and len(r) >= 18]
                valid_ai = [r for r in ai_refs if isinstance(r, str) and len(r) >= 18]
                combined_refs = list(set(valid_ocr + valid_ai))
                extracted["cadastral_references"] = combined_refs
                ai_data["cadastral_references"] = combined_refs
                print(f"AI+OCR: Referencias catastrales combinadas: {combined_refs}")

        
        if type == models.DocType.DEATH_CERTIFICATE:
            if "date_of_death" in extracted:
                # Actualizar siempre para DEMO, aunque ya exista valor
                old_date = db_case.date_of_death
                db_case.date_of_death = datetime.fromisoformat(extracted["date_of_death"])
                print(f"OCR: Fecha de defunción actualizada: {old_date} -> {db_case.date_of_death}")
            
            if "deceased_name" in extracted:
                # Actualizar siempre para DEMO
                old_name = db_case.deceased_name
                db_case.deceased_name = extracted["deceased_name"]
                print(f"OCR: Nombre del fallecido actualizado: {old_name} -> {extracted['deceased_name']}")
            
            if "dni" in extracted:
                # Actualizar siempre para DEMO
                old_dni = db_case.deceased_dni
                db_case.deceased_dni = extracted["dni"]
                print(f"OCR: DNI del fallecido actualizado: {old_dni} -> {extracted['dni']}")

            db.commit()
        
        elif type == models.DocType.DNI:
            if "dni" in extracted:
                # Actualizar siempre para DEMO
                old_dni = db_case.deceased_dni
                db_case.deceased_dni = extracted["dni"]
                db.commit()
                print(f"OCR: DNI del fallecido actualizado desde DNI: {old_dni} -> {extracted['dni']}")
        
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
        
        elif type == models.DocType.TESTAMENT:
            # Procesar referencias catastrales encontradas en el testamento
            if "cadastral_references" in extracted and extracted["cadastral_references"]:
                cadastral_references_found = len(extracted["cadastral_references"])
                print(f"OCR: Procesando {cadastral_references_found} referencias catastrales")
                
                for ref in extracted["cadastral_references"]:
                    try:
                        # Verificar si ya existe un activo con esta referencia catastral
                        existing_asset = db.query(models.Asset).filter(
                            models.Asset.case_id == case_id,
                            models.Asset.cadastral_reference == ref
                        ).first()
                        
                        if existing_asset:
                            print(f"OCR: Referencia {ref} ya existe en el inventario, saltando...")
                            continue
                        
                        # Obtener datos del catastro
                        print(f"OCR: Consultando catastro para referencia {ref}")
                        catastro_data = catastro.CatastroService.get_property_by_ref(ref)
                        
                        if catastro_data:
                            # Intentar obtener el valor de referencia
                            reference_value = 0
                            try:
                                value_data = catastro.CatastroService.get_reference_value_url(ref)
                                # Si hay un valor disponible, usarlo
                                if isinstance(value_data, dict) and 'value' in value_data:
                                    reference_value = value_data['value']
                                elif isinstance(value_data, (int, float)):
                                    reference_value = float(value_data)
                            except Exception as value_error:
                                print(f"OCR: No se pudo obtener valor para {ref}: {value_error}")
                            
                            # Crear el activo con los datos obtenidos
                            new_asset = models.Asset(
                                case_id=case_id,
                                type=models.AssetType.REAL_ESTATE,
                                value=reference_value or 0,  # Usar valor de referencia o 0 como fallback
                                description=f"Inmueble extraído OCR: {catastro_data.get('address', 'Dirección no disponible')}",
                                cadastral_reference=ref,
                                address=catastro_data.get('address'),
                                surface=catastro_data.get('surface'),
                                usage=catastro_data.get('usage'),
                                reference_value=reference_value,
                                is_ganancial=False,
                                is_debt=False
                            )
                            
                            db.add(new_asset)
                            db.commit()
                            assets_created += 1
                            print(f"OCR: Inmueble añadido automáticamente: {ref} - {catastro_data.get('address', 'Dirección no disponible')}")
                        else:
                            print(f"OCR: No se encontraron datos para la referencia {ref}")
                            
                    except Exception as e:
                        print(f"OCR: Error procesando referencia {ref}: {e}")
                        # Continuar con la siguiente referencia
                        continue
                
                # Crear mensaje de procesamiento para testamentos
                if cadastral_references_found > 0:
                    if assets_created > 0:
                        processing_message = f"Se encontraron {cadastral_references_found} referencias catastrales y se crearon {assets_created} bienes automáticamente."
                    else:
                        processing_message = f"Se encontraron {cadastral_references_found} referencias catastrales, pero no se pudieron crear bienes (ya existían o no se encontraron datos)."
                else:
                    processing_message = "No se encontraron referencias catastrales en el testamento."

    except Exception as e:
        print(f"Error procesando OCR: {e}")

    # Devolver respuesta con información de procesamiento
    return schemas.DocUploadResponse(
        document=db_doc,
        assets_created=assets_created,
        cadastral_references_found=cadastral_references_found,
        message=processing_message,
        ai_data=ai_data
    )

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
