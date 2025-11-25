# Informe de Revisión de Código - ClimatotAlmacen

**Fecha**: 2025-01-21
**Auditor**: Claude (Asistente IA)
**Alcance**: Revisión completa del código fuente

---

## Resumen Ejecutivo

Se ha realizado una auditoría exhaustiva del código del sistema ClimatotAlmacen. Se identificaron **problemas críticos, mejoras de arquitectura y optimizaciones** que pueden mejorar significativamente la calidad, seguridad y mantenibilidad del código.

### Métricas del Proyecto
- **Archivos Python**: ~100 archivos activos en `src/`
- **Base de datos**: PostgreSQL (migrado desde SQLite)
- **Framework UI**: PySide6 (Qt)
- **Arquitectura**: Patrón Repository + Services

---

## 1. PROBLEMAS CRÍTICOS 🔴

### 1.1 Manejo de Excepciones Genérico
**Severidad**: Alta
**Ubicación**: Multiple files

**Problema**:
```python
except:  # ❌ Captura TODOS los errores, incluso KeyboardInterrupt
    pass

except Exception:  # ❌ Demasiado genérico
    pass
```

**Archivos afectados**:
- `src/dialogs/dialogo_historial.py` (líneas 185, 278)
- `src/core/db_utils.py` (líneas 170, 253)
- `src/repos/consumos_repo.py` (línea 488)
- `src/ventanas/operativas/ventana_inventario.py` (líneas 297, 316, 781, 814)
- `src/ventanas/operativas/ventana_recepcion.py` (líneas 273, 445)
- Y muchos más...

**Impacto**:
- Oculta errores reales
- Dificulta el debugging
- Puede capturar excepciones del sistema (KeyboardInterrupt, SystemExit)

**Recomendación**:
```python
# ✅ CORRECTO
except (psycopg2.Error, ValueError, KeyError) as e:
    logger.error(f"Error específico: {e}")
    # Manejar el error apropiadamente
```

---

### 1.2 Gestión de Conexiones a Base de Datos
**Severidad**: Media-Alta
**Ubicación**: `src/core/db_utils.py`

**Problema**:
El pool de conexiones se inicializa correctamente, pero hay riesgo de fugas de conexiones si ocurren excepciones antes del `finally`.

**Código actual**:
```python
def fetch_all(query: str, params: tuple = ()) -> List[Dict[str, Any]]:
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, params)
            rows = cur.fetchall()
            return [dict(row) for row in rows]
    except Exception as e:
        log_error(f"Error ejecutando fetch_all: {e}")
        raise  # ✅ Bien: relanza la excepción
    finally:
        release_connection(conn)  # ✅ Bien: siempre libera
```

**Estado**: ✅ Bien implementado

---

### 1.3 Seguridad: Hash de Contraseñas
**Severidad**: CRÍTICA 🔥
**Ubicación**: `src/core/db_utils.py:260`

**Problema**:
```python
def hash_pwd(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()
```

**Vulnerabilidades**:
1. **SHA256 NO es seguro para contraseñas**: Es demasiado rápido y vulnerable a ataques de fuerza bruta
2. **Sin salt**: Contraseñas idénticas generan el mismo hash (rainbow tables)
3. **Sin iteraciones**: Un atacante puede probar millones de contraseñas por segundo

**Recomendación URGENTE**:
```python
import bcrypt

def hash_pwd(password: str) -> str:
    """Hash seguro de contraseñas usando bcrypt"""
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_pwd(password: str, hashed: str) -> bool:
    """Verifica una contraseña contra su hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
```

**O usar argon2** (recomendado en 2025):
```python
from argon2 import PasswordHasher

ph = PasswordHasher()

def hash_pwd(password: str) -> str:
    return ph.hash(password)

def verify_pwd(password: str, hashed: str) -> bool:
    try:
        ph.verify(hashed, password)
        return True
    except:
        return False
```

---

### 1.4 TODOs y Código Incompleto
**Severidad**: Media

**Hallazgos**:
1. `src/ventanas/consultas/ventana_historico.py:216` - Filtro de artículos por texto no implementado
2. `src/ventanas/operativas/ventana_inventario.py:606` - Usuario hardcodeado como fallback
3. Búsqueda de artículos por texto en histórico deshabilitada

**Recomendación**: Priorizar completar funcionalidades críticas.

---

## 2. PROBLEMAS DE ARQUITECTURA 🟡

### 2.1 Gestión de Sesión e Inactividad
**Ubicación**: `src/core/idle_manager.py`, `app.py`

**Estado actual**: ✅ **DESHABILITADO** (por solicitud del usuario)

El código del `idle_manager` está completo y funcional pero fue deshabilitado. Esto está bien documentado en el código:
```python
# NO iniciar el gestor de inactividad - deshabilitado por solicitud del usuario
```

**Recomendación**: Si en el futuro se desea reactivar, el código está listo.

---

### 2.2 Validación de Datos
**Severidad**: Media
**Ubicación**: Múltiples ventanas operativas

**Problema**: Las validaciones están dispersas en la capa de UI en lugar de estar centralizadas.

**Ejemplo actual**:
```python
# En ventana_recepcion.py
if not articulo_nombre:
    QMessageBox.warning(self, "Validación", "Seleccione un artículo")
    return

if cantidad <= 0:
    QMessageBox.warning(self, "Validación", "La cantidad debe ser positiva")
    return
```

**Recomendación**: Crear validadores centralizados:
```python
# src/validators/movimientos_validator.py
class MovimientoValidator:
    @staticmethod
    def validate_entrada(articulo_id: int, cantidad: float, almacen_dest: int) -> tuple[bool, str]:
        if not articulo_id:
            return False, "Debe seleccionar un artículo"
        if cantidad <= 0:
            return False, "La cantidad debe ser positiva"
        if not almacen_dest:
            return False, "Debe seleccionar un almacén destino"
        return True, ""
```

---

### 2.3 Código Duplicado
**Severidad**: Media

Se detectó código similar en múltiples ventanas para:
- Carga de combos (almacenes, operarios, artículos)
- Validación de formularios
- Formateo de tablas

**Recomendación**: Crear mixins o clases base:
```python
# src/ui/mixins.py
class CombosLoaderMixin:
    def cargar_almacenes(self, combo: QComboBox, incluir_todos: bool = False):
        """Método reutilizable para cargar almacenes"""
        if incluir_todos:
            combo.addItem("Todos", None)
        almacenes = almacenes_service.obtener_almacenes()
        for alm in almacenes:
            combo.addItem(alm['nombre'], alm['id'])
```

---

## 3. MEJORAS DE RENDIMIENTO ⚡

### 3.1 Queries N+1
**Severidad**: Media
**Ubicación**: Varios repositorios

**Problema**: En algunos casos se hacen múltiples queries cuando se podría hacer una sola con JOIN.

**Ejemplo potencial**:
```python
# ❌ N+1 Problem
articulos = get_articulos()
for art in articulos:
    proveedor = get_proveedor(art['proveedor_id'])  # Query por cada artículo
```

**Solución**: Ya implementado correctamente en la mayoría de repos con JOINS:
```python
# ✅ CORRECTO en src/repos/articulos_repo.py
SELECT a.*, p.nombre as proveedor_nombre, f.nombre as familia_nombre
FROM articulos a
LEFT JOIN proveedores p ON a.proveedor_id = p.id
LEFT JOIN familias f ON a.familia_id = f.id
```

**Estado**: ✅ Mayormente correcto

---

### 3.2 Índices de Base de Datos
**Estado**: ✅ **CORRECTO**

Los índices críticos están bien definidos en `schema_postgres.sql`:
```sql
CREATE INDEX idx_movimientos_articulo ON movimientos(articulo_id);
CREATE INDEX idx_movimientos_fecha ON movimientos(fecha);
CREATE INDEX idx_articulos_nombre ON articulos(nombre);
```

---

## 4. PROBLEMAS DE LA MIGRACIÓN SQLite → PostgreSQL 🔧

### 4.1 PRIMARY KEYs y FOREIGN KEYs Faltantes
**Severidad**: CRÍTICA (Ya corregida ✅)

**Problema detectado**:
- PRIMARY KEY incorrecta en `asignaciones_furgoneta`
- 15 FOREIGN KEYs faltantes
- Tabla `historial` sin PRIMARY KEY

**Estado**: ✅ **CORREGIDO** mediante scripts:
- `fix_asignaciones_constraint.py`
- `fix_schema_completo.py`
- `verificar_schema_postgres.py`

**Pendiente**:
- `furgonetas.almacen_id` FK (tabla legacy, no crítico)

---

## 5. SEGURIDAD 🔒

### 5.1 Inyección SQL
**Estado**: ✅ **SEGURO**

Uso correcto de consultas parametrizadas en todos los repos:
```python
# ✅ CORRECTO
cur.execute("SELECT * FROM articulos WHERE id = %s", (articulo_id,))
```

No se encontró concatenación de strings en queries SQL.

---

### 5.2 Gestión de Sesiones
**Estado**: ✅ **CORRECTO**

Sistema de sesiones bien implementado en `src/core/session_manager.py`:
- Gestión centralizada
- Almacenamiento en BD
- Tracking de usuarios conectados

---

## 6. BUENAS PRÁCTICAS ENCONTRADAS ✅

1. **Separación de responsabilidades**: Arquitectura clara Repos → Services → UI
2. **Pool de conexiones**: Bien implementado con psycopg2.pool
3. **Logging**: Sistema de logs estructurado con niveles
4. **Type hints**: Uso de tipos en la mayoría de funciones
5. **Documentación**: Docstrings en funciones críticas
6. **Vistas de BD**: Uso inteligente de vistas para cálculo de stock
7. **Transacciones**: Commit/rollback correcto en operaciones de escritura

---

## 7. RECOMENDACIONES PRIORITARIAS 📋

### Prioridad CRÍTICA 🔥
1. **Cambiar hash de contraseñas de SHA256 a bcrypt/argon2**
2. Completar funcionalidad de filtro de artículos en histórico

### Prioridad ALTA 🟠
3. Mejorar manejo de excepciones específicas (eliminar `except:` genéricos)
4. Crear validadores centralizados
5. Añadir tests unitarios (actualmente ausentes)

### Prioridad MEDIA 🟡
6. Refactorizar código duplicado en carga de combos
7. Crear clases base/mixins para ventanas comunes
8. Documentar parámetros de configuración en config.ini

### Prioridad BAJA 🟢
9. Añadir type hints en código legacy
10. Mejorar nombres de variables en español (inconsistencia con inglés)
11. Considerar internacionalización (i18n) para strings de UI

---

## 8. MÉTRICAS DE CALIDAD 📊

| Aspecto | Calificación | Comentario |
|---------|--------------|------------|
| Arquitectura | 8/10 | Buena separación de capas |
| Seguridad | 4/10 | ⚠️ Hash de contraseñas débil |
| Manejo de errores | 5/10 | Muchos except genéricos |
| Mantenibilidad | 7/10 | Código claro pero duplicado |
| Rendimiento | 8/10 | Queries optimizados, buenos índices |
| Testing | 0/10 | ❌ Sin tests automatizados |
| Documentación | 6/10 | Docstrings presentes pero incompletos |

**Calificación General**: **6.5/10** - ACEPTABLE con áreas críticas a mejorar

---

## 9. PLAN DE ACCIÓN SUGERIDO

### Semana 1: Seguridad Crítica
- [ ] Migrar hash de contraseñas a bcrypt
- [ ] Script de migración para re-hashear contraseñas existentes
- [ ] Actualizar servicio de autenticación

### Semana 2: Manejo de Errores
- [ ] Crear excepciones personalizadas
- [ ] Reemplazar `except:` por excepciones específicas
- [ ] Añadir logging estructurado en excepciones

### Semana 3: Tests
- [ ] Setup de pytest
- [ ] Tests unitarios para servicios críticos
- [ ] Tests de integración para repos

### Semana 4: Refactorización
- [ ] Crear mixins para código duplicado
- [ ] Validadores centralizados
- [ ] Documentación actualizada

---

## 10. CONCLUSIÓN

El sistema ClimatotAlmacen tiene una **arquitectura sólida** y un **diseño bien estructurado**. Los problemas principales son:

1. **Seguridad de contraseñas** (CRÍTICO)
2. **Manejo de excepciones** (necesita mejora)
3. **Falta de tests** (riesgo de regresiones)

Con las correcciones sugeridas, el sistema alcanzaría un nivel de **calidad profesional de 8.5/10**.

---

**Fin del informe**
