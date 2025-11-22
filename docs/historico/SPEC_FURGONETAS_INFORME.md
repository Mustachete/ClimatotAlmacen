# 📦 ESPECIFICACIÓN — INFORME SEMANAL DE FURGONETAS

## 🧭 Objetivo
Generar un **informe semanal de stock por furgoneta**, mostrando:
- El stock inicial con el que comenzó la semana.  
- Todos los movimientos diarios de material (entregas, devoluciones y consumos).  
- El stock final al cierre del viernes (que representa el material que debe tener físicamente el lunes siguiente).  

El informe debe poder **generarse desde el programa** (módulo “Furgonetas”) para una o varias furgonetas, **exportándose en formato Excel y PDF** con formato tabular.

---

## 🧩 Estructura general del informe
Cada informe corresponde a **una furgoneta concreta** e incluye:

| Campo | Descripción |
|-------|--------------|
| **Encabezado** | Nombre de la furgoneta (o su código interno), nombre del operario asignado, y rango de fechas (semana). |
| **GRUPO** | Categoría del artículo (extraída de `ARTICULOS.E`). |
| **ARTÍCULO** | Descripción del artículo (`ARTICULOS.B`). |
| **STOCK INICIAL** | Cantidad que tenía el lunes a primera hora (stock al cierre del viernes anterior). |
| **Movimientos diarios** | Seis bloques de columnas, uno por día de lunes a sábado (normalmente lunes a viernes). Cada día tiene tres subcolumnas: **E**, **D**, **G**. |
| **TOTAL** | Suma neta semanal del movimiento (E − D − G) aplicada al stock inicial para calcular el stock final. |

---

## 📅 Detalle de las columnas
Para cada día de la semana:
- **E (Entregado)** → Cantidad de material **entregado desde almacén a la furgoneta**.  
- **D (Devuelto)** → Cantidad **devuelta por la furgoneta al almacén**.  
- **G (Gastado)** → Cantidad **consumida en instalaciones o usada por el operario** (según movimientos registrados en `IMPUTAR OT` o `Material Perdido`).  

El informe debe recorrer todas las fechas comprendidas entre el lunes y el sábado de la semana seleccionada, tomando los datos de movimientos registrados por cada día y agrupándolos por artículo.

---

## ⚙️ Lógica de cálculo
1. **Stock inicial** = stock de la furgoneta el **domingo anterior** (dato obtenido desde la tabla `vw_stock` filtrando por `ubicacion = furgoneta` y `fecha < lunes`).  
2. **Movimientos diarios** = todas las operaciones con `origen_id` o `destino_id` coincidentes con la furgoneta, clasificadas según tipo:  
   - `ENTRADA` → columna **E**  
   - `DEVOLUCIÓN` → columna **D**  
   - `GASTO` / `IMPUTAR` / `PERDIDA` → columna **G**  
3. **Total semanal** = stock inicial + (ΣE − ΣD − ΣG)  
4. **Stock final** = valor que debe tener la furgoneta el lunes siguiente (inicio de la siguiente semana).

---

## 🧾 Ejemplo textual
```
FURGONETA: 44
OPERARIO: SAID
SEMANA: 27/10 – 31/10

GRUPO | ARTÍCULO | STOCK INICIAL | L (27-10) E D G | M (28-10) E D G | X (29-10) E D G | J (30-10) E D G | V (31-10) E D G | TOTAL
A/A (FRÍO) | Tubo 1/4-1/2 | - | - - - | 40 - - | - - - | - - - | - - - | 40
ELECTRICIDAD Y FIJACIÓN | Cable 4x1,5 | 191 | - - 3 | - - - | - - - | - - - | - - - | 188
CONSUMIBLES | Cinta aislante | 18 | - - 1 | - - - | - - - | - - - | - - - | 17
SIN GRUPO | Tornillos | - | - - - | - - - | - - - | 8 - - | - - - | 8
```

---

## 📤 Requisitos de exportación
- **Formato Excel (.xlsx):**  
  - Celdas con bordes y encabezados fijos.  
  - Colores alternos por grupo.  
  - Totales al final de cada grupo.  
  - Archivo nombrado como `Furgoneta_[NOMBRE]_Semana_[YYYY-MM-DD].xlsx`.
- **Formato PDF:**  
  - Igual diseño que Excel.  
  - Encabezado con logo Climatot, nombre de la furgoneta y fechas.  
  - Pie con “Informe generado automáticamente desde Climatot Almacén”.

---

## 🔩 Consideraciones técnicas
- Permitir selección de **semana** (a partir de un lunes) y **furgoneta(s)**.  
- El generador creará un informe por cada furgoneta.  
- El informe se basa en los movimientos registrados, no en stock en tiempo real.  
- El stock inicial se recalcula según el viernes anterior.  
- Si una furgoneta no tiene movimientos, se mostrará con stock inicial y totales en cero.

---

## 🧠 Resumen operativo
Cada lunes, el usuario seleccionará la semana anterior (ej. “27/10–31/10”) y la furgoneta.  
El sistema generará una tabla con **una fila por artículo**, mostrando **stock inicial, entregas, devoluciones, gastos diarios y total final**.  
El resultado podrá exportarse directamente a Excel o PDF desde el módulo “Furgonetas”.
