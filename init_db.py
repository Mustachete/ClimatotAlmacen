# init_db.py - Inicializar base de datos con estructura actualizada
import sqlite3
import hashlib
from pathlib import Path

BASE = Path(__file__).resolve().parent
DB_PATH = BASE / "db" / "almacen.db"
SCHEMA = BASE / "db" / "schema.sql"

def hash_pwd(p: str) -> str:
    return hashlib.sha256(p.encode("utf-8")).hexdigest()

def main():
    print("🔧 Inicializando base de datos...")
    
    # Crear carpeta db si no existe
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    # Conectar a la BD
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    
    # Ejecutar el schema
    print("📋 Creando tablas...")
    with open(SCHEMA, "r", encoding="utf-8") as f:
        cur.executescript(f.read())
    con.commit()
    
    # ========================================
    # DATOS INICIALES
    # ========================================
    
    # 1. Usuarios
    print("👤 Creando usuarios...")
    cur.execute("SELECT COUNT(*) FROM usuarios")
    if cur.fetchone()[0] == 0:
        cur.execute(
            "INSERT INTO usuarios(usuario, pass_hash, rol, activo) VALUES(?,?,?,1)",
            ("admin", hash_pwd("admin"), "admin")
        )
        cur.execute(
            "INSERT INTO usuarios(usuario, pass_hash, rol, activo) VALUES(?,?,?,1)",
            ("almacen", hash_pwd("1234"), "almacen")
        )
        print("   ✅ Usuario: admin / Contraseña: admin (ROL: admin)")
        print("   ✅ Usuario: almacen / Contraseña: 1234 (ROL: almacen)")
    
    # 2. Almacenes y Furgonetas
    print("🏢 Creando almacenes y furgonetas...")
    cur.execute("SELECT COUNT(*) FROM almacenes")
    if cur.fetchone()[0] == 0:
        # Almacén principal
        cur.execute("INSERT INTO almacenes(nombre, tipo) VALUES(?,?)", ("Almacén", "almacen"))
        # Furgonetas 01-10
        for i in range(1, 11):
            nombre = f"{i:02d}"  # 01, 02, 03...10
            cur.execute("INSERT INTO almacenes(nombre, tipo) VALUES(?,?)", (nombre, "furgoneta"))
        print("   ✅ Almacén principal + 10 furgonetas (01-10)")
    
    # 3. Proveedores de ejemplo
    print("🏭 Creando proveedores de ejemplo...")
    cur.execute("SELECT COUNT(*) FROM proveedores")
    if cur.fetchone()[0] == 0:
        proveedores = [
            ("Suministros Climáticos S.L.", "912345678", "Juan Pérez", "ventas@climasum.es"),
            ("Distribuciones HVAC", "934567890", "María García", "info@hvac.com"),
            ("Ferretería Industrial", "956789012", "Carlos López", "pedidos@ferreteria.es"),
        ]
        for nombre, tel, contacto, email in proveedores:
            cur.execute(
                "INSERT INTO proveedores(nombre, telefono, contacto, email) VALUES(?,?,?,?)",
                (nombre, tel, contacto, email)
            )
        print(f"   ✅ {len(proveedores)} proveedores de ejemplo")
    
    # 4. Familias de artículos
    print("📦 Creando familias de artículos...")
    cur.execute("SELECT COUNT(*) FROM familias")
    if cur.fetchone()[0] == 0:
        familias = [
            "Calefacción",
            "Climatización",
            "Tubería y Racores",
            "Elementos de Fijación",
            "Material Eléctrico",
            "Herramientas",
            "Consumibles",
        ]
        for f in familias:
            cur.execute("INSERT INTO familias(nombre) VALUES(?)", (f,))
        print(f"   ✅ {len(familias)} familias de artículos")
    
    # 5. Ubicaciones del almacén
    print("📍 Creando ubicaciones...")
    cur.execute("SELECT COUNT(*) FROM ubicaciones")
    if cur.fetchone()[0] == 0:
        ubicaciones = ["A1", "A2", "A3", "B1", "B2", "B3", "C1", "C2", "Estantería 1", "Estantería 2"]
        for u in ubicaciones:
            cur.execute("INSERT INTO ubicaciones(nombre) VALUES(?)", (u,))
        print(f"   ✅ {len(ubicaciones)} ubicaciones")
    
    # 6. Operarios de ejemplo
    print("👷 Creando operarios de ejemplo...")
    cur.execute("SELECT COUNT(*) FROM operarios")
    if cur.fetchone()[0] == 0:
        operarios = [
            ("José Martínez", "oficial"),
            ("Pedro Sánchez", "oficial"),
            ("Luis García", "oficial"),
            ("Antonio Rodríguez", "oficial"),
            ("Manuel López", "oficial"),
            ("Carlos Fernández", "ayudante"),
            ("Miguel Pérez", "ayudante"),
            ("David González", "ayudante"),
            ("Javier Moreno", "ayudante"),
            ("Sergio Romero", "ayudante"),
        ]
        for nombre, rol in operarios:
            cur.execute(
                "INSERT INTO operarios(nombre, rol_operario, activo) VALUES(?,?,1)",
                (nombre, rol)
            )
        print(f"   ✅ {len(operarios)} operarios (5 oficiales + 5 ayudantes)")
    
    # 7. Artículos de ejemplo
    print("📦 Creando artículos de ejemplo...")
    cur.execute("SELECT COUNT(*) FROM articulos")
    if cur.fetchone()[0] == 0:
        # Obtener IDs de proveedores, familias y ubicaciones
        cur.execute("SELECT id FROM proveedores LIMIT 1")
        prov_id = cur.fetchone()[0]
        
        cur.execute("SELECT id FROM familias WHERE nombre='Tubería y Racores'")
        familia_tub = cur.fetchone()[0]
        
        cur.execute("SELECT id FROM familias WHERE nombre='Elementos de Fijación'")
        familia_fij = cur.fetchone()[0]
        
        cur.execute("SELECT id FROM ubicaciones LIMIT 1")
        ubic_id = cur.fetchone()[0]
        
        articulos = [
            # (ean, ref, nombre, palabras_clave, u_medida, min_alerta, ubic, prov, familia, marca, coste, pvp, iva)
            ("8412345678901", "CUP-32-90", "Codo 90° cobre 32mm", "codo, curva, racor", "unidad", 10, ubic_id, prov_id, familia_tub, "CopperPro", 2.50, 4.50, 21),
            ("8412345678902", "TUB-15-5M", "Tubo cobre 15mm 5m", "tubo, tubería, barra", "metro", 50, ubic_id, prov_id, familia_tub, "CopperPro", 3.80, 6.50, 21),
            (None, "TORN-4x40", "Tornillo 4x40mm", "tornillo, autorroscante, fijación", "unidad", 100, ubic_id, prov_id, familia_fij, "FixPro", 0.05, 0.12, 21),
            ("8412345678903", "PERFO-48", "Perfil Omega 48mm", "montante, barra omega, pladur, perfil vertical", "unidad", 20, ubic_id, prov_id, familia_tub, "Pladur", 3.20, 5.80, 21),
            (None, "SIL-280", "Silicona neutra 280ml", "silicona, sellador, cartucho", "unidad", 15, ubic_id, prov_id, familia_tub, "Sika", 4.50, 8.00, 21),
        ]
        
        for art in articulos:
            cur.execute("""
                INSERT INTO articulos(ean, ref_proveedor, nombre, palabras_clave, u_medida, 
                                     min_alerta, ubicacion_id, proveedor_id, familia_id, 
                                     marca, coste, pvp_sin, iva, activo)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,1)
            """, art)
        
        print(f"   ✅ {len(articulos)} artículos de ejemplo")
    
    # Guardar cambios
    con.commit()
    con.close()
    
    print("\n✅ Base de datos inicializada correctamente!")
    print(f"📁 Ubicación: {DB_PATH}")
    print("\n🔐 Credenciales:")
    print("   Admin: admin / admin")
    print("   Almacén: almacen / 1234")

if __name__ == "__main__":
    main()