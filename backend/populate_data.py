import requests
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000"

def populate_demo_case():
    # 1. Crear Caso
    case_data = {
        "user_id": "demo_user_001",
        "status": "ABIERTO",
        "deadline": (datetime.now() + timedelta(days=180)).isoformat(),
        "date_of_death": (datetime.now() - timedelta(days=45)).isoformat(), # Falleció hace 45 días
        "has_will": True
    }
    res = requests.post(f"{BASE_URL}/cases/", json=case_data)
    if res.status_code != 200:
        print(f"Error creando caso: {res.text}")
        return
    case = res.json()
    case_id = case["id"]
    print(f"Caso creado: ID {case_id}")

    # 2. Añadir Herederos
    heirs = [
        {"name": "Hijo 1", "tax_percentage": 33.33, "relationship_degree": "Hijo", "fiscal_residence": "Madrid"},
        {"name": "Hijo 2", "tax_percentage": 33.33, "relationship_degree": "Hijo", "fiscal_residence": "Madrid"},
        {"name": "Cónyuge", "tax_percentage": 33.33, "relationship_degree": "Cónyuge", "fiscal_residence": "Madrid"},
    ]
    for h in heirs:
        requests.post(f"{BASE_URL}/cases/{case_id}/heirs/", json=h)
    print("Herederos añadidos")

    # 3. Añadir Bienes (Activos)
    assets = [
        {"type": "inmueble", "value": 350000, "description": "Vivienda Habitual Madrid", "is_ganancial": True},
        {"type": "cuenta", "value": 120000, "description": "Cuenta Corriente BBVA", "is_ganancial": True},
        {"type": "vehiculo", "value": 15000, "description": "Coche Toyota", "is_ganancial": False},
        {"type": "seguro", "value": 60000, "description": "Seguro de Vida", "is_ganancial": False},
    ]
    for a in assets:
        requests.post(f"{BASE_URL}/cases/{case_id}/assets/", json=a)
    print("Activos añadidos")

    # 4. Añadir Deudas (Pasivos)
    debts = [
        {"type": "otro", "value": 5000, "description": "Gastos Sepelio", "is_debt": False, "is_funeral_expense": True}, # Ojo, en modelo puse is_funeral_expense separado
        {"type": "otro", "value": 2500, "description": "Deuda Tarjeta", "is_debt": True},
    ]
    for d in debts:
        requests.post(f"{BASE_URL}/cases/{case_id}/assets/", json=d)
    print("Pasivos añadidos")

    # 5. Añadir Documentos (Simular subida)
    docs = [
        {"type": "DNI", "file_url": "http://fake.url/dni.pdf", "status": "VALIDADO", "is_verified": True},
        {"type": "certificado_defuncion", "file_url": "http://fake.url/cert.pdf", "status": "VALIDADO", "is_verified": True},
    ]
    for d in docs:
        requests.post(f"{BASE_URL}/cases/{case_id}/docs/", json=d)
    print("Documentos simulados añadidos")

    print(f"\nDatos de prueba cargados. Visita: http://localhost:3000/cases/{case_id}")

if __name__ == "__main__":
    populate_demo_case()
