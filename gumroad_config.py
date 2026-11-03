"""CONFIGURACIÓN DE GUMROAD. Es el único archivo que tienes que editar para conectar la venta con la app.

Mientras PRODUCTOS esté vacío, la app NO consulta a Gumroad y solo acepta las claves «RLM-…» que crea generar_clave.py
(sirve para la beta: tú les das la clave a mano). Cuando lo llenes, la app acepta TAMBIÉN las claves que Gumroad
entrega al comprar, y las verifica en línea (cancelaciones, reembolsos, pagos fallidos, claves compartidas).
"""

# --- 1) Los productos de Gumroad -------------------------------------------------------------------------------
# En Gumroad, cada producto debe tener activada la opción «Generar una clave de licencia única para cada venta».
# El «ID del producto» lo encuentras en Gumroad → tu producto → pestaña Contenido (o en la página de licencias de la API).
# Llena una línea por producto. Ejemplos (quita el # y pon tu ID verdadero):
PRODUCTOS = {
    # "AbCdEfGhIjKlMnOpQrStUv==": {"tipo": "plan", "plan": "basico", "periodo": "mes"},     # Básico mensual
    # "XxXxXxXxXxXxXxXxXxXxXx==": {"tipo": "plan", "plan": "basico", "periodo": "anio"},    # Básico anual
    # "YyYyYyYyYyYyYyYyYyYyYy==": {"tipo": "plan", "plan": "pro",    "periodo": "mes"},     # Pro mensual
    # "ZzZzZzZzZzZzZzZzZzZzZz==": {"tipo": "plan", "plan": "pro",    "periodo": "anio"},    # Pro anual
    # "AgAgAgAgAgAgAgAgAgAgAg==": {"tipo": "plan", "plan": "agencia", "periodo": "mes"},   # Agencia mensual
    # "AhAhAhAhAhAhAhAhAhAhAh==": {"tipo": "plan", "plan": "agencia", "periodo": "anio"},  # Agencia anual
    # "FuFuFuFuFuFuFuFuFuFuFu==": {"tipo": "plan", "plan": "pro", "periodo": "vida"},      # Fundador: Pro de por vida (pago único, limita a 100 ventas en Gumroad)
    # "Eq5Eq5Eq5Eq5Eq5Eq5Eq5==": {"tipo": "plan", "plan": "pro", "periodo": "mes", "activaciones": 5},    # Equipos: 5 licencias Pro
    # "Eq10Eq10Eq10Eq10Eq10E==": {"tipo": "plan", "plan": "pro", "periodo": "mes", "activaciones": 10},   # Equipos: 10 licencias Pro
    # "AaAaAaAaAaAaAaAaAaAaAa==": {"tipo": "creditos", "n": 1},                              # 1 crédito
    # "BbBbBbBbBbBbBbBbBbBbBb==": {"tipo": "creditos", "n": 5},                              # paquete de 5
    # "CcCcCcCcCcCcCcCcCcCcCc==": {"tipo": "creditos", "n": 10},                             # paquete de 10
}

# --- 2) Reglas ----------------------------------------------------------------------------------------------
ACTIVACIONES = 1      # en cuántas computadoras se puede activar una misma clave de plan (Gumroad no sabe cuáles; cuenta activaciones)
GRACIA_DIAS = 5       # días que el plan sigue funcionando sin poder verificarse (sin internet). Pasado ese tiempo, pasa a Gratis hasta verificar.

# --- 3) Enlaces (si los dejas vacíos se usan los de marca.py) --------------------------------------------------------
URL_COMPRA = ""        # página con tus planes en Gumroad (botón «Ver planes y comprar»)
URL_CREDITOS = ""      # página con tus paquetes de créditos (botón «Comprar créditos»)
URL_SUSCRIPCION = ""   # opcional: dónde administra o cancela su suscripción el cliente (si no la pones, la app le explica cómo)
