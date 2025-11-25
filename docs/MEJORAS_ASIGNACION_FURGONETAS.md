# Mejoras en Asignación de Furgonetas

**Fecha**: 2025-01-24
**Estado**: ✅ Completado

---

## 📋 Resumen de Cambios

Se ha implementado una lógica inteligente de asignación de furgonetas a operarios que maneja automáticamente conflictos de turnos y previene errores en las asignaciones.

---

## 🎯 Funcionalidades Implementadas

### 1. **Manejo Inteligente de Conflictos de Turnos**

#### Caso 1: Día Completo → Turno Parcial
**Situación**: Operario tiene asignación de "día completo" y se le asigna un turno parcial

**Comportamiento Anterior**: ❌ Sobrescribía o causaba error

**Comportamiento Nuevo**: ✅ Divide automáticamente

- **Si se asigna "tarde"**:
  - Cambia "día completo" → "mañana" (automático)
  - Agrega nueva asignación de "tarde"

- **Si se asigna "mañana"**:
  - Cambia "día completo" → "tarde" (automático)
  - Agrega nueva asignación de "mañana"

**Ejemplo**:
```
Estado inicial: Operario A → Furgoneta 1 (día completo)
Acción: Asignar Furgoneta 2 (tarde)
Resultado:
  - Operario A → Furgoneta 1 (mañana)  ✅ Automático
  - Operario A → Furgoneta 2 (tarde)   ✅ Nueva
```

#### Caso 2: Día Completo → Otro Día Completo
**Situación**: Operario tiene "día completo" y se intenta asignar otra furgoneta como "día completo"

**Comportamiento**: ⚠️ Requiere confirmación del usuario

Se muestra un diálogo de confirmación:
```
⚠️ Confirmar Cambio de Furgoneta

El operario Antonio Rodríguez ya tiene asignada la furgoneta:
  🚚 Furgoneta 1 - ABC123 (Día completo)

¿Deseas cambiarla por la furgoneta seleccionada?
  🚚 Furgoneta 2 - XYZ789 (Día completo)

Esto eliminará la asignación anterior.

[Sí] [No]
```

Si el usuario confirma:
- Elimina la asignación anterior
- Crea la nueva asignación

#### Caso 3: Turnos Compatibles
**Situación**: Se asignan turnos que no entran en conflicto

**Comportamiento**: ✅ Asignación directa sin confirmación

Ejemplos válidos:
- Tiene "mañana" → Asignar "tarde" ✅
- Tiene "tarde" → Asignar "mañana" ✅
- No tiene asignación → Asignar cualquier turno ✅

---

## 🛠️ Archivos Modificados

### 1. **[src/repos/asignaciones_repo.py](../src/repos/asignaciones_repo.py)**

**Nueva función añadida**:
```python
def verificar_asignacion_operario_fecha(operario_id: int, fecha: str) -> Optional[Dict[str, Any]]:
    """
    Verifica si un operario ya tiene asignación en una fecha específica.
    Retorna información completa de la asignación existente.
    """
```

**Función modificada**:
```python
def asignar_furgoneta(
    operario_id: int,
    fecha: str,
    furgoneta_id: int,
    turno: str = 'completo',
    forzar: bool = False  # ← NUEVO parámetro
) -> bool:
```

**Lógica implementada**:
- ✅ Verificación de asignaciones existentes
- ✅ División automática de "día completo" en turnos parciales
- ✅ Validación de conflictos con opción de forzar
- ✅ Logging detallado de todas las operaciones

---

### 2. **[src/services/furgonetas_service.py](../src/services/furgonetas_service.py)**

**Función actualizada**:
```python
def asignar_furgoneta_a_operario(
    operario_id: int,
    furgoneta_id: int,
    fecha: str,
    turno: str = 'completo',
    forzar: bool = False  # ← NUEVO parámetro
) -> bool:
```

**Cambios**:
- Propaga el parámetro `forzar` al repositorio
- Mantiene la misma interfaz pública

---

### 3. **[src/ventanas/operativas/ventana_movimientos.py](../src/ventanas/operativas/ventana_movimientos.py)**

**Función del diálogo modificada**:
```python
def asignar(forzar_asignacion=False):  # ← NUEVO parámetro
    # ...
    try:
        asignar_furgoneta_a_operario(
            operario_id, furgoneta_id, fecha, turno,
            forzar=forzar_asignacion  # ← Pasa el flag
        )
    except ValueError as e:
        # ← NUEVO: Manejo de conflictos
        if e.startswith("CONFLICTO_DIA_COMPLETO"):
            # Mostrar diálogo de confirmación
            # Si acepta, reintentar con forzar=True
```

**Mejoras en UX**:
- ✅ Detección automática de conflictos
- ✅ Diálogo de confirmación informativo
- ✅ Opción de cancelar o confirmar el cambio
- ✅ Actualización automática de la UI tras asignación

---

## 📊 Tabla de Comportamientos

| Asignación Actual | Nueva Asignación | Comportamiento |
|-------------------|------------------|----------------|
| *(Ninguna)* | Cualquier turno | ✅ Asigna directamente |
| Mañana | Tarde | ✅ Asigna directamente (2 turnos) |
| Tarde | Mañana | ✅ Asigna directamente (2 turnos) |
| Día completo | Mañana | 🔄 Cambia "completo" → "tarde" + Asigna "mañana" |
| Día completo | Tarde | 🔄 Cambia "completo" → "mañana" + Asigna "tarde" |
| Día completo | Día completo | ⚠️ Requiere confirmación del usuario |
| Mañana | Mañana (otra furg.) | 🔄 Sobrescribe con nueva furgoneta |
| Tarde | Tarde (otra furg.) | 🔄 Sobrescribe con nueva furgoneta |

---

## 🔍 Casos de Uso

### Caso 1: Dividir Jornada Completa
**Escenario**:
- Antonio tiene Furgoneta 1 asignada para el día completo
- Se necesita que vaya con Furgoneta 2 por la tarde

**Acción**:
1. Abrir "Asignar Furgoneta" para Antonio
2. Seleccionar Furgoneta 2
3. Seleccionar turno "🌆 Tarde"
4. Clic en "✅ Asignar"

**Resultado**:
```sql
-- Antes
operario_id | fecha      | turno    | furgoneta_id
1          | 2025-01-24 | completo | 1

-- Después (automático)
operario_id | fecha      | turno  | furgoneta_id
1          | 2025-01-24 | manana | 1
1          | 2025-01-24 | tarde  | 2
```

---

### Caso 2: Cambiar Furgoneta de Día Completo
**Escenario**:
- Antonio tiene Furgoneta 1 para el día completo
- Necesita cambiar a Furgoneta 2 también para el día completo

**Acción**:
1. Abrir "Asignar Furgoneta" para Antonio
2. Seleccionar Furgoneta 2
3. Seleccionar turno "🕐 Día completo"
4. Clic en "✅ Asignar"
5. ⚠️ Aparece diálogo de confirmación
6. Clic en "Sí" para confirmar

**Resultado**:
```sql
-- Antes
operario_id | fecha      | turno    | furgoneta_id
1          | 2025-01-24 | completo | 1

-- Después (tras confirmar)
operario_id | fecha      | turno    | furgoneta_id
1          | 2025-01-24 | completo | 2
```

---

## 🎁 Beneficios

### Para el Usuario
✅ **Menos errores**: El sistema previene asignaciones conflictivas
✅ **Más rápido**: No necesita eliminar manualmente asignaciones antiguas
✅ **Más claro**: Diálogos informativos explican exactamente qué va a pasar
✅ **Más seguro**: Requiere confirmación para cambios importantes

### Para el Sistema
✅ **Datos consistentes**: No hay asignaciones superpuestas inválidas
✅ **Logging completo**: Todas las operaciones quedan registradas
✅ **Código limpio**: Lógica centralizada en el repositorio
✅ **Fácil mantenimiento**: Comportamientos bien documentados

---

## 📝 Notas Técnicas

### Formato de Error para Conflictos
```python
"CONFLICTO_DIA_COMPLETO|{nombre_furgoneta_actual}|{id_furgoneta_nueva}"
```

Este formato permite al diálogo parsear la información y mostrar un mensaje claro al usuario.

### Manejo de Transacciones
Todas las operaciones usan `execute_query` de `db_utils`, que maneja automáticamente:
- Commits de transacciones
- Rollbacks en caso de error
- Logging de excepciones

### Compatibilidad
✅ Compatible con PostgreSQL
✅ Usa constraint único: `(fecha, turno, furgoneta_id)`
✅ Maneja conflictos con `ON CONFLICT` cuando es apropiado

---

## 🚀 Pruebas Recomendadas

### Test 1: División Automática
1. Asignar operario con día completo
2. Asignar mismo operario con turno tarde (otra furgoneta)
3. Verificar que tiene dos registros: mañana + tarde

### Test 2: Confirmación de Cambio
1. Asignar operario con día completo
2. Intentar asignar otra furgoneta también día completo
3. Verificar que aparece diálogo de confirmación
4. Cancelar y verificar que mantiene asignación original
5. Repetir y confirmar, verificar que cambia correctamente

### Test 3: Turnos Independientes
1. Asignar operario turno mañana
2. Asignar mismo operario turno tarde (otra furgoneta)
3. Verificar que ambas asignaciones coexisten

---

## 📚 Documentación Relacionada

- [Schema PostgreSQL](../db/schema_postgres_full.sql) - Estructura de tabla `asignaciones_furgoneta`
- [Ventana de Asignaciones](../src/ventanas/consultas/ventana_asignaciones.py) - Consulta de asignaciones históricas

---

## ✅ Estado

**Implementación**: ✅ Completada
**Testing**: ⏳ Pendiente (pruebas manuales en producción)
**Documentación**: ✅ Completa

---

**Desarrollado por**: Claude Code Assistant
**Fecha**: 2025-01-24
