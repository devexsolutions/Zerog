import requests
import time
import os
from PIL import Image, ImageDraw, ImageFont
import uuid

# Configuration
API_URL = "http://localhost:8000"
random_suffix = str(uuid.uuid4())[:8]
USER_EMAIL = f"test_dni_{random_suffix}@example.com"
USER_PASSWORD = "password123"
DNI_FILE = "test_dni_doc.png"

def create_test_dni_doc():
    """Creates a dummy image with a DNI number"""
    img = Image.new('RGB', (800, 600), color='white')
    d = ImageDraw.Draw(img)
    
    # Try to load a font, fallback to default
    try:
        # Mac standard font
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 40)
    except IOError:
        print("Warning: Custom font not found, using default (might be small)")
        font = ImageFont.load_default()

    # Draw text simulating a document
    d.text((50, 50), "DOCUMENTO NACIONAL DE IDENTIDAD", fill=(0,0,0), font=font)
    d.text((50, 150), "DNI: 12345678Z", fill=(0,0,0), font=font)
    d.text((50, 250), "NOMBRE: JUAN PEREZ", fill=(0,0,0), font=font)
    
    img.save(DNI_FILE)
    print(f"   Created dummy DNI document: {DNI_FILE}")

def run_test():
    try:
        print(f"1. Creating user {USER_EMAIL} and logging in...")
        # Register
        requests.post(f"{API_URL}/auth/register", json={"email": USER_EMAIL, "password": USER_PASSWORD})
        
        # Login
        response = requests.post(f"{API_URL}/auth/token", data={"username": USER_EMAIL, "password": USER_PASSWORD})
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
        case_id = response.json()["id"]
        print(f"   Case created with ID: {case_id}")

        print("3. Uploading dummy DNI Document...")
        create_test_dni_doc()
        
        with open(DNI_FILE, "rb") as f:
            files = {"file": (DNI_FILE, f, "image/png")}
            data = {"type": "DNI"} # Using DNI type
            response = requests.post(f"{API_URL}/cases/{case_id}/upload-doc/", files=files, data=data, headers=headers)
            
        if response.status_code == 200:
            print("   Upload successful. OCR should be running in background...")
        else:
            print(f"   Upload failed: {response.text}")
            return

        print("4. Verifying DNI Extraction...")
        # Poll for a few seconds to let OCR finish (it's synchronous in code but good to wait slightly if async changed)
        # Actually it's synchronous in main.py right now
        
        # Fetch case details
        response = requests.get(f"{API_URL}/cases/", headers=headers)
        cases = response.json()
        my_case = next((c for c in cases if c["id"] == case_id), None)
        
        if my_case and my_case.get("deceased_dni") == "12345678Z":
             print(f"✅ SUCCESS: DNI extracted correctly: {my_case['deceased_dni']}")
        else:
             print(f"❌ FAILURE: DNI not extracted or incorrect. Found: {my_case.get('deceased_dni') if my_case else 'Case not found'}")

    finally:
        if os.path.exists(DNI_FILE):
            os.remove(DNI_FILE)

if __name__ == "__main__":
    run_test()
