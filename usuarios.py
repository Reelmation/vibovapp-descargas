"""Usuarios del programa: cada uno tiene su propia carpeta con sus productos, estilos, plantillas y preferencias.
Todos viven dentro de la carpeta de datos del programa (Documentos\\Vibovapp)."""
import json
import re
import shutil
import unicodedata
from pathlib import Path

import generar_diario as gd

RAIZ = Path(gd.DATOS)          # carpeta de datos original (antes de elegir usuario)
ACTIVO = None                  # id del usuario con sesion abierta


def _archivo():
    return RAIZ / "usuarios.json"


def _leer():
    try:
        d = json.loads(_archivo().read_text(encoding="utf-8"))
        if isinstance(d, dict) and isinstance(d.get("usuarios"), list):
            return d
    except Exception:
        pass
    d = {"usuarios": [], "ultimo": None, "idioma": "es"}
    # si ya habia productos de versiones anteriores, se quedan en un usuario "Principal"
    if (RAIZ / "productos").is_dir() and any((RAIZ / "productos").iterdir()):
        d["usuarios"].append({"id": "principal", "nombre": "Principal", "ruta": "."})
    return d


def _guardar(d):
    RAIZ.mkdir(parents=True, exist_ok=True)
    _archivo().write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")


def _ruta(u):
    return (RAIZ / u["ruta"]).resolve() if u.get("ruta") else (RAIZ / "usuarios" / u["id"])


def _id(nombre):
    n = unicodedata.normalize("NFD", nombre.strip().lower())
    n = "".join(c for c in n if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]+", "_", n).strip("_")


def listar():
    d = _leer()
    return {"usuarios": [{"id": u["id"], "nombre": u["nombre"]} for u in d["usuarios"]],
            "activo": ACTIVO, "idioma": d.get("idioma", "es")}


def idioma(nuevo=None):
    d = _leer()
    if nuevo in ("es", "en"):
        d["idioma"] = nuevo
        d["idioma_elegido"] = True
        _guardar(d)
    return d.get("idioma", "es")


def tema(nuevo=None):
    """Apariencia del programa: 'oscuro' (por defecto), 'claro' o 'auto' (como el tema de Windows)."""
    d = _leer()
    if nuevo in ("oscuro", "claro", "auto"):
        d["tema"] = nuevo
        d["tema_elegido"] = True
        _guardar(d)
    t = d.get("tema", "oscuro")
    return t if t in ("oscuro", "claro", "auto") else "oscuro"


def idioma_elegido():
    """True si ya eligió el idioma (o si ya usaba el programa antes de que existiera la pregunta): la pregunta de idioma sale solo la primera vez."""
    d = _leer()
    return bool(d.get("idioma_elegido") or d.get("tema_elegido") or "tema" in d or d.get("usuarios"))


def tema_elegido():
    """True si la persona ya escogió la apariencia (o ya la había cambiado antes): la pregunta de bienvenida solo sale una vez."""
    d = _leer()
    return bool(d.get("tema_elegido") or "tema" in d)


def crear(nombre):
    nombre = (nombre or "").strip()[:40]
    base = _id(nombre)
    if not base:
        raise gd.ErrorMotor("Escribe un nombre (letras o números).")
    d = _leer()
    import planes
    aviso = planes.revisar_conteo("usuarios", len(d["usuarios"]), "usuarios")
    if aviso:
        raise gd.ErrorMotor(aviso)
    ids = {u["id"] for u in d["usuarios"]}
    uid, n = base, 2
    while uid in ids or (RAIZ / "usuarios" / uid).exists():
        uid, n = f"{base}_{n}", n + 1
    d["usuarios"].append({"id": uid, "nombre": nombre})
    (RAIZ / "usuarios" / uid / "productos").mkdir(parents=True, exist_ok=True)
    _guardar(d)
    return uid


def _buscar(d, uid):
    for u in d["usuarios"]:
        if u["id"] == uid:
            return u
    raise gd.ErrorMotor("No encuentro ese usuario.")


def activar(uid):
    """Abre la sesion de un usuario: todo el programa pasa a trabajar en su carpeta."""
    global ACTIVO
    d = _leer()
    u = _buscar(d, uid)
    ruta = _ruta(u)
    (ruta / "productos").mkdir(parents=True, exist_ok=True)
    gd.DATOS = ruta
    gd.PRODUCTOS = ruta / "productos"
    ACTIVO = uid
    d["ultimo"] = uid
    _guardar(d)
    return uid


def cerrar_sesion():
    global ACTIVO
    ACTIVO = None
    gd.DATOS = RAIZ
    gd.PRODUCTOS = RAIZ / "productos"


def renombrar(uid, nombre):
    nombre = (nombre or "").strip()[:40]
    if not nombre:
        raise gd.ErrorMotor("Escribe un nombre.")
    d = _leer()
    _buscar(d, uid)["nombre"] = nombre
    _guardar(d)


def borrar(uid):
    """Borra el usuario y TODO su trabajo."""
    d = _leer()
    u = _buscar(d, uid)
    if uid == ACTIVO:
        raise gd.ErrorMotor("Cierra la sesión de este usuario antes de borrarlo.")
    ruta = _ruta(u)
    if u.get("ruta"):                       # usuario de versiones anteriores: solo se borran sus datos
        for sub in ("productos", "estilos", "plantillas_temas", "cache_miniaturas"):
            shutil.rmtree(ruta / sub, ignore_errors=True)
        (ruta / "config_programa.json").unlink(missing_ok=True)
    else:
        shutil.rmtree(ruta, ignore_errors=True)
    d["usuarios"] = [x for x in d["usuarios"] if x["id"] != uid]
    if d.get("ultimo") == uid:
        d["ultimo"] = None
    _guardar(d)


def unico():
    """Un solo usuario por computadora (los proyectos son lo que se separa). Si había varios, se queda el que tiene más trabajo;
    los demás se apartan en una carpeta (no se pierde nada) y dejan de verse. Si no hay ninguno, se crea «Principal»."""
    d = _leer()
    if not d["usuarios"]:
        return crear("Principal")
    if len(d["usuarios"]) > 1:
        def peso(x):
            p = _ruta(x) / "productos"
            return sum(1 for _ in p.iterdir()) if p.is_dir() else 0
        quedan = max(d["usuarios"], key=lambda x: (peso(x), x["id"] == d.get("ultimo")))
        for x in d["usuarios"]:
            if x is quedan:
                continue
            r = _ruta(x)
            if not x.get("ruta") and r.is_dir():
                dest = RAIZ / "usuarios_apartados"
                dest.mkdir(parents=True, exist_ok=True)
                try:
                    shutil.move(str(r), str(dest / x["id"]))
                except Exception:
                    pass
        d["usuarios"] = [quedan]
        d["ultimo"] = quedan["id"]
        _guardar(d)
    return d["usuarios"][0]["id"]


def arrancar():
    """Al abrir el programa nadie ha iniciado sesión: primero sale la bienvenida y después se elige el usuario."""
    cerrar_sesion()
