# actualizar_bd_inventario.py - Añade tablas de inventario a la BD existente
import sqlite3
from pathlib import Path
import sys

# IMPORTANTE: Como este script está en scripts/, necesitamos subir un nivel
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent  # Subir un nivel desde scripts/ a la raíz

# Añadir la raíz del proyecto al path
sys.path.insert(0, str(PROJECT_ROOT))

# Rutas relativas a la raíz del proyecto
DB_PATH = PROJECT_ROOT / "db" / "almacen.db"

def actualizar_bd():
    """Añade las tablas de inventario si no existen"""
    print("🔧 Actualizando base de datos...")
    print(f"📁 Base de datos: {DB_PATH}")
    
    if not DB_PATH.exists():
        print(f"\n❌ ERROR: No se encuentra la base de datos")
        print(f"   Buscada en: {DB_PATH}")
        print(f"   Ejecuta primero: python scripts/init_db.py")
        return
    
    try:
        con = sqlite3.connect(DB_PATH)
        cur = con.cursor()
        
        # Verificar si ya existen las tablas
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='inventarios'")
        if cur.fetchone():
            print("ℹ️  Las tablas de inventario ya existen.")
            con.close()
            return
        
        print("📋 Creando tablas de inventario...")
        
        # Crear tablas
        cur.executescript("""
        -- ========================================
        -- INVENTARIOS FÍSICOS
        -- ========================================
        CREATE TABLE IF NOT EXISTS inventarios(
          id           INTEGER PRIMARY KEY AUTOINCREMENT,
          fecha        TEXT NOT NULL,
          responsable  TEXT NOT NULL,
          almacen_id   INTEGER,
          observaciones TEXT,
          estado       TEXT NOT NULL DEFAULT 'EN_PROCESO' CHECK(estado IN ('EN_PROCESO','FINALIZADO')),
          fecha_cierre TEXT,
          FOREIGN KEY(almacen_id) REFERENCES almacenes(id)
        );

        CREATE TABLE IF NOT EXISTS inventario_detalle(
          id              INTEGER PRIMARY KEY AUTOINCREMENT,
          inventario_id   INTEGER NOT NULL,
          articulo_id     INTEGER NOT NULL,
          stock_teorico   REAL NOT NULL DEFAULT 0,
          stock_contado   REAL NOT NULL DEFAULT 0,
          diferencia      REAL NOT NULL DEFAULT 0,
          FOREIGN KEY(inventario_id) REFERENCES inventarios(id) ON DELETE CASCADE,
          FOREIGN KEY(articulo_id) REFERENCES articulos(id)
        );

        -- Índices para inventarios
        CREATE INDEX IF NOT EXISTS idx_inventarios_fecha ON inventarios(fecha);
        CREATE INDEX IF NOT EXISTS idx_inventarios_almacen ON inventarios(almacen_id);
        CREATE INDEX IF NOT EXISTS idx_inventario_detalle_inv ON inventario_detalle(inventario_id);
        CREATE INDEX IF NOT EXISTS idx_inventario_detalle_art ON inventario_detalle(articulo_id);
        """)
        
        con.commit()
        con.close()
        
        print("✅ Tablas de inventario creadas correctamente!")
        print("📊 Ya puedes usar el módulo de Inventario Físico.")
        
    except Exception as e:
        print(f"❌ Error al actualizar BD: {e}")

if __name__ == "__main__":
    actualizar_bd()
