"""
Script de migración para añadir nuevas columnas a la BD existente.
Ejecutar una vez: python migrate.py
"""
import sqlite3
import os

DB_PATH = os.getenv("DATABASE_URL", "sqlite:///./antigravity.db").replace("sqlite:///", "")
DB_PATH = os.path.join(os.path.dirname(__file__), DB_PATH.lstrip("./")) if not os.path.isabs(DB_PATH) else DB_PATH

# Buscar el archivo DB relativo al CWD
if not os.path.exists(DB_PATH):
    alt = "./antigravity.db"
    if os.path.exists(alt):
        DB_PATH = alt
    else:
        print(f"Base de datos no encontrada en {DB_PATH}. Se creará al arrancar el servidor.")
        exit(0)

print(f"Migrando base de datos: {DB_PATH}")

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Obtener columnas actuales de 'heirs'
cursor.execute("PRAGMA table_info(heirs)")
columns = {row[1] for row in cursor.fetchall()}
print(f"Columnas actuales en 'heirs': {columns}")

migrations = [
    ("heirs", "nif", "TEXT"),
    ("heirs", "age", "INTEGER"),
]

for table, column, col_type in migrations:
    if column not in columns:
        try:
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")
            print(f"  ✅ Añadida columna '{column}' a '{table}'")
        except Exception as e:
            print(f"  ⚠️  Error añadiendo '{column}': {e}")
    else:
        print(f"  ℹ️  Columna '{column}' ya existe en '{table}'")

conn.commit()
conn.close()
print("Migración completada.")
