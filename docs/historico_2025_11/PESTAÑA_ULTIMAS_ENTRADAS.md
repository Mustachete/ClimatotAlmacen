# Pestaña "Últimas Entradas" en Ficha de Artículo

**Fecha de implementación:** 18 de noviembre de 2025

## Resumen

Se ha añadido una nueva pestaña "📦 Últimas Entradas" en la ventana de ficha de artículo que muestra un historial de las últimas 50 recepciones del artículo desde proveedores.

## Características Implementadas

### 1. **Nueva Consulta en Repositorio**

**Archivo:** [src/repos/articulos_repo.py](src/repos/articulos_repo.py:533-559)

Se agregó la función `get_ultimas_entradas(articulo_id, limit)`:

```python
def get_ultimas_entradas(articulo_id: int, limit: int = 50) -> List[Dict[str, Any]]:
    """
    Obtiene las últimas entradas (recepciones) de un artículo desde proveedores.

    Retorna:
        - fecha: Fecha de la recepción
        - cantidad: Cantidad recibida
        - proveedor: Nombre del proveedor
        - albaran: Número de albarán
        - coste_unit: Coste unitario
    """
```

**Query SQL:**
- Busca movimientos de tipo 'ENTRADA'
- Hace JOIN con la tabla proveedores para obtener el nombre
- Ordenado por fecha descendente (más recientes primero)
- Limitado a las últimas 50 entradas por defecto

### 2. **Nueva Pestaña en Ventana Ficha Artículo**

**Archivo:** [src/ventanas/consultas/ventana_ficha_articulo.py](src/ventanas/consultas/ventana_ficha_articulo.py:70-73)

Se añadió la 5ª pestaña "📦 Últimas Entradas" después de las pestañas existentes:
- ℹ️ Información General
- 📊 Stock por Almacén
- 📋 Historial de Movimientos
- 📈 Estadísticas
- **📦 Últimas Entradas** (NUEVA)

### 3. **Tabla con Información Detallada**

**Columnas de la tabla:**

| Columna | Descripción | Alineación | Ancho |
|---------|-------------|------------|-------|
| Fecha | Fecha de recepción (formato dd/mm/yyyy) | Centro | Ajustado |
| Cantidad | Cantidad recibida | Derecha | Ajustado |
| Proveedor | Nombre del proveedor | Izquierda | Expandible |
| Albarán | Número de albarán | Centro | Ajustado |
| Coste Unit. | Coste unitario en € | Derecha | Ajustado |

### 4. **Funcionalidades de la Tabla**

✅ **Ordenable por columnas**: Se puede hacer clic en cualquier cabecera para ordenar
✅ **Orden predeterminado**: Por fecha descendente (más reciente primero)
✅ **Colores alternados**: Mejora la legibilidad
✅ **Solo lectura**: No se pueden editar los datos
✅ **Selección por filas**: Al hacer clic se selecciona la fila completa
✅ **Límite de 50 entradas**: Muestra las últimas 50 recepciones

## Ejemplo de Visualización

```
Fecha        Cantidad    Proveedor              Albarán    Coste Unit.
───────────────────────────────────────────────────────────────────────
21/10/2025      30.00    FONTGAS                ALB-12345    12.50 €
10/10/2025      25.00    FONTGAS                ALB-12300    12.00 €
09/09/2025      50.00    Suministros FrioCalor  ALB-11895    11.75 €
```

## Implementación Técnica

### Métodos Añadidos

#### `crear_tab_entradas()` (líneas 553-586)
Crea la interfaz de la pestaña:
- Título descriptivo
- Tabla con 5 columnas
- Configuración de ordenamiento
- Ajuste automático de anchos de columna

#### `actualizar_ultimas_entradas()` (líneas 588-647)
Actualiza el contenido de la tabla:
- Obtiene datos del repositorio
- Formatea la fecha a formato español (dd/mm/yyyy)
- Rellena la tabla con los datos
- Aplica ordenamiento por fecha descendente

### Integración con el Sistema

La nueva pestaña se actualiza automáticamente cuando:
- Se selecciona un artículo diferente en el combo
- Se carga la ventana con un artículo específico

**Llamada en `cargar_articulo()`** (línea 126):
```python
self.actualizar_ultimas_entradas()
```

## Manejo de Datos Faltantes

El sistema maneja correctamente los casos donde:
- ✅ No hay proveedor asociado → Muestra "Sin proveedor"
- ✅ No hay número de albarán → Muestra "-"
- ✅ No hay coste unitario → Muestra "-"
- ✅ No hay entradas para el artículo → Tabla vacía (sin error)

## Archivos Modificados

1. **[src/repos/articulos_repo.py](src/repos/articulos_repo.py:533-559)**
   - Añadida función `get_ultimas_entradas()`

2. **[src/ventanas/consultas/ventana_ficha_articulo.py](src/ventanas/consultas/ventana_ficha_articulo.py)**
   - Líneas 70-73: Creación de nueva pestaña
   - Línea 126: Llamada a actualización
   - Líneas 553-586: Método `crear_tab_entradas()`
   - Líneas 588-647: Método `actualizar_ultimas_entradas()`

## Notas Técnicas

- La consulta SQL es eficiente usando índices existentes en la tabla movimientos
- El formato de fecha se convierte de ISO (YYYY-MM-DD) a español (DD/MM/YYYY)
- La ordenación es manejada por Qt, permitiendo ordenar por cualquier columna
- Los valores numéricos están alineados a la derecha para mejor lectura
- La tabla es responsive: la columna de proveedor se expande para usar espacio disponible

## Uso

1. Ir a **Informes → Ficha Completa de Artículo**
2. Seleccionar un artículo del combo
3. Hacer clic en la pestaña **"📦 Últimas Entradas"**
4. Ver el historial de recepciones
5. **(Opcional)** Hacer clic en las cabeceras de columna para ordenar

## Compatibilidad

- ✅ Compatible con la estructura actual de la BD
- ✅ No requiere cambios en esquema de base de datos
- ✅ Funciona con datos existentes y futuros
- ✅ No afecta otras funcionalidades del sistema
