# -*- coding: utf-8 -*-
"""
CATALOGO DE AJUSTES
===================
Aqui esta, en un solo lugar, TODO lo que se puede cambiar de un video:
nombre interno, tipo, valor por defecto, limites, categoria y textos en
espanol e ingles (nombre corto + ayuda).

De este catalogo salen:
  - los valores por defecto del motor,
  - la validacion de lo que el usuario escribe en ajustes.txt,
  - el archivo ajustes.txt comentado (en espanol o ingles),
  - y, mas adelante, las pantallas de la interfaz (cada tipo = un control:
    interruptor, deslizador, selector de color, lista de fuentes...).

Para agregar un ajuste nuevo basta una linea en AJUSTES; el resto lo toma de aqui.
"""
from PIL import ImageColor

# ----------------------------------------------------------------------------
# Categorias (orden en que se muestran)
# ----------------------------------------------------------------------------
CATEGORIAS = [
    ("formato", "Formato del video", "Video format"),
    ("titulo", "Título", "Title"),
    ("subtitulos", "Subtítulos", "Subtitles"),
    ("frase_final", "Frase final", "Closing phrase"),
    ("usuario", "Usuario o marca", "Username or brand"),
    ("burbujas", "Burbujas de WhatsApp", "WhatsApp bubbles"),
    ("clips", "Clips y escenas", "Clips and scenes"),
    ("transiciones", "Transiciones y efectos", "Transitions and effects"),
    ("animaciones", "Animaciones", "Animations"),
    ("audio", "Audio y música", "Audio and music"),
    ("tiempos", "Tiempos", "Timing"),
    ("avanzado", "Avanzado", "Advanced"),
]

TRANSICIONES_DINAMICAS = ["slideleft", "slideright", "slideup", "slidedown", "wipeleft", "wiperight",
                          "circleopen", "circleclose", "zoomin", "squeezeh", "squeezev", "radial",
                          "diagtl", "diagbr", "hlslice", "vuslice"]
TRANSICIONES_SUAVES = ["fade", "smoothleft", "smoothright", "dissolve"]
EFECTOS_CLIP = ["punch", "zoom_in", "zoom_out", "pan_izq", "pan_der"]

# nombres amigables de los efectos y transiciones (para la interfaz)
NOMBRES_TRANSICIONES = {
    "slideleft": ("Deslizar a la izquierda", "Slide left"), "slideright": ("Deslizar a la derecha", "Slide right"),
    "slideup": ("Deslizar hacia arriba", "Slide up"), "slidedown": ("Deslizar hacia abajo", "Slide down"),
    "wipeleft": ("Cortina a la izquierda", "Wipe left"), "wiperight": ("Cortina a la derecha", "Wipe right"),
    "circleopen": ("Círculo que abre", "Circle open"), "circleclose": ("Círculo que cierra", "Circle close"),
    "zoomin": ("Zoom", "Zoom in"), "squeezeh": ("Apretar horizontal", "Squeeze horizontal"),
    "squeezev": ("Apretar vertical", "Squeeze vertical"), "radial": ("Giro radial", "Radial"),
    "diagtl": ("Diagonal arriba", "Diagonal top"), "diagbr": ("Diagonal abajo", "Diagonal bottom"),
    "hlslice": ("Cortes horizontales", "Horizontal slices"), "vuslice": ("Cortes verticales", "Vertical slices"),
    "fade": ("Fundido", "Fade"), "smoothleft": ("Suave a la izquierda", "Smooth left"),
    "smoothright": ("Suave a la derecha", "Smooth right"), "dissolve": ("Disolver", "Dissolve"),
}
# formatos de video: nombre -> (ancho, alto)
FORMATOS = {"vertical": (1080, 1920), "retrato": (1080, 1350), "cuadrado": (1080, 1080), "horizontal": (1920, 1080)}

# posiciones y tamanos recomendados para cada formato (el de "vertical" son los valores de fabrica)
PRESETS_FORMATO = {
    "retrato": {"pantalla_completa": True, "titulo_y": 110, "titulo_alto": 280, "tam_texto_arriba": 96,
                "subs_y_completa": 730, "subs_tam": 80, "cta_y": 900, "cta_alto": 240, "tam_cta": 72,
                "usuario_y": 60, "usuario_tam": 44, "burbuja_y": 540, "burbuja_tam": 56, "barra_y": 1330,
                "zona_segura_arriba": 100, "zona_segura_abajo": 160},
    "cuadrado": {"pantalla_completa": True, "titulo_y": 70, "titulo_alto": 230, "tam_texto_arriba": 84,
                 "subs_y_completa": 730, "subs_tam": 76, "cta_y": 780, "cta_alto": 200, "tam_cta": 66,
                 "usuario_y": 36, "usuario_tam": 40, "burbuja_y": 470, "burbuja_tam": 50, "barra_y": 1060,
                 "zona_segura_arriba": 70, "zona_segura_abajo": 100},
    "horizontal": {"pantalla_completa": True, "titulo_y": 50, "titulo_alto": 200, "tam_texto_arriba": 84,
                   "subs_y_completa": 930, "subs_tam": 72, "cta_y": 900, "cta_alto": 160, "tam_cta": 60,
                   "usuario_y": 30, "usuario_tam": 40, "burbuja_y": 560, "burbuja_tam": 50, "barra_y": 1060,
                   "zona_segura_arriba": 60, "zona_segura_abajo": 100},
}
PRESETS_FORMATO["vertical"] = {}   # se completa mas abajo con los valores de fabrica

# forma de las burbujas: clave -> (nombre ES, nombre EN, factor ancho, factor alto, redondeo, tipo de cola)
FORMAS_BURBUJA = {
    "whatsapp": ("Clásica (WhatsApp)", "Classic (WhatsApp)", 1.0, 1.0, 38, "pico"),
    "cuadro": ("Cuadrada con pico", "Square with tip", 1.0, 1.0, 8, "pico"),
    "cuadro_liso": ("Cuadrada lisa", "Plain square", 1.0, 1.0, 6, ""),
    "pildora": ("Píldora (muy redonda)", "Pill (very round)", 1.1, 1.1, 999, ""),
    "globo": ("Globo ovalado", "Oval balloon", 1.22, 1.4, 999, "pico_abajo"),
    "pensamiento": ("Pensamiento (con bolitas)", "Thought (with dots)", 1.28, 1.42, 999, "bolitas"),
}


# estilos listos para usar: clave -> (nombre ES, nombre EN, descripción ES, descripción EN, valores). Solo cambian colores, formas y contornos.
ESTILOS_LISTOS = {
    "clasico": ("Clásico WhatsApp", "Classic WhatsApp", "Blanco, amarillo y burbujas verdes de siempre.", "White, yellow and the usual green bubbles.",
                {"color_texto": "#FFFFFF", "subs_color": "#FFFFFF", "subs_color_activo": "#FFD400", "color_cta": "#FFFFFF", "color_usuario": "#FFFFFF",
                 "color_burbuja_yo": "#DCF8C6", "color_burbuja_cliente": "#FFFFFF", "color_burbuja_texto": "#111B21",
                 "burbuja_forma": "whatsapp", "burbuja_forma_yo": "", "burbuja_forma_cliente": "", "trazo_titulo": 6, "trazo_subs": 9}),
    "elegante": ("Elegante", "Elegant", "Dorado y crema, burbujas oscuras en píldora.", "Gold and cream, dark pill bubbles.",
                 {"color_texto": "#F5E6C8", "subs_color": "#FFFFFF", "subs_color_activo": "#D4AF37", "color_cta": "#F5E6C8", "color_usuario": "#F5E6C8",
                  "color_burbuja_yo": "#2B2B2B", "color_burbuja_cliente": "#4A4A4A", "color_burbuja_texto": "#FFFFFF",
                  "burbuja_forma": "pildora", "burbuja_forma_yo": "", "burbuja_forma_cliente": "", "trazo_titulo": 4, "trazo_subs": 6}),
    "divertido": ("Divertido", "Fun", "Colores vivos y globos; el cliente piensa en nubecitas.", "Bright colors and balloons; the customer 'thinks' in clouds.",
                  {"color_texto": "#FFE14D", "subs_color": "#FFFFFF", "subs_color_activo": "#FF4D9D", "color_cta": "#FFE14D", "color_usuario": "#FFFFFF",
                   "color_burbuja_yo": "#B9F6CA", "color_burbuja_cliente": "#FFFFFF", "color_burbuja_texto": "#1A1A1A",
                   "burbuja_forma": "globo", "burbuja_forma_yo": "", "burbuja_forma_cliente": "pensamiento", "trazo_titulo": 8, "trazo_subs": 10}),
    "minimal": ("Minimal", "Minimal", "Limpio: poco contorno y cuadros lisos.", "Clean: thin outlines and plain squares.",
                {"color_texto": "#FFFFFF", "subs_color": "#FFFFFF", "subs_color_activo": "#FFFFFF", "color_cta": "#FFFFFF", "color_usuario": "#FFFFFF",
                 "color_burbuja_yo": "#FFFFFF", "color_burbuja_cliente": "#EDEDED", "color_burbuja_texto": "#111111",
                 "burbuja_forma": "cuadro_liso", "burbuja_forma_yo": "", "burbuja_forma_cliente": "", "trazo_titulo": 2, "trazo_subs": 3}),
    "cinematico": ("Cinemático", "Cinematic", "Texto blanco con la palabra clave en dorado; entra con un fundido suave.", "White text with the key word in gold; fades in softly.",
                   {"subs_color": "#FFFFFF", "subs_color_activo": "#FFFFFF", "subs_estilo": "color", "subs_animacion": "fundido", "subs_destacar": "color",
                    "subs_destacar_color": "#E8C26A", "subs_estilo_azar": False, "trazo_subs": 3}),
    "viral": ("Viral", "Viral", "Cada tarjeta cambia de estilo y entra distinto; la palabra clave va en una caja rosa.", "Every card changes style and enters differently; the key word sits in a pink box.",
              {"subs_color": "#FFFFFF", "subs_color_activo": "#FFE14D", "subs_estilo_azar": True, "subs_animacion": "azar", "subs_destacar": "caja",
               "subs_destacar_color": "#FF3B6B", "trazo_subs": 8}),
    "palabra_a_palabra": ("Palabra a palabra", "Word by word", "Una palabra a la vez, grande y con efecto pop.", "One word at a time, big, with a pop effect.",
                          {"subs_color": "#FFFFFF", "subs_color_activo": "#FFE14D", "subs_estilo": "una", "subs_animacion": "pop", "subs_destacar": "no",
                           "subs_estilo_azar": False, "trazo_subs": 9}),
    "creador": ("Creador", "Creator", "Palabra que se dice en caja de color, rebote al entrar y una palabra clave en otro color.", "Spoken word in a color box, bounce on entry and a key word in another color.",
                {"subs_color": "#FFFFFF", "subs_color_activo": "#7C5CFF", "subs_estilo": "caja", "subs_animacion": "rebote", "subs_destacar": "color",
                 "subs_destacar_color": "#FFD400", "subs_estilo_azar": False, "trazo_subs": 7}),
    "noticia": ("Noticia", "News", "Palabras clave grandes y rojas arriba, la frase en una caja abajo y una barra de avance; como los reels de noticias.", "Big red key words on top, the phrase in a box below and a progress bar; like news reels.",
               {"subs_color": "#FFFFFF", "subs_color_activo": "#FFFFFF", "subs_estilo": "doble", "subs_animacion": "fundido", "subs_destacar": "no",
                "subs_destacar_color": "#E5252A", "subs_estilo_azar": False, "trazo_subs": 6, "color_texto": "#FFFFFF", "trazo_titulo": 6, "barra_progreso": True, "color_barra": "#E5252A", "barra_y": 430, "barra_alto": 8, "burbujas": False}),
    "neon": ("Neón", "Neon", "Cian y rosa brillante sobre burbujas oscuras.", "Cyan and bright pink over dark bubbles.",
             {"color_texto": "#00F5FF", "subs_color": "#FFFFFF", "subs_color_activo": "#FF2BD6", "color_cta": "#00F5FF", "color_usuario": "#00F5FF",
              "color_burbuja_yo": "#1B1B3A", "color_burbuja_cliente": "#2A1B3D", "color_burbuja_texto": "#E0FFFF",
              "burbuja_forma": "cuadro", "burbuja_forma_yo": "", "burbuja_forma_cliente": "", "trazo_titulo": 5, "trazo_subs": 7}),
}


# efectos de entrada y salida de cada burbuja (clave -> (nombre ES, nombre EN))
ENTRADAS_BURBUJA = {
    "subir": ("Subir con fundido", "Slide up with fade"), "fundido": ("Solo fundido", "Fade only"),
    "rebote": ("Rebote", "Bounce"), "izquierda": ("Entrar desde la izquierda", "Slide in from the left"),
    "derecha": ("Entrar desde la derecha", "Slide in from the right"), "ninguna": ("Aparece de golpe", "Instant"),
}
SALIDAS_BURBUJA = {
    "ninguna": ("Desaparece de golpe", "Instant"), "fundido": ("Fundido", "Fade out"),
    "bajar": ("Baja y se desvanece", "Slide down and fade"),
}
NOMBRES_EFECTOS = {
    "punch": ("Golpe de zoom al entrar", "Zoom punch on entry"), "zoom_in": ("Acercar", "Zoom in"),
    "zoom_out": ("Alejar", "Zoom out"), "pan_izq": ("Mover hacia la izquierda", "Pan left"),
    "pan_der": ("Mover hacia la derecha", "Pan right"),
}

AJUSTES = []


def _a(clave, tipo, defecto, cat, es, en, ayuda_es, ayuda_en, minimo=None, maximo=None,
       opciones=None, nivel="basico", unidad=""):
    AJUSTES.append({
        "clave": clave, "tipo": tipo, "defecto": defecto, "categoria": cat,
        "es": es, "en": en, "ayuda_es": ayuda_es, "ayuda_en": ayuda_en,
        "min": minimo, "max": maximo, "opciones": opciones, "nivel": nivel, "unidad": unidad,
    })


# ---- Formato ---------------------------------------------------------------
_a("nombre_video", "texto", "video_finalizado_{numero}_guion_{guion}", "formato", "Nombre de los videos terminados",
   "Name of finished videos",
   "Puedes usar {numero} (001, 002…), {guion} (nombre del guion), {producto} y {fecha}. Si dos videos quedarían con el mismo nombre, se agrega un número al final.",
   "You can use {numero} (001, 002…), {guion} (script name), {producto} and {fecha}. If two videos would get the same name, a number is added at the end.")
_a("formato_video", "opcion", "vertical", "formato", "Formato del video", "Video format",
   "Vertical 9:16 (Reels, TikTok, Shorts) · Retrato 4:5 (feed de Instagram) · Cuadrado 1:1 · Horizontal 16:9 (YouTube).",
   "Vertical 9:16 (Reels, TikTok, Shorts) · Portrait 4:5 (Instagram feed) · Square 1:1 · Landscape 16:9 (YouTube).",
   opciones=[("vertical", "Vertical 9:16 (1080×1920)", "Vertical 9:16 (1080×1920)"),
             ("retrato", "Retrato 4:5 (1080×1350)", "Portrait 4:5 (1080×1350)"),
             ("cuadrado", "Cuadrado 1:1 (1080×1080)", "Square 1:1 (1080×1080)"),
             ("horizontal", "Horizontal 16:9 (1920×1080)", "Landscape 16:9 (1920×1080)"),
             ("personalizado", "Personalizado (usa ancho y alto de Avanzado)", "Custom (uses width and height from Advanced)")])
_a("calidad", "opcion", "1080", "formato", "Calidad del video", "Video quality",
   "Tamaño final del video. 720 pesa menos y se hace más rápido; 1080 es la normal; 4K se ve más nítido pero tarda y pesa mucho más. Tu plan define la calidad máxima.",
   "Final video size. 720 is lighter and faster; 1080 is the standard; 4K is sharper but slower and much heavier. Your plan sets the maximum quality.",
   opciones=[("720", "720p (HD)", "720p (HD)"), ("1080", "1080p (Full HD)", "1080p (Full HD)"), ("2160", "4K (2160p)", "4K (2160p)")])
_a("formatos_crear", "lista", "", "formato", "Formatos a crear (se elige en Crear videos)", "Formats to create (chosen in Create videos)",
   "Vacío = solo el formato de arriba. Se cambia con las casillas de la pestaña Crear videos.",
   "Empty = only the format above. Change it with the checkboxes in the Create videos tab.",
   opciones=["vertical", "retrato", "cuadrado", "horizontal", "personalizado"], nivel="avanzado")
_a("pantalla_completa", "si_no", True, "formato", "Video a pantalla completa", "Full-screen video",
   "Si: el clip llena toda la pantalla. No: el clip va en una franja con negro arriba y abajo.",
   "Yes: the clip fills the whole screen. No: the clip sits in a strip with black bars.")
_a("chroma_quitar", "opcion", "", "formato", "Quitar la pantalla verde o azul de mis videos en cámara", "Remove the green or blue screen from my on-camera videos",
   "Si grabas frente a una tela verde o azul, se quita y se pone el fondo de abajo.", "If you record in front of a green or blue cloth, it is removed and replaced by the background below.",
   opciones=[("", "No", "No"), ("verde", "Quitar fondo verde", "Remove green background"), ("azul", "Quitar fondo azul", "Remove blue background")])
_a("chroma_fondo", "color", "#101830", "formato", "Color del fondo nuevo", "New background color", "", "")
_a("chroma_archivo", "texto", "", "formato", "O una imagen o video de fondo (nombre del archivo)", "Or a background image or video (file name)",
   "Escribe el nombre de un archivo de «Imágenes del proyecto». Vacío = usa el color.", "Type the name of a file from the project images. Empty = use the color.")
_a("color_fondo", "color", "#000000", "formato", "Color de fondo", "Background color",
   "Se ve solo si el video no es de pantalla completa.", "Only visible when the video is not full-screen.")
_a("media_y", "entero", 560, "formato", "Franja: altura donde empieza", "Strip: starting height",
   "Solo con pantalla completa en No.", "Only when full-screen is No.", 0, 1500, nivel="avanzado", unidad="px")
_a("media_alto", "entero", 800, "formato", "Franja: alto", "Strip: height",
   "Solo con pantalla completa en No.", "Only when full-screen is No.", 200, 1920, nivel="avanzado", unidad="px")
_a("oscurecer_min", "entero", 20, "formato", "Oscurecer clips: mínimo", "Darken clips: minimum",
   "Qué tanto se oscurecen los clips para que el texto se lea. Cada video usa un valor al azar entre mínimo y máximo.",
   "How much clips are darkened so text stays readable. Each video picks a random value between min and max.",
   0, 90, unidad="%")
_a("oscurecer_max", "entero", 40, "formato", "Oscurecer clips: máximo", "Darken clips: maximum",
   "Ver el mínimo.", "See the minimum.", 0, 90, unidad="%")
_a("color_trazo", "color", "#000000", "formato", "Color del contorno de los textos", "Text outline color",
   "El contorno ayuda a leer el texto sobre cualquier clip.", "The outline keeps text readable over any clip.")
_a("variar_color", "si_no", True, "formato", "Variar el color de los clips", "Vary clip colors",
   "Cada clip recibe un pequeño ajuste de contraste y saturación al azar.",
   "Each clip gets a small random contrast/saturation tweak.", nivel="avanzado")

# ---- Titulo ----------------------------------------------------------------
_a("fuente_titulo", "fuente", "", "titulo", "Tipo de letra del título", "Title font",
   "Vacío = usa la letra general.", "Empty = use the general font.")
_a("tam_texto_arriba", "entero", 110, "titulo", "Tamaño del título", "Title size",
   "Es el tamaño máximo; si el título es largo, se reduce solo para no cortarse.",
   "Maximum size; long titles shrink automatically so they never get cut.", 30, 220, unidad="px")
_a("color_texto", "color", "#FFFFFF", "titulo", "Color del título", "Title color", "", "")
_a("titulo_y", "entero", 170, "titulo", "Posición del título (altura)", "Title position (height)",
   "0 = arriba de todo, 1920 = abajo de todo.", "0 = very top, 1920 = very bottom.", 0, 1800, unidad="px")
_a("titulo_x", "entero", 0, "titulo", "Mover a los lados", "Move sideways", "0 = centrado. Negativo = izquierda, positivo = derecha.", "0 = centered. Negative = left, positive = right.", -1080, 1080, nivel="avanzado", unidad="px")
_a("titulo_ancho", "entero", 0, "titulo", "Ancho de la zona del título", "Title area width", "0 = todo el ancho. Más angosto = el texto se acomoda en más renglones.", "0 = full width. Narrower = the text wraps into more lines.", 0, 2160, nivel="avanzado", unidad="px")
_a("titulo_alto", "entero", 350, "titulo", "Alto de la zona del título", "Title area height",
   "El título se centra dentro de esta zona.", "The title is centered inside this area.", 100, 900,
   nivel="avanzado", unidad="px")
_a("trazo_titulo", "entero", 6, "titulo", "Grosor del contorno", "Outline thickness", "0 = sin contorno.",
   "0 = no outline.", 0, 20, unidad="px")
_a("titulo_segundos", "decimal", 3, "titulo", "Segundos que se ve el título", "Seconds the title is visible",
   "0 = se ve todo el video.", "0 = visible for the whole video.", 0, 60, unidad="s")

# ---- Subtitulos ------------------------------------------------------------
_a("fuente_subs", "fuente", "", "subtitulos", "Tipo de letra de subtítulos", "Subtitle font",
   "Vacío = usa la letra general.", "Empty = use the general font.")
_a("subs_tam", "entero", 88, "subtitulos", "Tamaño de subtítulos", "Subtitle size", "", "", 30, 200, unidad="px")
_a("subs_color", "color", "#FFFFFF", "subtitulos", "Color de subtítulos", "Subtitle color", "", "")
_a("subs_color_activo", "color", "#FFD400", "subtitulos", "Color de la palabra que se dice", "Active word color",
   "La palabra que se está diciendo se resalta con este color.", "The word being spoken is highlighted.")
_a("subs_estilo", "opcion", "color", "subtitulos", "Estilo del subtítulo", "Subtitle style",
   "Cómo se marca la palabra que se dice: solo con color, dentro de una caja de color, más grande, o una palabra a la vez.",
   "How the spoken word is marked: color only, inside a color box, bigger, or one word at a time.",
   opciones=[("color", "Solo color", "Color only"), ("caja", "Caja de color", "Color box"),
             ("grande", "Palabra más grande", "Bigger word"), ("una", "Una palabra a la vez", "One word at a time"),
             ("doble", "Dos niveles (palabras clave arriba y frase abajo)", "Two levels (key words on top, phrase below)")])
_a("subs_animacion", "opcion", "pop", "subtitulos", "Animación de entrada del texto", "Text entrance animation",
   "Cómo aparece cada tarjeta de subtítulos. «Al azar» usa una distinta cada vez.",
   "How each subtitle card appears. 'Random' uses a different one each time.",
   opciones=[("ninguna", "Sin animación", "None"), ("pop", "Pop (crece)", "Pop (grows)"), ("subir", "Sube con fundido", "Slide up with fade"),
             ("fundido", "Solo fundido", "Fade only"), ("rebote", "Rebote", "Bounce"), ("azar", "Al azar", "Random")])
_a("subs_estilo_azar", "si_no", False, "subtitulos", "Cambiar el estilo en cada tarjeta (al azar)", "Change style on every card (random)",
   "Cada tarjeta de subtítulos usa uno de los 4 estilos, elegido al azar y sin repetir el de la anterior.",
   "Each subtitle card uses one of the 4 styles, picked at random and never the same as the previous one.")
_a("subs_destacar", "opcion", "no", "subtitulos", "Destacar una palabra clave", "Highlight a key word",
   "En cada tarjeta, la palabra más larga se destaca con otro color (y otra letra, si eliges una abajo) o dentro de una caja.",
   "In each card the longest word stands out with another color (and another font if you pick one below) or inside a box.",
   opciones=[("no", "No destacar", "Off"), ("color", "Otro color", "Another color"), ("caja", "Caja de color", "Color box")])
_a("subs_destacar_color", "color", "#FF4D6D", "subtitulos", "Color de la palabra destacada", "Highlighted word color", "", "")
_a("fuente_acento", "fuente", "", "subtitulos", "Letra de la palabra destacada", "Highlighted word font",
   "Vacío = la misma letra de los subtítulos. Una letra distinta (por ejemplo, cursiva o con serifa) da un aspecto más editorial.",
   "Empty = same font as the subtitles. A different font (italic or serif, for example) gives an editorial look.")
_a("subs_y_completa", "entero", 960, "subtitulos", "Posición (pantalla completa)", "Position (full-screen)",
   "Altura del centro de los subtítulos. Más grande = más abajo.", "Height of the subtitles' center. Larger = lower.", 0, 1800, unidad="px")
_a("subs_y", "entero", 1190, "subtitulos", "Posición (con franja)", "Position (strip mode)",
   "Solo si la pantalla completa está en No.", "Only when full-screen is No.", 0, 1800, nivel="avanzado", unidad="px")
_a("subs_x", "entero", 0, "subtitulos", "Mover a los lados", "Move sideways", "0 = centrado. Negativo = izquierda, positivo = derecha.", "0 = centered. Negative = left, positive = right.", -1080, 1080, nivel="avanzado", unidad="px")
_a("subs_ancho", "entero", 0, "subtitulos", "Ancho de los subtítulos", "Subtitle width", "0 = automático. Más angosto = letra más chica para que quepa.", "0 = automatic. Narrower = smaller letters so it fits.", 0, 2160, nivel="avanzado", unidad="px")
_a("subs_palabras", "entero", 3, "subtitulos", "Palabras por tarjeta", "Words per card",
   "Cuántas palabras salen a la vez.", "How many words show at once.", 1, 6)
_a("subs_mayusculas", "si_no", True, "subtitulos", "Todo en MAYÚSCULAS", "ALL CAPS", "", "")
_a("trazo_subs", "entero", 9, "subtitulos", "Grosor del contorno", "Outline thickness", "0 = sin contorno.",
   "0 = no outline.", 0, 20, unidad="px")

# ---- Frase final -----------------------------------------------------------
_a("cta", "texto", "Escríbenos y recibe más información", "frase_final", "Texto de la frase final",
   "Closing phrase text", "Aparece abajo en los últimos segundos. Déjalo vacío si no la quieres.",
   "Shown near the end. Leave empty to hide it.")
_a("fuente_cta", "fuente", "", "frase_final", "Tipo de letra", "Font", "Vacío = usa la letra general.",
   "Empty = use the general font.")
_a("tam_cta", "entero", 80, "frase_final", "Tamaño", "Size", "", "", 30, 200, unidad="px")
_a("color_cta", "color", "#FFFFFF", "frase_final", "Color", "Color", "", "")
_a("cta_y", "entero", 1250, "frase_final", "Posición (altura)", "Position (height)",
   "Más chico = más arriba. Evita bajar de 1400: los botones de las apps tapan esa zona.",
   "Smaller = higher. Avoid going below 1400: app buttons cover that area.", 0, 1800, unidad="px")
_a("cta_x", "entero", 0, "frase_final", "Mover a los lados", "Move sideways", "0 = centrado. Negativo = izquierda, positivo = derecha.", "0 = centered. Negative = left, positive = right.", -1080, 1080, nivel="avanzado", unidad="px")
_a("cta_ancho", "entero", 0, "frase_final", "Ancho de la zona", "Area width", "0 = todo el ancho.", "0 = full width.", 0, 2160, nivel="avanzado", unidad="px")
_a("cta_alto", "entero", 260, "frase_final", "Alto de la zona", "Area height", "", "", 100, 900,
   nivel="avanzado", unidad="px")
_a("trazo_cta", "entero", 6, "frase_final", "Grosor del contorno", "Outline thickness", "", "", 0, 20, unidad="px")
_a("cta_segundos", "decimal", 7, "frase_final", "Segundos finales en que aparece", "Seconds shown at the end",
   "0 = se ve todo el video.", "0 = visible for the whole video.", 0, 60, unidad="s")

# ---- Usuario ---------------------------------------------------------------
_a("usuario", "texto", "", "usuario", "Usuario o marca (ej. @tuusuario)", "Username or brand (e.g. @yourname)",
   "Sale chiquito en todo el video. Vacío = no aparece.", "Shown small during the whole video. Empty = hidden.")
_a("fuente_usuario", "fuente", "", "usuario", "Tipo de letra", "Font", "Vacío = usa la letra general.",
   "Empty = use the general font.")
_a("usuario_tam", "entero", 50, "usuario", "Tamaño", "Size", "", "", 20, 150, unidad="px")
_a("color_usuario", "color", "#FFFFFF", "usuario", "Color", "Color", "", "")
_a("usuario_y", "entero", 95, "usuario", "Posición (altura)", "Position (height)", "", "", 0, 1850, unidad="px")
_a("usuario_x", "entero", 0, "usuario", "Mover a los lados", "Move sideways", "0 = centrado. Negativo = izquierda, positivo = derecha.", "0 = centered. Negative = left, positive = right.", -1080, 1080, nivel="avanzado", unidad="px")
_a("trazo_usuario", "entero", 3, "usuario", "Grosor del contorno", "Outline thickness", "", "", 0, 20, unidad="px")

# ---- Burbujas --------------------------------------------------------------
_a("burbujas", "si_no", True, "burbujas", "Mostrar burbujas", "Show bubbles",
   "Las frases que marcas en tu texto salen como mensajes de WhatsApp.",
   "Phrases you mark in your script appear as chat messages.")
_a("burbuja_y", "entero", 760, "burbujas", "Posición (altura de la base)", "Position (bottom height)", "", "",
   200, 1800, unidad="px")
_a("burbuja_cliente_ajuste", "entero", 0, "burbujas", "Mover la burbuja del cliente (+ baja, − sube)",
   "Move the customer bubble (+ down, − up)",
   "Si la burbuja del cliente se encima con el título o los subtítulos, súbele o bájale aquí.",
   "If the customer bubble overlaps the title or subtitles, move it here.", -400, 400, unidad="px")
_a("burbuja_espacio", "entero", 30, "burbujas", "Espacio entre la burbuja del cliente y la tuya",
   "Gap between the customer's bubble and yours", "Solo cuando el cliente pregunta y tú contestas.",
   "Only when the customer asks and you answer.", 0, 200, unidad="px")
_a("burbuja_tam", "entero", 62, "burbujas", "Tamaño de letra", "Text size", "", "", 30, 120, unidad="px")
_a("fuente_burbuja", "fuente", "", "burbujas", "Tipo de letra", "Font", "Vacío = usa la letra general.",
   "Empty = use the general font.")
_a("color_burbuja_yo", "color", "#DCF8C6", "burbujas", "Color de tus mensajes", "Your messages color", "", "")
_a("color_burbuja_cliente", "color", "#FFFFFF", "burbujas", "Color de mensajes del cliente",
   "Customer messages color", "", "")
_a("color_burbuja_texto", "color", "#111B21", "burbujas", "Color del texto", "Text color", "", "")
_a("burbuja_x", "entero", 0, "burbujas", "Mover las burbujas a los lados (+ derecha, − izquierda)",
   "Move the bubbles sideways (+ right, − left)", "Mueve todas las burbujas de todos tus guiones.",
   "Moves all the bubbles of all your scripts.", -900, 900, unidad="px")
_a("burbuja_yo_x", "entero", 0, "burbujas", "Tu burbuja: mover a los lados (+ derecha, − izquierda)", "Your bubble: move sideways (+ right, − left)",
   "Mueve solo tus mensajes (la burbuja verde). También puedes arrastrarla en la vista previa.", "Moves only your messages (the green bubble). You can also drag it in the preview.", -900, 900, unidad="px")
_a("burbuja_yo_y", "entero", 0, "burbujas", "Tu burbuja: subir o bajar (+ baja, − sube)", "Your bubble: move up or down (+ down, − up)",
   "Mueve solo tus mensajes (la burbuja verde).", "Moves only your messages (the green bubble).", -1200, 1200, unidad="px")
_a("burbuja_yo_escala", "entero", 100, "burbujas", "Tu burbuja: tamaño", "Your bubble: size",
   "Agranda o achica tus mensajes sin deformarlos (100 = normal).", "Makes your messages bigger or smaller without distorting them (100 = normal).", 40, 220, unidad="%")
_a("burbuja_cliente_x", "entero", 0, "burbujas", "Burbuja del cliente: mover a los lados (+ derecha, − izquierda)", "Customer bubble: move sideways (+ right, − left)",
   "Mueve solo los mensajes del cliente (la burbuja blanca). También puedes arrastrarla en la vista previa.", "Moves only the customer's messages (the white bubble). You can also drag it in the preview.", -900, 900, unidad="px")
_a("burbuja_cliente_escala", "entero", 100, "burbujas", "Burbuja del cliente: tamaño", "Customer bubble: size",
   "Agranda o achica los mensajes del cliente sin deformarlos (100 = normal).", "Makes the customer's messages bigger or smaller without distorting them (100 = normal).", 40, 220, unidad="%")
_a("burbuja_forma", "opcion", "whatsapp", "burbujas", "Forma de las burbujas", "Bubble shape",
   "Cámbiala para que tus mensajes se vean como globos, cuadros o píldoras. Las formas ovaladas no llevan hora ni palomitas.",
   "Change it so your messages look like balloons, squares or pills. Oval shapes have no time or ticks.",
   opciones=[(k, v[0], v[1]) for k, v in FORMAS_BURBUJA.items()])
_a("burbuja_forma_yo", "opcion", "", "burbujas", "Forma del mensaje del emisor", "Sender message shape",
   "Vacío = usa la forma general. Así los mensajes del emisor y los del receptor pueden verse distintos.",
   "Empty = use the general shape. This lets the sender's and the receiver's messages look different.",
   opciones=[("", "Igual que la general", "Same as general")] + [(k, v[0], v[1]) for k, v in FORMAS_BURBUJA.items()])
_a("burbuja_forma_cliente", "opcion", "", "burbujas", "Forma del mensaje del receptor", "Receiver message shape",
   "Vacío = usa la forma general.", "Empty = use the general shape.",
   opciones=[("", "Igual que la general", "Same as general")] + [(k, v[0], v[1]) for k, v in FORMAS_BURBUJA.items()])
_a("marca_x", "entero", 0, "animaciones", "Texto marcado: mover a los lados", "Marked text: move sideways", "El texto que pones en pantalla desde el guion (sin una posición propia). Se mueve en la vista previa.", "On-screen text you add from the script (without its own position). Move it in the preview.", -1080, 1080, nivel="avanzado", unidad="px")
_a("marca_y", "entero", 47, "animaciones", "Texto marcado: altura (% del video)", "Marked text: height (% of the video)", "0 = arriba de todo, 100 = abajo de todo.", "0 = very top, 100 = very bottom.", 5, 95, nivel="avanzado", unidad="%")
_a("marca_tam", "entero", 0, "animaciones", "Texto marcado: tamaño de letra", "Marked text: letter size", "0 = igual que el título.", "0 = same as the title.", 0, 220, nivel="avanzado", unidad="px")
_a("marca_img_x", "entero", 0, "animaciones", "Imágenes y figuras marcadas: mover a los lados", "Marked images and shapes: move sideways", "", "", -1080, 1080, nivel="avanzado", unidad="px")
_a("marca_img_y", "entero", 47, "animaciones", "Imágenes y figuras marcadas: altura (% del video)", "Marked images and shapes: height (% of the video)", "0 = arriba de todo, 100 = abajo de todo.", "0 = very top, 100 = very bottom.", 5, 95, nivel="avanzado", unidad="%")
_a("marca_img_pct", "entero", 55, "animaciones", "Imágenes marcadas: ancho (% del video)", "Marked images: width (% of the video)", "", "", 10, 100, nivel="avanzado", unidad="%")
_a("onda_audio", "si_no", False, "animaciones", "Onda de sonido que se mueve con la voz", "Sound wave that moves with the voice",
   "Ideal para podcasts y audios: dibuja una onda animada con tu voz.", "Great for podcasts and audio: draws an animated wave with your voice.")
_a("onda_pos", "opcion", "abajo", "animaciones", "Dónde va la onda", "Where the wave goes", "", "",
   opciones=[("arriba", "Arriba", "Top"), ("centro", "Centro", "Center"), ("abajo", "Abajo", "Bottom")])
_a("onda_alto", "entero", 14, "animaciones", "Alto de la onda", "Wave height", "", "", 5, 40, unidad="%")
_a("onda_color", "texto", "#ffffff", "animaciones", "Color de la onda (ej.: #ffffff)", "Wave color (e.g. #ffffff)", "", "")
_a("burbuja_brillo", "si_no", False, "burbujas", "Brillo alrededor de las burbujas", "Glow around the bubbles", "", "")
_a("burbuja_entrada", "opcion", "normal", "burbujas", "Cómo entran las burbujas", "How bubbles come in",
   "«Normal» = como el resto del video.", "“Normal” = like the rest of the video.",
   opciones=[("normal", "Normal", "Normal")] + [(k, v[0], v[1]) for k, v in ENTRADAS_BURBUJA.items()])
_a("burbuja_salida", "opcion", "normal", "burbujas", "Cómo salen las burbujas", "How bubbles go out",
   "«Normal» = desaparecen de golpe.", "“Normal” = they disappear instantly.",
   opciones=[("normal", "Normal", "Normal")] + [(k, v[0], v[1]) for k, v in SALIDAS_BURBUJA.items()])
_a("burbuja_silenciosa_seg", "decimal", 2.5, "burbujas", "Segundos de una burbuja sin voz",
   "Seconds for a silent bubble", "Las que escribes entre llaves { }.", "The ones you write between { }.",
   0.5, 10, unidad="s")

# ---- Clips y escenas -------------------------------------------------------
_a("escena_min", "decimal", 1.5, "clips", "Duración mínima de una escena", "Minimum scene length", "", "",
   0.5, 10, unidad="s")
_a("escena_max", "decimal", 3, "clips", "Duración máxima de una escena", "Maximum scene length", "", "",
   0.8, 15, unidad="s")
_a("kit_final", "si_no", True, "clips", "Terminar siempre con las imágenes del producto",
   "Always end with the product images",
   "La última escena usa tus imágenes de producto / servicio.", "The last scene uses your product / service images.")
_a("final_segundos", "decimal", 2.8, "clips", "Duración de esa escena final", "Final scene length", "", "",
   1, 10, unidad="s")

# ---- Transiciones y efectos ------------------------------------------------
_a("transiciones", "opcion", "dinamicas", "transiciones", "Estilo de transiciones", "Transition style",
   "Dinámicas: deslizar, círculo, zoom... Suaves: solo fundidos. Mixtas: de todo.",
   "Dynamic: slides, circles, zooms... Soft: fades only. Mixed: everything.",
   opciones=[("dinamicas", "Dinámicas", "Dynamic"), ("suaves", "Suaves", "Soft"), ("mixtas", "Mixtas", "Mixed")])
_a("transiciones_permitidas", "lista", "", "transiciones", "Elegir transiciones una por una",
   "Pick transitions one by one", "Vacío = según el estilo. Si eliges algunas, solo se usan esas.",
   "Empty = follow the style. If you pick some, only those are used.",
   opciones=TRANSICIONES_DINAMICAS + TRANSICIONES_SUAVES, nivel="avanzado")
_a("transicion", "decimal", 0.25, "transiciones", "Duración de cada transición", "Transition length",
   "Más chico = corte más seco.", "Smaller = snappier cut.", 0.05, 1.0, unidad="s")
_a("efectos_clip", "lista", ",".join(EFECTOS_CLIP), "transiciones", "Movimiento de los clips",
   "Clip movement", "Qué movimientos pueden usarse en los clips.", "Which movements may be used on clips.",
   opciones=EFECTOS_CLIP)
_a("zoom_max", "decimal", 1.25, "transiciones", "Fuerza del zoom", "Zoom strength",
   "1.0 = sin zoom. 1.25 = fuerte.", "1.0 = no zoom. 1.25 = strong.", 1.0, 1.6)
_a("destello", "si_no", True, "transiciones", "Destello en cada corte", "Flash on every cut", "", "")
_a("destello_intensidad", "entero", 16, "transiciones", "Intensidad del destello", "Flash intensity", "", "",
   1, 60, unidad="%", nivel="avanzado")

# ---- Animaciones -----------------------------------------------------------
_a("movimiento", "si_no", True, "animaciones", "Animaciones activadas", "Animations on",
   "Interruptor general de las animaciones de abajo.", "Master switch for the animations below.")
_a("barra_progreso", "si_no", True, "animaciones", "Barra de progreso", "Progress bar", "", "")
_a("color_barra", "color", "", "animaciones", "Color de la barra", "Bar color",
   "Vacío = el color de la palabra activa de los subtítulos.", "Empty = the active subtitle word color.")
_a("barra_y", "entero", 1890, "animaciones", "Posición de la barra", "Bar position", "", "", 0, 1906, unidad="px")
_a("barra_alto", "entero", 14, "animaciones", "Grosor de la barra", "Bar thickness", "", "", 2, 60, unidad="px")

# ---- Audio -----------------------------------------------------------------
_a("voz_volumen", "entero", 100, "audio", "Volumen de la voz", "Voice volume", "", "", 0, 300, unidad="%")
_a("musica_volumen", "entero", 8, "audio", "Volumen de la música", "Music volume",
   "0 = sin música. La música sale de la carpeta 'musica' del producto.",
   "0 = no music. Music comes from the product's 'musica' folder.", 0, 100, unidad="%")
_a("musica_archivo", "texto", "", "audio", "Usar siempre esta canción", "Always use this song",
   "Vacío = una al azar de la carpeta 'musica'. Escribe el nombre del archivo para fijar una.",
   "Empty = random from the 'musica' folder. Type a file name to pin one.")
_a("sonido_burbuja", "si_no", True, "audio", "Sonido «pop» con cada burbuja", "Bubble «pop» sound", "", "")
_a("sonido_burbuja_volumen", "entero", 55, "audio", "Volumen del «pop»", "Pop volume", "", "", 0, 100, unidad="%")
_a("burbuja_sonido", "texto", "", "audio", "Sonido de las burbujas", "Bubble sound",
   "Vacío = el «pop» normal. Tus propios sonidos (los subes aquí mismo) aparecen en la lista.", "Empty = the normal “pop”. Your own sounds (upload them right here) appear in the list.")
_a("sonido_transicion", "texto", "", "audio", "Sonido en cada transición", "Sound on each transition",
   "Vacío = sin sonido. Elige uno de la app o uno que hayas subido.", "Empty = no sound. Pick one from the app or one you uploaded.")
_a("sonido_titulo", "texto", "", "audio", "Sonido al aparecer el título", "Title entrance sound",
   "Vacío = sin sonido.", "Empty = no sound.")
_a("sonido_cta", "texto", "", "audio", "Sonido al aparecer la frase final", "Closing line entrance sound",
   "Vacío = sin sonido.", "Empty = no sound.")
_a("sonido_efectos_volumen", "entero", 60, "audio", "Volumen de estos efectos", "Effects volume", "", "", 0, 100, unidad="%")

# ---- Tiempos / avanzado ----------------------------------------------------
_a("cola_segundos", "decimal", 0.6, "tiempos", "Segundos extra al final del audio", "Extra seconds after the audio",
   "Silencio al final para que el video no termine de golpe.", "Silence at the end so the video doesn't stop abruptly.",
   0, 5, unidad="s")
_a("subs_ajuste", "decimal", 0, "tiempos", "Ajuste fino de subtítulos (segundos)", "Subtitle fine-tune (seconds)",
   "Si los subtítulos salen tarde, pon un número negativo (por ejemplo -0.3); si salen antes que la voz, uno positivo. 0 = sin ajuste.",
   "If subtitles show up late, use a negative number (e.g. -0.3); if they appear before the voice, a positive one. 0 = no adjustment.",
   -3, 3, unidad="s")
_a("ancho", "entero", 1080, "avanzado", "Ancho del video", "Video width", "", "", 360, 2160, nivel="avanzado", unidad="px")
_a("alto", "entero", 1920, "avanzado", "Alto del video", "Video height", "", "", 640, 3840, nivel="avanzado", unidad="px")
_a("fps", "entero", 30, "avanzado", "Cuadros por segundo", "Frames per second", "", "", 24, 60, nivel="avanzado")
_a("zona_segura_arriba", "entero", 150, "avanzado", "Franja: margen superior del título", "Strip: title top margin",
   "", "", 0, 600, nivel="avanzado", unidad="px")
_a("zona_segura_abajo", "entero", 260, "avanzado", "Franja: margen inferior", "Strip: bottom margin",
   "", "", 0, 600, nivel="avanzado", unidad="px")
_a("fuente", "fuente", "", "avanzado", "Tipo de letra general", "General font",
   "Nombre (ej. Impact) o ruta de un archivo .ttf. Vacío = automático.",
   "Name (e.g. Impact) or path to a .ttf file. Empty = automatic.", nivel="basico")
_a("whisper_modelo", "texto", "small", "avanzado", "Modelo de reconocimiento de voz (opcional)",
   "Speech recognition model (optional)", "", "", nivel="avanzado")

POR_CLAVE = {a["clave"]: a for a in AJUSTES}


# ----------------------------------------------------------------------------
# Valores, validacion y escritura
# ----------------------------------------------------------------------------
def defectos():
    return {a["clave"]: a["defecto"] for a in AJUSTES}


_SI = {"si", "sí", "s", "yes", "y", "true", "1", "on", "activado"}
_NO = {"no", "n", "false", "0", "off", "desactivado"}


def validar(clave, texto):
    """Convierte lo que escribió el usuario al tipo correcto.
    Devuelve (valor, mensaje_de_error). Si hay error, valor es None."""
    a = POR_CLAVE.get(clave)
    if a is None:
        return None, "ese ajuste no existe"
    t = str(texto).strip()
    tipo = a["tipo"]
    if tipo == "si_no":
        if t.lower() in _SI:
            return True, None
        if t.lower() in _NO:
            return False, None
        return None, "escribe si o no"
    if tipo in ("entero", "decimal"):
        limpio = t.lower().replace(",", ".").replace("%", "").replace("px", "").strip()
        if limpio.endswith("s"):
            limpio = limpio[:-1].strip()
        try:
            v = float(limpio)
        except ValueError:
            return None, "debe ser un número"
        if a["min"] is not None and v < a["min"]:
            v = a["min"]
        if a["max"] is not None and v > a["max"]:
            v = a["max"]
        return (int(round(v)) if tipo == "entero" else v), None
    if tipo == "color":
        if t == "":
            return "", None
        try:
            ImageColor.getrgb(t)
        except ValueError:
            return None, "color no válido (usa por ejemplo #FFD400 o yellow)"
        return t, None
    if tipo == "opcion":
        validos = [o[0] for o in a["opciones"]]
        n = t.lower()
        if n in validos:
            return n, None
        for v in validos:
            if v and (n == v or (n.startswith(v[:4]) and len(n) >= 4)):
                return v, None
        return None, "elige una de: " + ", ".join(validos)
    if tipo == "lista":
        if t == "":
            return "", None
        items = [x.strip() for x in t.split(",") if x.strip()]
        malos = [x for x in items if x not in a["opciones"]]
        if malos:
            return None, "no reconozco: " + ", ".join(malos)
        return ",".join(items), None
    return t, None  # texto, fuente


def a_texto(a, valor):
    """Como se escribe un valor en ajustes.txt."""
    if a["tipo"] == "si_no":
        return "si" if valor else "no"
    if a["tipo"] == "decimal":
        return f"{valor:g}"
    return str(valor)


def texto_ajustes(valores=None, idioma="es"):
    """Genera el contenido de ajustes.txt, con comentarios, a partir del catalogo."""
    valores = {**defectos(), **(valores or {})}
    en = idioma == "en"
    cab = ("# SETTINGS FOR THIS PRODUCT (edit with Notepad, or use the program)\n"
           "# Format:  name: value     (lines starting with # are ignored)\n"
           if en else
           "# AJUSTES DE ESTE PRODUCTO (se editan con el Bloc de notas o desde el programa)\n"
           "# Formato:  nombre: valor     (las lineas que empiezan con # se ignoran)\n")
    partes = [cab]
    nombres_cat = {c[0]: (c[2] if en else c[1]) for c in CATEGORIAS}
    for cat, _, _ in CATEGORIAS:
        grupo = [a for a in AJUSTES if a["categoria"] == cat]
        if not grupo:
            continue
        partes.append(f"\n# ===== {nombres_cat[cat].upper()} =====\n")
        for a in grupo:
            ayuda = a["ayuda_en"] if en else a["ayuda_es"]
            titulo = a["en"] if en else a["es"]
            extra = ""
            if a["min"] is not None and a["max"] is not None:
                extra = f" ({a['min']} - {a['max']}{(' ' + a['unidad']) if a['unidad'] else ''})"
            elif a["tipo"] == "si_no":
                extra = " (si / no)" if not en else " (yes / no)"
            elif a["tipo"] == "opcion":
                extra = " (" + " / ".join(o[0] for o in a["opciones"]) + ")"
            elif a["tipo"] == "lista":
                extra = " (" + ", ".join(a["opciones"]) + ")" if len(a["opciones"]) < 8 else ""
            partes.append(f"# {titulo}{extra}" + (f": {ayuda}" if ayuda else "") + "\n")
            partes.append(f"{a['clave']}: {a_texto(a, valores[a['clave']])}\n")
    return "".join(partes)


# valores de fabrica del formato vertical = los del catalogo (para poder volver a ellos)
PRESETS_FORMATO["vertical"] = {k: POR_CLAVE[k]["defecto"] for k in PRESETS_FORMATO["cuadrado"]}
