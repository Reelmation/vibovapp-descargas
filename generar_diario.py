#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generador de videos verticales por PRODUCTO.

Cada producto vive en su propia carpeta dentro de "productos" y tiene sus propios guiones,
clips, imágenes del kit, ajustes y videos terminados. Nada se mezcla entre productos.

Uso (lo normal es hacer doble clic en el .bat de cada producto):
  python generar_diario.py --producto inmobiliaria     genera 1 video
  python generar_diario.py --producto viajes --cantidad 3
  python generar_diario.py --nuevo viajes              crea un producto nuevo
  python generar_diario.py --prueba                    demo con material de ejemplo
"""
import argparse
import datetime
import json
import math
import os
import random
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import unicodedata
import uuid
from pathlib import Path

from PIL import Image, ImageColor, ImageDraw

import catalogo
import generar_video as gv
from generar_video import BASE, IMG_EXT, VIDEO_EXT, duracion, run

# Donde viven los productos del usuario. En el programa instalado es una carpeta en Documentos;
# en modo desarrollo, la carpeta del programa.
DATOS = Path(os.environ.get("VIBOVAPP_DATOS") or BASE)

# Sonidos que vienen con la app (se generan al vuelo, no hay archivos). "@nombre" -> (expresión de aevalsrc, segundos)
SONIDOS_BASE = {
    "@pop": ("0.8*sin(2*PI*820*t)*exp(-26*t)", 0.2),
    "@ding": ("0.5*(sin(2*PI*1320*t)+0.5*sin(2*PI*1980*t))*exp(-6*t)", 0.8),
    "@click": ("0.8*sin(2*PI*2400*t)*exp(-120*t)", 0.08),
    "@whoosh": ("0.5*(random(0)*2-1)*sin(PI*t/0.5)*sin(PI*t/0.5)", 0.5),
}


def args_sonido(cfg, valor):
    """Argumentos de entrada de ffmpeg para un sonido elegido (de la app '@...' o un archivo de la carpeta sonidos del producto)."""
    v = str(valor or "").strip()
    if v in SONIDOS_BASE:
        expr, d = SONIDOS_BASE[v]
        return ["-f", "lavfi", "-t", f"{d}", "-i", f"aevalsrc={expr}:s=44100:d={d}"]
    if v and v.lower() != "ninguno":
        a = cfg["dir"] / "sonidos" / Path(v).name
        if a.is_file():
            return ["-i", str(a)]
        print(f"  Aviso: no encuentro el sonido '{v}'.")
    return None
PRODUCTOS = DATOS / "productos"


class ErrorMotor(Exception):
    """Error que se le puede mostrar tal cual al usuario (mensaje claro, sin detalles tecnicos)."""


class Cancelado(Exception):
    """El usuario pidio detener la generacion."""


CANCELAR = threading.Event()
ETAPA = [1]          # en qué paso del proceso va la creación de un video (para avisar bien si algo falla)


def paso(n):
    ETAPA[0] = n

AUDIO_EXT = {".mp3", ".wav", ".m4a", ".aac", ".ogg", ".oga", ".opus", ".flac", ".wma", ".amr", ".weba", ".3ga"}   # incluye las notas de voz de WhatsApp (.opus / .ogg)
TRANS_DINAMICAS = catalogo.TRANSICIONES_DINAMICAS
TRANS_SUAVES = catalogo.TRANSICIONES_SUAVES
PALABRAS_KIT = ["kit", "guiones", "guion", "prompts", "prompt", "crm", "notion", "pdf",
                "plantilla", "plantillas", "herramientas"]

# Todos los ajustes (valores por defecto, limites, textos) viven en catalogo.py
DEFECTOS = catalogo.defectos()
AJUSTES_BASE = catalogo.texto_ajustes({"usuario": "@tuusuario"})

TEMAS_BASE = """# TEMAS DE ESTE PRODUCTO (se edita con el Bloc de notas)
# Cada linea:  nombre_del_tema: palabra, palabra, palabra
# - El nombre del tema es el nombre de la carpeta (dentro de "clips") donde pones los videos de ese tema.
# - Las palabras son las que, cuando se dicen en el audio, hacen que se use un clip de ese tema.
# - Una palabra por espacio (no frases). Da igual si llevan acentos o mayusculas.
# - El tema "kit" es especial: usa las imagenes de la carpeta "kit" (tus capturas del producto).
# - Las carpetas de cada tema se crean solas la primera vez que generas un video.
#
# Ejemplo (quita el # y cambia las palabras por las de tu producto):
# playa: playa, mar, arena, costa, vacaciones
# hoteles: hotel, hoteles, habitacion, alojamiento

# kit: tus, palabras, que, mencionan, tu, producto
"""


# ----------------------------------------------------------------------------
# Lectura de archivos de texto sencillos
# ----------------------------------------------------------------------------
def leer_archivo_texto(path):
    crudo = Path(path).read_bytes()
    try:
        return crudo.decode("utf-8-sig")
    except UnicodeDecodeError:
        return crudo.decode("cp1252", errors="replace")


def normalizar(t):
    t = unicodedata.normalize("NFD", t.lower())
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]", "", t)


def leer_ajustes(path, cfg):
    """Lee ajustes.txt (nombre: valor), valida cada valor con el catalogo y avisa de lo que no entienda."""
    avisos = []
    if not path.exists():
        return avisos
    for linea in leer_archivo_texto(path).splitlines():
        s = linea.strip()
        if not s or s.startswith("#") or ":" not in s:
            continue
        k, v = s.split(":", 1)
        k, v = k.strip().lower().replace(" ", "_"), v.strip()
        if k not in catalogo.POR_CLAVE:
            avisos.append(f"El ajuste '{k}' no existe, se ignora.")
            continue
        valor, error = catalogo.validar(k, v)
        if error:
            avisos.append(f"Ajuste '{k}': {error}. Se usa el valor anterior ({cfg[k]}).")
            continue
        cfg[k] = valor
    for a in avisos:
        print("Aviso:", a)
    return avisos


def leer_temas(path):
    temas = {}
    if path.exists():
        for linea in leer_archivo_texto(path).splitlines():
            s = linea.strip()
            if not s or s.startswith("#") or ":" not in s:
                continue
            nombre, kws = s.split(":", 1)
            nombre = normalizar(nombre)
            palabras = [normalizar(k) for k in kws.split(",") if normalizar(k)]
            if nombre and palabras:
                temas[nombre] = palabras
    temas.setdefault("kit", [])   # sin palabras de fabrica: cada producto define las suyas
    return temas


def es_si(v):
    return str(v).strip().lower() in ("si", "sí", "s", "yes", "y", "true", "1")


def aplicar_formato(cfg):
    """Pone ancho y alto segun el formato elegido (vertical, cuadrado, horizontal...). 'personalizado' respeta ancho y alto."""
    medidas = catalogo.FORMATOS.get(str(cfg.get("formato_video")))
    if medidas:
        cfg["ancho"], cfg["alto"] = medidas
    return cfg


def carpeta_formato(cfg):
    """Subcarpeta de salida segun el formato: vertical, retrato, cuadrado, horizontal o personalizado/1200x800."""
    fv = str(cfg.get("formato_video"))
    if fv in catalogo.FORMATOS:
        return fv
    return f"personalizado/{int(cfg['ancho'])}x{int(cfg['alto'])}"


def ajustar_pantalla_completa(cfg):
    if es_si(cfg["pantalla_completa"]):
        cfg["media_y"], cfg["media_alto"] = 0, cfg["alto"]
        cfg["subs_y"] = cfg["subs_y_completa"]
    return cfg


def es_producto_practica(carpeta):
    """True si es el producto de la práctica guiada (lleva la marca practica.json, o se llama «practica»)."""
    carpeta = Path(carpeta)
    return carpeta.name == "practica" or (carpeta / "practica.json").exists()


def practica_terminada(carpeta):
    """True si ya se llegó al final de la práctica guiada con este producto (queda bloqueado para crear videos)."""
    try:
        return bool(json.loads((Path(carpeta) / "practica.json").read_text(encoding="utf-8")).get("terminada"))
    except Exception:
        return False


def terminar_practica(carpeta):
    f = Path(carpeta) / "practica.json"
    d = {}
    try:
        d = json.loads(f.read_text(encoding="utf-8"))
    except Exception:
        pass
    d["practica"] = True
    d["terminada"] = True
    f.write_text(json.dumps(d), encoding="utf-8")


CLAVES_DISPOSICION = tuple(catalogo.PRESETS_FORMATO["cuadrado"]) + ("burbuja_x",)


def leer_disposiciones(carpeta):
    """Posiciones y tamaños (titulo, subtitulos, frase final, usuario, burbujas, barra) que dejaste en cada formato.
    Se guardan en el producto, aparte del estilo, para que cada formato se quede como lo usaste la ultima vez."""
    try:
        d = json.loads((Path(carpeta) / "disposicion_formatos.json").read_text(encoding="utf-8"))
        return {f: v for f, v in d.items() if isinstance(v, dict)} if isinstance(d, dict) else {}
    except Exception:
        return {}


def guardar_disposiciones(carpeta, d):
    try:
        (Path(carpeta) / "disposicion_formatos.json").write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    except OSError:
        pass


def cfg_formato(cfg, fmt):
    """Copia de la configuracion para crear el mismo video en otro formato (con las posiciones recomendadas de ese formato)."""
    if fmt == cfg.get("formato_video"):
        return cfg
    c = dict(cfg)
    c["formato_video"] = fmt
    aplicar_formato(c)
    c.update(catalogo.PRESETS_FORMATO.get(fmt, {}))
    # si ya afinaste ese formato (posiciones y tamaños de textos y burbujas), se usa lo que dejaste la ultima vez
    if cfg.get("dir"):
        c.update(leer_disposiciones(cfg["dir"]).get(fmt, {}))
    return ajustar_pantalla_completa(c)


def normalizar_tamano(t):
    """{ancho, alto} escritos por la persona -> (ancho, alto) pares y dentro de lo razonable; None si no sirven."""
    try:
        w, h = int(float(t["ancho"])), int(float(t["alto"]))
    except Exception:
        return None
    w, h = max(240, min(4320, w // 2 * 2)), max(240, min(4320, h // 2 * 2))
    return (w, h)


def formatos_destino(cfg, formatos=None):
    """Lista de (formato, cfg) a crear. 'formatos' = los que el usuario marcó (si no se da, se usa lo guardado
    en el ajuste formatos_crear, y si está vacío, solo el formato principal)."""
    principal = str(cfg["formato_video"])
    if formatos is None:
        formatos = str(cfg.get("formatos_crear") or "").split(",")
    pedidos = []
    for f in formatos:
        f = str(f).strip()
        if (f in catalogo.FORMATOS or f == "personalizado") and f not in pedidos:
            pedidos.append(f)
    if not pedidos:
        pedidos = [principal]
    # el principal es el que lleva tus posiciones y tamaños afinados; los demas usan los recomendados de su formato
    res = []
    for f in pedidos:
        c = cfg if f == principal else cfg_formato(cfg, f)
        if f == "personalizado" and cfg.get("_pers"):          # tamaño escrito en «Crear videos»
            c = dict(c)
            c["ancho"], c["alto"] = cfg["_pers"]
            ajustar_pantalla_completa(c)
        res.append((f, c))
    return res


def cargar_config(carpeta_producto):
    cfg = dict(DEFECTOS)
    leer_ajustes(carpeta_producto / "ajustes.txt", cfg)
    aplicar_formato(cfg)
    if cfg["oscurecer_min"] > cfg["oscurecer_max"]:
        cfg["oscurecer_min"], cfg["oscurecer_max"] = cfg["oscurecer_max"], cfg["oscurecer_min"]
    ajustar_pantalla_completa(cfg)
    cfg["dir"] = carpeta_producto
    return cfg


# ----------------------------------------------------------------------------
# Guiones y estado
# ----------------------------------------------------------------------------
def clave_natural(p):
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", p.stem)]


def listar_guiones(carpeta):
    if not carpeta.exists():
        raise RuntimeError(f"No existe la carpeta de guiones: {carpeta}")
    todos = [p for p in carpeta.iterdir() if p.suffix.lower() in AUDIO_EXT and not p.name.startswith("_")]
    if not todos:
        raise RuntimeError(f"No hay audios (.mp3/.wav/.m4a) en {carpeta}")
    apagados = guiones_apagados(carpeta)
    archivos = [p for p in todos if p.name not in apagados]
    if not archivos:
        raise RuntimeError("Todos tus guiones están apagados. Enciende al menos uno en la pestaña Guiones.")
    return sorted(archivos, key=clave_natural)


def guiones_apagados(carpeta_guiones):
    """Nombres de los guiones que el usuario apagó (no se usan al crear videos)."""
    try:
        d = json.loads((carpeta_guiones.parent / "guiones_apagados.json").read_text(encoding="utf-8"))
        return set(d) if isinstance(d, list) else set()
    except Exception:
        return set()


def leer_texto(audio):
    """Devuelve (gancho, texto_hablado). Ambos vacíos si no hay .txt."""
    t = audio.with_suffix(".txt")
    if not t.exists():
        return "", ""
    gancho, cuerpo = "", []
    for linea in leer_archivo_texto(t).splitlines():
        s = linea.strip()
        if not s:
            continue
        if s.startswith("#") and not gancho:
            gancho = s.lstrip("#").strip()
        else:
            cuerpo.append(s)
    return gancho, " ".join(cuerpo)


def cargar_estado(path):
    est = {"usados": [], "ciclo": 1, "contador": 0, "recientes": []}
    if path.exists():
        est.update(json.loads(path.read_text(encoding="utf-8")))
    return est


def guardar_estado(path, est):
    path.write_text(json.dumps(est, indent=2, ensure_ascii=False), encoding="utf-8")


def elegir_guion(guiones, est):
    """Siguiente guion que NO se haya usado en esta vuelta. Al agotarlos todos, empieza otra vuelta."""
    nombres = [g.name for g in guiones]
    est["usados"] = [n for n in est["usados"] if n in nombres]
    pendientes = [g for g in guiones if g.name not in est["usados"]]
    if not pendientes:
        est["ciclo"] += 1
        est["usados"] = []
        pendientes = guiones
        print(f"Ya usaste los {len(guiones)} guiones. Empieza la vuelta {est['ciclo']}.")
    return pendientes[0]


# ----------------------------------------------------------------------------
# Tiempos de las palabras (para subtítulos y para ligar imágenes con lo que se dice)
# ----------------------------------------------------------------------------
_whisper = None


def transcribir_whisper(cfg, audio):
    """Tiempos por palabra con faster-whisper (opcional). None si no está instalado."""
    cache_dir = cfg["dir"] / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache = cache_dir / (audio.stem + ".json")
    if cache.exists() and cache.stat().st_mtime >= audio.stat().st_mtime:
        return json.loads(cache.read_text(encoding="utf-8"))
    global _whisper
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        return None
    if _whisper is None:
        print("  Cargando Whisper (la primera vez descarga el modelo)...")
        _whisper = WhisperModel(cfg["whisper_modelo"], device="cpu", compute_type="int8")
    segs, _ = _whisper.transcribe(str(audio), language="es", word_timestamps=True)
    palabras = [[w.word.strip(), float(w.start), float(w.end)]
                for s in segs for w in (s.words or []) if w.word.strip()]
    cache.write_text(json.dumps(palabras, ensure_ascii=False), encoding="utf-8")
    return palabras


_ENV_CACHE = {}


def envolvente_voz(audio):
    """Analiza el volumen del audio cada 20 ms y separa HABLA de NO-HABLA con un umbral que se adapta al propio audio
    (así funciona aunque haya ruido de fondo o música). Devuelve (inicio_voz, fin_voz, pausas[(a, b)]) o None."""
    clave = (str(audio), os.path.getmtime(audio))
    if clave in _ENV_CACHE:
        return _ENV_CACHE[clave]
    res = None
    try:
        import array
        r = subprocess.run(["ffmpeg", "-v", "error", "-i", str(audio), "-vn", "-ac", "1", "-ar", "8000",
                            "-af", "highpass=f=120,lowpass=f=3400", "-f", "s16le", "-"],
                           capture_output=True, stdin=subprocess.DEVNULL, creationflags=gv.SIN_VENTANA)
        pcm = array.array("h")
        pcm.frombytes(r.stdout[: len(r.stdout) // 2 * 2])
        hop = 160                                            # 20 ms a 8 kHz
        n = len(pcm) // hop
        if n >= 25:
            db = []
            for k in range(n):
                tr = pcm[k * hop:(k + 1) * hop]
                db.append(10 * math.log10(sum(x * x for x in tr) / hop + 1.0))
            # suavizar (ventana de 3)
            sm = [sum(db[max(0, i - 1):i + 2]) / len(db[max(0, i - 1):i + 2]) for i in range(n)]
            orden = sorted(sm)
            piso, techo = orden[int(n * 0.04)], orden[int(n * 0.90)]
            if techo - piso >= 10:
                umbral = max(piso + 0.35 * (techo - piso), techo - 25)      # el ruido del micrófono nunca cuenta como voz, aunque haya huecos de silencio total
                habla = [v > umbral for v in sm]
                # cerrar huecos muy cortos (< 80 ms) dentro del habla y quitar destellos de menos de 100 ms
                runs, i = [], 0
                while i < n:
                    j = i
                    while j < n and habla[j] == habla[i]:
                        j += 1
                    runs.append([habla[i], i, j])
                    i = j
                for rr in runs:
                    if not rr[0] and rr[2] - rr[1] < 4:
                        rr[0] = True
                fus = []
                for rr in runs:
                    if fus and fus[-1][0] == rr[0]:
                        fus[-1][2] = rr[2]
                    else:
                        fus.append(rr[:])
                for rr in fus:
                    if rr[0] and rr[2] - rr[1] < 5:
                        rr[0] = False
                voz = [(a * 0.02, b * 0.02) for h_, a, b in fus if h_]
                # (volver a juntar si al quitar destellos quedaron huecos contiguos)
                if voz:
                    inicio, fin = voz[0][0], voz[-1][1]
                    pausas = []
                    for (a1, b1), (a2, b2) in zip(voz, voz[1:]):
                        pausas.append((b1, a2))
                    res = (inicio, fin, [(a, b) for a, b in pausas if b - a >= 0.12])
    except Exception:
        res = None
    _ENV_CACHE[clave] = res
    return res


def rango_voz(audio, total):
    env = envolvente_voz(audio)
    if env:
        return max(0.0, env[0] - 0.05), max(env[1] + 0.1, env[0] + 0.5)
    return _rango_voz_silencio(audio, total)


def _rango_voz_silencio(audio, total):
    r = subprocess.run(["ffmpeg", "-v", "info", "-i", str(audio), "-af",
                        "silencedetect=noise=-35dB:d=0.3", "-f", "null", "-"],
                       capture_output=True, text=True, stdin=subprocess.DEVNULL, creationflags=gv.SIN_VENTANA)
    starts = [float(x) for x in re.findall(r"silence_start: (-?[\d.]+)", r.stderr)]
    ends = [float(x) for x in re.findall(r"silence_end: (-?[\d.]+)", r.stderr)]
    inicio, fin = 0.0, total
    if starts and starts[0] < 0.05 and ends:
        inicio = ends[0]
    if starts:
        # ¿el último silencio llega hasta el final del archivo? (ffmpeg lo reporta con su 'silence_end' al terminar)
        try:
            largo = duracion(audio)
        except Exception:
            largo = total
        if len(ends) < len(starts) or ends[-1] >= largo - 0.15:
            fin = starts[-1]
    return max(0.0, inicio), max(fin, inicio + 0.5)


_FUERTES = set("aeoáéóàè")
_VOCALES = set("aeiouáéíóúüàèìòù")


def silabas(p):
    """Cuenta sílabas de una palabra en español (aproximado). Los números y símbolos se cuentan como se leen."""
    n = 0
    for tramo in re.findall(r"\d+|[^\W\d_]+|[%$@&+=€£]", p):
        if tramo.isdigit():
            n += max(2, int(len(tramo) * 1.6))         # "2026" se lee "dos mil veintiséis"
        elif tramo in "%$@&+=€£":
            n += 3 if tramo == "%" else 2
        else:
            t = tramo.lower()
            cuenta, prev = 0, ""
            for ch in t:
                if ch in _VOCALES:
                    # nueva sílaba si la anterior no era vocal, o dos vocales fuertes juntas (hiato), o í/ú con tilde al lado
                    if not prev or prev not in _VOCALES or (prev in _FUERTES and ch in _FUERTES) or ch in "íú" or prev in "íú":
                        cuenta += 1
                prev = ch
            if cuenta == 0:
                cuenta = max(1, len(t) // 2)          # siglas o letras sueltas
            elif tramo.isupper() and len(tramo) <= 5 and cuenta == 1 and len(tramo) > 2:
                cuenta = len(tramo)                    # siglas como "IVA" o "CRM" se deletrean
            n += cuenta
    return n


def peso_habla(p):
    """Cuánto tarda más o menos en decirse una palabra (en 'sílabas'). Guiones y signos sueltos casi no pesan."""
    if not re.search(r"\w", p):
        return 0.05
    return silabas(p) + 0.4


def tiempos_proporcionales(palabras, inicio, fin):
    def peso(p):
        base = peso_habla(p)
        if p[-1:] in ".!?":
            base += 3
        elif p[-1:] in ",;:":
            base += 1.5
        return base
    pesos = [peso(p) for p in palabras]
    escala = (fin - inicio) / sum(pesos)
    out, t = [], inicio
    for p, w in zip(palabras, pesos):
        out.append([p, t, t + w * escala])
        t += w * escala
    return out


def _alinear_por_indice(palabras_txt, palabras_w):
    n, m = len(palabras_txt), len(palabras_w)
    out = []
    for i, p in enumerate(palabras_txt):
        f = i * m / n
        j = min(int(f), m - 1)
        sig = palabras_w[j + 1][1] if j + 1 < m else palabras_w[j][2]
        inicio = palabras_w[j][1] + (f - j) * (sig - palabras_w[j][1])
        out.append([p, inicio, None])
    for i in range(n):
        out[i][2] = out[i + 1][1] if i + 1 < n else palabras_w[-1][2]
    return out


def alinear(palabras_txt, palabras_w):
    """Pone tiempos a las palabras de TU texto usando lo que Whisper escucho. Se apoya en las palabras que
    coinciden (anclas) y reparte las demas entre ancla y ancla, asi el desfase no se acumula en guiones largos."""
    import difflib
    n, m = len(palabras_txt), len(palabras_w)
    if not n or not m:
        return _alinear_por_indice(palabras_txt, palabras_w) if m else []
    a = [normalizar(p) or "_" for p in palabras_txt]
    b = [normalizar(p[0]) or "_" for p in palabras_w]
    anclas = []
    for bloque in difflib.SequenceMatcher(None, a, b, autojunk=False).get_matching_blocks():
        for k in range(bloque.size):
            anclas.append((bloque.a + k, palabras_w[bloque.b + k][1]))
    if len(anclas) < max(3, n * 0.25):          # casi no coincide: reparto parejo como antes
        return _alinear_por_indice(palabras_txt, palabras_w)
    if anclas[0][0] > 0:
        anclas.insert(0, (0, min(palabras_w[0][1], anclas[0][1])))
    anclas.append((n, palabras_w[-1][2]))
    inicios = [0.0] * n
    for (i0, t0), (i1, t1) in zip(anclas, anclas[1:]):
        for i in range(i0, min(i1, n)):
            inicios[i] = t0 + (t1 - t0) * (i - i0) / max(1, i1 - i0)
    out = []
    for i, p in enumerate(palabras_txt):
        fin = inicios[i + 1] if i + 1 < n else palabras_w[-1][2]
        out.append([p, inicios[i], max(fin, inicios[i] + 0.05)])
    return out


def _pausas_audio(audio, total):
    """Pausas del habla: [(inicio, fin)]. Sirven como puntos de apoyo para los subtitulos."""
    p = _pausas_silencio(audio, total)       # silencio real: es lo más fiable
    if len(p) < 3:                           # audio con ruido o música de fondo: no hay silencio total; se usa el volumen de la voz
        env = envolvente_voz(audio)
        if env:
            p = [(a, b) for a, b in env[2] if b - a >= 0.3]
    return p


def _pausas_silencio(audio, total):
    r = subprocess.run(["ffmpeg", "-v", "info", "-i", str(audio), "-af",
                        "silencedetect=noise=-35dB:d=0.18", "-f", "null", "-"],
                       capture_output=True, text=True, stdin=subprocess.DEVNULL, creationflags=gv.SIN_VENTANA)
    s = [float(x) for x in re.findall(r"silence_start: (-?[\d.]+)", r.stderr)]
    e = [float(x) for x in re.findall(r"silence_end: (-?[\d.]+)", r.stderr)]
    pares = []
    for k, ini in enumerate(s):
        pares.append((max(0.0, ini), e[k] if k < len(e) else total))
    return pares


def _emparejar_pausas(internas, A, cortes, habla_total):
    """Decide qué pausa del audio corresponde a cada signo de puntuación del texto (alineación monótona:
    gana la pareja pausa-corte más cercana, premiando las pausas largas). Devuelve [(índice de palabra, pausa)]."""
    P, C = len(internas), len(cortes)
    TOL = 0.12
    dp = [[0.0] * (C + 1) for _ in range(P + 1)]
    pareja = [[None] * (C + 1) for _ in range(P + 1)]
    for i in range(1, P + 1):
        a, b = internas[i - 1]
        largo = min(2.0, (b - a) / 0.4)
        for j in range(1, C + 1):
            mejor, de = dp[i - 1][j], (i - 1, j)
            if dp[i][j - 1] > mejor:
                mejor, de = dp[i][j - 1], (i, j - 1)
            d = abs(A[i - 1] - cortes[j - 1][1])
            if d <= TOL:
                v = dp[i - 1][j - 1] + (TOL - d) * (0.5 + largo) * cortes[j - 1][2] + 0.01
                if v > mejor:
                    mejor, de = v, (i - 1, j - 1, True)
            dp[i][j], pareja[i][j] = mejor, de
    anclas, i, j = [], P, C
    while i > 0 and j > 0:
        de = pareja[i][j]
        if de is None:
            break
        if len(de) == 3:
            anclas.append((cortes[j - 1][0], internas[i - 1]))
        i, j = de[0], de[1]
    anclas.reverse()
    return anclas


def tiempos_con_pausas(palabras, pausas, inicio, fin):
    """Sin Whisper: reparte las palabras segun su largo, pero amarrando los signos de puntuacion del texto
    (. , ; : ! ?) a las pausas reales del audio. Asi el error se reinicia en cada pausa y no se acumula."""
    peso = peso_habla
    n = len(palabras)
    pesos = [peso(p) for p in palabras]
    acum, s = [], 0.0
    for w in pesos:
        s += w
        acum.append(s)
    total_peso = s
    # pausas dentro del habla (no las de los extremos)
    internas = [(a, b) for a, b in pausas if a > inicio + 0.25 and b < fin - 0.25 and b - a >= 0.18]
    if not internas or n < 4:
        return tiempos_proporcionales(palabras, inicio, fin)
    dur = fin - inicio
    # fraccion de "tiempo de habla" de cada pausa (sin contar el tiempo de las pausas)
    habla_total = dur - sum(b - a for a, b in internas)
    if habla_total <= 0:
        return tiempos_proporcionales(palabras, inicio, fin)
    A, acumulado = [], 0.0
    prev = inicio
    for a, b in internas:
        acumulado += a - prev
        A.append(acumulado / habla_total)
        prev = b
    # limites del texto: despues de una palabra con puntuacion
    fuertes = ".!?"
    cortes = [(i, acum[i] / total_peso, 1.0 if palabras[i][-1:] in fuertes else 0.6)
              for i in range(n - 1) if palabras[i][-1:] in ".!?,;:"]
    if not cortes:
        return tiempos_proporcionales(palabras, inicio, fin)
    anclas = _emparejar_pausas(internas, A, cortes, habla_total)
    if not anclas:
        return tiempos_proporcionales(palabras, inicio, fin)
    # tramos: [inicio .. pausa1.inicio], [pausa1.fin .. pausa2.inicio], ... [pausaN.fin .. fin]
    out = [None] * n
    ini_tramo, i0 = inicio, 0
    for idx_corte, (pa, pb) in anclas + [(n - 1, (fin, fin))]:
        fin_tramo = pa
        trozo = pesos[i0:idx_corte + 1]
        esc = max(0.0, fin_tramo - ini_tramo) / max(1, sum(trozo))
        t = ini_tramo
        for k, w in enumerate(trozo):
            out[i0 + k] = [palabras[i0 + k], t, t + w * esc]
            t += w * esc
        ini_tramo, i0 = pb, idx_corte + 1
    return out


def palabras_con_tiempos(cfg, audio, texto, total):
    w = transcribir_whisper(cfg, audio)
    palabras_txt = texto.split()
    if w and palabras_txt:
        print("  Subtítulos: sincronizados con Whisper (escucha el audio).")
        res = alinear(palabras_txt, w)
    elif w:
        res = w
    elif palabras_txt:
        print("  Subtítulos: tiempos estimados con las pausas del audio (sin Whisper).")
        inicio, fin = rango_voz(audio, total)
        try:
            res = tiempos_con_pausas(palabras_txt, _pausas_audio(audio, total), inicio, fin)
        except Exception:
            res = tiempos_proporcionales(palabras_txt, inicio, fin)
    else:
        return None
    aj = float(cfg.get("subs_ajuste", 0) or 0)       # ajuste fino manual (segundos)
    if aj:
        res = [[p, max(0.0, a + aj), max(0.0, b + aj)] for p, a, b in res]
    return res


# ----------------------------------------------------------------------------
# Subtítulos (secuencia de imágenes PNG con transparencia)
# ----------------------------------------------------------------------------
def limpiar_palabra(p, mayusculas=True):
    p = p.strip(".,;:")
    return p.upper() if mayusculas else p


ALTO_BANDA_SUBS = 260      # alto de la imagen de subtitulos; "subs_y" es la altura de su CENTRO (igual que en la vista previa)


def _color_texto_sobre(fondo):
    """Texto oscuro sobre una caja clara y claro sobre una oscura."""
    try:
        r, g, b = ImageColor.getrgb(fondo)[:3]
    except ValueError:
        return "#000000"
    return "#111111" if (r * 299 + g * 587 + b * 114) / 1000 > 140 else "#FFFFFF"


ESTILOS_SUBS = ("color", "caja", "grande", "una")
ESTILOS_VALIDOS = ESTILOS_SUBS + ("doble",)      # «doble» (palabras clave grandes arriba y la frase en una caja abajo) se elige a propósito; no entra en el «al azar»
ANIMACIONES_SUBS = ("pop", "subir", "fundido", "rebote")


def _palabra_clave(textos):
    """Índice de la palabra que más conviene destacar en una tarjeta: la más larga (de 5 letras en adelante). None si no hay."""
    mejor, largo = None, 4
    for i, t in enumerate(textos):
        n = len(t.strip(".,;:!?¡¿\"'"))
        if n > largo:
            mejor, largo = i, n
    return mejor


def _imagen_subtitulo_doble(cfg, grupo, activa):
    """Dos niveles, como en los reels de noticias: arriba las palabras clave grandes y de color; abajo la frase completa en una caja
    (lo que ya se dijo en blanco y lo que falta en gris)."""
    W = cfg["ancho"]
    img = Image.new("RGBA", (W, ALTO_BANDA_SUBS), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    palabras = [p.strip() for p in grupo if p.strip()]
    if not palabras:
        return img
    limpias = [p.strip(".,;:!?¡¿\"'") for p in palabras]
    largas = sorted(range(len(limpias)), key=lambda i: -len(limpias[i]))
    claves = sorted(i for i in largas[:2] if len(limpias[i]) >= 4) or [min(activa, len(palabras) - 1)]
    arriba = " ".join(limpiar_palabra(palabras[i], True) for i in claves)
    color_clave = cfg.get("subs_destacar_color") or "#FF4D6D"
    tam = int(cfg["subs_tam"])
    while True:
        f_top = gv.cargar_fuente(cfg, tam, "subs")
        f_baj = gv.cargar_fuente(cfg, max(26, int(tam * 0.5)), "subs")
        lineas = gv.envolver(f_baj, " ".join(palabras), W - 200)[:2]
        alto_baj = len(lineas) * int(f_baj.size * 1.3) + 26
        alto_top = int(tam * 1.2)
        if (alto_top + 10 + alto_baj <= ALTO_BANDA_SUBS - 6 and f_top.getlength(arriba) <= W - 100) or tam <= 34:
            break
        tam -= 4
    y = (ALTO_BANDA_SUBS - (alto_top + 10 + alto_baj)) / 2
    d.text(((W - f_top.getlength(arriba)) / 2, y), arriba, font=f_top, fill=color_clave, stroke_width=int(cfg["trazo_subs"]), stroke_fill=cfg["color_trazo"])
    y += alto_top + 10
    ancho_caja = max(f_baj.getlength(l) for l in lineas) + 56
    x0 = (W - ancho_caja) / 2
    d.rounded_rectangle((x0, y, x0 + ancho_caja, y + alto_baj), radius=16, fill=(0, 0, 0, 175))
    dichas = 0
    yy = y + 13
    for l in lineas:
        x = (W - f_baj.getlength(l)) / 2
        for pal in l.split(" "):
            hecho = dichas <= activa
            d.text((x, yy), pal, font=f_baj, fill=(255, 255, 255, 255) if hecho else (170, 170, 170, 255))
            x += f_baj.getlength(pal + " ")
            dichas += 1
        yy += int(f_baj.size * 1.3)
    return img


def imagen_subtitulo(cfg, grupo, activa, estilo=None, destacar=None):
    """Dibuja una tarjeta de subtítulos (imagen con transparencia). estilo/destacar permiten variar tarjeta por tarjeta."""
    W = cfg["ancho"]
    alto_banda = ALTO_BANDA_SUBS
    img = Image.new("RGBA", (W, alto_banda), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    estilo = str(estilo or cfg.get("subs_estilo", "color") or "color")
    if estilo == "doble":
        return _imagen_subtitulo_doble(cfg, grupo, activa)
    destacar = str(destacar if destacar is not None else cfg.get("subs_destacar", "no") or "no")
    textos = [limpiar_palabra(p, cfg["subs_mayusculas"]) for p in grupo]
    if estilo == "una":                      # una palabra a la vez, bien grande
        textos, activa = [textos[activa]], 0
    clave = _palabra_clave(textos) if destacar in ("color", "caja") and estilo != "una" else None
    color_dest = cfg.get("subs_destacar_color") or "#FF4D6D"
    tam = int(cfg["subs_tam"]) if estilo != "una" else int(cfg["subs_tam"] * 1.25)
    extra = 1.18 if estilo == "grande" else 1.0
    while True:
        fuente = gv.cargar_fuente(cfg, tam, "subs")
        fuente_act = gv.cargar_fuente(cfg, int(tam * extra), "subs") if extra != 1.0 else fuente
        fuente_cl = gv.cargar_fuente(cfg, int(tam * 1.12), "acento") if clave is not None else fuente
        esp = fuente.getlength(" ")
        fuentes = [fuente_cl if i == clave else (fuente_act if i == activa else fuente) for i in range(len(textos))]
        anchos = [fuentes[i].getlength(t) for i, t in enumerate(textos)]
        total = sum(anchos) + esp * (len(textos) - 1)
        if total <= (int(float(cfg.get("subs_ancho", 0) or 0)) or W) - 120 or tam <= 36:
            break
        tam -= 4
    x = (W - total) / 2
    y = (alto_banda - tam * 1.15) / 2
    trazo = int(cfg["trazo_subs"])
    for i, (t, a) in enumerate(zip(textos, anchos)):
        act = i == activa
        f = fuentes[i]
        yy = y - (tam * (extra - 1.0) * 0.55 if act else 0)
        if i == clave:                       # palabra clave: otro color (y otra letra si se eligió una en «Letra de la palabra destacada»)
            yy = y - tam * 0.06
            if destacar == "caja":
                pad = int(tam * 0.16)
                bb = d.textbbox((x, yy), t, font=f)
                d.rounded_rectangle((bb[0] - pad, bb[1] - pad * 0.7, bb[2] + pad, bb[3] + pad * 0.7), radius=int(tam * 0.2), fill=color_dest)
                d.text((x, yy), t, font=f, fill=_color_texto_sobre(color_dest))
            else:
                d.text((x, yy), t, font=f, fill=color_dest, stroke_width=trazo, stroke_fill=cfg["color_trazo"])
        elif act and estilo == "caja":
            pad = int(tam * 0.16)
            bb = d.textbbox((x, y), t, font=f)
            d.rounded_rectangle((bb[0] - pad, bb[1] - pad * 0.7, bb[2] + pad, bb[3] + pad * 0.7), radius=int(tam * 0.2), fill=cfg["subs_color_activo"])
            d.text((x, y), t, font=f, fill=_color_texto_sobre(cfg["subs_color_activo"]))
        else:
            color = cfg["subs_color_activo"] if act and estilo != "una" else cfg["subs_color"]
            if estilo == "una":
                color = cfg["subs_color_activo"]
            d.text((x, yy), t, font=f, fill=color, stroke_width=trazo, stroke_fill=cfg["color_trazo"])
        x += a + esp
    return img


def png_subtitulo(cfg, grupo, activa, destino, estilo=None, destacar=None):
    imagen_subtitulo(cfg, grupo, activa, estilo, destacar).save(destino)


# Animación de entrada de cada tarjeta: unos pocos cuadros (≈0.17 s) que se dibujan con Pillow antes de la tarjeta ya quieta.
_PASOS_ANIM = {
    #            escala                      desplazamiento vertical (px)   opacidad
    "pop":     ([0.70, 0.88, 1.10, 1.05, 1.0], [0, 0, 0, 0, 0],             [0.45, 0.8, 1, 1, 1]),
    "subir":   ([1.0] * 5,                     [64, 34, 15, 5, 0],          [0.25, 0.55, 0.8, 0.95, 1]),
    "fundido": ([1.0] * 5,                     [0] * 5,                     [0.15, 0.35, 0.6, 0.85, 1]),
    "rebote":  ([1.0] * 5,                     [70, -22, 11, -4, 0],        [0.7, 1, 1, 1, 1]),
}
DUR_CUADRO_ANIM = 0.034


def cuadros_animacion(img, anim):
    """Lista de imágenes (una por cuadro) que llevan la tarjeta a su posición final. [] si no hay animación."""
    paso = _PASOS_ANIM.get(anim)
    if not paso:
        return []
    escalas, dys, ops = paso
    W, H = img.size
    res = []
    for e, dy, op in zip(escalas, dys, ops):
        im = img if e == 1.0 else img.resize((max(1, int(W * e)), max(1, int(H * e))), Image.LANCZOS)
        lienzo = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        lienzo.paste(im, (int((W - im.width) / 2), int((H - im.height) / 2 + dy)), im)
        if op < 1:
            al = lienzo.getchannel("A").point(lambda v, o=op: int(v * o))
            lienzo.putalpha(al)
        res.append(lienzo)
    return res


def crear_subtitulos(cfg, palabras, total, tmp):
    W = cfg["ancho"]
    blank = tmp / "sub_blank.png"
    Image.new("RGBA", (W, 260), (0, 0, 0, 0)).save(blank)
    est_pal = {}                              # estilo propio de una frase marcada («estilo=caja» en la marca)
    for idx_, w_ in enumerate(palabras):
        for m_ in (w_[3] if len(w_) > 3 and isinstance(w_[3], list) else []):
            if isinstance(m_, dict) and m_.get("estilo") in ESTILOS_VALIDOS:
                for j_ in range(idx_, min(len(palabras), idx_ + max(1, int(m_.get("n") or 1)))):
                    est_pal[j_] = m_["estilo"]
    n_por = cfg["subs_palabras"]
    grupos, act = [], []
    for i, w in enumerate(palabras):
        doble = (est_pal.get(i) or str(cfg.get("subs_estilo") or "")) == "doble"
        if act and est_pal.get(i) != est_pal.get(act[-1]):          # al cambiar de estilo empieza otra tarjeta
            grupos.append(act)
            act = []
        if act and len(" ".join(limpiar_palabra(palabras[j][0]) for j in act + [i])) > (40 if doble else 18):
            grupos.append(act)
            act = []
        act.append(i)
        if len(act) >= (max(n_por, 6) if doble else n_por) or w[0][-1:] in ".!?":
            grupos.append(act)
            act = []
    if act:
        grupos.append(act)

    anim_cfg = str(cfg.get("subs_animacion", "ninguna") or "ninguna")
    al_azar_estilo = es_si(cfg.get("subs_estilo_azar", False))
    entradas, t, contador, previo = [], 0.0, 0, None
    for g in grupos:
        textos = [palabras[i][0] for i in g]
        estilo_g = None
        if al_azar_estilo:                   # cada tarjeta estrena estilo (sin repetir el de la anterior)
            estilo_g = random.choice([e for e in ESTILOS_SUBS if e != previo] or list(ESTILOS_SUBS))
            previo = estilo_g
        if est_pal.get(g[0]):
            estilo_g = est_pal[g[0]]
        anim_g = random.choice(ANIMACIONES_SUBS) if anim_cfg == "azar" else anim_cfg
        col_g = palabras[g[0]][4] if len(palabras[g[0]]) > 4 else None      # color propio de quien habla (conversaciones)
        cfg_g = dict(cfg, subs_color_activo=col_g) if col_g else cfg
        for k, idx in enumerate(g):
            inicio = palabras[idx][1]
            fin = palabras[g[k + 1]][1] if k + 1 < len(g) else palabras[idx][2] + 0.15
            if inicio > t + 0.02:
                entradas.append((blank, inicio - t))
                t = inicio
            dur = max(0.04, fin - t)
            png = tmp / f"sub_{contador:04d}.png"
            contador += 1
            img = imagen_subtitulo(cfg_g, textos, k, estilo_g)
            img.save(png)
            if k == 0 and anim_g in _PASOS_ANIM and dur > len(_PASOS_ANIM[anim_g][0]) * DUR_CUADRO_ANIM + 0.08:
                for im in cuadros_animacion(img, anim_g):       # la tarjeta entra con un pequeño movimiento
                    pa = tmp / f"sub_{contador:04d}.png"
                    contador += 1
                    im.save(pa)
                    entradas.append((pa, DUR_CUADRO_ANIM))
                    t += DUR_CUADRO_ANIM
                dur -= len(_PASOS_ANIM[anim_g][0]) * DUR_CUADRO_ANIM
            entradas.append((png, dur))
            t += dur
    if total > t:
        entradas.append((blank, total - t))
    lineas = [f"file '{png.name}'\nduration {dur:.3f}\n" for png, dur in entradas]
    lineas.append(f"file '{entradas[-1][0].name}'\n")
    lista = tmp / "subs.txt"
    lista.write_text("".join(lineas), encoding="utf-8")
    return lista


# ----------------------------------------------------------------------------
# Escenas: se cortan según lo que se dice
# ----------------------------------------------------------------------------
def planear_por_texto(cfg, palabras, total):
    """Cada escena cubre una frase (o varias cortas) del audio. Devuelve lista de dicts."""
    mn, mx, fin_min = cfg["escena_min"], cfg["escena_max"], cfg["final_segundos"]
    frases, act = [], []
    for w in palabras:
        act.append(w)
        ult = w[0][-1:]
        if ult in ".!?;:" or (ult == "," and len(act) >= 3):
            frases.append(act)
            act = []
    if act:
        frases.append(act)

    # juntar frases hasta alcanzar la duración mínima
    grupos, cur = [], []
    for i, f in enumerate(frases):
        cur = cur + f
        fin = frases[i + 1][0][1] if i + 1 < len(frases) else total
        ini = 0.0 if not grupos else cur[0][1]
        if fin - ini >= mn:
            grupos.append(cur)
            cur = []
    if cur:
        if grupos:
            grupos[-1] = grupos[-1] + cur
        else:
            grupos = [cur]

    escenas = []
    for g, pals in enumerate(grupos):
        t0 = 0.0 if g == 0 else pals[0][1]
        t1 = grupos[g + 1][0][1] if g + 1 < len(grupos) else total
        escenas.append({"t0": t0, "t1": t1, "pals": pals})

    # partir las escenas demasiado largas
    res = []
    for e in escenas:
        dur = e["t1"] - e["t0"]
        if dur <= mx or len(e["pals"]) < 2:
            res.append(e)
            continue
        k = min(math.ceil(dur / mx), len(e["pals"]))
        tam = len(e["pals"]) / k
        trozos = [e["pals"][int(round(i * tam)):int(round((i + 1) * tam))] for i in range(k)]
        trozos = [t for t in trozos if t]
        for j, t in enumerate(trozos):
            t0 = e["t0"] if j == 0 else t[0][1]
            t1 = e["t1"] if j == len(trozos) - 1 else trozos[j + 1][0][1]
            res.append({"t0": t0, "t1": t1, "pals": t})
    return cerrar_con_kit(res, fin_min, cfg["kit_final"])


def planear_sin_texto(cfg, total):
    """Sin .txt no se sabe qué se dice: escenas de duración al azar."""
    mn, mx = cfg["escena_min"], cfg["escena_max"]
    res, t = [], 0.0
    while total - t > mx + mn:
        d = random.uniform(mn, mx)
        res.append({"t0": t, "t1": t + d, "pals": []})
        t += d
    res.append({"t0": t, "t1": total, "pals": []})
    return cerrar_con_kit(res, cfg["final_segundos"], cfg["kit_final"])


def cerrar_con_kit(escenas, fin_min, activo=True):
    """La última escena siempre es del kit y dura al menos 'final_segundos' (si kit_final está activo)."""
    if not activo:
        return escenas
    if len(escenas) == 1 and escenas[0]["t1"] - escenas[0]["t0"] >= fin_min + 1.2:
        e = escenas[0]
        corte = e["t1"] - fin_min
        escenas = [{"t0": e["t0"], "t1": corte, "pals": []},
                   {"t0": corte, "t1": e["t1"], "pals": e["pals"]}]
    while len(escenas) >= 2 and escenas[-1]["t1"] - escenas[-1]["t0"] < fin_min:
        ant, ult = escenas[-2], escenas[-1]
        nuevo = max(ant["t0"] + 1.0, ult["t1"] - fin_min)
        if nuevo > ult["t1"] - 0.8:
            # entre las dos escenas no alcanza el tiempo: se juntan (antes salía una escena de duración negativa)
            ult["t0"] = ant["t0"]
            ult["pals"] = ant["pals"] + ult["pals"]
            del escenas[-2]
            continue
        ant["t1"] = nuevo
        ult["t0"] = nuevo
        break
    escenas[-1]["final"] = True
    return escenas


def tema_de(temas, textos):
    """Tema cuyas palabras clave aparecen más veces en el texto de la escena."""
    norm = [normalizar(t) for t in textos]
    puntajes = {}
    for tema, kws in temas.items():
        s = sum(1 for w in norm for k in kws if w.startswith(k))
        if s:
            puntajes[tema] = s
    if not puntajes:
        return None
    mejor = max(puntajes.values())
    return random.choice([t for t, s in puntajes.items() if s == mejor])


# ----------------------------------------------------------------------------
# Clips
# ----------------------------------------------------------------------------
_CLAVES = {}


def clave_archivo(p):
    """Identifica un archivo por su contenido (tamaño + primeros bytes), para que dos copias con otro nombre cuenten como el mismo clip."""
    k = _CLAVES.get(p)
    if k is None:
        try:
            with open(p, "rb") as f:
                k = (p.stat().st_size, hash(f.read(65536)))
        except OSError:
            k = (str(p),)
        _CLAVES[p] = k
    return k


class Pool:
    """Elige archivos al azar sin repetir (ni dentro del video, ni entre carpetas, ni con los videos recientes).
    `usados` es un conjunto COMPARTIDO por todas las carpetas del video, de claves de archivo."""

    def __init__(self, archivos, usados, ultimo=None):
        self.archivos = list(archivos)
        self.usados = usados
        self.ultimo = ultimo      # lista de un elemento compartida: el último clip elegido

    def elegir(self):
        libres = [p for p in self.archivos if clave_archivo(p) not in self.usados]
        if not libres:
            # se acabaron los clips nuevos: se vuelve a empezar solo con esta carpeta, sin repetir el clip anterior
            for p in self.archivos:
                self.usados.discard(clave_archivo(p))
            ant = self.ultimo[0] if self.ultimo else None
            libres = [p for p in self.archivos if ant is None or clave_archivo(p) != ant] or self.archivos
        p = random.choice(libres)
        self.usados.add(clave_archivo(p))
        if self.ultimo is not None:
            self.ultimo[0] = clave_archivo(p)
        return p


def listar_media(carpeta, recursivo):
    if not carpeta.exists():
        return []
    it = carpeta.rglob("*") if recursivo else carpeta.iterdir()
    return [p for p in it if p.is_file() and p.suffix.lower() in VIDEO_EXT | IMG_EXT]


MUSICA_ELEGIDA = None    # canción ya elegida (para cortar las escenas al ritmo)
PLAN_ESCENAS = None      # lo pone «escenas» antes de crear un video por escenas (escena por escena, sin voz)


class Material:
    def __init__(self, cfg, temas, recientes):
        d = cfg["dir"]
        self.d = d
        self.temas = temas
        usados = {clave_archivo(d / r) for r in recientes if (d / r).exists()}
        ultimo = [None]
        self._usados, self._ultimo = usados, ultimo
        self.pools = {}
        for tema in list(temas) + ["general"]:
            if tema == "kit":
                continue
            archivos = listar_media(d / "clips" / tema, True)
            if archivos:
                self.pools[tema] = Pool(archivos, usados, ultimo)
        self.todos = Pool(listar_media(d / "clips", True), usados, ultimo)
        kit = listar_media(d / "kit", False)
        self.kit = Pool(kit, usados, ultimo) if kit else None
        self.avisos = set()
        self.elegidos = []

    def para_escena(self, escena):
        textos = [p[0] for p in escena.get("pals", [])]
        if escena.get("archivo"):                           # escena con un archivo elegido a mano
            ruta_a = self.d / escena["archivo"]
            if ruta_a.exists():
                self.elegidos.append(ruta_a)
                return ruta_a, "contain" if str(escena["archivo"]).startswith("kit/") else "cover", "archivo"
            print(f"  Aviso: no encuentro {escena['archivo']}; se usó otro clip.")
        tema = "kit" if escena.get("final") else (escena.get("tema_fijo") or tema_de(self.temas, textos))
        if tema == "kit":
            if self.kit:
                media = self.kit.elegir()
                self.elegidos.append(media)
                return media, "contain", "kit"
            if "kit" not in self.avisos:
                print("  Aviso: la carpeta 'kit' está vacía; pon ahí tus capturas del producto.")
                self.avisos.add("kit")
            tema = None
        if tema and tema not in self.pools and escena.get("tema_fijo") and tema != "kit":      # carpeta de clips que no está en la lista de temas: se busca igual
            fs = listar_media(self.d / "clips" / tema, True)
            if fs:
                self.pools[tema] = Pool(fs, self._usados, self._ultimo)
        pool = self.pools.get(tema) if tema else None
        etiqueta = tema
        if not pool:
            if tema and tema not in self.avisos:
                print(f"  Aviso: no hay clips en la carpeta del tema '{tema}'; se usó un clip general.")
                self.avisos.add(tema)
            pool = self.pools.get("general") or self.todos
            etiqueta = "general"
        media = pool.elegir()
        self.elegidos.append(media)
        return media, "cover", etiqueta


def lista_transiciones(cfg):
    elegidas = [t for t in str(cfg.get("transiciones_permitidas", "")).split(",") if t.strip()]
    if elegidas:
        return [t.strip() for t in elegidas]
    estilo = str(cfg.get("transiciones", "dinamicas")).strip().lower()
    if estilo.startswith("suav"):
        return TRANS_SUAVES
    if estilo.startswith("mix"):
        return TRANS_DINAMICAS + TRANS_SUAVES
    return TRANS_DINAMICAS


def elegir_transicion(cfg, anterior=None):
    lista = lista_transiciones(cfg)
    opciones = [t for t in lista if t != anterior] or lista
    return random.choice(opciones)


def elegir_efecto(cfg, modo):
    """Movimiento del clip. Con todos los efectos activos el orden y las probabilidades son los de siempre."""
    permitidos = {e.strip() for e in str(cfg.get("efectos_clip", "")).split(",") if e.strip()}
    if modo == "contain":
        base = ["punch", "zoom_in"]
    else:
        base = ["punch", "zoom_in", "zoom_out", "pan_izq", "pan_der", "punch", "zoom_in"]
    lista = [e for e in base if e in permitidos]
    return random.choice(lista) if lista else "none"


def par(x):
    return int(x) // 2 * 2


def aplanar_si_transparente(cfg, media, salida):
    """Si el clip es una imagen con transparencia (PNG, WebP, GIF), la acomoda entera sobre el color de fondo del video:
    así lo transparente se ve como fondo y no negro o blanco. Devuelve (archivo, ¿se_aplanó?)."""
    try:
        im = Image.open(media)
        if im.mode == "P" and "transparency" in im.info:
            im = im.convert("RGBA")
        if im.mode not in ("RGBA", "LA") or im.getchannel("A").getextrema()[0] >= 255:
            return media, False
        im = im.convert("RGBA")
        W, mh = int(cfg["ancho"]), int(cfg["media_alto"])
        k = min(W / im.width, mh / im.height)
        im = im.resize((max(1, round(im.width * k)), max(1, round(im.height * k))), Image.LANCZOS)
        lienzo = Image.new("RGBA", (W, mh), ImageColor.getrgb(str(cfg.get("color_fondo") or "#000000"))[:3] + (255,))
        lienzo.alpha_composite(im, ((W - im.width) // 2, (mh - im.height) // 2))
        destino = Path(salida).with_name(Path(salida).stem + "_plano.png")
        lienzo.convert("RGB").save(destino)
        return destino, True
    except Exception:
        return media, False


def crear_segmento(cfg, media, dur, modo, efecto, oscuro, salida, ajuste=None):
    W, mh, fps = cfg["ancho"], cfg["media_alto"], cfg["fps"]
    if media.suffix.lower() in IMG_EXT:
        media, plano = aplanar_si_transparente(cfg, media, salida)
        if plano:
            modo = "cover"
    cmd = ["ffmpeg", "-y", "-v", "error"]
    if media.suffix.lower() in IMG_EXT:
        cmd += ["-loop", "1", "-framerate", str(fps), "-i", str(media)]
    else:
        mdur = duracion(media)
        ini_aj = float((ajuste or {}).get("ini") or 0)
        if ini_aj > 0 and mdur > ini_aj + dur:                 # la persona eligió desde qué segundo empieza este clip
            cmd += ["-ss", f"{ini_aj:.2f}", "-i", str(media)]
        elif mdur > dur + 0.4:
            cmd += ["-ss", f"{random.uniform(0, mdur - dur - 0.3):.2f}", "-i", str(media)]
        else:
            cmd += ["-stream_loop", "-1", "-i", str(media)]

    D = f"{dur:.3f}"
    if modo == "contain":
        base = (f"[0:v]fps={fps},split[a][b];"
                f"[a]scale={W}:{mh}:force_original_aspect_ratio=increase,crop={W}:{mh},boxblur=25:5[bg];"
                f"[b]scale={W}:{mh}:force_original_aspect_ratio=decrease[fg];"
                f"[bg][fg]overlay=(W-w)/2:(H-h)/2,setsar=1")
    else:
        base = (f"[0:v]fps={fps},scale={W}:{mh}:force_original_aspect_ratio=increase,"
                f"crop={W}:{mh},setsar=1")

    if efecto in ("pan_izq", "pan_der") and modo != "contain":
        BW, BH = par(W * 1.2), par(mh * 1.2)
        px = f"t/{D}" if efecto == "pan_der" else f"(1-t/{D})"
        base = (f"[0:v]fps={fps},scale={BW}:{BH}:force_original_aspect_ratio=increase,"
                f"crop={BW}:{BH},setsar=1,crop={W}:{mh}:x='(iw-ow)*{px}':y='(ih-oh)/2'")
    elif efecto in ("zoom_in", "zoom_out", "punch"):
        # el factor siempre queda entre 1 y Z, para que la imagen nunca sea mas chica que el recuadro
        Z = max(1.05, float(cfg.get("zoom_max", 1.25)))
        if efecto == "zoom_in":
            k = f"min({Z},1+({Z}-1)*t/{D})"
        elif efecto == "zoom_out":
            k = f"max(1,{Z}-({Z}-1)*t/{D})"
        else:  # "punch": llega acercado y se asienta rapido, luego sigue un zoom lento
            k = f"min({Z},1+({Z}-1)*0.7*max(0,1-t/0.4)+0.06*t/{D})"
        base += (f",scale=w='2*trunc({W}*{k}/2)':h='2*trunc({mh}*{k}/2)':eval=frame,"
                 f"crop={W}:{mh}")
    color = ""
    if cfg["variar_color"]:
        color = random.choice(["", ",eq=contrast=1.06:saturation=1.12",
                               ",eq=contrast=1.04:saturation=1.2:brightness=0.02",
                               ",eq=contrast=1.08:saturation=0.95"])
    # Filtro oscuro (capa negra con la opacidad indicada) solo en los clips, no en las imágenes del kit
    sombra = ""
    if oscuro and modo != "contain":
        f = 1.0 - oscuro
        sombra = f",colorchannelmixer=rr={f:.3f}:gg={f:.3f}:bb={f:.3f}"
    if ajuste and (ajuste.get("espejo") or ajuste.get("giro")):       # girar y/o espejo del clip (antes de recortar y ampliar)
        giro = int(ajuste.get("giro") or 0)
        pre = {90: "transpose=1,", 180: "hflip,vflip,", 270: "transpose=2,"}.get(giro, "") + ("hflip," if ajuste.get("espejo") else "")
        base = base.replace("[0:v]fps=", "[0:v]" + pre + "fps=", 1)
    filtro = base + color + sombra + ",format=yuv420p[v]"
    cmd += ["-filter_complex", filtro, "-map", "[v]", "-t", D, "-r", str(fps),
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-an", str(salida)]
    run(cmd)


# ----------------------------------------------------------------------------
# Render de un video
# ----------------------------------------------------------------------------
def gancho_por_defecto(texto):
    """Primera frase completa (sin puntos suspensivos). Si es muy larga, corta en una coma o en una palabra."""
    if not texto:
        return ""
    primera = re.split(r"(?<=[.!?])\s", texto.strip())[0].strip()
    if len(primera) > 90:
        corte = primera.rfind(",", 30, 90)
        if corte == -1:
            corte = primera.rfind(" ", 30, 90)
        primera = primera[:corte] if corte != -1 else primera[:90]
    return primera.rstrip(" ,;:")


RE_MARCA_POS = re.compile(r"\(\s*([*/])\s*(\d{1,2})\s*\)|(?<![\w/*])([*/])(\d{1,2})(?![\w/*])")
_CENTINELA = re.compile(r"^\x00([*/])(\d+)\x00$")


def extraer_burbujas(texto, con_pos=False):
    """Quita « » y { } del texto. Devuelve (texto_limpio, [(indice_ini, indice_fin, frase, en_silencio)]).
    «frase»  = burbuja que SI se dice en el audio (sale mientras se dice).
    {frase}  = burbuja que NO se dice: sale justo despues de la palabra anterior del texto.
    Si la frase empieza con 'Cliente:' es un mensaje del cliente; esa palabra NO se dice ni se subtitula.
    Marcas de posicion *1 y /2 (tambien valen con parentesis): indican DONDE sale una burbuja hecha en el editor (* = Persona 1, / = Persona 2,
    el numero es el orden de sus mensajes). No se dicen ni se subtitulan. Con con_pos=True se devuelven tambien:
    [(lado, numero, indice_de_la_palabra_anterior)]."""
    texto = RE_MARCA_POS.sub(lambda m: f" \x00{m.group(1) or m.group(3)}{m.group(2) or m.group(4)}\x00 ", texto)
    tokens, marcas, pos, ini, frase, cliente, silencio = [], [], [], None, [], False, False
    for tok in texto.split():
        c = _CENTINELA.match(tok)
        if c:
            pos.append((c.group(1), int(c.group(2)), len(tokens) - 1))
            continue
        if ini is None and ("«" in tok or "{" in tok):
            silencio = "{" in tok and "«" not in tok
            ini, frase, cliente = len(tokens), [], False
        limpio = tok.translate({ord(c): None for c in "«»{}"})
        if ini is not None and not frase and not cliente and limpio.lower() == "cliente:":
            cliente = True
            continue
        if limpio:
            if not silencio or ini is None:
                tokens.append(limpio)
            if ini is not None:
                frase.append(limpio)
        if ini is not None and (("}" in tok) if silencio else ("»" in tok)):
            if frase:
                texto_b = ("Cliente: " if cliente else "") + " ".join(frase)
                if silencio:
                    marcas.append((len(tokens) - 1, len(tokens) - 1, texto_b, True))
                else:
                    marcas.append((ini, len(tokens) - 1, texto_b, False))
            ini = None
    if con_pos:
        return " ".join(tokens), marcas, pos
    return " ".join(tokens), marcas


def _es_cliente(frase):
    m = re.match(r"^\s*cliente\s*:\s*(.+)$", frase, re.I | re.S)
    return (True, m.group(1).strip()) if m else (False, frase)


def _medidas_burbuja(cfg, frase):
    cliente, texto = _es_cliente(frase)
    fuente = gv.cargar_fuente(cfg, int(cfg["burbuja_tam"]), "burbuja")
    lineas = gv.envolver(fuente, texto, int(780 / catalogo.FORMAS_BURBUJA[_forma(cfg, cliente)][2]))
    ancho_txt = max(fuente.getlength(l) for l in lineas)
    pad, alto_linea = 40, int(round(int(cfg["burbuja_tam"]) * 76 / 62))
    bw = int(max(ancho_txt, 260) + 2 * pad)
    bh = int(len(lineas) * alto_linea + 2 * pad + 40)
    fx, fy = catalogo.FORMAS_BURBUJA[_forma(cfg, cliente)][2:4]
    bw, bh = int(bw * fx), int(bh * fy)       # los globos ovalados necesitan más aire alrededor del texto
    return cliente, texto, fuente, lineas, pad, alto_linea, bw, bh


def _forma(cfg, cliente=False):
    """Forma de la burbuja: la de su lado (tuya o del cliente) si la hay; si no, la general."""
    f = str(cfg.get("burbuja_forma_cliente" if cliente else "burbuja_forma_yo") or cfg.get("burbuja_forma") or "whatsapp")
    return f if f in catalogo.FORMAS_BURBUJA else "whatsapp"


def _dibujar_forma(d, caja, forma, cola, relleno, desp=(0, 0), cliente=False):
    """Dibuja la burbuja (cuerpo y cola) en la forma elegida. 'cola' es el triángulo clásico."""
    x0, y0, x1, y1 = caja
    ox, oy = desp
    radio = catalogo.FORMAS_BURBUJA[forma][4]
    tipo = catalogo.FORMAS_BURBUJA[forma][5]
    radio = min(radio, (y1 - y0) // 2, (x1 - x0) // 2)
    if tipo == "pico":
        d.polygon([(a + ox, b + oy) for a, b in cola], fill=relleno)
    elif tipo == "pico_abajo":
        bx = (x0 + 110) if cliente else (x1 - 110)
        sg = -1 if cliente else 1
        d.polygon([(bx - 45 * sg + ox, y1 - 20 + oy), (bx + 10 * sg + ox, y1 - 20 + oy), (bx + 55 * sg + ox, y1 + 55 + oy)], fill=relleno)
    elif tipo == "bolitas":
        bx = (x0 + 110) if cliente else (x1 - 110)
        for k, r in enumerate((20, 13, 8)):
            cx_ = bx + (-20 if cliente else 20) * k
            cy_ = y1 + 14 + k * 24
            d.ellipse((cx_ - r + ox, cy_ - r + oy, cx_ + r + ox, cy_ + r + oy), fill=relleno)
    d.rounded_rectangle((x0 + ox, y0 + oy, x1 + ox, y1 + oy), radius=radio, fill=relleno)


def catalogo_color(valor):
    """El color si es valido; '' si esta vacio o no se entiende (asi se usa el del estilo general)."""
    v = str(valor or "").strip()
    try:
        ImageColor.getrgb(v)
        return v
    except ValueError:
        return ""



# ----------------------------------------------------------------------------
# Capas encima del video (logos, PNG, GIF y videos con transparencia)
# ----------------------------------------------------------------------------
CAPA_POSICIONES = ("arriba_izq", "arriba_centro", "arriba_der", "medio_izq", "centro", "medio_der", "abajo_izq", "abajo_centro", "abajo_der")
CAPA_ESTATICAS = {".png", ".jpg", ".jpeg", ".jfif", ".webp", ".bmp"}


def capa_defecto(archivo):
    return {"archivo": archivo, "activa": True, "pos": "abajo_der", "ancho": 25, "dx": 0, "dy": 0, "desde": 0.0, "hasta": 0.0, "opacidad": 100}


def limpiar_capa(c):
    """Deja una capa con valores válidos (se usa al guardar y al leer)."""
    def num(v, lo, hi, d):
        try:
            return max(lo, min(hi, float(v)))
        except (TypeError, ValueError):
            return d
    r = capa_defecto(Path(str(c.get("archivo", ""))).name)
    r["activa"] = bool(c.get("activa", True))
    r["pos"] = c.get("pos") if c.get("pos") in CAPA_POSICIONES else r["pos"]
    r["ancho"] = int(num(c.get("ancho"), 3, 100, 25))
    r["dx"], r["dy"] = int(num(c.get("dx"), -2000, 2000, 0)), int(num(c.get("dy"), -4000, 4000, 0))
    r["desde"], r["hasta"] = round(num(c.get("desde"), 0, 3600, 0.0), 2), round(num(c.get("hasta"), 0, 3600, 0.0), 2)
    r["opacidad"] = int(num(c.get("opacidad"), 5, 100, 100))
    return r


def leer_capas(carpeta, solo_activas=True):
    """Las capas del producto que existen de verdad: [{..., 'ruta': Path}]."""
    if not carpeta:
        return []
    carpeta = Path(carpeta)
    try:
        lista = json.loads((carpeta / "capas.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        lista = []
    res = []
    for c in lista if isinstance(lista, list) else []:
        if not isinstance(c, dict):
            continue
        c = limpiar_capa(c)
        p = carpeta / "capas" / c["archivo"]
        if p.is_file() and (c["activa"] or not solo_activas):
            res.append(dict(c, ruta=p))
    return res


def miniatura_capa(ruta):
    """Imagen (RGBA) de la capa para la vista previa: la propia imagen, o el primer cuadro de un video/GIF."""
    ruta = Path(ruta)
    try:
        if ruta.suffix.lower() in CAPA_ESTATICAS | {".gif"}:
            return Image.open(ruta).convert("RGBA")
        mini = ruta.with_name("_mini_" + ruta.stem + ".png")
        return Image.open(mini).convert("RGBA") if mini.is_file() else None
    except Exception:
        return None


def hacer_miniatura_video(ruta):
    """Guarda el primer cuadro (con transparencia) de un video para mostrarlo en la vista previa."""
    ruta = Path(ruta)
    mini = ruta.with_name("_mini_" + ruta.stem + ".png")
    cmd = ["ffmpeg", "-y", "-v", "error"] + (["-c:v", "libvpx-vp9"] if ruta.suffix.lower() == ".webm" else []) + \
          ["-i", str(ruta), "-frames:v", "1", "-pix_fmt", "rgba", str(mini)]
    try:
        subprocess.run(cmd, capture_output=True, stdin=subprocess.DEVNULL, creationflags=gv.SIN_VENTANA, timeout=60)
    except Exception:
        pass
    return mini if mini.is_file() else None


def posicion_capa(W, H, w, h, pos, dx=0, dy=0):
    """Esquina superior izquierda (en píxeles) de una capa de w×h dentro de un video de W×H."""
    m = int(W * 0.04)
    col, fila = {"izq": 0, "centro": 1, "der": 2}, {"arriba": 0, "medio": 1, "abajo": 2}
    f, _, c = pos.partition("_")
    if pos == "centro":
        f, c = "medio", "centro"
    x = [m, (W - w) // 2, W - w - m][col.get(c, 2)] + int(dx)
    y = [m, (H - h) // 2, H - h - m][fila.get(f, 2)] + int(dy)
    return x, y


def _expr_capa(pos, dx, dy, m):
    f, _, c = pos.partition("_")
    if pos == "centro":
        f, c = "medio", "centro"
    x = {"izq": f"{m}", "centro": "(W-w)/2", "der": f"W-w-{m}"}.get(c, f"W-w-{m}")
    y = {"arriba": f"{m}", "medio": "(H-h)/2", "abajo": f"H-h-{m}"}.get(f, f"H-h-{m}")
    return f"{x}+({int(dx)})", f"{y}+({int(dy)})"


def args_entrada_capa(ruta, fps):
    """Argumentos de ffmpeg para leer una capa: las imágenes fijas se repiten, y lo animado se repite en bucle."""
    ext = Path(ruta).suffix.lower()
    if ext in CAPA_ESTATICAS:
        return ["-loop", "1", "-framerate", str(fps), "-i", str(ruta)]
    return ["-stream_loop", "-1"] + (["-c:v", "libvpx-vp9"] if ext == ".webm" else []) + ["-i", str(ruta)]


def filtros_capa(idx, ruta, c, W, H, total, ultimo_v):
    """Líneas de filtro para montar una capa encima del video. Devuelve (lineas, nombre_de_salida)."""
    ext = Path(ruta).suffix.lower()
    ini = float(c["desde"])
    fin = float(c["hasta"]) if float(c["hasta"]) > ini else total + 1
    cadena = "format=rgba"
    if ext not in CAPA_ESTATICAS:
        cadena += f",setpts=PTS-STARTPTS+{ini:.3f}/TB"         # la animación empieza justo cuando aparece
    cadena += f",scale={max(16, int(W * c['ancho'] / 100) // 2 * 2)}:-2:flags=lanczos"
    if int(c["opacidad"]) < 100:
        cadena += f",colorchannelmixer=aa={int(c['opacidad']) / 100:.2f}"
    ex, ey = _expr_capa(c["pos"], c["dx"], c["dy"], int(W * 0.04))
    sal = f"cap{idx}"
    return [f"[{idx}:v]{cadena}[cp{idx}]",
            f"[{ultimo_v}][cp{idx}]overlay=x='{ex}':y='{ey}':enable='between(t,{ini:.3f},{fin:.3f})':eof_action=pass[{sal}]"], sal


def cfg_burbuja(cfg, estilo=None):
    """Copia de los ajustes con el estilo propio de una burbuja (fondo, color de letra, tipo de letra)."""
    if not estilo:
        return cfg
    c2 = dict(cfg)
    if estilo.get("fondo"):
        c2["color_burbuja_yo"] = c2["color_burbuja_cliente"] = estilo["fondo"]
    if estilo.get("color_texto"):
        c2["color_burbuja_texto"] = estilo["color_texto"]
    if estilo.get("fuente"):
        c2["fuente_burbuja"] = estilo["fuente"]
    if estilo.get("tam"):
        c2["burbuja_tam"] = int(estilo["tam"])
    return c2


def ajustar_item_burbuja(cfg, it):
    """Aplica a una burbuja lo que tiene su lado (tú o el cliente): posición y tamaño propios, definidos en Estilo."""
    cliente = _es_cliente(it["frase"])[0]
    pre = "burbuja_cliente_" if cliente else "burbuja_yo_"
    it["mover_x"] = int(it.get("mover_x", 0)) + int(float(cfg.get(pre + "x") or 0))
    if not cliente:    # la del cliente ya tiene su propio ajuste vertical (burbuja_cliente_ajuste)
        it["mover"] = int(it.get("mover", 0)) + int(float(cfg.get("burbuja_yo_y") or 0))
    esc = int(float(cfg.get(pre + "escala") or 100))
    if esc != 100:
        est = dict(it.get("estilo") or {})
        est["escala"] = max(40, min(220, esc))
        it["estilo"] = est
    return it


def alto_burbuja(cfg, frase, estilo=None):
    alto = _medidas_burbuja(cfg_burbuja(cfg, estilo), frase)[7]
    return int(alto * (estilo or {}).get("escala", 100) / 100)


def leer_burbujas_manuales(audio):
    """Burbujas hechas en el editor del programa (archivo 01.burbujas.json junto al audio).
    Devuelve None si el guion no tiene ese archivo (entonces se usan las marcas del texto)."""
    f = audio.with_suffix(".burbujas.json")
    if not f.exists():
        return None
    try:
        datos = json.loads(f.read_text(encoding="utf-8"))
    except Exception:
        return None
    return datos.get("burbujas", []) if isinstance(datos, dict) else None


def leer_estilo_titulo(audio):
    """Posicion y estilo propios del titulo de un guion (archivo 01.titulo.json junto al audio). Vacio si no hay."""
    f = audio.with_suffix(".titulo.json")
    try:
        d = json.loads(f.read_text(encoding="utf-8"))
        return d if isinstance(d, dict) else {}
    except Exception:
        return {}


def aplicar_estilo_titulo(cfg, est):
    """Copia de cfg con el estilo propio del titulo. Devuelve (cfg2, desplazamiento_x)."""
    est = est or {}
    c2 = dict(cfg)
    c2["titulo_y"] = int(cfg["titulo_y"]) + int(float(est.get("y", 0) or 0))
    if int(float(est.get("tam", 0) or 0)) > 0:
        c2["tam_texto_arriba"] = int(float(est["tam"]))
    if catalogo_color(est.get("color")):
        c2["color_texto"] = est["color"]
    if str(est.get("fuente") or "").strip():
        c2["fuente_titulo"] = str(est["fuente"]).strip()
    if est.get("trazo") not in (None, ""):
        c2["trazo_titulo"] = int(float(est["trazo"]))
    return c2, int(float(est.get("x", 0) or 0))


def leer_grupo_burbujas(audio):
    """Desplazamiento (x, y) de TODAS las burbujas de un guion, como conjunto (viene del editor)."""
    f = audio.with_suffix(".burbujas.json")
    try:
        d = json.loads(f.read_text(encoding="utf-8")).get("grupo", {})
        return int(float(d.get("x", 0))), int(float(d.get("y", 0)))
    except Exception:
        return 0, 0


def colocar_burbujas(cfg, items):
    """items: [{'frase', 't0', 't1', 'mover', 'estilo'}] en orden de aparicion. Devuelve la altura (borde de abajo)
    de cada burbuja. Las que coinciden en el tiempo se apilan como en un chat: la mas nueva abajo y las
    anteriores arriba, sin encimarse. Si el grupo no cabe antes del borde de arriba, se achica la letra
    de ese grupo (item['estilo']['tam']) hasta que quepa."""
    base = int(cfg["burbuja_y"])
    gap = int(cfg["burbuja_espacio"])
    tope = int(cfg["zona_segura_arriba"])
    n = len(items)

    def juntas(a, b):
        return items[a]["t0"] < items[b]["t1"] and items[b]["t0"] < items[a]["t1"]

    def apilar(idx):
        """Alturas del grupo idx (indices en orden de aparicion) sin ajustes manuales."""
        alto = {k: alto_burbuja(cfg, items[k]["frase"], items[k].get("estilo")) for k in idx}
        ys = {}
        for k in reversed(idx):
            y = base
            for j in idx:
                if j > k and juntas(k, j):
                    y = min(y, ys[j] - alto[j] - gap)
            ys[k] = y
        return ys, alto

    # grupos de burbujas encadenadas en el tiempo
    grupos, actual, fin = [], [], -1.0
    for k in range(n):
        if actual and items[k]["t0"] >= fin:
            grupos.append(actual); actual = []
        actual.append(k)
        fin = max(fin, items[k]["t1"]) if len(actual) > 1 else items[k]["t1"]
    if actual:
        grupos.append(actual)
    tam0 = int(cfg["burbuja_tam"])
    ys_final = [0] * n
    for idx in grupos:
        for factor in (1.0, 0.9, 0.8, 0.7, 0.6, 0.5):
            for k in idx:
                est = dict(items[k].get("estilo") or {})
                if factor < 1.0:
                    est["tam"] = max(30, int(tam0 * factor))
                else:
                    est.pop("tam", None)
                items[k]["estilo"] = est
            ys, alto = apilar(idx)
            if min(ys[k] - alto[k] for k in idx) >= tope:
                break
        for k in idx:
            extra = int(items[k].get("mover", 0))
            if _es_cliente(items[k]["frase"])[0]:
                extra += int(cfg["burbuja_cliente_ajuste"])
            ys_final[k] = ys[k] + extra
    return ys_final


def crear_burbuja(cfg, frase, destino, y1=None, estilo=None, dx=0):
    """Mensaje de WhatsApp: verde a la derecha (tú) o blanco a la izquierda (si la frase empieza con 'Cliente:').
    estilo (opcional): fondo, color_texto, fuente y brillo propios de esta burbuja."""
    brillo = bool(estilo and estilo.get("brillo"))
    cfg = cfg_burbuja(cfg, estilo)
    W, H = cfg["ancho"], cfg["alto"]
    cliente, texto, fuente, lineas, pad, alto_linea, bw, bh = _medidas_burbuja(cfg, frase)
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    chica = gv.cargar_fuente(cfg, 32, "burbuja")
    y1 = int(cfg["burbuja_y"]) if y1 is None else int(y1)
    y0 = y1 - bh
    col = min(W, 1080)             # en formato horizontal el chat se queda en una columna centrada
    cx = (W - col) // 2 + int(dx)
    if cliente:
        x0 = cx + 70
        x1 = x0 + bw
        fondo = ImageColor.getrgb(cfg["color_burbuja_cliente"])[:3] + (255,)
        cola = [(x0 + 40, y0 + 2), (x0 - 26, y0 - 12), (x0 + 6, y0 + 50)]
    else:
        x1 = cx + col - 70
        x0 = x1 - bw
        fondo = ImageColor.getrgb(cfg["color_burbuja_yo"])[:3] + (255,)
        cola = [(x1 - 40, y0 + 2), (x1 + 26, y0 - 12), (x1 - 6, y0 + 50)]
    forma = _forma(cfg, cliente)
    fx, fy = catalogo.FORMAS_BURBUJA[forma][2:4]
    ex, ey = int(bw * (1 - 1 / fx) / 2), int(bh * (1 - 1 / fy) / 2)    # aire extra alrededor del texto en formas ovaladas
    _dibujar_forma(d, (x0, y0, x1, y1), forma, cola, (0, 0, 0, 90), (5, 8), cliente)
    _dibujar_forma(d, (x0, y0, x1, y1), forma, cola, fondo, (0, 0), cliente)
    if brillo:   # reflejo suave en la mitad de arriba, como un botón con brillo
        mascara = Image.new("L", (W, H), 0)
        _dibujar_forma(ImageDraw.Draw(mascara), (x0, y0, x1, y1), forma, cola, 255, (0, 0), cliente)
        luz = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        dl = ImageDraw.Draw(luz)
        alto_luz = max(8, int((y1 - y0) * 0.55))
        for k in range(alto_luz):
            dl.line([(x0, y0 + k), (x1, y0 + k)], fill=(255, 255, 255, int(120 * (1 - k / alto_luz) ** 1.5)))
        dl.line([(x0 + 30, y0 + 5), (x1 - 30, y0 + 5)], fill=(255, 255, 255, 150), width=3)
        luz.putalpha(Image.composite(luz.getchannel("A"), Image.new("L", (W, H), 0), mascara))
        img.alpha_composite(luz)
        d = ImageDraw.Draw(img)
    y = y0 + pad - 8 + ey + (0 if forma in ("whatsapp", "cuadro", "cuadro_liso") else 20)
    for l in lineas:
        d.text((x0 + pad + ex, y), l, font=fuente, fill=ImageColor.getrgb(cfg["color_burbuja_texto"])[:3] + (255,))
        y += alto_linea
    hora = "10:42"
    if forma not in ("whatsapp", "cuadro", "cuadro_liso"):
        pass                    # las formas redondas no llevan hora ni palomitas (quedarían fuera de la curva)
    elif cliente:
        d.text((x1 - pad - chica.getlength(hora), y1 - pad - 16), hora, font=chica, fill=(120, 130, 125, 255))
    else:
        hx = x1 - pad - 74
        d.text((hx - chica.getlength(hora) - 10, y1 - pad - 16), hora, font=chica, fill=(110, 130, 110, 255))
        tx, ty = x1 - pad - 54, y1 - pad - 2
        azul = (53, 159, 224, 255)
        for dx in (0, 17):
            d.line([(tx + dx, ty), (tx + dx + 9, ty + 11), (tx + dx + 28, ty - 15)], fill=azul, width=5)
    esc = float((estilo or {}).get("escala") or 100) / 100
    if abs(esc - 1) > 0.01:      # tamaño propio: se agranda o achica toda la burbuja igual (sin deformarla), fija en su esquina de abajo
        ax, ay = (x0 if cliente else x1), y1
        caja = img.getbbox()
        if caja:
            rec = img.crop(caja)
            rec = rec.resize((max(1, round(rec.width * esc)), max(1, round(rec.height * esc))), Image.LANCZOS)
            nuevo = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            nuevo.paste(rec, (round(ax + (caja[0] - ax) * esc), round(ay + (caja[1] - ay) * esc)), rec)
            img = nuevo
    img.save(destino)


def _zona_lados(cfg, pref, z, W):
    """Aplica «mover a los lados» y «ancho» (ajustes <pref>_x y <pref>_ancho) a una zona (x0, y0, x1, y1)."""
    x = int(float(cfg.get(pref + "_x", 0) or 0))
    ancho = int(float(cfg.get(pref + "_ancho", 0) or 0))
    x0, x1 = z[0], z[2]
    if ancho > 0:
        cx = (x0 + x1) / 2
        x0, x1 = cx - ancho / 2, cx + ancho / 2
    return (int(x0 + x), z[1], int(x1 + x), z[3])


def crear_capas(cfg, gancho, cta, tmp, dx_titulo=0):
    """Crea 3 imágenes: base (usuario), título y frase de abajo (las dos últimas con su propio horario)."""
    W, H = cfg["ancho"], cfg["alto"]
    m = 60
    completa = es_si(cfg["pantalla_completa"])
    if completa:
        z_titulo = (m, int(cfg["titulo_y"]), W - m, int(cfg["titulo_y"]) + int(cfg["titulo_alto"]))
        z_cta = (m, int(cfg["cta_y"]), W - m, int(cfg["cta_y"]) + int(cfg["cta_alto"]))
    else:
        z_titulo = (m, cfg["zona_segura_arriba"], W - m, cfg["media_y"] - 30)
        z_cta = (m, cfg["media_y"] + cfg["media_alto"] + 30, W - m, H - cfg["zona_segura_abajo"])
    z_titulo = (z_titulo[0] + dx_titulo, z_titulo[1], z_titulo[2] + dx_titulo, z_titulo[3])
    z_titulo = _zona_lados(cfg, "titulo", z_titulo, W)
    z_cta = _zona_lados(cfg, "cta", z_cta, W)
    out = {}
    for nombre, texto, zona, tam, color, trazo in (
            ("titulo", gancho, z_titulo, cfg["tam_texto_arriba"], cfg["color_texto"], cfg["trazo_titulo"]),
            ("cta", cta, z_cta, cfg["tam_cta"], cfg["color_cta"], cfg["trazo_cta"])):
        img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        if texto:
            gv.dibujar_en_zona(ImageDraw.Draw(img), cfg, texto, zona, tam, color, trazo=int(trazo),
                               elemento=nombre, trazo_color=cfg["color_trazo"])
        ruta_png = tmp / f"capa_{nombre}.png"
        img.save(ruta_png)
        out[nombre] = ruta_png
    base = tmp / "capa_base.png"
    Image.new("RGBA", (W, H), (0, 0, 0, 0)).save(base)
    poner_usuario(cfg, base)
    out["base"] = base
    return out


MARCA_FINAL_SEGUNDOS = 3.0      # cuánto dura la pantalla final con la marca grande (plan gratis)


def _logo_marca():
    """El logo de Vibovapp (con fondo transparente) o None si no se encuentra el archivo."""
    try:
        ruta = Path(__file__).resolve().parent / "web" / "logo.png"
        return Image.open(ruta).convert("RGBA") if ruta.exists() else None
    except Exception:
        return None


def _etiqueta_marca(cfg, tam):
    """Dibuja «Hecho con» + el logo de Vibovapp dentro de una píldora oscura. `tam` = alto aproximado de las letras."""
    import planes
    fuente = gv.cargar_fuente(cfg, tam, "subs")
    prefijo = "Hecho con"
    logo = _logo_marca()
    box = ImageDraw.Draw(Image.new("RGBA", (1, 1))).textbbox((0, 0), prefijo, font=fuente)
    tw, th = box[2] - box[0], box[3] - box[1]
    if logo is not None:
        logo = logo.crop(logo.getbbox() or (0, 0, logo.width, logo.height))
        lh = max(8, int(tam * 1.5))
        lw = max(8, int(logo.width * lh / logo.height))
        logo = logo.resize((lw, lh), Image.LANCZOS)
        contenido_w, contenido_h, hueco = tw + 14 + lw, max(th, lh), 14
    else:                                           # sin el archivo del logo: se escribe el nombre
        prefijo = planes.TEXTO_MARCA
        box = ImageDraw.Draw(Image.new("RGBA", (1, 1))).textbbox((0, 0), prefijo, font=fuente)
        tw, th = box[2] - box[0], box[3] - box[1]
        contenido_w, contenido_h, hueco = tw, th, 0
    mx, my = int(tam * 0.9), int(tam * 0.55)
    w, h = contenido_w + 2 * mx, contenido_h + 2 * my
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((0, 0, w - 1, h - 1), radius=h // 2, fill=(0, 0, 0, 165))
    d.text((mx - box[0], my + (contenido_h - th) // 2 - box[1]), prefijo, font=fuente, fill=(255, 255, 255, 240))
    if logo is not None:
        img.alpha_composite(logo, (mx + tw + hueco, my + (contenido_h - logo.height) // 2))
    return img


def crear_marca_agua(cfg, tmp):
    """Etiqueta pequeña «Hecho con» + logo de Vibovapp para el plan gratis (se ve durante todo el video)."""
    W = int(cfg["ancho"])
    img = _etiqueta_marca(cfg, max(20, int(W * 0.032)))
    ruta = Path(tmp) / "marca_agua.png"
    img.save(ruta)
    return ruta


def crear_marca_final(cfg, tmp):
    """Pantalla final del plan gratis: la imagen se oscurece un poco y aparece «Hecho con» + el logo en grande, al centro."""
    W, H = int(cfg["ancho"]), int(cfg["alto"])
    img = Image.new("RGBA", (W, H), (0, 0, 0, 120))
    tam = max(24, int(min(W, H) * 0.06))
    et = _etiqueta_marca(cfg, tam)
    if et.width > W * 0.86:                              # que quepa en pantallas angostas
        r = W * 0.86 / et.width
        et = et.resize((int(et.width * r), int(et.height * r)), Image.LANCZOS)
    img.alpha_composite(et, ((W - et.width) // 2, (H - et.height) // 2))
    ruta = Path(tmp) / "marca_final.png"
    img.save(ruta)
    return ruta


def renderizar(cfg, audio, salida, material):
    W, H, fps, my = cfg["ancho"], cfg["alto"], cfg["fps"], cfg["media_y"]
    tr = cfg["transicion"]
    cola = cfg.get("cola_segundos", 0.6)
    gancho, texto = leer_texto(audio)
    texto, marcas, marcas_pos = extraer_burbujas(texto, con_pos=True)
    manuales = leer_burbujas_manuales(audio)
    if manuales is not None or not es_si(cfg["burbujas"]):
        marcas = []
    total = duracion(audio) + cola
    gancho = gancho or gancho_por_defecto(texto)

    paso(3)
    palabras = palabras_con_tiempos(cfg, audio, texto, total)
    if palabras is None:
        if audio.stem == "sin_guion":
            print("  Video sin guion: clips al azar y música de fondo (sin voz ni subtítulos).")
        else:
            print("  Aviso: este guion no tiene .txt; sin subtítulos y con imágenes al azar.")
        plan_e = PLAN_ESCENAS if audio.stem == "sin_guion" else None
        if plan_e:
            escenas = [dict(e) for e in plan_e["escenas"]]
            escenas[-1]["t1"] = total
            print(f"  Video por escenas: {len(escenas)} escenas.")
        else:
            escenas = planear_sin_texto(cfg, total)
    elif PLAN_ESCENAS and PLAN_ESCENAS.get("con_voz"):
        k = total / max(0.1, PLAN_ESCENAS["total"])          # las escenas de la plantilla se estiran para durar lo que dura la voz
        escenas = [dict(e, t0=e["t0"] * k, t1=e["t1"] * k) for e in PLAN_ESCENAS["escenas"]]
        escenas[-1]["t1"] = total
        print(f"  Escenas de la plantilla sobre la voz: {len(escenas)} escenas (x{k:.2f}).")
    else:
        escenas = planear_por_texto(cfg, palabras, total)
    n = len(escenas)
    durs = [e["t1"] - e["t0"] for e in escenas]
    lo, hi = sorted((cfg["oscurecer_min"], cfg["oscurecer_max"]))
    oscuro = random.uniform(lo, hi) / 100.0
    print(f"  {n} escenas, oscurecido {oscuro * 100:.0f}%, audio {total - cola:.1f}s")

    paso(4)
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        segmentos = []
        for i, (e, d) in enumerate(zip(escenas, durs)):
            if CANCELAR.is_set():
                raise Cancelado()
            media, modo, etiqueta = material.para_escena(e)
            efecto = elegir_efecto(cfg, modo)
            # cada segmento dura de más lo que se solapa con las transiciones vecinas
            extra = (tr / 2 if i > 0 else 0) + (tr / 2 if i < n - 1 else 0)
            seg = tmp / f"seg_{i:03d}.mp4"
            fragmento = " ".join(p[0] for p in e.get("pals", []))[:48]
            print(f"  Escena {i + 1}/{n} [{etiqueta}] {media.name} ({d:.1f}s)  «{fragmento}»")
            crear_segmento(cfg, media, d + extra, modo, efecto, oscuro, seg, e.get("ajuste"))
            segmentos.append(seg)

        paso(5)
        cfg_t, dx_t = aplicar_estilo_titulo(cfg, leer_estilo_titulo(audio))
        capas = crear_capas(cfg_t, gancho, cfg["cta"], tmp, dx_t)
        burbujas = []
        items = []
        # todo lo visual de las burbujas viene de Estilo (igual para todos los guiones)
        _e, _s = str(cfg.get("burbuja_entrada") or ""), str(cfg.get("burbuja_salida") or "")
        ent_g, sal_g = ("" if _e in ("", "normal") else _e), ("" if _s in ("", "normal") else _s)
        son_g = str(cfg.get("burbuja_sonido") or "").strip()
        est_g = {"brillo": True} if es_si(cfg.get("burbuja_brillo", False)) else None
        dx_g = int(float(cfg.get("burbuja_x") or 0))
        if es_si(cfg["burbujas"]) and manuales is not None:
            vistos = {"*": 0, "/": 0}
            for b in manuales:
                try:
                    simbolo = "/" if b.get("lado") == "receptor" else "*"
                    vistos[simbolo] += 1
                    t0 = max(0.0, float(b.get("inicio", 0)))
                    # si el guion tiene la marca (*1) / (/2) de este mensaje, el momento sale de ahi
                    m_pos = next((m for m in marcas_pos if m[0] == simbolo and m[1] == vistos[simbolo]), None)
                    if m_pos and palabras:
                        i0 = min(m_pos[2], len(palabras) - 1)
                        t0 = palabras[i0][2] if i0 >= 0 else 0.3
                    t1 = min(total, t0 + max(0.5, float(b.get("duracion", 3))))
                    texto_b = str(b.get("texto", "")).strip()
                    if not texto_b or t0 >= total:
                        continue
                    frase_b = ("Cliente: " + texto_b) if b.get("lado") == "receptor" else texto_b
                    items.append({"frase": frase_b, "t0": t0, "t1": t1, "mover": 0, "mover_x": dx_g, "estilo": est_g,
                                  "entrada": ent_g, "salida": sal_g, "sonido": son_g})
                except (TypeError, ValueError):
                    continue
            items.sort(key=lambda x: x["t0"])
        elif palabras:
            validas = [m for m in marcas if m[1] < len(palabras)]
            tiempos = []
            for (i0, i1, frase, mudo) in validas:
                if mudo:   # no se dice: sale al terminar la palabra anterior y dura unos segundos
                    t_ini = palabras[i0][2] if i0 >= 0 else 0.3
                    t_fin = min(total, t_ini + float(cfg["burbuja_silenciosa_seg"]))
                else:
                    t_ini = max(0.0, palabras[i0][1] - 0.1)
                    t_fin = min(total, palabras[i1][2] + 0.7)
                tiempos.append([t_ini, t_fin])
            for k, (i0, i1, frase, mudo) in enumerate(validas):
                t_ini, t_fin = tiempos[k]
                if _es_cliente(frase)[0] and k + 1 < len(validas) and not _es_cliente(validas[k + 1][2])[0]:
                    t_fin = max(t_fin, tiempos[k + 1][1])   # el cliente se queda mientras contestas
                items.append({"frase": frase, "t0": t_ini, "t1": t_fin, "mover": 0, "mover_x": dx_g, "estilo": est_g,
                              "entrada": ent_g, "salida": sal_g, "sonido": son_g})
        if items:
            for it in items:
                ajustar_item_burbuja(cfg, it)
            for k, (it, y1) in enumerate(zip(items, colocar_burbujas(cfg, items))):
                png = tmp / f"burbuja_{k}.png"
                crear_burbuja(cfg, it["frase"], png, y1, it.get("estilo"), it.get("mover_x", 0))
                burbujas.append((png, it["t0"], it["t1"], it))
            print(f"  {len(burbujas)} burbuja(s) de WhatsApp")

        _voz_e = bool(PLAN_ESCENAS and PLAN_ESCENAS.get("con_voz") and palabras is not None)
        if PLAN_ESCENAS and PLAN_ESCENAS.get("textos") and (_voz_e or (palabras is None and audio.stem == "sin_guion")):
            import hablado
            _k = total / max(0.1, PLAN_ESCENAS["total"]) if _voz_e else 1.0
            _tx = [(a, b * _k, c * _k, [dict(x, seg=x.get("seg", 1) * _k) for x in d_]) for a, b, c, d_ in PLAN_ESCENAS["textos"]]
            tx_e, _pops = hablado.planear_textos(cfg, _tx, total, tmp)
            for png_e, t0_e, t1_e, anim_e in tx_e:
                burbujas.append((png_e, t0_e, t1_e, anim_e))
            print(f"  {len(tx_e)} texto(s) en pantalla")

        cmd = ["ffmpeg", "-y", "-v", "error"]
        for s_ in segmentos:
            cmd += ["-i", str(s_)]
        sig = n

        def entrada_png(ruta_png):
            nonlocal sig
            cmd.extend(["-loop", "1", "-framerate", str(fps), "-i", str(ruta_png)])
            sig += 1
            return sig - 1

        i_base = entrada_png(capas["base"])
        i_tit = entrada_png(capas["titulo"])
        i_cta = entrada_png(capas["cta"])
        i_bub = [entrada_png(b[0]) for b in burbujas]
        i_sub = None
        if palabras:
            lista = crear_subtitulos(cfg, palabras, total, tmp)
            cmd += ["-f", "concat", "-safe", "0", "-i", str(lista)]
            i_sub = sig
            sig += 1
        i_aud = sig
        cmd += ["-i", str(audio)]
        sig += 1
        i_pops = []     # (entrada, burbuja, es_archivo) para cada burbuja que suena
        vol_pop = int(cfg["sonido_burbuja_volumen"]) / 100
        for k_b, (_, t_b, _, it_b) in enumerate(burbujas):
            son = str(it_b.get("sonido") or "").strip()
            if not es_si(cfg["sonido_burbuja"]):
                continue
            args_s = args_sonido(cfg, son) if son else None
            if args_s:
                cmd += args_s
                i_pops.append((sig, k_b, True))
            else:
                cmd += ["-f", "lavfi", "-t", "0.2", "-i",
                        f"aevalsrc={vol_pop:g}*sin(2*PI*820*t)*exp(-26*t):s=44100:d=0.2"]
                i_pops.append((sig, k_b, False))
            sig += 1
        # Efectos de sonido que elige el usuario: en cada transición, al entrar el título y al entrar la frase final
        i_fx = []       # (entrada, milisegundos)
        vol_fx = int(cfg.get("sonido_efectos_volumen", 60)) / 100
        puntos_fx = []
        if str(cfg.get("sonido_transicion") or "").strip():
            puntos_fx += [(cfg["sonido_transicion"], escenas[k]["t0"]) for k in range(1, n)]
        if str(cfg.get("sonido_titulo") or "").strip() and float(cfg["titulo_segundos"]) > 0:
            puntos_fx.append((cfg["sonido_titulo"], 0.0))
        if str(cfg.get("sonido_cta") or "").strip() and float(cfg["cta_segundos"]) > 0:
            puntos_fx.append((cfg["sonido_cta"], max(0.0, total - float(cfg["cta_segundos"]))))
        for val_fx, t_fx in puntos_fx:
            a_fx = args_sonido(cfg, val_fx)
            if a_fx:
                cmd += a_fx
                i_fx.append((sig, int(t_fx * 1000)))
                sig += 1
        paso(6)
        musicas = [p for p in (cfg["dir"] / "musica").glob("*") if p.suffix.lower() in AUDIO_EXT] \
            if (cfg["dir"] / "musica").exists() else []
        i_mus = None
        fijada = [p for p in musicas if p.name.lower() == str(cfg["musica_archivo"]).strip().lower()]
        if str(cfg["musica_archivo"]).strip() and not fijada:
            print(f"  Aviso: no encuentro la canción '{cfg['musica_archivo']}' en la carpeta musica; se elige otra.")
        if musicas and float(cfg["musica_volumen"]) > 0:
            cm = fijada[0] if fijada else (MUSICA_ELEGIDA if MUSICA_ELEGIDA in musicas else random.choice(musicas))
            print(f"  Musica de fondo: {cm.name}")
            cmd += ["-stream_loop", "-1", "-i", str(cm)]
            i_mus = sig
            sig += 1

        marca_agua_png = crear_marca_agua(cfg, tmp) if cfg.get("_marca_agua") else None
        marca_final_png = crear_marca_final(cfg, tmp) if cfg.get("_marca_agua") else None
        t_tit, t_cta = float(cfg["titulo_segundos"]), float(cfg["cta_segundos"])
        en_tit = f":enable='lt(t,{t_tit})'" if t_tit > 0 else ""
        en_cta = f":enable='gte(t,{max(0.0, total - t_cta):.3f})'" if t_cta > 0 else ""

        partes = [f"[{i}:v]settb=AVTB,fps={fps},format=yuv420p[s{i}]" for i in range(n)]
        ult = "s0"
        ant = None
        for k in range(1, n):
            offset = escenas[k]["t0"] - tr / 2  # la transición queda centrada en el corte
            ant = elegir_transicion(cfg, ant)
            partes.append(f"[{ult}][s{k}]xfade=transition={ant}:"
                          f"duration={tr}:offset={max(0.0, offset):.3f}[x{k}]")
            ult = f"x{k}"
        partes.append(f"color=c={cfg['color_fondo']}:s={W}x{H}:r={fps}[bg]")
        partes.append(f"[bg][{ult}]overlay=0:{my}:shortest=1[b1]")
        mov = es_si(cfg["movimiento"])
        partes.append(f"[b1][{i_base}:v]overlay=0:0[c1]")
        # el titulo baja desde arriba con frenado suave
        y_tit = ":y='-420*pow(max(0,1-t/0.45),2)'" if mov else ":y=0"
        partes.append(f"[c1][{i_tit}:v]overlay=x=0{y_tit}{en_tit}[c2]")
        ultimo = "c2"
        for j, ((_, t_ini, t_fin, it_b), idx) in enumerate(zip(burbujas, i_bub)):
            ent = it_b.get("entrada") or ("subir" if mov else "ninguna")
            sal = it_b.get("salida") or "ninguna"
            fx, fy, filtros = [], [], []
            p_in = f"(t-{t_ini:.3f})"
            if ent in ("subir", "fundido", "rebote", "izquierda", "derecha"):
                filtros.append(f"fade=t=in:st={t_ini:.3f}:d={0.12 if ent == 'rebote' else 0.2}:alpha=1")
            if ent == "subir":
                fy.append(f"110*pow(max(0,1-{p_in}/0.28),2)")
            elif ent == "rebote":
                fy.append(f"170*pow(max(0,1-{p_in}/0.4),2)*cos(1.5*PI*min(1,{p_in}/0.4))")
            elif ent == "izquierda":
                fx.append(f"-{W}*pow(max(0,1-{p_in}/0.35),2)")
            elif ent == "derecha":
                fx.append(f"{W}*pow(max(0,1-{p_in}/0.35),2)")
            if sal in ("fundido", "bajar") and t_fin - t_ini > 0.6:
                filtros.append(f"fade=t=out:st={max(t_ini, t_fin - 0.3):.3f}:d=0.3:alpha=1")
            if sal == "bajar" and t_fin - t_ini > 0.6:
                fy.append(f"110*pow(max(0,(t-{t_fin - 0.3:.3f})/0.3),2)")
            if filtros:
                partes.append(f"[{idx}:v]format=rgba,{','.join(filtros)}[bu{j}]")
                fuente_b = f"bu{j}"
            else:
                fuente_b = f"{idx}:v"
            ex = "+".join(fx) or "0"
            ey = "+".join(fy) or "0"
            partes.append(f"[{ultimo}][{fuente_b}]overlay=x='{ex}':y='{ey}':"
                          f"enable='between(t,{t_ini:.3f},{t_fin:.3f})'[d{j}]")
            ultimo = f"d{j}"
        if i_sub is not None:
            partes.append(f"[{i_sub}:v]fps={fps},format=rgba[sub]")
            partes.append(f"[{ultimo}][sub]overlay={int(float(cfg.get('subs_x', 0) or 0))}:{int(cfg['subs_y']) - ALTO_BANDA_SUBS // 2}[e1]")
            ultimo = "e1"
        # destello blanco muy suave en cada corte
        if mov and es_si(cfg["destello"]) and n > 1:
            ventanas = "+".join(f"between(t,{e['t0'] - 0.03:.3f},{e['t0'] + 0.05:.3f})" for e in escenas[1:])
            partes.append(f"[{ultimo}]drawbox=x=0:y=0:w=iw:h=ih:color=white@{int(cfg['destello_intensidad']) / 100:g}:t=fill:"
                          f"enable='{ventanas}'[e2]")
            ultimo = "e2"
        # la frase final sube desde abajo cuando le toca aparecer
        t0_cta = max(0.0, total - t_cta) if t_cta > 0 else 0.0
        y_cta = f":y='220*pow(max(0,1-(t-{t0_cta:.3f})/0.45),2)'" if mov else ":y=0"
        partes.append(f"[{ultimo}][{i_cta}:v]overlay=x=0{y_cta}{en_cta}[f0]")
        ultimo = "f0"
        # barra de progreso delgada que avanza durante todo el video
        if mov and es_si(cfg["barra_progreso"]):
            color_barra = cfg["color_barra"] or cfg["subs_color_activo"]
            partes.append(f"color=c={color_barra}:s={W}x{int(cfg['barra_alto'])}:r={fps}[barra]")
            partes.append(f"[{ultimo}][barra]overlay=x='-w+w*t/{total:.3f}':y={int(cfg['barra_y'])}[f1]")
        else:
            partes.append(f"[{ultimo}]null[f1]")
        ultimo_v = "f1"
        if es_si(cfg.get("onda_audio", False)):          # onda de sonido animada (podcasts y audios): se dibuja con la voz del video
            cmd += ["-i", str(audio)]
            alto_o = max(40, int(H * int(cfg.get("onda_alto", 14)) / 100.0) // 2 * 2)
            y_o = {"arriba": int(H * 0.12), "centro": int((H - alto_o) / 2)}.get(str(cfg.get("onda_pos", "abajo")), int(H * 0.72))
            col_o = str(cfg.get("onda_color") or "#ffffff").lstrip("#")[:6]
            partes.append(f"[{sig}:a]aformat=channel_layouts=mono,showwaves=s={W - 2 * int(W * 0.08)}x{alto_o}:mode=cline:rate={fps}:colors=0x{col_o}:draw=full,format=rgba[onda]")
            partes.append(f"[{ultimo_v}][onda]overlay=x={int(W * 0.08)}:y={y_o}:shortest=0[fonda]")
            ultimo_v = "fonda"
            sig += 1
        ini_final = max(0.0, total - min(MARCA_FINAL_SEGUNDOS, total * 0.4))
        if marca_agua_png:
            cmd += ["-i", str(marca_agua_png)]
            partes.append(f"[{ultimo_v}][{sig}:v]overlay=x=(W-w)/2:y=H-h-{int(H * 0.04)}:enable='lt(t,{ini_final:.3f})'[fw]")
            ultimo_v = "fw"
            sig += 1
        if marca_final_png:
            cmd += ["-i", str(marca_final_png)]
            partes.append(f"[{ultimo_v}][{sig}:v]overlay=0:0:enable='gte(t,{ini_final:.3f})'[ff]")
            ultimo_v = "ff"
            sig += 1
        for cp in leer_capas(cfg.get("dir")):       # logos y capas con transparencia, encima de todo
            cmd += args_entrada_capa(cp["ruta"], fps)
            lineas, ultimo_v = filtros_capa(sig, cp["ruta"], cp, W, H, total, ultimo_v)
            partes += lineas
            sig += 1
        factor = int(cfg.get("calidad", 1080) or 1080) / float(min(W, H))
        if abs(factor - 1) > 0.01:
            partes.append(f"[{ultimo_v}]scale=trunc(iw*{factor:.5f}/2)*2:trunc(ih*{factor:.5f}/2)*2:flags=lanczos[fq]")
            ultimo_v = "fq"
        partes.append(f"[{ultimo_v}]format=yuv420p[vout]")
        vol_voz = int(cfg["voz_volumen"])
        if i_pops or i_fx or i_mus is not None or vol_voz != 100:
            fmt = "aresample=44100,aformat=channel_layouts=stereo"
            ajuste_voz = f",volume={vol_voz / 100:g}" if vol_voz != 100 else ""
            partes.append(f"[{i_aud}:a]{fmt}{ajuste_voz},apad=whole_dur={total:.3f}[va]")
            mezcla = ["[va]"]
            for j, (ip, k_b, es_archivo) in enumerate(i_pops):
                ms = int(burbujas[k_b][1] * 1000)
                recorte = f",volume={vol_pop:g},atrim=0:5" if es_archivo else ""
                partes.append(f"[{ip}:a]{fmt}{recorte},adelay={ms}|{ms}[p{j}]")
                mezcla.append(f"[p{j}]")
            for j, (ip, ms) in enumerate(i_fx):
                partes.append(f"[{ip}:a]{fmt},volume={vol_fx:g},atrim=0:5,adelay={ms}|{ms}[f{j}]")
                mezcla.append(f"[f{j}]")
            if i_mus is not None:
                vol = float(cfg["musica_volumen"]) / 100.0
                partes.append(f"[{i_mus}:a]{fmt},volume={vol:.3f},atrim=0:{total:.3f}[mu]")
                mezcla.append("[mu]")
            partes.append("".join(mezcla) + f"amix=inputs={len(mezcla)}:normalize=0:duration=first[aout]")
            audio_map = "[aout]"
        else:
            audio_map = f"{i_aud}:a"

        salida.parent.mkdir(parents=True, exist_ok=True)
        # El video se escribe con extensión .parte y solo se renombra a .mp4 cuando está COMPLETO. Así nunca aparece
        # (ni cuenta como hecho, ni se puede descargar) un video a medias.
        parcial = salida.with_name(salida.name + ".parte")
        cmd += ["-filter_complex", ";".join(partes), "-map", "[vout]", "-map", audio_map,
                "-t", f"{total:.3f}", "-r", str(fps), "-c:v", "libx264", "-preset", "veryfast",
                "-crf", "20", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-f", "mp4", str(parcial)]
        paso(7)
        try:
            run(cmd)
            paso(8)
            os.replace(parcial, salida)
        finally:
            try:
                parcial.unlink()
            except OSError:
                pass


# ----------------------------------------------------------------------------
# Productos
# ----------------------------------------------------------------------------
def limpiar_nombre(nombre):
    n = unicodedata.normalize("NFD", nombre.strip().lower())
    n = "".join(c for c in n if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9_]+", "_", n).strip("_")


def poner_usuario(cfg, overlay):
    """Escribe el @usuario (si hay) sobre la capa base."""
    usuario = str(cfg.get("usuario", "")).strip()
    if not usuario:
        return
    img = Image.open(overlay).convert("RGBA")
    d = ImageDraw.Draw(img)
    fuente = gv.cargar_fuente(cfg, int(cfg["usuario_tam"]), "usuario")
    w = fuente.getlength(usuario)
    x = (img.width - w) / 2 + int(float(cfg.get("usuario_x", 0) or 0))
    r, g, b = ImageColor.getrgb(cfg["color_usuario"])[:3]
    d.text((x, int(cfg["usuario_y"])), usuario, font=fuente, fill=(r, g, b, 235),
           stroke_width=int(cfg["trazo_usuario"]),
           stroke_fill=ImageColor.getrgb(cfg["color_trazo"])[:3] + (230,))
    img.save(overlay)


def crear_estructura(carpeta, ajustes=AJUSTES_BASE, temas=TEMAS_BASE):
    for sub in ("guiones", "clips/general", "kit", "musica", "videos_finalizados"):
        (carpeta / sub).mkdir(parents=True, exist_ok=True)
    (carpeta / "ajustes.txt").write_text(ajustes, encoding="utf-8-sig")
    (carpeta / "temas.txt").write_text(temas, encoding="utf-8-sig")
    (carpeta / "guiones" / "_pon_guiones_aqui.txt").write_text(
        "Pon aqui los audios (01.mp3, 02.mp3...) y sus textos (01.txt, 02.txt...) de ESTE producto.\n",
        encoding="utf-8")
    (carpeta / "kit" / "_pon_imagenes_del_kit_aqui.txt").write_text(
        "Pon aqui capturas y videos de tu producto (portada, paginas, el CRM...). "
        "Salen al final de cada video y cada vez que se menciona el kit.\n", encoding="utf-8")
    (carpeta / "clips" / "general" / "_clips_generales_aqui.txt").write_text(
        "Pon aqui clips que sirven para cualquier tema. Se usan cuando no hay clip del tema que se menciona.\n",
        encoding="utf-8")


def escribir_bat(nombre):
    contenido = f"""@echo off
cd /d "%~dp0"
title Generando video ({nombre})...
echo Generando 1 video del producto: {nombre}
echo NO CIERRES esta ventana hasta que diga TERMINADO.
echo.
py generar_diario.py --producto {nombre}
echo.
echo ===== TERMINADO =====
explorer "%~dp0productos\\{nombre}\\videos_finalizados"
pause
"""
    bat = BASE / f"GENERAR_VIDEO_{nombre}.bat"
    with open(bat, "w", encoding="utf-8", newline="\r\n") as f:
        f.write(contenido)
    return bat


def nuevo_producto(nombre_crudo):
    nombre = limpiar_nombre(nombre_crudo)
    if not nombre:
        raise ErrorMotor("Escribe un nombre válido (letras y números, sin espacios).")
    carpeta = PRODUCTOS / nombre
    if carpeta.exists():
        raise ErrorMotor(f"Ya existe el producto '{nombre}'.")
    crear_estructura(carpeta)
    bat = escribir_bat(nombre)
    print(f"\nProducto creado: {carpeta}")
    print(f"Archivo para generar videos: {bat.name} (está en la carpeta principal)")
    print("\nSiguientes pasos:")
    print(f"  1) Abre productos\\{nombre}\\ajustes.txt y cambia la frase de abajo ('cta').")
    print(f"  2) Abre productos\\{nombre}\\temas.txt y escribe los temas de ESTE producto.")
    print(f"  3) Pon tus audios y textos en productos\\{nombre}\\guiones")
    print(f"  4) Pon tus capturas del producto en productos\\{nombre}\\kit")
    print(f"  5) Genera un video una vez para que se creen las carpetas de los temas y ahí pon tus clips.")


def elegir_producto(nombre):
    existentes = sorted(p.name for p in PRODUCTOS.iterdir()
                        if p.is_dir() and not p.name.startswith("_")) if PRODUCTOS.exists() else []
    if nombre:
        n = limpiar_nombre(nombre)
        if not (PRODUCTOS / n).is_dir():
            raise ErrorMotor(f"No existe el producto '{nombre}'. Productos disponibles: {', '.join(existentes) or '(ninguno)'}")
        return PRODUCTOS / n
    if len(existentes) == 1:
        return PRODUCTOS / existentes[0]
    raise ErrorMotor("Hay varios productos. Elige uno. "
                     f"Productos: {', '.join(existentes) or '(ninguno)'}")


# ----------------------------------------------------------------------------
# Modo prueba
# ----------------------------------------------------------------------------
def preparar_prueba():
    carpeta = PRODUCTOS / "_prueba"
    if carpeta.exists():
        shutil.rmtree(carpeta)
    temas = ("# temas de prueba\ncasas: casa, casas, propiedad, zona\n"
             "dinero: precio, caro, presupuesto, pago\n"
             "celular: whatsapp, mensaje, mensajes, visto\n"
             "clientes: cliente, clientes, prospecto\n"
             "kit: kit, guiones\n")
    crear_estructura(carpeta, ajustes=AJUSTES_BASE, temas=temas)
    fuente = gv.cargar_fuente({}, 140)
    colores = {"casas": (31, 78, 121), "dinero": (47, 107, 79), "celular": (122, 59, 29),
               "clientes": (110, 50, 120), "general": (70, 70, 70)}
    for tema, col in colores.items():
        (carpeta / "clips" / tema).mkdir(parents=True, exist_ok=True)
        for i in range(2):
            img = Image.new("RGB", (1280, 720), col)
            d = ImageDraw.Draw(img)
            d.text((60, 250), f"{tema.upper()} {i + 1}", font=fuente, fill=(255, 255, 255))
            img.save(carpeta / "clips" / tema / f"{tema}_{i + 1}.png")
    for i in range(2):
        img = Image.new("RGB", (540, 1170), (245, 240, 230))
        d = ImageDraw.Draw(img)
        d.rectangle([30, 30, 510, 140], fill=(31, 78, 121))
        d.text((60, 400), f"KIT {i + 1}", font=fuente, fill=(31, 78, 121))
        img.save(carpeta / "kit" / f"kit_{i + 1}.png")
    (carpeta / "musica").mkdir(exist_ok=True)
    run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "sine=frequency=220:duration=10",
         str(carpeta / "musica" / "musica_prueba.mp3")])
    textos = [
        ("# ¿Te dejaron en visto?",
         "Cuando tu cliente te deja en visto en WhatsApp, no insistas con más mensajes. "
         "El cliente dice: «Cliente: Lo voy a pensar» y tú contestas mejor: «Claro, ¿qué te gustaría revisar con calma?» Pregunta si fue la casa o el precio. En el kit tienes cincuenta guiones listos para responder."),
        ("# Primer contacto",
         "Un prospecto pide información de una casa. No le mandes todo de golpe. "
         "Primero pregúntale si busca mudarse pronto. {Cliente: Estoy viendo otras opciones} El presupuesto lo defines después. "
         "Todos esos mensajes están en el kit."),
    ]
    for i, (g, t) in enumerate(textos, 1):
        a = carpeta / "guiones" / f"{i:02d}.wav"
        run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i",
             f"sine=frequency={200 + 40 * i}:duration={18 + 2 * i}", str(a)])
        a.with_suffix(".txt").write_text(g + "\n" + t, encoding="utf-8")
    return carpeta


# ----------------------------------------------------------------------------
def nombre_de_video(cfg, carpeta_salida, numero, guion, producto):
    """Arma el nombre del video con el patron de ajustes (nombre_video). Siempre devuelve un nombre unico y seguro."""
    patron = str(cfg.get("nombre_video") or DEFECTOS["nombre_video"])
    datos = {"numero": f"{numero:03d}", "guion": re.sub(r"\s+", "_", guion),
             "producto": limpiar_nombre(producto) or producto, "fecha": datetime.date.today().isoformat()}
    nombre = patron
    for k, v in datos.items():
        nombre = nombre.replace("{" + k + "}", v)
    nombre = re.sub(r"\{[^}]*\}", "", nombre)                         # marcas que no existen
    nombre = re.sub(r'[<>:"/\\|?*\x00-\x1f]+', "_", nombre).strip(" ._")  # caracteres que Windows no acepta
    nombre = nombre[:120] or f"video_{numero:03d}"
    final, n = nombre, 2
    carpetas = carpeta_salida if isinstance(carpeta_salida, (list, tuple)) else [carpeta_salida]
    while any((c / f"{final}.mp4").exists() for c in carpetas):
        final, n = f"{nombre}_{n}", n + 1
    return f"{final}.mp4"


def revisar_ffmpeg():
    for herramienta in ("ffmpeg", "ffprobe"):
        if not shutil.which(herramienta):
            raise ErrorMotor(f"No encuentro {herramienta}. Reinstala el programa o reinicia la computadora.")


def reiniciar_producto(carpeta, mostrar=print):
    """Archiva los videos hechos y deja el producto listo para empezar en 001, vuelta 1."""
    sal = carpeta / "videos_finalizados"
    if sal.exists() and any(sal.iterdir()):
        destino = carpeta / ("videos_anteriores_" + datetime.datetime.now().strftime("%Y-%m-%d_%H-%M"))
        shutil.move(str(sal), str(destino))
        mostrar(f"Tus videos anteriores se guardaron en: {destino}")
    ruta_estado = carpeta / "estado.json"
    if ruta_estado.exists():
        ruta_estado.unlink()
    (carpeta / "videos_finalizados").mkdir(exist_ok=True)
    mostrar("Listo: el siguiente video será el 001 y empezará desde el primer guion.")


def generar_videos(carpeta, cantidad=1, reiniciar=False, reiniciar_numeracion=False, mostrar=print, al_crear=None, guion_elegido=None, formatos=None, sin_guion=None, usar_creditos=False, tamano=None, plantilla_voz=None):
    """Genera 'cantidad' videos del producto. Devuelve la lista de archivos creados.
    Lanza ErrorMotor con un mensaje claro si falta algo, y Cancelado si el usuario detiene el proceso.
    sin_guion = {"segundos": 30, "titulo": ""}: video solo con clips y música (sin voz ni subtítulos).
    usar_creditos=True: cada archivo gasta 1 crédito y se hace con los límites del plan Pro (4K, hasta 60 min, sin marca de agua)."""
    tmp_sg = Path(tempfile.mkdtemp(prefix="rm_sg_")) if sin_guion else None
    try:
        return _generar_videos(carpeta, cantidad, reiniciar, reiniciar_numeracion, mostrar, al_crear, guion_elegido, formatos, sin_guion, tmp_sg, usar_creditos, tamano, plantilla_voz)
    finally:
        if tmp_sg:
            shutil.rmtree(tmp_sg, ignore_errors=True)


def _elegir_musica(cfg):
    """La canción que usará el video (la fijada en el estilo o una al azar de la carpeta «musica»), o None."""
    d = cfg["dir"] / "musica"
    musicas = [p for p in d.glob("*") if p.suffix.lower() in AUDIO_EXT] if d.exists() else []
    if not musicas or float(cfg["musica_volumen"]) <= 0:
        return None
    fijada = [p for p in musicas if p.name.lower() == str(cfg["musica_archivo"]).strip().lower()]
    return fijada[0] if fijada else random.choice(musicas)


def _audio_sin_voz(tmp, segundos, titulo=""):
    """Crea un audio en silencio de la duración pedida (y un .txt solo con el título). El video usa la música de fondo."""
    a = tmp / "sin_guion.wav"
    gv.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo", "-t", f"{segundos:.2f}", str(a)])
    titulo = " ".join(str(titulo or "").split())[:140]
    if titulo:
        a.with_suffix(".txt").write_text("# " + titulo + "\n", encoding="utf-8")
    return a


def _generar_videos(carpeta, cantidad, reiniciar, reiniciar_numeracion, mostrar, al_crear, guion_elegido, formatos, sin_guion, tmp_sg, usar_creditos=False, tamano=None, plantilla_voz=None):
    paso(1)
    revisar_ffmpeg()
    cfg = cargar_config(carpeta)
    if tamano:
        cfg["_pers"] = tamano
    temas = leer_temas(carpeta / "temas.txt")
    ruta_estado = carpeta / "estado.json"
    for tema in temas:  # crea las carpetas de los temas para que sepas dónde poner los clips
        if tema != "kit":
            (carpeta / "clips" / tema).mkdir(parents=True, exist_ok=True)
    (carpeta / "clips" / "general").mkdir(parents=True, exist_ok=True)
    (carpeta / "kit").mkdir(parents=True, exist_ok=True)

    if sin_guion:
        guiones = []
        try:
            seg_sg = float(sin_guion.get("segundos") or 30)
        except (TypeError, ValueError):
            seg_sg = 30.0
        seg_sg = max(5.0, min(seg_sg, 600.0))
        titulo_sg = str(sin_guion.get("titulo") or "")
        plantilla_e = None
        if sin_guion.get("plantilla"):
            import escenas as _esc
            plantilla_e = _esc.plantilla(carpeta, str(sin_guion["plantilla"]))
            piezas_e = _esc.cargar_piezas()
            if not _esc.expandir(plantilla_e, piezas_e, azar=False):
                raise ErrorMotor("Esa plantilla de escenas está vacía. Agrega escenas en la pestaña «Escenas».")
            seg_sg = max(2.0, min(_esc.duracion(plantilla_e, piezas_e), 600.0))
    else:
        import hablado
        entradas_h = hablado.entradas_hablando(carpeta)            # tus videos hablando: cada guion de solo texto (o cada video) cuenta como un guion más
        try:
            guiones = listar_guiones(carpeta / "guiones")
        except RuntimeError as ex:
            if not entradas_h:
                raise ErrorMotor(str(ex))
            guiones = []
        guiones = sorted(guiones + entradas_h, key=clave_natural)
    plantilla_pv = None
    if plantilla_voz and not sin_guion:                  # guion con voz + escenas de una plantilla
        import escenas as _esc
        plantilla_pv = _esc.plantilla(carpeta, str(plantilla_voz))
        piezas_e = _esc.cargar_piezas()
        if not _esc.expandir(plantilla_pv, piezas_e, azar=False):
            raise ErrorMotor("Esa plantilla de escenas está vacía. Agrega escenas en la pestaña «Escenas».")
    if sin_guion:
        entradas_h = []
    if not listar_media(carpeta / "clips", True) and not entradas_h:
        raise ErrorMotor("No hay clips. Agrega videos o imágenes en alguno de los temas.")

    fijo = None
    if guion_elegido and not sin_guion:   # el usuario escogio un guion: se usa ese y la vuelta normal no se mueve
        fijo = next((g for g in guiones if guion_elegido in (g.name, g.stem)), None)
        if fijo is None:
            raise ErrorMotor(f"No encuentro el guion «{guion_elegido}».")
    import planes
    n_formatos = len(formatos_destino(cfg, formatos))
    # el producto de muestra no gasta los videos del mes ni los créditos; el de práctica guiada, solo sus primeros 3 archivos
    previos = sum(1 for _ in (carpeta / "videos_finalizados").rglob("*.mp4")) if (carpeta / "videos_finalizados").exists() else 0
    pedidos = cantidad * n_formatos
    es_prac = es_producto_practica(carpeta)
    if es_prac and practica_terminada(carpeta):
        raise ErrorMotor("Esta práctica ya terminó: el proyecto de práctica ya no crea más videos. Para repetirla, borra este proyecto y empieza la práctica otra vez, o crea tu propio proyecto.")
    if es_prac and previos + pedidos > 3:       # el producto de práctica no sirve como producto real: máximo 3 videos
        raise ErrorMotor("Este proyecto es solo de práctica (máximo 3 videos). Crea tu propio proyecto para seguir haciendo videos.")
    gratis_prac = es_prac and planes.practica_gratis_restantes() >= pedidos     # los de práctica son gratis solo hasta cierto total
    de_muestra = carpeta.name == "muestra" or gratis_prac
    usar_creditos = bool(usar_creditos) and not de_muestra
    lim_c = planes.PLANES["pro"] if usar_creditos else None      # con créditos: todo lo del plan Pro
    if n_formatos > 1 and not de_muestra and not (lim_c or planes.limites()).get("multiformato"):
        raise ErrorMotor("Tu plan crea un formato a la vez. Con el plan Pro o Agencia (o con créditos) puedes hacer varios formatos en el mismo pedido.")
    cfg["calidad"] = planes.calidad_permitida(cfg.get("calidad", 1080), lim_c)
    cfg["_marca_agua"] = (lim_c or planes.limites())["marca_agua"]
    if usar_creditos:
        aviso = planes.revisar_creditos(cantidad * n_formatos)
    else:
        aviso = None if de_muestra else planes.revisar_videos(cantidad * n_formatos)
    if aviso:
        raise ErrorMotor(aviso)
    candidatos = [fijo] if fijo else guiones
    largos = {}
    for g in candidatos:
        if not sin_guion and entradas_h and g in entradas_h:     # la duración de tus videos hablando se revisa al escucharlos
            continue
        aviso_d = planes.revisar_duracion(duracion(g), lim_c)
        if aviso_d:
            largos[g] = aviso_d
    if sin_guion:
        aviso_d = planes.revisar_duracion(seg_sg, lim_c)
        if aviso_d:
            raise ErrorMotor(aviso_d.replace("Este guion dura", "Este video dura").replace("Usa un guion más corto.", "Elige una duración menor."))
        musicas_ok = [p for p in (carpeta / "musica").glob("*") if p.suffix.lower() in AUDIO_EXT] if (carpeta / "musica").exists() else []
        if not musicas_ok:
            mostrar("Aviso: este proyecto no tiene música; el video quedará sin sonido. Agrega una canción en la pestaña Música.")
    if fijo and largos:
        raise ErrorMotor(largos[fijo])
    if largos:
        if len(largos) == len(guiones):
            raise ErrorMotor(next(iter(largos.values())))
        mostrar(f"Aviso: {len(largos)} guion(es) se saltan porque duran más de lo que permite {'el pago con créditos' if usar_creditos else 'tu plan'}.")
        guiones = [g for g in guiones if g not in largos]
    est = cargar_estado(ruta_estado)
    if reiniciar:
        est["usados"], est["ciclo"] = [], est["ciclo"] + 1
    if reiniciar_numeracion:
        est["contador"] = 0
    carpeta_salida = carpeta / "videos_finalizados"
    carpeta_salida.mkdir(exist_ok=True)
    hoy = datetime.date.today().isoformat()

    if sin_guion:
        mostrar(f"Proyecto: {carpeta.name}  |  " + (f"escenas «{plantilla_e['nombre']}» ({seg_sg:.0f} s)" if plantilla_e else f"sin guion ({seg_sg:.0f} s)"))
    else:
        mostrar(f"Proyecto: {carpeta.name}  |  {len(guiones)} guiones  |  ciclo {est['ciclo']}")
    creados = []
    for _ in range(cantidad):
        if CANCELAR.is_set():
            raise Cancelado()
        if est["contador"] + 1 > 999:
            mostrar("\nLlegaste al video 999. Reinicia la numeración para volver a empezar en 001.")
            break
        paso(2)
        semilla = random.randrange(1 << 30)     # misma semilla = mismos clips y tiempos en todos los formatos
        plan_v = None
        musica_v = None
        if sin_guion and plantilla_e:
            random.seed(semilla)
            pulsos_v, musica_v = [], None
            if plantilla_e.get("ritmo"):                        # cortes al ritmo: se elige antes la canción y se busca su pulso
                musica_v = _elegir_musica(cfg)
                if musica_v:
                    import ritmo
                    pulsos_v = ritmo.pulsos(musica_v)
                    if not pulsos_v:
                        mostrar("  No pude sentir el pulso de esa canción; los cortes quedan con los tiempos de la plantilla.")
            plan_v = _esc.plan(plantilla_e, piezas_e, pulsos_v)           # las piezas «al azar» se eligen una vez por video (igual en todos los formatos)
            guion = _audio_sin_voz(tmp_sg, max(2.0, plan_v["total"]), titulo_sg)
        else:
            guion = _audio_sin_voz(tmp_sg, seg_sg, titulo_sg) if sin_guion else (fijo or elegir_guion(guiones, est))
            if plantilla_pv and not (entradas_h and guion in entradas_h):
                random.seed(semilla)
                plan_v = _esc.plan(plantilla_pv, piezas_e, [])
                plan_v["con_voz"] = True
        numero = est["contador"] + 1
        destinos = formatos_destino(cfg, formatos)
        carpetas = [carpeta_salida / carpeta_formato(c) for _, c in destinos]
        for d in carpetas:
            d.mkdir(parents=True, exist_ok=True)
        nombre = nombre_de_video(cfg, carpetas, numero, (limpiar_nombre(plantilla_e["nombre"]) or "escenas") if (sin_guion and plantilla_e) else guion.stem, carpeta.name)
        grupo = uuid.uuid4().hex[:10]
        mostrar(f"\n== Video finalizado {numero:03d} (guion {guion.stem}) ==")
        elegidos = []
        ctx_h = None
        if not sin_guion and entradas_h and guion in entradas_h:
            import hablado
            random.seed(semilla)
            paso(2)
            ctx_h = hablado.preparar_entrada(carpeta, guion, cfg, mostrar, lim_c)
        for (fmt, cfg_f), dir_f in zip(destinos, carpetas):
            if CANCELAR.is_set():
                raise Cancelado()
            salida = dir_f / nombre
            if len(destinos) > 1:
                mostrar(f"  Formato: {fmt} ({int(cfg_f['ancho'])}x{int(cfg_f['alto'])})")
            random.seed(semilla)
            material = Material(cfg_f, temas, est["recientes"])
            try:
                if ctx_h:
                    hablado.render_entrada(ctx_h, carpeta, cfg_f, temas, material, salida)
                else:
                    global PLAN_ESCENAS, MUSICA_ELEGIDA
                    PLAN_ESCENAS = plan_v
                    MUSICA_ELEGIDA = musica_v if plan_v else None
                    try:
                        renderizar(cfg_f, guion, salida, material)
                    finally:
                        PLAN_ESCENAS = None
                        MUSICA_ELEGIDA = None
            except (Cancelado, ErrorMotor):
                raise
            except Exception as ex:
                raise ErrorMotor(f"No se pudo crear el video {numero:03d} ({fmt}). {ex}")
            if usar_creditos:
                planes.gastar_credito()
            elif gratis_prac:
                planes.sumar_practica_gratis()
            elif not de_muestra:
                planes.sumar_video()
            elegidos = material.elegidos
            with open(carpeta_salida / "registro.txt", "a", encoding="utf-8") as reg:
                reg.write(f"{numero:03d} | guion {guion.stem} | vuelta {est['ciclo']} | {hoy} | {fmt} | {salida.relative_to(carpeta_salida).as_posix()}\n")
            mostrar(f"  Listo: {salida.name}  [{fmt}]")
            creados.append(salida)
            if al_crear:
                try:
                    al_crear({"archivo": salida.relative_to(carpeta_salida).as_posix(), "nombre": salida.name,
                              "formato": "personalizado" if fmt not in catalogo.FORMATOS else fmt,
                              "medidas": f"{int(cfg_f['ancho'])}x{int(cfg_f['alto'])}", "numero": numero,
                              "guion": guion.stem, "vuelta": est["ciclo"], "grupo": grupo,
                              "mb": round(salida.stat().st_size / 1e6, 1)})
                except Exception:
                    pass
        if not fijo and not sin_guion:
            est["usados"].append(guion.name)
        est["contador"] = numero
        usados = [str(p.relative_to(carpeta)) for p in elegidos]
        est["recientes"] = (est["recientes"] + usados)[-150:]
        guardar_estado(ruta_estado, est)
    return creados


def main():
    try:
        sys.stdout.reconfigure(errors="replace")
    except Exception:
        pass
    ap = argparse.ArgumentParser(description="Generador de videos por producto.")
    ap.add_argument("--producto", help="nombre del producto (carpeta dentro de 'productos')")
    ap.add_argument("--nuevo", help="crea un producto nuevo con ese nombre")
    ap.add_argument("--cantidad", type=int, default=1, help="cuántos videos generar (por defecto 1)")
    ap.add_argument("--desde-cero", action="store_true",
                    help="archiva los videos hechos y empieza en 001, vuelta 1")
    ap.add_argument("--reiniciar", action="store_true", help="vuelve a empezar la vuelta de guiones")
    ap.add_argument("--reiniciar-numeracion", action="store_true",
                    help="vuelve a numerar desde el video 001")
    ap.add_argument("--prueba", action="store_true", help="demo con material de ejemplo")
    args = ap.parse_args()
    try:
        if args.nuevo:
            nuevo_producto(args.nuevo)
            return
        revisar_ffmpeg()
        if args.prueba:
            carpeta = preparar_prueba()
            args.cantidad = max(args.cantidad, 2)
        else:
            carpeta = elegir_producto(args.producto)
        if args.desde_cero:
            reiniciar_producto(carpeta)
            return
        generar_videos(carpeta, args.cantidad, args.reiniciar, args.reiniciar_numeracion)
    except ErrorMotor as ex:
        sys.exit(str(ex))
    except Cancelado:
        sys.exit("Detenido.")


if __name__ == "__main__":
    main()
