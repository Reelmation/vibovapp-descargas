"""Abre Vibovapp: arranca el servidor local y muestra la ventana del programa."""
import os
import sys
import time
import webbrowser
from pathlib import Path

_AVISO_CARPETA = ""


def _carpeta_de_datos():
    """Documentos\\Vibovapp. Si todavía existe la carpeta de la versión anterior (Documentos\\Reelmation) y la nueva no,
    se renombra para conservar productos, videos, usuarios y licencia. Si no se puede (por ejemplo, el programa viejo sigue abierto),
    se sigue usando la carpeta vieja sin perder nada; el cambio se intenta de nuevo la próxima vez."""
    global _AVISO_CARPETA
    docs = Path.home() / "Documents"
    base = docs if docs.exists() else Path.home()
    nueva, vieja = base / "Vibovapp", base / "Reelmation"
    if not nueva.exists() and vieja.is_dir():
        try:
            vieja.rename(nueva)
            _AVISO_CARPETA = "Datos movidos de Reelmation a Vibovapp"
        except Exception as e:
            _AVISO_CARPETA = f"No se pudo mover la carpeta Reelmation ({e}); se usa donde estaba"
            return vieja
    return nueva


if not os.environ.get("VIBOVAPP_DATOS"):
    os.environ["VIBOVAPP_DATOS"] = str(_carpeta_de_datos())

# programa empaquetado (.exe): sin consola y con ffmpeg incluido en la carpeta "bin"
# permite que el sonido de bienvenida suene sin tener que hacer clic antes (ventana propia de Windows)
os.environ.setdefault("WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS", "--autoplay-policy=no-user-gesture-required")
if sys.stdout is None:
    sys.stdout = open(os.devnull, "w")
if sys.stderr is None:
    sys.stderr = open(os.devnull, "w")
if getattr(sys, "frozen", False):
    _bin = Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent)) / "bin"
    os.environ["PATH"] = str(_bin) + os.pathsep + os.environ.get("PATH", "")

# En Windows, cualquier programa que se lance por debajo (ffmpeg, etc.) abriría una ventanita negra. Esto las oculta todas.
if os.name == "nt":
    import subprocess as _sp
    _init_original = _sp.Popen.__init__

    def _init_sin_ventana(self, *args, **kwargs):
        kwargs["creationflags"] = kwargs.get("creationflags", 0) | 0x08000000   # CREATE_NO_WINDOW
        _init_original(self, *args, **kwargs)
    _sp.Popen.__init__ = _init_sin_ventana

import marca
import servidor


def _anotar(texto):
    """Guarda una línea en arranque.log (carpeta de datos). Sirve para saber qué pasó si la ventana no abre bien."""
    try:
        ruta = Path(os.environ["VIBOVAPP_DATOS"]) / "arranque.log"
        ruta.parent.mkdir(parents=True, exist_ok=True)
        if ruta.exists() and ruta.stat().st_size > 60000:
            ruta.unlink()
        with open(ruta, "a", encoding="utf-8") as f:
            f.write(time.strftime("%Y-%m-%d %H:%M:%S ") + str(texto) + "\n")
    except Exception:
        pass


def _webview2_instalado():
    """True si Windows tiene el motor de ventana moderno (WebView2). En Windows 11 viene; en algunos Windows 10 no."""
    if os.name != "nt":
        return True
    try:
        import winreg
        guid = "{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}"
        base = "\\Microsoft\\EdgeUpdate\\Clients\\" + guid
        sitios = [(winreg.HKEY_LOCAL_MACHINE, "SOFTWARE\\WOW6432Node" + base),
                  (winreg.HKEY_LOCAL_MACHINE, "SOFTWARE" + base),
                  (winreg.HKEY_CURRENT_USER, "Software" + base)]
        for raiz, ruta in sitios:
            try:
                with winreg.OpenKey(raiz, ruta) as k:
                    version = winreg.QueryValueEx(k, "pv")[0]
                    if version and version != "0.0.0.0":
                        return True
            except OSError:
                continue
    except Exception:
        pass
    return False


def _ventana_edge(url):
    """Abre Vibovapp como una ventana de aplicación (Edge o Chrome) con el sonido permitido. Espera a que la cierres."""
    import subprocess
    cands = []
    for var in ("ProgramFiles(x86)", "ProgramFiles", "LocalAppData"):
        base = os.environ.get(var)
        if base:
            cands += [Path(base) / "Microsoft/Edge/Application/msedge.exe", Path(base) / "Google/Chrome/Application/chrome.exe"]
    exe = next((p for p in cands if p.exists()), None)
    if not exe:
        return False
    perfil = Path(os.environ.get("VIBOVAPP_DATOS", Path.home())) / "ventana_perfil"
    try:
        proc = subprocess.Popen([str(exe), f"--app={url}", "--autoplay-policy=no-user-gesture-required", f"--user-data-dir={perfil}",
                                 "--start-maximized", "--no-first-run", "--disable-session-crashed-bubble"])
        t0 = time.time()
        proc.wait()
        return "ok" if time.time() - t0 > 3 else "rapido"   # si se cerró casi al instante, Edge pasó la orden a otra ventana: no se apaga nada
    except Exception:
        return False


def main():
    srv, puerto = servidor.iniciar(0)
    url = f"http://127.0.0.1:{puerto}/"
    try:
        v = sys.getwindowsversion() if os.name == "nt" else None
        _anotar(f"Inicio {marca.NOMBRE} {marca.VERSION} | Windows {v.major}.{v.minor}.{v.build}" if v else f"Inicio {marca.NOMBRE} {marca.VERSION}")
        if _AVISO_CARPETA:
            _anotar(_AVISO_CARPETA)
    except Exception:
        pass
    try:
        if not _webview2_instalado():
            # sin WebView2 la ventana propia saldría en blanco: se usa directamente una ventana de Edge
            _anotar("WebView2 no encontrado: se usará la ventana de Edge/Chrome")
            raise RuntimeError("sin WebView2")
        import webview  # ventana propia (opcional)
        try:
            webview.settings["ALLOW_DOWNLOADS"] = True   # por si algún enlace de descarga se usa dentro de la ventana
        except Exception:
            pass
        ventana_w = webview.create_window(marca.NOMBRE, url, width=1280, height=860, min_size=(900, 600))
        def _elegir_archivos(directorio):
            """Selector de archivos de Windows (varios a la vez) que abre directamente en `directorio`."""
            try:
                tipo = webview.FileDialog.OPEN
            except AttributeError:
                tipo = webview.OPEN_DIALOG
            r = ventana_w.create_file_dialog(tipo, directory=directorio, allow_multiple=True)
            return list(r) if r else []

        servidor.ELEGIR_ARCHIVOS = _elegir_archivos
        servidor.VENTANA_PROPIA = True   # la X de la ventana es la única salida (el botón Cerrar de la app se oculta)

        def _al_cerrar(*_):
            """Si hay videos creándose, pregunta antes de cerrar. Devuelve False para cancelar el cierre."""
            try:
                if servidor.T.activo:
                    if os.name == "nt":
                        import ctypes
                        # 0x4 = Si/No, 0x30 = aviso, 0x40000 = siempre encima; 6 = Si
                        r = ctypes.windll.user32.MessageBoxW(
                            0, "Hay videos creándose. Si cierras ahora se detienen.\n\n¿Cerrar de todos modos?",
                            marca.NOMBRE, 0x4 | 0x30 | 0x40000)
                        if r != 6:
                            return False
                    import generar_diario
                    generar_diario.CANCELAR.set()
                    _anotar("Ventana cerrada con videos en proceso: se cancelaron")
            except Exception as ex:
                _anotar(f"Aviso de cierre: {ex!r}")
            return True
        try:
            ventana_w.events.closing += _al_cerrar
        except Exception as ex:
            _anotar(f"No se pudo vigilar el cierre de la ventana ({ex!r})")
        _anotar("Abriendo ventana propia (WebView2)")
        try:   # recuerda tamaño y posición de la ventana (la primera vez se abre maximizada)
            import ventana
            ventana.seguir(marca.NOMBRE, Path(os.environ["VIBOVAPP_DATOS"]) / "ventana.json", _anotar)
        except Exception as ex:
            _anotar(f"Ventana: no se pudo recordar su tamaño ({ex!r})")
        webview.start(gui="edgechromium") if os.name == "nt" else webview.start()
        _anotar("Ventana propia cerrada")
    except Exception as ex:   # sin ventana propia (pywebview no está o no hay WebView2): se abre una ventana de Edge/Chrome sin barra de direcciones
        _anotar(f"Ventana propia no disponible ({ex!r}); se prueba Edge/Chrome")
        r = _ventana_edge(url)
        _anotar(f"Resultado de la ventana de Edge/Chrome: {r}")
        if r == "ok":          # cerraste la ventana: se termina
            srv.shutdown()
            return
        if r != "rapido":
            webbrowser.open(url)
        print(f"{marca.NOMBRE} está abierto en tu navegador: {url}")
        print("Deja esta ventana abierta mientras lo usas. Ciérrala para salir.")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
    srv.shutdown()


if __name__ == "__main__":
    main()
