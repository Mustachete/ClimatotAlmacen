# 🏢 Sistema Climatot Almacén

Sistema de gestión integral de almacén desarrollado en Python.

## 🚀 Instalación

1. Instalar dependencias:
```bash
pip install -r requirements.txt
```

2. Inicializar base de datos:
```bash
python scripts/init_db.py
```

3. Ejecutar aplicación:
```bash
python app.py
```

## 📁 Estructura del Proyecto

- `src/core/` - Módulos centrales (BD, configuración)
- `src/ui/` - Componentes de interfaz
- `src/ventanas/` - Ventanas de la aplicación
- `src/dialogs/` - Diálogos auxiliares
- `scripts/` - Scripts de utilidad
- `db/` - Base de datos SQLite
- `config/` - Archivos de configuración
- `docs/` - Documentación

## 📖 Documentación

Ver carpeta `docs/` para documentación completa.

## 🔐 Acceso por Defecto

- Usuario: `admin`
- Contraseña: `admin`

⚠️ **IMPORTANTE:** Cambiar contraseña tras primer login.

## 🛠️ Tecnologías

- Python 3.12+
- PySide6 (Qt)
- SQLite3
- pandas
- openpyxl
