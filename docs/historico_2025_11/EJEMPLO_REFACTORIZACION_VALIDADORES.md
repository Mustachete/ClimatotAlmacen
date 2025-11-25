# Guía de Refactorización: Validadores y Excepciones

Este documento muestra cómo refactorizar el código existente para usar el nuevo sistema de validadores centralizados y excepciones personalizadas.

---

## ANTES: Código Actual

### movimientos_service.py (código actual)

```python
def validar_cantidad(cantidad: float) -> Tuple[bool, str]:
    """Valida que la cantidad sea válida."""
    if cantidad <= 0:
        log_validacion("movimientos", "cantidad", f"Cantidad inválida: {cantidad}")
        return False, "La cantidad debe ser mayor que 0"

    if cantidad > 999999:
        log_validacion("movimientos", "cantidad", f"Cantidad excesiva: {cantidad}")
        return False, "La cantidad es demasiado grande"

    return True, ""

# Uso en el servicio
def registrar_entrada(...):
    valido, mensaje = validar_cantidad(cantidad)
    if not valido:
        logger.error(mensaje)
        return False, mensaje
    # ... resto del código
```

### Problemas del enfoque actual:
1. ❌ Retorna tuplas (bool, str) - código verboso
2. ❌ Validaciones duplicadas en múltiples servicios
3. ❌ No usa excepciones - dificulta el manejo de errores
4. ❌ Logging manual en cada validación
5. ❌ No hay tipos de error específicos

---

## DESPUÉS: Código Refactorizado

### movimientos_service.py (refactorizado)

```python
from src.validators import MovimientosValidator
from src.core.exceptions import (
    ValidationError,
    InsufficientStockError,
    NotFoundError
)
from src.core.logger import logger, log_operacion

def registrar_entrada(
    articulo_id: int,
    cantidad: float,
    almacen_destino_id: int,
    fecha: str,
    proveedor_id: int = None,
    coste_unit: float = None,
    albaran: str = None,
    responsable: str = None
) -> int:
    """
    Registra una entrada de material al almacén.

    Args:
        articulo_id: ID del artículo
        cantidad: Cantidad recibida
        almacen_destino_id: Almacén donde se recibe
        fecha: Fecha de la entrada (YYYY-MM-DD)
        proveedor_id: ID del proveedor (opcional)
        coste_unit: Coste unitario (opcional)
        albaran: Número de albarán (opcional)
        responsable: Responsable de la recepción (opcional)

    Returns:
        ID del movimiento creado

    Raises:
        ValidationError: Si los datos no son válidos
        NotFoundError: Si el artículo o almacén no existe
        DatabaseError: Si hay error en la base de datos
    """
    try:
        # ✅ Validación centralizada
        MovimientosValidator.validate_entrada(
            articulo_id=articulo_id,
            cantidad=cantidad,
            almacen_destino_id=almacen_destino_id,
            proveedor_id=proveedor_id,
            coste_unit=coste_unit
        )

        MovimientosValidator.validate_fecha(fecha)

        # Verificar que el artículo existe
        articulo = articulos_repo.get_by_id(articulo_id)
        if not articulo:
            raise NotFoundError("Artículo", articulo_id)

        # Verificar que el almacén existe
        almacen = almacenes_repo.get_by_id(almacen_destino_id)
        if not almacen:
            raise NotFoundError("Almacén", almacen_destino_id)

        # Registrar entrada en BD
        movimiento_id = movimientos_repo.crear_movimiento(
            fecha=fecha,
            tipo='ENTRADA',
            origen_id=None,
            destino_id=almacen_destino_id,
            articulo_id=articulo_id,
            cantidad=cantidad,
            coste_unit=coste_unit,
            motivo=None,
            ot=None,
            operario_id=None,
            responsable=responsable,
            albaran=albaran
        )

        log_operacion(
            "movimientos",
            "entrada_creada",
            {"id": movimiento_id, "articulo": articulo['nombre'], "cantidad": cantidad}
        )

        return movimiento_id

    except ValidationError as e:
        # ✅ Manejo específico de errores de validación
        logger.warning(f"Validación falló: {e}")
        raise  # Re-lanzar para que la UI lo maneje

    except NotFoundError as e:
        # ✅ Manejo específico de entidades no encontradas
        logger.error(f"Entidad no encontrada: {e}")
        raise

    except Exception as e:
        # ✅ Solo capturamos excepciones inesperadas
        logger.exception(f"Error inesperado al registrar entrada: {e}")
        raise DatabaseError(
            "Error al registrar entrada",
            detalles=str(e)
        )


def registrar_traspaso(
    articulo_id: int,
    cantidad: float,
    almacen_origen_id: int,
    almacen_destino_id: int,
    fecha: str,
    ot: str = None,
    operario_id: int = None,
    responsable: str = None
) -> int:
    """
    Registra un traspaso entre almacenes con validación de stock.

    Raises:
        ValidationError: Si los datos no son válidos
        InsufficientStockError: Si no hay stock suficiente
        NotFoundError: Si alguna entidad no existe
    """
    try:
        # Validar datos básicos
        MovimientosValidator.validate_traspaso(
            articulo_id=articulo_id,
            cantidad=cantidad,
            almacen_origen_id=almacen_origen_id,
            almacen_destino_id=almacen_destino_id
        )

        MovimientosValidator.validate_fecha(fecha)

        # Verificar stock disponible
        stock_por_almacen = movimientos_repo.get_stock_por_almacen(articulo_id)
        stock_origen = next(
            (s['stock'] for s in stock_por_almacen if s['almacen_id'] == almacen_origen_id),
            0
        )

        if stock_origen < cantidad:
            articulo = articulos_repo.get_by_id(articulo_id)
            raise InsufficientStockError(
                articulo=articulo['nombre'] if articulo else f"ID {articulo_id}",
                solicitado=cantidad,
                disponible=stock_origen
            )

        # Registrar traspaso
        movimiento_id = movimientos_repo.crear_movimiento(
            fecha=fecha,
            tipo='TRASPASO',
            origen_id=almacen_origen_id,
            destino_id=almacen_destino_id,
            articulo_id=articulo_id,
            cantidad=cantidad,
            coste_unit=None,
            motivo=None,
            ot=ot,
            operario_id=operario_id,
            responsable=responsable,
            albaran=None
        )

        log_operacion(
            "movimientos",
            "traspaso_creado",
            {"id": movimiento_id, "articulo_id": articulo_id, "cantidad": cantidad}
        )

        return movimiento_id

    except (ValidationError, InsufficientStockError, NotFoundError):
        # Re-lanzar excepciones de negocio tal cual
        raise

    except Exception as e:
        logger.exception(f"Error inesperado en traspaso: {e}")
        raise DatabaseError(
            "Error al registrar traspaso",
            detalles=str(e)
        )
```

---

## Refactorización de la UI

### ANTES: ventana_recepcion.py (código actual)

```python
def confirmar_guardar(self):
    # Validaciones manuales dispersas
    if not self.articulo_seleccionado:
        QMessageBox.warning(self, "Validación", "Debe seleccionar un artículo")
        return

    cantidad_str = self.txt_cantidad.text()
    try:
        cantidad = float(cantidad_str)
        if cantidad <= 0:
            QMessageBox.warning(self, "Validación", "La cantidad debe ser positiva")
            return
    except ValueError:
        QMessageBox.warning(self, "Validación", "La cantidad debe ser un número")
        return

    # Llamar al servicio (retorna tupla)
    exito, mensaje = movimientos_service.registrar_entrada(...)
    if not exito:
        QMessageBox.critical(self, "Error", mensaje)
        return

    QMessageBox.information(self, "Éxito", "Entrada registrada")
```

### DESPUÉS: ventana_recepcion.py (refactorizado)

```python
from src.core.exceptions import (
    ValidationError,
    InsufficientStockError,
    NotFoundError,
    DatabaseError
)

def confirmar_guardar(self):
    """
    Guarda la recepción de material.
    Usa el sistema de excepciones para manejo de errores.
    """
    try:
        # ✅ El servicio ya valida, no necesitamos validar aquí
        movimiento_id = movimientos_service.registrar_entrada(
            articulo_id=self.articulo_seleccionado['id'],
            cantidad=float(self.txt_cantidad.text()),
            almacen_destino_id=self.cmb_almacen.currentData(),
            fecha=self.date_fecha.date().toString("yyyy-MM-dd"),
            proveedor_id=self.cmb_proveedor.currentData(),
            coste_unit=float(self.txt_coste.text()) if self.txt_coste.text() else None,
            albaran=self.txt_albaran.text(),
            responsable=session_manager.get_usuario_actual()
        )

        QMessageBox.information(
            self,
            "✅ Éxito",
            f"Entrada registrada correctamente.\nID: {movimiento_id}"
        )

        # Limpiar formulario
        self.limpiar_formulario()

    except ValidationError as e:
        # ✅ Mensaje específico de validación
        QMessageBox.warning(
            self,
            "⚠️ Validación",
            str(e)
        )

    except InsufficientStockError as e:
        # ✅ Mensaje específico de stock
        QMessageBox.critical(
            self,
            "❌ Stock Insuficiente",
            str(e)
        )

    except NotFoundError as e:
        # ✅ Mensaje cuando no se encuentra algo
        QMessageBox.critical(
            self,
            "❌ No Encontrado",
            str(e)
        )

    except DatabaseError as e:
        # ✅ Error de BD
        QMessageBox.critical(
            self,
            "❌ Error de Base de Datos",
            f"{e.mensaje}\n\nContacte al administrador si el problema persiste."
        )
        logger.error(f"Error en UI recepción: {e}")

    except Exception as e:
        # ✅ Solo para errores completamente inesperados
        QMessageBox.critical(
            self,
            "❌ Error Inesperado",
            f"Ocurrió un error inesperado:\n{str(e)}\n\n"
            "Contacte al administrador."
        )
        logger.exception(f"Error inesperado en ventana recepción: {e}")
```

---

## Ventajas del Nuevo Enfoque

### 1. Código más limpio y conciso
- ❌ ANTES: 10-15 líneas de validación + manejo de tuplas
- ✅ DESPUÉS: 1-3 líneas de validación

### 2. Errores tipados y específicos
```python
# ❌ ANTES: Todo es genérico
except Exception as e:
    QMessageBox.critical(self, "Error", str(e))

# ✅ DESPUÉS: Manejo específico por tipo
except ValidationError as e:
    QMessageBox.warning(...)
except InsufficientStockError as e:
    QMessageBox.critical(...)
```

### 3. Validaciones reutilizables
```python
# ✅ Una sola definición, múltiples usos
MovimientosValidator.validate_entrada(...)  # En servicio
MovimientosValidator.validate_entrada(...)  # En API
MovimientosValidator.validate_entrada(...)  # En tests
```

### 4. Testing más fácil
```python
def test_entrada_cantidad_negativa():
    with pytest.raises(InvalidValueError) as exc_info:
        MovimientosValidator.validate_entrada(
            articulo_id=1,
            cantidad=-10,  # ❌ Inválido
            almacen_destino_id=1
        )

    assert "positivo" in str(exc_info.value)
```

---

## Plan de Migración Gradual

### Fase 1: Operaciones Críticas (Semana 1)
- [x] Crear sistema de excepciones
- [x] Crear validadores
- [ ] Refactorizar `movimientos_service.py`
- [ ] Actualizar ventanas operativas:
  - [ ] `ventana_recepcion.py`
  - [ ] `ventana_movimientos.py`
  - [ ] `ventana_imputacion.py`

### Fase 2: Maestros (Semana 2)
- [ ] Refactorizar servicios de maestros
- [ ] Actualizar ventanas de maestros

### Fase 3: Consultas y Reportes (Semana 3)
- [ ] Refactorizar servicios de consultas
- [ ] Actualizar ventanas de consultas

### Fase 4: Testing y Documentación (Semana 4)
- [ ] Crear tests unitarios para validadores
- [ ] Documentar patrones de uso
- [ ] Code review completo

---

## Recursos Adicionales

- **Excepciones**: `src/core/exceptions.py`
- **Validadores**: `src/validators/`
- **Ejemplo completo**: Este documento
- **Tests**: (pendiente) `tests/validators/`

---

## Notas Importantes

1. **No romper código existente**: La migración es gradual
2. **Tests primero**: Crear tests antes de refactorizar
3. **Documentar cambios**: Actualizar docstrings
4. **Code review**: Revisar cada refactorización
5. **Logging**: Mantener logs informativos

---

**Siguiente paso**: Implementar prueba de concepto en `movimientos_service.py`
