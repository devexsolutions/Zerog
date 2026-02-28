import requests
from PIL import Image, ImageDraw, ImageFont
import io
import os
import time
import uuid

# Configuration
API_URL = "http://localhost:8000"
random_suffix = str(uuid.uuid4())[:8]
USER_EMAIL = f"test_bank_{random_suffix}@example.com"
USER_PASSWORD = "password123"

def create_test_bank_cert():
    """Create a dummy Bank Certificate image with text for OCR testing."""
    # Create a white image
    img = Image.new('RGB', (1000, 800), color='white')
    d = ImageDraw.Draw(img)
    
    # Load a font (try Arial or similar, fallback to default)
    try:
        # Mac path
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 40)
        # font = ImageFont.truetype("arial.ttf", 40) 
    except IOError:
        print("Warning: Custom font not found, using default (might be small)")
        font = None # default
    
    # Add text
    fill = (0, 0, 0)
    if font:
        d.text((50, 50), "CERTIFICADO BANCARIO", fill=fill, font=font)
        d.text((50, 150), "Banco: Banco de Prueba", fill=fill, font=font)
        d.text((50, 250), "Titular: Juan Perez", fill=fill, font=font)
        d.text((50, 350), "IBAN: ES12 1234 5678 90 1234567890", fill=fill, font=font)
        d.text((50, 450), "Saldo: 1.250,50 EUR", fill=fill, font=font)
    else:
        # Fallback for default font
        d.text((50, 50), "CERTIFICADO BANCARIO", fill=fill)
        d.text((50, 100), "Banco: Banco de Prueba", fill=fill)
        d.text((50, 150), "Titular: Juan Perez", fill=fill)
        d.text((50, 200), "IBAN: ES12 1234 5678 90 1234567890", fill=fill)
        d.text((50, 250), "Saldo: 1.250,50 EUR", fill=fill)
    
    # Save to bytes
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    return img_byte_arr

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

    print("3. Uploading dummy Bank Certificate...")
    img_bytes = create_test_bank_cert()
    files = {
        'file': ('bank_cert_test.png', img_bytes, 'image/png')
    }
    # DocType enum value for BANK_CERTIFICATE is 'certificado_bancario'
    data = {
        'type': 'certificado_bancario' 
    }
    
    response = requests.post(f"{API_URL}/cases/{case_id}/upload-doc/", files=files, data=data, headers=headers)
    if response.status_code != 200:
        print(f"Upload failed: {response.text}")
        return
    
    print("   Upload successful. OCR should be running in background...")

    print("4. Verifying Asset Creation...")
    time.sleep(2) 
    
    # Get case details to check assets
    response = requests.get(f"{API_URL}/cases/{case_id}", headers=headers)
    updated_case = response.json()
    
    assets = updated_case.get("assets", [])
    print(f"   Assets found: {len(assets)}")
    
    found = False
    for asset in assets:
        print(f"   - Asset: {asset['description']} | Value: {asset['value']}")
        if "ES1212345678901234567890" in asset['description'] and asset['value'] == 1250.5:
            found = True
    
    if found:
        print("✅ SUCCESS: Asset created automatically from Bank Certificate!")
    else:
        print("❌ FAILURE: Asset not created or incorrect data.")
        print(f"   Full case data: {updated_case}")

if __name__ == "__main__":
    run_test()
