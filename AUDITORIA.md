# AUDITORÍA COMPLETA DEL CÓDIGO - ClimatotAlmacen

Fecha: 2025-11-14

## RESUMEN EJECUTIVO

Auditoría exhaustiva enfocada en:
1. Estilos CSS/Qt (centralización)
2. Arquitectura (separación de capas)
3. Complejidad (funciones largas)
4. Duplicación (código repetido)
5. Dependencias (imports correctos)

**Severidad general: ALTO**

---

## 1. AUDITORÍA DE ESTILOS CSS/Qt

### Estilos Centralizados (POSITIVO)
- Ubicación: src/ui/estilos.py (371 líneas)
- ESTILO_VENTANA, ESTILO_DIALOGO, ESTILO_LOGIN bien definidos

### PROBLEMA: Estilos Inline (CRÍTICO)
- Total setStyleSheet: 102 llamadas
- Que NO usan estilos.py: 86 (85%)

**Problemas principales:**
1. ventana_consumos.py: 188 líneas de estilos duplicados (5 tablas)
2. ventana_pedido_ideal.py: 26 líneas inline
3. Maestros (7 archivos): 18 llamadas inline
4. Operativas (5 archivos): 30+ llamadas inline

**Impacto:** Cambiar colores requiere editar 20+ archivos

---

## 2. AUDITORÍA DE ARQUITECTURA (CRÍTICO)

### Acceso Directo a BD desde Ventanas (VIOLACIÓN)

Patrón correcto: Ventana -> Service -> Repo -> BD
Patrón actual: Ventana -> BD (INCORRECTO)

**11 archivos violando esta regla:**

Operativas:
- ventana_inventario.py (línea 13: get_con)
- ventana_recepcion.py (línea 13: get_con)
- ventana_devolucion.py (línea 11: get_con)
- ventana_imputacion.py (línea 12: get_con)
- ventana_movimientos.py (línea 13: get_con)
- ventana_material_perdido.py (línea 13: get_con)

Consultas:
- ventana_stock.py (línea 12: get_con, SQL directo en cargar_familias/almacenes)
- ventana_asignaciones.py (acceso directo)
- ventana_historico.py (línea 13: get_con)

Configuración:
- dialogs_configuracion.py (línea 17: get_con, PRAGMA directo)

**Impacto:** Cambios en BD requieren modificar 11 ventanas

### Importación Directa de Repos (VIOLACIÓN)

**7 ventanas importan repos (debería ser solo services):**
- ventana_inventario.py -> inventarios_repo
- ventana_devolucion.py -> movimientos_repo
- ventana_imputacion.py -> movimientos_repo
- ventana_movimientos.py -> movimientos_repo
- ventana_asignaciones.py -> asignaciones_repo
- ventana_historico.py -> movimientos_repo
- ventana_ficha_articulo.py -> articulos_repo

**Impacto:** Bypass de la capa SERVICE

---

## 3. COMPLEJIDAD INNECESARIA (CRÍTICO)

### Funciones > 100 líneas (máximo recomendado: 50)

Crítico:
- ventana_asignaciones.py:__init__ - 162 líneas
- ventana_asignaciones.py:buscar - 122 líneas
- ventana_historico.py:__init__ - 153 líneas
- ventana_historico.py:buscar - 141 líneas
- ventana_stock.py:__init__ - 126 líneas
- ventana_stock.py:aplicar_filtros - 129 líneas

Importante:
- ventana_informe_furgonetas.py:mostrar_datos - 112 líneas
- ventana_ficha_articulo.py:crear_tab - 93 líneas
- ventana_ficha_articulo.py:actualizar_historial - 88 líneas
- ventana_pedido_ideal.py:_crear_tab - 86 líneas

### Archivos Excesivamente Grandes (> 300 líneas)

- ventana_consumos.py - 932 líneas
- ventana_inventario.py - 893 líneas
- ventana_pedido_ideal.py - 827 líneas
- ventana_movimientos.py - 753 líneas

### Anidación Compleja

- ventana_informe_furgonetas.py: loops anidados (O(n²))
- Múltiples diálogos: 150+ líneas en __init__

---

## 4. CÓDIGO DUPLICADO (MUY ALTO)

### Duplicación en Maestros

**7 ventanas maestros** (articulos, familias, operarios, proveedores, 
ubicaciones, furgonetas, usuarios) duplican exactamente el mismo patrón:

- cargar_* (2-6 métodos c/u)
- guardar
- eliminar
- mostrar_tabla
- limpiar_formulario

**Total: 1500+ líneas de código idéntico**

### Duplicación en Operativas

**5 ventanas operativas** (recepcion, devolucion, imputacion, 
movimientos, material_perdido) duplican:

- cargar_proveedores/operarios/ubicaciones
- __init__ (100+ líneas)
- articulos_temp = []
- agregar_articulo / quitar_articulo
- guardar con try/except

**Total: 2500+ líneas de código idéntico**

### Duplicación de Estilos

- ventana_consumos.py: 188 líneas de CSS idéntico (5 tablas)
- Patrón repetido en: QTabWidget, QTableWidget styling

**Total: 400+ líneas de estilos duplicados**

---

## 5. RESUMEN POR SEVERIDAD

### CRÍTICO (Requiere ahora)

1. Acceso directo a BD desde 11 ventanas
   - Impacto: Arquitectura quebrada
   - Estimación: 40 horas

2. 188 líneas de estilos duplicados en ventana_consumos
   - Impacto: Cambios visuales difíciles
   - Estimación: 3 horas

3. Funciones __init__ de 150+ líneas (5 ventanas)
   - Impacto: No testeable
   - Estimación: 20 horas

### IMPORTANTE (Próximo sprint)

4. 1500+ líneas código duplicado (maestros)
   - Impacto: Mantenimiento difícil
   - Estimación: 20 horas

5. 2500+ líneas código duplicado (operativas)
   - Impacto: Bugs se replican
   - Estimación: 25 horas

6. 7 ventanas importan repos directamente
   - Impacto: Dificulta cambios lógica negocio
   - Estimación: 8 horas

### MENOR (Mantenimiento)

7. Estilos inline pequeños (20+ ubicaciones)
   - Estimación: 5 horas

8. Anidación compleja
   - Estimación: 10 horas

---

## 6. RECOMENDACIONES PRINCIPALES

### Acción 1: Crear estilos para componentes (5 horas)

Agregar a src/ui/estilos.py:
- ESTILO_TITULO_VENTANA
- ESTILO_DESCRIPCION
- ESTILO_TABLA_DATOS (reemplazaría 188 líneas)

### Acción 2: Refactorizar ventana_consumos (3 horas)

Remover 188 líneas de estilos inline, usar ESTILO_TABLA_DATOS

### Acción 3: Crear servicios faltantes (8 horas)

- almacenes_service.py
- operarios_service.py (completar)
- proveedores_service.py (completar)
- ubicaciones_service.py (completar)

### Acción 4: Crear VentanaMaestroBase (15 horas)

Clase base para 7 maestros, elimina 1500 líneas duplicadas

### Acción 5: Crear VentanaOperativaBase (20 horas)

Clase base para 5 operativas, elimina 2500 líneas duplicadas

### Acción 6: Refactorizar __init__ de diálogos (10 horas)

Dividir en: _crear_ui(), _conectar_signals(), _cargar_datos()

### Acción 7: Remover get_con de ventanas (15 horas)

Actualizar 11 archivos para usar services únicamente

---

## 7. ESTIMACIÓN TOTAL

155 horas de refactorización (~4 sprints)

Beneficios:
- Reducción 4000+ líneas código
- Mantenibilidad +70%
- Bugs reducidos ~50%
- Onboarding más rápido

---

## ARCHIVOS CRÍTICOS POR REVISAR

Prioridad 1 (AHORA):
- src/ventanas/consultas/ventana_consumos.py (188 líneas estilos)
- src/ventanas/operativas/ventana_inventario.py (acceso BD)
- src/ventanas/consultas/ventana_stock.py (acceso BD + 129 líneas)

Prioridad 2 (Este sprint):
- src/ventanas/consultas/ventana_historico.py (141 líneas)
- src/ventanas/consultas/ventana_asignaciones.py (162 líneas)
- Todos los maestros (1500 líneas duplicadas)

Prioridad 3 (Próximo sprint):
- Todas las operativas (2500 líneas duplicadas)
- src/ui/estilos.py (completar estilos)

---

## LISTA DE VENTANAS CON PROBLEMAS

### Ventanas Maestros (Duplicación 1500 líneas):
- ventana_articulos.py (6 métodos cargar_)
- ventana_familias.py (2 métodos cargar_)
- ventana_operarios.py (2 métodos cargar_)
- ventana_proveedores.py (2 métodos cargar_)
- ventana_ubicaciones.py (2 métodos cargar_)
- ventana_furgonetas.py (2 métodos cargar_)
- ventana_usuarios.py (2 métodos cargar_)

### Ventanas Operativas (Duplicación 2500 líneas):
- ventana_recepcion.py (567 líneas)
- ventana_devolucion.py (424 líneas)
- ventana_imputacion.py (449 líneas)
- ventana_movimientos.py (753 líneas)
- ventana_material_perdido.py (410 líneas)

### Ventanas Consultas (Problemas varios):
- ventana_consumos.py (932 líneas, 188 estilos duplicados)
- ventana_pedido_ideal.py (827 líneas, 26 inline styles)
- ventana_stock.py (353 líneas, acceso BD directo)
- ventana_asignaciones.py (408 líneas, 162 líneas __init__)
- ventana_historico.py (395 líneas, 141 líneas búsqueda)
- ventana_ficha_articulo.py (631 líneas, múltiples inline)
- ventana_informe_furgonetas.py (363 líneas, loops O(n²))

### Diálogos y Configuración:
- dialogs_configuracion.py (acceso BD, 347 líneas)
- dialogo_cambiar_password.py (101 líneas __init__)
- ventana_login.py (estilos inline)

