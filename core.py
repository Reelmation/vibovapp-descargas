"""Operaciones de productos, temas, archivos, guiones y estilos.
Todo lo que la interfaz necesita, sin nada de web: asi se puede probar solo."""
import os
import json
import re
import shutil
import subprocess
import hashlib
from pathlib import Path

import catalogo
import plantillas
import generar_diario as gd
import generar_video as gv

VIDEO_EXT = gv.VIDEO_EXT
IMG_EXT = gv.IMG_EXT
AUDIO_EXT = gd.AUDIO_EXT
FUENTE_EXT = {".ttf", ".otf"}
VECTOR_EXT = {".svg", ".pdf", ".ai"}      # logos en vector: se convierten a PNG (con transparencia) al subirlos
TEXTO_EXT = {".txt"}
LIMITE_MB = 500

# Secciones de archivos de un producto: carpeta y extensiones permitidas
SECCIONES = {
    "capas": ("capas", IMG_EXT | VIDEO_EXT),
    "kit": ("kit", VIDEO_EXT | IMG_EXT),
    "musica": ("musica", AUDIO_EXT),
    "sonidos": ("sonidos", AUDIO_EXT),
    "guiones": ("guiones", AUDIO_EXT | TEXTO_EXT),
}


def _productos():
    gd.PRODUCTOS.mkdir(parents=True, exist_ok=True)
    return gd.PRODUCTOS


def _estilos():
    d = gd.DATOS / "estilos"
    d.mkdir(parents=True, exist_ok=True)
    return d


# ----------------------------------------------------------------------------
# Configuracion del programa (idioma, aviso aceptado)
# ----------------------------------------------------------------------------
def _ruta_config():
    gd.DATOS.mkdir(parents=True, exist_ok=True)
    return gd.DATOS / "config_programa.json"


def config_programa():
    try:
        return json.loads(_ruta_config().read_text(encoding="utf-8"))
    except Exception:
        return {"idioma": "es", "aviso_aceptado": False, "tutorial_visto": False}


def guardar_config_programa(**cambios):
    c = config_programa()
    c.update({k: v for k, v in cambios.items() if k in ("idioma", "aviso_aceptado", "tutorial_visto", "sesion", "voz_nombre", "voz_velocidad", "voz_motor", "voz_el_id", "version_vista", "camino", "caminos")})
    if c.get("idioma") not in ("es", "en"):
        c["idioma"] = "es"
    if "voz_nombre" in c:
        c["voz_nombre"] = str(c["voz_nombre"] or "")[:120]
    if "voz_el_id" in c:
        c["voz_el_id"] = str(c["voz_el_id"] or "")[:80]
    if c.get("camino") not in (None, "", "guion", "presentador", "podcast", "musica", "todo"):
        c.pop("camino", None)
    if "caminos" in c:
        _ok = ("guion", "presentador", "podcast", "musica", "todo")
        cm = c["caminos"] if isinstance(c["caminos"], dict) else {}
        c["caminos"] = {str(k)[:80]: v for k, v in cm.items() if v in _ok}
    if "version_vista" in c:
        c["version_vista"] = str(c["version_vista"] or "")[:20]
    if c.get("voz_motor") not in ("windows", "elevenlabs"):
        c.pop("voz_motor", None)
    if "voz_velocidad" in c:
        try:
            c["voz_velocidad"] = max(-5, min(5, int(c["voz_velocidad"])))
        except (TypeError, ValueError):
            c["voz_velocidad"] = 0
    if not isinstance(c.get("sesion"), dict):
        c.pop("sesion", None)
    else:   # solo textos cortos: producto, pestaña y guion abiertos
        c["sesion"] = {k: str(v)[:120] for k, v in c["sesion"].items() if k in ("pid", "pestana", "guion")}
    _ruta_config().write_text(json.dumps(c, ensure_ascii=False, indent=2), encoding="utf-8")
    return c


# ----------------------------------------------------------------------------
# Productos
# ----------------------------------------------------------------------------
def carpeta(pid):
    pid = gd.limpiar_nombre(pid or "")
    c = _productos() / pid
    if not pid or not c.is_dir():
        raise gd.ErrorMotor("No encuentro ese proyecto.")
    return c


def _leer_meta(c):
    try:
        return json.loads((c / "producto.json").read_text(encoding="utf-8"))
    except Exception:
        return {}


def nombre_visible(c):
    return _leer_meta(c).get("nombre") or c.name


def _contar(c, sub, exts, recursivo=False):
    d = c / sub
    if not d.exists():
        return 0
    it = d.rglob("*") if recursivo else d.iterdir()
    return sum(1 for p in it if p.is_file() and p.suffix.lower() in exts and not p.name.startswith("_"))


def _hab(c):
    import hablado
    return hablado.listar_hablando(c)


def _entradas_h(c):
    import hablado
    return hablado.entradas_hablando(c)


def _proximos_guiones(c, est):
    """(guion que sigue, el que seguiría después) en modo Automático."""
    import hablado
    try:
        gs = gd.listar_guiones(c / "guiones")
    except RuntimeError:
        gs = []
    gs = sorted(gs + hablado.entradas_hablando(c), key=gd.clave_natural)       # tus videos hablando entran en la misma vuelta
    if not gs:
        return "", ""
    usados = [n for n in est.get("usados", []) if n in [g.name for g in gs]]
    pend = [g for g in gs if g.name not in usados] or gs
    sig = pend[0].stem
    desp = (pend[1] if len(pend) > 1 else gs[0]).stem
    return sig, (desp if len(gs) > 1 else "")


def resumen(c):
    est = gd.cargar_estado(c / "estado.json")
    g_sig, g_desp = _proximos_guiones(c, est)
    return {
        "guion_siguiente": g_sig, "guion_despues": g_desp,
        "id": c.name,
        "practica": gd.es_producto_practica(c),
        "nombre": nombre_visible(c),
        "guiones": max(0, _contar(c, "guiones", AUDIO_EXT) - len(gd.guiones_apagados(c / "guiones") & {p.name for p in (c / "guiones").glob("*") if p.is_file()})) + len(_entradas_h(c)),
        "hablando": sum(len(p["archivos"]) for p in _hab(c)["personas"]),
        "clips": _contar(c, "clips", VIDEO_EXT | IMG_EXT, True),
        "kit": _contar(c, "kit", VIDEO_EXT | IMG_EXT),
        "musica": _contar(c, "musica", AUDIO_EXT),
        "videos": _contar(c, "videos_finalizados", {".mp4"}, True),
        "papelera": sum(1 for _ in (c / "papelera").glob("*/meta.json")) if (c / "papelera").exists() else 0,
        "siguiente": est["contador"] + 1,
        "vuelta": est["ciclo"],
    }


def listar_productos():
    return [resumen(c) for c in sorted(_productos().iterdir()) if c.is_dir() and not c.name.startswith(("_", "."))]


def _id_libre(nombre):
    base = gd.limpiar_nombre(nombre)
    if not base:
        raise gd.ErrorMotor("Escribe un nombre (letras o números).")
    pid, n = base, 2
    while (_productos() / pid).exists():
        pid, n = f"{base}_{n}", n + 1
    return pid


def _limite(clave, actual, texto):
    import planes
    aviso = planes.revisar_conteo(clave, actual, texto)
    if aviso:
        raise gd.ErrorMotor(aviso)


ESPECIALES = ("demo", "muestra", "practica")      # productos que trae el programa: no cuentan en el límite de productos


def crear_producto(nombre, practica=False):
    """practica=True: es el producto de la práctica guiada; no cuenta en el límite de productos del plan."""
    nombre = (nombre or "").strip()
    if not practica:
        _limite("productos", sum(1 for q in listar_productos() if q["id"] not in ESPECIALES and not q.get("practica")), "proyectos por usuario")
    pid = _id_libre(nombre)
    c = _productos() / pid
    gd.crear_estructura(c, ajustes=catalogo.texto_ajustes({"usuario": "@tuusuario"}))
    (c / "producto.json").write_text(json.dumps({"nombre": nombre}, ensure_ascii=False), encoding="utf-8")
    if practica:
        (c / "practica.json").write_text(json.dumps({"practica": True}), encoding="utf-8")
    return pid


_TEMAS_MUESTRA = {   # tema: (palabras clave, color 1, color 2, rótulo es, rótulo en)
    "casas": ("casa, casas, hogar, departamento", (31, 78, 121), (86, 160, 211), "CASAS", "HOUSES"),
    "ciudad": ("ciudad, calle, zona, barrio", (92, 46, 120), (214, 110, 160), "CIUDAD", "CITY"),
    "dinero": ("dinero, precio, presupuesto, ahorro", (24, 94, 70), (120, 200, 140), "DINERO", "MONEY"),
}
_GUION_MUESTRA = {
    "es": ("Tu primer video con Vibovapp",
           "Así se ve un video hecho con Vibovapp. Cuando el guion habla de una casa, el video muestra un clip de casas. "
           "*1 /1 Cuando menciona la ciudad o el dinero, el clip cambia solo. "
           "Ahora haz el tuyo con tus propios clips y tu propio audio."),
    "en": ("Your first video with Vibovapp",
           "This is a video made with Vibovapp. When the script talks about a house, the video shows a houses clip. "
           "*1 /1 When it mentions the city or money, the clip changes by itself. "
           "Now make yours with your own clips and your own audio."),
}
_BURBUJAS_MUESTRA = {
    "es": [("emisor", "Hola, ¿esta casa sigue disponible?"), ("receptor", "Claro, te cuento todo sobre la zona y el precio.")],
    "en": [("emisor", "Hi, is this house still available?"), ("receptor", "Sure, I will tell you all about the area and the price.")],
}


def crear_muestra(idioma="es"):
    """Crea (si no existe) un producto de muestra con clips, música y un guion hechos por el programa, para el primer video."""
    from PIL import Image, ImageDraw
    en = idioma == "en"
    c = _productos() / "muestra"
    if c.exists():
        return "muestra"
    temas = "# temas de muestra\n" + "".join(f"{t}: {v[0]}\n" for t, v in _TEMAS_MUESTRA.items()) + "kit: producto, servicio\n"
    try:
        gd.crear_estructura(c, ajustes=catalogo.texto_ajustes({"usuario": "@tuusuario", "calidad": "720", "formato_video": "vertical"}, idioma), temas=temas)
        (c / "producto.json").write_text(json.dumps({"nombre": "Sample product" if en else "Proyecto de muestra"}, ensure_ascii=False), encoding="utf-8")
        fuente = gv.cargar_fuente({}, 150)
        W, H = 720, 1280
        for tema, (_, c1, c2, rot_es, rot_en) in _TEMAS_MUESTRA.items():
            (c / "clips" / tema).mkdir(parents=True, exist_ok=True)
            for i in range(2):
                img = Image.new("RGB", (W, H), c1)
                px = img.load()
                for y in range(H):                      # degradado vertical
                    f = y / (H - 1)
                    fila = tuple(int(c1[k] + (c2[k] - c1[k]) * f) for k in range(3))
                    for x in range(W):
                        px[x, y] = fila
                d = ImageDraw.Draw(img)
                for k in range(3):                      # círculos suaves para dar movimiento al zoom
                    r = 120 + 70 * k + 40 * i
                    cx, cy = 140 + 210 * k + 60 * i, 260 + 320 * k
                    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(255, 255, 255), width=6)
                rot = rot_en if en else rot_es
                ancho = d.textlength(rot, font=fuente)
                d.text(((W - ancho) / 2, H / 2 - 80), rot, font=fuente, fill=(255, 255, 255))
                img.save(c / "clips" / tema / f"{tema}_{i + 1}.png")
        (c / "kit").mkdir(exist_ok=True)
        for i in range(2):
            img = Image.new("RGB", (540, 1170), (246, 244, 238))
            d = ImageDraw.Draw(img)
            d.rectangle([30, 30, 510, 150], fill=(79, 70, 229))
            txt = "YOUR PRODUCT" if en else "TU PRODUCTO"
            d.text((60, 520), txt, font=gv.cargar_fuente({}, 70), fill=(79, 70, 229))
            img.save(c / "kit" / f"kit_{i + 1}.png")
        (c / "musica").mkdir(exist_ok=True)
        gv.run(["ffmpeg", "-y", "-v", "error",
                "-f", "lavfi", "-i", "sine=frequency=220:duration=40", "-f", "lavfi", "-i", "sine=frequency=277:duration=40",
                "-f", "lavfi", "-i", "sine=frequency=330:duration=40",
                "-filter_complex", "[0][1][2]amix=inputs=3:normalize=0,tremolo=f=0.4:d=0.5,volume=0.5,afade=t=in:d=2,afade=t=out:st=37:d=3[a]",
                "-map", "[a]", "-c:a", "aac", "-b:a", "128k", str(c / "musica" / ("sample_music.m4a" if en else "musica_muestra.m4a"))])
        (c / "guiones").mkdir(exist_ok=True)
        a = c / "guiones" / "01.wav"
        gv.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono", "-t", "22", str(a)])
        titulo, cuerpo = _GUION_MUESTRA["en" if en else "es"]
        a.with_suffix(".txt").write_text("# " + titulo + "\n" + cuerpo + "\n", encoding="utf-8")
        guardar_burbujas("muestra", "01.wav", [{"lado": lado, "texto": txt, "inicio": 4 + 4 * i, "duracion": 5}
                                              for i, (lado, txt) in enumerate(_BURBUJAS_MUESTRA["en" if en else "es"])])
    except Exception:
        shutil.rmtree(c, ignore_errors=True)
        raise
    return "muestra"


def crear_material_practica(idioma="es"):
    """Escribe en Documentos\\Vibovapp\\Material de práctica los archivos para la práctica guiada: el usuario los sube él mismo.
    Devuelve la carpeta. Si ya existe, la rehace completa (siempre queda igual)."""
    from PIL import Image, ImageDraw
    en = idioma == "en"
    import usuarios
    raiz = Path(usuarios.RAIZ) / ("Practice material" if en else "Material de práctica")
    if raiz.exists():
        shutil.rmtree(raiz, ignore_errors=True)
    d_guion, d_clips, d_kit, d_mus = (raiz / n for n in (("1 Script", "2 Clips", "3 Product images", "4 Music") if en
                                                          else ("1 Guion", "2 Clips", "3 Imágenes del producto", "4 Música")))
    try:
        for d in (d_guion, d_kit, d_mus):
            d.mkdir(parents=True, exist_ok=True)
        fuente = gv.cargar_fuente({}, 150)
        W, H = 720, 1280
        for tema, (_, c1, c2, rot_es, rot_en) in _TEMAS_MUESTRA.items():
            (d_clips / tema).mkdir(parents=True, exist_ok=True)
            for i in range(2):
                img = Image.new("RGB", (W, H), c1)
                px = img.load()
                for y in range(H):
                    f = y / (H - 1)
                    fila = tuple(int(c1[k] + (c2[k] - c1[k]) * f) for k in range(3))
                    for x in range(W):
                        px[x, y] = fila
                d = ImageDraw.Draw(img)
                for k in range(3):
                    r = 120 + 70 * k + 40 * i
                    cx, cy = 140 + 210 * k + 60 * i, 260 + 320 * k
                    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(255, 255, 255), width=6)
                rot = rot_en if en else rot_es
                ancho = d.textlength(rot, font=fuente)
                d.text(((W - ancho) / 2, H / 2 - 80), rot, font=fuente, fill=(255, 255, 255))
                img.save(d_clips / tema / f"{tema}_{i + 1}.png")
        for i in range(2):
            img = Image.new("RGB", (540, 1170), [(246, 244, 238), (232, 240, 252)][i])
            d = ImageDraw.Draw(img)
            d.rectangle([30, 30, 510, 150], fill=[(79, 70, 229), (224, 85, 155)][i])
            d.text((60, 480), "YOUR PRODUCT" if en else "TU PRODUCTO", font=gv.cargar_fuente({}, 70), fill=(79, 70, 229))
            d.text((60, 590), str(i + 1), font=gv.cargar_fuente({}, 260), fill=[(79, 70, 229), (224, 85, 155)][i])
            img.save(d_kit / f"kit_{i + 1}.png")
        gv.run(["ffmpeg", "-y", "-v", "error",
                "-f", "lavfi", "-i", "sine=frequency=220:duration=40", "-f", "lavfi", "-i", "sine=frequency=277:duration=40",
                "-f", "lavfi", "-i", "sine=frequency=330:duration=40",
                "-filter_complex", "[0][1][2]amix=inputs=3:normalize=0,tremolo=f=0.4:d=0.5,volume=0.5,afade=t=in:d=2,afade=t=out:st=37:d=3[a]",
                "-map", "[a]", "-c:a", "aac", "-b:a", "128k", str(d_mus / ("practice_music.m4a" if en else "musica_practica.m4a"))])
        a = d_guion / "01.wav"
        gv.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono", "-t", "22", str(a)])
        titulo, cuerpo = _GUION_MUESTRA["en" if en else "es"]
        a.with_suffix(".txt").write_text("# " + titulo + "\n" + cuerpo + "\n", encoding="utf-8")
        (raiz / ("READ ME.txt" if en else "LEEME.txt")).write_text(
            ("Practice material for the guided practice. Upload each file from the app when the guide asks. "
             "The audio is silent on purpose (only to practice); later you'll use your own voice.\n") if en else
            ("Material para la práctica guiada. Sube cada archivo desde la app cuando la guía te lo pida. "
             "El audio es silencioso a propósito (solo sirve para practicar); después usarás tu propia voz.\n"), encoding="utf-8")
    except Exception:
        shutil.rmtree(raiz, ignore_errors=True)
        raise
    return raiz


def duplicar_producto(pid, nombre, con_material=False):
    origen = carpeta(pid)
    nuevo = crear_producto(nombre)
    destino = _productos() / nuevo
    shutil.copy2(origen / "ajustes.txt", destino / "ajustes.txt")
    shutil.copy2(origen / "temas.txt", destino / "temas.txt")
    if (origen / "capas").is_dir():              # los logos y capas son parte del diseño: se copian siempre
        shutil.copytree(origen / "capas", destino / "capas", dirs_exist_ok=True)
        if (origen / "capas.json").is_file():
            shutil.copy2(origen / "capas.json", destino / "capas.json")
    if con_material:
        for sub in ("clips", "kit", "musica", "guiones", "sonidos"):
            if (origen / sub).exists():
                shutil.rmtree(destino / sub, ignore_errors=True)
                shutil.copytree(origen / sub, destino / sub, copy_function=_copiar_o_enlazar)
    else:
        for tema in gd.leer_temas(destino / "temas.txt"):
            if tema != "kit":
                (destino / "clips" / tema).mkdir(parents=True, exist_ok=True)
    return nuevo


def renombrar_producto(pid, nombre):
    c = carpeta(pid)
    nombre = (nombre or "").strip()
    if not nombre:
        raise gd.ErrorMotor("Escribe un nombre.")
    meta = _leer_meta(c)
    meta["nombre"] = nombre
    (c / "producto.json").write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8")


def _borrados():
    d = gd.PRODUCTOS.parent / "proyectos_borrados"
    d.mkdir(parents=True, exist_ok=True)
    return d


def borrar_producto(pid):
    """No se borra de verdad: pasa a «Proyectos borrados» y se puede recuperar durante 30 días."""
    import time
    c = carpeta(pid)
    dest = _borrados() / f"{int(time.time())}__{c.name}"
    try:
        shutil.move(str(c), str(dest))
    except Exception:
        shutil.rmtree(c)


def proyectos_borrados():
    import time
    out = []
    for d in sorted(_borrados().iterdir(), reverse=True):
        try:
            ts, nombre = d.name.split("__", 1)
            ts = int(ts)
        except ValueError:
            continue
        if time.time() - ts > 30 * 86400:
            shutil.rmtree(d, ignore_errors=True)
            continue
        out.append({"clave": d.name, "nombre": nombre, "dias": max(0, 30 - int((time.time() - ts) / 86400))})
    return out


def recuperar_proyecto(clave):
    d = _borrados() / gd.limpiar_nombre(clave)
    if not d.is_dir() or "__" not in d.name:
        raise gd.ErrorMotor("No encuentro ese proyecto.")
    nombre = d.name.split("__", 1)[1]
    dest = _productos() / nombre
    n = 2
    while dest.exists():
        dest = _productos() / f"{nombre} {n}"
        n += 1
    shutil.move(str(d), str(dest))
    return dest.name


def reiniciar(pid):
    msgs = []
    gd.reiniciar_producto(carpeta(pid), msgs.append)
    return msgs


# ----------------------------------------------------------------------------
# Temas y palabras clave
# ----------------------------------------------------------------------------
def _nombre_tema(t):
    return gd.normalizar(t or "")      # igual que al leer temas.txt (sin espacios ni guiones bajos)


def leer_temas(pid):
    """{tema: [palabras]} en orden; 'kit' siempre presente."""
    return gd.leer_temas(carpeta(pid) / "temas.txt")


def guardar_temas(pid, temas):
    """temas: {nombre: [palabras]}. Crea las carpetas de clips que falten. No borra carpetas viejas."""
    c = carpeta(pid)
    limpio = {}
    previos = set(gd.leer_temas(c / "temas.txt"))
    for nombre, palabras in temas.items():
        n = _nombre_tema(nombre)
        if not n or n == "general":
            continue
        if isinstance(palabras, str):
            palabras = re.split(r"[,\n]", palabras)
        pals = []
        for p in palabras:
            p = gd.normalizar(p).strip()
            if p and p not in pals:
                pals.append(p)
        if pals:
            limpio[n] = pals
    kit = limpio.pop("kit", [])
    if set(limpio) - previos:     # solo se revisa si se está agregando una carpeta nueva
        _limite("carpetas", len(set(limpio) - {"kit"}) - 1, "carpetas de palabras clave")
    lineas = [gd.TEMAS_BASE.split("\n\n")[0], ""]
    if kit:
        lineas.append("kit: " + ", ".join(kit))
    for n, pals in limpio.items():
        lineas.append(f"{n}: " + ", ".join(pals))
        (c / "clips" / n).mkdir(parents=True, exist_ok=True)
    (c / "temas.txt").write_text("\n".join(lineas) + "\n", encoding="utf-8-sig")
    return leer_temas(pid)


def renombrar_tema(pid, tema, nuevo):
    """Cambia el nombre de la carpeta de palabras clave (conserva palabras, clips y orden)."""
    c = carpeta(pid)
    viejo = _nombre_tema(tema)
    nuevo_n = _nombre_tema(nuevo)
    temas = gd.leer_temas(c / "temas.txt")
    if viejo in ("kit", "general") or viejo not in temas:
        raise gd.ErrorMotor("Esa carpeta no se puede renombrar.")
    if not nuevo_n:
        raise gd.ErrorMotor("Escribe un nombre (letras o números).")
    if nuevo_n == viejo:
        return viejo
    if nuevo_n in temas or nuevo_n in ("kit", "general"):
        raise gd.ErrorMotor(f"Ya existe una carpeta llamada «{nuevo_n}». Elige otro nombre.")
    d_viejo, d_nuevo = c / "clips" / viejo, c / "clips" / nuevo_n
    if d_nuevo.exists() and any(d_nuevo.iterdir()):
        raise gd.ErrorMotor(f"Ya hay archivos en una carpeta llamada «{nuevo_n}».")
    if d_viejo.exists():
        if d_nuevo.exists():
            d_nuevo.rmdir()
        d_viejo.rename(d_nuevo)
    guardar_temas(pid, {(nuevo_n if k == viejo else k): v for k, v in temas.items()})
    return nuevo_n


def borrar_tema(pid, tema, modo="todo"):
    """Quita algo de un tema de palabras clave. Todo lo que se quita va a la papelera y se puede recuperar.
    modo: "todo" = palabras y clips (la carpeta completa) | "archivos" = solo los clips (el tema y sus palabras se quedan)
          | "palabras" = solo el tema con sus palabras (los clips pasan a 'Clips generales' para que no se pierdan)."""
    c = carpeta(pid)
    t = _nombre_tema(tema)
    if t in ("general", "kit"):
        return leer_temas(pid)
    temas = leer_temas(pid)
    palabras = temas.get(t) or []
    origen = c / "clips" / t
    archivos = [p for p in origen.iterdir() if p.is_file() and not p.name.startswith("_")] if origen.is_dir() else []
    if modo == "archivos":
        _a_papelera(c, archivos, f"{t} · {len(archivos)} clips", "clips")
        return temas
    if modo == "palabras":
        temas.pop(t, None)
        _a_papelera(c, [], t, "tema", {"tema": {"nombre": t, "palabras": palabras}})
        if archivos:
            general = c / "clips" / "general"
            general.mkdir(exist_ok=True)
            for p in archivos:
                p.rename(_nombre_libre(general, p.name))
    else:
        temas.pop(t, None)
        _a_papelera(c, archivos, t, "tema", {"tema": {"nombre": t, "palabras": palabras}})
    if origen.is_dir():
        shutil.rmtree(origen, ignore_errors=True)
    return guardar_temas(pid, temas)


# ----------------------------------------------------------------------------
# Archivos (clips, kit, musica, guiones)
# ----------------------------------------------------------------------------

def vector_a_png(datos, ext, ancho=2000):
    """Convierte un SVG, PDF o AI (primera página) a PNG con fondo transparente. Devuelve los bytes del PNG."""
    try:
        try:
            import pymupdf as fitz
        except ImportError:
            import fitz
    except ImportError:
        raise gd.ErrorMotor("Este programa no puede leer logos en vector todavía; guárdalo como PNG y súbelo.")
    try:
        doc = fitz.open(stream=bytes(datos), filetype="svg" if ext == ".svg" else "pdf")
        pag = doc[0]
        k = max(0.2, min(8.0, ancho / max(1.0, pag.rect.width)))
        pix = pag.get_pixmap(matrix=fitz.Matrix(k, k), alpha=True)
        return pix.tobytes("png")
    except Exception:
        raise gd.ErrorMotor("No pude leer ese archivo. Si es un .ai o .eps antiguo, expórtalo como PNG, SVG o PDF.")


def detectar_extension(datos):
    """Adivina el tipo de un archivo por su contenido (sirve cuando baja sin extensión o con una rara, como a veces en WhatsApp Web)."""
    c = bytes(datos[:64])
    if c[4:8] == b"ftyp":
        return ".mov" if c[8:12] == b"qt  " else ".3gp" if c[8:10] == b"3g" else ".m4a" if c[8:12] in (b"M4A ", b"M4B ") else ".mp4"
    if c[:4] == b"OggS":
        return ".ogg"
    if c[:3] == b"ID3" or c[:2] in (b"\xff\xfb", b"\xff\xf3", b"\xff\xf2"):
        return ".mp3"
    if c[:4] == b"RIFF" and c[8:12] == b"WAVE":
        return ".wav"
    if c[:4] == b"RIFF" and c[8:12] == b"WEBP":
        return ".webp"
    if c[:4] == b"RIFF" and c[8:12] == b"AVI ":
        return ".avi"
    if c[:3] == b"\xff\xd8\xff":
        return ".jpg"
    if c[:8] == b"\x89PNG\r\n\x1a\n":
        return ".png"
    if c[:3] == b"GIF":
        return ".gif"
    if c[:2] == b"BM":
        return ".bmp"
    if c[:4] == b"\x1a\x45\xdf\xa3":
        return ".webm"
    if c[:4] == b"fLaC":
        return ".flac"
    if c[:6] == b"#!AMR\n"[:6]:
        return ".amr"
    return ""


def _nombre_libre(dest, nombre):
    stem = re.sub(r"[^\w\-. ]+", "_", Path(nombre).stem, flags=re.UNICODE).strip() or "archivo"
    ext = Path(nombre).suffix.lower()
    p, n = dest / f"{stem}{ext}", 2
    while p.exists():
        p, n = dest / f"{stem}_{n}{ext}", n + 1
    return p


def _dir_clips(c, tema):
    t = _nombre_tema(tema)
    if t == "kit":
        return c / "kit"
    if t != "general" and t not in gd.leer_temas(c / "temas.txt"):
        raise gd.ErrorMotor("Ese tema no existe.")
    return c / "clips" / t


def _dir_seccion(c, seccion, tema=None):
    if seccion == "clips":
        return _dir_clips(c, tema or "general"), VIDEO_EXT | IMG_EXT
    if seccion not in SECCIONES:
        raise gd.ErrorMotor("Sección desconocida.")
    sub, ext = SECCIONES[seccion]
    return c / sub, ext


def listar_archivos(pid, seccion, tema=None):
    c = carpeta(pid)
    d, ext = _dir_seccion(c, seccion, tema)
    if not d.exists():
        return []
    salida = []
    for p in sorted(d.iterdir(), key=gd.clave_natural):
        if p.is_file() and not p.name.startswith("_") and p.suffix.lower() in ext:
            salida.append({"nombre": p.name, "tam": p.stat().st_size,
                           "tipo": "video" if p.suffix.lower() in VIDEO_EXT else
                                   "imagen" if p.suffix.lower() in IMG_EXT else
                                   "audio" if p.suffix.lower() in AUDIO_EXT else "texto"})
    return salida


class Duplicado(gd.ErrorMotor):
    """El archivo ya existe (con el mismo contenido) en esa misma carpeta."""


def _hash(datos_o_ruta):
    h = hashlib.sha256()
    if isinstance(datos_o_ruta, (bytes, bytearray)):
        h.update(datos_o_ruta)
    else:
        with open(datos_o_ruta, "rb") as f:
            for bloque in iter(lambda: f.read(1 << 20), b""):
                h.update(bloque)
    return h.hexdigest()


def _repetido_en(d, datos):
    """Nombre del archivo de la carpeta d con exactamente el mismo contenido, o None."""
    if not d.exists():
        return None
    mi = None
    for p in d.iterdir():
        if p.is_file() and p.stat().st_size == len(datos):
            mi = mi or _hash(datos)
            if _hash(p) == mi:
                return p.name
    return None


def quitar_duplicados(pid, seccion, tema=None):
    """Borra los archivos repetidos de UNA carpeta (se queda con el primero de cada grupo). Devuelve cuántos borró."""
    c = carpeta(pid)
    d, ext = _dir_seccion(c, seccion, tema)
    vistos, borrados = {}, 0
    if not d.exists():
        return 0
    for p in sorted(d.iterdir(), key=gd.clave_natural):
        if p.is_file() and not p.name.startswith("_") and p.suffix.lower() in ext:
            k = (p.stat().st_size, _hash(p))
            if k in vistos:
                _a_papelera(c, [p], p.name, seccion)
                borrados += 1
            else:
                vistos[k] = p.name
    return borrados



# ----------------------------------------------------------------------------
# Ahorro de espacio (interno, el usuario no ve nada): el mismo archivo subido otra vez se guarda una sola vez en disco.
# Cada carpeta sigue teniendo su archivo de siempre; por debajo comparten el espacio (enlace duro), y si no se puede, se copia normal.
# ----------------------------------------------------------------------------
import hashlib
_HUELLAS_MIN = 64 * 1024


def _ruta_huellas():
    return Path(gd.DATOS) / "_huellas.json"


def _escribir_sin_repetir(destino, datos):
    destino = Path(destino)
    try:
        if len(datos) >= _HUELLAS_MIN:
            h = hashlib.sha256(datos).hexdigest()
            try:
                idx = json.loads(_ruta_huellas().read_text(encoding="utf-8"))
            except Exception:
                idx = {}
            viejo = Path(idx.get(h, ""))
            if idx.get(h) and viejo.is_file() and viejo.stat().st_size == len(datos) and viejo != destino:
                try:
                    os.link(viejo, destino)
                    return
                except OSError:
                    pass
            destino.write_bytes(datos)
            idx[h] = str(destino)
            idx = {k: v for k, v in idx.items() if Path(v).is_file()} if len(idx) > 2000 else idx
            _ruta_huellas().write_text(json.dumps(idx), encoding="utf-8")
            return
    except Exception:
        pass
    destino.write_bytes(datos)


def _copiar_o_enlazar(origen, destino, **kw):
    try:
        if Path(destino).exists():
            Path(destino).unlink()
        os.link(origen, destino)
    except OSError:
        shutil.copy2(origen, destino)
    return destino


def guardar_archivo(pid, seccion, nombre, datos, tema=None):
    c = carpeta(pid)
    d, ext = _dir_seccion(c, seccion, tema)
    if Path(nombre).suffix.lower() in VECTOR_EXT and seccion in ("capas", "clips", "kit"):
        datos = vector_a_png(datos, Path(nombre).suffix.lower())     # logo en vector -> PNG transparente
        nombre = Path(nombre).stem + ".png"
    if Path(nombre).suffix.lower() not in ext:
        real = detectar_extension(datos)      # sin extensión o con una rara: se mira qué es por dentro
        if real and real in ext:
            nombre = Path(nombre).stem + real if Path(nombre).suffix.lower() in ("", ".bin", ".tmp", ".download", ".crdownload") or not Path(nombre).suffix else nombre + real
        else:
            raise gd.ErrorMotor(f"'{nombre}': este tipo de archivo no se puede usar aquí." + (" Los .heic/.heif conviértelos antes a JPG." if Path(nombre).suffix.lower() in (".heic", ".heif") else ""))
    if len(datos) > LIMITE_MB * 1024 * 1024:
        raise gd.ErrorMotor(f"'{nombre}' pesa demasiado (máximo {LIMITE_MB} MB).")
    d.mkdir(parents=True, exist_ok=True)
    if seccion == "guiones" and Path(nombre).suffix.lower() in AUDIO_EXT:
        _limite("guiones", sum(1 for q in d.iterdir() if q.suffix.lower() in AUDIO_EXT), "guiones")
    elif seccion == "clips" and (tema or "general") not in ("kit",):
        _limite("archivos", sum(1 for q in d.iterdir() if q.is_file()), "archivos por carpeta de palabras clave")
    if seccion == "guiones":  # guiones conservan su nombre (01.mp3 + 01.txt)
        destino = d / re.sub(r"[^\w\-. ]+", "_", Path(nombre).name, flags=re.UNICODE)
    else:
        destino = _nombre_libre(d, nombre)
    if seccion != "guiones":      # un mismo archivo no puede estar dos veces en la misma carpeta (en otra carpeta de palabras clave sí)
        igual = _repetido_en(d, datos)
        if igual:
            raise Duplicado(f"{nombre}|{igual}")
    _escribir_sin_repetir(destino, datos)
    if seccion == "capas" and destino.suffix.lower() in VIDEO_EXT | {".gif"} and destino.suffix.lower() != ".gif":
        gd.hacer_miniatura_video(destino)
    if seccion == "capas":
        _asegurar_capa(c, destino.name)
    return destino.name


# ----------------------------------------------------------------------------
# Capas encima del video (logos, PNG, GIF y videos con transparencia)
# ----------------------------------------------------------------------------
def _leer_capas_json(c):
    try:
        lista = json.loads((c / "capas.json").read_text(encoding="utf-8"))
        return lista if isinstance(lista, list) else []
    except (OSError, ValueError):
        return []


def _asegurar_capa(c, nombre):
    lista = _leer_capas_json(c)
    if not any(isinstance(x, dict) and x.get("archivo") == nombre for x in lista):
        lista.append(gd.capa_defecto(nombre))
        (c / "capas.json").write_text(json.dumps(lista, ensure_ascii=False, indent=1), encoding="utf-8")


def listar_capas(pid):
    """Las capas del producto (cada archivo de la carpeta 'capas' con su configuración)."""
    c = carpeta(pid)
    d = c / "capas"
    guardadas = {x.get("archivo"): x for x in _leer_capas_json(c) if isinstance(x, dict)}
    res = []
    if d.is_dir():
        for p in sorted(d.iterdir(), key=gd.clave_natural):
            if p.is_file() and not p.name.startswith("_") and p.suffix.lower() in IMG_EXT | VIDEO_EXT:
                cap = gd.limpiar_capa(dict(guardadas.get(p.name) or gd.capa_defecto(p.name), archivo=p.name))
                cap["tipo"] = "imagen" if p.suffix.lower() in gd.CAPA_ESTATICAS else "animada"
                res.append(cap)
    return res


def guardar_capas(pid, capas):
    c = carpeta(pid)
    existentes = {x["archivo"] for x in listar_capas(pid)}
    limpias = [gd.limpiar_capa(x) for x in (capas or []) if isinstance(x, dict) and Path(str(x.get("archivo", ""))).name in existentes][:30]
    (c / "capas.json").write_text(json.dumps(limpias, ensure_ascii=False, indent=1), encoding="utf-8")
    return listar_capas(pid)


def _seguro(d, nombre):
    p = (d / Path(nombre).name).resolve()
    if p.parent != d.resolve() or not p.is_file():
        raise gd.ErrorMotor("No encuentro ese archivo.")
    return p


# ----------------------------------------------------------------------------
# Papelera: lo que se "borra" se guarda 30 días y se puede recuperar
# ----------------------------------------------------------------------------
DIAS_PAPELERA = 30


def _a_papelera(c, archivos, etiqueta, seccion, extra=None):
    """Mueve los archivos (rutas dentro del producto c) a la papelera como UNA entrada."""
    import time, uuid
    archivos = [Path(a) for a in archivos if Path(a).exists()]
    if not archivos and not extra:
        return None
    eid = f"{int(time.time())}_{uuid.uuid4().hex[:6]}"
    dest = c / "papelera" / eid
    dest.mkdir(parents=True, exist_ok=True)
    meta = {"etiqueta": etiqueta, "seccion": seccion, "ts": time.time(), "archivos": [], **(extra or {})}
    for i, a in enumerate(archivos):
        guardado = f"{i}_{a.name}"
        meta["archivos"].append({"guardado": guardado, "origen": a.relative_to(c).as_posix(), "tam": a.stat().st_size})
        shutil.move(str(a), str(dest / guardado))
    (dest / "meta.json").write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8")
    return eid


def _vaciar_viejos(c):
    import time
    raiz = c / "papelera"
    if not raiz.exists():
        return
    for d in raiz.iterdir():
        try:
            m = json.loads((d / "meta.json").read_text(encoding="utf-8"))
            if time.time() - m.get("ts", 0) > DIAS_PAPELERA * 86400:
                shutil.rmtree(d, ignore_errors=True)
        except Exception:
            shutil.rmtree(d, ignore_errors=True)


def listar_papelera(pid):
    c = carpeta(pid)
    _vaciar_viejos(c)
    raiz = c / "papelera"
    salida = []
    if raiz.exists():
        import time
        for d in raiz.iterdir():
            try:
                m = json.loads((d / "meta.json").read_text(encoding="utf-8"))
            except Exception:
                continue
            tam = sum(a.get("tam", 0) for a in m["archivos"])
            quedan = max(0, int(DIAS_PAPELERA - (time.time() - m["ts"]) / 86400))
            salida.append({"nombre": d.name, "etiqueta": m["etiqueta"], "seccion": m["seccion"], "ts": m["ts"],
                           "tam": tam, "archivos": len(m["archivos"]), "dias": quedan,
                           "detalle": ", ".join((m.get("tema") or {}).get("palabras", []))[:90]})
    return sorted(salida, key=lambda e: e["ts"], reverse=True)


def restaurar_papelera(pid, ids):
    c = carpeta(pid)
    n = 0
    for eid in ids:
        d = c / "papelera" / Path(str(eid)).name
        try:
            m = json.loads((d / "meta.json").read_text(encoding="utf-8"))
        except Exception:
            continue
        if m.get("tema"):           # un tema de palabras clave vuelve con sus palabras y su carpeta de clips
            nombre_t = _nombre_tema(m["tema"]["nombre"])
            temas = leer_temas(pid)
            temas.setdefault(nombre_t, [])
            temas[nombre_t] = list(dict.fromkeys(temas[nombre_t] + [w for w in m["tema"].get("palabras", []) if not any(w in v for k, v in temas.items() if k != nombre_t)]))
            guardar_temas(pid, temas)
            (c / "clips" / nombre_t).mkdir(parents=True, exist_ok=True)
        for a in m["archivos"]:
            destino = (c / a["origen"]).resolve()
            if c.resolve() not in destino.parents:
                continue
            if not destino.parent.exists() and a["origen"].startswith("clips/"):
                destino = c / "clips" / "general" / destino.name   # el tema ya no existe: va a los clips generales
            destino.parent.mkdir(parents=True, exist_ok=True)
            if destino.exists():
                destino = _nombre_libre(destino.parent, destino.stem + "_recuperado" + destino.suffix)
            shutil.move(str(d / a["guardado"]), str(destino))
        shutil.rmtree(d, ignore_errors=True)
        n += 1
    return n


def borrar_de_papelera(pid, ids):
    c = carpeta(pid)
    n = 0
    for eid in ids:
        d = c / "papelera" / Path(str(eid)).name
        if d.is_dir():
            shutil.rmtree(d, ignore_errors=True)
            n += 1
    return n


def vaciar_papelera(pid):
    return borrar_de_papelera(pid, [e["nombre"] for e in listar_papelera(pid)])


def borrar_archivo(pid, seccion, nombre, tema=None, que=None):
    """'Borra' un archivo: lo manda a la papelera (se puede recuperar).
    En guiones, `que` dice qué se borra: 'ambos' (audio y texto, por defecto), 'texto' o 'audio'."""
    c = carpeta(pid)
    d, _ = _dir_seccion(c, seccion, tema)
    p = _seguro(d, nombre)
    archivos = [p]
    if seccion == "guiones":
        que = que if que in ("texto", "audio") else "ambos"
        es_audio = p.suffix.lower() in AUDIO_EXT
        grupo_texto = [p.with_suffix(".txt"), p.with_suffix(".burbujas.json"), p.with_suffix(".titulo.json")]
        if es_audio and que == "audio":
            archivos = [p]
        elif es_audio and que == "texto":
            archivos = grupo_texto                      # el audio se queda
        elif es_audio:
            archivos = [p] + grupo_texto
        elif que == "audio":                            # guion que solo tiene texto: no hay audio que borrar
            archivos = []
        else:
            archivos = grupo_texto
    eid = _a_papelera(c, archivos, archivos[0].name if archivos else p.name, seccion)
    if seccion == "guiones" and not p.exists():
        poner_guion_limpio(c, p.name)
    return eid is not None


def poner_guion_limpio(c, nombre):
    apagados = gd.guiones_apagados(c / "guiones")
    if nombre in apagados:
        apagados.discard(nombre)
        (c / "guiones_apagados.json").write_text(json.dumps(sorted(apagados), ensure_ascii=False), encoding="utf-8")


def poner_guion(pid, nombre, activo):
    """Enciende o apaga un guion (apagado = no se usa al crear videos, pero no se borra)."""
    c = carpeta(pid)
    _seguro(c / "guiones", nombre)
    apagados = gd.guiones_apagados(c / "guiones")
    (apagados.discard if activo else apagados.add)(nombre)
    (c / "guiones_apagados.json").write_text(json.dumps(sorted(apagados), ensure_ascii=False), encoding="utf-8")


def renombrar_guion(pid, nombre, nuevo):
    """Cambia el nombre de un guion llevándose todo lo suyo (audio, texto, título y burbujas). Devuelve el nombre nuevo."""
    c = carpeta(pid)
    d = c / "guiones"
    p = _seguro(d, nombre)
    base = gd.limpiar_nombre(Path(nuevo).stem if Path(nuevo or "").suffix.lower() in (set(AUDIO_EXT) | {".txt"}) else (nuevo or ""))
    if not base:
        raise gd.ErrorMotor("Escribe un nombre.")
    if base.lower() == p.stem.lower():
        return p.name
    if any(x.is_file() and x.stem.split(".")[0].lower() == base.lower() for x in d.iterdir()):
        raise gd.ErrorMotor("Ya hay un guion con ese nombre.")
    grupo = [p] + [p.with_suffix(s) for s in (".txt", ".burbujas.json", ".titulo.json")]
    nuevo_p = p.with_name(base + p.suffix)
    for f in grupo:
        if f.is_file():
            f.rename(f.with_name(base + f.name[len(p.stem):]))
    apagados = gd.guiones_apagados(d)
    if p.name in apagados:
        apagados.discard(p.name)
        apagados.add(nuevo_p.name)
        (c / "guiones_apagados.json").write_text(json.dumps(sorted(apagados), ensure_ascii=False), encoding="utf-8")
    return nuevo_p.name


def borrar_archivos(pid, seccion, nombres, tema=None, que=None):
    """Borra varios archivos de una vez. Devuelve cuántos borró."""
    n = 0
    for nombre in nombres[:2000]:
        try:
            if borrar_archivo(pid, seccion, nombre, tema, que):
                n += 1
        except gd.ErrorMotor:
            pass
    return n


def renombrar_archivo(pid, seccion, nombre, nuevo, tema=None):
    c = carpeta(pid)
    d, _ = _dir_seccion(c, seccion, tema)
    p = _seguro(d, nombre)
    base = re.sub(r'[<>:"/\\|?*\x00-\x1f]+', "_", Path(nuevo or "").stem).strip(" ._")[:120]
    if not base:
        raise gd.ErrorMotor("Escribe un nombre.")
    destino = p.with_name(base + p.suffix.lower())
    if destino.exists() and destino != p:
        raise gd.ErrorMotor("Ya hay un archivo con ese nombre en esta carpeta.")
    p.rename(destino)
    return destino.name


def ruta_archivo(pid, seccion, nombre, tema=None):
    c = carpeta(pid)
    d, _ = _dir_seccion(c, seccion, tema)
    return _seguro(d, nombre)


def miniatura(pid, seccion, nombre, tema=None):
    """Devuelve la ruta de un JPG chico del archivo (cache). None si no se pudo."""
    p = ruta_archivo(pid, seccion, nombre, tema)
    cache = gd.DATOS / "cache_miniaturas"
    cache.mkdir(parents=True, exist_ok=True)
    clave = hashlib.md5(f"{p}|{p.stat().st_mtime_ns}|{p.stat().st_size}".encode()).hexdigest()
    out = cache / f"{clave}.jpg"
    if out.exists():
        return out
    try:
        if p.suffix.lower() in IMG_EXT:
            from PIL import Image
            im = Image.open(p).convert("RGB")
            im.thumbnail((240, 240))
            im.save(out, "JPEG", quality=80)
        elif p.suffix.lower() in VIDEO_EXT:
            gv.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", "0.5", "-i", str(p), "-frames:v", "1",
                    "-vf", "scale=240:-2", str(out)])
            if not out.exists():
                gv.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(p), "-frames:v", "1",
                        "-vf", "scale=240:-2", str(out)])
        else:
            return None
    except Exception:
        return None
    return out if out.exists() else None


# ----------------------------------------------------------------------------
# Guiones (texto)
# ----------------------------------------------------------------------------
def leer_guion(pid, nombre):
    """nombre = nombre del audio. Devuelve texto crudo del .txt (vacío si no hay)."""
    c = carpeta(pid)
    audio = _seguro(c / "guiones", nombre)
    t = audio.with_suffix(".txt")
    return gd.leer_archivo_texto(t) if t.exists() else ""


def guardar_guion(pid, nombre, texto):
    c = carpeta(pid)
    audio = _seguro(c / "guiones", nombre)
    audio.with_suffix(".txt").write_text(texto.strip() + "\n", encoding="utf-8")
    return analizar_guion(texto)


MAX_BURBUJAS = 12


def _color_ok(valor):
    v = str(valor or "").strip()
    if not v:
        return ""
    from PIL import ImageColor
    try:
        ImageColor.getrgb(v)
        return v
    except ValueError:
        return ""


def _sonido_ok(pid, valor):
    """'' = el sonido normal, 'ninguno' = sin sonido, o el nombre de un archivo de la carpeta sonidos."""
    v = str(valor or "").strip()
    if v.lower() == "ninguno" or not v:
        return v.lower()
    if v in gd.SONIDOS_BASE:
        return v
    return v if (carpeta(pid) / "sonidos" / Path(v).name).is_file() else ""


def leer_burbujas(pid, nombre):
    """Burbujas del editor para un guion. modo 'editor' si ya se usa el editor; 'texto' si usa las marcas del .txt."""
    audio = _seguro(carpeta(pid) / "guiones", nombre)
    datos = gd.leer_burbujas_manuales(audio)
    t = audio.with_suffix(".txt")
    marcas, pos, total = 0, [], 1
    dur = round(gd.duracion(audio), 2)
    if t.exists():
        _g, cuerpo = gd.leer_texto(audio)
        limpio, m, p = gd.extraer_burbujas(cuerpo, con_pos=True)
        marcas, total = len(m), max(1, len(limpio.split()))
        # momento aproximado (solo para la vista previa; al crear el video se usa el audio real)
        pos = [{"lado": "receptor" if s == "/" else "emisor", "n": n, "t": round(min(dur, (i + 1) / total * dur), 1)} for s, n, i in p]
    return {"modo": "editor" if datos is not None else "texto", "burbujas": datos or [], "marcas_texto": marcas,
            "marcas_pos": pos, "duracion": dur,
            "grupo": dict(zip(("x", "y"), gd.leer_grupo_burbujas(audio)))}


def guardar_burbujas(pid, nombre, lista, usar_texto=False, grupo=None):
    audio = _seguro(carpeta(pid) / "guiones", nombre)
    f = audio.with_suffix(".burbujas.json")
    if usar_texto:
        f.unlink(missing_ok=True)
        return leer_burbujas(pid, nombre)
    limpias = []
    for b in (lista or [])[:MAX_BURBUJAS]:
        texto = str(b.get("texto", "")).strip()[:200]
        try:
            limpias.append({"lado": "receptor" if b.get("lado") == "receptor" else "emisor", "texto": texto,
                            "inicio": round(min(max(float(b.get("inicio", 0)), 0), 600), 2),
                            "duracion": round(min(max(float(b.get("duracion", 3)), 0.5), 30), 2)})      # lo visual (tamaño, color, letra, posición, efectos) vive solo en Estilo
        except (TypeError, ValueError):
            raise gd.ErrorMotor("Revisa los números de las burbujas (aparece en, dura y mover).")
    f.write_text(json.dumps({"burbujas": limpias}, ensure_ascii=False, indent=1), encoding="utf-8")
    return leer_burbujas(pid, nombre)


def leer_titulo(pid, nombre):
    audio = _seguro(carpeta(pid) / "guiones", nombre)
    d = gd.leer_estilo_titulo(audio)
    return {"x": int(d.get("x", 0) or 0), "y": int(d.get("y", 0) or 0), "tam": int(d.get("tam", 0) or 0),
            "color": gd.catalogo_color(d.get("color")), "fuente": str(d.get("fuente") or ""),
            "trazo": d.get("trazo") if d.get("trazo") not in (None, "") else ""}


def guardar_titulo(pid, nombre, d):
    audio = _seguro(carpeta(pid) / "guiones", nombre)
    d = d or {}
    try:
        n = lambda k, a, b: int(min(max(float(d.get(k, 0) or 0), a), b))
        limpio = {"x": n("x", -900, 900), "y": n("y", -900, 900), "tam": n("tam", 0, 300),
                  "color": gd.catalogo_color(d.get("color")), "fuente": str(d.get("fuente") or "").strip()[:80],
                  "trazo": (n("trazo", 0, 30) if d.get("trazo") not in (None, "") else "")}
    except (TypeError, ValueError):
        raise gd.ErrorMotor("Revisa los números del título.")
    f = audio.with_suffix(".titulo.json")
    if not any(v not in (0, "") for v in limpio.values()):
        f.unlink(missing_ok=True)
    else:
        f.write_text(json.dumps(limpio, ensure_ascii=False, indent=1), encoding="utf-8")
    return leer_titulo(pid, nombre)


def analizar_guion(texto):
    """Cuenta palabras, burbujas y avisa de errores de marcas « » { }."""
    avisos = []
    if texto.count("«") != texto.count("»"):
        avisos.append("burbuja_sin_cerrar_comillas")
    if texto.count("{") != texto.count("}"):
        avisos.append("burbuja_sin_cerrar_llaves")
    cuerpo = "\n".join(l for l in texto.splitlines() if not l.strip().startswith("#"))
    limpio, burbujas, pos = gd.extraer_burbujas(" ".join(cuerpo.split()), con_pos=True)
    palabras = len(limpio.split())
    if texto.count("(") != texto.count(")"):
        avisos.append("marca_sin_cerrar")
    return {"palabras": palabras, "burbujas": len(burbujas), "marcas_pos": len(pos),
            "gancho": any(l.strip().startswith("#") for l in texto.splitlines()), "avisos": avisos}


def nuevo_guion(pid, nombre=None):
    """Crea un guion vacío, solo con texto (el audio se sube después o se genera con voz). Devuelve su nombre."""
    c = carpeta(pid)
    d = c / "guiones"
    d.mkdir(exist_ok=True)
    usados = {p.stem.lower() for p in d.iterdir() if p.is_file()}
    base = gd.limpiar_nombre(nombre or "")
    if not base:
        nums = [int(x) for x in usados if x.isdigit()]
        n = (max(nums) if nums else 0) + 1
        base = f"{n:02d}"
        while base in usados:
            n += 1
            base = f"{n:02d}"
    elif base in usados:
        raise gd.ErrorMotor("Ya hay un guion con ese nombre.")
    (d / (base + ".txt")).write_text("", encoding="utf-8")
    return base + ".txt"


def agregar_guion_listo(pid, id_, idioma="es"):
    """Crea un guion (solo texto; la voz se pone después) a partir de uno de los guiones listos. Es una función del plan Pro y Agencia."""
    import guiones_listos
    import planes
    if not planes.limites().get("plantillas_nicho"):
        raise gd.ErrorMotor("Los guiones listos son parte del plan Pro y Agencia. Puedes verlos, pero para usarlos necesitas uno de esos planes (o escribir tu propio guion, que es gratis).")
    g = guiones_listos.obtener(id_, idioma)
    if not g:
        raise gd.ErrorMotor("No encuentro ese guion listo.")
    c = carpeta(pid)
    d = c / "guiones"
    d.mkdir(exist_ok=True)
    _limite("guiones", sum(1 for q in d.iterdir() if q.suffix.lower() in AUDIO_EXT or q.suffix.lower() == ".txt"), "guiones")
    nombre = nuevo_guion(pid, gd.limpiar_nombre(g["nombre"])[:60] or None)
    ruta = d / nombre
    ruta.write_text("# " + g["titulo"] + "\n" + g["texto"] + "\n", encoding="utf-8")
    if g["burbujas"]:
        n = len(g["burbujas"])
        (d / (ruta.stem + ".burbujas.json")).write_text(json.dumps({"burbujas": [{"lado": lado, "texto": txt, "inicio": round(3 + 4 * i, 2), "duracion": 4}
                                                                     for i, (lado, txt) in enumerate(g["burbujas"])]}, ensure_ascii=False, indent=1), encoding="utf-8")
    return nombre


def texto_hablado(pid, nombre):
    """Lo que dice el audio de este guion: el texto sin el título (#) y sin las marcas de burbuja."""
    d = carpeta(pid) / "guiones"
    _gancho, cuerpo = gd.leer_texto(d / (Path(nombre).stem + ".txt"))
    limpio, _marcas = gd.extraer_burbujas(cuerpo)
    return limpio


def _ruta_clave_el():
    gd.DATOS.mkdir(parents=True, exist_ok=True)
    return gd.DATOS / "elevenlabs.json"


def clave_elevenlabs():
    try:
        return str(json.loads(_ruta_clave_el().read_text(encoding="utf-8")).get("clave", "")).strip()
    except Exception:
        return ""


def guardar_clave_elevenlabs(clave):
    clave = (clave or "").strip()
    if clave:
        _ruta_clave_el().write_text(json.dumps({"clave": clave}), encoding="utf-8")
    else:
        _ruta_clave_el().unlink(missing_ok=True)


def exigir_elevenlabs():
    import planes
    if not planes.limites().get("voz_elevenlabs"):
        raise gd.ErrorMotor("Las voces de ElevenLabs están en los planes de pago (Básico y Pro). Mejora tu plan en «Mi plan».")


def generar_voz(pid, nombre, voz="", velocidad=0, reemplazar=False, motor="windows"):
    """Narra el texto del guion con una voz de Windows y guarda el audio con el mismo nombre (.wav)."""
    import voz as motor_voz
    c = carpeta(pid)
    d = c / "guiones"
    stem = Path(nombre).stem
    texto = texto_hablado(pid, nombre)
    if not texto.strip():
        raise gd.ErrorMotor("Escribe primero el texto del guion (lo que debe decir la voz).")
    audios = [p for p in d.iterdir() if p.is_file() and p.suffix.lower() in AUDIO_EXT and p.stem == stem]
    if audios and not reemplazar:
        raise gd.ErrorMotor("Este guion ya tiene audio. Confirma si quieres reemplazarlo.")
    if not audios:
        _limite("guiones", sum(1 for q in d.iterdir() if q.suffix.lower() in AUDIO_EXT), "guiones")
    el = motor == "elevenlabs"
    if el:
        exigir_elevenlabs()
        clave = clave_elevenlabs()
        if not clave:
            raise gd.ErrorMotor("Primero conecta tu cuenta de ElevenLabs pegando tu clave.")
    ext = ".mp3" if el else ".wav"
    temporal = d / ("_voz_temporal" + ext)       # empieza con _ : la lista de guiones lo ignora
    try:
        if el:
            motor_voz.el_sintetizar(texto, temporal, clave, voz, velocidad)
        else:
            motor_voz.sintetizar(texto, temporal, voz, velocidad)
        if audios:                               # el audio anterior no se pierde: va a la papelera
            _a_papelera(c, audios, audios[0].name, "guiones")
        destino = d / (stem + ext)
        os.replace(temporal, destino)
    finally:
        temporal.unlink(missing_ok=True)
    return destino.name


def guardar_grabacion(pid, nombre, datos, tipo="", reemplazar=False):
    """Guarda como audio del guion lo que la persona grabó con el micrófono (llega en el formato del navegador: webm, ogg, mp4...)
    y lo convierte a .wav."""
    c = carpeta(pid)
    d = c / "guiones"
    stem = Path(nombre).stem
    if not any(p.stem == stem for p in d.iterdir() if p.is_file() and not p.name.startswith("_")):
        raise gd.ErrorMotor("No encuentro ese guion.")
    if not datos or len(datos) < 1000:
        raise gd.ErrorMotor("La grabación quedó vacía. Revisa tu micrófono e intenta de nuevo.")
    if len(datos) > 200 * 1024 * 1024:
        raise gd.ErrorMotor("La grabación es demasiado larga.")
    audios = [p for p in d.iterdir() if p.is_file() and p.suffix.lower() in AUDIO_EXT and p.stem == stem]
    if audios and not reemplazar:
        raise gd.ErrorMotor("Este guion ya tiene audio. Confirma si quieres reemplazarlo.")
    if not audios:
        _limite("guiones", sum(1 for q in d.iterdir() if q.suffix.lower() in AUDIO_EXT), "guiones")
    t = (tipo or "").lower()
    ext = ".webm" if "webm" in t else ".ogg" if "ogg" in t else ".m4a" if ("mp4" in t or "m4a" in t) else ".wav" if "wav" in t else ".bin"
    origen = d / ("_grab_origen" + ext)              # empiezan con _ : la lista de guiones los ignora
    temporal = d / "_grab_temporal.wav"
    try:
        origen.write_bytes(datos)
        try:
            gv.run(["ffmpeg", "-y", "-v", "error", "-i", str(origen), "-vn", "-ac", "1", "-ar", "44100", "-c:a", "pcm_s16le", str(temporal)])
        except RuntimeError:
            raise gd.ErrorMotor("No pude leer la grabación. Intenta grabar de nuevo.")
        if gd.duracion(temporal) < 1.0:
            raise gd.ErrorMotor("La grabación quedó muy corta o vacía. Revisa tu micrófono e intenta de nuevo.")
        if audios:                                   # el audio anterior no se pierde: va a la papelera
            _a_papelera(c, audios, audios[0].name, "guiones")
        destino = d / (stem + ".wav")
        os.replace(temporal, destino)
    finally:
        origen.unlink(missing_ok=True)
        temporal.unlink(missing_ok=True)
    return destino.name


_DUR = {}


def _duracion_cache(p):
    """Duración de un audio, recordada mientras el archivo no cambie (no se vuelve a medir cada vez que se abre la lista)."""
    try:
        st = p.stat()
        k = (str(p), st.st_mtime_ns, st.st_size)
        if k not in _DUR:
            _DUR[k] = round(gv.duracion(p), 2)
        return _DUR[k]
    except Exception:
        return None


_PESO = {}


def peso_base(pid):
    """Cuánto pesan, en promedio, los videos que ya hiciste en este producto: MB por segundo por megapíxel.
    Sirve para calcular el peso aproximado de los siguientes. Sin videos hechos devuelve un valor típico (n = 0)."""
    d = carpeta(pid) / "videos_finalizados"
    ks = []
    if d.exists():
        for p in sorted(d.rglob("*.mp4"), key=lambda x: x.stat().st_mtime, reverse=True)[:6]:
            try:
                st = p.stat()
                clave = (str(p), st.st_mtime_ns, st.st_size)
                if clave not in _PESO:
                    out = gv.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height", "-of", "csv=p=0", str(p)])
                    w, h = [int(x) for x in out.strip().split(",")[:2]]
                    _PESO[clave] = (st.st_size / 1e6) / (gv.duracion(p) * w * h / 1e6)
                ks.append(_PESO[clave])
            except Exception:
                continue
    if not ks:
        return {"k": 0.12, "n": 0}
    ks.sort()
    return {"k": round(ks[len(ks) // 2], 4), "n": len(ks)}


def listar_guiones(pid, para_generar=False):
    c = carpeta(pid)
    salida = []
    if para_generar:        # lo que se puede elegir en Generar: los guiones con voz y, con «Mis videos hablando», cada guion de texto (o cada video) como un guion más
        salida = [g for g in listar_guiones(pid) if g["tiene_audio"] and g["activo"]]
        for f in _entradas_h(c):
            salida.append({"nombre": f.name, "tiene_texto": f.suffix == ".txt", "tiene_audio": False, "activo": True, "hablando": True,
                           "duracion": __import__("hablado").duracion_entrada(f)})
        return sorted(salida, key=lambda g: gd.clave_natural(Path(g["nombre"])))
    apagados = gd.guiones_apagados(c / "guiones")
    archivos = sorted((c / "guiones").iterdir(), key=gd.clave_natural)
    con_audio = {p.stem.lower() for p in archivos if p.suffix.lower() in AUDIO_EXT}
    for p in archivos:
        if p.name.startswith("_"):
            continue
        if p.suffix.lower() in AUDIO_EXT:
            t = p.with_suffix(".txt")
            info = analizar_guion(gd.leer_archivo_texto(t)) if t.exists() else None
            salida.append({"nombre": p.name, "tiene_texto": t.exists(), "tiene_audio": True, "analisis": info, "activo": p.name not in apagados,
                           "duracion": _duracion_cache(p)})
        elif p.suffix.lower() == ".txt" and p.stem.lower() not in con_audio:
            # texto sin audio (por ejemplo, borraste solo el audio): se muestra para poder editarlo o borrarlo
            salida.append({"nombre": p.name, "tiene_texto": True, "tiene_audio": False,
                           "analisis": analizar_guion(gd.leer_archivo_texto(p)), "activo": False})
    return salida


# ----------------------------------------------------------------------------
# Ajustes y estilos guardados
# ----------------------------------------------------------------------------
def leer_ajustes(pid):
    cfg = catalogo.defectos()
    gd.leer_ajustes(carpeta(pid) / "ajustes.txt", cfg)
    return cfg


def guardar_ajustes(pid, valores):
    """Valida cada valor. Devuelve (ajustes_finales, errores{clave: mensaje})."""
    cfg = leer_ajustes(pid)
    antes = dict(cfg)
    errores = {}
    for k, v in valores.items():
        if k not in catalogo.POR_CLAVE:
            continue
        val, err = catalogo.validar(k, v if isinstance(v, str) else catalogo.a_texto(catalogo.POR_CLAVE[k], v))
        if err:
            errores[k] = err
        else:
            cfg[k] = val
    est = estilo_actual(pid)
    if est.get("nombre") and not est.get("modificado") and any(cfg[k] != antes.get(k) for k in cfg if k not in ("formatos_crear", "nombre_video")):
        marcar_estilo(pid, est["nombre"], True)
    idioma = config_programa().get("idioma", "es")
    (carpeta(pid) / "ajustes.txt").write_text(catalogo.texto_ajustes(cfg, idioma), encoding="utf-8-sig")
    # cada formato recuerda sus posiciones y tamaños tal como los dejaste la ultima vez
    disp = gd.leer_disposiciones(carpeta(pid))
    disp[str(cfg["formato_video"])] = {k: cfg[k] for k in gd.CLAVES_DISPOSICION if k in cfg}
    gd.guardar_disposiciones(carpeta(pid), disp)
    return cfg, errores


# claves que NO se copian al guardar/aplicar un estilo (son del producto, no del look)
_PROPIAS = {"cta", "usuario", "musica_archivo", "formatos_crear"}


def aplicar_formato(pid, formato):
    """Cambia el formato del video y pone las posiciones y tamaños recomendados para ese formato.
    No toca colores, letras ni efectos."""
    if formato not in catalogo.FORMATOS:
        raise gd.ErrorMotor("Formato desconocido.")
    valores = {"formato_video": formato}
    origen = dict(catalogo.PRESETS_FORMATO[formato])
    origen.update(gd.leer_disposiciones(carpeta(pid)).get(formato, {}))   # lo que dejaste la ultima vez en ese formato
    for k, v in origen.items():
        if k in catalogo.POR_CLAVE:
            valores[k] = v if isinstance(v, str) else catalogo.a_texto(catalogo.POR_CLAVE[k], v)
    return guardar_ajustes(pid, valores)


def listar_estilos():
    return sorted(p.stem for p in _estilos().glob("*.json"))


def guardar_estilo(nombre, valores, pid=None):
    n = gd.limpiar_nombre(nombre or "")
    if not n:
        raise gd.ErrorMotor("Escribe un nombre para el estilo.")
    datos = {k: v for k, v in valores.items() if k in catalogo.POR_CLAVE and k not in _PROPIAS}
    if pid:   # el estilo lleva tambien las posiciones de cada formato (vertical, retrato, cuadrado, horizontal)
        datos["_disposiciones"] = gd.leer_disposiciones(carpeta(pid))
    (_estilos() / f"{n}.json").write_text(json.dumps(datos, ensure_ascii=False, indent=1), encoding="utf-8")
    return n


def aplicar_estilo(pid, nombre):
    f = _estilos() / f"{gd.limpiar_nombre(nombre)}.json"
    if not f.exists():
        raise gd.ErrorMotor("No encuentro ese estilo.")
    datos = json.loads(f.read_text(encoding="utf-8"))
    disp = datos.pop("_disposiciones", None)
    if isinstance(disp, dict) and disp:
        gd.guardar_disposiciones(carpeta(pid), {k: v for k, v in disp.items() if isinstance(v, dict)})
    # un estilo viejo (sin posiciones por formato) hecho para otro formato no trae sus posiciones ni tamaños (no cabrían)
    elif datos.get("formato_video", "vertical") != leer_ajustes(pid).get("formato_video"):
        for k in list(catalogo.PRESETS_FORMATO["cuadrado"]) + ["formato_video"]:
            datos.pop(k, None)
    r = guardar_ajustes(pid, {k: catalogo.a_texto(catalogo.POR_CLAVE[k], v) for k, v in datos.items()})
    marcar_estilo(pid, nombre)
    return r


def borrar_estilo(nombre):
    (_estilos() / f"{gd.limpiar_nombre(nombre)}.json").unlink(missing_ok=True)


# ----------------------------------------------------------------------------
# Videos terminados
# ----------------------------------------------------------------------------
def listar_videos(pid):
    """Videos terminados, con la carpeta del formato en que quedaron (vertical, cuadrado, personalizado/1200x800...)."""
    d = carpeta(pid) / "videos_finalizados"
    if not d.exists():
        return []
    res = []
    for p in sorted(d.rglob("*.mp4"), key=lambda x: x.stat().st_mtime, reverse=True):
        rel = p.relative_to(d)
        res.append({"nombre": rel.as_posix(), "titulo": p.stem, "formato": rel.parent.as_posix() if rel.parent != Path(".") else "",
                    "tam": p.stat().st_size})
    return res


def texto_publicar(pid, nombre, idioma="es"):
    """Descripción y hashtags sugeridos para un video, armados con su título, su guion, el nombre del producto y los temas de clips (sin IA)."""
    c = carpeta(pid)
    stem = Path(nombre).stem
    m = re.search(r"_guion_(.+)$", stem)
    texto, titulo = "", ""
    if m:
        for g in (c / "guiones").glob(m.group(1) + ".*"):
            if g.suffix.lower() == ".txt":
                texto = gd.leer_archivo_texto(g)
        if not texto:
            for g in (c / "guiones").iterdir():
                if g.stem.lower() == m.group(1).lower() and g.suffix.lower() == ".txt":
                    texto = gd.leer_archivo_texto(g)
    lineas = []
    for l in texto.splitlines():
        l = l.strip()
        if l.startswith("#"):
            titulo = l.lstrip("# ").strip()
        elif l:
            lineas.append(l)
    cuerpo = re.sub(r"\(\s*[*/]\d+\s*\)|[*/]\d+", "", " ".join(lineas))
    frases = [f.strip() for f in re.split(r"(?<=[.!?])\s+", cuerpo) if f.strip()]
    resumen = " ".join(frases[:2])[:260]
    try:
        prod = next((r["nombre"] for r in listar_productos() if r.get("id") == pid), pid)
    except Exception:
        prod = pid
    temas = []
    cl = c / "clips"
    if cl.exists():
        temas = [t.name for t in sorted(cl.iterdir()) if t.is_dir() and t.name.lower() not in ("general", "kit") and not t.name.startswith("_")]
    def tag(x):
        x = re.sub(r"[^0-9A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+", "", x.title())
        return "#" + x if len(x) > 2 else ""
    etiquetas = []
    for x in [prod] + temas:
        t_ = tag(x)
        if t_ and t_ not in etiquetas:
            etiquetas.append(t_)
    base = ["#reels", "#videocorto"] if idioma != "en" else ["#reels", "#shorts"]
    etiquetas = (etiquetas + [b for b in base if b not in etiquetas])[:8]
    cab = titulo or prod
    import planes
    enlace = planes.enlace_publico()
    partes = [cab, resumen, "👉 " + ("¿Te interesa? Escríbenos." if idioma != "en" else "Interested? Message us."), ("🔗 " + enlace) if enlace else "", " ".join(etiquetas)]
    return {"texto": "\n\n".join(p for p in partes if p)}


def renombrar_video(pid, nombre, nuevo):
    p = ruta_video(pid, nombre)
    antes = p.relative_to(carpeta(pid) / "videos_finalizados").as_posix()
    base = re.sub(r'[<>:"/\\|?*\x00-\x1f]+', "_", Path(nuevo or "").stem).strip(" ._")[:120]
    if not base:
        raise gd.ErrorMotor("Escribe un nombre para el video.")
    destino = p.with_name(base + ".mp4")
    if destino.exists() and destino != p:
        raise gd.ErrorMotor("Ya hay un video con ese nombre.")
    p.rename(destino)
    _historial_renombrado(antes, destino.relative_to(carpeta(pid) / "videos_finalizados").as_posix(), pid)
    return destino.relative_to(carpeta(pid) / "videos_finalizados").as_posix()


def borrar_video(pid, nombre):
    c = carpeta(pid)
    p = ruta_video(pid, nombre)
    _a_papelera(c, [p], p.name, "videos")


def borrar_videos(pid, nombres):
    n = 0
    for nombre in nombres[:2000]:
        try:
            borrar_video(pid, nombre)
            n += 1
        except gd.ErrorMotor:
            pass
    return n


def ruta_video(pid, nombre):
    raiz = (carpeta(pid) / "videos_finalizados").resolve()
    p = (raiz / str(nombre)).resolve()
    if raiz not in p.parents or not p.is_file():
        raise gd.ErrorMotor("No encuentro ese archivo.")
    return p


# ----------------------------------------------------------------------------
# Historial: que videos se hicieron, cuando, quien, con que estilo y formato (uno por usuario)
# ----------------------------------------------------------------------------
def _arch_historial():
    return Path(gd.DATOS) / "historial.json"


def _leer_historial():
    try:
        d = json.loads(_arch_historial().read_text(encoding="utf-8"))
        return d if isinstance(d, list) else []
    except Exception:
        return []


def estilo_actual(pid):
    try:
        return json.loads((carpeta(pid) / "estilo_actual.json").read_text(encoding="utf-8"))
    except Exception:
        return {"nombre": "", "modificado": False}


def marcar_estilo(pid, nombre, modificado=False):
    (carpeta(pid) / "estilo_actual.json").write_text(json.dumps({"nombre": nombre, "modificado": modificado}, ensure_ascii=False), encoding="utf-8")


def registrar_historial(pid, info, usuario):
    """Anota un video recien creado. 'info' es lo que entrega el motor (archivo, formato, medidas, numero, guion...)."""
    import datetime
    ahora = datetime.datetime.now()
    est = estilo_actual(pid)
    nombre_est = est.get("nombre") or ""
    if nombre_est and est.get("modificado"):
        nombre_est += " (modificado)"
    h = _leer_historial()
    h.append({"fecha": ahora.strftime("%Y-%m-%d"), "hora": ahora.strftime("%H:%M:%S"), "usuario": usuario,
              "producto_id": pid, "producto": pid, "video": info.get("nombre", ""), "archivo": info.get("archivo", ""),
              "formato": info.get("formato", ""), "medidas": info.get("medidas", ""), "numero": info.get("numero"),
              "guion": info.get("guion", ""), "guion_elegido": bool(info.get("guion_elegido")), "estilo": nombre_est or "—",
              "grupo": info.get("grupo", "")})
    _arch_historial().write_text(json.dumps(h[-5000:], ensure_ascii=False, indent=0), encoding="utf-8")


def _historial_renombrado(antes, ahora, pid):
    h = _leer_historial()
    cambio = False
    for e in h:
        if e.get("producto_id") == pid and e.get("archivo") == antes:
            e["archivo"], e["video"] = ahora, Path(ahora).name
            cambio = True
    if cambio:
        _arch_historial().write_text(json.dumps(h, ensure_ascii=False, indent=0), encoding="utf-8")


def listar_historial(pid=None):
    h = [e for e in _leer_historial() if not pid or e.get("producto_id") == pid]
    h.sort(key=lambda e: (e.get("fecha", ""), e.get("hora", "")), reverse=True)
    return h


def historial_csv(pid=None):
    import csv, io
    cols = ["fecha", "hora", "usuario", "producto", "video", "formato", "medidas", "guion", "estilo", "numero"]
    out = io.StringIO()
    w = csv.writer(out)
    w.writerow(["Fecha", "Hora", "Usuario", "Producto", "Video", "Formato", "Medidas", "Guion", "Estilo", "Número"])
    for e in listar_historial(pid):
        w.writerow([e.get(c, "") for c in cols])
    return "\ufeff" + out.getvalue()      # con BOM para que Excel lea bien los acentos


def fuentes_disponibles():
    """Nombres de fuentes que el usuario puede escoger (carpeta fuentes/ del programa y la del sistema)."""
    nombres = set()
    dirs = [gv.BASE / "fuentes", gd.DATOS / "fuentes"]
    import os
    if os.name == "nt":
        dirs.append(Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts")
    else:
        dirs += [Path("/usr/share/fonts"), Path("/usr/local/share/fonts")]
    for d in dirs:
        if d.exists():
            for p in d.rglob("*"):
                if p.suffix.lower() in FUENTE_EXT:
                    nombres.add(p.stem)
    return sorted(nombres, key=str.lower)


def fuentes_propias():
    """Tipografías que el usuario subió (carpeta fuentes de sus datos)."""
    d = gd.DATOS / "fuentes"
    return sorted((p.name for p in d.glob("*") if p.suffix.lower() in FUENTE_EXT), key=str.lower) if d.exists() else []


def guardar_fuente(nombre, datos):
    n = Path(nombre or "").name
    if Path(n).suffix.lower() not in FUENTE_EXT:
        raise gd.ErrorMotor("Solo se aceptan tipografías .ttf o .otf.")
    if len(datos) > 25 * 1024 * 1024 or len(datos) < 1000:
        raise gd.ErrorMotor(f"«{n}» no parece una tipografía válida.")
    try:
        from PIL import ImageFont
        import io
        ImageFont.truetype(io.BytesIO(datos), 20)
    except Exception:
        raise gd.ErrorMotor(f"«{n}» no se pudo abrir como tipografía.")
    d = gd.DATOS / "fuentes"
    d.mkdir(parents=True, exist_ok=True)
    (d / n).write_bytes(datos)
    return Path(n).stem


def borrar_fuente(nombre):
    p = gd.DATOS / "fuentes" / Path(nombre or "").name
    if p.is_file() and p.suffix.lower() in FUENTE_EXT:
        p.unlink()
        return True
    return False


# ----------------------------------------------------------------------------
# Plantillas de temas y palabras clave
# ----------------------------------------------------------------------------
def _dir_plantillas():
    d = gd.DATOS / "plantillas_temas"
    d.mkdir(parents=True, exist_ok=True)
    return d


def listar_plantillas():
    idioma = config_programa().get("idioma", "es")
    propias = []
    for f in sorted(_dir_plantillas().glob("*.json")):
        try:
            propias.append({"id": f.stem, "nombre": json.loads(f.read_text(encoding="utf-8")).get("nombre", f.stem), "tipo": "mia"})
        except Exception:
            pass
    return propias + plantillas.listar_base(idioma)


def _leer_plantilla(plid):
    idioma = config_programa().get("idioma", "es")
    if plid in plantillas.BASE:
        return plantillas.contenido_base(plid, idioma)[1]
    f = _dir_plantillas() / f"{gd.limpiar_nombre(plid)}.json"
    if not f.exists():
        raise gd.ErrorMotor("No encuentro esa plantilla.")
    return json.loads(f.read_text(encoding="utf-8"))["temas"]


def guardar_plantilla(pid, nombre):
    nombre = (nombre or "").strip()
    n = gd.limpiar_nombre(nombre)
    if not n or n in plantillas.BASE:
        raise gd.ErrorMotor("Escribe otro nombre para la plantilla.")
    temas = leer_temas(pid)
    (_dir_plantillas() / f"{n}.json").write_text(
        json.dumps({"nombre": nombre, "temas": temas}, ensure_ascii=False, indent=1), encoding="utf-8")
    return n


def borrar_plantilla(plid):
    if plid in plantillas.BASE:
        raise gd.ErrorMotor("Las plantillas de arranque no se pueden borrar.")
    (_dir_plantillas() / f"{gd.limpiar_nombre(plid)}.json").unlink(missing_ok=True)


def aplicar_plantilla(pid, plid, modo="sumar"):
    """modo 'sumar': agrega temas y palabras sin quitar nada. 'reemplazar': deja solo los de la plantilla
    (los clips de temas que desaparecen se conservan en su carpeta)."""
    nuevos = _leer_plantilla(plid)
    actual = leer_temas(pid)
    if modo == "reemplazar":
        resultado = {k: list(v) for k, v in nuevos.items()}
        resultado.setdefault("kit", [])
    else:
        resultado = {k: list(v) for k, v in actual.items()}
        usadas = {w: t for t, ws in resultado.items() for w in ws}
        for tema, palabras in nuevos.items():
            for w in palabras:
                w = gd.normalizar(w)
                if w and w not in usadas:
                    resultado.setdefault(tema, []).append(w)
                    usadas[w] = tema
    # una palabra solo en un tema (la primera que la tenga)
    vistas, limpio = set(), {}
    for t, ws in resultado.items():
        ws2 = [w for w in ws if not (w in vistas or vistas.add(w))]
        if ws2 or t == "kit":
            limpio[t] = ws2
    return guardar_temas(pid, limpio)
