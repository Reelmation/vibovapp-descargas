#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generador de videos verticales (1080x1920) para Reels / TikTok / Shorts.

Cada video = audio (tu voz de ElevenLabs) + escenas. Cada escena tiene:
  - un clip o imagen elegido al azar de una carpeta de clips/ (por "tema"),
  - un texto grande arriba,
  - el llamado a la acción (CTA) abajo.

Uso:
  python generar_video.py --prueba                 (verifica que todo funciona)
  python generar_video.py videos/mi_video.json     (un video)
  python generar_video.py videos                   (todos los .json de la carpeta)
"""
import argparse
import json
import os
import random
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

BASE = Path(__file__).resolve().parent
# Si el programa trae su propio FFmpeg (carpeta ffmpeg/bin), se usa ese.
_ff = BASE / "ffmpeg" / "bin"
if _ff.is_dir():
    os.environ["PATH"] = str(_ff) + os.pathsep + os.environ.get("PATH", "")
# Tipos que se aceptan (incluye lo que baja WhatsApp Web y los celulares): ffmpeg y Pillow los leen todos.
VIDEO_EXT = {".mp4", ".mov", ".m4v", ".webm", ".mkv", ".avi", ".3gp", ".3g2", ".mpeg", ".mpg", ".wmv", ".flv"}
IMG_EXT = {".jpg", ".jpeg", ".jfif", ".png", ".webp", ".bmp", ".gif"}


# ----------------------------------------------------------------------------
# Utilidades
# ----------------------------------------------------------------------------
# En Windows, cada llamada a ffmpeg abriría una ventanita negra (cmd). Esta bandera la oculta; en otros sistemas vale 0.
SIN_VENTANA = getattr(subprocess, "CREATE_NO_WINDOW", 0)


def run(cmd, cwd=None):
    # stdin=DEVNULL: en el programa instalado (sin consola) Windows no da entrada estándar y ffmpeg podía fallar sin explicar.
    # encoding utf-8 + errors=replace: si ffmpeg escribe acentos, no se rompe la lectura de su mensaje.
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace",
                       stdin=subprocess.DEVNULL, creationflags=SIN_VENTANA)
    if r.returncode != 0:
        raise RuntimeError(
            "Falló el comando: " + " ".join(str(c) for c in cmd[:2]) + f" ... (código {r.returncode})\n"
            + (r.stderr or "(ffmpeg no escribió ningún mensaje)")[-1500:]
        )
    return r.stdout


def duracion(path):
    """Duración en segundos. Algunos archivos (webm grabados en el navegador, algunos de WhatsApp) no la traen escrita:
    en ese caso se busca en la pista de video y, si tampoco, se mide leyendo el archivo."""
    for entrada in ("format=duration", "stream=duration"):
        try:
            out = run(["ffprobe", "-v", "error", "-show_entries", entrada, "-of", "default=nw=1:nk=1", str(path)])
            for linea in out.split():
                try:
                    v = float(linea)
                    if v > 0:
                        return v
                except ValueError:
                    continue
        except Exception:
            pass
    try:       # último recurso: se lee el archivo completo y se toma el último tiempo que reporta ffmpeg
        r = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-f", "null", "-", "-progress", "pipe:1", "-nostats"],
                           capture_output=True, text=True, stdin=subprocess.DEVNULL, creationflags=SIN_VENTANA, timeout=300)
        t = [l.split("=")[1] for l in r.stdout.splitlines() if l.startswith("out_time_us=") and l.split("=")[1].lstrip("-").isdigit()]
        if t and int(t[-1]) > 0:
            return int(t[-1]) / 1e6
    except Exception:
        pass
    raise ValueError(f"No pude saber cuánto dura el archivo {Path(path).name}.")


def ruta(p):
    """Rutas relativas se leen desde la carpeta del proyecto."""
    p = Path(p)
    return p if p.is_absolute() else BASE / p


# ----------------------------------------------------------------------------
# Texto
# ----------------------------------------------------------------------------
_DIRS_FUENTES = ["C:/Windows/Fonts", "/usr/share/fonts", "/usr/local/share/fonts",
                 "/System/Library/Fonts", "/System/Library/Fonts/Supplemental", "/Library/Fonts"]
_FUENTES_RESPALDO = [
    "C:/Windows/Fonts/impact.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
]


def buscar_fuente(valor):
    """Acepta la ruta de un archivo .ttf/.otf o solo el nombre ("Impact", "Arial Bold").
    Devuelve la ruta del archivo o None si no la encuentra."""
    valor = str(valor or "").strip().strip('"')
    if not valor:
        return None
    p = ruta(valor)
    if p.is_file():
        return str(p)
    nombre = "".join(c for c in valor.lower() if c.isalnum())
    try:
        import generar_diario as _gd          # las tipografías subidas viven en la carpeta del usuario activo
        propias = Path(_gd.DATOS) / "fuentes"
    except Exception:
        propias = Path(os.environ.get("VIBOVAPP_DATOS") or BASE) / "fuentes"
    carpetas = [BASE / "fuentes", propias] + [Path(d) for d in _DIRS_FUENTES]
    for d in carpetas:
        if not d.exists():
            continue
        for f in d.rglob("*"):
            if f.suffix.lower() in (".ttf", ".otf") and nombre and \
                    "".join(c for c in f.stem.lower() if c.isalnum()) == nombre:
                return str(f)
    return None


def cargar_fuente(cfg, size, elemento=None):
    """Letra de un elemento ("titulo", "subs", "cta", "usuario", "burbuja"); si no tiene, la general."""
    candidatos = []
    for clave in ([f"fuente_{elemento}"] if elemento else []) + ["fuente"]:
        encontrada = buscar_fuente(cfg.get(clave))
        if cfg.get(clave) and not encontrada and clave not in _avisadas:
            _avisadas.add(clave)
            print(f"Aviso: no encontré la letra '{cfg.get(clave)}' ({clave}); se usa otra.")
        if encontrada:
            candidatos.append(encontrada)
    candidatos += _FUENTES_RESPALDO
    for c in candidatos:
        if Path(c).exists():
            return ImageFont.truetype(c, size)
    raise RuntimeError("No encontré una letra para escribir los textos. "
                       "Pon un archivo .ttf en la carpeta 'fuentes' del programa.")


_avisadas = set()


def envolver(fuente, texto, ancho_max):
    lineas = []
    for parrafo in texto.split("\n"):
        actual = ""
        for palabra in parrafo.split():
            prueba = (actual + " " + palabra).strip()
            if fuente.getlength(prueba) <= ancho_max:
                actual = prueba
            else:
                if actual:
                    lineas.append(actual)
                actual = palabra
        lineas.append(actual)
    return lineas


def dibujar_en_zona(draw, cfg, texto, zona, tam_max, color, trazo=0, elemento=None, trazo_color="black"):
    x0, y0, x1, y1 = zona
    ancho = x1 - x0
    tam = tam_max
    while True:
        fuente = cargar_fuente(cfg, tam, elemento)
        lineas = envolver(fuente, texto, ancho)
        alto_linea = int(tam * 1.15)
        if len(lineas) * alto_linea <= (y1 - y0) or tam <= 28:
            break
        tam -= 4
    total = len(lineas) * alto_linea
    y = y0 + ((y1 - y0) - total) // 2
    for linea in lineas:
        w = fuente.getlength(linea)
        draw.text((x0 + (ancho - w) / 2, y), linea, font=fuente, fill=color,
                  stroke_width=trazo, stroke_fill=trazo_color)
        y += alto_linea


def crear_overlay(cfg, arriba, cta, destino):
    W, H = cfg["ancho"], cfg["alto"]
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    margen = 60
    media_y0 = cfg["media_y"]
    media_y1 = media_y0 + cfg["media_alto"]
    if arriba:
        dibujar_en_zona(d, cfg, arriba,
                        (margen, cfg["zona_segura_arriba"], W - margen, media_y0 - 30),
                        cfg["tam_texto_arriba"], cfg["color_texto"])
    if cta:
        dibujar_en_zona(d, cfg, cta,
                        (margen, media_y1 + 30, W - margen, H - cfg["zona_segura_abajo"]),
                        cfg["tam_cta"], cfg["color_cta"])
    img.save(destino)


# ----------------------------------------------------------------------------
# Biblioteca de clips
# ----------------------------------------------------------------------------
class Biblioteca:
    """Elige clips al azar evitando repetirlos mientras queden clips sin usar."""

    def __init__(self, carpeta):
        self.carpeta = carpeta
        self.usados = set()

    def elegir(self, tema):
        d = self.carpeta / tema
        archivos = []
        if d.exists():
            archivos = [p for p in d.iterdir() if p.suffix.lower() in VIDEO_EXT | IMG_EXT]
        if not archivos:
            raise RuntimeError(f"No hay clips ni imágenes en la carpeta: {d}")
        libres = [p for p in archivos if p not in self.usados] or archivos
        elegido = random.choice(libres)
        self.usados.add(elegido)
        return elegido


# ----------------------------------------------------------------------------
# Audio (ElevenLabs opcional)
# ----------------------------------------------------------------------------
def generar_con_elevenlabs(cfg, texto, destino):
    voz = cfg.get("elevenlabs_voice_id")
    clave = os.environ.get("ELEVENLABS_API_KEY")
    if not voz or not clave:
        raise RuntimeError("Faltan elevenlabs_voice_id (config.json) o la variable ELEVENLABS_API_KEY.")
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voz}?output_format=mp3_44100_128"
    cuerpo = json.dumps({
        "text": texto,
        "model_id": cfg.get("elevenlabs_model", "eleven_multilingual_v2"),
    }).encode("utf-8")
    req = urllib.request.Request(url, data=cuerpo, method="POST", headers={
        "xi-api-key": clave, "Content-Type": "application/json", "Accept": "audio/mpeg"})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            destino.parent.mkdir(parents=True, exist_ok=True)
            destino.write_bytes(r.read())
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"ElevenLabs respondió {e.code}: {e.read().decode('utf-8', 'ignore')[:400]}")


def obtener_audio(cfg, v):
    destino = ruta(v["audio"])
    if destino.exists():
        return destino
    if v.get("texto_voz"):
        print(f"  Generando audio con ElevenLabs -> {destino.name}")
        generar_con_elevenlabs(cfg, v["texto_voz"], destino)
        return destino
    raise FileNotFoundError(f"No existe el audio {destino} y el video no tiene \"texto_voz\" para generarlo.")


# ----------------------------------------------------------------------------
# Render
# ----------------------------------------------------------------------------
def planificar(escenas, total):
    """Reparte la duración total entre las escenas (respeta 'duracion' si la pones)."""
    fijos = [e.get("duracion") for e in escenas]
    faltan = [i for i, d in enumerate(fijos) if d is None]
    suma = sum(d for d in fijos if d is not None)
    if faltan:
        resto = total - suma
        reparto = resto / len(faltan) if resto >= 1.0 * len(faltan) else total / len(escenas)
        fijos = [reparto if d is None else d for d in fijos]
    factor = total / sum(fijos)
    return [d * factor for d in fijos]


def crear_segmento(cfg, media, dur, overlay, salida):
    W, H, fps = cfg["ancho"], cfg["alto"], cfg["fps"]
    mh, my = cfg["media_alto"], cfg["media_y"]
    cmd = ["ffmpeg", "-y", "-v", "error"]
    if media.suffix.lower() in IMG_EXT:
        cmd += ["-loop", "1", "-framerate", str(fps), "-i", str(media)]
    else:
        mdur = duracion(media)
        if mdur > dur + 0.4:
            ss = random.uniform(0, mdur - dur - 0.3)
            cmd += ["-ss", f"{ss:.2f}", "-i", str(media)]
        else:
            cmd += ["-stream_loop", "-1", "-i", str(media)]
    cmd += ["-loop", "1", "-framerate", str(fps), "-i", str(overlay)]
    filtro = (
        f"[0:v]scale={W}:{mh}:force_original_aspect_ratio=increase,crop={W}:{mh},setsar=1,fps={fps}[m];"
        f"color=c={cfg['color_fondo']}:s={W}x{H}:r={fps}[bg];"
        f"[bg][m]overlay=0:{my}:shortest=1[b];"
        f"[b][1:v]overlay=0:0:shortest=1,format=yuv420p[v]"
    )
    cmd += ["-filter_complex", filtro, "-map", "[v]", "-t", f"{dur:.3f}", "-r", str(fps),
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-an", str(salida)]
    run(cmd)


def renderizar(cfg, archivo_json, biblioteca):
    v = json.loads(Path(archivo_json).read_text(encoding="utf-8"))
    nombre = Path(archivo_json).stem
    print(f"\n== {nombre} ==")
    audio = obtener_audio(cfg, v)
    total = duracion(audio) + cfg.get("cola_segundos", 0.6)
    escenas = v["escenas"]
    duraciones = planificar(escenas, total)
    cta = v.get("cta", cfg["cta"])
    salida = ruta(cfg["carpeta_salida"]) / f"{nombre}.mp4"
    salida.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        arriba_actual = ""
        lista = []
        for i, (esc, dur) in enumerate(zip(escenas, duraciones)):
            if "archivo" in esc:
                media = ruta(esc["archivo"])
                if not media.exists():
                    raise FileNotFoundError(f"No existe el archivo: {media}")
            else:
                media = biblioteca.elegir(esc["tema"])
            # Si la escena no trae "texto_arriba" se conserva el anterior; "" lo quita.
            if "texto_arriba" in esc:
                arriba_actual = esc["texto_arriba"]
            overlay = tmp / f"ov_{i:03d}.png"
            crear_overlay(cfg, arriba_actual, esc.get("cta", cta), overlay)
            seg = tmp / f"seg_{i:03d}.mp4"
            print(f"  Escena {i + 1}/{len(escenas)}: {media.name} ({dur:.1f}s)")
            crear_segmento(cfg, media, dur, overlay, seg)
            lista.append(seg.name)
        (tmp / "lista.txt").write_text("".join(f"file '{n}'\n" for n in lista), encoding="utf-8")
        run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", "lista.txt",
             "-c", "copy", "video.mp4"], cwd=tmp)
        run(["ffmpeg", "-y", "-v", "error", "-i", str(tmp / "video.mp4"), "-i", str(audio),
             "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
             "-movflags", "+faststart", str(salida)])
    print(f"  Listo: {salida}")
    return salida


# ----------------------------------------------------------------------------
# Modo prueba (no necesita clips ni internet)
# ----------------------------------------------------------------------------
def preparar_prueba():
    carpeta = BASE / "clips" / "prueba"
    carpeta.mkdir(parents=True, exist_ok=True)
    colores = ["0x1f4e79", "0x7a3b1d", "0x2d6a4f"]
    for i, c in enumerate(colores):
        destino = carpeta / f"demo_{i}.mp4"
        if not destino.exists():
            run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi",
                 "-i", f"testsrc2=size=1280x720:rate=30:duration=6", "-vf", f"colorchannelmixer=rr=0.6:gg=0.6:bb=0.6,drawbox=x=0:y=0:w=iw:h=ih:color={c}@0.35:t=fill",
                 "-pix_fmt", "yuv420p", "-c:v", "libx264", str(destino)])
    audio = BASE / "audio" / "prueba.wav"
    audio.parent.mkdir(parents=True, exist_ok=True)
    if not audio.exists():
        run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "sine=frequency=220:duration=10", str(audio)])
    config_video = {
        "audio": "audio/prueba.wav",
        "cta": "Escribe “GUIONES” y recibe el link",
        "escenas": [
            {"tema": "prueba", "texto_arriba": "Deja de perder ventas inmobiliarias"},
            {"tema": "prueba", "texto_arriba": "Responde esto cuando te digan: “Lo voy a pensar”"},
            {"tema": "prueba", "texto_arriba": "50 guiones, 25 prompts y 1 CRM en Notion"},
        ],
    }
    destino = BASE / "videos" / "prueba.json"
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(json.dumps(config_video, ensure_ascii=False, indent=2), encoding="utf-8")
    return destino


# ----------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description="Generador de videos verticales para el kit.")
    ap.add_argument("entrada", nargs="*", help="archivo(s) .json o una carpeta con .json")
    ap.add_argument("--prueba", action="store_true", help="crea material de prueba y genera un video demo")
    args = ap.parse_args()

    for herramienta in ("ffmpeg", "ffprobe"):
        if not shutil.which(herramienta):
            sys.exit(f"No encuentro {herramienta}. Instálalo y agrégalo al PATH (ver LEEME.txt).")

    cfg = json.loads((BASE / "config.json").read_text(encoding="utf-8"))
    archivos = []
    if args.prueba:
        archivos.append(preparar_prueba())
    for e in args.entrada:
        p = ruta(e)
        archivos += sorted(p.glob("*.json")) if p.is_dir() else [p]
    if not archivos:
        ap.print_help()
        sys.exit(1)

    biblioteca = Biblioteca(ruta(cfg["carpeta_clips"]))
    errores = 0
    for a in archivos:
        try:
            renderizar(cfg, a, biblioteca)
        except Exception as ex:  # sigue con los demás videos del lote
            errores += 1
            print(f"  ERROR en {Path(a).name}: {ex}")
    if errores:
        sys.exit(1)


if __name__ == "__main__":
    main()
