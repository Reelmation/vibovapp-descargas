"""Ver Vibovapp en el celular (misma red Wi-Fi). Es opcional y se activa a mano en «Configuración»:
abre un segundo acceso a la red, protegido con un PIN que cambia cada vez, y se apaga solo al cerrar la app.
Desde el celular se puede trabajar, pero no salir de la app, abrir carpetas de la computadora ni cambiar de usuario."""
import os
import re
import secrets
import socket
import subprocess
import sys
import threading
import time
import urllib.request
from pathlib import Path

from flask import jsonify, make_response, request

LOCAL = ("127.0.0.1", "::1", "::ffff:127.0.0.1")
_CF_HEADERS = ("Cf-Connecting-Ip", "Cf-Ray", "X-Forwarded-For", "Cf-Visitor")      # solo los trae lo que llega por el túnel
R = {"estado": "", "url": "", "proc": None, "error": ""}                          # acceso desde cualquier lugar (túnel)
E = {"srv": None, "puerto": None, "pin": None, "url": None, "fallos": {}, "sesiones": {}}
_LOCK = threading.Lock()
# solo desde la computadora
_SOLO_PC = ("/api/salir", "/api/abrir_ruta", "/api/practica/abrir", "/api/soporte/abrir")
_SOLO_LEER = ("/api/actualizacion",)      # desde el celular solo se pueden consultar

PAGINA_PIN = """<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Vibovapp</title><style>body{margin:0;min-height:100vh;display:flex;align-items:center;justify-content:center;background:#0c172e;color:#e8ecf7;font:18px system-ui;padding:20px;box-sizing:border-box}
.c{max-width:340px;width:100%%;text-align:center}input{width:100%%;box-sizing:border-box;font-size:28px;letter-spacing:8px;text-align:center;padding:12px;border-radius:12px;border:1px solid #4a5a86;background:#121f3d;color:#fff;margin:14px 0}
button{width:100%%;font-size:18px;padding:12px;border-radius:12px;border:0;background:#7a5cff;color:#fff}p{color:#9fb0d8;font-size:15px}.e{color:#ff8a8a;min-height:22px}</style></head>
<body><div class="c"><h2>Vibovapp</h2><p>Escribe el PIN que aparece en la computadora, en Configuración → Ver en mi celular.</p>
<input id="p" inputmode="numeric" autocomplete="one-time-code" maxlength="8" autofocus><div class="e" id="e"></div><button onclick="ir()">Entrar</button></div>
<script>async function ir(){const r=await fetch('/__pin',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({pin:document.getElementById('p').value})});
const d=await r.json().catch(()=>({}));if(r.ok){location.reload()}else{document.getElementById('e').textContent=d.error||'PIN incorrecto'}}
document.getElementById('p').addEventListener('keydown',e=>{if(e.key==='Enter')ir()})</script></body></html>"""


def ip_local():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("10.255.255.255", 1))      # no envía nada: solo averigua por qué red saldría
        return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"
    finally:
        s.close()


def es_local():
    """True solo si viene de esta misma computadora y NO por el túnel (el túnel también llega desde 127.0.0.1)."""
    return request.remote_addr in LOCAL and not any(request.headers.get(h) for h in _CF_HEADERS)


def _ip_cliente():
    return request.headers.get("Cf-Connecting-Ip") or request.remote_addr


def _qr(url):
    try:
        import segno
        return segno.make(url, error="m").svg_inline(scale=6, border=2, dark="#000000", light="#ffffff")
    except Exception:
        return ""


def estado():
    with _LOCK:
        if not E["srv"]:
            return {"activo": False}
        ahora = time.time()
        disp = [{"id": k[:8], "nombre": v["nombre"], "en_linea": ahora - v["ultimo"] < 45, "hace": int(ahora - v["ultimo"])} for k, v in E["sesiones"].items()]
        url_qr = R["url"] if R["estado"] == "listo" else E["url"]
        return {"activo": True, "url": E["url"], "pin": E["pin"], "qr": _qr(url_qr), "url_qr": url_qr,
                "remoto": {"estado": R["estado"], "url": R["url"], "error": R["error"]}, "dispositivos": sorted(disp, key=lambda d: d["hace"])}


def desconectar(id_corto):
    """Saca a un dispositivo (o a todos con id='todos'); tendrá que volver a escribir el PIN."""
    with _LOCK:
        for k in [k for k in E["sesiones"] if id_corto == "todos" or k[:8] == id_corto]:
            E["sesiones"].pop(k, None)


def _nombre_dispositivo(ua):
    ua = str(ua or "")
    for frag, n in (("iPhone", "iPhone"), ("iPad", "iPad"), ("Android", "Android"), ("Windows", "Computadora Windows"), ("Macintosh", "Mac")):
        if frag in ua:
            return n
    return "Celular"


def activar(app):
    from werkzeug.serving import make_server
    with _LOCK:
        if E["srv"]:
            return
        srv = make_server("0.0.0.0", 0, app, threaded=True)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        E.update(srv=srv, puerto=srv.server_port, pin=f"{secrets.randbelow(10 ** 8):08d}", fallos={}, sesiones={})
        E["url"] = f"http://{ip_local()}:{E['puerto']}/"


def _binario():
    nombre = "cloudflared.exe" if os.name == "nt" else "cloudflared"
    return Path(os.environ.get("VIBOVAPP_DATOS") or ".") / "_herramientas" / nombre


def _url_binario():
    base = "https://github.com/cloudflare/cloudflared/releases/latest/download/"
    if os.name == "nt":
        return base + "cloudflared-windows-amd64.exe"
    return base + "cloudflared-linux-amd64"


def _lanzar_tunel(puerto):
    exe = _binario()
    if not exe.is_file():
        exe.parent.mkdir(parents=True, exist_ok=True)
        tmp = exe.with_name(exe.name + ".parte")
        with urllib.request.urlopen(_url_binario(), timeout=60) as r, open(tmp, "wb") as f:
            while True:
                b = r.read(1 << 20)
                if not b:
                    break
                f.write(b)
        os.replace(tmp, exe)
        try:
            exe.chmod(0o755)
        except OSError:
            pass
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    p = subprocess.Popen([str(exe), "tunnel", "--url", f"http://127.0.0.1:{puerto}", "--no-autoupdate"],
                         stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, creationflags=flags, text=True)
    R["proc"] = p
    limite = time.time() + 60
    for linea in p.stdout:
        m = re.search(r"https://(?!api\.)[a-z0-9\-]+\.trycloudflare\.com", linea)
        if m:
            R["url"] = m.group(0) + "/"
            R["estado"] = "listo"
            threading.Thread(target=lambda: [None for _ in p.stdout], daemon=True).start()     # sigue leyendo para que no se llene
            return
        if time.time() > limite or p.poll() is not None:
            break
    raise RuntimeError("No se pudo abrir el acceso desde cualquier lugar.")


def activar_remoto():
    if R["estado"] in ("preparando", "listo") or not E["srv"]:
        return
    R.update(estado="preparando", url="", error="")
    puerto = E["puerto"]

    def hacer():
        try:
            _lanzar_tunel(puerto)
        except Exception:
            _apagar_tunel()
            R.update(estado="error", error="No se pudo abrir. Revisa tu internet e intenta de nuevo.")
    threading.Thread(target=hacer, daemon=True).start()


def _apagar_tunel():
    p = R.get("proc")
    R.update(proc=None, url="")
    if p:
        try:
            p.terminate()
        except Exception:
            pass
    if R["estado"] != "error":
        R["estado"] = ""


def apagar_remoto():
    _apagar_tunel()
    R["estado"] = ""


def apagar():
    _apagar_tunel()
    with _LOCK:
        srv = E["srv"]
        E.update(srv=None, puerto=None, pin=None, url=None, fallos={}, sesiones={})
    if srv:
        try:
            srv.shutdown()
            srv.server_close()
        except Exception:
            pass


def guardia():
    """Se ejecuta antes de cada petición: lo que viene de la red necesita el PIN (y no puede hacer lo exclusivo de la computadora)."""
    if es_local():
        return None
    if not E["srv"]:
        return ("Acceso por celular desactivado.", 403)
    ip = _ip_cliente()
    if request.path == "/__pin" and request.method == "POST":
        f = E["fallos"].get(ip, [0, 0.0])
        g = E["fallos"].get("*", [0, 0.0])
        if g[0] >= 20 and time.time() >= g[1]:
            g = [0, 0.0]
        if g[0] >= 20 and time.time() < g[1]:
            return jsonify({"error": "Demasiados intentos. Espera unos minutos."}), 429
        if f[0] >= 5 and time.time() < f[1]:
            return jsonify({"error": "Demasiados intentos. Espera un par de minutos."}), 429
        pin = str((request.get_json(silent=True) or {}).get("pin") or "").strip()
        if secrets.compare_digest(pin, E["pin"] or "x"):
            E["fallos"].pop(ip, None)
            tok = secrets.token_urlsafe(24)
            n_igual = sum(1 for v in E["sesiones"].values() if v["nombre"].startswith(_nombre_dispositivo(request.headers.get("User-Agent"))))
            nom = _nombre_dispositivo(request.headers.get("User-Agent")) + (f" {n_igual + 1}" if n_igual else "")
            E["sesiones"][tok] = {"nombre": nom, "ultimo": time.time()}
            r = make_response(jsonify({"ok": True}))
            r.set_cookie("vib_t", tok, httponly=True, samesite="Lax", max_age=60 * 60 * 12)
            return r
        n = f[0] + 1
        E["fallos"][ip] = [n, time.time() + 120 if n >= 5 else 0.0]
        gn = g[0] + 1
        E["fallos"]["*"] = [gn, time.time() + 600 if gn >= 20 else 0.0]
        return jsonify({"error": "PIN incorrecto"}), 403
    ses = E["sesiones"].get(request.cookies.get("vib_t", ""))
    if not ses:
        if request.path.startswith("/api/"):
            return jsonify({"error": "Falta el PIN."}), 401
        return PAGINA_PIN.replace("%%", "%"), 200, {"Content-Type": "text/html; charset=utf-8"}
    if request.path != "/api/generar/estado" or True:
        ses["ultimo"] = time.time()
    p = request.path
    if p == "/api/celular" and request.method != "GET":
        return jsonify({"error": "Esto solo se puede hacer desde la computadora."}), 403
    if (p.startswith(_SOLO_LEER) and request.method != "GET") or (p.startswith("/api/usuarios") and request.method == "DELETE") or (p.startswith("/api/productos/") and p.count("/") == 3 and request.method == "DELETE") or p.startswith(_SOLO_PC) or p.endswith("/abrir") or p.endswith("/abrir_carpeta"):
        return jsonify({"error": "Esto solo se puede hacer desde la computadora."}), 403
    return None
