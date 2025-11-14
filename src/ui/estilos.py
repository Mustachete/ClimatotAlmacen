# estilos.py - Estilos centralizados para todas las ventanas de Climatot

# Colores corporativos Climatot
COLOR_AZUL_PRINCIPAL = "#1e3a8a"      # Azul navy-royal
COLOR_AZUL_HOVER = "#1e40af"          # Azul más oscuro para hover
COLOR_AZUL_CLARO = "#dbeafe"          # Azul muy claro para hover en tablas
COLOR_AZUL_PASTEL = "#eff6ff"         # Azul pastel suave para fondos
COLOR_FONDO = "#f8fafc"               # Gris muy claro, casi blanco
COLOR_BLANCO = "#ffffff"
COLOR_GRIS_BORDE = "#e2e8f0"          # Gris claro para bordes
COLOR_TEXTO_OSCURO = "#1e293b"        # Casi negro para texto
COLOR_TEXTO_GRIS = "#64748b"          # Gris para texto secundario
COLOR_ROJO = "#dc2626"                # Rojo para acciones destructivas
COLOR_ROJO_HOVER = "#b91c1c"          # Rojo hover
COLOR_ROJO_PRESSED = "#991b1b"        # Rojo pressed

# ========================================
# ESTILO PARA VENTANAS PRINCIPALES
# ========================================
ESTILO_VENTANA = f"""
    QWidget {{
        background-color: {COLOR_FONDO};
        font-size: 14px;
        color: {COLOR_TEXTO_OSCURO};
    }}
    
    QPushButton {{
        padding: 10px 15px;
        background-color: {COLOR_BLANCO};
        border: 2px solid {COLOR_AZUL_PRINCIPAL};
        border-radius: 6px;
        min-height: 35px;
        color: {COLOR_AZUL_PRINCIPAL};
        font-weight: bold;
    }}
    
    QPushButton:hover {{
        background-color: {COLOR_AZUL_PRINCIPAL};
        color: {COLOR_BLANCO};
    }}
    
    QPushButton:pressed {{
        background-color: {COLOR_AZUL_HOVER};
    }}
    
    QPushButton:disabled {{
        background-color: {COLOR_GRIS_BORDE};
        border-color: {COLOR_GRIS_BORDE};
        color: {COLOR_TEXTO_GRIS};
    }}
    
    QLineEdit, QComboBox, QDateEdit, QSpinBox, QDoubleSpinBox, QTextEdit {{
        padding: 8px;
        border: 2px solid {COLOR_GRIS_BORDE};
        border-radius: 5px;
        background-color: {COLOR_BLANCO};
        color: {COLOR_TEXTO_OSCURO};
    }}
    
    QLineEdit:focus, QComboBox:focus, QDateEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QTextEdit:focus {{
        border: 2px solid {COLOR_AZUL_PRINCIPAL};
    }}
    
    QSpinBox, QDoubleSpinBox {{
        padding: 8px;
        border: 2px solid {COLOR_GRIS_BORDE};
        border-radius: 5px;
        background-color: {COLOR_BLANCO};
        color: {COLOR_TEXTO_OSCURO};
    }}
    
    QSpinBox:focus, QDoubleSpinBox:focus {{
        border: 2px solid {COLOR_AZUL_PRINCIPAL};
    }}
        
    QTableWidget {{
        background-color: {COLOR_BLANCO};
        border: 2px solid {COLOR_GRIS_BORDE};
        border-radius: 6px;
        gridline-color: {COLOR_GRIS_BORDE};
    }}
    
    QTableWidget::item {{
        padding: 6px;
        color: {COLOR_TEXTO_OSCURO};
    }}
    
    QTableWidget::item:selected {{
        background-color: {COLOR_AZUL_PRINCIPAL};
        color: {COLOR_BLANCO};
    }}
    
    QTableWidget::item:hover {{
        background-color: {COLOR_AZUL_CLARO};
    }}
    
    QHeaderView::section {{
        background-color: {COLOR_AZUL_PRINCIPAL};
        color: {COLOR_BLANCO};
        padding: 10px;
        border: none;
        font-weight: bold;
        font-size: 13px;
    }}
    
    QLabel {{
        color: {COLOR_TEXTO_OSCURO};
        background-color: transparent;
    }}
    
    QCheckBox {{
        color: {COLOR_TEXTO_OSCURO};
        spacing: 8px;
    }}
    
    QCheckBox::indicator {{
        width: 20px;
        height: 20px;
        border: 2px solid {COLOR_GRIS_BORDE};
        border-radius: 4px;
        background-color: {COLOR_BLANCO};
    }}
    
    QCheckBox::indicator:checked {{
        background-color: {COLOR_AZUL_PRINCIPAL};
        border-color: {COLOR_AZUL_PRINCIPAL};
    }}
    
    QRadioButton {{
        color: {COLOR_TEXTO_OSCURO};
        spacing: 8px;
    }}
    
    QRadioButton::indicator {{
        width: 18px;
        height: 18px;
        border: 2px solid {COLOR_AZUL_PRINCIPAL};
        border-radius: 9px;
        background-color: {COLOR_BLANCO};
    }}
    
    QRadioButton::indicator:checked {{
        width: 18px;
        height: 18px;
        border: 2px solid {COLOR_AZUL_PRINCIPAL};
        border-radius: 9px;
        background-color: {COLOR_BLANCO};
        background: qradialgradient(cx:0.5, cy:0.5, radius:0.4, fx:0.5, fy:0.5, stop:0 {COLOR_AZUL_PRINCIPAL}, stop:0.5 {COLOR_AZUL_PRINCIPAL}, stop:0.51 {COLOR_BLANCO}, stop:1 {COLOR_BLANCO});
    }}
"""

# ========================================
# ESTILO PARA DIÁLOGOS (ventanas popup)
# ========================================
ESTILO_DIALOGO = f"""
    QDialog {{
        background-color: {COLOR_FONDO};
        font-size: 14px;
    }}
    
    QWidget {{
        background-color: {COLOR_FONDO};
        color: {COLOR_TEXTO_OSCURO};
    }}
    
    QPushButton {{
        padding: 10px 15px;
        background-color: {COLOR_BLANCO};
        border: 2px solid {COLOR_AZUL_PRINCIPAL};
        border-radius: 6px;
        min-height: 35px;
        color: {COLOR_AZUL_PRINCIPAL};
        font-weight: bold;
    }}
    
    QPushButton:hover {{
        background-color: {COLOR_AZUL_PRINCIPAL};
        color: {COLOR_BLANCO};
    }}
    
    QLineEdit, QComboBox, QDateEdit, QSpinBox, QDoubleSpinBox, QTextEdit {{
        padding: 8px;
        border: 2px solid {COLOR_GRIS_BORDE};
        border-radius: 5px;
        background-color: {COLOR_BLANCO};
        color: {COLOR_TEXTO_OSCURO};
    }}
    
    QLineEdit:focus, QComboBox:focus, QDateEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QTextEdit:focus {{
        border: 2px solid {COLOR_AZUL_PRINCIPAL};
    }}
    
    QSpinBox, QDoubleSpinBox {{
        padding: 8px;
        border: 2px solid {COLOR_GRIS_BORDE};
        border-radius: 5px;
        background-color: {COLOR_BLANCO};
        color: {COLOR_TEXTO_OSCURO};
    }}
    
    QSpinBox:focus, QDoubleSpinBox:focus {{
        border: 2px solid {COLOR_AZUL_PRINCIPAL};
    }}
        
    QGroupBox {{
        font-weight: bold;
        border: 2px solid {COLOR_AZUL_PRINCIPAL};
        border-radius: 8px;
        margin-top: 12px;
        padding: 15px 10px 10px 10px;
        background-color: {COLOR_AZUL_PASTEL};
    }}
    
    QGroupBox::title {{
        color: {COLOR_AZUL_PRINCIPAL};
        subcontrol-origin: margin;
        subcontrol-position: top left;
        left: 15px;
        padding: 0 8px;
        background-color: {COLOR_FONDO};
        border-radius: 3px;
    }}
    
    QLabel {{
        color: {COLOR_TEXTO_OSCURO};
        background-color: transparent;
    }}
    
    QCheckBox {{
        color: {COLOR_TEXTO_OSCURO};
        spacing: 8px;
        background-color: transparent;
    }}
    
    QCheckBox::indicator {{
        width: 20px;
        height: 20px;
        border: 2px solid {COLOR_GRIS_BORDE};
        border-radius: 4px;
        background-color: {COLOR_BLANCO};
    }}
    
    QCheckBox::indicator:checked {{
        background-color: {COLOR_AZUL_PRINCIPAL};
        border-color: {COLOR_AZUL_PRINCIPAL};
    }}
    
    QRadioButton {{
        color: {COLOR_TEXTO_OSCURO};
        spacing: 8px;
    }}
    
    QRadioButton::indicator {{
        width: 18px;
        height: 18px;
        border: 2px solid {COLOR_AZUL_PRINCIPAL};
        border-radius: 9px;
        background-color: {COLOR_BLANCO};
    }}
    
    QRadioButton::indicator:checked {{
        width: 18px;
        height: 18px;
        border: 2px solid {COLOR_AZUL_PRINCIPAL};
        border-radius: 9px;
        background-color: {COLOR_BLANCO};
        background: qradialgradient(cx:0.5, cy:0.5, radius:0.4, fx:0.5, fy:0.5, stop:0 {COLOR_AZUL_PRINCIPAL}, stop:0.5 {COLOR_AZUL_PRINCIPAL}, stop:0.51 {COLOR_BLANCO}, stop:1 {COLOR_BLANCO});
    }}
        
    QTableWidget {{
        background-color: {COLOR_BLANCO};
        border: 2px solid {COLOR_GRIS_BORDE};
        border-radius: 6px;
        gridline-color: {COLOR_GRIS_BORDE};
    }}
    
    QHeaderView::section {{
        background-color: {COLOR_AZUL_PRINCIPAL};
        color: {COLOR_BLANCO};
        padding: 8px;
        border: none;
        font-weight: bold;
    }}
    
    QScrollArea {{
        border: none;
        background-color: transparent;
    }}
"""

# ========================================
# ESTILO PARA LOGIN
# ========================================
ESTILO_LOGIN = f"""
    QWidget {{
        background-color: {COLOR_FONDO};
        font-size: 14px;
    }}
    
    QLabel {{
        color: {COLOR_TEXTO_OSCURO};
        background-color: transparent;
    }}
    
    QLineEdit {{
        padding: 12px 15px;
        border: 2px solid {COLOR_GRIS_BORDE};
        border-radius: 8px;
        background-color: {COLOR_BLANCO};
        font-size: 15px;
        color: {COLOR_TEXTO_OSCURO};
        min-height: 45px;
    }}

    QLineEdit:focus {{
        border: 2px solid {COLOR_AZUL_PRINCIPAL};
        background-color: {COLOR_BLANCO};
    }}

    QLineEdit::placeholder {{
        color: {COLOR_TEXTO_GRIS};
        font-style: italic;
    }}
    
    QPushButton {{
        padding: 14px 20px;
        background-color: {COLOR_BLANCO};
        border: 2px solid {COLOR_AZUL_PRINCIPAL};
        border-radius: 8px;
        color: {COLOR_AZUL_PRINCIPAL};
        font-weight: bold;
        font-size: 15px;
        min-height: 50px;
    }}

    QPushButton:hover {{
        background-color: {COLOR_AZUL_PRINCIPAL};
        color: {COLOR_BLANCO};
    }}

    QPushButton:pressed {{
        background-color: {COLOR_AZUL_HOVER};
    }}
"""

# ========================================
# ESTILO PARA BOTÓN QUITAR (COMPACTO Y RESPONSIVE)
# ========================================
# Este estilo permite que el botón se adapte al contenedor donde se coloca
# No usa tamaños fijos, sino que se ajusta al espacio disponible
ESTILO_BOTON_QUITAR = f"""
    QPushButton {{
        background-color: {COLOR_ROJO};
        color: {COLOR_BLANCO};
        border: none;
        border-radius: 3px;
        padding: 2px 6px;
        font-size: 13px;
        font-weight: normal;
        min-width: 50px;
        max-width: 80px;
        min-height: 20px;
        max-height: 24px;
    }}
    QPushButton:hover {{
        background-color: {COLOR_ROJO_HOVER};
    }}
    QPushButton:pressed {{
        background-color: {COLOR_ROJO_PRESSED};
    }}
"""