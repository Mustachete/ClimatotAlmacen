# ========================================
# CONFIG UTILS — GESTIÓN DE CONFIGURACIONES
# ========================================
from pathlib import Path
import os
import configparser

# ----------------------------------------
# DESCUBRIR RAÍZ DEL PROYECTO
# ----------------------------------------
_THIS = Path(__file__).resolve()

def _find_project_root(start: Path) -> Path:
    """
    Busca hacia arriba una carpeta que contenga las carpetas 'db' y 'config'.
    Si no las encuentra, usa como fallback dos niveles arriba.
    """
    for cand in [start, *start.parents]:
        if (cand / "db").is_dir() and (cand / "config").is_dir():
            return cand
    return start.parents[2]

PROJECT_ROOT = _find_project_root(_THIS)

# ----------------------------------------
# DEFINICIÓN DE RUTAS
# ----------------------------------------
env_cfg = os.getenv("CLIMATOT_CONFIG_DIR")

if env_cfg:
    CONFIG_DIR = Path(env_cfg).resolve()
else:
    CONFIG_DIR = PROJECT_ROOT / "config"

CONFIG_DIR.mkdir(parents=True, exist_ok=True)


# ----------------------------------------
# FUNCIÓN PRINCIPAL DE CARGA DE CONFIGURACIÓN
# ----------------------------------------
def load_config(name: str = "app.ini") -> configparser.ConfigParser:
    """
    Carga un archivo INI desde la carpeta de configuración.
    Si no existe, crea uno básico automáticamente.
    """
    cfg = configparser.ConfigParser()
    path = CONFIG_DIR / name

    if not path.exists():
        # Crear configuración mínima por defecto
        cfg["app"] = {
            "env": "dev",
            "debug": "true",
            "version": "1.0.0"
        }
        with path.open("w", encoding="utf-8") as f:
            cfg.write(f)
    else:
        cfg.read(path, encoding="utf-8")

    return cfg


# ----------------------------------------
# FUNCIÓN OPCIONAL PARA GUARDAR CONFIG
# ----------------------------------------
def save_config(cfg: configparser.ConfigParser, name: str = "app.ini") -> None:
    """
    Guarda el objeto ConfigParser en disco dentro de la carpeta de configuración.
    """
    path = CONFIG_DIR / name
    with path.open("w", encoding="utf-8") as f:
        cfg.write(f)


# ----------------------------------------
# EJEMPLO DE USO (solo si se ejecuta directamente)
# ----------------------------------------
if __name__ == "__main__":
    config = load_config()
    print(f"Ruta de configuración: {CONFIG_DIR}")
    print("Contenido actual del archivo de configuración:")
    for section in config.sections():
        print(f"[{section}]")
        for key, value in config[section].items():
            print(f"{key} = {value}")