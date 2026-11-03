"""Servidor local: la ventana del programa habla con este servidor (solo en tu computadora)."""
import json
import os
import re
import shutil
import subprocess
import sys
import threading
import time
import webbrowser
from pathlib import Path
from urllib.parse import quote

from flask import Flask, jsonify, request, send_file, send_from_directory, Response

import actualizador
import catalogo
import core
import errores
import planes
import marca
import novedades
import usuarios
import previa
import generar_diario as gd
import generar_video as gv

BASE = Path(__file__).resolve().parent
VENTANA_PROPIA = False
ELEGIR_ARCHIVOS = None      # lo pone iniciar.py cuando hay ventana propia: abre el selector de archivos en una carpeta   # lo pone iniciar.py cuando el programa se abre en su propia ventana (la X de la ventana es la salida)

app = Flask(__name__, static_folder=None)
app.config["MAX_CONTENT_LENGTH"] = 2 * 1024 * 1024 * 1024


# ---------------------------------------------------------------- errores
@app.errorhandler(gd.ErrorMotor)
def _err_motor(e):
    return jsonify(errores.info(str(e), errores.paso_de_ruta(request.path))), 400


@app.errorhandler(Exception)
def _err_general(e):
    from werkzeug.exceptions import HTTPException
    if isinstance(e, HTTPException):
        msg = {413: "El archivo es demasiado grande (el máximo es 2 GB). Prueba con uno más chico.",
               404: "No encontré eso. Recarga la página e intenta de nuevo.",
               405: "Esa acción no está disponible."}.get(e.code, e.description)
        r = errores.info(msg, errores.paso_de_ruta(request.path))
        r["error"] = msg
        r["codigo"] = (r.get("codigo") or "VV-0-0").rsplit("-", 1)[0] + f"-{e.code}"
        return jsonify(r), e.code
    import traceback
    traceback.print_exc()
    msg, det = errores.explicar(repr(e))
    try:                                   # queda guardado en Documentos\\Vibovapp\\errores.log para saber qué falló
        with open(gd.DATOS / "errores.log", "a", encoding="utf-8") as f:
            f.write(time.strftime("%Y-%m-%d %H:%M:%S ") + request.method + " " + request.path + "\n" + traceback.format_exc() + "\n")
    except Exception:
        pass
    if msg == errores.GENERICO:
        msg = "Algo falló en el programa."
    r = errores.info(repr(e), errores.paso_de_ruta(request.path))
    r["error"] = msg
    return jsonify(r), 500


# ---------------------------------------------------------------- sesion de usuario
_LIBRES = ("/api/celular", "/api/usuarios", "/api/config", "/api/inicio", "/api/catalogo", "/api/salir", "/api/generar/estado", "/api/actualizacion", "/api/plan", "/api/novedades")


import celular


@app.before_request
def _guardia_celular():
    return celular.guardia()


@app.get("/api/celular")
def celular_estado():
    if not celular.es_local():          # desde el celular no se muestra ni se maneja este acceso
        return jsonify({"activo": True, "solo_pc": True})
    return jsonify(celular.estado())


@app.post("/api/celular")
def celular_cambiar():
    if not celular.es_local():
        return jsonify({"error": "Solo desde la computadora."}), 403
    d = request.json or {}
    if d.get("desconectar"):
        celular.desconectar(str(d["desconectar"]))
    elif "remoto" in d:
        if d["remoto"]:
            celular.activar(app); celular.activar_remoto()
        else:
            celular.apagar_remoto()
    elif d.get("activo"):
        celular.activar(app)
    elif "activo" in d:
        celular.apagar()
    return jsonify(celular.estado())


@app.before_request
def _requiere_usuario():
    p = request.path
    if p.startswith("/api/") and usuarios.ACTIVO is None and not p.startswith(_LIBRES):
        return jsonify({"error": "Primero elige un usuario."}), 409


@app.get("/api/usuarios")
def usuarios_listar():
    return jsonify(usuarios.listar())


@app.post("/api/usuarios")
def usuarios_crear():
    uid = usuarios.crear((request.json or {}).get("nombre"))
    return jsonify({"id": uid})


def _sin_trabajo():
    if T.activo:
        raise gd.ErrorMotor("Hay videos creándose. Espera a que terminen o deténlos antes de cambiar de usuario.")


@app.post("/api/usuarios/activar")
def usuarios_activar():
    _sin_trabajo()
    usuarios.activar((request.json or {}).get("id"))
    return jsonify({"ok": True})


@app.post("/api/usuarios/cerrar")
def usuarios_cerrar():
    _sin_trabajo()
    usuarios.cerrar_sesion()
    return jsonify({"ok": True})


@app.post("/api/usuarios/renombrar")
def usuarios_renombrar():
    d = request.json or {}
    usuarios.renombrar(d.get("id"), d.get("nombre"))
    return jsonify({"ok": True})


@app.post("/api/referencia")
def referencia_subir():
    import referencia
    f = request.files.get("archivo")
    if not f:
        raise gd.ErrorMotor("Elige un video.")
    return jsonify(referencia.guardar(f.filename, f.read()))


@app.get("/api/referencia/video")
def referencia_video():
    import referencia
    r = referencia.ruta_video()
    if not r:
        return jsonify({"error": "No hay video de referencia."}), 404
    return send_file(str(r), conditional=True)


@app.post("/api/usuarios/unico")
def usuario_unico():
    uid = usuarios.unico()
    usuarios.activar(uid)
    return jsonify({"id": uid})


@app.delete("/api/usuarios/<uid>")
def usuarios_borrar(uid):
    usuarios.borrar(uid)
    return jsonify({"ok": True})


@app.post("/api/salir")
def salir():
    """Cierra el programa. Si hay videos en proceso, hay que confirmar (forzar)."""
    if T.activo and not (request.json or {}).get("forzar"):
        return jsonify({"error": "Hay videos creándose. Si sales ahora se detienen.", "ocupado": True}), 409
    gd.CANCELAR.set()
    threading.Timer(0.8, lambda: os._exit(0)).start()
    return jsonify({"ok": True})


# ---------------------------------------------------------------- web
@app.get("/")
def index():
    return send_from_directory(BASE / "web", "index.html")


@app.get("/favicon.ico")
def favicon():
    return send_from_directory(BASE / "web", "favicon.png")


@app.get("/web/<path:f>")
def web(f):
    return send_from_directory(BASE / "web", f)


# ---------------------------------------------------------------- programa
@app.get("/api/inicio")
def inicio():
    if usuarios.ACTIVO is None:
        return jsonify({"marca": marca.NOMBRE, "version": marca.VERSION, "titular": marca.TITULAR, "anio_inicio": marca.ANIO_INICIO, "ventana_propia": VENTANA_PROPIA, "usuario": None,
                        "tema": usuarios.tema(), "tema_elegido": usuarios.tema_elegido(), "idioma_elegido": usuarios.idioma_elegido(),
                        "config": {"idioma": usuarios.idioma(), "aviso_aceptado": True, "tutorial_visto": True}, "productos": []})
    cfg = core.config_programa()
    quien = next((u for u in usuarios.listar()["usuarios"] if u["id"] == usuarios.ACTIVO), None)
    return jsonify({"marca": marca.NOMBRE, "version": marca.VERSION, "titular": marca.TITULAR, "anio_inicio": marca.ANIO_INICIO, "ventana_propia": VENTANA_PROPIA, "usuario": quien, "config": cfg,
                    "tema": usuarios.tema(), "tema_elegido": usuarios.tema_elegido(), "idioma_elegido": usuarios.idioma_elegido(), "productos": core.listar_productos()})


@app.post("/api/config")
def config():
    d = request.json or {}
    if d.get("idioma"):
        usuarios.idioma(d["idioma"])
    if d.get("tema"):
        usuarios.tema(d["tema"])
        if len(d) == 1:
            return jsonify({"tema": usuarios.tema()})
    if usuarios.ACTIVO is None:
        return jsonify({"idioma": usuarios.idioma(), "tema": usuarios.tema()})
    return jsonify(core.guardar_config_programa(**d))


@app.get("/api/catalogo")
def api_catalogo():
    return jsonify({
        "categorias": [{"id": c[0], "es": c[1], "en": c[2]} for c in catalogo.CATEGORIAS],
        "ajustes": catalogo.AJUSTES,
        "transiciones": {k: {"es": v[0], "en": v[1]} for k, v in catalogo.NOMBRES_TRANSICIONES.items()},
        "efectos": {k: {"es": v[0], "en": v[1]} for k, v in catalogo.NOMBRES_EFECTOS.items()},
        "entradas_burbuja": {k: {"es": v[0], "en": v[1]} for k, v in catalogo.ENTRADAS_BURBUJA.items()},
        "salidas_burbuja": {k: {"es": v[0], "en": v[1]} for k, v in catalogo.SALIDAS_BURBUJA.items()},
        "fuentes": core.fuentes_disponibles(),
        "formas_burbuja": {k: {"es": v[0], "en": v[1]} for k, v in catalogo.FORMAS_BURBUJA.items()},
        "estilos_listos": {k: {"es": v[0], "en": v[1], "des": v[2], "den": v[3], "valores": v[4]} for k, v in catalogo.ESTILOS_LISTOS.items()},
    })


# ---------------------------------------------------------------- tipografías y sonidos propios
@app.get("/api/fuentes")
def fuentes_listar():
    return jsonify({"propias": core.fuentes_propias(), "todas": core.fuentes_disponibles()})


@app.post("/api/fuentes")
def fuentes_subir():
    ok, fallos = [], []
    for f in request.files.getlist("archivos"):
        try:
            ok.append(core.guardar_fuente(f.filename, f.read()))
        except gd.ErrorMotor as e:
            fallos.append(str(e))
    return jsonify({"subidas": ok, "errores": fallos, "propias": core.fuentes_propias(), "todas": core.fuentes_disponibles()})


@app.post("/api/fuentes/borrar")
def fuentes_borrar():
    core.borrar_fuente((request.json or {}).get("nombre"))
    return jsonify({"propias": core.fuentes_propias(), "todas": core.fuentes_disponibles()})


_SON_BASE = {}


@app.get("/api/sonido_base/<nombre>")
def sonido_base(nombre):
    clave = "@" + nombre
    if clave not in gd.SONIDOS_BASE:
        return ("", 404)
    if clave not in _SON_BASE:
        import subprocess, tempfile
        expr, d = gd.SONIDOS_BASE[clave]
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "s.wav"
            subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-t", str(d), "-i",
                            f"aevalsrc={expr}:s=44100:d={d}", str(out)], check=False,
                           creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            _SON_BASE[clave] = out.read_bytes() if out.is_file() else b""
    return Response(_SON_BASE[clave], mimetype="audio/wav")


# ---------------------------------------------------------------- productos
@app.get("/api/productos")
def productos():
    return jsonify(core.listar_productos())


@app.post("/api/productos")
def producto_nuevo():
    d = request.json or {}
    if d.get("copiar_de"):
        pid = core.duplicar_producto(d["copiar_de"], d.get("nombre"), bool(d.get("con_material")))
    else:
        pid = core.crear_producto(d.get("nombre"), bool(d.get("practica")))
    return jsonify({"id": pid})


@app.post("/api/productos/<pid>/renombrar")
def producto_renombrar(pid):
    core.renombrar_producto(pid, (request.json or {}).get("nombre"))
    return jsonify({"ok": True})


@app.delete("/api/productos/<pid>")
def producto_borrar(pid):
    core.borrar_producto(pid)
    return jsonify({"ok": True})


@app.get("/api/proyectos_borrados")
def proyectos_borrados():
    return jsonify(core.proyectos_borrados())


@app.post("/api/proyectos_borrados/recuperar")
def proyecto_recuperar():
    return jsonify({"id": core.recuperar_proyecto((request.json or {}).get("clave", ""))})


@app.post("/api/productos/<pid>/reiniciar")
def producto_reiniciar(pid):
    return jsonify({"mensajes": core.reiniciar(pid)})


@app.post("/api/productos/<pid>/abrir")
def producto_abrir(pid):
    sub = (request.json or {}).get("sub", "")
    c = core.carpeta(pid)
    destino = c / sub if sub in ("videos_finalizados", "clips", "kit", "musica", "guiones") else c
    destino.mkdir(exist_ok=True)
    if os.name == "nt":
        os.startfile(str(destino))  # noqa
    elif sys.platform == "darwin":
        subprocess.Popen(["open", str(destino)])
    else:
        subprocess.Popen(["xdg-open", str(destino)])
    return jsonify({"ruta": str(destino)})



# ---------------------------------------------------------------- escenas (videos sin voz, escena por escena)
@app.get("/api/productos/<pid>/escenas")
def escenas_get(pid):
    import escenas
    c = core.carpeta(pid)
    d = escenas.cargar(c)
    d["fuentes"] = escenas.fuentes(c)
    return jsonify(d)


@app.put("/api/productos/<pid>/escenas")
def escenas_put(pid):
    import escenas
    c = core.carpeta(pid)
    d = escenas.guardar(c, request.json or {})
    d["fuentes"] = escenas.fuentes(c)
    return jsonify(d)


@app.put("/api/escenas/piezas")
def escenas_piezas_put():
    import escenas
    return jsonify({"piezas": escenas.guardar_piezas((request.json or {}).get("piezas") or [])})


# ---------------------------------------------------------------- temas
@app.get("/api/productos/<pid>/temas")
def temas_get(pid):
    return jsonify(core.leer_temas(pid))


@app.put("/api/productos/<pid>/temas")
def temas_put(pid):
    return jsonify(core.guardar_temas(pid, (request.json or {}).get("temas", {})))


@app.post("/api/productos/<pid>/temas/<tema>/renombrar")
def temas_renombrar(pid, tema):
    return jsonify({"nombre": core.renombrar_tema(pid, tema, (request.json or {}).get("nuevo", ""))})


@app.delete("/api/productos/<pid>/temas/<tema>")
def temas_del(pid, tema):
    return jsonify(core.borrar_tema(pid, tema, request.args.get("modo", "todo")))


@app.get("/api/plantillas")
def plantillas_listar():
    return jsonify(core.listar_plantillas())


@app.post("/api/plantillas")
def plantillas_guardar():
    d = request.json or {}
    return jsonify({"id": core.guardar_plantilla(d.get("producto"), d.get("nombre"))})


@app.delete("/api/plantillas/<plid>")
def plantillas_borrar(plid):
    core.borrar_plantilla(plid)
    return jsonify({"ok": True})


@app.post("/api/productos/<pid>/plantillas/aplicar")
def plantillas_aplicar(pid):
    d = request.json or {}
    return jsonify(core.aplicar_plantilla(pid, d.get("id"), d.get("modo", "sumar")))


# ---------------------------------------------------------------- archivos
@app.get("/api/productos/<pid>/archivos/<seccion>")
def archivos(pid, seccion):
    return jsonify(core.listar_archivos(pid, seccion, request.args.get("tema")))


@app.post("/api/productos/<pid>/archivos/<seccion>")
def archivos_subir(pid, seccion):
    tema = request.args.get("tema")
    ok, fallos, repetidos = [], [], []
    for f in request.files.getlist("archivos"):
        try:
            ok.append(core.guardar_archivo(pid, seccion, f.filename, f.read(), tema))
        except core.Duplicado as e:
            repetidos.append(str(e).split("|")[0])
        except gd.ErrorMotor as e:
            fallos.append(str(e))
    return jsonify({"subidos": ok, "errores": fallos, "repetidos": repetidos})


@app.get("/api/productos/<pid>/papelera")
def papelera(pid):
    return jsonify(core.listar_papelera(pid))


@app.post("/api/productos/<pid>/papelera/<accion>")
def papelera_accion(pid, accion):
    ids = (request.json or {}).get("ids") or []
    if accion == "restaurar":
        return jsonify({"n": core.restaurar_papelera(pid, [str(i) for i in ids])})
    if accion == "borrar":
        return jsonify({"n": core.borrar_de_papelera(pid, [str(i) for i in ids])})
    if accion == "vaciar":
        return jsonify({"n": core.vaciar_papelera(pid)})
    raise gd.ErrorMotor("Acción desconocida.")


@app.post("/api/productos/<pid>/archivos/<seccion>/borrar")
def archivos_borrar_varios(pid, seccion):
    d = request.json or {}
    n = d.get("nombres") or []
    return jsonify({"borrados": core.borrar_archivos(pid, seccion, [str(x) for x in n], request.args.get("tema"), d.get("que"))})


@app.post("/api/productos/<pid>/archivos/<seccion>/renombrar")
def archivos_renombrar(pid, seccion):
    d = request.json or {}
    return jsonify({"nombre": core.renombrar_archivo(pid, seccion, d.get("nombre", ""), d.get("nuevo", ""), request.args.get("tema"))})


@app.post("/api/productos/<pid>/videos/borrar")
def videos_borrar_varios(pid):
    n = (request.json or {}).get("nombres") or []
    return jsonify({"borrados": core.borrar_videos(pid, [str(x) for x in n])})


@app.post("/api/productos/<pid>/archivos/<seccion>/duplicados")
def archivos_duplicados(pid, seccion):
    return jsonify({"borrados": core.quitar_duplicados(pid, seccion, request.args.get("tema"))})


@app.delete("/api/productos/<pid>/archivos/<seccion>")
def archivos_borrar(pid, seccion):
    core.borrar_archivo(pid, seccion, request.args.get("nombre", ""), request.args.get("tema"), request.args.get("que"))
    return jsonify({"ok": True})


@app.get("/api/productos/<pid>/capas")
def capas_ver(pid):
    return jsonify(core.listar_capas(pid))


@app.put("/api/productos/<pid>/capas")
def capas_guardar(pid):
    return jsonify(core.guardar_capas(pid, (request.json or {}).get("capas")))


@app.get("/api/productos/<pid>/capa_mini")
def capa_mini(pid):
    """Imagen de una capa para mostrarla en la lista (la propia imagen o el primer cuadro del video)."""
    d = core.carpeta(pid) / "capas"
    p = (d / Path(request.args.get("nombre", "")).name)
    if not p.is_file():
        return jsonify({"error": "No encontré esa capa."}), 404
    if p.suffix.lower() in IMG_EXT_WEB:
        return send_file(p, conditional=True)
    mini = p.with_name("_mini_" + p.stem + ".png")
    return send_file(mini) if mini.is_file() else (jsonify({"error": "Sin vista previa."}), 404)


@app.get("/api/productos/<pid>/archivo/<seccion>")
def archivo_ver(pid, seccion):
    p = core.ruta_archivo(pid, seccion, request.args.get("nombre", ""), request.args.get("tema"))
    return send_file(p, conditional=True)


@app.get("/api/productos/<pid>/miniatura/<seccion>")
def archivo_mini(pid, seccion):
    m = core.miniatura(pid, seccion, request.args.get("nombre", ""), request.args.get("tema"))
    if not m:
        return Response(status=204)
    return send_file(m, mimetype="image/jpeg", max_age=3600)


# ---------------------------------------------------------------- guiones
@app.get("/api/voces")
def voces():
    import voz as motor_voz
    import planes
    cfg = core.config_programa()
    clave = core.clave_elevenlabs()
    permitido = bool(planes.limites().get("voz_elevenlabs"))
    base = {"nombre": cfg.get("voz_nombre", ""), "velocidad": cfg.get("voz_velocidad", 0),
            "motor": cfg.get("voz_motor", "windows") if permitido else "windows", "el_id": cfg.get("voz_el_id", ""),
            "el": {"permitido": permitido, "conectado": bool(clave and permitido), "clave_final": clave[-4:] if clave else ""}}
    try:
        return jsonify({**base, "voces": motor_voz.listar_voces(request.args.get("forzar") == "1"), "error": ""})
    except gd.ErrorMotor as e:
        return jsonify({**base, "voces": [], "error": str(e)})


@app.post("/api/productos/<pid>/guiones/grabacion")
def guion_grabacion(pid):
    nombre = core.guardar_grabacion(pid, request.args.get("nombre", ""), request.get_data(), request.headers.get("Content-Type", ""),
                                    request.args.get("reemplazar") == "1")
    return jsonify({"nombre": nombre})


@app.get("/api/elevenlabs/voces")
def el_voces():
    import voz as motor_voz
    core.exigir_elevenlabs()
    clave = core.clave_elevenlabs()
    if not clave:
        raise gd.ErrorMotor("Primero conecta tu cuenta de ElevenLabs pegando tu clave.")
    return jsonify({"voces": motor_voz.el_voces(clave), "cuota": motor_voz.el_cuota(clave)})


@app.post("/api/elevenlabs/clave")
def el_clave():
    import voz as motor_voz
    core.exigir_elevenlabs()
    clave = ((request.json or {}).get("clave") or "").strip()
    if len(clave) < 10 or " " in clave:
        raise gd.ErrorMotor("Pega tu clave de ElevenLabs completa, sin espacios.")
    voces = motor_voz.el_voces(clave)               # comprueba que la clave sirve antes de guardarla
    core.guardar_clave_elevenlabs(clave)
    return jsonify({"voces": voces, "cuota": motor_voz.el_cuota(clave)})


@app.delete("/api/elevenlabs/clave")
def el_clave_borrar():
    core.guardar_clave_elevenlabs("")
    return jsonify({"ok": True})


@app.get("/api/guiones_listos")
def guiones_listos_ver():
    import guiones_listos
    idioma = core.config_programa().get("idioma", "es")
    return jsonify({"lista": guiones_listos.listar(idioma), "permitido": bool(planes.limites().get("plantillas_nicho"))})


@app.post("/api/productos/<pid>/guiones/listo")
def guion_listo(pid):
    return jsonify({"nombre": core.agregar_guion_listo(pid, (request.json or {}).get("id"), core.config_programa().get("idioma", "es"))})


@app.post("/api/productos/<pid>/guiones/nuevo")
def guion_nuevo(pid):
    return jsonify({"nombre": core.nuevo_guion(pid, (request.json or {}).get("nombre"))})


@app.post("/api/productos/<pid>/guiones/voz")
def guion_voz(pid):
    d = request.json or {}
    motor = "elevenlabs" if d.get("motor") == "elevenlabs" else "windows"
    nombre = core.generar_voz(pid, d.get("nombre", ""), d.get("voz", ""), d.get("velocidad", 0), bool(d.get("reemplazar")), motor)
    if motor == "elevenlabs":
        core.guardar_config_programa(voz_motor=motor, voz_el_id=d.get("voz", ""), voz_velocidad=d.get("velocidad", 0))
    else:
        core.guardar_config_programa(voz_motor=motor, voz_nombre=d.get("voz", ""), voz_velocidad=d.get("velocidad", 0))
    return jsonify({"nombre": nombre})


@app.get("/api/productos/<pid>/guiones")
def guiones(pid):
    return jsonify(core.listar_guiones(pid, bool(request.args.get("generar"))))


@app.post("/api/productos/<pid>/guiones/activo")
def guion_activo(pid):
    d = request.json or {}
    core.poner_guion(pid, d.get("nombre", ""), bool(d.get("activo")))
    return jsonify({"ok": True})


@app.post("/api/productos/<pid>/guiones/renombrar")
def guion_renombrar(pid):
    d = request.json or {}
    return jsonify({"nombre": core.renombrar_guion(pid, d.get("nombre", ""), d.get("nuevo", ""))})


@app.get("/api/productos/<pid>/guiones/texto")
def guion_leer(pid):
    return jsonify({"texto": core.leer_guion(pid, request.args.get("nombre", ""))})


@app.put("/api/productos/<pid>/guiones/texto")
def guion_guardar(pid):
    d = request.json or {}
    return jsonify(core.guardar_guion(pid, d.get("nombre", ""), d.get("texto", "")))


@app.get("/api/productos/<pid>/guiones/burbujas")
def burbujas_leer(pid):
    return jsonify(core.leer_burbujas(pid, request.args.get("nombre", "")))


@app.put("/api/productos/<pid>/guiones/burbujas")
def burbujas_guardar(pid):
    d = request.json or {}
    return jsonify(core.guardar_burbujas(pid, d.get("nombre", ""), d.get("burbujas", []), bool(d.get("usar_texto")), d.get("grupo")))


@app.get("/api/productos/<pid>/guiones/titulo")
def titulo_leer(pid):
    return jsonify(core.leer_titulo(pid, request.args.get("nombre", "")))


@app.put("/api/productos/<pid>/guiones/titulo")
def titulo_guardar(pid):
    d = request.json or {}
    return jsonify(core.guardar_titulo(pid, d.get("nombre", ""), d.get("titulo")))


@app.post("/api/analizar")
def guion_analizar():
    return jsonify(core.analizar_guion((request.json or {}).get("texto", "")))


# ---------------------------------------------------------------- ajustes y estilos
@app.get("/api/productos/<pid>/ajustes")
def ajustes_get(pid):
    return jsonify(core.leer_ajustes(pid))


@app.put("/api/productos/<pid>/ajustes")
def ajustes_put(pid):
    cfg, errores = core.guardar_ajustes(pid, (request.json or {}).get("valores", {}))
    return jsonify({"ajustes": cfg, "errores": errores})


@app.post("/api/productos/<pid>/formato")
def formato_cambiar(pid):
    cfg, errores = core.aplicar_formato(pid, (request.json or {}).get("formato"))
    return jsonify({"ajustes": cfg, "errores": errores})


@app.post("/api/productos/<pid>/previa")
def previa_png(pid):
    d = request.json or {}
    png, aviso, cajas = previa.generar(pid, d.get("valores", {}), core.config_programa().get("idioma", "es"),
                                d.get("burbujas"), d.get("tiempo"), d.get("grupo"), d.get("titulo"))
    r = Response(png, mimetype="image/png")
    r.headers["X-Aviso-Burbujas"] = "1" if aviso else "0"
    r.headers["X-Cajas"] = json.dumps(cajas)
    return r


@app.post("/api/productos/<pid>/previa_marca")
def previa_marca_png(pid):
    """Cómo se verá una marca (texto, imagen o figura) puesta en una frase del guion."""
    import hablado
    d = request.json or {}
    span = str(d.get("marca") or "")[:600]
    return Response(hablado.previa_marca(core.carpeta(pid), span, d.get("formato")), mimetype="image/png")


@app.post("/api/productos/<pid>/previa_formato")
def previa_formato_png(pid):
    """Vista previa de cómo saldría el video en un formato (para la pantalla «Crear videos»)."""
    d = request.json or {}
    fmt = str(d.get("formato") or "")
    if fmt not in catalogo.FORMATOS and fmt != "personalizado":
        raise gd.ErrorMotor("Formato no válido.")
    png = previa.generar_formato(pid, fmt, gd.normalizar_tamano(d.get("tamano") or {}), core.config_programa().get("idioma", "es"))
    return Response(png, mimetype="image/png")


@app.get("/api/estilos")
def estilos():
    return jsonify(core.listar_estilos())


@app.post("/api/estilos")
def estilo_guardar():
    d = request.json or {}
    if d.get("producto"):       # primero se guarda lo que tienes en pantalla, para que el estilo lleve tus posiciones actuales
        core.guardar_ajustes(d["producto"], d.get("valores", {}))
    nombre = core.guardar_estilo(d.get("nombre"), d.get("valores", {}), d.get("producto"))
    if d.get("producto"):       # el producto queda "con ese estilo" para el historial
        core.marcar_estilo(d["producto"], nombre)
    return jsonify({"nombre": nombre})


@app.post("/api/productos/<pid>/estilos/aplicar")
def estilo_aplicar(pid):
    cfg, errores = core.aplicar_estilo(pid, (request.json or {}).get("nombre"))
    return jsonify({"ajustes": cfg, "errores": errores})


@app.delete("/api/estilos/<nombre>")
def estilo_borrar(nombre):
    core.borrar_estilo(nombre)
    return jsonify({"ok": True})


# ---------------------------------------------------------------- generar
class Trabajo:
    def __init__(self):
        self.lock = threading.Lock()
        self.n = 0                     # número de trabajo (sube con cada «Crear videos»): sirve para avisar una sola vez cuando termina
        self.reset()

    def reset(self):
        self.activo = False
        self.pid = None
        self.total = 0
        self.hecho = 0
        self.escena = (0, 0)
        self.log = []
        self.creados = []
        self.por_video = 1
        self.error = None
        self.codigo = ""
        self.paso = ""
        self.paso_en = ""
        self.cancelado = False
        self.terminado = False


T = Trabajo()
_RE_ESC = re.compile(r"Escena (\d+)/(\d+)")
_RE_VID = re.compile(r"== Video finalizado")


def _mostrar(txt):
    for linea in str(txt).splitlines():
        if not linea.strip():
            continue
        T.log.append(linea)
        m = _RE_ESC.search(linea)
        if m:
            T.escena = (int(m.group(1)), int(m.group(2)))
    T.log = T.log[-300:]


def _usuario_activo():
    for u in usuarios.listar().get("usuarios", []):
        if u.get("id") == usuarios.ACTIVO:
            return u.get("nombre", "")
    return ""


def _correr(pid, cantidad, guion=None, formatos=None, sin_guion=None, usar_creditos=False, tamano=None, plantilla_voz=None):
    try:
        carpeta = core.carpeta(pid)
        quien = _usuario_activo()
        T.por_video = max(1, len(gd.formatos_destino(gd.cargar_config(carpeta), formatos)))

        def anotar(info):
            info["guion_elegido"] = bool(guion)
            core.registrar_historial(pid, info, quien)
        for archivo in gd.generar_videos(carpeta, cantidad, mostrar=_mostrar, al_crear=anotar, guion_elegido=guion, formatos=formatos, sin_guion=sin_guion, usar_creditos=usar_creditos, tamano=tamano, plantilla_voz=plantilla_voz) or []:
            T.creados.append(archivo.name)
    except gd.Cancelado:
        T.cancelado = True
        _mostrar("Detenido.")
    except gd.ErrorMotor as e:
        _i = errores.info(str(e), gd.ETAPA[0]); T.error, det = _i["error"], _i["detalle"]; T.codigo, T.paso, T.paso_en = _i["codigo"], _i["paso"], _i["paso_en"]
        if det:
            _mostrar("DETALLE TÉCNICO: " + det)
    except Exception as e:  # nunca dejar al usuario sin mensaje
        _i = errores.info(repr(e), gd.ETAPA[0]); T.error, det = _i["error"], _i["detalle"]; T.codigo, T.paso, T.paso_en = _i["codigo"], _i["paso"], _i["paso_en"]
        _mostrar("DETALLE TÉCNICO: " + (det or repr(e)))
    finally:
        T.activo = False
        T.terminado = True


# ---------------------------------------------------------------- Multimedia > Mis videos hablando (se guardan en el producto)
def _hab_pago():
    if not planes.limites().get("hablado"):
        raise gd.ErrorMotor("«Mis videos hablando» es de los planes Básico, Pro y Agencia. Mira «Mi plan» para activarlo.")


def _hab_ruta(pid, persona, archivo=None):
    import hablado
    base = hablado.carpeta_hablando(core.carpeta(pid))
    d = base / (hablado.NARRADOR_CARPETA if persona == hablado.NARRADOR_CARPETA else hablado._nombre_seguro(persona))
    if archivo is not None:
        d = d / re.sub(r"[^\w\-. ]", "_", archivo)[-100:]
    if base.resolve() not in d.resolve().parents and d.resolve() != base.resolve():
        raise gd.ErrorMotor("Ruta no válida.")
    return d


@app.get("/api/productos/<pid>/hablando")
def hablando_get(pid):
    import hablado
    d = hablado.listar_hablando(core.carpeta(pid))
    d["permitido"] = bool(planes.limites().get("hablado"))
    d["motor"] = hablado.estado_motor()
    return jsonify(d)


@app.post("/api/productos/<pid>/hablando/persona")
def hablando_persona(pid):
    _hab_pago()
    d = request.json or {}
    ruta = _hab_ruta(pid, d.get("nombre") or "Presentador")
    ruta.mkdir(parents=True, exist_ok=True)
    return jsonify({"nombre": ruta.name})


@app.post("/api/productos/<pid>/hablando/persona/renombrar")
def hablando_renombrar(pid):
    _hab_pago()
    d = request.json or {}
    a, b = _hab_ruta(pid, d.get("nombre") or ""), _hab_ruta(pid, d.get("nuevo") or "")
    if not a.is_dir():
        raise gd.ErrorMotor("No encuentro esa persona.")
    if b.exists():
        raise gd.ErrorMotor("Ya hay una persona con ese nombre.")
    a.rename(b)
    return jsonify({"nombre": b.name})


@app.delete("/api/productos/<pid>/hablando/persona")
def hablando_borrar_persona(pid):
    ruta = _hab_ruta(pid, request.args.get("nombre", ""))
    if ruta.is_dir():
        shutil.rmtree(ruta, ignore_errors=True)
    return jsonify({"ok": True})


@app.post("/api/productos/<pid>/hablando/subir")
def hablando_subir(pid):
    """Recibe un video tal cual (cuerpo crudo; ?persona= y ?nombre=) y lo guarda en la carpeta de esa persona."""
    import hablado
    _hab_pago()
    persona = request.args.get("persona", "Presentador 1")
    nombre = re.sub(r"[^\w\-. ]", "_", request.args.get("nombre", "video.mp4"))[-80:] or "video.mp4"
    ext = Path(nombre).suffix.lower()
    if persona == hablado.NARRADOR_CARPETA:
        permitido = ext in hablado.EXT_VIDEO | hablado.EXT_AUDIO_N
    else:
        permitido = ext in hablado.EXT_VIDEO
    if not permitido:
        return jsonify({"error": "Ese archivo no parece un video. Usa mp4, mov, mkv o webm."}), 400
    carpeta = _hab_ruta(pid, persona)
    carpeta.mkdir(parents=True, exist_ok=True)
    destino = carpeta / nombre
    k = 2
    while destino.exists():
        destino = carpeta / f"{Path(nombre).stem}_{k}{ext}"
        k += 1
    parte = destino.with_name(destino.name + ".parte")
    with open(parte, "wb") as f:
        shutil.copyfileobj(request.stream, f, 1 << 20)
    os.replace(parte, destino)
    return jsonify({"nombre": destino.name})


@app.post("/api/productos/<pid>/hablando/texto")
def hablando_texto(pid):
    """Escucha un video guardado y crea un guion con lo que se dice (para corregirlo y marcarlo)."""
    import hablado
    _hab_pago()
    d = request.json or {}
    persona = hablado._nombre_seguro(d.get("persona") or "Presentador 1")
    f = _hab_ruta(pid, persona, d.get("nombre") or "")
    if not f.is_file():
        raise gd.ErrorMotor("No encuentro ese video.")
    if not hablado.estado_motor().get("motor"):
        raise gd.ErrorMotor("Falta el motor de voz en esta instalación.")
    hablado.iniciar(hablado.tarea_texto, f, persona, pid, d.get("idioma") or "es")
    return jsonify({"ok": True})


@app.delete("/api/productos/<pid>/hablando/archivo")
def hablando_borrar_archivo(pid):
    f = _hab_ruta(pid, request.args.get("persona", ""), request.args.get("nombre", ""))
    if f.is_file():
        f.unlink()
    return jsonify({"ok": True})


@app.get("/api/productos/<pid>/hablando/archivo")
def hablando_ver(pid):
    f = _hab_ruta(pid, request.args.get("persona", ""), request.args.get("nombre", ""))
    if not f.is_file():
        return ("", 404)
    return send_file(str(f))


@app.put("/api/productos/<pid>/hablando/config")
def hablando_config(pid):
    import hablado
    _hab_pago()
    return jsonify(hablado.guardar_config_h(core.carpeta(pid), request.json or {}))


# ---------------------------------------------------------------- Subtitular mi video (el usuario habla en el video)
@app.before_request
def _hablado_solo_pagos():
    if request.path.startswith("/api/hablado/") and request.path.rsplit("/", 1)[-1] not in ("info", "estado", "cancelar", "carpeta"):
        if not planes.limites().get("hablado"):
            return jsonify({"error": "El «Video hablado» es de los planes Básico, Pro y Agencia. Mira «Mi plan» para activarlo."}), 403


@app.get("/api/hablado/info")
def hablado_info():
    import hablado
    return jsonify({"motor": hablado.estado_motor(request.args.get("modelo", "base")),
                    "estilos": [{"id": k, "es": v[0], "en": v[1]} for k, v in catalogo.ESTILOS_LISTOS.items()],
                    "limite": planes.revisar_videos(1) or "", "permitido": bool(planes.limites().get("hablado")),
                    "temas": [t for t in (core.leer_temas(request.args["pid"]) if request.args.get("pid") else []) if t != "kit"]})


@app.post("/api/hablado/subir")
def hablado_subir():
    """Recibe el video tal cual (cuerpo crudo, el nombre va en ?nombre=) y lo guarda en una carpeta temporal."""
    import hablado
    nombre = re.sub(r"[^\w\-. ]", "_", request.args.get("nombre", "video.mp4"))[-80:] or "video.mp4"
    if Path(nombre).suffix.lower() not in hablado.EXT_VIDEO:
        return jsonify({"error": "Ese archivo no parece un video. Usa mp4, mov, mkv o webm."}), 400
    carpeta = Path(gd.DATOS) / "_entrada_hablado"
    if request.args.get("nuevo"):                 # el primer archivo de cada trabajo vacía la carpeta; los demás se suman
        shutil.rmtree(carpeta, ignore_errors=True)
    carpeta.mkdir(parents=True, exist_ok=True)
    destino = carpeta / f"{int(time.time() * 1000) % 10**9}_{nombre}"
    with open(destino, "wb") as f:
        shutil.copyfileobj(request.stream, f, 1 << 20)
    return jsonify({"ruta": str(destino), "nombre": nombre})


def _hablado_ruta(r):
    ruta = Path(r or "").resolve()
    base = (Path(gd.DATOS) / "_entrada_hablado").resolve()
    if base not in ruta.parents or not ruta.is_file():
        raise gd.ErrorMotor("No encuentro el video. Súbelo otra vez.")
    return ruta


@app.post("/api/hablado/transcribir")
def hablado_transcribir():
    import hablado
    d = request.json or {}
    try:
        hablado.iniciar(hablado.tarea_transcribir, _hablado_ruta(d.get("ruta")), d.get("idioma") or usuarios.idioma(), d.get("modelo") or "base", d.get("guion") or "")
    except gd.ErrorMotor as e:
        return jsonify({"error": str(e)}), 400
    return jsonify({"ok": True})


@app.post("/api/hablado/crear")
def hablado_crear():
    import hablado
    d = request.json or {}
    palabras = [[str(w[0]), float(w[1]), float(w[2])] + ([str(w[3])] if len(w) > 3 and w[3] else []) for w in (d.get("palabras") or []) if len(w) >= 3 and str(w[0]).strip()]
    if not palabras:
        return jsonify({"error": "No hay texto para subtitular."}), 400
    op = {k: d.get(k) for k in ("estilo", "formato", "quitar_silencios", "umbral", "zoom", "ajustes", "nombre", "pid", "broll") if d.get(k) is not None}
    op["quien"] = _usuario_activo()
    try:
        hablado.iniciar(hablado.tarea_crear, _hablado_ruta(d.get("ruta")), palabras, op)
    except gd.ErrorMotor as e:
        return jsonify({"error": str(e)}), 400
    return jsonify({"ok": True})


@app.post("/api/hablado/analizar_conv")
def hablado_analizar_conv():
    import hablado
    d = request.json or {}
    try:
        personas = [{"nombre": str(p.get("nombre") or f"Persona {i + 1}").strip(), "rutas": [str(_hablado_ruta(r)) for r in (p.get("rutas") or [])]}
                    for i, p in enumerate(d.get("personas") or [])]
        if not (d.get("narrador") or {}).get("modo") and (not personas or not any(p["rutas"] for p in personas)):
            return jsonify({"error": "Sube al menos un video de una persona."}), 400
        narr = d.get("narrador") or None
        if narr and narr.get("modo") == "grabar":
            narr = dict(narr, rutas=[str(_hablado_ruta(r)) for r in (narr.get("rutas") or [])])
        hablado.iniciar(hablado.tarea_analizar_conv, personas, d.get("guion") or "", d.get("idioma") or usuarios.idioma(), d.get("modelo") or "base", narr)
    except gd.ErrorMotor as e:
        return jsonify({"error": str(e)}), 400
    return jsonify({"ok": True})


@app.post("/api/hablado/crear_conv")
def hablado_crear_conv():
    import hablado
    d = request.json or {}
    op = {k: d.get(k) for k in ("estilo", "formato", "zoom", "color_personas", "ajustes", "nombre", "pid", "broll") if d.get(k) is not None}
    op["quien"] = _usuario_activo()
    try:
        hablado.iniciar(hablado.tarea_crear_conv, op)
    except gd.ErrorMotor as e:
        return jsonify({"error": str(e)}), 400
    return jsonify({"ok": True})


@app.get("/api/hablado/estado")
def hablado_estado():
    import hablado
    return jsonify(hablado.estado())


@app.post("/api/hablado/cancelar")
def hablado_cancelar():
    import hablado
    hablado.H.cancelado = True
    return jsonify({"ok": True})


@app.post("/api/hablado/carpeta")
def hablado_carpeta():
    import hablado
    ruta = hablado.carpeta_salida()
    try:
        _abrir_carpeta(ruta)
    except Exception:
        pass
    return jsonify({"ruta": str(ruta)})


@app.post("/api/muestra")
def muestra_crear():
    """Crea el producto de muestra (si no existe) para el recorrido de bienvenida."""
    pid = core.crear_muestra(usuarios.idioma())
    return jsonify({"id": pid})


def _abrir_carpeta(ruta):
    """Abre la carpeta en el Explorador y muestra lo que tiene adentro."""
    ruta = Path(ruta)
    if os.name == "nt":
        os.startfile(str(ruta))  # noqa
    elif sys.platform == "darwin":
        subprocess.Popen(["open", str(ruta)])
    else:
        subprocess.Popen(["xdg-open", str(ruta)])


def _raiz_material_practica():
    return Path(usuarios.RAIZ) / ("Practice material" if usuarios.idioma() == "en" else "Material de práctica")


@app.post("/api/practica/material")
def practica_material():
    """Crea la carpeta «Material de práctica» en Documentos\\Vibovapp y la abre (se ven sus 4 subcarpetas)."""
    raiz = core.crear_material_practica(usuarios.idioma())
    try:
        _abrir_carpeta(raiz)
    except Exception:
        pass
    return jsonify({"ruta": str(raiz)})


@app.post("/api/practica/abrir")
def practica_abrir():
    """Vuelve a abrir el material de práctica (o una de sus 4 subcarpetas: sub = 1 a 4). Si no existe, lo crea."""
    raiz = _raiz_material_practica()
    if not raiz.is_dir():
        raiz = core.crear_material_practica(usuarios.idioma())
    destino = raiz
    try:
        n = int((request.json or {}).get("sub") or 0)
        subs = sorted(p for p in raiz.iterdir() if p.is_dir())
        if 1 <= n <= len(subs):
            destino = subs[n - 1]
    except Exception:
        pass
    try:
        _abrir_carpeta(destino)
    except Exception:
        pass
    return jsonify({"ruta": str(destino)})


@app.post("/api/practica/elegir")
def practica_elegir():
    """Abre el selector de archivos de Windows justo en la carpeta del material de práctica donde están los archivos del paso.
    sub = 1 a 4 (carpeta del material); idx = cuántas carpetas de clips ya se llenaron (para abrir la siguiente). Si no se puede, fallback=True."""
    if not VENTANA_PROPIA or ELEGIR_ARCHIVOS is None:
        return jsonify({"fallback": True})
    raiz = _raiz_material_practica()
    if not raiz.is_dir():
        raiz = core.crear_material_practica(usuarios.idioma())
    d = request.json or {}
    destino = raiz
    try:
        n = int(d.get("sub") or 0)
        subs = sorted(p for p in raiz.iterdir() if p.is_dir())
        if 1 <= n <= len(subs):
            destino = subs[n - 1]
            hijas = sorted(p for p in destino.iterdir() if p.is_dir())
            if hijas:                                           # «2 Clips» tiene una carpeta por tema: se abre la que toca
                destino = hijas[max(0, min(int(d.get("idx") or 0), len(hijas) - 1))]
    except Exception:
        pass
    try:
        rutas = ELEGIR_ARCHIVOS(str(destino)) or []
    except Exception:
        return jsonify({"fallback": True})
    return jsonify({"rutas": [str(r) for r in rutas], "fallback": False})


@app.get("/api/practica/leer")
def practica_leer():
    """Entrega un archivo del material de práctica (solo de esa carpeta) para subirlo a la app."""
    raiz = _raiz_material_practica().resolve()
    try:
        p = Path(request.args.get("ruta", "")).resolve()
    except Exception:
        return ("", 404)
    if raiz not in p.parents or not p.is_file() or p.stat().st_size > 200 * 1024 * 1024:
        return ("", 404)
    return send_file(str(p))


@app.post("/api/productos/<pid>/practica/terminar")
def practica_terminar(pid):
    c = core.carpeta(pid)
    if gd.es_producto_practica(c):
        gd.terminar_practica(c)
    return jsonify({"ok": True})


@app.post("/api/generar")
def generar():
    d = request.json or {}
    with T.lock:
        if T.activo:
            raise gd.ErrorMotor("Ya hay videos generándose. Espera a que termine o detenlo.")
        pid = d.get("producto")
        _c = core.carpeta(pid)
        if gd.es_producto_practica(_c) and gd.practica_terminada(_c):
            raise gd.ErrorMotor("Esta práctica ya terminó: el proyecto de práctica ya no crea más videos. Para repetirla, borra este proyecto y empieza la práctica otra vez, o crea tu propio proyecto.")
        cantidad = max(1, min(int(d.get("cantidad") or 1), 1000))
        T.reset()
        T.n += 1
        T.activo, T.pid, T.total = True, pid, cantidad
        gd.CANCELAR.clear()
        guion = (d.get("guion") or "").strip() or None
        sg = d.get("sin_guion") if isinstance(d.get("sin_guion"), dict) else None
        formatos = d.get("formatos") if isinstance(d.get("formatos"), list) else None
        if formatos is not None and not [f for f in formatos if f in catalogo.FORMATOS or f == "personalizado"]:
            T.reset()
            raise gd.ErrorMotor("Selecciona el formato que deseas.")
        _lim = planes.PLANES["pro"] if d.get("usar_creditos") else planes.limites()
        if formatos is not None and len(set(formatos)) > 1 and pid != "muestra" and not gd.es_producto_practica(_c) and not _lim.get("multiformato"):
            T.reset()
            raise gd.ErrorMotor("Tu plan crea un formato a la vez. Con el plan Pro o Agencia (o con créditos) puedes hacer varios formatos en el mismo pedido.")
        _tope = int(_lim.get("tanda") or 50)
        _archivos = cantidad * max(1, len(set(formatos or [""])))
        if _archivos > _tope and pid != "muestra":
            T.reset()
            raise gd.ErrorMotor(f"Tu plan permite hasta {_tope} archivos de video por tanda (videos × formatos). Pediste {_archivos}. Baja la cantidad o los formatos, o crea otra tanda después.")
        threading.Thread(target=_correr, args=(pid, cantidad, guion, formatos, sg, bool(d.get("usar_creditos")), gd.normalizar_tamano(d.get("tamano") or {}), (str(d.get("plantilla_voz") or "") or None)), daemon=True).start()
    return jsonify({"ok": True})


@app.get("/api/generar/estado")
def generar_estado():
    # videos completos = los que ya aparecen en 'creados' (se llenan al final); contamos por log
    hechos = sum(1 for l in T.log if l.strip().startswith("Listo:")) // max(1, T.por_video)
    return jsonify({"activo": T.activo, "producto": T.pid, "total": T.total, "hechos": hechos,
                    "escena": T.escena, "log": T.log[-40:], "error": T.error,
                    "codigo": T.codigo, "paso": T.paso, "paso_en": T.paso_en, "cancelado": T.cancelado, "terminado": T.terminado, "n": T.n, "por_video": T.por_video})


@app.post("/api/generar/cancelar")
def generar_cancelar():
    gd.CANCELAR.set()
    return jsonify({"ok": True})


# ---------------------------------------------------------------- aviso de versión nueva
_ACT = {"t": 0, "datos": None}


def _tupla(v):
    try:
        return tuple(int(x) for x in re.findall(r"\d+", str(v))[:4])
    except Exception:
        return ()


def _url_ok(u):
    return isinstance(u, str) and (u.startswith("https://") or u.startswith("http://127.0.0.1"))


def _consultar_version():
    url = os.environ.get("VIBOVAPP_URL_VERSION") or marca.URL_VERSION
    base = {"hay": False, "actual": marca.VERSION}
    if not _url_ok(url):
        return base
    try:
        import json as _j
        import urllib.request
        with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Vibovapp"}), timeout=4) as r:
            d = _j.loads(r.read(200000).decode("utf-8"))
        nueva = str(d.get("version", ""))
        if _tupla(nueva) and _tupla(nueva) > _tupla(marca.VERSION):
            idioma = usuarios.idioma()
            nov = d.get("novedades_" + idioma) or d.get("novedades_es") or []
            cambios = novedades.limpiar(d.get("cambios"))
            return {"hay": True, "actual": marca.VERSION, "version": nueva, "descargar": d.get("descargar") if _url_ok(d.get("descargar")) else "",
                    "novedades": [str(x)[:200] for x in nov][:12], "cambios": cambios,
                    "auto": actualizador.manifiesto_ok(d), "sha256": str(d.get("sha256", ""))[:64], "firma": str(d.get("firma", ""))[:40]}
    except Exception:
        pass
    return base


@app.get("/api/plan")
def plan_estado():
    return jsonify(planes.estado())


@app.post("/api/plan/activar")
def plan_activar():
    try:
        tipo, valor = planes.activar_clave((request.json or {}).get("clave", ""))
    except ValueError as ex:
        raise gd.ErrorMotor(str(ex))
    est = planes.estado()
    est["activado"] = {"tipo": tipo, "valor": valor}
    return jsonify(est)


@app.post("/api/plan/verificar")
def plan_verificar():
    ok = planes.refrescar_licencia()          # pregunta a Gumroad ahora mismo
    est = planes.estado()
    est["verificado"] = bool(ok)
    return jsonify(est)


@app.delete("/api/plan")
def plan_quitar():
    planes.quitar_licencia()
    return jsonify(planes.estado())


@app.get("/api/actualizacion")
def actualizacion():
    if time.time() - _ACT["t"] > 6 * 3600 or _ACT["datos"] is None:
        _ACT["datos"], _ACT["t"] = _consultar_version(), time.time()
    return jsonify(_ACT["datos"])


def _salir_pronto():
    gd.CANCELAR.set()
    threading.Timer(1.2, lambda: os._exit(0)).start()


def _lanzar_instalador(ruta):
    actualizador.lanzar(ruta)


@app.post("/api/actualizacion/instalar")
def actualizacion_instalar():
    """Empieza a descargar la versión nueva (el avance se pide en /progreso)."""
    d = _ACT["datos"] or {}
    if not d.get("hay"):
        raise gd.ErrorMotor("No hay ninguna actualización pendiente.")
    try:
        actualizador.iniciar_descarga(d)
    except ValueError as ex:
        raise gd.ErrorMotor(str(ex) + " Usa «Descargar» para bajarla a mano.")
    return jsonify(dict(actualizador.ESTADO))


@app.get("/api/actualizacion/progreso")
def actualizacion_progreso():
    return jsonify(dict(actualizador.ESTADO))


@app.post("/api/actualizacion/cancelar")
def actualizacion_cancelar():
    actualizador.cancelar()
    return jsonify(dict(actualizador.ESTADO))


@app.post("/api/actualizacion/lanzar")
def actualizacion_lanzar():
    """Con la descarga lista: ejecuta el instalador y cierra el programa (el instalador lo vuelve a abrir)."""
    if actualizador.ESTADO["fase"] != "listo" or not Path(actualizador.ESTADO["ruta"]).is_file():
        raise gd.ErrorMotor("La actualización todavía no está lista.")
    if T.activo and not (request.json or {}).get("forzar"):
        return jsonify({"error": "Hay videos creándose. Espera a que terminen para actualizar.", "ocupado": True}), 409
    _lanzar_instalador(actualizador.ESTADO["ruta"])
    _salir_pronto()
    return jsonify({"ok": True})


@app.get("/api/novedades")
def novedades_ver():
    """Qué cambió desde la última versión que vio esta persona (?desde=0.4.0)."""
    cambios = novedades.desde(request.args.get("desde", ""), marca.VERSION) or [dict(c, version=marca.VERSION) for c in novedades.de_la_version(marca.VERSION)]
    if not cambios:     # sin lista nueva: usa las frases sueltas de marca.py
        idioma_texto = lambda l: list(getattr(marca, "NOVEDADES_" + l, []) or [])
        es, en = idioma_texto("ES"), idioma_texto("EN")
        cambios = [{"tipo": "nuevo", "es": x, "en": en[i] if i < len(en) else x, "tema": "", "version": marca.VERSION} for i, x in enumerate(es)][:12]
    return jsonify({"version": marca.VERSION, "cambios": cambios})


@app.post("/api/actualizacion/descargar")
def actualizacion_descargar():
    import webbrowser
    u = (_ACT["datos"] or {}).get("descargar")
    if u:
        webbrowser.open(u)
    return jsonify({"ok": bool(u)})


@app.get("/api/historial")
def historial():
    return jsonify(core.listar_historial(request.args.get("producto") or None))


@app.get("/api/historial.csv")
def historial_csv():
    from flask import Response
    return Response(core.historial_csv(request.args.get("producto") or None), mimetype="text/csv",
                    headers={"Content-Disposition": "attachment; filename=historial_vibovapp.csv"})


@app.get("/api/productos/<pid>/video/texto")
def video_texto(pid):
    return jsonify(core.texto_publicar(pid, request.args.get("nombre", ""), core.config_programa().get("idioma", "es")))


@app.get("/api/productos/<pid>/peso_base")
def peso_base(pid):
    return jsonify(core.peso_base(pid))


@app.get("/api/productos/<pid>/videos")
def videos(pid):
    return jsonify(core.listar_videos(pid))


@app.post("/api/productos/<pid>/video/renombrar")
def video_renombrar(pid):
    d = request.json or {}
    return jsonify({"nombre": core.renombrar_video(pid, d.get("nombre", ""), d.get("nuevo", ""))})


@app.delete("/api/productos/<pid>/video")
def video_borrar(pid):
    core.borrar_video(pid, request.args.get("nombre", ""))
    return jsonify({"ok": True})


def _carpeta_descargas():
    """Carpeta de Descargas del usuario (en Windows se llama Downloads por dentro, aunque se vea «Descargas»)."""
    for nombre in ("Downloads", "Descargas"):
        d = Path.home() / nombre
        if d.is_dir():
            return d
    return Path.home()


def _mostrar_en_carpeta(ruta):
    """Abre el Explorador con el archivo seleccionado (o la carpeta, si no es Windows)."""
    ruta = Path(ruta)
    if os.name == "nt":
        try:
            subprocess.Popen(["explorer", "/select,", str(ruta)])
        except Exception:
            os.startfile(str(ruta.parent))  # noqa
    elif sys.platform == "darwin":
        subprocess.Popen(["open", "-R", str(ruta)])
    else:
        subprocess.Popen(["xdg-open", str(ruta.parent)])


# ---------------------------------------------------------------- soporte (asistente de ayuda): solo arma el correo; nada se envía solo
CORREO_SOPORTE = getattr(marca, "CORREO_SOPORTE", "") or "sistemasinmo32@gmail.com"


@app.get("/api/soporte/info")
def soporte_info():
    """Datos técnicos que la persona puede incluir en su mensaje (sin claves ni rutas personales)."""
    est = planes.estado()
    log = ""
    try:
        txt = (Path(os.environ.get("VIBOVAPP_DATOS", "")) / "arranque.log").read_text(encoding="utf-8", errors="replace")
        log = "\n".join(txt.strip().splitlines()[-12:])
        log = log.replace(str(Path.home()), "~")
    except Exception:
        pass
    return jsonify({"correo": CORREO_SOPORTE, "version": marca.VERSION, "plan": est["nombre"], "videos_usados": est["videos_usados"],
                    "creditos": est["creditos"], "sistema": sys.platform, "log": log[-1500:]})


@app.post("/api/soporte/abrir")
def soporte_abrir():
    """Abre el correo ya escrito: en Gmail (navegador) o en el programa de correo de la computadora."""
    d = request.json or {}
    asunto = str(d.get("asunto", ""))[:150]
    cuerpo = str(d.get("cuerpo", ""))
    if d.get("via") == "gmail":
        url = "https://mail.google.com/mail/?view=cm&fs=1&to=" + quote(CORREO_SOPORTE) + "&su=" + quote(asunto) + "&body=" + quote(cuerpo[:6000])
        webbrowser.open(url)
    else:
        url = f"mailto:{CORREO_SOPORTE}?subject=" + quote(asunto) + "&body=" + quote(cuerpo[:1500])
        if os.name == "nt":
            os.startfile(url)  # noqa
        else:
            webbrowser.open(url)
    return jsonify({"ok": True})


@app.post("/api/abrir_ruta")
def abrir_ruta():
    """Abre una carpeta o un video que el programa acaba de guardar (solo dentro de Descargas o de los datos del programa)."""
    ruta = Path((request.json or {}).get("ruta", "")).resolve()
    permitidas = [_carpeta_descargas().resolve(), Path(gd.DATOS).resolve()]
    if not any(r == ruta or r in ruta.parents for r in permitidas) or not ruta.exists():
        return jsonify({"error": "No encuentro esa ruta."}), 404
    if os.name == "nt":
        os.startfile(str(ruta))  # noqa
    elif sys.platform == "darwin":
        subprocess.Popen(["open", str(ruta)])
    else:
        subprocess.Popen(["xdg-open", str(ruta)])
    return jsonify({"ruta": str(ruta)})


@app.post("/api/productos/<pid>/video/guardar")
def video_guardar(pid):
    """Copia el video a Descargas (sin pisar uno con el mismo nombre) y lo deja a la vista."""
    import shutil
    origen = core.ruta_video(pid, (request.json or {}).get("nombre", ""))
    destino_dir = _carpeta_descargas()
    destino = destino_dir / origen.name
    n = 2
    while destino.exists():
        destino = destino_dir / f"{origen.stem} ({n}){origen.suffix}"
        n += 1
    shutil.copy2(origen, destino)
    try:
        _mostrar_en_carpeta(destino)
    except Exception:
        pass
    return jsonify({"ruta": str(destino), "carpeta": str(destino_dir), "nombre": destino.name})


@app.post("/api/productos/<pid>/video/mostrar")
def video_mostrar(pid):
    origen = core.ruta_video(pid, (request.json or {}).get("nombre", ""))
    _mostrar_en_carpeta(origen)
    return jsonify({"ruta": str(origen)})


IMG_EXT_WEB = {".png", ".jpg", ".jpeg", ".jfif", ".webp", ".bmp", ".gif"}
_SITIOS_COMPARTIR = {      # solo se abren estos sitios (nada que venga de afuera)
    "whatsapp": "https://web.whatsapp.com/",
    "instagram": "https://www.instagram.com/",
    "tiktok": "https://www.tiktok.com/upload",
    "facebook": "https://www.facebook.com/",
    "youtube": "https://studio.youtube.com/",
}


def _copiar_archivo_al_portapapeles(ruta):
    """Copia el ARCHIVO (no el texto) al portapapeles de Windows: después se pega con Ctrl+V en WhatsApp Web, correo, etc."""
    if os.name != "nt":
        return False
    try:
        seguro = str(ruta).replace("'", "''")
        r = subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", f"Set-Clipboard -LiteralPath '{seguro}'"],
                           capture_output=True, timeout=20, creationflags=gv.SIN_VENTANA)
        return r.returncode == 0
    except Exception:
        return False


@app.post("/api/productos/<pid>/video/compartir")
def video_compartir(pid):
    """Prepara un video para compartirlo: lo copia al portapapeles (Windows) y/o abre el sitio donde se sube."""
    import webbrowser
    d = request.json or {}
    origen = core.ruta_video(pid, d.get("nombre", ""))
    destino = str(d.get("destino", "copiar"))
    copiado = _copiar_archivo_al_portapapeles(origen) if destino in ("copiar", "whatsapp") else False
    if destino in _SITIOS_COMPARTIR:
        try:
            webbrowser.open(_SITIOS_COMPARTIR[destino])
        except Exception:
            pass
        if destino != "whatsapp" or not copiado:
            try:
                _mostrar_en_carpeta(origen)      # para arrastrarlo o elegirlo en la página
            except Exception:
                pass
    elif destino == "carpeta":
        _mostrar_en_carpeta(origen)
    return jsonify({"copiado": copiado, "ruta": str(origen)})


@app.get("/api/productos/<pid>/videos_ruta")
def videos_ruta(pid):
    return jsonify({"ruta": str(core.carpeta(pid) / "videos_finalizados")})


@app.get("/api/productos/<pid>/video")
def video_ver(pid):
    return send_file(core.ruta_video(pid, request.args.get("nombre", "")), conditional=True)


def iniciar(puerto=0):
    from werkzeug.serving import make_server
    usuarios.arrancar()
    planes.iniciar_vigilancia()
    srv = make_server("127.0.0.1", puerto, app, threaded=True)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, srv.server_port


if __name__ == "__main__":
    usuarios.arrancar()
    planes.iniciar_vigilancia()
    puerto = int(os.environ.get("VIBOVAPP_PUERTO", "5055"))
    app.run("127.0.0.1", puerto, threaded=True)
