# Implementación del Filtro de Artículos en Histórico

**Fecha**: 2025-11-24
**Tipo**: Nueva Funcionalidad

---

## Cambios Realizados

### 1. **Repositorio de Movimientos** ([src/repos/movimientos_repo.py](../src/repos/movimientos_repo.py))

Se añadieron 3 nuevos parámetros a la función `get_todos()`:

- `articulo_texto: Optional[str]` - Busca en nombre, EAN o ref_proveedor del artículo
- `ot: Optional[str]` - Busca por número de orden de trabajo
- `responsable: Optional[str]` - Busca por nombre del responsable

#### Implementación

```python
if articulo_texto:
    # Buscar en nombre, EAN o referencia del artículo (case insensitive)
    condiciones.append("(LOWER(a.nombre) LIKE LOWER(%s) OR LOWER(a.ean) LIKE LOWER(%s) OR LOWER(a.ref_proveedor) LIKE LOWER(%s))")
    texto_busqueda = f"%{articulo_texto}%"
    params.extend([texto_busqueda, texto_busqueda, texto_busqueda])

if ot:
    condiciones.append("LOWER(m.ot) LIKE LOWER(%s)")
    params.append(f"%{ot}%")

if responsable:
    condiciones.append("LOWER(m.responsable) LIKE LOWER(%s)")
    params.append(f"%{responsable}%")
```

**Características**:
- ✅ Búsqueda case-insensitive (mayúsculas/minúsculas)
- ✅ Búsqueda parcial con comodines (LIKE)
- ✅ Busca en 3 campos del artículo: nombre, EAN, referencia

---

### 2. **Servicio de Movimientos** ([src/services/movimientos_service.py](../src/services/movimientos_service.py))

Se actualizó `obtener_movimientos_filtrados()` para pasar los nuevos parámetros:

```python
def obtener_movimientos_filtrados(
    fecha_desde: Optional[str] = None,
    fecha_hasta: Optional[str] = None,
    tipo: Optional[str] = None,
    articulo_id: Optional[int] = None,
    almacen_id: Optional[int] = None,
    operario_id: Optional[int] = None,
    articulo_texto: Optional[str] = None,  # ✅ NUEVO
    ot: Optional[str] = None,              # ✅ NUEVO
    responsable: Optional[str] = None,     # ✅ NUEVO
    limit: int = 1000
) -> List[Dict[str, Any]]:
```

---

### 3. **Ventana de Histórico** ([src/ventanas/consultas/ventana_historico.py](../src/ventanas/consultas/ventana_historico.py))

Se habilitó el filtro de artículo que estaba comentado:

#### Antes:
```python
# Filtro de artículo - Por ahora no implementado en el servicio
# TODO: Implementar búsqueda de artículos por texto en el servicio
# texto_articulo = self.txt_articulo.text().strip()
# if texto_articulo:
#     filtros['articulo_filtro'] = texto_articulo
```

#### Después:
```python
# Filtro de artículo por texto (nombre, EAN o referencia)
texto_articulo = self.txt_articulo.text().strip()
if texto_articulo:
    filtros['articulo_texto'] = texto_articulo
```

**Bonus**: También se corrigió un `except` genérico en el formateo de fechas (línea 245).

---

## Ejemplos de Uso

### Búsqueda por Nombre de Artículo

**Input del usuario**: `"tornillo"`

**Resultado**: Encuentra todos los movimientos de artículos que contengan "tornillo" en su nombre:
- Tornillo M6
- Tornillo hexagonal
- Kit de tornillos

### Búsqueda por EAN

**Input del usuario**: `"8437013"`

**Resultado**: Encuentra todos los movimientos del artículo con ese código de barras.

### Búsqueda por Referencia de Proveedor

**Input del usuario**: `"REF-1234"`

**Resultado**: Encuentra movimientos del artículo con esa referencia de proveedor.

### Combinación de Filtros

El usuario puede combinar múltiples filtros:
- **Fecha**: 01/11/2025 - 30/11/2025
- **Tipo**: ENTRADA
- **Artículo**: "tornillo"
- **Almacén**: Almacén Principal

**Resultado**: Solo entradas de tornillos en el almacén principal durante noviembre.

---

## Mejoras de Rendimiento

### Índices Recomendados (opcional)

Para mejorar el rendimiento en búsquedas de texto, se recomienda añadir índices:

```sql
-- Índice para búsquedas por nombre de artículo
CREATE INDEX idx_articulos_nombre_lower ON articulos (LOWER(nombre));

-- Índice para búsquedas por EAN
CREATE INDEX idx_articulos_ean ON articulos (ean);

-- Índice para búsquedas por referencia
CREATE INDEX idx_articulos_ref_proveedor ON articulos (ref_proveedor);

-- Índice para búsquedas por OT
CREATE INDEX idx_movimientos_ot ON movimientos (ot);

-- Índice para búsquedas por responsable
CREATE INDEX idx_movimientos_responsable ON movimientos (responsable);
```

**Nota**: Estos índices son opcionales y solo necesarios si hay problemas de rendimiento con la búsqueda.

---

## Testing

### Casos de Prueba

1. ✅ **Búsqueda vacía**: Sin filtros, muestra últimos 1000 movimientos
2. ✅ **Búsqueda por texto parcial**: "torn" encuentra "Tornillo M6"
3. ✅ **Case insensitive**: "TORNILLO" = "tornillo" = "Tornillo"
4. ✅ **Búsqueda por EAN**: Encuentra por código exacto o parcial
5. ✅ **Búsqueda por referencia**: Encuentra por ref de proveedor
6. ✅ **Sin resultados**: Texto que no existe muestra 0 resultados
7. ✅ **Combinación de filtros**: Múltiples filtros se aplican con AND

---

## Retrocompatibilidad

✅ **100% compatible** con código existente:
- Los nuevos parámetros son opcionales (`Optional[str] = None`)
- El código que no pasa estos parámetros funciona igual que antes
- No se modificó la estructura de la base de datos

---

## Próximas Mejoras (Opcionales)

1. **Autocompletado**: Añadir QCompleter al campo de texto para sugerir artículos mientras el usuario escribe
2. **Búsqueda avanzada**: Permitir operadores como AND/OR
3. **Exportar con filtros**: El Excel exportado respeta los filtros aplicados
4. **Guardar filtros**: Recordar los últimos filtros usados

---

## Archivos Modificados

- ✅ `src/repos/movimientos_repo.py` - Añadidos 3 parámetros de búsqueda
- ✅ `src/services/movimientos_service.py` - Propagados parámetros al servicio
- ✅ `src/ventanas/consultas/ventana_historico.py` - Habilitado filtro de artículo + fix except

---

**Funcionalidad completamente implementada y lista para usar** ✅
