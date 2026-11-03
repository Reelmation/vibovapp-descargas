"""Escenas: videos sin voz armados escena por escena (clips de una carpeta o un archivo, duración, texto) al ritmo de la música.
Se guardan como plantillas en «escenas.json» dentro del proyecto. Las PIEZAS (intros, cierres, otras) se guardan una sola vez
para todos tus proyectos y solo llevan nombres de carpetas, no archivos: en cada proyecto usan los clips de ese proyecto."""
import json
import random
import uuid
from pathlib import Path

import generar_diario as gd

POSICIONES = ("arriba", "centro", "abajo")
EFECTOS = ("subir", "fundido", "rebote", "izquierda", "derecha", "ninguna")
TIPOS = ("intro", "cierre", "otra")
GIROS = (0, 90, 180, 270)
MAX_PLANTILLAS, MAX_ESCENAS, MAX_PIEZAS = 30, 40, 60


def _ruta(carpeta):
    return Path(carpeta) / "escenas.json"


def _ruta_piezas():
    gd.DATOS.mkdir(parents=True, exist_ok=True)
    return Path(gd.DATOS) / "piezas_escenas.json"


def _fuente_ok(carpeta, f):
    f = str(f or "").strip()
    if f == "kit":
        return "kit"
    if f.startswith("tema:"):
        n = gd.limpiar_nombre(f[5:])
        return "tema:" + n if n else "tema:general"
    if f.startswith("archivo:"):
        rel = f[8:].replace("\\", "/").lstrip("/")
        base = Path(carpeta).resolve() if carpeta else None
        if base is not None:
            try:
                (base / rel).resolve().relative_to(base)
            except ValueError:
                return "tema:general"
        if rel.split("/")[0] in ("clips", "kit") and ".." not in rel.split("/"):
            return "archivo:" + rel
    return "tema:general"


def _limpia_escena(carpeta, e):
    e = e if isinstance(e, dict) else {}
    if e.get("pieza"):                                   # una pieza guardada (o «una al azar» de un tipo: *intro, *cierre, *otra)
        return {"pieza": str(e["pieza"])[:40]}
    try:
        seg = float(e.get("seg") or 3)
    except (TypeError, ValueError):
        seg = 3.0
    try:
        ini = max(0.0, min(float(e.get("ini") or 0), 36000.0))
    except (TypeError, ValueError):
        ini = 0.0
    try:
        giro = int(e.get("giro") or 0)
    except (TypeError, ValueError):
        giro = 0
    return {"nombre": str(e.get("nombre") or "")[:60],
            "fuente": _fuente_ok(carpeta, e.get("fuente")),
            "seg": round(max(1.0, min(seg, 30.0)), 1),
            "texto": " ".join(str(e.get("texto") or "").split())[:120],
            "pos": e.get("pos") if e.get("pos") in POSICIONES else "abajo",
            "efecto": e.get("efecto") if e.get("efecto") in EFECTOS else "fundido",
            "espejo": bool(e.get("espejo")),
            "giro": giro if giro in GIROS else 0,
            "ini": round(ini, 1)}


def _limpia_plantilla(carpeta, p):
    p = p if isinstance(p, dict) else {}
    return {"id": gd.limpiar_nombre(str(p.get("id") or "")) or uuid.uuid4().hex[:8],
            "nombre": (str(p.get("nombre") or "").strip()[:60]) or "Plantilla",
            "ritmo": bool(p.get("ritmo")),
            "escenas": [_limpia_escena(carpeta, e) for e in (p.get("escenas") or [])[:MAX_ESCENAS]]}


def _unicos(lista):
    vistos = set()
    for p in lista:
        while p["id"] in vistos:
            p["id"] = uuid.uuid4().hex[:8]
        vistos.add(p["id"])


# ---------------------------------------------------------------- piezas (valen para todos tus proyectos)
EJEMPLOS = [
    {"id": "ej_intro_descuento", "nombre": "Intro con descuento (ejemplo)", "tipo": "intro",
     "escenas": [{"fuente": "tema:general", "seg": 2.5, "texto": "¡20% de descuento hoy!", "pos": "centro", "efecto": "rebote"}]},
    {"id": "ej_intro_logo", "nombre": "Intro con tu marca (ejemplo)", "tipo": "intro",
     "escenas": [{"fuente": "tema:general", "seg": 2.5, "texto": "Tu marca aquí", "pos": "centro", "efecto": "fundido"}]},
    {"id": "ej_cierre_redes", "nombre": "Cierre con redes (ejemplo)", "tipo": "cierre",
     "escenas": [{"fuente": "tema:general", "seg": 3, "texto": "Sígueme: @tuusuario", "pos": "abajo", "efecto": "subir"}]}]


def cargar_piezas():
    try:
        d = json.loads(_ruta_piezas().read_text(encoding="utf-8"))
    except FileNotFoundError:
        d = {"piezas": EJEMPLOS}                # la primera vez vienen tres piezas de ejemplo ya hechas (editables y borrables)
    except Exception:
        d = {}
    res = []
    for p in (d.get("piezas") or [])[:MAX_PIEZAS]:
        if not isinstance(p, dict):
            continue
        res.append({"id": gd.limpiar_nombre(str(p.get("id") or "")) or uuid.uuid4().hex[:8],
                    "nombre": (str(p.get("nombre") or "").strip()[:60]) or "Pieza",
                    "tipo": p.get("tipo") if p.get("tipo") in TIPOS else "otra",
                    "escenas": [x for x in (_limpia_escena(None, e) for e in (p.get("escenas") or [])[:MAX_ESCENAS]) if "pieza" not in x]})
    return res


def guardar_piezas(lista):
    pz = [{"id": p.get("id"), "nombre": p.get("nombre"), "tipo": p.get("tipo"), "escenas": p.get("escenas")} for p in (lista or []) if isinstance(p, dict)]
    pz = cargar_piezas_desde(pz)
    _unicos(pz)
    _ruta_piezas().write_text(json.dumps({"piezas": pz}, ensure_ascii=False, indent=2), encoding="utf-8")
    return cargar_piezas()


def cargar_piezas_desde(lista):
    res = []
    for p in lista[:MAX_PIEZAS]:
        res.append({"id": gd.limpiar_nombre(str(p.get("id") or "")) or uuid.uuid4().hex[:8],
                    "nombre": (str(p.get("nombre") or "").strip()[:60]) or "Pieza",
                    "tipo": p.get("tipo") if p.get("tipo") in TIPOS else "otra",
                    "escenas": [x for x in (_limpia_escena(None, e) for e in (p.get("escenas") or [])[:MAX_ESCENAS]) if "pieza" not in x]})
    return res


def _piezas_de_tipo(piezas, tipo):
    return [p for p in piezas if p["tipo"] == tipo and p["escenas"]]


def expandir(p, piezas, azar=True):
    """Lista plana de escenas: cada pieza se reemplaza por sus escenas; «una al azar» elige una (o la más larga si azar=False)."""
    res = []
    for e in p["escenas"]:
        if "pieza" not in e:
            res.append(e)
            continue
        ref = e["pieza"]
        if ref.startswith("*"):
            ops = _piezas_de_tipo(piezas, ref[1:])
            if not ops:
                continue
            sel = random.choice(ops) if azar else max(ops, key=lambda x: sum(s["seg"] for s in x["escenas"]))
        else:
            sel = next((x for x in piezas if x["id"] == ref), None)
            if not sel:
                continue
        res.extend(sel["escenas"])
    return res


def duracion(p, piezas=None):
    return round(sum(float(e["seg"]) for e in expandir(p, piezas or [], azar=False)), 1)


def cargar(carpeta):
    try:
        d = json.loads(_ruta(carpeta).read_text(encoding="utf-8"))
    except Exception:
        d = {}
    pz = cargar_piezas()
    pls = [_limpia_plantilla(carpeta, p) for p in (d.get("plantillas") or [])[:MAX_PLANTILLAS]]
    for p in pls:
        p["duracion"] = duracion(p, pz)
    return {"plantillas": pls, "piezas": pz}


def guardar(carpeta, d):
    pls = [_limpia_plantilla(carpeta, p) for p in ((d or {}).get("plantillas") or [])[:MAX_PLANTILLAS]]
    _unicos(pls)
    _ruta(carpeta).write_text(json.dumps({"plantillas": pls}, ensure_ascii=False, indent=2), encoding="utf-8")
    return cargar(carpeta)


def plantilla(carpeta, pid):
    for p in cargar(carpeta)["plantillas"]:
        if p["id"] == pid:
            return p
    raise gd.ErrorMotor("No encuentro esa plantilla de escenas. Elige otra en «Crear videos».")


def fuentes(carpeta):
    """Qué se puede elegir como fuente de una escena: carpetas de palabras clave, kit y archivos sueltos."""
    carpeta = Path(carpeta)
    clips = carpeta / "clips"
    temas, archivos = [], {}
    if clips.exists():
        for d in sorted(x for x in clips.iterdir() if x.is_dir()):
            fs = sorted(p.relative_to(carpeta).as_posix() for p in gd.listar_media(d, True))
            temas.append({"nombre": d.name, "n": len(fs)})
            archivos[d.name] = fs
    kit = sorted(p.relative_to(carpeta).as_posix() for p in gd.listar_media(carpeta / "kit", False))
    return {"temas": temas, "kit": kit, "archivos": archivos}


def plan(p, piezas=None, pulsos=None):
    """Plan para el motor: escenas con su tiempo, qué clip buscar, ajustes del clip y los textos (marcas de texto en pantalla)."""
    escenas, textos, t = [], [], 0.0
    lista = expandir(p, piezas or [], azar=True)
    durs = [float(e["seg"]) for e in lista]
    if pulsos:
        import ritmo
        durs = ritmo.acomodar(durs, pulsos)
    for e, d in zip(lista, durs):
        esc = {"t0": t, "t1": t + d, "pals": []}
        f = e["fuente"]
        if f == "kit":
            esc["final"] = True
        elif f.startswith("tema:"):
            esc["tema_fijo"] = f[5:]
        elif f.startswith("archivo:"):
            esc["archivo"] = f[8:]
        if e.get("espejo") or e.get("giro") or e.get("ini"):
            esc["ajuste"] = {"espejo": bool(e.get("espejo")), "giro": int(e.get("giro") or 0), "ini": float(e.get("ini") or 0)}
        escenas.append(esc)
        if e["texto"]:
            textos.append(("", t + 0.05, t + 0.1, [{"t": "fx", "txt": True, "texto": e["texto"], "antes": True,
                                                    "seg": max(1.0, d - 0.25), "pos": e["pos"], "efecto": e["efecto"]}]))
        t += d
    if not escenas:
        raise gd.ErrorMotor("La plantilla no tiene escenas (o sus piezas están vacías). Agrega escenas en la pestaña «Escenas».")
    return {"escenas": escenas, "textos": textos, "total": t}
