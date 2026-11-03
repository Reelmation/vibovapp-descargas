"""Planes, límites y licencia. Los límites viven SOLO aquí (tabla PLANES)."""
import base64
import calendar
import datetime
import hashlib
import hmac
import json
import os
import re
import threading
import time
from pathlib import Path

import gumroad
import gumroad_config as gcfg
import marca

# voz_elevenlabs: puede usar voces de ElevenLabs con SU PROPIA cuenta (se paga aparte a ElevenLabs).
# 0 = sin límite.  duracion en segundos; calidad = lado corto en píxeles (720, 1080, 2160)
# hablado: «Video hablado» (subtitular tu video, conversación, narrador, burbujas).  multiformato: varios formatos (vertical, cuadrado...) a la vez.  plantillas_nicho: guiones listos por tema.  uso_clientes: permiso de hacer videos para clientes.
PLANES = {
    "gratis":  {"nombre": "Gratis", "tanda": 4, "usuarios": 1, "productos": 1, "videos_mes": 5, "duracion": 45, "calidad": 720,
                "guiones": 3, "carpetas": 10, "archivos": 5, "marca_agua": True, "voz_elevenlabs": False,
                "multiformato": False, "plantillas_nicho": False, "uso_clientes": False, "hablado": False},
    "basico":  {"nombre": "Básico", "tanda": 10, "usuarios": 1, "productos": 2, "videos_mes": 30, "duracion": 180, "calidad": 1080,
                "guiones": 10, "carpetas": 10, "archivos": 20, "marca_agua": False, "voz_elevenlabs": True,
                "multiformato": False, "plantillas_nicho": False, "uso_clientes": False, "hablado": True},
    "pro":     {"nombre": "Pro", "tanda": 20, "usuarios": 3, "productos": 5, "videos_mes": 90, "duracion": 3600, "calidad": 2160,
                "guiones": 20, "carpetas": 20, "archivos": 20, "marca_agua": False, "voz_elevenlabs": True,
                "multiformato": True, "plantillas_nicho": True, "uso_clientes": False, "hablado": True},
    "agencia": {"nombre": "Agencia", "tanda": 50, "usuarios": 10, "productos": 15, "videos_mes": 300, "duracion": 3600, "calidad": 2160,
                "guiones": 40, "carpetas": 30, "archivos": 30, "marca_agua": False, "voz_elevenlabs": True,
                "multiformato": True, "plantillas_nicho": True, "uso_clientes": True, "hablado": True},
}
def _sitio_corto():
    """Solo el nombre del sitio, sin https:// ni lo que sigue a la primera «/», y de máximo 28 caracteres (para que la marca de agua se vea bien)."""
    x = re.sub(r"^https?://", "", str(getattr(marca, "SITIO", "") or "").strip(), flags=re.I).split("/")[0].strip()
    return x[:28]


TEXTO_MARCA = "Hecho con " + marca.NOMBRE + ((" · " + _sitio_corto()) if _sitio_corto() else "")


def enlace_publico():
    """Enlace completo (con https://) para poner en los textos de publicación. SITIO de marca.py; si no hay, URL_COMPRA."""
    x = str(getattr(marca, "SITIO", "") or "").strip() or str(getattr(gcfg, "URL_COMPRA", "") or "").strip() or str(getattr(marca, "URL_COMPRA", "") or "").strip()
    if x and not re.match(r"^https?://", x, re.I):
        x = "https://" + x
    return x


def _datos():
    d = Path(os.environ.get("VIBOVAPP_DATOS") or Path(__file__).resolve().parent)
    d.mkdir(parents=True, exist_ok=True)
    return d


# ---- Archivos de datos protegidos (licencia, uso del mes, créditos, claves canjeadas) ----------------------------
# Cada archivo se guarda FIRMADO y con una copia de respaldo fuera de la carpeta de datos (en Windows:
# %LOCALAPPDATA%\\Vibovapp). Si alguien edita el archivo, o lo borra para «empezar de cero», se usa la copia buena.
# No es infalible (el programa corre en la computadora de la persona), pero frena el 99 % de las trampas caseras.
# Pruebas en Linux: la copia solo se activa si existe la variable VIBOVAPP_ESPEJO.
def _firma_doc(nombre, d):
    cuerpo = json.dumps({k: v for k, v in d.items() if k != "_f"}, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hmac.new((marca.SECRETO_LICENCIA + "|" + nombre).encode(), cuerpo.encode("utf-8"), hashlib.sha256).hexdigest()[:32]


def _ruta_espejo(nombre):
    base = os.environ.get("VIBOVAPP_ESPEJO") or (os.path.join(os.environ["LOCALAPPDATA"], "Vibovapp") if os.environ.get("LOCALAPPDATA") else "")
    if not base:
        return None
    sello = hashlib.sha1(str(_datos().resolve()).lower().encode("utf-8")).hexdigest()[:10]
    return Path(base) / f"{sello}_{nombre}"


def _abrir(ruta):
    """-> dict, o None si no existe / no se entiende."""
    try:
        d = json.loads(Path(ruta).read_text(encoding="utf-8"))
        return d if isinstance(d, dict) else None
    except Exception:
        return None


def _escribir(ruta, d):
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    tmp = ruta.with_name(ruta.name + ".tmp")
    tmp.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, ruta)


def _leer_doc(nombre):
    """-> (datos, alterado). La copia buena más reciente gana; un archivo sin firma de una versión vieja se acepta UNA vez y se firma."""
    rutas = [_datos() / nombre]
    esp = _ruta_espejo(nombre)
    if esp:
        rutas.append(esp)
    buenas, hay_mala, vieja = [], False, None
    for r in rutas:
        d = _abrir(r)
        if d is None:
            continue
        if "_f" not in d:
            vieja = vieja if vieja is not None else d
        elif hmac.compare_digest(str(d["_f"]), _firma_doc(nombre, d)):
            buenas.append(d)
        else:
            hay_mala = True
    if buenas:
        mejor = max(buenas, key=lambda x: int(x.get("_s", 0)))
        for r in rutas:                       # repara la copia que falte, esté vieja o esté alterada
            d = _abrir(r)
            if d != mejor:
                try:
                    _escribir(r, mejor)
                except Exception:
                    pass
        return {k: v for k, v in mejor.items() if k not in ("_f", "_s")}, False
    if vieja is not None and not hay_mala:
        _guardar_doc(nombre, vieja)
        return vieja, False
    return {}, hay_mala


def _guardar_doc(nombre, d):
    previos = []
    for r in [_datos() / nombre, _ruta_espejo(nombre)]:
        x = _abrir(r) if r else None
        if x and "_f" in x and hmac.compare_digest(str(x["_f"]), _firma_doc(nombre, x)):
            previos.append(int(x.get("_s", 0)))
    nuevo = {k: v for k, v in d.items() if k not in ("_f", "_s")}
    nuevo["_s"] = (max(previos) if previos else 0) + 1
    nuevo["_f"] = _firma_doc(nombre, nuevo)
    _escribir(_datos() / nombre, nuevo)
    esp = _ruta_espejo(nombre)
    if esp:
        try:
            _escribir(esp, nuevo)
        except Exception:
            pass


def _leer(nombre):
    return _leer_doc(nombre)[0]


def _alterado(nombre):
    return _leer_doc(nombre)[1]


def _guardar(nombre, d):
    _guardar_doc(nombre, d)


# ---------------------------------------------------------------- claves
def _firma(texto):
    h = hmac.new(marca.SECRETO_LICENCIA.encode(), texto.encode(), hashlib.sha256).digest()
    return base64.b32encode(h).decode()[:8]


def crear_clave(plan, serie):
    """Uso del dueño (generar_clave.py). Formato: RLM-BASICO-AB12CD-XXXXXXXX"""
    if plan not in PLANES:
        raise ValueError("plan desconocido")
    cuerpo = f"RLM-{plan.upper()}-{str(serie).upper()}"
    return f"{cuerpo}-{_firma(cuerpo)}"


def validar_clave(clave):
    """-> plan o None"""
    m = re.fullmatch(r"RLM-([A-Z]+)-([A-Z0-9]{4,12})-([A-Z2-7]{8})", (clave or "").strip().upper())
    if not m or m.group(1).lower() not in PLANES:
        return None
    cuerpo = f"RLM-{m.group(1)}-{m.group(2)}"
    return m.group(1).lower() if hmac.compare_digest(_firma(cuerpo), m.group(3)) else None


def activar(clave):
    plan = validar_clave(clave)
    if not plan or plan == "gratis":
        return None
    _guardar("licencia.json", {"clave": clave.strip().upper(), "plan": plan, "desde": datetime.date.today().isoformat()})
    return plan


# ---------------------------------------------------------------- créditos (pagar por un video o una tanda)
# Un crédito = 1 archivo de video con TODO lo del plan Pro (4K, hasta 60 min, sin marca de agua).
# Clave: RLM-CR<cantidad>-<SERIE>-<firma>. Ejemplo: RLM-CR5-0007-XXXXXXXX = 5 créditos. Cada clave se canjea una sola vez por computadora.
def crear_clave_creditos(cantidad, serie):
    """Uso del dueño (generar_clave.py)."""
    cantidad = int(cantidad)
    if not 1 <= cantidad <= 999:
        raise ValueError("la cantidad debe estar entre 1 y 999")
    cuerpo = f"RLM-CR{cantidad}-{str(serie).upper()}"
    return f"{cuerpo}-{_firma(cuerpo)}"


def validar_clave_creditos(clave):
    """-> cantidad de créditos o None"""
    m = re.fullmatch(r"RLM-CR(\d{1,3})-([A-Z0-9]{4,12})-([A-Z2-7]{8})", (clave or "").strip().upper())
    if not m or not 1 <= int(m.group(1)) <= 999:
        return None
    cuerpo = f"RLM-CR{int(m.group(1))}-{m.group(2)}"
    return int(m.group(1)) if hmac.compare_digest(_firma(cuerpo), m.group(3)) else None


# ---------------------------------------------------------------- PRECIOS (USD). Solo se MUESTRAN en «Mi plan»; el cobro lo haces tú (Gumroad, etc.) y entregas la clave.
# Diseño: el plan Pro cuesta apenas un poco más que el Básico y da mucho más; los créditos sueltos son más caros por video que
# cualquier plan (así los planes se ven como la mejor compra) y dentro de los créditos el paquete grande es el de mejor valor.
# Para cambiar un precio, edita estas listas. "anio" = 10 meses (2 meses gratis).
PRECIOS_PLANES = {"basico": {"mes": 9, "anio": 90}, "pro": {"mes": 19, "anio": 190}, "agencia": {"mes": 39, "anio": 390}}
FUNDADOR = {"usd": 69, "cupos": 100}                      # Pro de por vida, pago único (los cupos los limitas tú en Gumroad)
EQUIPOS = [(5, 69), (10, 119)]                             # (licencias Pro, USD al mes)
PAQUETES_CREDITOS = [(1, 2), (10, 12)]      # (cuántos créditos, precio en USD); el último se marca como "mejor valor"


# ---------------------------------------------------------------- clave de reinicio (devuelve el contador de videos del mes a 0)
# Clave: RLM-RST-<SERIE>-<firma>. Cada clave se canjea una sola vez por computadora. La crea el dueño con generar_clave.py.
def crear_clave_reinicio(serie):
    """Uso del dueño (generar_clave.py)."""
    cuerpo = f"RLM-RST-{str(serie).upper()}"
    return f"{cuerpo}-{_firma(cuerpo)}"


def validar_clave_reinicio(clave):
    m = re.fullmatch(r"RLM-RST-([A-Z0-9]{4,12})-([A-Z2-7]{8})", (clave or "").strip().upper())
    return bool(m) and hmac.compare_digest(_firma(f"RLM-RST-{m.group(1)}"), m.group(2))


def canjear_reinicio(clave):
    """Pone en 0 los videos usados este mes. -> cuántos videos había usado. ValueError si no se puede."""
    if not validar_clave_reinicio(clave):
        raise ValueError("Esa clave de reinicio no es válida. Revisa que esté completa y sin espacios de más.")
    d = _leer("reinicios.json")
    usadas = list(d.get("canjeadas", []))
    k = clave.strip().upper()
    if k in usadas:
        raise ValueError("Esa clave de reinicio ya se usó en esta computadora.")
    antes = videos_usados()
    _guardar("uso.json", {_mes(): 0})
    usadas.append(k)
    _guardar("reinicios.json", {"canjeadas": usadas})
    return antes


def _cred():
    d, alterado = _leer_doc("creditos.json")
    return {"saldo": 0, "canjeadas": list(d.get("canjeadas", []))} if alterado else d


def creditos():
    return max(0, int(_cred().get("saldo", 0)))


def canjear_creditos(clave):
    """Suma los créditos de la clave. Lanza ValueError con un mensaje claro si no se puede."""
    n = validar_clave_creditos(clave)
    if not n:
        raise ValueError("Esa clave de créditos no es válida. Revisa que esté completa y sin espacios de más.")
    d = _cred()
    usadas = list(d.get("canjeadas", []))
    k = clave.strip().upper()
    if k in usadas:
        raise ValueError("Esa clave de créditos ya se canjeó en esta computadora.")
    usadas.append(k)
    _guardar("creditos.json", {"saldo": max(0, int(d.get("saldo", 0))) + n, "canjeadas": usadas})
    return n


def activar_clave(clave):
    """Acepta una clave de plan, de créditos o de reinicio. -> ("plan", "pro"), ("creditos", 5) o ("reinicio", videos_que_habia_usado)."""
    if validar_clave_reinicio(clave):
        return "reinicio", canjear_reinicio(clave)
    if validar_clave_creditos(clave):
        return "creditos", canjear_creditos(clave)
    plan = activar(clave)
    if plan:
        return "plan", plan
    if gumroad.activo() and not (clave or "").strip().upper().startswith("RLM-"):
        return activar_gumroad(clave)
    raise ValueError("Esa clave no es válida. Revisa que esté completa, sin espacios de más, y que sea la que te llegó al comprar.")


# ---------------------------------------------------------------- Gumroad (planes por suscripción y créditos comprados en línea)
def _msg_sin_internet():
    return "Para activar esta clave necesitamos internet un momento. Conéctate e inténtalo de nuevo."


def activar_gumroad(clave):
    """Clave que entregó Gumroad. -> ("plan", "pro") o ("creditos", 5). ValueError con un mensaje claro si no se puede."""
    clave = (clave or "").strip()
    k = clave.upper()
    try:
        r = gumroad.verificar(clave)
    except gumroad.SinConexion:
        raise ValueError(_msg_sin_internet())
    except gumroad.ClaveInvalida:
        raise ValueError("Esa clave no es válida. Revisa que esté completa, sin espacios de más, y que sea la que te llegó al comprar.")
    c, pid, clave = r["cfg"], r["producto"], r["clave"]          # clave: tal como la aceptó Gumroad
    k = clave.upper()
    estado, hasta = gumroad.estado_compra(r["compra"], c.get("periodo", "mes"))
    if estado in ("terminada", "reembolsada"):
        raise ValueError("Esa compra ya no está activa (la suscripción terminó o la compra se reembolsó). Si fue un error, escribe a soporte desde «Ayuda».")
    try:
        if c.get("tipo") == "creditos":
            n = int(c.get("n", 0))
            d = _cred()
            usadas = list(d.get("canjeadas", []))
            if k in usadas:
                raise ValueError("Esa clave de créditos ya se canjeó en esta computadora.")
            if r["uses"] >= 1:
                raise ValueError("Esa clave de créditos ya se canjeó antes (en esta u otra computadora). Cada clave se usa una sola vez.")
            if gumroad.verificar(clave, pid, incrementar=True)["uses"] > 1:
                raise ValueError("Esa clave de créditos ya se canjeó antes (en esta u otra computadora). Cada clave se usa una sola vez.")
            usadas.append(k)
            _guardar("creditos.json", {"saldo": max(0, int(d.get("saldo", 0))) + n, "canjeadas": usadas})
            return "creditos", n
        plan = c.get("plan")
        if plan not in PLANES or plan == "gratis":
            raise ValueError("Esta clave no está bien configurada. Escribe a soporte desde «Ayuda».")
        g = (_leer("licencia.json").get("gumroad") or {})
        usos = r["uses"]
        if str(g.get("clave", "")).upper() != k or g.get("maq") != maquina():          # computadora nueva para esta clave: cuenta una activación
            tope = int(c.get("activaciones") or getattr(gcfg, "ACTIVACIONES", 3))
            if usos >= tope:
                raise ValueError("Esta clave ya se activó en " + ("otra computadora" if tope == 1 else f"{tope} computadoras") + ", que es el máximo. Si cambiaste de computadora, escribe a soporte desde «Ayuda».")
            usos = gumroad.verificar(clave, pid, incrementar=True)["uses"]
    except gumroad.SinConexion:
        raise ValueError(_msg_sin_internet())
    _guardar("licencia.json", {"gumroad": {"clave": clave, "producto": pid, "plan": plan, "periodo": c.get("periodo", "mes"), "estado": estado,
                                          "hasta": hasta.isoformat() if hasta else None, "verificada": gumroad.ahora().isoformat(), "usos": usos, "maq": maquina(),
                                          "desde": _fecha_compra(r["compra"])}})
    return "plan", plan


def refrescar_licencia():
    """Pregunta a Gumroad si la suscripción sigue vigente. -> True si pudo hablar con Gumroad."""
    g = _leer("licencia.json").get("gumroad")
    if not isinstance(g, dict) or not g.get("clave"):
        return True
    try:
        r = gumroad.verificar(g["clave"], g.get("producto"))
    except gumroad.SinConexion:
        return False
    except gumroad.ClaveInvalida:
        g["estado"], g["verificada"] = "terminada", gumroad.ahora().isoformat()
    else:
        estado, hasta = gumroad.estado_compra(r["compra"], g.get("periodo", "mes"))
        g.update({"estado": estado, "hasta": hasta.isoformat() if hasta else None, "verificada": gumroad.ahora().isoformat(), "usos": r["uses"]})
        if _fecha_compra(r["compra"], None):
            g["desde"] = _fecha_compra(r["compra"])
    _guardar("licencia.json", {"gumroad": g})
    return True


_VIGILANCIA = {"hilo": None}


def iniciar_vigilancia():
    """Hilo de fondo: revisa la suscripción al abrir la app y cada 6 horas (cada 30 min si no hay internet)."""
    if _VIGILANCIA["hilo"] or not gumroad.activo():
        return

    def _ciclo():
        while True:
            try:
                ok = refrescar_licencia()
            except Exception:
                ok = False
            time.sleep(6 * 3600 if ok else 1800)
    _VIGILANCIA["hilo"] = threading.Thread(target=_ciclo, daemon=True)
    _VIGILANCIA["hilo"].start()


def gastar_credito(n=1):
    d = _cred()
    d["saldo"] = max(0, int(d.get("saldo", 0)) - n)
    _guardar("creditos.json", d)


def quitar_licencia():
    _guardar("licencia.json", {})


def _proximo_cobro(desde, periodo):
    """Próxima fecha de cobro de la suscripción (mensual o anual), contando desde el día de la compra."""
    try:
        a = datetime.date.fromisoformat(str(desde)[:10])
    except ValueError:
        return None
    if periodo == "vida":
        return None
    paso = 12 if periodo == "anio" else 1
    hoy = datetime.date.today()
    if a > hoy:
        return a.isoformat()
    return _suma_meses(a, (_meses_desde(a, hoy) // paso + 1) * paso).isoformat()


def info_licencia():
    """Estado de la licencia para la pantalla «Mi plan». -> None (sin licencia) o
    {origen: gumroad|clave, plan, vigente, estado: activa|cancelada|pago_pendiente|terminada|reembolsada|sin_verificar, hasta, verificar_antes}"""
    lic = _leer("licencia.json")
    g = lic.get("gumroad")
    if isinstance(g, dict) and g.get("plan") in PLANES:
        n = gumroad.ahora()
        estado, hasta, ver = g.get("estado", "activa"), gumroad.fecha(g.get("hasta")), gumroad.fecha(g.get("verificada"))
        gracia = datetime.timedelta(days=int(getattr(gcfg, "GRACIA_DIAS", 7)))
        limite = ver + gracia if ver else None
        if g.get("maq") and g.get("maq") != maquina():
            vigente, estado = False, "otra_computadora"
        elif estado in ("terminada", "reembolsada"):
            vigente = False
        elif hasta and n > hasta:
            vigente, estado = False, "terminada"
        elif ver is None or n > limite or n < ver - datetime.timedelta(days=1):
            vigente, estado = False, "sin_verificar"
        else:
            vigente = True
        return {"origen": "gumroad", "plan": g["plan"], "vigente": vigente, "estado": estado, "periodo": g.get("periodo", "mes"),
                "hasta": hasta.isoformat() if hasta else None, "verificar_antes": limite.isoformat() if limite else None,
                "desde": g.get("desde"), "proximo_cobro": _proximo_cobro(g.get("desde"), g.get("periodo", "mes"))}
    p = validar_clave(lic.get("clave", ""))
    if p:
        return {"origen": "clave", "plan": p, "vigente": True, "estado": "activa", "periodo": None, "hasta": None, "verificar_antes": None,
                "desde": lic.get("desde"), "proximo_cobro": None}
    return None


def plan_actual():
    i = info_licencia()
    return i["plan"] if i and i["vigente"] else "gratis"


def limites():
    return dict(PLANES[plan_actual()])


# ---------------------------------------------------------------- uso mensual
# Con un plan de pago, cada mes cuenta desde el día de la compra (compra el 15 → renueva el 15). El plan gratis cuenta por mes calendario.
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]


def _fecha_compra(compra, defecto="hoy"):
    """Fecha (ISO) en que se compró el plan, según Gumroad; si no la trae, hoy."""
    c = compra or {}
    for k in ("sale_timestamp", "created_at"):
        f = gumroad.fecha(c.get(k))
        if f:
            return f.date().isoformat()
    return datetime.date.today().isoformat() if defecto == "hoy" else None


def _suma_meses(d, k):
    y, m = divmod(d.year * 12 + d.month - 1 + k, 12)
    m += 1
    return datetime.date(y, m, min(d.day, calendar.monthrange(y, m)[1]))


def _ancla():
    """Día desde el que cuenta cada mes del plan de pago. None = plan gratis (mes calendario)."""
    if plan_actual() == "gratis":
        return None
    lic = _leer("licencia.json")
    g = lic.get("gumroad")
    dato = (g.get("desde") if isinstance(g, dict) else None) or lic.get("desde")
    try:
        return datetime.date.fromisoformat(str(dato)[:10])
    except ValueError:
        pass
    hoy = datetime.date.today()          # licencia anterior sin fecha: se toma hoy como inicio y se guarda
    if isinstance(g, dict):
        g["desde"] = hoy.isoformat()
        _guardar("licencia.json", {"gumroad": g})
    elif lic.get("clave"):
        lic["desde"] = hoy.isoformat()
        _guardar("licencia.json", lic)
    return hoy


def _meses_desde(a, hoy):
    k = (hoy.year - a.year) * 12 + hoy.month - a.month
    return k if _suma_meses(a, k) <= hoy else k - 1


def inicio_periodo():
    hoy = datetime.date.today()
    a = _ancla()
    return hoy.replace(day=1) if a is None or a > hoy else _suma_meses(a, _meses_desde(a, hoy))


def proxima_renovacion():
    """Fecha en que se renuevan los videos del plan."""
    hoy = datetime.date.today()
    a = _ancla()
    if a is None or a > hoy:
        return _suma_meses(hoy.replace(day=1), 1)
    return _suma_meses(a, _meses_desde(a, hoy) + 1)


def fecha_larga(d):
    return f"{d.day} de {MESES[d.month - 1]}"


def _mes():
    """Identificador del periodo actual (donde se cuentan los videos)."""
    return datetime.date.today().strftime("%Y-%m") if _ancla() is None else inicio_periodo().isoformat()


def _uso():
    """Contador del mes. Si el archivo fue alterado y no hay copia buena, se considera agotado el mes (una clave de reinicio lo arregla)."""
    d, alterado = _leer_doc("uso.json")
    if alterado:
        return {_mes(): limites()["videos_mes"] or 10 ** 6}
    return d


def videos_usados():
    d, k = _uso(), _mes()
    if k not in d and len(k) > 7:            # primer periodo con fechas de compra: se respeta lo que ya se usó este mes calendario
        return int(d.get(datetime.date.today().strftime("%Y-%m"), 0))
    return int(d.get(k, 0))


def sumar_video(n=1):
    d = {_mes(): videos_usados() + n}      # solo se guarda el periodo actual
    _guardar("uso.json", d)


PRACTICA_GRATIS_TOTAL = 6      # videos de práctica que no gastan el plan, en total por instalación (dos prácticas completas)


def practica_gratis_usadas():
    """Videos de práctica ya hechos gratis. Si el archivo fue alterado y no hay copia buena, se consideran agotados."""
    d, alterado = _leer_doc("practica.json")
    return PRACTICA_GRATIS_TOTAL if alterado else int(d.get("usados", 0))


def practica_gratis_restantes():
    return max(0, PRACTICA_GRATIS_TOTAL - practica_gratis_usadas())


def sumar_practica_gratis(n=1):
    _guardar("practica.json", {"usados": practica_gratis_usadas() + n})


def videos_extra():
    return int(_uso().get("extra", 0))


def videos_restantes():
    tope = limites()["videos_mes"]
    return None if not tope else max(0, tope - videos_usados())


def _paquetes():
    base = PAQUETES_CREDITOS[0][1] / PAQUETES_CREDITOS[0][0]          # precio por video del paquete más chico
    res = []
    for i, (n, usd) in enumerate(PAQUETES_CREDITOS):
        por = usd / n
        res.append({"creditos": n, "usd": usd, "por_video": round(por, 2), "ahorro": max(0, round((1 - por / base) * 100)),
                    "mejor": i == len(PAQUETES_CREDITOS) - 1 and len(PAQUETES_CREDITOS) > 1})
    return res


_ID_MAQUINA = {"v": None}


def maquina():
    """Identificador (anónimo, con hash) de esta computadora. La licencia de Gumroad queda atada a él."""
    if _ID_MAQUINA["v"] is None:
        crudo = ""
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Cryptography", 0, winreg.KEY_READ | winreg.KEY_WOW64_64KEY) as k:
                crudo = str(winreg.QueryValueEx(k, "MachineGuid")[0])
        except Exception:
            pass
        if not crudo:
            import platform
            import uuid
            crudo = f"{uuid.getnode()}-{platform.node()}"
        _ID_MAQUINA["v"] = hashlib.sha256(("vibovapp|" + crudo).encode("utf-8")).hexdigest()[:16]
    return _ID_MAQUINA["v"]


def _url(nombre):
    return getattr(gcfg, nombre, "") or getattr(marca, nombre, "")


def estado():
    l = limites()
    return {"plan": plan_actual(), "nombre": l["nombre"], "limites": l, "videos_usados": videos_usados(),
            "videos_restantes": videos_restantes(), "compra": _url("URL_COMPRA"), "planes": PLANES, "licencia": info_licencia(), "gumroad": gumroad.activo(), "url_suscripcion": getattr(gcfg, "URL_SUSCRIPCION", ""),
            "creditos": creditos(), "paquetes_creditos": _paquetes(), "precios_planes": PRECIOS_PLANES, "compra_creditos": _url("URL_CREDITOS") or _url("URL_COMPRA"), "limites_pro": PLANES["pro"], "fundador": FUNDADOR, "equipos": EQUIPOS,
            "renueva": proxima_renovacion().isoformat(), "renueva_texto": fecha_larga(proxima_renovacion()), "renueva_por_compra": _ancla() is not None}


# ---------------------------------------------------------------- mensajes de límite
def _mejorar():
    n = creditos()
    if n:
        return f" Tienes {n} crédito(s): marca «Usar créditos» al crear el video para pagarlo con ellos, o mejora tu plan en «Mi plan»."
    return " Mejora tu plan o compra créditos para hacer videos sueltos en «Mi plan»."


def _min_seg(s):
    s = int(round(s))
    return f"{s // 60} min {s % 60} s" if s >= 60 else f"{s} s"


def revisar_duracion(seg, lim=None):
    """lim=None: límites del plan. lim=PLANES['pro']: se paga con créditos."""
    credito = lim is not None
    lim = lim or limites()
    tope = lim["duracion"]
    if tope and seg > tope + 0.5:
        quien = "los créditos" if credito else "tu plan " + lim["nombre"]
        ayuda = _mejorar() if (not credito and tope < PLANES["pro"]["duracion"]) else ""
        verbo = "permiten" if credito else "permite"
        return f"Este guion dura {_min_seg(seg)} y {quien} {verbo} videos de hasta {_min_seg(tope)}. Usa un guion más corto." + ayuda


def revisar_videos(cantidad):
    resta = videos_restantes()
    if resta is not None and cantidad > resta:
        if resta == 0:
            return f"Ya usaste los {limites()['videos_mes']} videos de este mes en tu plan {limites()['nombre']}. Se renuevan el " + (fecha_larga(proxima_renovacion()) if _ancla() else "día 1 del mes siguiente") + "." + _mejorar()
        return f"Te quedan {resta} videos este mes y pediste {cantidad}. Pide {resta} o menos." + _mejorar()


def revisar_creditos(archivos):
    """Antes de generar con créditos: ¿alcanzan? (1 crédito por archivo de video)."""
    n = creditos()
    if archivos > n:
        return (f"Necesitas {archivos} crédito(s) (1 por cada archivo de video, contando cada formato) y tienes {n}. "
                "Pide menos videos o formatos, o canjea una clave de créditos en «Mi plan».")


def calidad_permitida(pedida, lim=None):
    return min(int(pedida), (lim or limites())["calidad"])


def revisar_conteo(clave, actual, texto):
    tope = limites()[clave]
    if tope and actual >= tope:
        return f"Tu plan {limites()['nombre']} permite {tope} {texto}." + " Mejora tu plan en «Mi plan»."
