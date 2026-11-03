"""Nombre y datos de la marca. Es el UNICO lugar donde aparece el nombre del programa:
si cambia, se cambia aqui."""
NOMBRE = "Vibovapp"
VERSION = "0.6.3"
# Aviso de versión nueva: el programa lee este archivo (version.json) publicado en internet. Mientras esté vacío, no consulta nada.
# Ejemplo: "https://raw.githubusercontent.com/TU_USUARIO/vibovapp-version/main/version.json"
URL_VERSION = ""
# Novedades de la versión ACTUAL (se copian a version.json al crear el instalador). Se actualizan con cada versión.
NOVEDADES_ES = [
    "Formatos vertical, retrato, cuadrado y horizontal, con varios a la vez y carpetas por formato",
    "Historial de videos creados y elección de guion",
    "Interruptor para encender o apagar guiones",
    "Pantalla de bienvenida y pantalla adaptable a celular",
    "Detección de archivos repetidos y pie de página con aviso legal",
]
NOVEDADES_EN = [
    "Vertical, portrait, square and landscape formats, several at once, with a folder per format",
    "History of created videos and script selection",
    "Switch to turn scripts on or off",
    "Welcome screen and phone-friendly layout",
    "Duplicate file detection and footer with legal notice",
]
TITULAR = ""          # nombre de la persona o empresa dueña del programa (aparece en el pie de página). Ej.: "Arturo Pérez" o "Mi Empresa S.A. de C.V."
ANIO_INICIO = 2026     # año en que empezó el programa (el pie muestra 2026 o 2026–2028, etc.)
LEMA_ES = "Crea videos verticales con tus guiones, tus clips y tu estilo."
LEMA_EN = "Create vertical videos with your scripts, your clips and your style."

# ---- Licencias ---------------------------------------------------------------
# CAMBIA este texto por uno largo y secreto tuyo ANTES de vender. Con él se firman las claves (generar_clave.py).
# Nunca lo compartas ni lo subas a un lugar público.
SECRETO_LICENCIA = "CAMBIA-ESTE-TEXTO-POR-UNO-SECRETO"
URL_COMPRA = ""        # página donde se compra o mejora el plan (se muestra en los avisos de límite)
