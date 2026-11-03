"""Verificación en línea de las claves de licencia de Gumroad.

Gumroad NO apaga una clave cuando el cliente cancela: solo marca fechas. Aquí se leen esas fechas y se decide si la
clave sigue valiendo. Este módulo solo habla con Gumroad; las reglas de planes y créditos están en planes.py.
"""
import datetime
import json
import re
import urllib.error
import urllib.parse
import urllib.request

import gumroad_config as cfg

API = "https://api.gumroad.com/v2/licenses/verify"
TIEMPO = 6                                  # segundos de espera por consulta
DIAS_PERIODO = {"mes": 31, "anio": 366}     # si el cliente cancela y Gumroad no dice cuándo termina: se le da un periodo más
DIAS_PAGO_PENDIENTE = 7                     # si falla un cobro, se le dan unos días para arreglarlo
UTC = datetime.timezone.utc


class SinConexion(Exception):
    """No se pudo hablar con Gumroad (sin internet, error del servidor, límite de consultas)."""


class ClaveInvalida(Exception):
    """Gumroad no reconoce la clave para ninguno de los productos configurados."""


def productos():
    return dict(getattr(cfg, "PRODUCTOS", {}) or {})


def activo():
    return bool(productos())


def ahora():
    return datetime.datetime.now(UTC)


def fecha(s):
    """Texto de fecha de Gumroad -> datetime con zona. Vacío -> None. Ilegible pero presente -> «ahora» (ya ocurrió)."""
    if not s:
        return None
    try:
        t = str(s).strip().replace("Z", "+00:00")
        t = re.sub(r"(\.\d{6})\d+", r"\1", t)
        d = datetime.datetime.fromisoformat(t)
        return (d if d.tzinfo else d.replace(tzinfo=UTC)).astimezone(UTC)
    except Exception:
        return ahora()


def _pedir(clave, producto, incrementar):
    """Una consulta a Gumroad. -> dict de la respuesta si la clave existe para ese producto; None si no."""
    datos = urllib.parse.urlencode({"product_id": producto, "license_key": clave,
                                    "increment_uses_count": "true" if incrementar else "false"}).encode()
    req = urllib.request.Request(API, data=datos, method="POST", headers={"User-Agent": "Vibovapp", "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=TIEMPO) as r:
            cuerpo = r.read(300000)
    except urllib.error.HTTPError as e:
        if e.code in (400, 404):
            return None
        raise SinConexion(f"HTTP {e.code}")
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        raise SinConexion(str(e))
    try:
        d = json.loads(cuerpo.decode("utf-8"))
    except Exception:
        raise SinConexion("respuesta ilegible")
    return d if isinstance(d, dict) and d.get("success") else None


def verificar(clave, producto=None, incrementar=False):
    """Pregunta a Gumroad por la clave. Sin `producto` la busca en todos los configurados.
    -> {"producto", "clave" (como la aceptó Gumroad), "cfg", "uses", "compra"}. Lanza SinConexion o ClaveInvalida."""
    clave = (clave or "").strip()
    todos = productos()
    ids = [producto] if producto else list(todos)
    if not clave or not ids:
        raise ClaveInvalida()
    variantes = [clave] + ([clave.upper()] if clave.upper() != clave else [])      # por si la escribieron en minúsculas
    for pid in ids:
        for v in variantes:
            d = _pedir(v, pid, incrementar)
            if d:
                try:
                    usos = int(d.get("uses") or 0)
                except Exception:
                    usos = 0
                return {"producto": pid, "clave": v, "cfg": todos.get(pid, {}), "uses": usos, "compra": d.get("purchase") or {}}
    raise ClaveInvalida()


def estado_compra(compra, periodo="mes"):
    """Interpreta las fechas de la compra. -> (estado, hasta)
    estado: activa | cancelada | pago_pendiente | terminada | reembolsada.   hasta: datetime o None (hasta cuándo vale)."""
    c = compra or {}
    if c.get("refunded") or c.get("chargebacked") or c.get("disputed") and not c.get("dispute_won"):
        return "reembolsada", None
    termina, cancelo, fallo = fecha(c.get("subscription_ended_at")), fecha(c.get("subscription_cancelled_at")), fecha(c.get("subscription_failed_at"))
    n = ahora()
    if termina:
        return ("terminada", termina) if termina <= n else ("cancelada", termina)
    if fallo:
        h = fallo + datetime.timedelta(days=DIAS_PAGO_PENDIENTE)
        return ("terminada", h) if h <= n else ("pago_pendiente", h)
    if cancelo:
        h = cancelo + datetime.timedelta(days=DIAS_PERIODO.get(periodo, 31))
        return ("terminada", h) if h <= n else ("cancelada", h)
    return "activa", None
