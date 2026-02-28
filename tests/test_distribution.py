import requests
import uuid
import time

# Configuration
API_URL = "http://localhost:8000"
random_suffix = str(uuid.uuid4())[:8]
USER_EMAIL = f"test_dist_{random_suffix}@example.com"
USER_PASSWORD = "password123"

def run_test():
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

    print("3. Adding Assets...")
    # Asset 1: Real Estate (100,000)
    asset1 = {
        "type": "inmueble",
        "value": 100000.0,
        "description": "Piso en Madrid",
        "is_debt": False
    }
    requests.post(f"{API_URL}/cases/{case_id}/assets/", json=asset1, headers=headers)
    
    # Asset 2: Bank Account (50,000)
    asset2 = {
        "type": "cuenta",
        "value": 50000.0,
        "description": "Cuenta BBVA",
        "is_debt": False
    }
    requests.post(f"{API_URL}/cases/{case_id}/assets/", json=asset2, headers=headers)
    
    # Debt 1: Mortgage (20,000)
    debt1 = {
        "type": "otro",
        "value": 20000.0,
        "description": "Hipoteca",
        "is_debt": True
    }
    requests.post(f"{API_URL}/cases/{case_id}/assets/", json=debt1, headers=headers)
    
    # Expected Net Estate (without Ajuar logic for distribution base? Wait.)
    # Calculator logic:
    # Assets = 150k.
    # Debts = 20k.
    # Net Estate = 150k - 20k = 130k.
    # Ajuar (3% of 150k) = 4.5k.
    # Taxable Base = 130k + 4.5k = 134.5k.
    
    # Distribution logic currently uses Net Estate (130k).
    # Let's verify if distribution should be on Net Estate or Taxable Base.
    # Usually, distribution is on the Net Estate (what is actually there).
    # Taxable Base includes Ajuar which is a tax concept, but often distributed too.
    # For now, let's assume distribution on Net Estate (130k).

    print("4. Adding Heirs...")
    heir1 = {
        "name": "Hijo A",
        "relationship_degree": "Hijo",
        "share_percentage": 50.0,
        "tax_percentage": 0.0 # Optional
    }
    requests.post(f"{API_URL}/cases/{case_id}/heirs/", json=heir1, headers=headers)

    heir2 = {
        "name": "Hija B",
        "relationship_degree": "Hija",
        "share_percentage": 50.0,
        "tax_percentage": 0.0
    }
    requests.post(f"{API_URL}/cases/{case_id}/heirs/", json=heir2, headers=headers)

    print("5. Calculating Distribution...")
    response = requests.get(f"{API_URL}/cases/{case_id}/distribution", headers=headers)
    
    if response.status_code != 200:
        print(f"Distribution failed: {response.text}")
        return
        
    result = response.json()
    print("   Distribution Result:")
    
    estate_summary = result["estate_summary"]
    net_estate = estate_summary["net_estate"]
    print(f"   - Net Estate: {net_estate}")
    
    heirs = result["heirs_distribution"]
    for h in heirs:
        print(f"   - Heir: {h['name']} ({h['share_percentage']}%) -> Quota: {h['quota_value']}")
        
    total_distributed = result["total_distributed"]
    print(f"   - Total Distributed: {total_distributed}")
    
    # Verification
    expected_quota = 65000.0 # 50% of 130k
    
    if (abs(heirs[0]['quota_value'] - expected_quota) < 0.1 and
        abs(heirs[1]['quota_value'] - expected_quota) < 0.1 and
        abs(total_distributed - 130000.0) < 0.1):
        print("✅ SUCCESS: Distribution is correct!")
    else:
        print(f"❌ FAILURE: Distribution mismatch. Expected {expected_quota} per heir.")

    print("6. Generating PDF Report...")
    pdf_response = requests.get(f"{API_URL}/cases/{case_id}/report", headers=headers)
    
    if pdf_response.status_code == 200:
        pdf_filename = f"report_test_{case_id}.pdf"
        with open(pdf_filename, "wb") as f:
            f.write(pdf_response.content)
        print(f"✅ SUCCESS: PDF Report generated and saved to {pdf_filename}")
    else:
        print(f"❌ FAILURE: PDF Generation failed: {pdf_response.text}")

if __name__ == "__main__":
    run_test()
