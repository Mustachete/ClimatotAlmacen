"""
Repositorios - Capa de acceso a datos
"""
from . import albaranes_repo
from . import almacenes_repo
from . import articulos_repo
from . import familias_repo
from . import inventarios_repo
from . import movimientos_repo
from . import operarios_repo
from . import proveedores_repo
from . import stock_repo
from . import ubicaciones_repo
from . import usuarios_repo

__all__ = [
    'albaranes_repo',
    'almacenes_repo',
    'articulos_repo',
    'familias_repo',
    'inventarios_repo',
    'movimientos_repo',
    'operarios_repo',
    'proveedores_repo',
    'stock_repo',
    'ubicaciones_repo',
    'usuarios_repo',
]
