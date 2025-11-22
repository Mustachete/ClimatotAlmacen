# 🚀 Guía de Migración a PostgreSQL

Este documento te guía paso a paso para migrar tu sistema de almacén de SQLite a PostgreSQL para soportar multiusuario en servidor.

## 📋 Estado Actual del Código

✅ **Completado por Claude:**
- Capa de abstracción de BD (`src/core/db_utils.py`) con soporte dual SQLite/PostgreSQL
- Schema PostgreSQL (`db/schema_postgres.sql`) adaptado desde SQLite
- Repositorio de sesiones (`src/repos/sesiones_repo.py`)
- Adaptaciones en `app.py` y `asignaciones_repo.py` para compatibilidad
- Scripts de inicialización, migración y testing
- `.gitignore` actualizado para proteger credenciales
- `requirements.txt` con `psycopg2-binary` y `python-dotenv`

⚠️ **Pendiente (TÚ debes hacer):**
1. Instalar dependencias Python
2. Verificar PostgreSQL en tu sistema
3. Crear base de datos PostgreSQL
4. Ejecutar scripts de migración
5. Probar la aplicación

---

## 📝 PASO 1: Instalar Dependencias Python

Abre tu terminal en la carpeta del proyecto y ejecuta:

```bash
pip install -r requirements.txt
```

Esto instalará:
- `psycopg2-binary==2.9.9` (driver PostgreSQL)
- `python-dotenv==1.0.0` (gestión de configuración)

**Verificar instalación:**
```bash
python -c "import psycopg2; print('✅ psycopg2 instalado correctamente')"
```

---

## 🗄️ PASO 2: Verificar PostgreSQL

### Opción A: Usando pgAdmin

1. Abre pgAdmin (si lo tienes instalado)
2. Verifica que puedas conectar al servidor PostgreSQL local
3. Anota el puerto (normalmente 5432)

### Opción B: Usando línea de comandos

```bash
# En Windows (si tienes psql en PATH)
psql --version

# Verificar servicio
# Abre "Servicios" de Windows y busca "postgresql"
# Asegúrate que esté "En ejecución"
```

### Si NO tienes PostgreSQL instalado:

Descarga e instala desde: https://www.postgresql.org/download/windows/

Durante la instalación:
- Anota la contraseña del usuario `postgres`
- Puerto por defecto: 5432
- Marca "pgAdmin 4" para instalar la herramienta gráfica

---

## 🔧 PASO 3: Crear Base de Datos PostgreSQL

### Opción A: Usando pgAdmin (Recomendado para Windows)

1. Abre pgAdmin
2. Conecta al servidor PostgreSQL
3. Click derecho en "Databases" → "Create" → "Database..."
4. **Name:** `climatot_almacen_dev`
5. **Owner:** postgres
6. Click "Save"
7. Ahora crea el usuario:
   - Click derecho en "Login/Group Roles" → "Create" → "Login/Group Role..."
   - **Name:** `climatot`
   - Pestaña "Definition" → **Password:** `Eduard90`
   - Pestaña "Privileges" → Marca: "Can login?"
   - Click "Save"
8. Dar permisos al usuario:
   - Click derecho en `climatot_almacen_dev` → "Properties"
   - Pestaña "Security" → Click "+"
   - **Grantee:** climatot
   - **Privileges:** ALL
   - Click "Save"

### Opción B: Usando SQL (si tienes psql)

```sql
-- Conectar a PostgreSQL como superusuario
-- psql -U postgres

CREATE DATABASE climatot_almacen_dev;
CREATE USER climatot WITH PASSWORD 'Eduard90';
GRANT ALL PRIVILEGES ON DATABASE climatot_almacen_dev TO climatot;

-- En PostgreSQL 15+, también necesitas:
\c climatot_almacen_dev
GRANT ALL ON SCHEMA public TO climatot;
```

---

## 📄 PASO 4: Verificar config.ini

Tu archivo `config.ini` ya está creado en la raíz del proyecto:

```ini
[database]
ENGINE = postgres
HOST = localhost
PORT = 5432
NAME = climatot_almacen_dev
USER = climatot
PASSWORD = Eduard90
```

**Si necesitas cambiar algo (ej: password diferente):**
1. Abre `config.ini` con un editor de texto
2. Modifica los valores según tu instalación de PostgreSQL
3. Guarda el archivo

⚠️ **IMPORTANTE:** NO subas `config.ini` a Git (ya está en `.gitignore`)

---

## 🚀 PASO 5: Ejecutar Migración

### 5.1 Inicializar la Base de Datos PostgreSQL

```bash
python scripts/init_postgres.py
```

**Salida esperada:**
```
======================================
  INICIALIZACIÓN DE BASE DE DATOS POSTGRESQL
======================================

📋 Configuración:
   Host: localhost
   Puerto: 5432
   Base de datos: climatot_almacen_dev
   Usuario: climatot

📄 Schema encontrado: schema_postgres.sql

🔌 Conectando a PostgreSQL...
✅ Conexión establecida

📝 Leyendo schema...
⚙️  Ejecutando schema SQL...
✅ Schema ejecutado correctamente

✅ 15 tablas creadas:
   • albaranes
   • almacenes
   • articulos
   • asignaciones_furgoneta
   • familias
   ...
```

**Si hay errores:**
- ❌ Error de conexión → Verifica que PostgreSQL esté corriendo
- ❌ Error de autenticación → Verifica usuario/password en `config.ini`
- ❌ Error de permisos → Asegúrate de haber dado permisos al usuario `climatot`

---

### 5.2 Migrar los Datos desde SQLite

```bash
python scripts/migrate_sqlite_to_postgres.py
```

**Salida esperada:**
```
======================================
  MIGRACIÓN DE DATOS: SQLite → PostgreSQL
======================================

📁 Base de datos SQLite: db/almacen.db
   Tamaño: 548.00 KB

🔌 Conectando a SQLite...
✅ SQLite conectado

🔌 Conectando a PostgreSQL...
✅ PostgreSQL conectado

📋 Migrando tablas...

✅ usuarios                       -      3 registros migrados
✅ proveedores                    -     15 registros migrados
✅ operarios                      -      8 registros migrados
✅ familias                       -     12 registros migrados
✅ articulos                      -    245 registros migrados
✅ movimientos                    -   1523 registros migrados
...

🔄 Actualizando secuencias (SERIAL)...
   ✅ usuarios
   ✅ proveedores
   ✅ articulos
   ...

======================================
  ✅ MIGRACIÓN COMPLETADA
======================================

📊 Estadísticas:
   Tablas migradas: 12
   Registros totales: 1,834
```

**Si hay errores:**
- Si una tabla falla, el script intentará insertar fila por fila
- Revisa los mensajes de error para identificar filas problemáticas
- Puedes ejecutar el script varias veces (no duplicará datos si usas TRUNCATE antes)

---

### 5.3 Validar la Migración

```bash
python scripts/test_postgres_migration.py
```

**Salida esperada:**
```
======================================
  VALIDACIÓN DE MIGRACIÓN: SQLite vs PostgreSQL
======================================

🔌 Conectando a SQLite...
✅ SQLite conectado
🔌 Conectando a PostgreSQL...
✅ PostgreSQL conectado

📊 Comparando conteo de registros...

Tabla                          SQLite PostgreSQL Estado
----------------------------------------------------------------------
usuarios                            3          3  ✅
proveedores                        15         15  ✅
operarios                           8          8  ✅
articulos                         245        245  ✅
movimientos                      1523       1523  ✅
...

======================================
  ✅ VALIDACIÓN EXITOSA
======================================

🎉 Todas las tablas tienen el mismo número de registros

🔍 Tests de integridad adicionales...

✅ Usuarios activos: 3
✅ Artículos activos: 245
✅ Vista vw_stock_total funciona: 245 artículos con stock
✅ Foreign keys funcionan correctamente
✅ Secuencias funcionan correctamente (next=16, max=15)

======================================
  RESUMEN DE VALIDACIÓN
======================================

✅ Tests pasados: 5
❌ Tests fallidos: 0

🎉 ¡Migración completamente exitosa!

💡 Puedes cambiar config.ini a ENGINE=postgres y usar la aplicación
```

---

## ✅ PASO 6: Probar la Aplicación

### 6.1 Modo de Prueba (con SQLite como respaldo)

Para probar sin tocar tu SQLite original, crea una copia de `config.ini`:

```bash
# Renombra el actual (backup)
copy config.ini config.ini.postgres

# Crea uno temporal para SQLite
copy config.ini config.ini.sqlite
```

En `config.ini.sqlite` cambia:
```ini
ENGINE = sqlite
```

### 6.2 Ejecutar con PostgreSQL

Asegúrate que `config.ini` tiene `ENGINE = postgres`, luego:

```bash
python app.py
```

**Pruebas recomendadas:**
1. ✅ Login con tu usuario
2. ✅ Ver consulta de stock (verifica que muestra datos)
3. ✅ Ver histórico de movimientos
4. ✅ Crear un movimiento de prueba
5. ✅ Ver ficha de un artículo
6. ✅ Cerrar y volver a abrir (verificar sesiones)

### 6.3 Probar Multiusuario

**En la misma máquina:**
1. Abre 2 terminales diferentes
2. En cada una ejecuta: `python app.py`
3. Haz login con usuarios diferentes
4. Crea movimientos simultáneamente
5. Verifica que ambos ven los cambios en tiempo real

**En diferentes máquinas (misma red):**
1. En el servidor, edita `config.ini`:
   ```ini
   HOST = <IP_DEL_SERVIDOR>  # Ej: 192.168.1.100
   ```
2. Asegúrate de que el firewall permita conexiones al puerto 5432
3. En los clientes, crea `config.ini` con la IP del servidor
4. Ejecuta `python app.py` en cada cliente

---

## 🔧 TROUBLESHOOTING

### Problema: "psycopg2 no está instalado"

```bash
pip install psycopg2-binary
# Si falla, intenta:
pip install --upgrade pip
pip install psycopg2-binary --no-cache-dir
```

### Problema: "Error de conexión a PostgreSQL"

1. Verifica que el servicio esté corriendo:
   - Windows: Busca "Servicios" → "postgresql" debe estar "En ejecución"
   - O abre pgAdmin y verifica conexión

2. Verifica las credenciales en `config.ini`

3. Verifica el puerto (5432 por defecto):
   ```bash
   netstat -an | findstr 5432
   ```

### Problema: "Foreign key constraint violation"

Ejecuta la migración EN ORDEN:
```bash
# 1. Primero inicializa (crea tablas vacías)
python scripts/init_postgres.py

# 2. Luego migra los datos
python scripts/migrate_sqlite_to_postgres.py
```

### Problema: "Permission denied"

En PostgreSQL 15+, necesitas dar permisos explícitos al schema:
```sql
-- Conectar con pgAdmin o psql como postgres
\c climatot_almacen_dev
GRANT ALL ON SCHEMA public TO climatot;
GRANT ALL ON ALL TABLES IN SCHEMA public TO climatot;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO climatot;
```

### Problema: La app no conecta desde otro equipo

1. Edita `postgresql.conf`:
   ```
   listen_addresses = '*'
   ```

2. Edita `pg_hba.conf` y añade:
   ```
   host    all    all    192.168.1.0/24    md5
   ```
   (Ajusta la IP a tu red)

3. Reinicia PostgreSQL

4. Abre el puerto 5432 en el firewall

---

## 📚 SIGUIENTES PASOS

### Opción 1: Desarrollo Local (Usar ambas BD)

- SQLite para desarrollo individual rápido
- PostgreSQL para pruebas de multiusuario

Cambia `ENGINE` en `config.ini` según necesites.

### Opción 2: Migración Completa

1. Haz backup de SQLite:
   ```bash
   copy db\almacen.db db\almacen_backup.db
   ```

2. Usa solo PostgreSQL:
   - Deja `ENGINE = postgres` en `config.ini`
   - Configura backups automáticos de PostgreSQL

3. En producción:
   - Instala PostgreSQL en el servidor
   - Configura acceso remoto
   - Los clientes apuntan al servidor en `config.ini`

---

## 🛡️ SEGURIDAD

### Producción en Servidor

1. **NO uses la password `Eduard90` en producción**
   ```sql
   ALTER USER climatot WITH PASSWORD 'tu_password_seguro_aqui';
   ```

2. **Configura SSL/TLS:**
   En `postgresql.conf`:
   ```
   ssl = on
   ```

3. **Limita conexiones:**
   En `pg_hba.conf`:
   ```
   host    climatot_almacen_dev    climatot    192.168.1.0/24    md5
   ```

4. **Backups automáticos:**
   ```bash
   pg_dump -U climatot climatot_almacen_dev > backup_$(date +%Y%m%d).sql
   ```

---

## 📞 SOPORTE

Si tienes problemas, revisa:
1. Los logs de PostgreSQL (ubicación varía según SO)
2. El archivo `logs/app.log` de tu aplicación
3. Ejecuta `python src/core/db_utils.py` para test de conexión

---

## ✅ CHECKLIST FINAL

- [ ] Instalé `psycopg2-binary` con pip
- [ ] Verifiqué que PostgreSQL está corriendo
- [ ] Creé la base de datos `climatot_almacen_dev`
- [ ] Creé el usuario `climatot` con permisos
- [ ] Configuré `config.ini` correctamente
- [ ] Ejecuté `init_postgres.py` exitosamente
- [ ] Ejecuté `migrate_sqlite_to_postgres.py` exitosamente
- [ ] Ejecuté `test_postgres_migration.py` y pasó todos los tests
- [ ] Probé la aplicación con PostgreSQL
- [ ] Probé multiusuario (2 sesiones simultáneas)
- [ ] Hice backup de mi SQLite original

🎉 **¡Listo! Ya tienes tu sistema funcionando en PostgreSQL multiusuario**
