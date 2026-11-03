"""Recuerda cómo estaba la ventana (tamaño, posición y si estaba maximizada) y la deja igual la próxima vez.
La primera vez se abre maximizada. Solo Windows: usa las funciones de ventanas del propio sistema, así que
no depende de la versión de pywebview. Si algo falla, no pasa nada: la ventana se abre como siempre."""
import json
import os
import threading
import time
from pathlib import Path

SW_NORMAL, SW_MINIMIZADA, SW_MAXIMIZADA = 1, 2, 3


def leer(ruta):
    try:
        d = json.loads(Path(ruta).read_text(encoding="utf-8"))
        return d if isinstance(d, dict) else {}
    except Exception:
        return {}


def guardar(ruta, estado):
    try:
        Path(ruta).parent.mkdir(parents=True, exist_ok=True)
        Path(ruta).write_text(json.dumps(estado), encoding="utf-8")
    except Exception:
        pass


class _Win32:
    """Las pocas funciones de Windows que se necesitan (se pueden sustituir al probar)."""

    def __init__(self):
        import ctypes
        from ctypes import wintypes
        self.c, self.w = ctypes, wintypes

        class PLACEMENT(ctypes.Structure):
            _fields_ = [("length", wintypes.UINT), ("flags", wintypes.UINT), ("showCmd", wintypes.UINT),
                        ("ptMinPosition", wintypes.POINT), ("ptMaxPosition", wintypes.POINT),
                        ("rcNormalPosition", wintypes.RECT)]
        self.PLACEMENT = PLACEMENT
        u = ctypes.windll.user32
        self.u = u
        u.GetWindowPlacement.argtypes = [wintypes.HWND, ctypes.POINTER(PLACEMENT)]
        u.SetWindowPlacement.argtypes = [wintypes.HWND, ctypes.POINTER(PLACEMENT)]
        u.IsWindow.argtypes = [wintypes.HWND]
        u.IsWindowVisible.argtypes = [wintypes.HWND]
        u.GetWindow.argtypes = [wintypes.HWND, wintypes.UINT]
        u.GetWindow.restype = wintypes.HWND
        u.GetWindowTextLengthW.argtypes = [wintypes.HWND]
        u.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
        u.MonitorFromRect.argtypes = [ctypes.POINTER(wintypes.RECT), wintypes.DWORD]
        u.MonitorFromRect.restype = wintypes.HANDLE

    def ventana_propia(self):
        c, w, u = self.c, self.w, self.u
        encontradas = []
        proc = c.WINFUNCTYPE(w.BOOL, w.HWND, w.LPARAM)

        def revisar(hwnd, _):
            pid = w.DWORD()
            u.GetWindowThreadProcessId(hwnd, c.byref(pid))
            if pid.value == os.getpid() and u.IsWindowVisible(hwnd) and not u.GetWindow(hwnd, 4) and u.GetWindowTextLengthW(hwnd) > 0:
                encontradas.append(hwnd)
            return True
        u.EnumWindows(proc(revisar), 0)
        return encontradas[0] if encontradas else None

    def existe(self, hwnd):
        return bool(self.u.IsWindow(hwnd))

    def _colocacion(self, hwnd):
        p = self.PLACEMENT()
        p.length = self.c.sizeof(self.PLACEMENT)
        self.u.GetWindowPlacement(hwnd, self.c.byref(p))
        return p

    def leer(self, hwnd):
        """Estado actual, o None si está minimizada (no se guarda)."""
        p = self._colocacion(hwnd)
        if p.showCmd == SW_MINIMIZADA:
            return None
        r = p.rcNormalPosition
        return {"x": r.left, "y": r.top, "ancho": r.right - r.left, "alto": r.bottom - r.top, "maximizado": p.showCmd == SW_MAXIMIZADA}

    def _visible_en_pantalla(self, x, y):
        r = self.w.RECT(x + 40, y, x + 160, y + 30)       # un pedazo de la barra de título
        return bool(self.u.MonitorFromRect(self.c.byref(r), 0))

    def poner(self, hwnd, est):
        p = self._colocacion(hwnd)
        try:
            x, y, an, al = (int(est[k]) for k in ("x", "y", "ancho", "alto"))
            if an >= 600 and al >= 400 and self._visible_en_pantalla(x, y):
                p.rcNormalPosition = self.w.RECT(x, y, x + an, y + al)
        except (KeyError, TypeError, ValueError):
            pass                                              # sin tamaño guardado: se queda el de siempre
        p.showCmd = SW_MAXIMIZADA if est.get("maximizado") else SW_NORMAL
        self.u.SetWindowPlacement(hwnd, self.c.byref(p))


def seguir(titulo, ruta, anotar=lambda *_: None, api=None, cada=1.5, espera=20):
    """Pone la ventana como estaba la última vez (o maximizada la primera) y vuelve a guardar cada vez que cambia."""
    if api is None:
        if os.name != "nt":
            return None
        api = _Win32()

    def trabajo():
        hwnd, t0 = None, time.time()
        while hwnd is None and time.time() - t0 < espera:
            try:
                hwnd = api.ventana_propia()
            except Exception as ex:
                anotar(f"Ventana: no se pudo buscar la ventana ({ex!r})")
                return
            if hwnd is None:
                time.sleep(min(0.15, cada))
        if hwnd is None:
            anotar("Ventana: no se encontró la ventana para recordar su tamaño")
            return
        guardado = leer(ruta)
        try:
            api.poner(hwnd, guardado or {"maximizado": True})      # primera vez: maximizada
            anotar("Ventana: " + ("restaurada como estaba" if guardado else "abierta maximizada (primera vez)"))
        except Exception as ex:
            anotar(f"Ventana: no se pudo acomodar ({ex!r})")
        ultimo = guardado
        time.sleep(cada)
        while True:
            try:
                if not api.existe(hwnd):
                    break
                est = api.leer(hwnd)
                if est and est != ultimo:
                    guardar(ruta, est)
                    ultimo = est
            except Exception:
                pass
            time.sleep(cada)

    h = threading.Thread(target=trabajo, daemon=True)
    h.start()
    return h
