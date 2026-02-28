# Antigravity - Módulo de Gestión de Herencias (MVP)

Plataforma SaaS para la gestión automatizada de herencias, centralizando documentación y cálculos para herederos y profesionales.

## 🚀 Stack Tecnológico

- **Frontend**: Next.js 15 (App Router), Tailwind CSS, Lucide React
- **Backend**: FastAPI (Python), SQLAlchemy, Pydantic
- **Base de Datos**: SQLite (Dev) / PostgreSQL (Prod)

## 🛠️ Estructura del Proyecto

```
/
├── backend/            # API FastAPI
│   ├── main.py         # Entry point y endpoints
│   ├── models.py       # Modelos SQLAlchemy (DB)
│   ├── schemas.py      # Esquemas Pydantic (Validación)
│   ├── database.py     # Configuración de BD
│   └── venv/           # Entorno virtual Python
├── frontend/           # Next.js App
│   ├── src/app/        # Páginas y componentes
│   └── public/         # Assets estáticos
└── antigravity.db      # Base de datos local (SQLite)
```

## 🏁 Cómo Iniciar

### 1. Backend (FastAPI)

```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
pip install -r requirements.txt # (Si existe) o instalar dependencias manuales
# Dependencias actuales: fastapi uvicorn sqlalchemy pydantic

# Iniciar servidor (desde la raíz del proyecto para resolver imports correctamente)
uvicorn backend.main:app --reload --port 8000
```
*El backend estará disponible en: http://localhost:8000*
*Documentación API (Swagger): http://localhost:8000/docs*

### 2. Frontend (Next.js)

```bash
cd frontend
npm install
npm run dev
```
*El frontend estará disponible en: http://localhost:3000*

## 📝 Funcionalidades MVP Implementadas

- **Gestión de Expedientes**: Crear y listar expedientes de herencia.
- **Base de Datos**: Modelos definidos para Expedientes, Herederos, Bienes y Documentos.
- **Interfaz**: Panel de control moderno con Tailwind CSS.

## 🔜 Próximos Pasos

- Integración de OCR (AWS Textract / Google Doc AI).
- Motor de Cálculo de Masa Hereditaria.
- Autenticación (Auth0/Clerk).
- Subida de archivos a S3/GCS.
