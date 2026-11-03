"""Subtitular mi video: la persona sube un video donde ella habla y Vibovapp
 1) lo transcribe (whisper.cpp que viene en la carpeta bin, o faster-whisper si está instalado),
 2) quita los silencios y las muletillas largas (opcional),
 3) alterna cortes con zoom (como los editores de TikTok/Reels) (opcional),
 4) le pone subtítulos animados con los mismos estilos de siempre.
El texto se puede corregir antes de crear el video final."""
import json
import os
import random
import re
import shutil
import subprocess
import threading
import urllib.request
from pathlib import Path

import catalogo
import core
import generar_diario as gd
import usuarios

MODELOS = {
    "base": ("ggml-base.bin", "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.bin", 148_000_000),
    "small": ("ggml-small.bin", "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-small.bin", 488_000_000),
}
EXT_VIDEO = {".mp4", ".mov", ".mkv", ".webm", ".avi", ".m4v", ".3gp", ".wav", ".mp3", ".m4a", ".ogg", ".opus", ".aac", ".flac"}   # también audios (la voz del narrador)


def carpeta_modelos():
    c = Path(usuarios.RAIZ) / "modelos"   # compartido por todos los usuarios (pesa unos 150 MB)
    c.mkdir(parents=True, exist_ok=True)
    return c


def carpeta_salida():
    c = Path(gd.DATOS) / "Videos con subtitulos"
    c.mkdir(parents=True, exist_ok=True)
    return c


def _cli():
    for n in ("whisper-cli", "whisper-cli.exe", "whisper-cpp", "main.exe"):
        r = shutil.which(n)
        if r:
            return r
    return None


def _fw():
    try:
        import faster_whisper  # noqa
        return True
    except Exception:
        return False


def estado_motor(modelo="base"):
    """Qué falta para poder transcribir: motor (programa) y modelo (archivo grande que se baja una vez)."""
    nombre = MODELOS.get(modelo, MODELOS["base"])[0]
    cli, fw = _cli(), _fw()
    return {"motor": "cli" if cli else ("fw" if fw else None),
            "modelo": (carpeta_modelos() / nombre).exists() or (fw and not cli),
            "mb": round(MODELOS.get(modelo, MODELOS["base"])[2] / 1e6)}


# ---------------------------------------------------------------- trabajo en segundo plano
class Trabajo:
    def __init__(self):
        self.reset()

    def reset(self):
        self.activo = False
        self.fase = ""          # modelo | transcribir | render
        self.pct = 0
        self.log = []
        self.error = None
        self.cancelado = False
        self.terminado = False
        self.palabras = None    # resultado de transcribir
        self.lineas = None      # resultado de analizar una conversación
        self.avisos = []
        self.plan = None
        self.base, self.span = 0, 100   # el % de una transcripción se acomoda dentro de este tramo
        self.video = None       # ruta de entrada
        self.resultado = None   # nombre del archivo final
        self.n = getattr(self, "n", 0)


H = Trabajo()
_lock = threading.Lock()


def _msg(t):
    H.log.append(str(t))
    H.log = H.log[-100:]


def _pct(x):
    H.pct = int(H.base + max(0, min(100, x)) * H.span / 100)


def _cancelado():
    return H.cancelado or gd.CANCELAR.is_set()


def _chequear():
    if _cancelado():
        raise gd.Cancelado()


def iniciar(fn, *a):
    with _lock:
        if H.activo:
            raise gd.ErrorMotor("Ya hay un video en proceso. Espera a que termine.")
        n = H.n + 1
        guardado = (H.plan, H.lineas, H.avisos)
        H.reset()
        H.n = n
        if getattr(fn, "__name__", "") == "tarea_crear_conv":      # crear usa lo que dejó el análisis
            H.plan, H.lineas, H.avisos = guardado
        H.activo = True

    def correr():
        try:
            fn(*a)
        except gd.Cancelado:
            H.cancelado = True
            _msg("Detenido.")
        except gd.ErrorMotor as e:
            H.error = str(e)
        except Exception as e:      # nunca dejar sin mensaje
            H.error = "No se pudo completar: " + repr(e)
            _msg("DETALLE TÉCNICO: " + repr(e))
        finally:
            H.activo = False
            H.terminado = True
    threading.Thread(target=correr, daemon=True).start()


def estado():
    return {"activo": H.activo, "fase": H.fase, "pct": H.pct, "log": H.log[-8:], "error": H.error, "cancelado": H.cancelado,
            "terminado": H.terminado, "n": H.n, "palabras": H.palabras, "resultado": H.resultado,
            "lineas": H.lineas, "avisos": H.avisos}


# ---------------------------------------------------------------- modelo
def bajar_modelo(modelo="base"):
    nombre, url, tam = MODELOS.get(modelo, MODELOS["base"])
    destino = carpeta_modelos() / nombre
    if destino.exists():
        return destino
    H.fase = "modelo"
    parte = destino.with_suffix(".parte")
    try:
        with urllib.request.urlopen(url, timeout=30) as r, open(parte, "wb") as f:
            total = int(r.headers.get("Content-Length") or tam)
            hecho = 0
            while True:
                _chequear()
                bloque = r.read(1 << 20)
                if not bloque:
                    break
                f.write(bloque)
                hecho += len(bloque)
                H.pct = min(99, int(hecho * 100 / total))
        os.replace(parte, destino)
    except gd.Cancelado:
        raise
    except Exception as e:
        try:
            parte.unlink()
        except OSError:
            pass
        raise gd.ErrorMotor("No se pudo descargar el modelo de voz (se necesita internet solo esta vez). Detalle: " + str(e)[:120])
    return destino


# ---------------------------------------------------------------- transcripción
def _duracion(video):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(video)],
                       capture_output=True, text=True)
    try:
        return float(r.stdout.strip())
    except ValueError:
        raise gd.ErrorMotor("No pude leer el video. Prueba con otro archivo (mp4 o mov).")


def _tiene_audio(video):
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries", "stream=codec_type", "-of", "csv=p=0", str(video)],
                       capture_output=True, text=True)
    return "audio" in r.stdout


def _tiene_video(video):
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v", "-show_entries", "stream=codec_type", "-of", "csv=p=0", str(video)],
                       capture_output=True, text=True)
    return "video" in r.stdout


def _parsear_json_cpp(ruta):
    """whisper.cpp con --max-len 1 --split-on-word: un trozo = una palabra, con tiempos en milisegundos."""
    d = json.loads(Path(ruta).read_text(encoding="utf-8", errors="replace"))
    out = []
    for s in d.get("transcription", []):
        t = (s.get("text") or "").strip()
        if not t or re.fullmatch(r"\[.*\]|\(.*\)|♪+", t):      # [MÚSICA], (aplausos)...
            continue
        o = s.get("offsets") or {}
        a, b = o.get("from", 0) / 1000.0, o.get("to", 0) / 1000.0
        out.append([t, a, max(b, a + 0.05)])
    return _unir_palabras(out)


def _unir_palabras(ws):
    """Si whisper partió una palabra (sin espacio) o dejó puntuación suelta, se pega a la anterior."""
    out = []
    for w in ws:
        if out and (re.fullmatch(r"[.,;:!?¿¡…\"')\]]+", w[0])):
            out[-1][0] += w[0]
            out[-1][2] = max(out[-1][2], w[2])
        else:
            out.append(list(w))
    return out


def transcribir(video, idioma="es", modelo="base"):
    video = Path(video)
    if not _tiene_audio(video):
        raise gd.ErrorMotor("Este video no tiene sonido, así que no hay nada que subtitular.")
    tmp = Path(gd.DATOS) / "_tmp_hablado"
    shutil.rmtree(tmp, ignore_errors=True)
    tmp.mkdir(parents=True)
    try:
        wav = tmp / "voz.wav"
        H.fase = "transcribir"
        _pct(3)
        _msg("Preparando el audio...")
        r = subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(video), "-vn", "-ac", "1", "-ar", "16000", str(wav)],
                           capture_output=True, text=True)
        if r.returncode != 0:
            raise gd.ErrorMotor("No pude leer el audio del video: " + r.stderr[-150:])
        _chequear()
        cli = _cli()
        if cli:
            mod = carpeta_modelos() / MODELOS.get(modelo, MODELOS["base"])[0]
            if not mod.exists():
                _msg("Descargando el modelo de voz (solo la primera vez)...")
                mod = bajar_modelo(modelo)
                H.fase = "transcribir"
            _msg("Escuchando lo que dices...")
            _pct(10)
            base = tmp / "sal"
            cmd = [cli, "-m", str(mod), "-f", str(wav), "-l", idioma if idioma in ("es", "en") else "auto",
                   "-ml", "1", "-sow", "-oj", "-of", str(base), "-np"]
            kw = {"creationflags": 0x08000000} if os.name == "nt" else {}
            reg = tmp / "whisper.log"                  # la salida va a un archivo: si se dejara en un pipe sin leer, en Windows whisper se atora al llenarse
            fl = open(reg, "w", encoding="utf-8", errors="replace")
            p = subprocess.Popen(cmd, stdout=fl, stderr=subprocess.STDOUT, text=True, errors="replace", **kw)
            while p.poll() is None:
                try:
                    p.wait(0.5)
                except subprocess.TimeoutExpired:
                    pass
                if _cancelado():
                    p.kill()
                    raise gd.Cancelado()
                _pct(min(90, (H.pct - H.base) * 100 / max(1, H.span) + 1))
            fl.close()
            if p.returncode != 0 or not Path(str(base) + ".json").exists():
                raise gd.ErrorMotor("El reconocimiento de voz falló. " + reg.read_text(encoding="utf-8", errors="replace")[-200:])
            palabras = _parsear_json_cpp(str(base) + ".json")
        elif _fw():
            _msg("Escuchando lo que dices...")
            from faster_whisper import WhisperModel
            m = WhisperModel(modelo, device="cpu", compute_type="int8")
            segs, _ = m.transcribe(str(wav), language=idioma if idioma in ("es", "en") else None, word_timestamps=True)
            palabras = []
            for s in segs:
                _chequear()
                palabras += [[w.word.strip(), float(w.start), float(w.end)] for w in (s.words or []) if w.word.strip()]
        else:
            raise gd.ErrorMotor("Falta el motor de reconocimiento de voz (whisper). Instala la versión más reciente de Vibovapp.")
        if not palabras:
            raise gd.ErrorMotor("No se escuchó ninguna voz en el video. ¿Se oye bien el audio?")
        _pct(100)
        return palabras
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def transcribir_cache(video, idioma="es", modelo="base"):
    """Como transcribir, pero si ese mismo archivo ya se escuchó antes, usa lo guardado (así cada video nuevo sale en segundos)."""
    import hashlib
    video = Path(video)
    try:
        st = video.stat()
        clave = hashlib.sha1(f"{video.resolve()}|{st.st_size}|{st.st_mtime_ns}|{idioma}|{modelo}".encode()).hexdigest()[:24]
    except OSError:
        return transcribir(video, idioma, modelo)
    carpeta = Path(gd.DATOS) / "_cache_hablado"
    ruta = carpeta / (clave + ".json")
    try:
        if ruta.exists():
            d = json.loads(ruta.read_text(encoding="utf-8"))
            if d:
                _msg(f"  (ya había escuchado {video.name.split('_', 1)[-1]})")
                return d
    except Exception:
        pass
    pal = transcribir(video, idioma, modelo)
    try:
        carpeta.mkdir(parents=True, exist_ok=True)
        ruta.write_text(json.dumps(pal, ensure_ascii=False), encoding="utf-8")
    except OSError:
        pass
    return pal


def tarea_transcribir(video, idioma, modelo, guion=""):
    H.video = str(video)
    pal = transcribir(video, idioma, modelo)
    if (guion or "").strip():                 # con guion: se muestran TUS palabras (bien escritas) con los tiempos de lo que se oyó
        lineas, avisos = parsear_guion(guion, None)
        H.avisos = avisos
        txt, marcas = [], {}
        for ln in lineas:
            for i, w in enumerate(ln["palabras"]):
                if i in ln["marcas"]:
                    marcas[len(txt)] = ln["marcas"][i]
                txt.append(w)
        if txt:
            al = gd.alinear(txt, pal)
            pal = [[w[0], w[1], w[2]] + ([_marcas_txt(marcas[i])] if i in marcas else []) for i, w in enumerate(al)]
    H.palabras = pal
    _msg(f"Listo: {len(pal)} palabras.")


def _lineas_de_palabras(pal, pausa=0.7, maximo=18):
    """Las palabras escuchadas -> líneas (una por frase o pausa larga), para escribirlas como guion."""
    lineas, act, prev = [], [], None
    for w in pal:
        if act and (w[1] - prev > pausa or len(act) >= maximo or re.search(r"[.!?…]$", act[-1])):
            lineas.append(" ".join(act))
            act = []
        act.append(str(w[0]).strip())
        prev = w[2]
    if act:
        lineas.append(" ".join(act))
    return [l for l in lineas if l.strip()]


def tarea_texto(video, persona, pid, idioma="es", modelo="base"):
    """Escucha un video y deja su texto escrito como guion («Persona 1: …») para poder corregirlo y marcarlo."""
    H.video = str(video)
    pal = transcribir_cache(video, idioma, modelo)
    if not pal:
        raise gd.ErrorMotor("No escuché palabras en ese video.")
    texto = "\n".join(f"{persona}: {l}" for l in _lineas_de_palabras(pal))
    nombre = core.nuevo_guion(pid, "Texto de " + Path(video).stem[:40])
    core.guardar_guion(pid, nombre, texto)
    H.resultado = nombre
    _msg(f"Listo: {len(pal)} palabras escritas en el guion «{nombre}».")


# ---------------------------------------------------------------- guion: «Persona 1: texto» y marcas [tema]
LADOS = {"yo": "yo", "mia": "yo", "mio": "yo", "mi": "yo", "me": "yo", "mine": "yo", "my": "yo", "emisor": "yo", "emisora": "yo", "receptor": "cliente", "receptora": "cliente", "cliente": "cliente", "client": "cliente", "them": "cliente", "ellos": "cliente", "otro": "cliente", "otra": "cliente"}
VISTAS = {"clips": "clips", "clip": "clips", "broll": "clips", "cara": "cara", "face": "cara", "video": "cara", "pantalla": "cara"}


def _marca_txt(m):
    """Una marca (dict) -> el texto que se escribe entre corchetes."""
    if m["t"] == "fx":
        return m.get("texto", "")
    if m["t"] == "burb":
        return f"{m['lado']}: {m['texto']}"
    return m["tema"] + (f" {m['seg']:g}" if m.get("seg") else "")


def _marcas_txt(ms):
    return "|".join(_marca_txt(m) for m in (ms or []))


def _leer_marca(txt):
    """«ciudad» · «ciudad 3» (3 = segundos) -> clip.   «yo: ¿Cuánto cuesta?» · «cliente: Desde 500» -> burbuja de WhatsApp."""
    txt = (txt or "").strip()
    m = re.match(r"^(?:burbuja\s+)?([^:]{1,10}?)\s*:\s*(.+)$", txt, re.I | re.S)
    if m and gd.normalizar(m.group(1)) in LADOS:
        return {"t": "burb", "lado": LADOS[gd.normalizar(m.group(1))], "texto": " ".join(m.group(2).split())}
    partes = txt.replace(",", " ").split()
    seg = None
    if partes and re.fullmatch(r"\d+([.,]\d+)?", partes[-1]):
        seg = float(partes.pop().replace(",", "."))
    return {"t": "clip", "tema": gd.normalizar(" ".join(partes)), "seg": seg}


def _marcas_de_texto(s):
    """«ciudad 3|yo: hola» -> lista de marcas (así viajan las marcas entre la pantalla y el servidor)."""
    return [_leer_marca(x) for x in str(s or "").split("|") if x.strip()] or None


def _clip_de(marcas):
    return next((m for m in (marcas or []) if m["t"] == "clip"), None)


POSICIONES = {"arriba": (0.12, 0.30), "centro": (0.36, 0.58), "abajo": (0.62, 0.80)}
EFECTOS_TEXTO = ("subir", "fundido", "rebote", "izquierda", "derecha", "ninguna")


def _leer_span(txt):
    """«muy feas por cierto|txt pop -sub tam=80 color=#FFAA00 efecto=rebote pos=centro seg=2»  (así se guarda una frase marcada).
    Opciones: -sub (no sale en los subtítulos) · -dice (nadie la dice: solo se ve el texto) · corta (la dicen en el video y se corta ese pedazo)
    · txt (texto en pantalla) · pop (sonido) · tam= · color= · efecto= · pos= · seg= (cuánto dura)."""
    frase, _, op = str(txt).partition("|")
    m = {"t": "fx", "texto": " ".join(frase.split()), "n": 0, "sub": True, "dice": True, "corta": False, "txt": False, "pop": False,
         "tam": None, "color": None, "efecto": None, "pos": None, "seg": None, "burbuja": None, "img": None, "fig": None, "estilo": None}
    for o in re.split(r"[\s,]+", op.strip()):
        o = o.strip()
        if not o:
            continue
        k, _, v = o.partition("=")
        k = gd.normalizar(k.lstrip("+-")) if not k.startswith("-") else "-" + gd.normalizar(k[1:])
        if k == "-sub":
            m["sub"] = False
        elif k == "-dice":
            m["dice"] = False
        elif k == "corta":
            m["corta"] = True
        elif k in ("txt", "texto"):
            m["txt"] = True
        elif k == "pop":
            m["pop"] = True
        elif k == "tam" and re.fullmatch(r"\d{2,3}", v):
            m["tam"] = int(v)
        elif k == "color" and re.fullmatch(r"#[0-9a-fA-F]{6}", v):
            m["color"] = v
        elif k == "efecto" and gd.normalizar(v) in EFECTOS_TEXTO:
            m["efecto"] = gd.normalizar(v)
        elif k == "pos" and gd.normalizar(v) in POSICIONES:
            m["pos"] = gd.normalizar(v)
        elif k == "seg" and re.fullmatch(r"\d+([.,]\d+)?", v):
            m["seg"] = float(v.replace(",", "."))
        elif k == "burbuja" and gd.normalizar(v) in LADOS:
            m["burbuja"] = LADOS[gd.normalizar(v)]
        elif k == "img" and v:
            from urllib.parse import unquote
            m["img"] = unquote(v)                                  # varias imágenes juntas (collage): a.png+b.png
        elif k == "estilo" and gd.normalizar(v) in gd.ESTILOS_VALIDOS:
            m["estilo"] = gd.normalizar(v)
        elif k == "fig" and gd.normalizar(v) in FIGURAS:
            m["fig"] = gd.normalizar(v)
    return m


def _tokens(texto):
    """Separa palabras y marcas. Devuelve (palabras, {indice_de_palabra: [marcas]}). Las marcas van justo después de la palabra.
    Una frase entre dobles corchetes [[frase|opciones]] lleva sus propias opciones (ver _leer_span)."""
    pal, marcas, pend = [], {}, []
    for tk in re.findall(r"\[\[.*?\]\]|\[[^\]]*\]|[^\s\[]+", texto, re.S):
        if tk.startswith("[["):
            sp = _leer_span(tk[2:-2])
            pals = sp["texto"].split()
            if sp.get("burbuja") and pals:                       # burbuja de chat: no se dice, se dibuja como las de siempre
                b = {"t": "burb", "lado": sp["burbuja"], "texto": sp["texto"]}
                if pal:
                    marcas.setdefault(len(pal) - 1, []).append(b)
                else:
                    pend.append(b)
                continue
            if not pals and (sp.get("img") or sp.get("fig")):                       # solo una imagen (sin texto)
                sp["n"] = 0
                if pal:
                    marcas.setdefault(len(pal) - 1, []).append(sp)
                else:
                    pend.append(sp)
                continue
            if not pals:
                continue
            if sp["dice"] or sp["corta"]:                       # se dice en el video: sus palabras entran al guion
                sp["n"] = len(pals)
                marcas.setdefault(len(pal), []).append(sp)
                pal.extend(pals)
            else:                                                # nadie la dice: solo se ve (como una burbuja)
                sp["n"] = 0
                if pal:
                    marcas.setdefault(len(pal) - 1, []).append(sp)
                else:
                    pend.append(sp)
            continue
        if tk.startswith("["):
            if pal:
                marcas.setdefault(len(pal) - 1, []).append(_leer_marca(tk[1:-1]))
        elif pal and re.fullmatch(r"[.,;:!?¿¡…\"')\]]+", tk):      # «prueba[ciudad].» -> el punto se queda con «prueba»
            pal[-1] += tk
        else:
            pal.append(tk)
    if pend and pal:
        for sp in pend:
            if sp.get("t") == "fx":
                sp["antes"] = True
        marcas.setdefault(0, [])[0:0] = pend
    return pal, marcas


def parsear_guion(texto, nombres):
    """nombres = ["Persona 1", ...] o None (un solo video). Devuelve (lineas, avisos).
    Cada línea: {"persona": indice|None, "vista": "cara"|"clips"|None, "texto", "palabras", "marcas"}.
    «Persona 1 (clips): …» = se oye a Persona 1 pero se ven clips.  «Narrador (cara): …» = se ve el video del narrador."""
    lineas, avisos = [], []
    claves = {gd.normalizar(n): i for i, n in enumerate(nombres or [])}
    for n, crudo in enumerate((texto or "").splitlines(), 1):
        crudo = crudo.strip()
        if not crudo:
            continue
        persona, resto, vista = None, crudo, None
        if nombres:
            m = re.match(r"^\s*([^:\[\]()]{1,40}?)\s*(?:\(([^)]{0,20})\))?\s*:\s*(.*)$", crudo)
            k = gd.normalizar(m.group(1)) if m else ""
            persona = None
            if m:
                if k in claves:
                    persona = claves[k]
                elif k.isdigit() and 1 <= int(k) <= len(nombres):
                    persona = int(k) - 1
                elif re.fullmatch(r"(persona|presentador|presentadora|person|presenter)\s*\d+", k) and 1 <= int(re.sub(r"\D", "", k)) <= len(nombres):
                    persona = int(re.sub(r"\D", "", k)) - 1
                else:
                    persona = next((i for i, x in enumerate(nombres) if k == gd.normalizar(x).replace("persona", "").replace("presentador", "").replace("presentadora", "").strip()), None)
            if persona is None:
                avisos.append(f"Línea {n}: no sé quién habla. Empieza con «{nombres[0]}:» (o el nombre de la persona).")
                lineas.append({"persona": None, "vista": None, "texto": crudo, "palabras": [], "marcas": {}, "n": n})
                continue
            resto = m.group(3)
            if m.group(2):
                vista = VISTAS.get(gd.normalizar(m.group(2)))
                if vista is None:
                    avisos.append(f"Línea {n}: «({m.group(2)})» no se entiende; usa (clips) o (cara). Se ignora.")
        pal, marcas = _tokens(resto)
        if pal:
            lineas.append({"persona": persona, "vista": vista, "texto": " ".join(pal), "palabras": pal, "marcas": marcas, "n": n})
    return lineas, avisos


# ---------------------------------------------------------------- conversación: cada persona grabó su parte
COLORES_PERSONAS = [None, "#4DE1FF", "#FF6BD6", "#7CFF6B", "#FFB347", "#B28DFF"]


def _norm_frase(pals):
    return " ".join(x for x in (gd.normalizar(p) for p in pals) if x)


def buscar_linea(pals, tomas, variar=False):
    """Busca en las tomas de una persona el pedazo que más se parece a la línea del guion.
    tomas = [(indice_fuente, [[txt, a, b], ...])]. Devuelve (puntaje 0-1, fuente, i0, i1) o None."""
    import difflib
    objetivo = _norm_frase(pals)
    n = len(pals)
    if not objetivo or n == 0:
        return None
    mejor = None
    cands = []
    for fi, ws in tomas:
        normas = [gd.normalizar(w[0]) for w in ws]
        for L in sorted({max(1, n - 2), max(1, n - 1), n, n + 1, n + 2}):
            for i in range(0, len(ws) - L + 1):
                cand = " ".join(x for x in normas[i:i + L] if x)
                if not cand:
                    continue
                sc = difflib.SequenceMatcher(None, objetivo, cand, autojunk=False).ratio()
                cands.append((sc, fi, i, i + L - 1))
                if mejor is None or sc >= mejor[0] - 1e-9:      # a igualdad gana la toma más tarde (suele ser la mejor)
                    mejor = (sc, fi, i, i + L - 1)
    if mejor and variar:                       # entre las tomas casi igual de buenas se elige una al azar
        cerca = [c for c in cands if c[0] >= mejor[0] - 0.04 and c[0] >= 0.55]
        tomas_cerca = {}
        for c in cerca:                         # una candidata (la mejor) por toma, para que el azar sea entre tomas y no entre recortes de la misma
            if c[1] not in tomas_cerca or c[0] > tomas_cerca[c[1]][0]:
                tomas_cerca[c[1]] = c
        if len(tomas_cerca) > 1:
            return random.choice(list(tomas_cerca.values()))
    return mejor


def _voz_narrador(texto, destino, narr):
    """Genera la voz del narrador (Windows o ElevenLabs) y devuelve su duración."""
    import voz as motor_voz
    vel = narr.get("velocidad", 0)
    if narr.get("modo") == "elevenlabs":
        core.exigir_elevenlabs()
        clave = core.clave_elevenlabs()
        if not clave:
            raise gd.ErrorMotor("Primero conecta tu cuenta de ElevenLabs (pestaña «Guiones», voz de ElevenLabs).")
        motor_voz.el_sintetizar(texto, destino, clave, narr.get("voz", ""), vel)
    else:
        motor_voz.sintetizar(texto, destino, narr.get("voz", ""), vel)
    return gd.duracion(destino)


def tarea_analizar_conv(personas, guion, idioma, modelo, narrador=None, variar=False):
    """personas = [{"nombre": "Persona 1", "rutas": [...]}, ...]
    narrador = None o {"modo": "grabar"|"windows"|"elevenlabs", "rutas": [...] (si grabó), "voz", "velocidad"}"""
    personas = list(personas)
    narr_idx = None
    if narrador and narrador.get("modo"):
        narr_idx = len(personas)
        personas.append({"nombre": "Narrador", "rutas": narrador.get("rutas") or [] if narrador["modo"] == "grabar" else []})
        if narrador["modo"] == "grabar" and not personas[-1]["rutas"]:
            raise gd.ErrorMotor("Graba o sube la voz del narrador.")
    nombres = [p["nombre"] for p in personas]
    lineas, avisos = parsear_guion(guion, nombres)
    if not any(l["persona"] is not None for l in lineas):
        raise gd.ErrorMotor("Escribe el guion con el nombre de quien habla en cada línea. Ejemplo:\n" + nombres[0] + ": Hola, ¿cómo estás?")
    fuentes, por_persona = [], {}
    total_f = sum(len(p["rutas"]) for p in personas) or 1
    hechos = 0
    trans = {}
    for pi, p in enumerate(personas):
        for ruta in p["rutas"]:
            fi = len(fuentes)
            fuentes.append(Path(ruta))
            por_persona.setdefault(pi, []).append(fi)
            H.base, H.span = hechos * 90 / total_f, 90 / total_f
            _msg(f"Escuchando a {p['nombre']}: {Path(ruta).name}")
            trans[fi] = transcribir_cache(ruta, idioma, modelo)
            hechos += 1
    H.base, H.span = 90, 10
    durs = {fi: _duracion(f) for fi, f in enumerate(fuentes)}
    tramos, resumen = [], []
    for ln in lineas:
        reg = {"n": ln["n"], "persona": nombres[ln["persona"]] if ln["persona"] is not None else "?", "texto": ln["texto"], "estado": "falta"}
        es_narr = narr_idx is not None and ln["persona"] == narr_idx
        clips = (ln.get("vista") or ("clips" if es_narr else "cara")) == "clips"      # Persona = su cara · Narrador = clips, salvo que se pida otra cosa
        if es_narr and not clips and (narrador["modo"] != "grabar"):
            avisos.append(f"Línea {ln['n']}: el narrador con voz de computadora/ElevenLabs no tiene cara; se muestran clips.")
            clips = True
        reg["vista"] = "clips" if clips else "cara"
        if es_narr and narrador["modo"] != "grabar":     # voz de la computadora o de ElevenLabs
            tn = Path(gd.DATOS) / "_tmp_hablado_n"
            tn.mkdir(parents=True, exist_ok=True)
            ext = ".mp3" if narrador["modo"] == "elevenlabs" else ".wav"
            dest = tn / f"narr_{ln['n']:03d}{ext}"
            _msg(f"Generando la voz del narrador (línea {ln['n']})…")
            total_a = _voz_narrador(" ".join(ln["palabras"]), dest, narrador) + 0.1
            ini_v, fin_v = gd.rango_voz(dest, total_a)
            al = gd.tiempos_con_pausas(ln["palabras"], gd._pausas_audio(dest, total_a), ini_v, fin_v)
            pal = [[w[0], w[1], w[2]] + ([ln["marcas"][i]] if i in ln["marcas"] else [None]) for i, w in enumerate(al)]
            tramos.append({"fi": None, "a": 0.0, "b": total_a, "persona": ln["persona"], "pal": pal, "clips": True, "audio": str(dest)})
            reg.update(estado="ok", fuente="voz del narrador", t=f"{total_a:.1f} s", puntaje=100)
        elif ln["persona"] is not None and por_persona.get(ln["persona"]):
            tomas = [(fi, trans[fi]) for fi in por_persona[ln["persona"]]]
            r = buscar_linea(ln["palabras"], tomas, variar)
            if r and r[0] >= 0.55:
                sc, fi, i0, i1 = r
                conocidas = {gd.normalizar(x) for x in ln["palabras"]}
                while i0 < i1 and gd.normalizar(trans[fi][i0][0]) not in conocidas:      # sin palabras de más en las orillas
                    i0 += 1
                while i1 > i0 and gd.normalizar(trans[fi][i1][0]) not in conocidas:
                    i1 -= 1
                trozo = trans[fi][i0:i1 + 1]
                al = gd.alinear(ln["palabras"], trozo)
                pal = [[w[0], w[1], w[2]] + ([ln["marcas"][i]] if i in ln["marcas"] else [None]) for i, w in enumerate(al)]
                a = max(0.0, trozo[0][1] - 0.12)
                b = min(durs[fi], trozo[-1][2] + 0.22)
                if es_narr and not clips and not _tiene_video(fuentes[fi]):
                    avisos.append(f"Línea {ln['n']}: el archivo del narrador no trae video; se muestran clips.")
                    clips = True
                    reg["vista"] = "clips"
                tramos.append({"fi": fi, "a": a, "b": b, "persona": ln["persona"], "pal": pal, "clips": clips})
                reg.update(estado="ok", fuente=fuentes[fi].name.split("_", 1)[-1], t=f"{a:.1f}–{b:.1f} s", puntaje=int(sc * 100))
            else:
                avisos.append(f"Línea {ln['n']} ({nombres[ln['persona']]}): no encontré esa frase en sus videos. Se omite; revisa que la haya dicho o cambia el texto.")
        resumen.append(reg)
    if not tramos:
        raise gd.ErrorMotor("No encontré ninguna línea del guion en los videos. Revisa que cada persona diga lo que dice el guion.")
    H.plan = {"fuentes": fuentes, "durs": durs, "tramos": tramos, "nombres": nombres}
    H.lineas, H.avisos = resumen, avisos
    _pct(100)
    _msg(f"Listo: {len(tramos)} de {len(resumen)} líneas encontradas.")


# ---------------------------------------------------------------- cortes
MULETILLAS = {"eh", "ehh", "eeh", "eeeh", "em", "emm", "eem", "mm", "mmm", "hmm", "hm", "uh", "um", "umm", "ah", "aah", "ahh", "uhm", "erm"}


def _es_muletilla(texto):
    return re.sub(r"[^\w]", "", str(texto).lower()) in MULETILLAS


def planear_cortes(palabras, dur, quitar_silencios=True, umbral=0.45, zoom=True, quitar_muletillas=False):
    """Devuelve (intervalos [(a,b,zoom_bool)], palabras_con_tiempos_nuevos)."""
    ws, corta_antes = [], set()
    for w in palabras:
        if not w[0].strip():
            continue
        if quitar_muletillas and _es_muletilla(w[0]):
            corta_antes.add(len(ws))          # la palabra siguiente empieza un tramo nuevo: la muletilla se queda fuera
            continue
        ws.append(list(w))
    if not ws:
        return [(0.0, dur, False, 0)], []
    if quitar_muletillas and not quitar_silencios:
        quitar_silencios = True
        umbral = 1e9                           # solo se corta donde había una muletilla
    ent, sal = 0.10, 0.18
    grupos, act = [], [0]
    for i in range(1, len(ws)):
        if quitar_silencios and (ws[i][1] - ws[i - 1][2] > umbral or i in corta_antes):
            grupos.append(act)
            act = []
        act.append(i)
    grupos.append(act)
    ints = []
    for g in grupos:
        a = max(0.0, ws[g[0]][1] - (0.03 if g[0] in corta_antes else ent))
        b = min(dur, ws[g[-1]][2] + (0.03 if (g[-1] + 1) in corta_antes else sal))
        if ints and a < ints[-1][1]:
            a = ints[-1][1]
        if b - a >= 0.15:
            ints.append([a, b, g])
    if not quitar_silencios:
        ints = [[0.0, dur, list(range(len(ws)))]]
    if zoom:                       # los tramos largos se parten en una palabra para alternar el zoom
        nuevo = []
        for a, b, g in ints:
            if b - a > 4.5 and len(g) >= 4:
                mid = (a + b) / 2
                k = min(range(1, len(g)), key=lambda j: abs(ws[g[j]][1] - mid))
                corte = (ws[g[k - 1]][2] + ws[g[k]][1]) / 2
                nuevo += [[a, corte, g[:k]], [corte, b, g[k:]]]
            else:
                nuevo.append([a, b, g])
        ints = nuevo
    out, rem, off = [], [], 0.0
    for n, (a, b, g) in enumerate(ints):
        out.append((a, b, bool(zoom and n % 2 == 1), 0))
        for i in g:
            rem.append([ws[i][0], off + max(0.0, ws[i][1] - a), off + min(b - a, ws[i][2] - a)] + list(ws[i][3:]))
        off += b - a
    return out, rem


def _cfg_para(estilo, formato, ajustes, pid=None):
    if pid:                                  # dentro de un producto: usa SU estilo, y solo cambia lo que se pida aquí
        carpeta = core.carpeta(pid)
        cfg = gd.cargar_config(carpeta)
    else:
        cfg = dict(gd.DEFECTOS)
    est = catalogo.ESTILOS_LISTOS.get(estilo)
    if est:
        cfg.update(est[4])
    if formato in catalogo.FORMATOS or not pid:
        cfg["formato_video"] = formato if formato in catalogo.FORMATOS else "vertical"
    gd.aplicar_formato(cfg)
    cfg.update(catalogo.PRESETS_FORMATO.get(cfg["formato_video"], {}))
    cfg["pantalla_completa"] = True
    gd.ajustar_pantalla_completa(cfg)
    for k, v in (ajustes or {}).items():
        if k in gd.DEFECTOS:
            cfg[k] = v
    return cfg


def _filtro_video(ints, W, H_, fps, zoom_f=1.14, chroma=None):
    """chroma = (color a quitar 0xRRGGBB, color del fondo nuevo 0xRRGGBB) o None."""
    p = []
    for i, (a, b, z, fi) in enumerate(ints):
        base = f"[{fi}:v]trim={a:.3f}:{b:.3f},setpts=PTS-STARTPTS,scale={W}:{H_}:force_original_aspect_ratio=increase,crop={W}:{H_},setsar=1"
        if z:
            base += f",scale={int(W * zoom_f) // 2 * 2}:{int(H_ * zoom_f) // 2 * 2},crop={W}:{H_}"
        d = b - a
        if chroma:                 # pantalla verde/azul: se quita ese color y se pone el fondo elegido
            p.append(base + f",setsar=1,fps={fps},format=yuva420p,chromakey={chroma[0]}:0.17:0.08[fg{i}]")
            if isinstance(chroma[1], tuple):         # fondo con una imagen o un clip del proyecto
                modo, ruta = chroma[1]
                esc = str(ruta).replace("\\", "/").replace(":", "\\:")
                esc = esc.replace("'", "")
                comun = f"scale={W}:{H_}:force_original_aspect_ratio=increase,crop={W}:{H_},setsar=1"
                if modo == "img":
                    p.append(f"movie='{esc}',{comun},loop=loop=-1:size=1,fps={fps},trim=duration={d + 0.05:.3f},setpts=PTS-STARTPTS[bg{i}]")
                else:
                    p.append(f"movie='{esc}':loop=0,{comun},fps={fps},trim=duration={d + 0.05:.3f},setpts=N/({fps}*TB)[bg{i}]")
            else:
                p.append(f"color=c={chroma[1]}:s={W}x{H_}:r={fps}:d={d + 0.05:.3f}[bg{i}]")
            p.append(f"[bg{i}][fg{i}]overlay=shortest=1:format=auto,format=yuv420p,setsar=1[v{i}]")
        else:
            p.append(base + f",setsar=1,fps={fps}[v{i}]")
        fa = min(0.012, d / 4)
        p.append(f"[{fi}:a]atrim={a:.3f}:{b:.3f},asetpts=PTS-STARTPTS,aresample=48000,aformat=channel_layouts=stereo,afade=t=in:d={fa:.3f},afade=t=out:st={max(0, d - fa):.3f}:d={fa:.3f}[a{i}]")
    n = len(ints)
    p.append("".join(f"[v{i}][a{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=1[vc][ac]")
    return p


def _pool_de(mat, tema):
    """El pool de clips de su tema; si no hay (carpeta vacía, [] o un tema que no existe), uno general del producto."""
    if tema in mat.pools:
        return tema, mat.pools[tema]
    if "general" in mat.pools:
        return "general", mat.pools["general"]
    if mat.todos.archivos:
        return "general", mat.todos
    return None, None


def planear_broll(cfg, rem, total, tmp, auto=True, mat=None, excluir=None):
    """Clips de las carpetas de temas encima del video (la voz sigue sonando).
    - Marcas puestas por la persona: la palabra lleva [tema] (o [tema 3] = 3 segundos) y justo ahí entra el clip.
    - Automático (si auto): cuando se dice una palabra de un tema de temas.txt.
    Devuelve [(t0, t1, ruta_mp4)]."""
    carpeta = Path(cfg["dir"])
    temas = gd.leer_temas(carpeta / "temas.txt")
    mat = mat or gd.Material(cfg, temas, [])
    excluir = excluir or []
    escena_max = float(cfg.get("escena_max", 3.5) or 3.5)
    largo_min = max(1.6, float(cfg.get("escena_min", 1.8) or 1.8))
    ventanas = []                                   # (t0, t1, tema, palabra)

    pool_de = lambda tema: _pool_de(mat, tema)

    def dur_azar(t0, pedida=None):
        d = float(pedida) if pedida else random.uniform(largo_min, max(largo_min, min(escena_max, 3.4)))
        return min(d, total - 0.5 - t0)

    for pal, a, _b, *extra in rem:                  # 1) las marcas manuales mandan
        marca = _clip_de(extra[0] if extra else None)
        if not marca:
            continue
        tema, seg = marca["tema"], marca["seg"]
        real, _pool = pool_de(tema)
        if real is None:
            _msg("  Aviso: el proyecto no tiene clips en ninguna carpeta; se omite la marca.")
            continue
        if real != tema:
            _msg(f"  La marca [{tema or 'general'}] no tiene clips propios: se usa un clip general del proyecto.")
            tema = real
        t0 = max(0.0, a - 0.05)
        d = dur_azar(t0, seg)
        if d >= 0.8:
            ventanas.append((t0, t0 + d, tema, pal))
    if auto:                                        # 2) los automáticos llenan lo que quede libre
        manual = list(ventanas)
        libre = 1.5
        for pal, a, _b, *extra in rem:
            if extra and _clip_de(extra[0]):
                continue
            if a < libre or a > total - 1.8:
                continue
            tema = gd.tema_de({k: v for k, v in temas.items() if k != "kit"}, [pal])
            if not tema or tema not in mat.pools:
                continue
            t0 = max(libre, a - 0.15)
            d = dur_azar(t0)
            if d < 1.0 or any(t0 < m1 + 0.5 and t0 + d > m0 - 0.5 for m0, m1, *_ in manual) \
                    or any(t0 < e1 and t0 + d > e0 for e0, e1 in excluir):
                continue
            ventanas.append((t0, t0 + d, tema, pal))
            libre = t0 + d + 2.5                    # entre un clip y otro se vuelve a ver a la persona
    ventanas.sort()
    res, fin_prev = [], 0.0
    for t0, t1, tema, pal in ventanas:
        t0 = max(t0, fin_prev)
        if t1 - t0 < 0.8:
            continue
        media = pool_de(tema)[1].elegir()
        seg = Path(tmp) / f"broll_{len(res):02d}.mp4"
        cfg_b = dict(cfg)
        cfg_b["media_alto"] = cfg["alto"]
        gd.crear_segmento(cfg_b, media, t1 - t0, "cover", gd.elegir_efecto(cfg, "cover"), 0, seg)
        _msg(f"  clip «{tema}» con «{str(pal).strip('.,;:!?')}» ({t0:.1f}s)")
        res.append((t0, t1, seg))
        fin_prev = t1
    return res


def _sin_ocultas(rem):
    """Las palabras de frases marcadas con -sub no salen en los subtítulos."""
    ocultas, res = 0, []
    for w in rem:
        for m in (w[3] if len(w) > 3 and w[3] else []):
            if m.get("t") == "fx" and not m.get("sub", True) and m.get("n"):
                ocultas = max(ocultas, m["n"])
        if ocultas > 0:
            ocultas -= 1
            continue
        res.append(w)
    return res


def _ruta_material(cfg, nombre):
    """Una imagen de la carpeta «Imágenes del proyecto» (kit) por su nombre."""
    base = (Path(cfg["dir"]) / "kit").resolve()
    p = (base / Path(str(nombre)).name).resolve()
    return p if p.is_file() and base in p.parents and p.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp") else None


def _archivo_fondo(cfg, nombre):
    """Imagen o video de «Imágenes del proyecto» para usar de fondo con el chroma: (modo, ruta) o None."""
    nombre = str(nombre or "").strip()
    if not nombre:
        return None
    base = (Path(cfg["dir"]) / "kit").resolve()
    p = (base / Path(nombre).name).resolve()
    if not (p.is_file() and base in p.parents):
        _msg(f"  Aviso: no encontré «{nombre}» para el fondo; se usa el color.")
        return None
    ext = p.suffix.lower()
    if ext in (".png", ".jpg", ".jpeg", ".webp", ".bmp"):
        return ("img", p)
    if ext in (".mp4", ".mov", ".m4v", ".webm", ".mkv", ".gif"):
        return ("vid", p)
    return None


FIGURAS = ("flecha", "circulo", "subrayado", "destello")


def _collage(img, rutas, W, H_, y0, y1, pct):
    """Una imagen, o hasta 4 juntas en cuadrícula (collage), dentro de la zona pedida."""
    from PIL import Image
    ims = [Image.open(r).convert("RGBA") for r in rutas]
    n = len(ims)
    cols = 1 if n == 1 else 2
    filas = (n + cols - 1) // cols
    zona_w = int(W * pct / 100)
    gap = int(W * 0.02)
    celda = (zona_w - gap * (cols - 1)) // cols
    zona_h = int(H_ * (y1 - y0))
    alto_c = min(celda, (zona_h - gap * (filas - 1)) // filas) if n > 1 else None
    tiles = []
    for im in ims:
        if n == 1:
            im = im.resize((zona_w, max(1, int(im.height * zona_w / im.width))))
        else:
            k = min(celda / im.width, alto_c / im.height)
            im = im.resize((max(1, int(im.width * k)), max(1, int(im.height * k))))
        tiles.append(im)
    alto_tot = sum(max(t.height for t in tiles[i:i + cols]) for i in range(0, n, cols)) + gap * (filas - 1)
    y = max(0, min(H_ - alto_tot, int(H_ * (y0 + y1) / 2) - alto_tot // 2))
    for f in range(filas):
        fila = tiles[f * cols:(f + 1) * cols]
        ancho_f = sum(t.width for t in fila) + gap * (len(fila) - 1)
        x = (W - ancho_f) // 2
        alto_f = max(t.height for t in fila)
        for t_ in fila:
            img.alpha_composite(t_, (x, y + (alto_f - t_.height) // 2))
            x += t_.width + gap
        y += alto_f + gap


def _dibujar_figura(img, fig, color, W, H_, y0, y1):
    """Flecha, círculo, subrayado o destello dibujados encima del video (en la zona pedida)."""
    from PIL import ImageDraw
    import math
    d = ImageDraw.Draw(img)
    cx, cy = W // 2, int(H_ * (y0 + y1) / 2)
    g = max(8, W // 70)
    if fig == "circulo":
        r = int(W * 0.22)
        d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=color, width=g)
    elif fig == "subrayado":
        d.rounded_rectangle((int(W * 0.15), cy, int(W * 0.85), cy + g * 2), radius=g, fill=color)
    elif fig == "flecha":
        h_ = int(W * 0.28)
        d.rectangle((cx - g, cy - h_, cx + g, cy), fill=color)
        d.polygon([(cx - g * 4, cy - 1), (cx + g * 4, cy - 1), (cx, cy + g * 6)], fill=color)
    else:                                              # destello (estrella de 8 puntas)
        pts = []
        for i in range(16):
            a = math.pi * i / 8
            r = int(W * (0.2 if i % 2 == 0 else 0.07))
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
        d.polygon(pts, fill=color)


def zona_marca(cfg, m, tipo):
    """Zona vertical (fracciones de la altura) de una marca: la que pidió con «pos», o la que se dejó en Estilo (marca_y / marca_img_y)."""
    if m.get("pos") in POSICIONES:
        return POSICIONES[m["pos"]]
    yc = float(cfg.get("marca_img_y" if tipo == "img" else "marca_y", 47) or 47) / 100
    return (max(0.0, yc - 0.11), min(1.0, yc + 0.11))


def _desplazar_x(img, dx):
    if not dx:
        return img
    from PIL import Image
    nuevo = Image.new("RGBA", img.size, (0, 0, 0, 0))
    nuevo.paste(img, (dx, 0), img)
    return nuevo


def planear_textos(cfg, rem, total, tmp):
    """Frases marcadas con texto en pantalla y/o sonido pop. Devuelve ([(png, t0, t1, animación)], [segundos de cada pop])."""
    from PIL import Image, ImageDraw
    import generar_video as gv
    W, H_ = int(cfg["ancho"]), int(cfg["alto"])
    textos, pops = [], []
    for i, w in enumerate(rem):
        for m in (w[3] if len(w) > 3 and w[3] else []):
            if m.get("t") != "fx" or not (m.get("txt") or m.get("pop") or m.get("img") or m.get("fig")):
                continue
            n = int(m.get("n") or 0)
            if n:
                t0 = w[1]
                fin = rem[min(len(rem) - 1, i + n - 1)][2]
                dur = float(m["seg"]) if m.get("seg") else max(1.8, fin - t0 + 0.5)
            else:
                t0 = w[1] if m.get("antes") else w[2]
                dur = float(m["seg"]) if m.get("seg") else 2.4
            t0 = max(0.0, min(t0, total - 0.8))
            t1 = min(total, t0 + dur)
            if m.get("pop"):
                pops.append(t0)
            quiere_img = bool(m.get("img"))
            if not ((m.get("txt") and m.get("texto")) or quiere_img or m.get("fig")):
                continue
            y0, y1 = zona_marca(cfg, m, "img" if (quiere_img or m.get("fig")) else "txt")
            ty0, ty1 = zona_marca(cfg, m, "txt")
            img = Image.new("RGBA", (W, H_), (0, 0, 0, 0))
            if quiere_img:
                nombres = [x for x in str(m["img"]).split("+") if x][:4]
                rutas = [(_ruta_material(cfg, x), x) for x in nombres]
                for r_, x_ in rutas:
                    if r_ is None:
                        _msg(f"  Aviso: no encontré «{x_}» en las imágenes del proyecto; se omite.")
                rutas = [r_ for r_, _x in rutas if r_ is not None]
                if rutas:
                    try:
                        _collage(img, rutas, W, H_, y0, y1, int(m["tam"]) if m.get("tam") and m.get("tam") <= 100 else int(float(cfg.get("marca_img_pct", 55) or 55)))
                    except Exception as e:
                        _msg(f"  Aviso: no pude abrir las imágenes ({e}).")
            if m.get("fig"):
                _dibujar_figura(img, m["fig"], m.get("color") or "#FFD400", W, H_, y0, y1)
            if quiere_img or m.get("fig"):
                img = _desplazar_x(img, int(float(cfg.get("marca_img_x", 0) or 0)))
            if m.get("txt") and m.get("texto") and not (quiere_img and not m.get("txt")):
                capa_t = Image.new("RGBA", (W, H_), (0, 0, 0, 0))
                tam_t = int(m.get("tam") if (m.get("tam") and not quiere_img) else (int(float(cfg.get("marca_tam", 0) or 0)) or cfg["tam_texto_arriba"]))
                gv.dibujar_en_zona(ImageDraw.Draw(capa_t), cfg, m["texto"], (60, int(H_ * ty0), W - 60, int(H_ * ty1)),
                                   tam_t, m.get("color") or cfg["color_texto"],
                                   trazo=int(cfg["trazo_titulo"]), elemento="titulo", trazo_color=cfg["color_trazo"])
                img.alpha_composite(_desplazar_x(capa_t, int(float(cfg.get("marca_x", 0) or 0))))
            png = Path(tmp) / f"texto_{len(textos):02d}.png"
            img.save(png)
            textos.append((png, t0, t1, {"entrada": m.get("efecto") or "fundido", "salida": "fundido"}))
    return textos, pops


def planear_burbujas(cfg, rem, total, tmp):
    """Burbujas de WhatsApp puestas con [yo: texto] / [cliente: texto]: salen justo al terminar la palabra marcada.
    Se dibujan con el Estilo del producto. Devuelve [(png, t0, t1, item)]."""
    items = []
    _e, _s = str(cfg.get("burbuja_entrada") or ""), str(cfg.get("burbuja_salida") or "")
    ent_g, sal_g = ("" if _e in ("", "normal") else _e), ("" if _s in ("", "normal") else _s)
    est_g = {"brillo": True} if gd.es_si(cfg.get("burbuja_brillo", False)) else None
    dx_g = int(float(cfg.get("burbuja_x") or 0))
    dur = max(1.5, float(cfg.get("burbuja_silenciosa_seg", 3) or 3))
    for pal, a, b, *extra in rem:
        for m in (extra[0] if extra and extra[0] else []):
            if m["t"] != "burb" or not m["texto"]:
                continue
            t0 = min(b, total - 0.6)
            if t0 < 0:
                continue
            frase = ("Cliente: " + m["texto"]) if m["lado"] == "cliente" else m["texto"]
            items.append({"frase": frase, "t0": t0, "t1": min(total, t0 + dur), "mover": 0, "mover_x": dx_g, "estilo": est_g,
                          "entrada": ent_g or "subir", "salida": sal_g, "sonido": ""})
    items.sort(key=lambda x: x["t0"])
    for k, it in enumerate(items):                                   # el cliente se queda mientras contestas
        if gd._es_cliente(it["frase"])[0] and k + 1 < len(items) and not gd._es_cliente(items[k + 1]["frase"])[0]:
            it["t1"] = max(it["t1"], items[k + 1]["t1"])
    res = []
    if items:
        for it in items:
            gd.ajustar_item_burbuja(cfg, it)
        for k, (it, y1) in enumerate(zip(items, gd.colocar_burbujas(cfg, items))):
            png = Path(tmp) / f"burb_{k:02d}.png"
            gd.crear_burbuja(cfg, it["frase"], png, y1, it.get("estilo"), it.get("mover_x", 0))
            res.append((png, it["t0"], it["t1"], it))
    return res


def _cfg_opciones(opciones):
    pid = opciones.get("pid") or None
    return _cfg_para(opciones.get("estilo") or ("" if pid else "viral"), opciones.get("formato") or ("" if pid else "vertical"), opciones.get("ajustes"), pid)


def _palabra_a_marca(w):
    """[txt, a, b, 'ciudad 3'] (del texto que corrigió la persona) -> [txt, a, b, ('ciudad', 3.0)]"""
    w = list(w)
    if len(w) > 3 and isinstance(w[3], str):
        w[3] = _marcas_de_texto(w[3])
    return w


def crear(video, palabras, opciones):
    """Un solo video (la persona, o varias juntas). opciones: pid, estilo, formato, quitar_silencios, umbral, zoom, broll, ajustes, nombre."""
    video = Path(video)
    dur = _duracion(video)
    ints, rem = planear_cortes([_palabra_a_marca(w) for w in palabras], dur, bool(opciones.get("quitar_silencios", True)),
                               float(opciones.get("umbral", 0.45)), bool(opciones.get("zoom", True)), bool(opciones.get("quitar_muletillas", False)))
    _msg(f"{len(ints)} cortes, el video queda de {sum(b - a for a, b, *_ in ints):.1f}s (antes {dur:.1f}s).")
    return _render([video], ints, rem, opciones, video.stem, opciones.get("cfg"), opciones.get("mat"))


def _escena_narrador(cfg, mat, temas, t, fuentes, tmp, k):
    """Voz del narrador + clips de las carpetas del producto (según las marcas [tema] y las palabras clave). Devuelve (mp4, duración)."""
    a, b = t["a"], t["b"]
    d = b - a
    origen = t.get("audio") or str(fuentes[t["fi"]])
    ss = 0.0 if t.get("audio") else a
    ws = [(w[0], max(0.0, w[1] - a), min(d, w[2] - a), (w[3] if len(w) > 3 else None)) for w in t["pal"]]
    trozos, ini, cur = [], 0.0, []
    for w in ws:
        cur.append(w)
        if w[2] - ini >= 3.2 or (w[0][-1:] in ".!?" and w[2] - ini >= 1.6):
            trozos.append([ini, w[2], cur])
            ini, cur = w[2], []
    if cur:
        if trozos and d - ini < 1.2:
            trozos[-1][1], trozos[-1][2] = d, trozos[-1][2] + cur
        else:
            trozos.append([ini, d, cur])
    if not trozos:
        trozos = [[0.0, d, []]]
    trozos[-1][1] = d
    temas_k = {x: v for x, v in temas.items() if x != "kit"}
    cfg_b = dict(cfg, media_alto=cfg["alto"])
    lo, hi = sorted((cfg["oscurecer_min"], cfg["oscurecer_max"]))
    segs = []
    for j, (t0, t1, pals) in enumerate(trozos):
        marca = next((c for c in (_clip_de(p[3]) for p in pals if p[3]) if c), None)
        tema = marca["tema"] if marca else gd.tema_de(temas_k, [p[0] for p in pals]) or ""
        real, pool = _pool_de(mat, tema)
        if pool is None:
            raise gd.ErrorMotor("Para la narración hacen falta clips en el proyecto (carpetas de «Clips y palabras clave»).")
        seg = Path(tmp) / f"nar_{k:02d}_{j:02d}.mp4"
        gd.crear_segmento(cfg_b, pool.elegir(), max(0.3, t1 - t0), "cover", gd.elegir_efecto(cfg, "cover"), random.uniform(lo, hi) / 100.0, seg)
        segs.append(seg)
    lista = Path(tmp) / f"nar_{k:02d}.txt"
    lista.write_text("".join(f"file '{p.name}'\n" for p in segs), encoding="utf-8")
    sal = Path(tmp) / f"narrador_{k:02d}.mp4"
    kw = {"creationflags": 0x08000000} if os.name == "nt" else {}
    r = subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(lista), "-ss", f"{ss:.3f}", "-t", f"{d:.3f}", "-i", origen,
                        "-map", "0:v", "-map", "1:a:0", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2", "-shortest", str(sal)],
                       capture_output=True, text=True, **kw)
    if r.returncode != 0 or not sal.exists():
        raise gd.ErrorMotor("No se pudo preparar la escena del narrador: " + r.stderr[-200:])
    return sal, _duracion(sal)


def _trocear(a, b, pal):
    """Quita del tramo [a, b] las frases marcadas con «corta». Devuelve [(desde, hasta, palabras)] de lo que se queda."""
    cortes = []
    for i, w in enumerate(pal):
        for m in (w[3] if len(w) > 3 and w[3] else []):
            if m.get("t") == "fx" and m.get("corta") and m.get("n"):
                j = min(len(pal) - 1, i + m["n"] - 1)
                cortes.append((max(a, w[1] - 0.04), min(b, pal[j][2] + 0.06), i, j))
    if not cortes:
        return [(a, b, list(pal))]
    cortes.sort()
    res, ini, k0 = [], a, 0
    for c0, c1, i, j in cortes:
        if c1 <= ini:
            continue
        pals = [w for n, w in enumerate(pal) if k0 <= n < i]
        if c0 - ini >= 0.25:
            res.append((ini, c0, pals))
        ini, k0 = c1, j + 1
    pals = [w for n, w in enumerate(pal) if n >= k0]
    if b - ini >= 0.25:
        res.append((ini, b, pals))
    return res or [(a, b, list(pal))]


def crear_conv(opciones):
    """Conversación: une, en el orden del guion, el pedazo de cada persona que dice cada línea. Las líneas del narrador
    llevan su voz sobre clips del producto."""
    plan = H.plan
    if not plan:
        raise gd.ErrorMotor("Primero analiza el guion y los videos.")
    zoom = bool(opciones.get("zoom", True))
    colores = bool(opciones.get("color_personas", True))
    pid = opciones.get("pid") or None
    cfg = opciones.get("cfg") or _cfg_opciones(opciones)
    hay_narr = any(t.get("clips") for t in plan["tramos"])
    if hay_narr and not pid:
        raise gd.ErrorMotor("Para mostrar clips mientras alguien habla (narrador o «(clips)») hace falta un proyecto con clips.")
    temas, mat = {}, None
    if pid:
        temas = gd.leer_temas(Path(cfg["dir"]) / "temas.txt")
        mat = opciones.get("mat") or gd.Material(cfg, temas, [])
    tmp_n = Path(gd.DATOS) / "_tmp_hablado_ne"
    shutil.rmtree(tmp_n, ignore_errors=True)
    tmp_n.mkdir(parents=True)
    try:
        fuentes = [Path(f) for f in plan["fuentes"]]
        ints, rem, excluir, off = [], [], [], 0.0
        for k, t in enumerate(plan["tramos"]):
            col = COLORES_PERSONAS[t["persona"] % len(COLORES_PERSONAS)] if colores else None
            if t.get("clips"):
                H.fase, H.pct = "render", min(40, 2 + k * 3)
                esc, d = _escena_narrador(cfg, mat, temas, t, fuentes, tmp_n, k)
                fuentes.append(esc)
                a, b, z, fi = 0.0, d, False, len(fuentes) - 1
                for w in t["pal"]:
                    rem.append([w[0], off + max(0.0, w[1] - t["a"]), off + min(d, w[2] - t["a"]), ([m for m in w[3] if m["t"] in ("burb", "fx")] or None) if len(w) > 3 and w[3] else None, col])      # los clips ya van en la escena; las burbujas se dibujan encima
                excluir.append((off, off + d))
            else:
                a, b, z, fi = t["a"], t["b"], bool(zoom and k % 2 == 1), t["fi"]
                tr = _trocear(a, b, t["pal"])
                for sa, sb, pals in tr:
                    for w in pals:
                        rem.append([w[0], off + max(0.0, w[1] - sa), off + min(sb - sa, w[2] - sa), w[3] if len(w) > 3 else None, col])
                    ints.append((sa, sb, z, fi))
                    off += sb - sa
                continue
            ints.append((a, b, z, fi))
            off += b - a
        _msg(f"{len(ints)} partes unidas en el orden del guion ({off:.1f} s).")
        return _render(fuentes, ints, rem, opciones, opciones.get("nombre") or "conversacion", cfg, mat, excluir)
    finally:
        shutil.rmtree(tmp_n, ignore_errors=True)


def _render(fuentes, ints, rem, opciones, nombre_base, cfg=None, mat=None, excluir=None):
    import planes
    externo = bool(opciones.get("externo"))          # lo genera la pestaña Generar: ella pone el nombre, cuenta el video y guarda el historial
    if not externo:
        msg = planes.revisar_videos(1)
        if msg:
            raise gd.ErrorMotor(msg)
    pid = opciones.get("pid") or None
    cfg = cfg or opciones.get("cfg") or _cfg_opciones(opciones)
    W, H_, fps = int(cfg["ancho"]), int(cfg["alto"]), int(cfg.get("fps", 30) or 30)
    H.fase, H.pct, H.base, H.span = "render", 2, 0, 100
    total = sum(b - a for a, b, *_ in ints)
    video = Path(nombre_base)
    tmp = Path(gd.DATOS) / "_tmp_hablado_r"
    shutil.rmtree(tmp, ignore_errors=True)
    tmp.mkdir(parents=True)
    try:
        cmd = ["ffmpeg", "-y", "-v", "error"]
        for f in fuentes:
            cmd += ["-i", str(f)]
        nf = len(fuentes)
        lista = gd.crear_subtitulos(cfg, _sin_ocultas(rem), total, tmp)
        cmd += ["-f", "concat", "-safe", "0", "-i", str(lista)]
        marca = None
        if planes.limites().get("marca_agua"):
            marca = gd.crear_marca_agua(cfg, tmp)
            cmd += ["-loop", "1", "-framerate", str(fps), "-i", str(marca)]
        broll = planear_broll(cfg, rem, total, tmp, bool(opciones.get("broll", True)), mat, excluir) if pid else []
        if broll:
            _msg(f"{len(broll)} clips de tus carpetas entran en el video.")
        burbs = planear_burbujas(cfg, rem, total, tmp)
        if burbs:
            _msg(f"{len(burbs)} burbuja(s) de WhatsApp.")
        textos, pops = planear_textos(cfg, rem, total, tmp)
        if textos:
            _msg(f"{len(textos)} texto(s) en pantalla.")
            burbs = sorted(burbs + textos, key=lambda x: x[1])
        _ck = {"verde": "0x00FF00", "azul": "0x0000FF"}.get(str(cfg.get("chroma_quitar") or ""))
        _fondo = "0x" + (re.sub(r"[^0-9a-fA-F]", "", str(cfg.get("chroma_fondo") or "")) or "101830")[:6].ljust(6, "0")
        _arch = _archivo_fondo(cfg, cfg.get("chroma_archivo"))
        partes = _filtro_video(ints, W, H_, fps, chroma=(_ck, _arch or _fondo) if _ck else None)
        sig = nf + (2 if marca else 1)
        ult = "vc"
        for k, (t0, t1, seg) in enumerate(broll):               # clips de las carpetas, encima del video, con la voz de la persona
            cmd += ["-i", str(seg)]
            partes.append(f"[{sig}:v]setpts=PTS-STARTPTS+{t0:.3f}/TB,format=yuva420p,"
                          f"fade=t=in:st={t0:.3f}:d=0.12:alpha=1,fade=t=out:st={t1 - 0.12:.3f}:d=0.12:alpha=1[b{k}]")
            partes.append(f"[{ult}][b{k}]overlay=0:0:eof_action=pass:enable='between(t,{t0:.3f},{t1:.3f})'[o{k}]")
            ult = f"o{k}"
            sig += 1
        for j, (png, t_ini, t_fin, it_b) in enumerate(burbs):    # burbujas de WhatsApp (mismas animaciones que en los guiones)
            cmd += ["-loop", "1", "-framerate", str(fps), "-i", str(png)]
            ent, sal = it_b.get("entrada") or "ninguna", it_b.get("salida") or "ninguna"
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
            fuente_b = f"{sig}:v"
            if filtros:
                partes.append(f"[{sig}:v]format=rgba,{','.join(filtros)}[bu{j}]")
                fuente_b = f"bu{j}"
            partes.append(f"[{ult}][{fuente_b}]overlay=x='{'+'.join(fx) or '0'}':y='{'+'.join(fy) or '0'}':"
                          f"enable='between(t,{t_ini:.3f},{t_fin:.3f})'[d{j}]")
            ult = f"d{j}"
            sig += 1
        if externo:       # lo de la pestaña Capas (logo fijo), el título arriba y la frase final, como en los demás guiones
            ruta_g = Path(opciones["capas_de"]) if opciones.get("capas_de") else Path(tmp) / "x.txt"
            cfg_t, dx_t = gd.aplicar_estilo_titulo(cfg, gd.leer_estilo_titulo(ruta_g))
            capas = gd.crear_capas(cfg_t, opciones.get("gancho") or "", cfg["cta"], tmp, dx_t)
            t_tit, t_cta = float(cfg["titulo_segundos"]), float(cfg["cta_segundos"])
            mov = gd.es_si(cfg["movimiento"])
            if capas.get("base") is not None:
                cmd += ["-loop", "1", "-framerate", str(fps), "-i", str(capas["base"])]
                partes.append(f"[{ult}][{sig}:v]overlay=0:0[cb]")
                ult = "cb"
                sig += 1
            if t_tit > 0 and opciones.get("gancho"):
                cmd += ["-loop", "1", "-framerate", str(fps), "-i", str(capas["titulo"])]
                y_tit = ":y='-420*pow(max(0,1-t/0.45),2)'" if mov else ":y=0"
                partes.append(f"[{ult}][{sig}:v]overlay=x=0{y_tit}:enable='lt(t,{t_tit})'[ct]")
                ult = "ct"
                sig += 1
            if t_cta > 0 and str(cfg.get("cta") or "").strip():
                cmd += ["-loop", "1", "-framerate", str(fps), "-i", str(capas["cta"])]
                t0c = max(0.0, total - t_cta)
                y_cta = f":y='220*pow(max(0,1-(t-{t0c:.3f})/0.45),2)'" if mov else ":y=0"
                partes.append(f"[{ult}][{sig}:v]overlay=x=0{y_cta}:enable='gte(t,{t0c:.3f})'[cc]")
                ult = "cc"
                sig += 1
        partes.append(f"[{nf}:v]fps={fps},format=rgba[sub]")
        partes.append(f"[{ult}][sub]overlay={int(float(cfg.get('subs_x', 0) or 0))}:{int(cfg['subs_y']) - gd.ALTO_BANDA_SUBS // 2}[e1]")
        ult = "e1"
        if marca:
            partes.append(f"[{nf + 1}:v]format=rgba[mk]")
            partes.append(f"[{ult}][mk]overlay=x=(W-w)/2:y=H-h-{int(H_ * 0.045)}[e2]")
            ult = "e2"
        partes.append(f"[{ult}]format=yuv420p[vf]")
        amap = "[ac]"
        if pops:                                              # sonidos «pop» de las frases marcadas, mezclados con la voz
            expr = "+".join(f"between(t,{t:.3f},{t + 0.25:.3f})*0.5*sin(2*PI*(650+1700*exp(-max(0,t-{t:.3f})*55))*max(0,t-{t:.3f}))*exp(-max(0,t-{t:.3f})*26)" for t in pops)
            cmd += ["-f", "lavfi", "-t", f"{total:.3f}", "-i", f"aevalsrc='{expr}':s=48000:c=stereo"]
            partes.append(f"[ac][{sig}:a]amix=inputs=2:duration=first:dropout_transition=0,volume=2,alimiter=limit=0.95[acx]")
            amap = "[acx]"
            sig += 1
        base = re.sub(r"[^\w\- ]", "", opciones.get("nombre") or video.stem)[:40].strip() or "video"
        if opciones.get("destino"):
            destino = Path(opciones["destino"])
            destino.parent.mkdir(parents=True, exist_ok=True)
        elif pid:                        # dentro del producto: aparece en su pestaña «Videos»
            sal = core.carpeta(pid) / "videos_finalizados" / cfg["formato_video"]
            sal.mkdir(parents=True, exist_ok=True)
            n = sum(1 for _ in sal.glob("video_hablado_*.mp4")) + 1
            destino = sal / f"video_hablado_{n:03d}_{base}.mp4"
            while destino.exists():
                n += 1
                destino = sal / f"video_hablado_{n:03d}_{base}.mp4"
        else:
            sal = carpeta_salida()
            destino = sal / f"{base}_subtitulado.mp4"
            k = 2
            while destino.exists():
                destino = sal / f"{base}_subtitulado_{k}.mp4"
                k += 1
        parte = destino.with_name(destino.stem + ".parte")
        cmd += ["-filter_complex", ";".join(partes), "-map", "[vf]", "-map", amap, "-t", f"{total:.3f}",
                "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-c:a", "aac", "-b:a", "192k",
                "-movflags", "+faststart", "-f", "mp4", "-progress", "pipe:1", "-nostats", str(parte)]
        kw = {"creationflags": 0x08000000} if os.name == "nt" else {}
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, errors="replace", **kw)
        err = []
        threading.Thread(target=lambda: err.append(p.stderr.read()), daemon=True).start()
        for linea in p.stdout:
            if _cancelado():
                p.kill()
                raise gd.Cancelado()
            if linea.startswith("out_time_ms="):
                try:
                    H.pct = max(H.pct, min(98, int(int(linea.split("=")[1]) / 1e6 / total * 100)))
                except (ValueError, ZeroDivisionError):
                    pass
        p.wait()
        if p.returncode != 0:
            try:
                parte.unlink()
            except OSError:
                pass
            raise gd.ErrorMotor("No se pudo crear el video: " + ("".join(err))[-300:])
        os.replace(parte, destino)
        if externo:
            H.resultado = destino.name
            return destino
        planes.sumar_video()
        if pid and opciones.get("quien") is not None:
            try:
                core.registrar_historial(pid, {"archivo": destino.relative_to(core.carpeta(pid) / "videos_finalizados").as_posix(), "nombre": destino.name,
                                               "formato": cfg["formato_video"], "medidas": f"{W}x{H_}", "guion": "(video hablado)"}, opciones["quien"])
            except Exception:
                pass
        H.pct = 100
        H.resultado = destino.name
        _msg("Listo: " + destino.name)
        return destino
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def tarea_crear(video, palabras, opciones):
    crear(video, palabras, opciones)


def tarea_crear_conv(opciones):
    crear_conv(opciones)


# ---------------------------------------------------------------- «Mis videos hablando»: lo que se guarda en cada producto
EXT_AUDIO_N = {".wav", ".mp3", ".m4a", ".ogg", ".opus", ".aac", ".flac", ".webm"}
NARRADOR_CARPETA = "Narrador"
CONFIG_H = {"narrador": {"modo": "", "voz": "", "velocidad": 0, "elVoz": ""}, "silencios": True, "muletillas": True, "zoom": True, "broll": True, "colores": True, "usar": True}


def carpeta_hablando(carpeta):
    return Path(carpeta) / "hablando"


def _nombre_seguro(n, defecto="Presentador"):
    n = re.sub(r'[<>:"/\\|?*\x00-\x1f.]+', "_", str(n or "")).strip(" _")[:40]
    return n or defecto


def leer_config_h(carpeta):
    cfg = json.loads(json.dumps(CONFIG_H))
    try:
        d = json.loads((carpeta_hablando(carpeta) / "config.json").read_text(encoding="utf-8"))
        for k, v in d.items():
            if k == "narrador" and isinstance(v, dict):
                cfg["narrador"].update(v)
            elif k in cfg:
                cfg[k] = v
    except Exception:
        pass
    return cfg


def guardar_config_h(carpeta, d):
    base = carpeta_hablando(carpeta)
    base.mkdir(parents=True, exist_ok=True)
    cfg = leer_config_h(carpeta)
    for k, v in (d or {}).items():
        if k == "narrador" and isinstance(v, dict):
            cfg["narrador"].update({a: v[a] for a in v if a in cfg["narrador"]})
        elif k in cfg and k != "narrador":
            cfg[k] = v
    (base / "config.json").write_text(json.dumps(cfg, ensure_ascii=False, indent=1), encoding="utf-8")
    return cfg


def _natural(p):
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", Path(p).name)]


def _archivos(d, ext):
    if not d.is_dir():
        return []
    return sorted([f for f in d.iterdir() if f.is_file() and f.suffix.lower() in ext and not f.name.startswith(".")], key=_natural)


def listar_hablando(carpeta):
    base = carpeta_hablando(carpeta)
    personas = []
    if base.is_dir():
        for d in sorted([x for x in base.iterdir() if x.is_dir() and not x.name.startswith(".") and x.name != NARRADOR_CARPETA], key=_natural):
            personas.append({"nombre": d.name, "archivos": [{"nombre": f.name, "mb": round(f.stat().st_size / 1e6, 1)} for f in _archivos(d, EXT_VIDEO)]})
    narr = [{"nombre": f.name, "mb": round(f.stat().st_size / 1e6, 1)} for f in _archivos(base / NARRADOR_CARPETA, EXT_VIDEO | EXT_AUDIO_N)]
    return {"personas": personas, "narrador_archivos": narr, "config": leer_config_h(carpeta)}


def hay_hablando(carpeta):
    return any(p["archivos"] for p in listar_hablando(carpeta)["personas"])


# ---------------------------------------------------------------- Generar con tus videos hablando
def _guiones_texto(carpeta):
    """Guiones con texto del producto (los .txt de la pestaña Guion) que no estén apagados."""
    gdir = Path(carpeta) / "guiones"
    if not gdir.is_dir():
        return []
    apag = gd.guiones_apagados(gdir)
    apag_stems = {Path(n).stem for n in apag}
    out = []
    for f in sorted(gdir.glob("*.txt"), key=_natural):
        if f.name.startswith("_") or f.stem in apag_stems:
            continue
        if _texto_guion(f).strip():
            out.append(f)
    return out


def _texto_guion(f):
    t = Path(f).read_text(encoding="utf-8", errors="replace")
    lin = [l for l in t.splitlines() if not l.strip().startswith("#")]
    t = "\n".join(lin)
    t = re.sub(r"\(\s*[*/]\s*\d{1,2}\s*\)", " ", t)           # marcas viejas de burbujas (*1) (/2)
    t = re.sub(r"(?<![\w/*])[*/]\d{1,2}(?![\w/*])", " ", t)
    return t


def _etiquetar(texto, nombres):
    """Si una línea no dice quién habla, la dice la primera persona (así un guion normal sirve para un solo video)."""
    claves = {gd.normalizar(n) for n in nombres}
    salida = []
    for l in texto.splitlines():
        if not l.strip():
            continue
        m = re.match(r"^\s*([^:\[\]()]{1,40}?)\s*(?:\([^)]*\))?\s*:", l)
        k = gd.normalizar(m.group(1)) if m else ""
        if m and (k in claves or (k.isdigit() and 1 <= int(k) <= len(nombres)) or any(k == gd.normalizar(n).replace("persona", "") for n in nombres)):
            salida.append(l)
        else:
            salida.append(f"{nombres[0]}: {l.strip()}")
    return "\n".join(salida)


def _guiones_solo_texto(carpeta):
    """Guiones que son solo texto (sin audio) en la pestaña Guion: con «Mis videos hablando» cada uno cuenta como un guion más."""
    gdir = Path(carpeta) / "guiones"
    if not gdir.is_dir():
        return []
    audios = {f.stem for f in gdir.iterdir() if f.suffix.lower() in gd.AUDIO_EXT}
    return [f for f in sorted(gdir.glob("*.txt"), key=_natural) if not f.name.startswith("_") and f.stem not in audios and _texto_guion(f).strip()]


def entradas_hablando(carpeta):
    """Lo que cuenta como «guion» cuando el producto tiene videos hablando: cada guion de solo texto; si no hay ninguno,
    cada video de la primera persona (se edita tal cual). Entran en la misma vuelta de guiones que los de voz."""
    import planes
    carpeta = Path(carpeta)
    if not planes.limites().get("hablado"):
        return []
    info = listar_hablando(carpeta)
    personas = [p for p in info["personas"] if p["archivos"]]
    if not personas or not info["config"].get("usar", True):
        return []
    textos = _guiones_solo_texto(carpeta)
    if textos:
        return textos
    return [carpeta_hablando(carpeta) / personas[0]["nombre"] / a["nombre"] for a in personas[0]["archivos"]]


def es_entrada(g):
    g = Path(g)
    return g.suffix.lower() == ".txt" or g.parent.parent.name == "hablando"


def duracion_entrada(g):
    g = Path(g)
    if g.suffix.lower() == ".txt":
        return max(5.0, len(_texto_guion(g).split()) / 2.6)
    return _duracion(g)


def preparar_entrada(carpeta, g, cfg, mostrar, lim_c=None):
    """Escucha tus videos y arma el plan de ESTE video (cada vez sale distinto: tomas, zoom, clips). Devuelve el plan."""
    import planes
    carpeta, g = Path(carpeta), Path(g)
    if estado_motor()["motor"] is None:
        raise gd.ErrorMotor("Falta el motor de reconocimiento de voz. Instala la versión más reciente de Vibovapp.")
    info = listar_hablando(carpeta)
    personas = [p for p in info["personas"] if p["archivos"]]
    ch = info["config"]
    idioma = usuarios.idioma()
    H.reset()
    H.activo = True
    try:
        ctx = {"g": g, "ch": ch, "tipo": "script" if g.suffix.lower() == ".txt" else "video"}
        if ctx["tipo"] == "script":
            narrador = None
            nar = ch["narrador"]
            if nar.get("modo") == "grabar":
                rutas = [str(f) for f in _archivos(carpeta_hablando(carpeta) / NARRADOR_CARPETA, EXT_VIDEO | EXT_AUDIO_N)]
                if rutas:
                    narrador = {"modo": "grabar", "rutas": rutas}
            elif nar.get("modo") in ("windows", "elevenlabs"):
                narrador = {"modo": nar["modo"], "voz": nar.get("elVoz") if nar["modo"] == "elevenlabs" else nar.get("voz"), "velocidad": nar.get("velocidad", 0)}
            nombres = [p["nombre"] for p in personas] + (["Narrador"] if narrador else [])
            texto = _etiquetar(_texto_guion(g), nombres)
            tarea_analizar_conv([{"nombre": p["nombre"], "rutas": [str(carpeta_hablando(carpeta) / p["nombre"] / a["nombre"]) for a in p["archivos"]]} for p in personas],
                                texto, idioma, "base", narrador, True)
            for a_ in H.avisos or []:
                mostrar("  Aviso: " + a_)
            ctx["dur"] = sum(t["b"] - t["a"] for t in H.plan["tramos"])
            ctx["plan"] = H.plan
            ctx["lineas"] = H.lineas
        else:
            H.base, H.span = 0, 90
            ctx["pal"] = transcribir_cache(g, idioma, "base")
            ctx["dur"] = max(w[2] for w in ctx["pal"]) - min(w[1] for w in ctx["pal"])
        aviso_d = planes.revisar_duracion(ctx["dur"], lim_c)
        if aviso_d:
            raise gd.ErrorMotor(aviso_d.replace("Este guion dura", "Este video dura").replace("Usa un guion más corto.", "Usa un guion más corto o un video más corto."))
        return ctx
    finally:
        H.activo = False


def _texto_limpio(txt):
    """El guion sin quién habla, sin marcas y sin lo que nadie dice: sirve para sacar el título por defecto."""
    t = re.sub(r"\[\[([^\]|]*)(?:\|([^\]]*))?\]\]", lambda m: "" if ("-dice" in (m.group(2) or "") or "burbuja=" in (m.group(2) or "")) else m.group(1), str(txt))
    t = re.sub(r"\[[^\]]*\]", "", t)
    t = re.sub(r"(?m)^\s*[^:\n]{1,40}?(?:\([^)\n]{0,20}\))?\s*:\s*", "", t)
    return " ".join(t.split())


def render_entrada(ctx, carpeta, cfg_f, temas, material, salida):
    """Crea el video de ese plan en un formato. Mantiene lo de cualquier guion: título arriba, frase final, estilo del producto."""
    g, ch = ctx["g"], ctx["ch"]
    cfg_h = dict(cfg_f)
    cfg_h["pantalla_completa"] = True
    gd.ajustar_pantalla_completa(cfg_h)
    gancho = ""
    if ctx["tipo"] == "script":
        gancho, cuerpo = gd.leer_texto(g)
        gancho = gancho or gd.gancho_por_defecto(_texto_limpio(cuerpo))
    op = {"pid": Path(carpeta).name, "cfg": cfg_h, "mat": gd.Material(cfg_h, temas, []) if material is None else material, "destino": str(salida), "externo": True,
          "zoom": ch["zoom"], "broll": ch["broll"], "color_personas": ch["colores"], "quitar_silencios": ch["silencios"], "quitar_muletillas": ch.get("muletillas", True), "nombre": g.stem,
          "capas_de": str(g) if ctx["tipo"] == "script" else None, "gancho": gancho}
    H.activo = False
    H.plan = ctx.get("plan")
    if ctx["tipo"] == "script":
        return crear_conv(op)
    return crear(g, ctx["pal"], op)


def previa_marca(carpeta, span, formato=None):
    """Imagen de cómo se verá UNA marca (texto, imagen, figura) sobre un fondo de ejemplo. span = lo que va dentro de [[ ]]."""
    from PIL import Image
    import tempfile
    cfg = gd.cargar_config(Path(carpeta))
    if formato in catalogo.FORMATOS:
        cfg["formato_video"] = formato
    gd.aplicar_formato(cfg)
    cfg["pantalla_completa"] = True
    gd.ajustar_pantalla_completa(cfg)
    W, H_ = int(cfg["ancho"]), int(cfg["alto"])
    sp = _leer_span(span)
    if sp["texto"] and not sp["txt"] and not sp.get("img") and not sp.get("fig"):
        sp["txt"] = False
    sp["seg"] = sp["seg"] or 5
    fondo = Image.new("RGBA", (W, H_), (24, 30, 52, 255))
    for y in range(H_):                                   # degradado suave para que se note lo que se dibuja
        c = int(24 + 40 * y / H_)
        fondo.paste((c, c + 6, c + 30, 255), (0, y, W, y + 1))
    with tempfile.TemporaryDirectory() as tmp:
        sp["n"] = 0
        sp["antes"] = True
        tx, _p = planear_textos(dict(cfg, dir=str(carpeta)), [["x", 0.0, 1.0, [sp]]], 10.0, tmp)
        for png, *_ in tx:
            fondo.alpha_composite(Image.open(png).convert("RGBA"))
    import io
    out = io.BytesIO()
    fondo.convert("RGB").resize((max(1, W // 3), max(1, H_ // 3))).save(out, "PNG")
    return out.getvalue()
