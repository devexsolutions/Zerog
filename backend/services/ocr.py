import pytesseract
from pdf2image import convert_from_path
from PIL import Image
from datetime import datetime
import re
import os
from ..models import DocType

# Configuración básica (en Docker, Tesseract suele estar en el PATH)
# Si fuera local Windows/Mac sin PATH, habría que configurar pytesseract.pytesseract.tesseract_cmd

def extract_text_from_file(file_path: str) -> str:
    """Extrae texto de una imagen o PDF usando Tesseract."""
    text = ""
    try:
        if file_path.lower().endswith('.pdf'):
            # Convertir PDF a imágenes (requiere poppler instalado en el sistema)
            pages = convert_from_path(file_path)
            for page in pages:
                text += pytesseract.image_to_string(page, lang='spa') + "\n"
        else:
            # Imagen
            img = Image.open(file_path)
            text = pytesseract.image_to_string(img, lang='spa')
    except Exception as e:
        print(f"Error en OCR: {e}")
        return ""
    
    return text

def analyze_document(file_path: str, doc_type: str):
    """
    Realiza OCR sobre el documento y extrae datos estructurados básicos usando Regex.
    """
    print(f"Iniciando OCR con Tesseract para: {file_path} ({doc_type})")
    
    # 1. Extraer texto crudo
    print(f"Iniciando extracción de texto para: {file_path}")
    raw_text = extract_text_from_file(file_path)
    print(f"Texto extraído ({len(raw_text)} chars):\n--- INICIO ---\n{raw_text}\n--- FIN ---") 

    extracted_data = {"raw_text": raw_text}

    # 2. Analizar según tipo de documento (Lógica heurística simple)
    
    if doc_type == DocType.DEATH_CERTIFICATE:
        # Intentar buscar fecha de defunción
        # Patrones comunes: "falleció el día XX de XXXXX de XXXX", "fecha de defunción: XX/XX/XXXX"
        
        # Regex simple para fecha DD/MM/AAAA o DD-MM-AAAA
        # Busca explícitamente "Fecha de Defunción:" o solo la fecha
        date_match = re.search(r'(?:Fecha de Defunción|Fallecimiento|Fecha)[:\s]+(\d{1,2})[/-](\d{1,2})[/-](\d{4})', raw_text, re.IGNORECASE)
        if not date_match:
             # Fallback: buscar cualquier fecha en formato DD/MM/YYYY
             date_match = re.search(r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})', raw_text)

        if date_match:
            try:
                # Si hay 3 grupos capturados (día, mes, año)
                # Si usó el primer regex con prefijo, los grupos son 1,2,3
                # Si usó el segundo, también.
                # Pero date_match.groups() devuelve tuple.
                groups = date_match.groups()
                # Filtrar None si hubiera grupos opcionales (aquí no hay)
                day, month, year = groups[-3], groups[-2], groups[-1]
                
                dt = datetime(int(year), int(month), int(day))
                extracted_data["date_of_death"] = dt.isoformat()
                print(f"Fecha de defunción encontrada: {extracted_data['date_of_death']}")
            except ValueError as e:
                print(f"Error parseando fecha: {e}")
        else:
             print("No se encontró fecha de defunción en el texto")
        
        # Intentar buscar Nombre del fallecido
        # Patrones: "Don/Doña NOMBRE APELLIDO", "Certifico que NOMBRE APELLIDO", "Nombre: ..."
        name_match = re.search(r'(?:Don|Doña|D\.|Dña\.|Nombre)[:\s]+([A-ZÁÉÍÓÚÑ\s]+)', raw_text, re.IGNORECASE)
        if name_match:
             extracted_data["deceased_name"] = name_match.group(1).strip()
             print(f"Nombre fallecido encontrado: {extracted_data['deceased_name']}")

        # Buscar DNI
        dni_match = re.search(r'(?:DNI)[:\s]+([XYZ]?\d{7,8})[-\s]?([A-Z])', raw_text, re.IGNORECASE)
        if dni_match:
             extracted_data["dni"] = f"{dni_match.group(1)}{dni_match.group(2)}".upper()
             print(f"DNI fallecido encontrado: {extracted_data['dni']}")
        elif "dni" not in extracted_data:
             # Fallback DNI general
             dni_match = re.search(r'\b([XYZ]?\d{7,8})[-\s]?([A-Z])\b', raw_text, re.IGNORECASE)
             if dni_match:
                  extracted_data["dni"] = f"{dni_match.group(1)}{dni_match.group(2)}".upper()

        # Si no encuentra fecha, fallback a la fecha actual
        if "date_of_death" not in extracted_data:
             print("Usando fecha actual como fallback")
             extracted_data["date_of_death"] = datetime.now().isoformat()
             extracted_data["ocr_status"] = "date_not_found_fallback"

    elif doc_type == DocType.DNI:
        print("Analizando DNI...")
        # Buscar patrón de DNI explícito "DNI: ..."
        dni_match = re.search(r'(?:DNI)[:\s]+([XYZ]?\d{7,8})[-\s]?([A-Z])', raw_text, re.IGNORECASE)
        if not dni_match:
            # Fallback patrón genérico
            dni_match = re.search(r'\b([XYZ]?\d{7,8})[-\s]?([A-Z])\b', raw_text, re.IGNORECASE)
            
        if dni_match:
            extracted_data["dni"] = f"{dni_match.group(1)}{dni_match.group(2)}".upper()
            print(f"DNI encontrado: {extracted_data['dni']}")
        else:
            print("No se encontró patrón de DNI")
        
    elif doc_type == DocType.BANK_CERTIFICATE: # 'certificado_bancario'
        # Buscar IBAN ESXX ...
        iban_match = re.search(r'\b(ES\d{2}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{2}[-\s]?\d{10})\b', raw_text)
        if iban_match:
            extracted_data["iban"] = iban_match.group(1).replace(" ", "").replace("-", "")
            print(f"IBAN encontrado: {extracted_data['iban']}")

        # Buscar Importe/Saldo
        # Patrones: "Saldo: 1.234,56", "Importe: 1.234,56 €"
        # Asumimos formato europeo 1.234,56
        amount_match = re.search(r'(?:Saldo|Importe|Valor|Total)[:\s]+(\d{1,3}(?:\.\d{3})*(?:,\d{1,2})?)', raw_text, re.IGNORECASE)
        if amount_match:
            amount_str = amount_match.group(1)
            print(f"Saldo encontrado: {amount_str}")
            clean_amount = amount_str.replace(".", "").replace(",", ".")
            try:
                extracted_data["amount"] = float(clean_amount)
            except ValueError:
                pass

    elif doc_type == DocType.TESTAMENT:
        # Búsqueda muy básica de palabras clave
        heirs = []
        if "hijo" in raw_text.lower():
             heirs.append({"name": "Posible Hijo (Mencionado)", "relationship": "Hijo"})
        if "esposa" in raw_text.lower() or "cónyuge" in raw_text.lower():
             heirs.append({"name": "Cónyuge (Mencionado)", "relationship": "Cónyuge"})
        
        extracted_data["heirs_found"] = heirs

    return extracted_data
