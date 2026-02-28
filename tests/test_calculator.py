import requests
import uuid
import time

# Configuration
API_URL = "http://localhost:8000"
random_suffix = str(uuid.uuid4())[:8]
USER_EMAIL = f"test_calc_{random_suffix}@example.com"
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

    print("4. Calculating Inheritance Mass...")
    response = requests.get(f"{API_URL}/cases/{case_id}/calculate", headers=headers)
    if response.status_code != 200:
        print(f"Calculation failed: {response.text}")
        return
        
    result = response.json()
    print("   Calculation Result:")
    print(f"   - Total Assets: {result['total_assets']} (Expected: 150000.0)")
    print(f"   - Total Debts: {result['total_debts']} (Expected: 20000.0)")
    print(f"   - Household Goods (Ajuar): {result['household_goods']} (Expected: 4500.0)")
    print(f"   - Net Estate: {result['net_estate']} (Expected: 130000.0)")
    print(f"   - Taxable Base: {result['taxable_base']} (Expected: 134500.0)")
    
    # Verification
    # Assets = 100k + 50k = 150k
    # Debts = 20k
    # Ajuar = 3% of 150k = 4,500
    # Net Estate = 150k - 20k = 130k
    # Taxable Base = 130k + 4.5k = 134.5k
    
    if (result['total_assets'] == 150000.0 and 
        result['total_debts'] == 20000.0 and 
        result['household_goods'] == 4500.0 and
        result['net_estate'] == 130000.0 and
        result['taxable_base'] == 134500.0):
        print("✅ SUCCESS: Calculation is correct!")
    else:
        print("❌ FAILURE: Calculation mismatch.")

if __name__ == "__main__":
    run_test()
