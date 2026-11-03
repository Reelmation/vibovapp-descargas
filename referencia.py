"""Video de referencia: la persona sube un video que le gusta y la app lo mide (duración, formato, cortes, voz).
Solo mira lo que se puede medir; lo demás lo contesta la persona con preguntas sencillas."""
import re
import shutil
from pathlib import Path

import generar_diario as gd
import generar_video as gv


def _carpeta():
    c = Path(gd.DATOS) / "_referencia"
    c.mkdir(parents=True, exist_ok=True)
    return c


def ruta_video():
    for f in _carpeta().glob("referencia.*"):
        return f
    return None


def guardar(nombre, datos):
    ext = Path(nombre or "").suffix.lower()
    if ext not in (".mp4", ".mov", ".m4v", ".webm", ".mkv"):
        raise gd.ErrorMotor("Sube un video (mp4, mov, webm o mkv).")
    shutil.rmtree(_carpeta(), ignore_errors=True)
    destino = _carpeta() / ("referencia" + ext)
    destino.write_bytes(datos)
    return analizar(destino)


def analizar(ruta):
    out = gv.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,width,height", "-of", "csv=p=0", str(ruta)])
    ancho = alto = 0
    voz = False
    for ln in out.splitlines():
        p = ln.strip().split(",")
        if p and p[0] == "video" and len(p) >= 3 and not ancho:
            try:
                ancho, alto = int(p[1]), int(p[2])
            except ValueError:
                pass
        elif p and p[0] == "audio":
            voz = True
    dur = float(gv.duracion(ruta) or 0)
    cortes = 0
    try:                                          # cada cambio fuerte de imagen cuenta como un corte
        r = gv.subprocess.run(["ffmpeg", "-v", "info", "-i", str(ruta), "-vf", "scale=270:-1,select='gt(scene,0.1)',showinfo", "-an", "-f", "null", "-"],
                              capture_output=True, text=True, encoding="utf-8", errors="replace", stdin=gv.subprocess.DEVNULL,
                              creationflags=gv.SIN_VENTANA, timeout=300)
        cortes = len(re.findall(r"pts_time:", r.stderr or ""))
    except Exception:
        pass
    return {"duracion": round(dur, 1), "ancho": ancho, "alto": alto, "vertical": alto > ancho, "voz": voz,
            "cortes": cortes, "cada": round(dur / (cortes + 1), 1) if dur else 0}
