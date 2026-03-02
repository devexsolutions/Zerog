
import os
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm

OUTPUT_DIR = "test_docs"

if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

def create_dni_pdf(filename):
    c = canvas.Canvas(filename, pagesize=A4)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(100, 750, "DOCUMENTO NACIONAL DE IDENTIDAD")
    
    c.setFont("Helvetica", 12)
    c.drawString(100, 700, "ESPAÑA")
    c.drawString(100, 680, "APELLIDOS: PÉREZ GARCÍA")
    c.drawString(100, 660, "NOMBRE: ANTONIO")
    c.drawString(100, 640, "SEXO: M")
    c.drawString(100, 620, "NACIONALIDAD: ESP")
    c.drawString(100, 600, "FECHA DE NACIMIENTO: 01 01 1950")
    
    # DNI Pattern for OCR (XYZ + 7-8 digits + Letter)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(100, 530, "DNI: 12345678Z")
    
    c.save()
    print(f"Generated: {filename}")

def create_death_cert_pdf(filename):
    c = canvas.Canvas(filename, pagesize=A4)
    c.setFont("Helvetica-Bold", 18)
    c.drawCentredString(300, 800, "CERTIFICADO DE DEFUNCIÓN")
    
    c.setFont("Helvetica", 12)
    c.drawString(100, 700, "En Madrid, a 20 de Enero de 2024.")
    c.drawString(100, 650, "El encargado del Registro Civil CERTIFICA:")
    
    c.drawString(100, 600, "Que en la inscripción de defunción consta que:")
    
    # Name Pattern: "Don/Doña NOMBRE APELLIDO"
    c.setFont("Helvetica-Bold", 12)
    c.drawString(100, 550, "Don ANTONIO PÉREZ GARCÍA")
    
    c.setFont("Helvetica", 12)
    # DNI Pattern
    c.drawString(100, 530, "con DNI 12345678Z")
    
    # Date Pattern: "falleció el día XX de XXXXX de XXXX" or "XX/XX/XXXX"
    c.drawString(100, 500, "Falleció el día 15 de Enero de 2024")
    c.setFont("Helvetica-Bold", 14)
    c.drawString(100, 480, "Fecha de Defunción: 15/01/2024")
    
    c.save()
    print(f"Generated: {filename}")

def create_bank_cert_pdf(filename):
    c = canvas.Canvas(filename, pagesize=A4)
    c.setFont("Helvetica-Bold", 18)
    c.drawCentredString(300, 800, "CERTIFICADO DE SALDO BANCARIO")
    
    c.setFont("Helvetica", 12)
    c.drawString(100, 750, "BANCO FICTICIO S.A.")
    c.drawString(100, 700, "Por la presente certificamos que a fecha de fallecimiento:")
    
    c.setFont("Helvetica-Bold", 12)
    c.drawString(100, 650, "Don ANTONIO PÉREZ GARCÍA")
    c.drawString(100, 630, "DNI: 12345678Z")
    
    c.setFont("Helvetica", 12)
    c.drawString(100, 600, "Era titular de la cuenta con IBAN:")
    
    # IBAN Pattern (ESXX ...)
    c.setFont("Courier-Bold", 14)
    c.drawString(100, 580, "ES12 3456 7890 1234 5678 9012")
    
    c.setFont("Helvetica", 12)
    c.drawString(100, 550, "Con un saldo acreedor de:")
    
    # Amount Pattern (European format)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(100, 500, "Saldo Total: 150.000,00 EUR")
    
    c.save()
    print(f"Generated: {filename}")

def create_testament_pdf(filename):
    c = canvas.Canvas(filename, pagesize=A4)
    c.setFont("Helvetica-Bold", 18)
    c.drawCentredString(300, 800, "COPIA AUTORIZADA DE TESTAMENTO")
    
    c.setFont("Helvetica", 12)
    c.drawString(100, 700, "En la ciudad de Madrid, ante mí, Notario del Ilustre Colegio...")
    
    c.drawString(100, 650, "COMPARECE: Don ANTONIO PÉREZ GARCÍA")
    
    c.drawString(100, 600, "Y OTORGA TESTAMENTO con las siguientes cláusulas:")
    
    # Keywords for heirs
    c.drawString(100, 550, "PRIMERA. Lega a su cónyuge Doña MARÍA LÓPEZ el usufructo universal.")
    c.drawString(100, 520, "SEGUNDA. Instituye herederos por partes iguales a sus hijos:")
    c.drawString(120, 500, "- Don JUAN PÉREZ LÓPEZ")
    c.drawString(120, 480, "- Doña ANA PÉREZ LÓPEZ")
    
    c.save()
    print(f"Generated: {filename}")

if __name__ == "__main__":
    create_dni_pdf(os.path.join(OUTPUT_DIR, "test_dni.pdf"))
    create_death_cert_pdf(os.path.join(OUTPUT_DIR, "test_certificado_defuncion.pdf"))
    create_bank_cert_pdf(os.path.join(OUTPUT_DIR, "test_certificado_bancario.pdf"))
    create_testament_pdf(os.path.join(OUTPUT_DIR, "test_testamento.pdf"))
    print(f"\nDocumentos generados en la carpeta '{OUTPUT_DIR}'")
