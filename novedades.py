"""QUÉ CAMBIÓ EN CADA VERSIÓN. Es el archivo que editas cada vez que sacas una versión nueva.

Cada cambio tiene:
  tipo: "nuevo" (algo que se agregó), "cambio" (algo que ahora funciona distinto) o "quitado" (algo que ya no está)
  es / en: el texto corto que verá la persona (una frase clara, sin tecnicismos)
  tema: (opcional) parte del tutorial que explica ese cambio, para el botón «Ver cómo». Temas válidos:
        empezar, producto, guiones, burbujas, clips, musica, estilo, crear, videos, papelera, app, plan
        En los «quitado» normalmente no hay tema.

Pasos para una versión nueva:  1) en marca.py sube VERSION (por ejemplo "0.6.0");  2) aquí abajo agrega una entrada con ESA misma versión
(arriba de las demás);  3) si cambiaste algo del tutorial (guia.js / i18n_guia.js) revisa que el tema siga contando lo correcto.
Con eso, quien actualice verá en el aviso lo que cambió y, al abrir la versión nueva, la pantalla «Qué hay de nuevo» con el botón del tutorial.
"""

CAMBIOS = {
    "0.6.3": [
        {"tipo": "nuevo", "tema": "app", "es": "Ver Vibovapp en tu celular con un QR y un PIN (también desde fuera de tu Wi-Fi). Ves quién está conectado y puedes sacar a cualquiera.",
         "en": "See Vibovapp on your phone with a QR and a PIN (even away from your Wi-Fi). You see who is connected and can remove anyone."},
        {"tipo": "nuevo", "tema": "clips", "es": "Graba video o solo audio directo en la app, para subirlo y editarlo al momento.",
         "en": "Record video or audio-only right in the app, to upload and edit it right away."},
        {"tipo": "nuevo", "tema": "estilo", "es": "En la vista previa de Estilo mueves de lado y cambias el ancho y el tamaño de los textos, eliges varios con Shift y acomodas también los textos e imágenes del guion.",
         "en": "In the Style preview you move texts sideways, change their width and size, pick several with Shift and also place the script's texts and images."},
        {"tipo": "nuevo", "tema": "estilo", "es": "Nuevo estilo de subtítulos «Dos niveles» y estilo listo «Noticia»: palabras clave grandes arriba, la frase en una caja abajo y una barra de avance, como los reels de noticias.",
         "en": "New “Two levels” subtitle style and ready-made “News” style: big key words on top, the phrase in a box below and a progress bar, like news reels."},
        {"tipo": "nuevo", "tema": "estilo", "es": "La forma de la burbuja del emisor y la del receptor pueden ser distintas.",
         "en": "The sender's and the receiver's bubble can have different shapes."},
        {"tipo": "nuevo", "tema": "guiones", "es": "Cambia el nombre de cada guion.",
         "en": "Rename each script."},
        {"tipo": "cambio", "tema": "crear", "es": "El botón de crear videos queda a la derecha, junto al avance con el logo.",
         "en": "The create-videos button now sits on the right, next to the progress with the logo."},
        {"tipo": "cambio", "tema": "app", "es": "Si algo falla, el aviso trae un código y, al tocarlo, te dice en qué paso falló.",
         "en": "If something fails, the notice shows a code and, when you tap it, tells you at which step it failed."},
        {"tipo": "cambio", "tema": "guiones", "es": "Los subtítulos de un audio grabado en la app empiezan cuando de verdad empiezas a hablar.",
         "en": "Subtitles for audio recorded in the app start when you really start talking."},
    ],
    "0.6.1": [
        {"tipo": "nuevo", "tema": "hablado", "es": "Pestaña «Video hablado» en cada producto: sube tu video hablando, o una conversación con un video por persona y un guion. Quita silencios, alterna zoom, mete tus clips con [tema] y subtitula.",
         "en": "“Talking video” tab in each product: upload you talking, or a conversation with one video per person and a script. Removes silences, alternates zoom, adds your clips with [topic] and subtitles."},
        {"tipo": "nuevo", "tema": "hablado", "es": "Guion más específico en «Video hablado» (planes de pago): (clips) o (cara) para elegir qué se ve, y burbujas de WhatsApp con [yo: …] y [cliente: …].",
         "en": "More specific “Talking video” script (paid plans): (clips) or (cara) to choose what is shown, and WhatsApp bubbles with [yo: …] and [cliente: …]."},
        {"tipo": "nuevo", "tema": "estilo", "es": "Subtítulos con movimiento (pop, subir, fundido, rebote), estilo al azar en cada tarjeta y palabra clave destacada con color o caja.",
         "en": "Subtitles with motion (pop, rise, fade, bounce), a random style on every card and a highlighted key word with color or box."},
        {"tipo": "nuevo", "tema": "estilo", "es": "Cuatro estilos listos nuevos: Cinemático, Viral, Palabra a palabra y Creador.",
         "en": "Four new ready-made styles: Cinematic, Viral, Word by word and Creator."},
        {"tipo": "nuevo", "tema": "app", "es": "Al abrir el programa por primera vez te pregunta el idioma (español o inglés) y luego la apariencia (oscuro, claro o como Windows). Los cambias cuando quieras arriba.",
         "en": "The first time you open the program it asks your language (Spanish or English) and then the look (dark, light or like Windows). You can change both any time at the top."},
        {"tipo": "cambio", "tema": "app", "es": "Corregidos los colores de las listas de idioma y apariencia: en el tema claro ya no salen con letra blanca sobre fondo blanco.",
         "en": "Fixed the colors of the language and appearance lists: in the light theme they no longer show white text on a white background."},
    ],
    "0.5.9": [
        {"tipo": "cambio", "tema": "app", "es": "Arreglo al abrir el programa: ya no se queda en pantalla vacía. Si algo falla, el aviso ahora dice qué fue.",
         "en": "Fix when opening the program: it no longer stays on an empty screen. If something fails, the message now says what it was."},
    ],
    "0.5.8": [
        {"tipo": "cambio", "tema": "plan", "es": "Planes nuevos: Gratis, Básico (9 USD), Pro (19) y Agencia (39), con más videos al mes. Créditos de 2 USD o 10 por 12. Varios formatos a la vez ahora es de Pro y Agencia.",
         "en": "New plans: Free, Basic (9 USD), Pro (19) and Agency (39), with more videos per month. Credits at 2 USD or 10 for 12. Several formats at once is now for Pro and Agency."},
        {"tipo": "nuevo", "tema": "guiones", "es": "Guiones listos para usar: ejemplos con burbujas de WhatsApp y otros básicos (solo texto y voz). Los agregas a tu producto, cambias los datos y les pones voz (Pro y Agencia).",
         "en": "Ready-made scripts: examples with WhatsApp bubbles and basic ones (text and voice only). Add them to your product, change the details and add a voice (Pro and Agency)."},
        {"tipo": "nuevo", "tema": "crear", "es": "Al crear videos ves el peso aproximado en MB de lo que se va a generar; se ajusta al peso real de tus videos anteriores.",
         "en": "When creating videos you see the approximate size in MB of what will be generated; it adjusts to the real size of your earlier videos."},
        {"tipo": "nuevo", "tema": "videos", "es": "Al compartir un video tienes un texto sugerido para publicar (descripción y hashtags) listo para editar y copiar.",
         "en": "When sharing a video you get a suggested text to post (caption and hashtags), ready to edit and copy."},
        {"tipo": "nuevo", "tema": "estilo", "es": "Nuevos estilos de subtítulo: palabra en caja de color, palabra más grande o una palabra a la vez. Se eligen en Estilo > Subtítulos.",
         "en": "New subtitle styles: word in a color box, bigger word or one word at a time. Choose them in Style > Subtitles."},
        {"tipo": "cambio", "tema": "clips", "es": "Los clips ya no se repiten en un mismo video, ni entre carpetas, ni cuando son copias del mismo archivo con otro nombre.",
         "en": "Clips no longer repeat within a video, across folders, or when they are copies of the same file with another name."},
        {"tipo": "cambio", "tema": "guiones", "es": "Guiones más limpios: arriba solo agregas guiones nuevos y abajo tus guiones salen como una lista; haz clic en uno para abrir su editor, con su interruptor y su basurita en la misma fila.",
         "en": "Cleaner scripts: add new ones at the top, and your scripts appear below as a list; click one to open its editor, with its switch and trash button on the same row."},
        {"tipo": "nuevo", "tema": "plan", "es": "«Mi plan» ahora es una tarjeta de membresía: estado, miembro desde, próxima renovación, videos usados con barra y botones para administrar, cambiar de plan o verificar.",
         "en": "“My plan” is now a membership card: status, member since, next renewal, videos used with a bar, and buttons to manage, change plan or verify."},
        {"tipo": "cambio", "tema": "app", "es": "Interfaz más ordenada y simétrica: la barra superior y el contenido comparten columna y las pestañas se reparten parejas en todo el ancho.",
         "en": "Tidier, symmetric interface: the top bar and content share one column and the tabs spread evenly across the full width."},
        {"tipo": "cambio", "tema": "plan", "es": "Con un plan de pago, tus videos se renuevan cada mes desde el día que compraste (si compraste el 15, cada día 15). En «Mi plan» ves la próxima fecha. El plan gratis sigue renovando el día 1.",
         "en": "With a paid plan, your videos renew every month from the day you bought it (bought on the 15th, renews every 15th). “My plan” shows the next date. The free plan still renews on the 1st."},
        {"tipo": "nuevo", "tema": "capas", "es": "Nueva pestaña «Logos y capas»: pon tu logo, un sello, un GIF o un video con fondo transparente encima de tus videos. Eliges dónde, qué tamaño y en qué segundos aparece, y conserva su transparencia.",
         "en": "New “Logos and layers” tab: put your logo, a stamp, a GIF or a video with a transparent background on top of your videos. Choose where, how big and in which seconds it shows; transparency is kept."},
        {"tipo": "nuevo", "tema": "capas", "es": "Ahora puedes subir logos en SVG, PDF o AI: se convierten solos a PNG y conservan su transparencia. Sirve en «Logos y capas» y también en clips y palabras clave.",
         "en": "You can now upload logos as SVG, PDF or AI: they convert to PNG by themselves and keep their transparency. Works in “Logos and layers” and also in clips and keywords."},
        {"tipo": "cambio", "tema": "clips", "es": "Los PNG, WebP y GIF con transparencia usados como clips ya no se ven con negro o blanco detrás: la parte transparente se llena con el color de fondo de tu video.",
         "en": "PNG, WebP and GIF files with transparency used as clips no longer show black or white behind them: the transparent part is filled with your video's background color."},
        {"tipo": "cambio", "tema": "estilo", "es": "Estilo tiene ahora un modo sencillo (Título, Subtítulos, Frase final, Usuario, Burbujas y Audio) y un «Modo completo» con todo lo demás. Si tocas la vista previa, abre solo la sección que necesitas.",
         "en": "Style now has a simple mode (Title, Subtitles, Closing phrase, Username, Bubbles and Audio) and a “Full mode” with everything else. If you tap the preview, it opens just the section you need."},
        {"tipo": "cambio", "tema": "estilo", "es": "En Estilo se quitó el botón «Guardar cambios»: todo ya se guardaba solo. Ahora lo dice claro, y se explica qué es un estilo guardado y qué es una plantilla de temas.",
         "en": "The “Save changes” button was removed from Style: everything was already saved automatically. It now says so clearly, and explains what a saved style and a topic template are."},
        {"tipo": "nuevo", "tema": "clips", "es": "Ahora puedes copiar archivos (o una captura) y pegarlos con Ctrl+V en las zonas de subida: clips, música, guiones y más. Pasa el mouse sobre la zona donde quieres pegar.",
         "en": "You can now copy files (or a screenshot) and paste them with Ctrl+V into the upload areas: clips, music, scripts and more. Hover over the area where you want to paste."},
        {"tipo": "nuevo", "tema": "videos", "es": "Botón «Compartir» en tus videos terminados: copia el video para pegarlo con Ctrl+V en WhatsApp Web, o abre Instagram, TikTok, Facebook o YouTube y te lo muestra en su carpeta.",
         "en": "“Share” button on your finished videos: copy the video to paste it with Ctrl+V in WhatsApp Web, or open Instagram, TikTok, Facebook or YouTube with your video shown in its folder."},
        {"tipo": "cambio", "tema": "clips", "es": "Ahora acepta más archivos de WhatsApp: notas de voz (.opus), videos .3gp y .mpeg, imágenes .gif y .jfif, y los que bajan sin extensión. Los .heic hay que pasarlos antes a JPG.",
         "en": "Accepts more WhatsApp files: voice notes (.opus), .3gp and .mpeg videos, .gif and .jfif images, and files saved without an extension. .heic files must be converted to JPG first."},
        {"tipo": "cambio", "tema": "clips", "es": "Corregido: algunos videos (como ciertos .webm) hacían fallar la creación porque no traían escrita su duración. Ahora la app la calcula sola.",
         "en": "Fixed: some videos (like certain .webm files) made creation fail because they had no duration saved. The app now works it out itself."},
        {"tipo": "nuevo", "tema": "estilo", "es": "Las burbujas pueden tener otra forma (clásica, cuadrada, píldora, globo, pensamiento). La eliges viendo un dibujito, y tus mensajes y los del cliente pueden tener formas distintas.",
         "en": "Bubbles can have a different shape (classic, square, pill, balloon, thought). Pick it from a small drawing, and your messages and the customer's can have different shapes."},
        {"tipo": "nuevo", "tema": "estilo", "es": "Estilos listos para usar en Estilo: Clásico, Elegante, Divertido, Minimal y Neón. Con un clic cambian colores, formas de burbuja y contornos; tu texto, música y clips no se tocan.",
         "en": "Ready-made styles in Style: Classic, Elegant, Fun, Minimal and Neon. One click changes colors, bubble shapes and outlines; your text, music and clips are not touched."},
        {"tipo": "cambio", "tema": "estilo", "es": "Estilo es más corto y limpio: abre una sección a la vez, y se cierran las demás solas.",
         "en": "Style is shorter and cleaner: it opens one section at a time and closes the others for you."},
        {"tipo": "cambio", "tema": "app", "es": "Pantallas más limpias: «Empezar de cero» y las plantillas de temas quedaron en «Más opciones» o plegadas, y las vistas previas son más chicas. El botón «Crear videos» queda siempre a la vista.",
         "en": "Cleaner screens: “Start from zero” and topic templates now sit under “More options” or folded, and format previews are smaller."},
        {"tipo": "cambio", "tema": "empezar", "es": "En la práctica, al hacer clic para subir archivos se abre el selector de Windows justo en la carpeta del material donde están los archivos de ese paso, y la siguiente carpeta de clips cada vez.",
         "en": "In the practice, clicking to upload files opens the Windows file picker right in the practice-material folder where that step's files are, and the next clips folder each time."},
        {"tipo": "cambio", "tema": "empezar", "es": "Al llegar al final de la práctica, su producto queda bloqueado y ya no crea más videos. Puedes borrarlo y repetir la práctica cuando quieras, o hacer tus videos en tu propio producto.",
         "en": "When you reach the end of the practice, its product is locked and no longer creates videos. You can delete it and repeat the practice any time, or make your videos in your own product."},
        {"tipo": "cambio", "tema": "empezar", "es": "El panel de la práctica se mueve para no tapar lo que hay que tocar y siempre muestra sus botones. Ya no te guía dentro de ventanas que abres tú (como «Mi plan») ni repite palabras que ya existen.",
         "en": "The practice panel moves out of the way of what you need to tap and always shows its buttons. It no longer guides you inside windows you open yourself (like “My plan”) or suggests words that already exist."},
        {"tipo": "nuevo", "tema": "app", "es": "La primera vez que abres la app te pregunta qué apariencia prefieres: oscuro, claro o como tu Windows. Tu elección se guarda y la puedes cambiar cuando quieras.",
         "en": "The first time you open the app it asks which look you prefer: dark, light or like your Windows. Your choice is saved and you can change it any time."},
        {"tipo": "cambio", "tema": "plan", "es": "La ventana «Mi plan» es más ancha y ya no hay textos tapados: los valores y las tarjetas de los planes se leen completos.",
         "en": "The “My plan” window is wider and no text is covered: values and plan cards read in full."},
    ],
    "0.5.7": [
        {"tipo": "cambio", "tema": "empezar", "es": "En la práctica guiada ya no tienes que usar las palabras ni los nombres del ejemplo: pones tus propias palabras clave y clips, una carpeta tras otra, y el resaltado te lleva a la siguiente.",
         "en": "In the guided practice you no longer have to use the example words or names: add your own keywords and clips, one folder after another, and the highlight takes you to the next one."},
        {"tipo": "cambio", "tema": "empezar", "es": "En la práctica, los pasos de burbujas e imágenes resaltan el lugar exacto donde hay que tocar, y «Crear videos» ya no se resalta mientras tu video se está creando.",
         "en": "In the practice, the bubbles and images steps highlight the exact spot to tap, and “Create videos” is no longer highlighted while your video is being made."},
    ],
    "0.5.6": [
        {"tipo": "cambio", "tema": "empezar", "es": "En la práctica guiada ya no tienes que usar las palabras ni los nombres del ejemplo: pones tus propias palabras clave y clips, una carpeta tras otra, y el resaltado te lleva a la siguiente.",
         "en": "In the guided practice you no longer have to use the example words or names: add your own keywords and clips, one folder after another, and the highlight takes you to the next one."},
        {"tipo": "cambio", "tema": "empezar", "es": "En la práctica, los pasos de burbujas e imágenes resaltan el lugar exacto donde hay que tocar, y «Crear videos» ya no se resalta mientras tu video se está creando.",
         "en": "In the practice, the bubbles and images steps highlight the exact spot to tap, and “Create videos” is no longer highlighted while your video is being made."},
    ],
    "0.5.4": [
        {"tipo": "nuevo", "tema": "estilo", "es": "Sube tus propias tipografías (.ttf/.otf) con «＋ Subir tipografía» junto a cada tipo de letra en «Estilo»: se agregan a la lista y puedes usarlas en título, subtítulos, burbujas, etc.",
         "en": "Upload your own fonts (.ttf/.otf) with “＋ Upload font” next to each font setting in “Style”: they join the list and you can use them for title, subtitles, bubbles, etc."},
        {"tipo": "nuevo", "tema": "estilo", "es": "Sube tus propios sonidos y elígelos en «Estilo» → Audio para burbujas, transiciones, entrada del título y de la frase final. Incluye sonidos de la app (pop, ding, clic, whoosh) con ▶ para oírlos.",
         "en": "Upload your own sounds and pick them in “Style” → Audio for bubbles, transitions, title entrance and closing-line entrance. Includes app sounds (pop, ding, click, whoosh) with ▶ to listen."},
        {"tipo": "nuevo", "tema": "estilo", "es": "Tu burbuja y la del cliente se mueven y cambian de tamaño cada una por su lado, arrastrándolas en la vista previa (Shift = línea recta, asas = tamaño) o con los ajustes de «Burbujas».",
         "en": "Your bubble and the customer's can each be moved and resized separately by dragging in the preview (Shift = straight line, handles = size) or with the “Bubbles” settings."},
        {"tipo": "cambio", "tema": "empezar", "es": "El producto de la práctica guiada no cuenta en el límite de productos de tu plan y sirve para repetirla. Es solo de práctica (máximo 3 videos); al final puedes borrarlo con un botón.",
         "en": "The guided-practice product doesn't count toward your plan's product limit and lets you repeat it. It's practice-only (max 3 videos); at the end you can delete it with a button."},
        {"tipo": "nuevo", "tema": "estilo", "es": "En «Estilo» usa la vista previa: arrastra título, subtítulos, frase final, usuario, burbujas o barra; un clic va a sus ajustes y doble clic escribe el usuario y la frase final (o va al guion).",
         "en": "In “Style” use the preview: drag title, subtitles, closing line, username, bubbles or bar; one click jumps to settings, double-click types the username and closing line (or goes to the script)."},
        {"tipo": "cambio", "tema": "empezar", "es": "En la práctica guiada puedes ponerle el nombre que quieras al producto, a los temas y a las burbujas (solo sugerimos ejemplos). El panel de instrucciones ya no se oscurece.",
         "en": "In the guided practice you can name the product, themes and bubbles whatever you like (we only suggest examples). The instructions panel no longer gets dimmed."},
        {"tipo": "nuevo", "tema": "empezar", "es": "Puedes salir de la práctica guiada en cualquier momento con la tecla Esc; no tienes que terminarla. La retomas desde «Ayuda».",
         "en": "You can leave the guided practice at any time with the Esc key; you don't have to finish it. Pick it up again from “Help”."},
        {"tipo": "nuevo", "tema": "empezar", "es": "En «Mis productos» siempre está a la vista el botón «Video de prueba · tutorial paso a paso», por si quieres hacerlo o se te olvidó.",
         "en": "In “My products” the “Test video · step-by-step tutorial” button is always in view, in case you want to do it or forgot."},
    ],
    "0.5.3": [
        {"tipo": "cambio", "tema": "estilo", "es": "Cada formato (vertical, retrato, cuadrado, horizontal) recuerda las posiciones y tamaños de tus textos y burbujas como los dejaste. Los estilos guardados también los llevan.",
         "en": "Each format (vertical, portrait, square, horizontal) remembers the positions and sizes of your texts and bubbles as you left them. Saved styles carry them too."},
        {"tipo": "nuevo", "tema": "guiones", "es": "Cada guion tiene su botecito 🗑 para mandarlo a la papelera, igual que las carpetas de clips.",
         "en": "Each script has its own 🗑 button to send it to the trash, just like the clip folders."},
        {"tipo": "cambio", "tema": "empezar", "es": "La práctica guiada (oscurece la pantalla y te dice dónde picar) ahora es la opción principal de la bienvenida y de Ayuda, y tiene su botón en «Qué hay de nuevo».",
         "en": "The guided practice (darkens the screen and shows where to click) is now the main option in the welcome and Help, and has its own button in “What’s new”."},
    ],
    "0.5.2": [
        {"tipo": "nuevo", "tema": "crear", "es": "En «Crear videos» ahora ves una vista previa de cada formato que vas a crear, y puedes poner un tamaño propio (ancho × alto) allí mismo.",
         "en": "In “Create videos” you now see a preview of each format you are about to create, and you can set your own size (width × height) right there."},
        {"tipo": "nuevo", "tema": "crear", "es": "Cuando tus videos terminan de crearse suena la campanita de bienvenida y te sale un aviso «tus videos están listos», sin importar en qué pestaña estés.",
         "en": "When your videos finish, the welcome chime plays and a “your videos are ready” notice pops up, whatever tab you are on."},
        {"tipo": "nuevo", "tema": "empezar", "es": "La práctica guiada ahora oscurece la pantalla y deja bien iluminado solo el lugar donde debes hacer clic, con una etiqueta que te dice qué hacer.",
         "en": "The guided practice now darkens the screen and leaves only the spot where you must click brightly lit, with a label telling you what to do."},
        {"tipo": "cambio", "tema": "estilo", "es": "Todo lo visual de las burbujas (tamaño, colores, letra, posición, brillo, efectos y sonido) ahora se cambia solo en «Estilo». En «Guiones» solo escribes el texto, de quién es y cuándo sale.",
         "en": "Everything visual about bubbles (size, colors, font, position, glow, effects and sound) is now changed only in “Style”. In “Scripts” you only write the text, whose it is and when it appears."},
        {"tipo": "cambio", "tema": "videos", "es": "Al ver un video en pantalla completa, la tecla Esc (o la ✕) te regresa a la lista de tus videos.",
         "en": "When you watch a video full screen, the Esc key (or the ✕) takes you back to your videos list."},
        {"tipo": "cambio", "tema": "plan", "es": "En el plan Gratis la marca «Hecho con» ahora lleva el logo de Vibovapp y también aparece en grande al final del video.",
         "en": "On the Free plan, the “Made with” mark now includes the Vibovapp logo and also appears large at the end of the video."},
        {"tipo": "cambio", "tema": "app", "es": "Las ventanas emergentes (como «Mi plan») ahora se cierran con la ✕ de la esquina, con la tecla Esc o con un clic fuera del cuadro.",
         "en": "Pop-up windows (like “My plan”) now close with the ✕ in the corner, the Esc key, or a click outside the box."},
        {"tipo": "cambio", "tema": "app", "es": "Ahora hay una sola forma de cerrar el programa: la ✕ de la ventana. Si estás creando videos, te pregunta antes de cerrar para que no pierdas el trabajo.",
         "en": "There is now a single way to close the program: the window’s ✕. If videos are being created, it asks before closing so you don’t lose the work."},
    ],
    "0.5.1": [
        {"tipo": "cambio", "tema": "app", "es": "El asistente «¿Dudas?» ahora sabe responder cómo cambiar el nombre de productos, guiones, clips, carpetas y videos.",
         "en": "The “Questions?” assistant now knows how to rename products, scripts, clips, folders and videos."},
    ],
    "0.5.0": [
        {"tipo": "nuevo", "tema": "guiones", "es": "Puedes grabar tu voz directamente en un guion, sin salir del programa.",
         "en": "You can record your voice straight into a script, without leaving the program."},
        {"tipo": "nuevo", "tema": "producto", "es": "En «Mis productos» y en los guiones ahora puedes buscar, filtrar, ordenar y borrar varios a la vez.",
         "en": "In “My products” and in scripts you can now search, filter, sort and delete several at once."},
        {"tipo": "nuevo", "tema": "app", "es": "Nuevas «Preguntas frecuentes» y un asistente de ayuda dentro del programa.",
         "en": "New “Frequently asked questions” and a help assistant inside the program."},
        {"tipo": "nuevo", "tema": "plan", "es": "Planes con precios, paquetes de créditos y compra en línea, con verificación automática de tu suscripción.",
         "en": "Plans with prices, credit packs and online purchase, with automatic checking of your subscription."},
        {"tipo": "nuevo", "tema": "app", "es": "Actualizaciones con un clic: el programa te avisa, te dice qué cambió y se instala solo.",
         "en": "One-click updates: the program notifies you, tells you what changed and installs itself."},
        {"tipo": "cambio", "tema": "estilo", "es": "Todo lo que cambias en «Estilo» (letras, colores, posiciones…) se guarda solo.",
         "en": "Everything you change in “Style” (fonts, colors, positions…) is saved automatically."},
        {"tipo": "cambio", "tema": "app", "es": "El programa abre con el tamaño y la posición con que lo cerraste la última vez.",
         "en": "The program opens with the size and position you left it in last time."},
        {"tipo": "cambio", "tema": "plan", "es": "«Mi plan» ahora muestra el estado de tu suscripción y te deja verificarla o cancelarla.",
         "en": "“My plan” now shows your subscription status and lets you check or cancel it."},
    ],
}

TIPOS = ("nuevo", "cambio", "quitado")
TEMAS = ("empezar", "producto", "guiones", "burbujas", "clips", "musica", "capas", "estilo", "crear", "hablado", "videos", "papelera", "app", "plan")


def _tupla(v):
    import re
    return tuple(int(x) for x in re.findall(r"\d+", str(v))[:4])


def limpiar(cambios):
    """Deja solo cambios bien formados (sirve también para lo que llega de version.json por internet)."""
    res = []
    for c in cambios or []:
        if not isinstance(c, dict) or c.get("tipo") not in TIPOS:
            continue
        es, en = str(c.get("es") or c.get("en") or "")[:220], str(c.get("en") or c.get("es") or "")[:220]
        if es:
            res.append({"tipo": c["tipo"], "es": es, "en": en, "tema": c.get("tema") if c.get("tema") in TEMAS else ""})
    return res[:20]


def desde(version_vista, version_actual):
    """Cambios de las versiones posteriores a version_vista hasta version_actual, la más nueva primero."""
    actual = _tupla(version_actual)
    vista = _tupla(version_vista) if version_vista else ()
    res = []
    for v in sorted(CAMBIOS, key=_tupla, reverse=True):
        if _tupla(v) <= actual and (not vista or _tupla(v) > vista):
            res += [dict(c, version=v) for c in limpiar(CAMBIOS[v])]
        if not vista:
            break                                          # sin dato de lo que vio: solo la versión actual
    return res


def de_la_version(version):
    """Los cambios de ESA versión. Si se te olvidó agregar su entrada arriba, no se muestran cambios de otras versiones
    (eso confundía): sale un aviso general hasta que la agregues."""
    r = limpiar(CAMBIOS.get(version, []))
    return r or [{"tipo": "cambio", "es": "Mejoras y correcciones generales.", "en": "General improvements and fixes.", "tema": ""}]


def frases(cambios, idioma):
    """Los cambios como frases sueltas (para versiones viejas del programa que solo leen una lista de textos)."""
    return [c["en" if idioma == "en" else "es"] for c in cambios]
