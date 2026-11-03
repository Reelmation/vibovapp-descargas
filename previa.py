"""Imagen de vista previa con los ajustes actuales (aunque aun no esten guardados)."""
import io
import random
import tempfile
from pathlib import Path

from PIL import Image, ImageColor, ImageDraw

import catalogo
import core
import generar_diario as gd
import generar_video as gv


def _fondo(cfg, c):
    """Un cuadro de un clip del producto (o un degradado si aun no hay clips)."""
    W, H = cfg["ancho"], cfg["alto"]
    candidatos = gd.listar_media(c / "clips", True) + gd.listar_media(c / "kit", False)
    random.Random(7).shuffle(candidatos)
    for p in candidatos[:4]:
        try:
            if p.suffix.lower() in core.IMG_EXT:
                im = Image.open(p).convert("RGB")
            else:
                miniatura = core.gv.run  # noqa: F841  (solo para comprobar que existe)
                with tempfile.TemporaryDirectory() as t:
                    out = Path(t) / "f.png"
                    gv.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", "0.5", "-i", str(p),
                            "-frames:v", "1", str(out)])
                    im = Image.open(out).convert("RGB")
            return _cubrir(im, W, H)
        except Exception:
            continue
    img = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(img)
    for y in range(H):
        t = y / H
        d.line([(0, y), (W, y)], fill=(int(40 + 30 * t), int(60 + 20 * t), int(95 + 50 * t)))
    return img


def _cubrir(im, W, H):
    k = max(W / im.width, H / im.height)
    im = im.resize((int(im.width * k) + 1, int(im.height * k) + 1))
    x, y = (im.width - W) // 2, (im.height - H) // 2
    return im.crop((x, y, x + W, y + H))


def gv_fuente(cfg, tam):
    import generar_video as gv
    return gv.cargar_fuente(cfg, int(tam), "titulo")


def generar(pid, valores, idioma="es", burbujas=None, tiempo=None, conjunto=None, titulo=None):
    """Devuelve bytes PNG (reducido) de como se vería un cuadro del video."""
    c = core.carpeta(pid)
    cfg = catalogo.defectos()
    for k, v in (valores or {}).items():
        if k in catalogo.POR_CLAVE:
            val, err = catalogo.validar(k, v if isinstance(v, str) else catalogo.a_texto(catalogo.POR_CLAVE[k], v))
            if not err:
                cfg[k] = val
    cfg["dir"] = c
    cfg["_ver_marcas"] = bool((valores or {}).get("_ver_marcas"))
    gd.aplicar_formato(cfg)
    if gd.es_si(cfg["pantalla_completa"]):
        cfg["media_y"], cfg["media_alto"], cfg["subs_y"] = 0, cfg["alto"], cfg["subs_y_completa"]
    return _dibujar(cfg, c, idioma, burbujas, tiempo, conjunto, titulo)


def generar_formato(pid, fmt, tamano=None, idioma="es"):
    """PNG de cómo saldría el video guardado en un formato concreto (con lo que ya tienes en Estilo). Solo bytes."""
    c = core.carpeta(pid)
    cfg = gd.cargar_config(c)
    if fmt != cfg.get("formato_video"):
        cfg = gd.cfg_formato(cfg, fmt)
    if fmt == "personalizado" and tamano:
        cfg = dict(cfg)
        cfg["ancho"], cfg["alto"] = tamano
        gd.ajustar_pantalla_completa(cfg)
    return _dibujar(cfg, c, idioma, None, None, None, None)[0]


def _dibujar(cfg, c, idioma, burbujas, tiempo, conjunto, titulo):
    W, H = cfg["ancho"], cfg["alto"]
    es = idioma == "es"
    titulo = titulo or {}
    gancho = str(titulo.get("texto") or "").strip() or ("Título de ejemplo" if es else "Example title")
    cta = cfg["cta"] or ("Tu frase final" if es else "Your closing line")
    frase = "Hola, ¿me das más información?" if es else "Hi, can I get more info?"
    grupo = (["Esto", "es", "un", "ejemplo"] if es else ["This", "is", "an", "example"])[:max(1, int(cfg["subs_palabras"]))]
    aviso = False   # True si las burbujas suben hasta la zona del titulo
    cajas = {}      # elemento -> [x0, y0, x1, y1] en pixeles del video (para poder tocarlos y arrastrarlos en la vista previa)

    def _caja(nombre, im, dx=0, dy=0):
        try:
            b = im.getchannel("A").getbbox()
        except Exception:
            b = None
        if b:
            x0, y0, x1, y1 = b[0] + dx, b[1] + dy, b[2] + dx, b[3] + dy
            c0 = cajas.get(nombre)
            cajas[nombre] = [min(x0, c0[0]), min(y0, c0[1]), max(x1, c0[2]), max(y1, c0[3])] if c0 else [x0, y0, x1, y1]
    with tempfile.TemporaryDirectory() as t:
        t = Path(t)
        fondo = _fondo(cfg, c)
        # oscurecido: el promedio del rango configurado
        osc = (float(cfg["oscurecer_min"]) + float(cfg["oscurecer_max"])) / 200
        fondo = Image.blend(fondo, Image.new("RGB", fondo.size, "black"), osc).convert("RGBA")
        cfg_t, dx_t = gd.aplicar_estilo_titulo(cfg, titulo)
        capas = gd.crear_capas(cfg_t, gancho, cta, t, dx_t)
        for nombre in ("base", "titulo", "cta"):
            capa_im = Image.open(capas[nombre])
            _caja({"base": "usuario"}.get(nombre, nombre), capa_im)
            fondo.alpha_composite(capa_im)
        if gd.es_si(cfg["burbujas"]):
            pregunta = "Cliente: ¿Cuánto cuesta?" if es else "Cliente: How much is it?"
            dx_g = int(float(cfg.get("burbuja_x") or 0))
            est_g = {"brillo": True} if gd.es_si(cfg.get("burbuja_brillo", False)) else None
            if burbujas is None:      # ejemplo para ver como se acomodan
                items = [{"frase": pregunta, "t0": 0, "t1": 3, "mover": 0, "mover_x": dx_g, "estilo": est_g}, {"frase": frase, "t0": 0, "t1": 3, "mover": 0, "mover_x": dx_g, "estilo": est_g}]
            else:                     # las burbujas reales del guion; con 'tiempo' solo las visibles en ese segundo
                items = []
                for b in burbujas:
                    texto_b = str(b.get("texto", "")).strip()
                    if not texto_b:
                        continue
                    t0 = float(b.get("inicio", 0)); t1 = t0 + max(0.5, float(b.get("duracion", 3)))
                    items.append({"frase": ("Cliente: " + texto_b) if b.get("lado") == "receptor" else texto_b,
                                  "t0": t0, "t1": t1, "mover": 0, "mover_x": dx_g, "estilo": est_g})
                items.sort(key=lambda x: x["t0"])
                if tiempo is None:    # todas juntas
                    for it in items:
                        it["t0"], it["t1"] = 0, 1
                else:
                    items = [it for it in items if it["t0"] <= float(tiempo) < it["t1"]]
            for it in items:
                gd.ajustar_item_burbuja(cfg, it)
            ys = gd.colocar_burbujas(cfg, items)
            for k, (it, y1) in enumerate(zip(items, ys)):
                aviso = aviso or (y1 - gd.alto_burbuja(cfg, it["frase"], it.get("estilo")) < int(cfg["zona_segura_arriba"]))
                gd.crear_burbuja(cfg, it["frase"], t / f"b{k}.png", y1, it.get("estilo"), it.get("mover_x", 0))
                im_b = Image.open(t / f"b{k}.png")
                _caja("burbuja_cliente" if gd._es_cliente(it["frase"])[0] else "burbuja_yo", im_b)
                fondo.alpha_composite(im_b)
        gd.png_subtitulo(cfg, grupo, min(1, len(grupo) - 1), t / "s.png")
        sub = Image.open(t / "s.png")
        sub_y = int(cfg["subs_y"]) - gd.ALTO_BANDA_SUBS // 2
        sub_x = int(float(cfg.get("subs_x", 0) or 0))
        _caja("subtitulos", sub, sub_x, sub_y)
        sub_mov = Image.new("RGBA", sub.size, (0, 0, 0, 0)); sub_mov.paste(sub, (sub_x, 0), sub)
        fondo.alpha_composite(sub_mov, (0, sub_y))
        if cfg.get("_ver_marcas"):      # ejemplo de lo que se pone desde las marcas del guion: un texto y una imagen (se mueven y cambian de tamaño aquí)
            try:
                import hablado
                pw = int(W * float(cfg.get("marca_img_pct", 55) or 55) / 100); ph = int(pw * 0.62)
                cxi = W // 2 + int(float(cfg.get("marca_img_x", 0) or 0)); cyi = int(H * float(cfg.get("marca_img_y", 47) or 47) / 100)
                im_i = Image.new("RGBA", (W, H), (0, 0, 0, 0)); di = ImageDraw.Draw(im_i)
                di.rounded_rectangle((cxi - pw // 2, cyi - ph // 2, cxi + pw // 2, cyi + ph // 2), radius=24, fill=(255, 255, 255, 70), outline=(255, 255, 255, 190), width=4)
                di.text((cxi, cyi), "🖼" if False else ("Imagen" if es else "Image"), fill=(255, 255, 255, 220), anchor="mm", font=gv_fuente(cfg, max(28, pw // 9)))
                _caja("marca_imagen", im_i); fondo.alpha_composite(im_i)
                tx, _p = hablado.planear_textos(dict(cfg, dir=str(c)), [["x", 0.0, 1.0, [{"t": "fx", "txt": True, "texto": "Texto marcado" if es else "Marked text", "n": 0, "antes": True, "seg": 5}]]], 10.0, t)
                for png, *_r in tx:
                    im_t = Image.open(png).convert("RGBA"); _caja("marca_texto", im_t); fondo.alpha_composite(im_t)
            except Exception:
                pass
        if gd.es_si(cfg["barra_progreso"]):
            d = ImageDraw.Draw(fondo)
            col = ImageColor.getrgb(cfg["color_barra"] or cfg["subs_color_activo"])[:3]
            y0 = int(cfg["barra_y"])
            d.rectangle((0, y0, int(W * 0.4), y0 + int(cfg["barra_alto"])), fill=col)
            cajas["barra"] = [0, y0 - 14, W, y0 + int(cfg["barra_alto"]) + 14]
        for cp in gd.leer_capas(cfg.get("dir")):      # capas (logos, etc.) encima de todo
            im_c = gd.miniatura_capa(cp["ruta"])
            if im_c is None or im_c.width < 1:
                continue
            wl = max(16, int(W * cp["ancho"] / 100) // 2 * 2)
            im_c = im_c.resize((wl, max(1, round(im_c.height * wl / im_c.width))), Image.LANCZOS)
            if cp["opacidad"] < 100:
                im_c.putalpha(im_c.getchannel("A").point(lambda v: int(v * cp["opacidad"] / 100)))
            px, py = gd.posicion_capa(W, H, im_c.width, im_c.height, cp["pos"], cp["dx"], cp["dy"])
            lienzo_c = Image.new("RGBA", fondo.size, (0, 0, 0, 0))
            lienzo_c.paste(im_c, (px, py))
            fondo.alpha_composite(lienzo_c)
        fondo = fondo.convert("RGB")
        fondo.thumbnail((540, 960))
        buf = io.BytesIO()
        fondo.save(buf, "PNG")
        cajas["_tam"] = [W, H]
        cajas["_completa"] = bool(gd.es_si(cfg["pantalla_completa"]))
        return buf.getvalue(), aviso, cajas
