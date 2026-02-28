import requests
from PIL import Image, ImageDraw
import io
import os
import time
import uuid

# Configuration
API_URL = "http://localhost:8000"
random_suffix = str(uuid.uuid4())[:8]
USER_EMAIL = f"test_pdf_{random_suffix}@example.com"
USER_PASSWORD = "password123"

def create_test_pdf():
    """Create a dummy PDF with text for OCR testing."""
    # Create a white image
    img = Image.new('RGB', (800, 600), color='white')
    d = ImageDraw.Draw(img)
    
    # Add text
    d.text((50, 50), "CERTIFICADO DE DEFUNCION (PDF)", fill=(0, 0, 0))
    d.text((50, 100), "Nombre: Maria Lopez", fill=(0, 0, 0))
    d.text((50, 150), "Fallecio el dia 20-04-2024", fill=(0, 0, 0))
    d.text((50, 200), "En Barcelona, Espana", fill=(0, 0, 0))
    
    # Save to PDF bytes
    pdf_byte_arr = io.BytesIO()
    img.save(pdf_byte_arr, format='PDF')
    pdf_byte_arr.seek(0)
    return pdf_byte_arr

def run_test():
    print(f"1. Creating user {USER_EMAIL} and logging in...")
    # Register
    reg_response = requests.post(f"{API_URL}/auth/register", json={"email": USER_EMAIL, "password": USER_PASSWORD})
    if reg_response.status_code != 200 and reg_response.status_code != 400:
        print(f"Register failed: {reg_response.text}")
        return

    # Login
    response = requests.post(f"{API_URL}/auth/token", data={"username": USER_EMAIL, "password": USER_PASSWORD})
    if response.status_code != 200:
        print(f"Login failed: {response.text}")
        return
    
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("   Logged in successfully.")

    print("2. Creating a new case...")
    case_data = {
        "user_id": "dummy",
        "status": "PENDIENTE",
        "has_will": False
    }
    response = requests.post(f"{API_URL}/cases/", json=case_data, headers=headers)
    if response.status_code != 200:
        print(f"Create case failed: {response.text}")
        return
    
    case = response.json()
    case_id = case["id"]
    print(f"   Case created with ID: {case_id}")

    print("3. Uploading dummy Death Certificate PDF...")
    pdf_bytes = create_test_pdf()
    files = {
        'file': ('death_cert_test.pdf', pdf_bytes, 'application/pdf')
    }
    data = {
        'type': 'certificado_defuncion' 
    }
    
    response = requests.post(f"{API_URL}/cases/{case_id}/upload-doc/", files=files, data=data, headers=headers)
    if response.status_code != 200:
        print(f"Upload failed: {response.text}")
        return
    
    print("   Upload successful. OCR should be running in background...")

    print("4. Verifying OCR extraction...")
    time.sleep(3) # Give a bit more time for PDF conversion
    
    # Get case details to check date_of_death
    response = requests.get(f"{API_URL}/cases/{case_id}", headers=headers)
    updated_case = response.json()
    
    date_of_death = updated_case.get("date_of_death")
    print(f"   Date of Death in Case: {date_of_death}")
    
    if date_of_death and "2024-04-20" in date_of_death:
        print("✅ SUCCESS: OCR correctly extracted the date 2024-04-20 from PDF!")
    else:
        print("❌ FAILURE: Date not extracted or incorrect.")
        print(f"   Full case data: {updated_case}")

if __name__ == "__main__":
    run_test()
