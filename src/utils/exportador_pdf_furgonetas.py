# exportador_pdf_furgonetas.py - Exportador de informes de furgonetas a PDF
"""
Módulo para exportar informes semanales de furgonetas a PDF.
Utiliza ReportLab para generar PDFs con tablas formateadas y logo.
"""

from typing import Dict, Any, List
from datetime import datetime
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfgen import canvas

from src.core.logger import logger


def exportar_informe_a_pdf(datos: Dict[str, Any], ruta_destino: str) -> bool:
    """
    Exporta los datos del informe semanal a un archivo PDF.

    Args:
        datos: Diccionario con la estructura completa del informe
        ruta_destino: Ruta completa donde guardar el PDF

    Returns:
        True si se exportó correctamente, False en caso contrario
    """
    try:
        # Crear documento en orientación horizontal (landscape) para que quepa todo
        doc = SimpleDocTemplate(
            ruta_destino,
            pagesize=landscape(A4),
            rightMargin=1.5*cm,
            leftMargin=1.5*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )

        # Elementos del documento
        elementos = []

        # Estilos
        estilos = getSampleStyleSheet()
        estilo_titulo = ParagraphStyle(
            'Titulo',
            parent=estilos['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#1e40af'),
            alignment=TA_CENTER,
            spaceAfter=0.3*cm
        )
        estilo_subtitulo = ParagraphStyle(
            'Subtitulo',
            parent=estilos['Normal'],
            fontSize=12,
            textColor=colors.HexColor('#64748b'),
            alignment=TA_CENTER,
            spaceAfter=0.5*cm
        )

        # ENCABEZADO
        titulo = Paragraph(f"Informe Semanal de Consumo - {datos['furgoneta_nombre']}", estilo_titulo)
        elementos.append(titulo)

        # Fechas
        fecha_ini = datetime.strptime(datos['fecha_inicio'], "%Y-%m-%d").strftime("%d/%m/%Y")
        fecha_fin = datetime.strptime(datos['fecha_fin'], "%Y-%m-%d").strftime("%d/%m/%Y")

        # Operarios
        operarios_txt = ", ".join(datos['operarios']) if datos['operarios'] else "Sin operarios asignados"

        subtitulo = Paragraph(
            f"Semana: {fecha_ini} - {fecha_fin} | Operario(s): {operarios_txt}",
            estilo_subtitulo
        )
        elementos.append(subtitulo)
        elementos.append(Spacer(1, 0.5*cm))

        # TABLA DE DATOS
        tabla_datos = construir_tabla_informe(datos)
        elementos.append(tabla_datos)

        # PIE DE PÁGINA
        elementos.append(Spacer(1, 0.5*cm))
        estilo_pie = ParagraphStyle(
            'Pie',
            parent=estilos['Normal'],
            fontSize=9,
            textColor=colors.HexColor('#94a3b8'),
            alignment=TA_CENTER,
            fontName='Helvetica-Oblique'
        )
        pie = Paragraph(
            f"Informe generado automáticamente desde Climatot Almacén - {datetime.now().strftime('%d/%m/%Y %H:%M')}",
            estilo_pie
        )
        elementos.append(pie)

        # Generar PDF
        doc.build(elementos)
        logger.info(f"PDF exportado correctamente: {ruta_destino}")
        return True

    except Exception as e:
        logger.exception(f"Error al exportar PDF: {e}")
        return False


def construir_tabla_informe(datos: Dict[str, Any]) -> Table:
    """
    Construye la tabla principal del informe con todos los datos.

    Args:
        datos: Diccionario con los datos del informe

    Returns:
        Objeto Table de ReportLab
    """
    dias = datos['dias_semana']
    articulos = datos['articulos']

    # CONSTRUIR ENCABEZADOS
    encabezados = [['FAMILIA', 'ARTÍCULO', 'STOCK\nINICIAL']]

    # Encabezados de días con E/D/G
    for dia in dias:
        encabezados[0].append(f"{dia['dia_nombre']}\n({dia['dia_completo']})\nE")
        encabezados[0].append('D')
        encabezados[0].append('G')

    encabezados[0].append('TOTAL\nFINAL')

    # CONSTRUIR FILAS DE DATOS
    filas = []
    for art in articulos:
        fila = [
            art['familia'],
            art['articulo_nombre'],
            f"{art['stock_inicial']:.2f}"
        ]

        # Movimientos por día
        for dia in dias:
            fecha = dia['fecha']
            movs = art['movimientos_diarios'].get(fecha, {'E': 0, 'D': 0, 'G': 0})

            for tipo in ['E', 'D', 'G']:
                valor = movs[tipo]
                fila.append(f"{valor:.2f}" if valor != 0 else "-")

        # Stock final
        fila.append(f"{art['stock_final']:.2f}")

        filas.append(fila)

    # Combinar encabezados y datos
    datos_tabla = encabezados + filas

    # CREAR TABLA
    tabla = Table(datos_tabla, repeatRows=1)

    # ESTILOS DE LA TABLA
    estilos_tabla = [
        # Encabezado
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e40af')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),

        # Columnas de texto (Familia y Artículo)
        ('FONTNAME', (0, 1), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (1, -1), 7),
        ('ALIGN', (0, 1), (0, -1), 'LEFT'),
        ('ALIGN', (1, 1), (1, -1), 'LEFT'),

        # Columnas numéricas
        ('FONTNAME', (2, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (2, 1), (-1, -1), 7),
        ('ALIGN', (2, 1), (-1, -1), 'RIGHT'),

        # Bordes
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('LINEABOVE', (0, 0), (-1, 0), 2, colors.HexColor('#1e40af')),
        ('LINEBELOW', (0, 0), (-1, 0), 2, colors.HexColor('#1e40af')),

        # Alternar colores de filas
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),

        # Columna FAMILIA con fondo gris claro
        ('BACKGROUND', (0, 1), (0, -1), colors.HexColor('#f1f5f9')),

        # Columna STOCK INICIAL
        ('BACKGROUND', (2, 1), (2, -1), colors.HexColor('#fef3c7')),

        # Columna TOTAL FINAL (última columna)
        ('BACKGROUND', (-1, 1), (-1, -1), colors.HexColor('#e0e7ff')),
        ('FONTNAME', (-1, 1), (-1, -1), 'Helvetica-Bold'),
    ]

    # COLOREAR COLUMNAS E/D/G
    num_dias = len(dias)
    col_inicio_movs = 3  # Después de FAMILIA, ARTÍCULO, STOCK INICIAL

    for i in range(num_dias):
        col_e = col_inicio_movs + (i * 3)
        col_d = col_e + 1
        col_g = col_e + 2

        # Entregas (E) - Verde claro
        estilos_tabla.append(
            ('BACKGROUND', (col_e, 1), (col_e, -1), colors.HexColor('#dcfce7'))
        )

        # Devoluciones (D) - Amarillo claro
        estilos_tabla.append(
            ('BACKGROUND', (col_d, 1), (col_d, -1), colors.HexColor('#fef3c7'))
        )

        # Gastos (G) - Rojo claro
        estilos_tabla.append(
            ('BACKGROUND', (col_g, 1), (col_g, -1), colors.HexColor('#fee2e2'))
        )

    # Aplicar estilos
    tabla.setStyle(TableStyle(estilos_tabla))

    return tabla
