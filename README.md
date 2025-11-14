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

- `src/core/` - Módulos centrales (BD, configuración, logging, error handling)
- `src/repos/` - Repositorios (capa de acceso a datos, SQL puro)
- `src/services/` - Servicios (capa de lógica de negocio)
- `src/ui/` - Componentes de interfaz
- `src/ventanas/` - Ventanas de la aplicación (capa de presentación)
- `src/dialogs/` - Diálogos auxiliares
- `scripts/` - Scripts de utilidad y backups
- `db/` - Base de datos SQLite y backups
- `logs/` - Archivos de log rotativos
- `config/` - Archivos de configuración
- `docs/` - Documentación

## 📖 Documentación

Ver carpeta `docs/` para documentación completa.

## 🔐 Primer Acceso

**Crear usuario administrador:**
```bash
python scripts/init_admin.py
```

Este script interactivo te guiará para crear el primer usuario administrador del sistema.

**Sistema de Autenticación:**
- Roles disponibles: `admin`, `almacen`, `operario`
- Contraseñas hasheadas con SHA256
- Sesiones con auditoría completa
- Trazabilidad de todas las operaciones por usuario

Ver documentación completa: [docs/SISTEMA_AUTENTICACION.md](docs/SISTEMA_AUTENTICACION.md)

## 🛠️ Tecnologías

- Python 3.12+
- PySide6 (Qt)
- SQLite3
- pandas
- openpyxl

## ✨ Características Implementadas

### ✅ Fase 1: Fundamentos - COMPLETADO
- ✅ Sistema de Logging estructurado con rotación automática
- ✅ Backups automáticos de base de datos (comprimidos con hash SHA256)
- ✅ Arquitectura en capas (Repositorio → Service → UI)

### ✅ Módulos Operativos Refactorizados - COMPLETADO
- ✅ **Movimientos** (repo + service + ventana) - Traspasos almacén-furgoneta
- ✅ **Material Perdido** (usando movimientos_service)
- ✅ **Devolución a Proveedor** (usando movimientos_service)
- ✅ **Recepción de Albaranes** (usando movimientos_service)
- ✅ **Imputación a OT** (usando movimientos_service)
- ✅ **Pedido Ideal** (repo + service + ventana)
- ✅ **Consumos** (repo + service + ventana)
- ✅ **Furgonetas** (repo + service + ventana)

### 📊 Estado del Proyecto
- **Tamaño del proyecto:** 4.3 MB (reducido desde 279 MB)
- **Módulos operativos refactorizados:** 8/8 (100%)
- **Líneas de código organizadas:** +2,000
- **Arquitectura:** 3 capas implementadas

### 🚀 Próximas Fases
- ⏳ Refactorizar módulos maestros (Artículos, Proveedores, etc.)
- ⏳ Refactorizar módulo de Inventarios
- ⏳ Sistema de Pedidos completo con estados
- ⏳ Coste Medio Ponderado (CMP)
- ⏳ Sistema de Anulaciones con auditoría
