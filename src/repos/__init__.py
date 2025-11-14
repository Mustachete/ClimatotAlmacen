"""
Repositorios - Capa de acceso a datos
"""
from . import articulos_repo
from . import familias_repo
from . import inventarios_repo
from . import movimientos_repo
from . import operarios_repo
from . import proveedores_repo
from . import ubicaciones_repo
from . import usuarios_repo

__all__ = [
    'articulos_repo',
    'familias_repo',
    'inventarios_repo',
    'movimientos_repo',
    'operarios_repo',
    'proveedores_repo',
    'ubicaciones_repo',
    'usuarios_repo',
]
