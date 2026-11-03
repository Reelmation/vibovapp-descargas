"""Convierte errores técnicos en mensajes claros: qué pasó + qué hacer.
explicar(texto) -> (mensaje_claro, detalle_tecnico)."""
import re

# (patrón, mensaje).  {archivo} se rellena si se puede detectar el nombre.
REGLAS = [
    (r"No encuentro (ffmpeg|ffprobe)|FileNotFoundError.*ffmpeg|\[WinError 2\].*ffmpeg",
     "Falta una pieza del programa (FFmpeg). Cierra Vibovapp, ábrelo de nuevo; si sigue igual, reinstálalo."),
    (r"moov atom not found|Invalid data found|could not find codec|Error while decoding|Invalid argument.*\.(mp4|mov|mkv|webm|jpg|png)",
     "Un archivo está dañado o no se puede leer{archivo}. Quítalo de Clips y palabras clave (o vuelve a subirlo) y prueba otra vez."),
    (r"Permission denied|PermissionError|\[WinError 5\]|\[WinError 32\]|being used by another process",
     "Windows no deja usar un archivo{archivo}: probablemente está abierto en otro programa. Ciérralo y vuelve a intentar."),
    (r"No space left|Errno 28|\[WinError 112\]|disk full",
     "Tu computadora se quedó sin espacio. Libera espacio (o borra videos viejos de Mis videos) y vuelve a generar."),
    (r"MemoryError|Cannot allocate memory|out of memory",
     "A la computadora le faltó memoria. Cierra otros programas o baja la calidad del video e intenta de nuevo."),
    (r"No hay clips",
     "No hay clips para armar el video. Sube al menos uno en «Clips y palabras clave»."),
    (r"No encuentro el guion",
     "No encuentro ese guion. Puede que lo hayas borrado; elige otro en «Guiones»."),
    (r"[Ss]in guiones|No hay guiones|no hay ning\S+ guion",
     "Este proyecto aún no tiene guiones. Sube un audio con su texto en «Guiones»."),
    (r"Whisper|faster_whisper",
     "No pude sincronizar los subtítulos con el audio. Revisa que el texto del guion corresponda al audio."),
    (r"Connection|timed out|Temporary failure|getaddrinfo",
     "No se pudo conectar a internet. Revisa tu conexión; para generar videos no se necesita, solo para actualizar."),
    (r"Ya hay videos generándose",
     "Ya hay videos generándose. Espera a que terminen o detenlos."),
]
GENERICO = "Algo no salió como esperaba y no pude terminar el video. Intenta de nuevo; si se repite, usa «Ver detalles técnicos» y mándanos esa información."


def _archivo(texto):
    m = re.search(r"([\w .()\-áéíóúñÁÉÍÓÚÑ]+\.(?:mp4|mov|mkv|webm|avi|jpg|jpeg|png|webp|mp3|wav|m4a|ogg))", texto)
    return f" («{m.group(1).strip()}»)" if m else ""


def explicar(texto):
    texto = str(texto or "").strip()
    for patron, msg in REGLAS:
        if re.search(patron, texto):
            return msg.replace("{archivo}", _archivo(texto)), texto
    # mensajes que ya escribimos en español claro (sin rastros técnicos) se dejan igual
    tecnico = re.search(r"Traceback|Errno|Error\b|ffmpeg|ffprobe|Exception|\[WinError|\.py\b|Falló el comando", texto)
    if texto and not tecnico and len(texto) < 220:
        return texto, ""
    return GENERICO, texto


# ---------------------------------------------------------------- código de error y paso del proceso
# El código tiene la forma VV-<paso>-<causa>: el paso donde falló y la causa (000 = no reconocida).
PASOS = {
    1: ("Preparar el proyecto", "Preparing the project"),
    2: ("Preparar la voz y el audio", "Preparing voice and audio"),
    3: ("Sincronizar subtítulos con el audio", "Syncing subtitles with the audio"),
    4: ("Elegir clips y armar las escenas", "Choosing clips and building scenes"),
    5: ("Poner textos y efectos en pantalla", "Adding on-screen text and effects"),
    6: ("Mezclar música y sonidos", "Mixing music and sounds"),
    7: ("Unir el video final", "Rendering the final video"),
    8: ("Guardar el video", "Saving the video"),
    20: ("Subir archivos", "Uploading files"),
    21: ("Guardar tus cambios", "Saving your changes"),
    22: ("Escenas y plantillas", "Scenes and templates"),
    23: ("Guiones y audios", "Scripts and audios"),
    24: ("Videos hablando y presentadores", "Talking videos and presenters"),
    25: ("Ver en el celular", "Phone access"),
    26: ("Cuenta, plan y actualizaciones", "Account, plan and updates"),
    27: ("Mis videos y papelera", "My videos and trash"),
    28: ("Abrir la aplicación", "Starting the app"),
}
_RUTAS = [("/api/generar", 1), ("/archivos/", 20), ("/fuentes", 20), ("/escenas", 22), ("/guion", 23), ("/hablad", 24), ("/hablando", 24),
          ("/referencia", 28), ("/celular", 25), ("/plan", 26), ("/actualiz", 26), ("/usuarios", 26), ("/videos", 27), ("/papelera", 27)]


def paso_de_ruta(ruta):
    for frag, n in _RUTAS:
        if frag in str(ruta or ""):
            return n
    return 21


def info(texto, paso=21):
    """(mensaje, detalle, código, paso en español, paso en inglés) para mostrar y registrar."""
    texto = str(texto or "").strip()
    causa = 0
    for i, (patron, _m) in enumerate(REGLAS, 1):
        if re.search(patron, texto):
            causa = i
            break
    msg, det = explicar(texto)
    p = PASOS.get(paso, PASOS[21])
    return {"error": msg, "detalle": det, "codigo": f"VV-{paso:02d}-{causa:03d}", "paso": p[0], "paso_en": p[1]}
