"""Cortes al ritmo de la música: detecta el pulso de una canción (sin librerías extra, solo ffmpeg) y acomoda los cortes de las escenas."""
import array
import subprocess

import generar_video as gv

_CACHE = {}
HOP = 160            # 20 ms a 8 kHz
MAX_SEG = 90         # solo se analizan los primeros 90 s


def pulsos(audio):
    """Lista de segundos en que cae cada pulso de la canción, o [] si no se pudo detectar."""
    clave = str(audio)
    if clave in _CACHE:
        return _CACHE[clave]
    res = []
    try:
        r = subprocess.run(["ffmpeg", "-v", "error", "-t", str(MAX_SEG), "-i", str(audio), "-vn", "-ac", "1", "-ar", "8000",
                            "-af", "lowpass=f=1800", "-f", "s16le", "-"], capture_output=True, stdin=subprocess.DEVNULL,
                           creationflags=getattr(gv, "SIN_VENTANA", 0))
        pcm = array.array("h")
        pcm.frombytes(r.stdout[: len(r.stdout) // 2 * 2])
        res = _pulsos_de_muestras(pcm)
    except Exception:
        res = []
    _CACHE[clave] = res
    return res


def _pulsos_de_muestras(pcm):
    n = len(pcm) // HOP
    if n < 150:                                    # menos de 3 s: no alcanza para saber el pulso
        return []
    en = []
    for k in range(n):
        tr = pcm[k * HOP:(k + 1) * HOP]
        en.append(sum(x * x for x in tr) / HOP)
    # «golpes»: subidas bruscas de energía
    on = [0.0] + [max(0.0, en[k] - en[k - 1]) for k in range(1, n)]
    m = sum(on) / n or 1.0
    on = [min(x / m, 8.0) for x in on]
    fps = 8000 / HOP                               # 50 cuadros por segundo
    mejor = (-1.0, 0, 0)
    for bpm in range(70, 181):
        lag = fps * 60.0 / bpm
        for fase in range(int(lag) + 1):
            s, k = 0.0, fase + 0.0
            while k < n:
                i = int(round(k))
                if i < n:
                    s += on[i] + 0.5 * (on[i - 1] if i > 0 else 0) + 0.5 * (on[i + 1] if i + 1 < n else 0)
                k += lag
            pts = max(1, int((n - fase) / lag))
            sc = s / pts
            if sc > mejor[0]:
                mejor = (sc, bpm, fase)
    sc, bpm, fase = mejor
    if sc < 0.9:                                   # no hay un pulso claro
        return []
    lag = 60.0 / bpm
    t, out = fase / fps, []
    while t < n / fps:
        out.append(round(t, 3))
        t += lag
    return out


def acomodar(duraciones, pulsos_s, minimo=1.0):
    """Mueve cada corte al pulso más cercano. Devuelve nuevas duraciones (ninguna menor a `minimo`)."""
    if not pulsos_s:
        return list(duraciones)
    nuevas, t_ini, t_fin = [], 0.0, 0.0
    for i, d in enumerate(duraciones):
        t_fin += d
        if i == len(duraciones) - 1:
            corte = t_fin                          # el final del video no se mueve
        else:
            cand = [p for p in pulsos_s if p >= t_ini + minimo]
            corte = min(cand, key=lambda p: abs(p - t_fin)) if cand else t_fin
            if abs(corte - t_fin) > 1.5:
                corte = t_fin
        nuevas.append(round(corte - t_ini, 3))
        t_ini = corte
        t_fin = corte
    return nuevas
