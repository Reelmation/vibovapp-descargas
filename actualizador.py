"""Actualización automática: descarga el instalador nuevo, comprueba que sea el verdadero y lo ejecuta en silencio.

Seguridad: el archivo version.json lo FIRMA el dueño (crear_version_json.py, con el secreto de marca.py) junto con el enlace y la
huella SHA-256 del instalador. El programa solo instala si la firma es correcta y la huella del archivo descargado coincide.
Así, aunque alguien cambiara los archivos publicados en internet, el programa no instalaría nada falso.
"""
import hashlib
import hmac
import os
import re
import subprocess
import sys
import tempfile
import threading
import urllib.request
from pathlib import Path

import marca

PERMITIR_NO_WINDOWS = False          # solo para pruebas en Linux
ESTADO = {"fase": "nada", "pct": 0, "msg": "", "ruta": "", "version": ""}      # fase: nada | descargando | verificando | listo | error
_cancelar = threading.Event()
_candado = threading.Lock()
MAX_BYTES = 1500 * 1024 * 1024


def firma(version, sha256, url):
    return hmac.new(marca.SECRETO_LICENCIA.encode(), f"upd|{version}|{str(sha256).lower()}|{url}".encode("utf-8"), hashlib.sha256).hexdigest()[:40]


def _url_ok(u):
    return isinstance(u, str) and (u.startswith("https://") or u.startswith("http://127.0.0.1"))


def manifiesto_ok(d):
    """¿version.json trae enlace, huella y firma correctos, y esta computadora puede instalar solo?"""
    try:
        if not (sys.platform == "win32" or PERMITIR_NO_WINDOWS):
            return False
        sha, url, ver = str(d.get("sha256", "")).lower(), d.get("descargar"), str(d.get("version", ""))
        return bool(re.fullmatch(r"[0-9a-f]{64}", sha) and _url_ok(url) and ver
                    and hmac.compare_digest(str(d.get("firma", "")), firma(ver, sha, url)))
    except Exception:
        return False


def carpeta_temporal():
    c = Path(tempfile.gettempdir()) / "Vibovapp-actualizacion"
    c.mkdir(parents=True, exist_ok=True)
    return c


def iniciar_descarga(d):
    """Empieza a descargar en segundo plano. -> True si arrancó (o ya estaba en marcha). ValueError si no es seguro."""
    if not manifiesto_ok(d):
        raise ValueError("No se pudo comprobar que la actualización sea auténtica.")
    with _candado:
        if ESTADO["fase"] in ("descargando", "verificando"):
            return True
        if ESTADO["fase"] == "listo" and ESTADO["version"] == str(d["version"]) and Path(ESTADO["ruta"]).is_file():
            return True
        ESTADO.update(fase="descargando", pct=0, msg="", ruta="", version=str(d["version"]))
        _cancelar.clear()
    threading.Thread(target=_descargar, args=(dict(d),), daemon=True).start()
    return True


def _error(msg):
    ESTADO.update(fase="error", msg=msg)


def _descargar(d):
    try:
        carpeta = carpeta_temporal()
        for viejo in carpeta.glob("*"):                      # limpia descargas anteriores
            try:
                viejo.unlink()
            except OSError:
                pass
        ruta, parcial = carpeta / f"Vibovapp-Setup-{d['version']}.exe", carpeta / "descarga.part"
        req = urllib.request.Request(d["descargar"], headers={"User-Agent": "Vibovapp"})
        h = hashlib.sha256()
        with urllib.request.urlopen(req, timeout=25) as r, open(parcial, "wb") as f:
            total, leido = int(r.headers.get("Content-Length") or 0), 0
            while True:
                if _cancelar.is_set():
                    f.close()
                    parcial.unlink(missing_ok=True)
                    ESTADO.update(fase="nada", pct=0)
                    return
                bloque = r.read(512 * 1024)
                if not bloque:
                    break
                leido += len(bloque)
                if leido > MAX_BYTES:
                    raise ValueError("El archivo es demasiado grande.")
                h.update(bloque)
                f.write(bloque)
                ESTADO["pct"] = int(leido * 100 / total) if total else 0
        ESTADO.update(fase="verificando", pct=100)
        if not hmac.compare_digest(h.hexdigest(), str(d["sha256"]).lower()):
            parcial.unlink(missing_ok=True)
            return _error("El archivo descargado no coincide con el original, así que no se instaló. Inténtalo de nuevo más tarde.")
        os.replace(parcial, ruta)
        ESTADO.update(fase="listo", ruta=str(ruta))
    except Exception as e:
        _error("No se pudo descargar la actualización: " + str(e)[:150])


def cancelar():
    _cancelar.set()
    if ESTADO["fase"] != "listo":
        ESTADO.update(fase="nada", pct=0)


def lanzar(ruta):
    """Ejecuta el instalador en silencio (se cierra este programa y el instalador lo vuelve a abrir al terminar)."""
    env = {k: v for k, v in os.environ.items() if not k.startswith("_PYI") and k != "_MEIPASS2"}      # que el programa nuevo no herede el entorno del viejo
    flags = 0
    if sys.platform == "win32":
        flags = getattr(subprocess, "DETACHED_PROCESS", 0) | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
    subprocess.Popen([str(ruta), "/SILENT", "/SUPPRESSMSGBOXES", "/NORESTART", "/CLOSEAPPLICATIONS"], env=env, close_fds=True, creationflags=flags)
