// PRÁCTICA GUIADA: un panel flotante que dice qué hacer y dónde, resalta el lugar en pantalla y comprueba cada paso.
// Al final el propio usuario genera su primer video con el material de práctica.
Object.assign(TEXTOS.es, {
  gp_foco_mat: "Presiona este botón", gp_foco_sig: "✓ ¡Listo! Ahora presiona «Siguiente»", gp_foco_ir: "Presiona aquí para ir al lugar correcto", gp_foco_escribe_crear: "Escribe tu nombre y presiona «Crear»", gp_foco_escribe: "Escribe aquí", gp_foco_boton: "Presiona este botón",
  gp_aqui_2: "Haz clic aquí: «+ Nuevo proyecto»", gp_aqui_3: "Arrastra aquí 01.wav y 01.txt", gp_aqui_4: "Haz clic en «01» de la lista", gp_aqui_5: "Aquí: presiona «+ Persona 1» y escribe el mensaje", gp_aqui_6: "Escribe un nombre aquí y presiona el botón (3 veces)",
  gp_aqui_7: "Aquí agrega las palabras clave", gp_f7_una: "Escribe aquí otra palabra clave para esta carpeta y presiona Enter (por ejemplo «{w}»; la que tú quieras, distinta del nombre de la carpeta)", gp_f7_otra: "Abre otra carpeta: aquí también agregas una palabra clave", gp_aqui_8: "Arrastra aquí los clips de este tema", gp_f8_aqui: "Arrastra aquí 2 clips (los que quieras) a esta carpeta", gp_f8_otra: "Abre una carpeta y sube ahí 2 clips", gp_aqui_9: "Abre «proyecto / servicio» y sube 2 imágenes", gp_f9_aqui: "Arrastra aquí las 2 imágenes de tu proyecto", gp_aqui_10: "Arrastra aquí la música", gp_aqui_11: "Escribe aquí tu @usuario", gp_aqui_12: "Presiona «Crear videos»", gp_aqui_13: "Presiona «Ver en carpeta»",
  gp_salio: "Saliste de la práctica. Puedes retomarla cuando quieras desde «Ayuda».", gp_no_cuenta: "Este proyecto es solo de práctica: no cuenta en el límite de tu plan y, al terminar la práctica, ya no crea más videos. Puedes borrarlo y repetir la práctica cuando quieras.", gp_borrar_prac: "Borrar el proyecto de práctica", gp_conf_borrar_prac: "¿Borrar el proyecto de práctica? Se quita con todo lo que subiste a él. Tus otros proyectos no se tocan.", gp_borrada: "Proyecto de práctica borrado", gp_titulo: "Práctica guiada", gp_paso: "Paso {a} de {b}", gp_salir: "Salir", gp_min: "Achicar", gp_max: "Abrir la práctica guiada",
  gp_ir: "Llévame ahí", gp_sig: "Siguiente →", gp_saltar: "Saltar este paso", gp_ant: "←", gp_listo: "✓ ¡Listo, lo hiciste!", gp_espera: "Esperando que lo hagas…",
  gp_terminar: "Terminar", gp_ver_temas: "Ver el recorrido por temas",
  gp_donde: "📍 Los archivos están en:", gp_abrir: "📂 Abrir esa carpeta", gp_abrir1: "📂 Abrir la carpeta", gp_docs: "Documentos", gp_mat_btn: "Guardar el material de práctica", gp_mat_ok: "✓ Listo. Tus archivos de práctica están en:", gp_mat_creando: "Creando el material…",
  gp_conf_salir: "¿Salir de la práctica? Lo que ya hiciste se queda guardado y puedes retomarla desde «? Ayuda».",
  gp_1t: "Guarda el material de práctica", gp_1: "Para practicar necesitas archivos de ejemplo. Presiona el botón de abajo y la app los prepara por ti.\nSe crea una carpeta llamada «Material de práctica» dentro de «Documentos» y se abre sola en una ventana (si no la ves, presiona «📂 Abrir la carpeta»).\nAhí dentro hay un guion, clips, imágenes y música. En cada paso te diré qué archivo subir y dónde está.",
  gp_2t: "Crea tu proyecto", gp_2: "Ve a «Mis proyectos» y presiona el recuadro punteado «+ Nuevo proyecto» (está resaltado).\nEscribe el nombre que tú quieras (por ejemplo: Mi primer proyecto).\nY presiona «Crear».",
  gp_3t: "Sube el guion", gp_3: "Estás en la pestaña «Guiones». Un guion es un audio con su texto escrito.\nSube los dos archivos de la carpeta «1 Guion»: 01.wav y 01.txt. Arrástralos al cuadro punteado (resaltado) o presiónalo para elegirlos; para escoger los dos juntos, mantén presionada la tecla Ctrl.\nSi no encuentras los archivos, presiona «📂 Abrir esa carpeta» aquí abajo.\nEse audio no tiene sonido a propósito: solo sirve para practicar. Después usarás tu propia voz.",
  gp_4t: "Mira el texto del guion", gp_4: "En la lista, haz clic en «01». A la derecha verás su texto: lo que dice el audio.\nFíjate en la primera línea: es el título, sale arriba al inicio y no se dice. Y en las marcas *1 y /1: son burbujas de WhatsApp (*1 = mensaje 1 de la Persona 1, /1 = mensaje 1 de la Persona 2).",
  gp_5t: "Agrega las dos burbujas", gp_5: "Más abajo, en «Burbujas de WhatsApp de este guion» (resaltado), presiona «+ Persona 1» y en su cuadro «Mensaje» escribe lo que quieras; por ejemplo: Hola, ¿esta casa sigue disponible?\nLuego presiona «+ Persona 2» y escribe otro mensaje; por ejemplo: Claro, te cuento todo sobre la zona y el precio.\nSe guardan solas (verás «✓ Guardado automáticamente»); si quieres, también puedes presionar «Guardar burbujas».",
  gp_6t: "Crea tres temas", gp_6: "Ve a la pestaña «Clips y palabras clave». Un tema es una carpeta de clips que se muestra cuando dices ciertas palabras.\nEscribe un nombre en el cuadro de arriba (resaltado) y presiona el botón para crear el tema. Hazlo tres veces, una por una. Ponles los nombres que quieras; te sugerimos casas, ciudad y dinero, porque tu guion habla de eso.",
  gp_7t: "Pon las palabras clave", gp_7: "Cada tema tiene palabras clave: cuando dices una en el audio, el video muestra un clip de ese tema (por ejemplo, si dices «casa» sale un clip del tema de casas).\nAgrega palabras clave en 3 de tus temas: en cada carpeta escribe una palabra en el cuadro de palabras y presiona Enter. Pon las que tú quieras: las del ejemplo («casa», «ciudad», «dinero») son solo una idea. Cuando pongas una, el resaltado te lleva a abrir la siguiente carpeta.",
  gp_8t: "Sube los clips de cada tema", gp_8: "Abre una carpeta con un clic (si ya se ve abierta, déjala así) y sube 2 clips; luego abre otra y sube otros 2, y así hasta completar los 6 archivos de la carpeta «2 Clips». Puedes repartirlos como quieras entre tus carpetas (los nombres casas, ciudad y dinero son solo un ejemplo).\nSi no los encuentras, presiona «📂 Abrir esa carpeta» aquí abajo.",
  gp_9t: "Sube las imágenes de tu proyecto", gp_9: "La carpeta ★ «proyecto / servicio» es para imágenes de lo que vendes: salen al final del video. Ábrela y sube 2 imágenes (las de la carpeta «3 Imágenes del proyecto» o las tuyas; si no las encuentras, presiona «📂 Abrir esa carpeta» aquí abajo).",
  gp_10t: "Sube la música", gp_10: "Ve a la pestaña «Música» y sube musica_practica.m4a (está en la carpeta «4 Música»; si no la encuentras, presiona «📂 Abrir esa carpeta» aquí abajo). Esa canción sonará de fondo, más bajita que la voz.",
  gp_11t: "Ponle tu usuario", gp_11: "Ve a la pestaña «Estilo». Aquí cambias cómo se ve el video. Escribe tu @usuario en «Usuario o marca» (resaltado): saldrá en el video. Mira la vista previa: los cambios se guardan solos (verás «✓ Guardado automáticamente»).\nTambién puedes cambiar el tipo de letra, los colores, el tamaño y la posición del título, los subtítulos y las burbujas; cada ajuste tiene su botón para volver al valor original.",
  gp_12t: "¡Crea tu video!", gp_12: "Ve a la pestaña «Crear videos». Deja 1 video y el formato vertical, y presiona «Crear videos» (resaltado).\nVerás el avance; tarda unos minutos. ESPERA a que termine por completo antes de pasar al siguiente paso. Los primeros 3 videos de la práctica no gastan los videos de tu plan.",
  gp_13t: "Encuentra tu video", gp_13: "Ve a la pestaña «Mis videos». Tu video ya está guardado dentro de la app: no tienes que hacer nada para conservarlo, y no se hacen copias.\nPara publicarlo, presiona «📂 Ver en carpeta» (resaltado): se abre la carpeta donde está tu video, ya seleccionado. Desde ahí lo arrastras o lo eliges cuando lo subas a Instagram, TikTok, WhatsApp, etc.",
  gp_14t: "¡Lo lograste!", gp_14: "Hiciste un video de principio a fin. Ahora repite el proceso con tu propio audio, clips y música. ¿No tienes audio? En «Guiones» presiona «＋ Escribir un guion nuevo», escribe el texto y presiona «🔊 Generar voz»: una voz de la computadora lo narra.\nSi estás en el plan Gratis, tu video lleva la marca «Hecho con Vibovapp»; con un plan de pago se quita.\nTus videos siempre quedan guardados en «Mis videos»; «📂 Ver en carpeta» abre su carpeta.\nCuando quieras, puedes borrar el proyecto «Práctica» (abre el proyecto y presiona «Borrar»). Si se te olvida algo, en «? Ayuda» está el recorrido por temas."
});
Object.assign(TEXTOS.en, {
  gp_foco_mat: "Press this button", gp_foco_sig: "✓ Done! Now press “Next”", gp_foco_ir: "Press here to go to the right place", gp_foco_escribe_crear: "Type a name and press “Create”", gp_foco_escribe: "Type here", gp_foco_boton: "Press this button",
  gp_aqui_2: "Click here: “+ New product”", gp_aqui_3: "Drag 01.wav and 01.txt here", gp_aqui_4: "Click “01” in the list", gp_aqui_5: "Here: press “+ Person 1” and type the message", gp_aqui_6: "Type a name here and press the button (3 times)",
  gp_aqui_7: "Add the keywords here", gp_f7_una: "Type another keyword for this folder here and press Enter (for example “{w}”; any you like, different from the folder name)", gp_f7_otra: "Open another folder: add a keyword here too", gp_aqui_8: "Drag this theme's clips here", gp_f8_aqui: "Drag 2 clips (any you like) into this folder", gp_f8_otra: "Open a folder and upload 2 clips there", gp_aqui_9: "Open “product / service” and upload 2 images", gp_f9_aqui: "Drag your 2 product images here", gp_aqui_10: "Drag the music here", gp_aqui_11: "Type your @username here", gp_aqui_12: "Press “Create videos”", gp_aqui_13: "Press “Show in folder”",
  gp_salio: "You left the practice. You can pick it up again anytime from “Help”.", gp_no_cuenta: "This product is for practice only: it does not count toward your plan limit and, once the practice is finished, it no longer creates videos. You can delete it and repeat the practice whenever you like.", gp_borrar_prac: "Delete the practice product", gp_conf_borrar_prac: "Delete the practice product? It is removed with everything you uploaded to it. Your other products are not touched.", gp_borrada: "Practice product deleted", gp_titulo: "Guided practice", gp_paso: "Step {a} of {b}", gp_salir: "Exit", gp_min: "Minimize", gp_max: "Open the guided practice",
  gp_ir: "Take me there", gp_sig: "Next →", gp_saltar: "Skip this step", gp_ant: "←", gp_listo: "✓ Done, you did it!", gp_espera: "Waiting for you to do it…",
  gp_terminar: "Finish", gp_ver_temas: "See the tour by topic",
  gp_donde: "📍 The files are in:", gp_abrir: "📂 Open that folder", gp_abrir1: "📂 Open the folder", gp_docs: "Documents", gp_mat_btn: "Save the practice material", gp_mat_ok: "✓ Done. Your practice files are in:", gp_mat_creando: "Creating the material…",
  gp_conf_salir: "Exit the practice? What you've done stays saved and you can resume from “? Help”.",
  gp_1t: "Save the practice material", gp_1: "To practice you need example files. Press the button below and the app prepares them for you.\nIt creates a folder called “Practice material” inside “Documents” and opens it in a window (if you don't see it, press “📂 Open the folder”).\nInside there's a script, clips, images and music. At each step I'll tell you which file to upload and where it is.",
  gp_2t: "Create your product", gp_2: "Go to “My products” and press the dashed “+ New product” box (highlighted).\nType any name you like (for example: My first product).\nAnd press “Create”.",
  gp_3t: "Upload the script", gp_3: "You're in the “Scripts” tab. A script is an audio with its written text.\nUpload the two files from the “1 Script” folder: 01.wav and 01.txt. Drag them onto the dashed box (highlighted) or press it to choose them; to pick both together, hold down the Ctrl key.\nIf you can't find the files, press “📂 Open that folder” below.\nThis audio has no sound on purpose: it's only for practice. Later you'll use your own voice.",
  gp_4t: "Look at the script text", gp_4: "In the list, click “01”. On the right you'll see its text: what the audio says.\nNotice the first line: it's the title, shown on top at the start and not spoken. And the marks *1 and /1: they are WhatsApp bubbles (*1 = Person 1's message 1, /1 = Person 2's message 1).",
  gp_5t: "Add the two bubbles", gp_5: "Further down, in “WhatsApp bubbles of this script” (highlighted), press “+ Person 1” and in its “Message” box type whatever you like; for example: Hi, is this house still available?\nThen press “+ Person 2” and type another message; for example: Sure, I will tell you all about the area and the price.\nThey save themselves (you will see “✓ Saved automatically”); you can also press “Save bubbles” if you like.",
  gp_6t: "Create three themes", gp_6: "Go to the “Clips & keywords” tab. A theme is a folder of clips shown when you say certain words.\nType a name in the box on top (highlighted) and press the button to create the theme. Do it three times, one by one. Name them whatever you like; we suggest casas, ciudad and dinero, because your script talks about those.",
  gp_7t: "Set the keywords", gp_7: "Each theme has keywords: when you say one in the audio, the video shows a clip from that theme (for example, saying “house” shows a clip from your houses theme).\nAdd keywords to 3 of your themes: in each folder type a word in the words box and press Enter. Use whatever you like: the examples (“casa”, “ciudad”, “dinero”) are just an idea. Once you add one, the highlight takes you to open the next folder.",
  gp_8t: "Upload each theme's clips", gp_8: "Open a folder with a click (if it already looks open, leave it) and upload 2 clips; then open another and upload 2 more, until you finish the 6 files in the “2 Clips” folder. Split them among your folders however you like (the names casas, ciudad and dinero are just an example).\nIf you can't find them, press “📂 Open that folder” below.",
  gp_9t: "Upload your product images", gp_9: "The ★ “product / service” folder is for images of what you sell: they show at the end of the video. Open it and upload 2 images (the ones in the “3 Product images” folder or your own; if you can't find them, press “📂 Open that folder” below).",
  gp_10t: "Upload the music", gp_10: "Go to the “Music” tab and upload practice_music.m4a (it's in the “4 Music” folder; if you can't find it, press “📂 Open that folder” below). That song plays in the background, softer than the voice.",
  gp_11t: "Add your username", gp_11: "Go to the “Style” tab. Here you change how the video looks. Type your @username in “Username or brand” (highlighted): it will appear in the video. Check the preview: changes save themselves (you will see “✓ Saved automatically”).\nYou can also change the font, colors, size and position of the title, subtitles and bubbles; each setting has a button to go back to its original value.",
  gp_12t: "Create your video!", gp_12: "Go to the “Create videos” tab. Leave 1 video and the vertical format, and press “Create videos” (highlighted).\nYou'll see the progress; it takes a few minutes. WAIT until it has fully finished before the next step. The first 3 practice videos don't use your plan's videos.",
  gp_13t: "Find your video", gp_13: "Go to the “My videos” tab. Your video is already saved inside the app: you don't have to do anything to keep it, and no copies are made.\nTo post it, press “📂 Show in folder” (highlighted): the folder where your video is opens, with the video already selected. From there you drag it or pick it when you upload it to Instagram, TikTok, WhatsApp, etc.",
  gp_14t: "You did it!", gp_14: "You made a video from start to finish. Now repeat the process with your own audio, clips and music. No audio? In “Scripts” press “+ Write a new script”, write the text and press “🔊 Generate voice”: a computer voice reads it aloud.\nIf you're on the Free plan, your video has the “Made with Vibovapp” mark; a paid plan removes it.\nYour videos always stay saved in “My videos”; “📂 Show in folder” opens its folder.\nWhenever you want, delete the “Practice” product (open it and press “Delete”). If you forget something, “? Help” has the tour by topic."
});

const G = { activa: false, i: 0, pid: null, material: null, descargado: false, min: false, tm: null, ultimo: null };
const porTexto = (q, sel) => [...document.querySelectorAll(sel || "#app h2, #app h3, #app button, #app b, #app label")].find(e => e.textContent.trim().toLowerCase().startsWith(q.toLowerCase()));
// El producto de práctica puede llevar el nombre que la persona quiera: es el que se crea durante la práctica (se recuerda su id)
const guardarPid = id => { G.pid = id; try { localStorage.setItem("vibovapp_practica_pid", id || ""); } catch (e) {} };
const practica = () => {
  if (!G.pid) { try { G.pid = localStorage.getItem("vibovapp_practica_pid") || null; } catch (e) {} }
  if (!G.pid && G.antes) { const n = S.productos.filter(p => !G.antes.has(p.id)); if (n.length) guardarPid(n[n.length - 1].id); }
  let p = G.pid ? S.productos.find(x => x.id === G.pid) : null;
  if (!p && G.pid) guardarPid(null);                                   // lo borraron: se empieza de nuevo
  return p || S.productos.filter(x => x.practica).pop() || S.productos.find(x => x.id === "practica") || S.productos.filter(x => x.id.startsWith("practica_")).pop();
};
const zonaSubida = () => document.querySelector("#contenido .soltar");
const bPracticaBase = () => `/api/productos/${(practica() || {}).id}`;

const FOLD = { es: ["Material de práctica", "1 Guion", "2 Clips", "3 Imágenes del producto", "4 Música"], en: ["Practice material", "1 Script", "2 Clips", "3 Product images", "4 Music"] };
const PASOS_G = [
  { vista: "inicio", accion: "material", obj: () => null, listo: async () => !!G.material },
  { vista: "inicio", obj: () => document.querySelector("#app .tarjeta.nuevo"), listo: async () => !!practica() },
  { vista: "guiones", obj: zonaSubida, listo: async () => (practica() || {}).guiones >= 1, carp: 1 },
  { vista: "guiones", obj: () => document.querySelector("#contenido textarea") || document.querySelector("#contenido .fila-guion button"), listo: async () => !!document.querySelector("#contenido textarea") },
  { vista: "guiones", obj: () => porTexto(t("bu_titulo")) || document.querySelector("#contenido textarea"),
    foco: () => {   // resalta lo que realmente hay que tocar: los botones «+ Persona», y después cada mensaje vacío
      const b1 = porTexto("+ " + t("bu_p1"), "#contenido button"), b2 = porTexto("+ " + t("bu_p2"), "#contenido button");
      const vacio = [...document.querySelectorAll("#contenido .tema textarea")].find(x => !x.value.trim());
      if (vacio) return { el: vacio, txt: t("gp_foco_escribe") };
      return b1 ? { el: b1, extra: b2 || undefined, txt: t("gp_aqui_5") } : null;
    },
    listo: async () => {
    try { const r = await fetch(`${bPracticaBase()}/guiones/burbujas?nombre=01.wav`).then(x => x.json()); return (Array.isArray(r) ? r : r.burbujas || []).filter(b => (b.texto || "").trim()).length >= 2; } catch (e) { return false; } } },
  { vista: "clips", obj: () => document.querySelector("#contenido .fijo-clips input"), listo: async () => { const T = await temasPractica(); return Object.keys(T).filter(n => n !== "kit").length >= 3; } },
  { vista: "clips", obj: () => document.querySelector("#contenido .etiquetas input") || document.querySelector("#contenido .carpeta-tile"),
    foco: () => {   // una palabra por carpeta (la que quiera la persona): si la carpeta abierta ya tiene la suya, te lleva a abrir otra
      temasPractica().then(T => { G.T = T; });
      const T = G.T || {}, EJ = ["casa", "ciudad", "dinero"];
      const temas = Object.keys(T).filter(n => n !== "kit");
      const tiene = n => (T[n] || []).length >= 2;          // el nombre del tema ya cuenta como palabra; una más = ya agregó la suya
      const hechos = temas.filter(tiene).length;
      if (hechos >= 3) return null;
      const abierta = document.querySelector("#contenido .carpeta-tile.abierta");
      const nom = abierta ? abierta.getAttribute("data-k") : null;
      const inp = document.querySelector("#contenido .etiquetas input");
      if (nom && nom !== "kit" && inp && !tiene(nom)) {
        const ya = Object.values(T).flat().map(x => String(x).toLowerCase());             // el ejemplo nunca es una palabra que ya esté en alguna carpeta (cada palabra solo puede estar en una)
        const w = ["casa", "ciudad", "dinero", "hogar", "precio", "oferta", "cliente", "viaje", "curso", "ayuda"].find(x => !ya.includes(x)) || "ejemplo";
        return { el: inp, txt: t("gp_f7_una", { w }) };
      }
      const otra = [...document.querySelectorAll("#contenido .carpeta-tile")].find(x => { const k = x.getAttribute("data-k"); return k && k !== "kit" && temas.includes(k) && !tiene(k); });
      return otra ? { el: otra, txt: t("gp_f7_otra") } : null;
    },
    listo: async () => { const T = await temasPractica(); return Object.keys(T).filter(n => n !== "kit" && (T[n] || []).length >= 2).length >= 3; } },
  { vista: "clips", obj: () => zonaSubida() || document.querySelector("#contenido .carpeta-tile"), carp: 2,
    foco: () => {   // 2 clips por carpeta, en las carpetas que la persona tenga: si la abierta ya tiene 2, te lleva a otra
      const num = x => { const m = (x.querySelector(".ct-sub") || {}).textContent; const n = parseInt(String(m || "").replace(/\D+/g, " ").trim(), 10); return isNaN(n) ? 0 : n; };
      const tiles = [...document.querySelectorAll("#contenido .carpeta-tile")].filter(x => x.getAttribute("data-k") && x.getAttribute("data-k") !== "kit");
      if (!tiles.length) return null;
      if (tiles.reduce((a, x) => a + num(x), 0) >= 6) return null;
      const ab = tiles.find(x => x.classList.contains("abierta")), z = zonaSubida();
      if (ab && z && num(ab) < 2) return { el: z, txt: t("gp_f8_aqui") };
      const otra = tiles.find(x => num(x) < 2);
      return otra ? { el: otra, txt: t("gp_f8_otra") } : null;
    },
    listo: async () => (practica() || {}).clips >= 6 },
  { vista: "clips", obj: () => document.querySelector("#contenido .carpeta-tile[data-k=kit]"),
    foco: () => {   // primero abrir la carpeta del producto; ya abierta, el resaltado pasa al lugar donde se sueltan las imágenes
      const tile = document.querySelector("#contenido .carpeta-tile[data-k=kit]"), z = zonaSubida();
      if (tile && tile.classList.contains("abierta") && z) return { el: z, txt: t("gp_f9_aqui") };
      return null;
    },
    listo: async () => (practica() || {}).kit >= 1, carp: 3 },
  { vista: "musica", obj: zonaSubida, listo: async () => (practica() || {}).musica >= 1, carp: 4 },
  { vista: "estilo", obj: () => { const l = porTexto("Usuario o marca", "#contenido label") || porTexto("Username or brand", "#contenido label"); return l ? l.closest(".ajuste") || l : null; },
    listo: async () => { try { const a = await fetch(`${bPracticaBase()}/ajustes`).then(x => x.json()); const u = String(a.usuario || "").trim(); return !!u && u !== "@tuusuario"; } catch (e) { return false; } } },
  { vista: "generar", obj: () => document.querySelector("#contenido button.primario.grande"),
    foco: () => {   // mientras el video se crea no se resalta «Crear videos» (si se vuelve a presionar, la app avisa que ya hay uno en marcha)
      if (!G.genT || Date.now() - G.genT > 1200) { G.genT = Date.now(); fetch("/api/generar/estado").then(x => x.json()).then(e => { G.gen = !!e.activo; }).catch(() => {}); }
      return G.gen ? { vacio: true } : null;
    },
    listo: async () => { if (!((practica() || {}).videos >= 1)) return false; try { const e = await fetch("/api/generar/estado").then(x => x.json()); return !e.activo; } catch (err) { return false; } } },
  { vista: "videos", obj: () => document.querySelector("#contenido .ver-carpeta"), listo: async () => !!G.descargado },
  { vista: "fin", obj: () => null, listo: async () => false }
];
async function temasPractica() { try { return await fetch(`${bPracticaBase()}/temas`).then(x => x.json()); } catch (e) { return {}; } }

// Durante la práctica, al hacer clic en una zona para subir archivos se abre el selector de Windows justo en la carpeta del material
// donde están los archivos del paso (si no se puede, devuelve null y se usa el selector normal). Devuelve [] si se cancela.
async function guiaElegir() {
  if (!G.activa || !S.ventanaPropia) return null;
  const p = PASOS_G[G.i]; if (!p || !p.carp) return null;
  try {
    let idx = 0;
    if (p.carp === 2) idx = [...document.querySelectorAll("#contenido .carpeta-tile")].filter(x => x.getAttribute("data-k") !== "kit" && /(\d+)/.test((x.querySelector(".ct-sub") || {}).textContent || "") && parseInt(((x.querySelector(".ct-sub") || {}).textContent.match(/\d+/) || [0])[0], 10) >= 2).length;
    const r = await fetch("/api/practica/elegir", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ sub: p.carp, idx }) }).then(x => x.json());
    if (r.fallback) return null;
    const fs = [];
    for (const ruta of r.rutas || []) { const b = await fetch("/api/practica/leer?ruta=" + encodeURIComponent(ruta)).then(x => x.ok ? x.blob() : null); if (b) fs.push(new File([b], ruta.split(/[\\/]/).pop())); }
    return fs;
  } catch (e) { return null; }
}
function irAPaso(p) {
  if (p.vista === "inicio") { if (S.pid || S.vista) { S.pid = null; S.vista = null; render(); } return; }
  const pr = practica(); if (!pr) return;
  if (p.vista === "fin") return;
  if (S.pid !== pr.id || S.pestana !== p.vista || S.vista) { S.pid = pr.id; S.vista = null; S.pestana = p.vista; render(); }
}
// FOCO: toda la pantalla se oscurece y solo queda con brillo completo el lugar donde hay que hacer clic (con una etiqueta que dice qué hacer).
// No bloquea nada: es solo visual, así que nadie se queda atrapado.
function objetivoFoco() {
  const p = PASOS_G[G.i], ultimo = G.i === PASOS_G.length - 1;
  const modal = document.getElementById("modal");
  if (modal && !modal.classList.contains("oculto")) {              // hay una ventanita abierta (por ejemplo, el nombre del producto)
    if (G.i !== 1) return null;                                    // solo el paso «crear producto» se hace dentro de una ventanita; en los demás pasos (plan, claves…) no se guía ahí
    const inp = modal.querySelector("input[type=text]");
    if (!inp) return null;
    if (!inp.value.trim()) return { el: inp, txt: t("gp_foco_escribe"), sobre: true };
    const b = modal.querySelector("button.primario");     // ya hay texto: se quedan resaltados el cuadro Y el botón, hasta que presione Crear
    return b ? { el: inp, extra: b, txt: t("gp_foco_escribe_crear"), sobre: true } : null;
  }
  if (ultimo) return null;
  if (G.ultimo && !G.min) { const b = document.querySelector("#guia .acciones .primario"); if (b) return { el: b, txt: t("gp_foco_sig") }; }
  if (p.accion === "material") { const b = document.getElementById("gp-mat"); return b && !G.material ? { el: b, txt: t("gp_foco_mat") } : null; }
  if (p.foco) { try { const f = p.foco(); if (f && f.vacio) return null; if (f && f.el && f.el.isConnected) return f; } catch (e) {} }
  let el = null; try { el = p.obj(); } catch (e) {}
  if (el && el.isConnected) return { el, txt: t(`gp_aqui_${G.i + 1}`) };
  if (!G.min) { const b = document.getElementById("gp-ir"); if (b) return { el: b, txt: t("gp_foco_ir") }; }
  return null;
}
function pintarFoco() {
  let f = document.getElementById("guia-foco"), et = document.getElementById("guia-foco-txt");
  let a = document.getElementById("guia-aro");
  const quitar = () => { if (f) f.style.display = "none"; if (a) a.style.display = "none"; if (et) et.style.display = "none"; const x2 = document.getElementById("guia-aro2"); if (x2) x2.style.display = "none"; };
  if (!G.activa) { if (f) f.remove(); if (a) a.remove(); if (et) et.remove(); const y2 = document.getElementById("guia-aro2"); if (y2) y2.remove(); clearInterval(G.tf); G.tf = null; return; }
  if (!f || !a) { if (f) f.remove(); if (a) a.remove(); if (et) et.remove(); f = h("div", { id: "guia-foco" }); a = h("div", { id: "guia-aro" }); et = h("div", { id: "guia-foco-txt" }); document.body.append(f, a, et); }
  const o = objetivoFoco();
  if (!o || !o.el || !o.el.isConnected) return quitar();
  let r = o.el.getBoundingClientRect(); const vw = innerWidth, vh = innerHeight;
  let a2 = document.getElementById("guia-aro2");
  if (o.extra && o.extra.isConnected) {                       // dos lugares resaltados a la vez (cuadro de texto + botón): el brillo cubre los dos
    const r2 = o.extra.getBoundingClientRect();
    if (!a2) { a2 = h("div", { id: "guia-aro2", class: "guia-aro" }); document.body.append(a2); }
    const m2 = 8;
    Object.assign(a2.style, { display: "block", left: (r2.left - m2) + "px", top: (r2.top - m2) + "px", width: (r2.width + 2 * m2) + "px", height: (r2.height + 2 * m2) + "px", zIndex: 62 });
    r = { left: Math.min(r.left, r2.left), top: Math.min(r.top, r2.top), right: Math.max(r.right, r2.right), bottom: Math.max(r.bottom, r2.bottom), width: Math.max(r.right, r2.right) - Math.min(r.left, r2.left), height: Math.max(r.bottom, r2.bottom) - Math.min(r.top, r2.top) };
  } else if (a2) a2.style.display = "none";
  if (r.width < 2 || r.height < 2 || r.bottom < 0 || r.top > vh || r.right < 0 || r.left > vw) return quitar();
  if (o.el !== G.elFoco) {                                         // objetivo nuevo: si queda tapado por el encabezado o fuera de pantalla, se desplaza para verlo
    G.elFoco = o.el;
    if (!o.sobre && (r.top < 90 || r.bottom > vh - 30)) o.el.scrollIntoView({ block: "center", behavior: "smooth" });
  }
  const encima = !!o.sobre || !!o.el.closest("#guia");          // si lo que se resalta está dentro del panel o de una ventanita, el foco va por encima de ellos
  const m = 8, x1 = Math.max(0, r.left - m), y1 = Math.max(0, r.top - m), x2 = Math.min(vw, r.right + m), y2 = Math.min(vh, r.bottom + m);
  Object.assign(f.style, { display: "block", left: x1 + "px", top: y1 + "px", width: (x2 - x1) + "px", height: (y2 - y1) + "px", zIndex: o.sobre ? 55 : 38 });
  a.style.cssText = f.style.cssText.replace(/box-shadow[^;]*;?/, ""); a.style.zIndex = 62;
  et.style.display = "block"; et.style.zIndex = 63;
  const abajo = y2 + 90 < vh || y1 < 90;                               // la etiqueta va debajo; arriba si no cabe
  const clave = o.txt + "|" + abajo;
  if (et.dataset.k !== clave) { et.dataset.k = clave; et.className = abajo ? "abajo" : "arriba"; et.textContent = ""; et.append(h("span", { class: "flecha" }, abajo ? "👆" : "👇"), h("span", {}, o.txt)); }
  const w = et.offsetWidth, hh = et.offsetHeight;
  et.style.left = Math.max(8, Math.min(vw - w - 8, (x1 + x2) / 2 - w / 2)) + "px";
  et.style.top = Math.max(8, Math.min(vh - hh - 8, abajo ? y2 + 10 : y1 - hh - 10)) + "px";
  if (!o.el.closest("#guia")) acomodarPanel(x1, abajo ? y1 : y1 - hh - 14, x2, abajo ? y2 + hh + 14 : y2);
}
// El panel de instrucciones se mueve (derecha/izquierda, abajo/arriba) para no tapar lo que hay que tocar ni su etiqueta
function acomodarPanel(x1, y1, x2, y2) {
  const p = document.getElementById("guia"); if (!p || G.min) return;
  const vw = innerWidth, vh = innerHeight, w = p.offsetWidth;
  const alto = comp => comp ? (p.dataset.altoc ? +p.dataset.altoc : 280) : (p.dataset.alto ? +p.dataset.alto : p.offsetHeight);
  if (!p.classList.contains("compacto")) p.dataset.alto = p.offsetHeight; else p.dataset.altoc = p.offsetHeight;
  const solape = (izq, arr, comp) => { const hh = Math.min(alto(comp), vh - 32), L = izq ? 16 : vw - 16 - w, T = arr ? 76 : vh - 16 - hh;
    const dx = Math.min(L + w, x2) - Math.max(L, x1), dy = Math.min(T + hh, y2) - Math.max(T, y1); return dx > 0 && dy > 0 ? dx * dy : 0; };
  const act = [p.classList.contains("izq"), p.classList.contains("arriba"), p.classList.contains("compacto")];
  if (!solape(...act)) return;                                       // donde está ahora no estorba: se queda
  let mejor = null;
  for (const comp of [false, true]) for (const [i, a] of [[false, false], [true, false], [false, true], [true, true]]) {
    const o = solape(i, a, comp);
    if (!o) { mejor = [i, a, comp, 0]; break; }
    if (!mejor || o < mejor[3]) mejor = [i, a, comp, o];
    if (mejor[3] === 0) break;
  }
  if (!mejor) return;
  p.classList.toggle("izq", mejor[0]); p.classList.toggle("arriba", mejor[1]); p.classList.toggle("compacto", mejor[2]);
}
function marcarObjetivo() {
  document.querySelectorAll(".guia-resalte").forEach(e => e.classList.remove("guia-resalte"));
  if (!G.activa) return;
  const pf = PASOS_G[G.i].foco;
  if (pf) { try { const f = pf(); if (f && f.vacio) return; } catch (e) {} }          // por ejemplo mientras el video se está creando: no se resalta nada
  const o = PASOS_G[G.i].obj();
  if (o) { o.classList.add("guia-resalte"); if (G.scrollPara !== G.i) { G.scrollPara = G.i; o.scrollIntoView({ block: "center", behavior: "smooth" }); } }
}
function pintarGuia() {
  let panel = document.getElementById("guia");
  if (G.activa && !G.tf) G.tf = setInterval(pintarFoco, 250);
  setTimeout(pintarFoco, 30);
  if (!G.activa) { if (panel) panel.remove(); document.querySelectorAll(".guia-resalte").forEach(e => e.classList.remove("guia-resalte")); return; }
  if (!panel) { panel = h("div", { id: "guia" }); document.body.append(panel); }
  panel.innerHTML = "";
  const p = PASOS_G[G.i], n = PASOS_G.length, ultimo = G.i === n - 1, ok = !!G.ultimo;
  panel.className = G.min ? "min" : "";
  if (G.min) { panel.append(h("button", { class: "primario", onclick: () => { G.min = false; pintarGuia(); } }, "🎓 " + t("gp_max") + ` · ${G.i + 1}/${n}`)); return; }
  poner(panel,
    h("div", { class: "fila", style: "gap:6px" }, h("span", { class: "insignia" }, "🎓 " + t("gp_paso", { a: G.i + 1, b: n })), h("div", { class: "espacio" }),
      h("button", { class: "link", title: t("gp_min"), onclick: () => { G.min = true; pintarGuia(); } }, "—"),
      h("button", { class: "link", onclick: async () => { if (await confirmar(t("gp_conf_salir"), t("gp_salir"))) { G.activa = false; clearInterval(G.tm); pintarGuia(); } } }, t("gp_salir") + " ✕")),
    h("h3", { style: "margin:8px 0 6px" }, t(`gp_${G.i + 1}t`)),
    t(`gp_${G.i + 1}`).split("\n").map(l => h("p", { style: "margin:0 0 6px;line-height:1.45" }, l)),
    p.accion === "material" ? h("div", { style: "margin:8px 0" },
      h("button", { class: G.material ? "" : "primario", id: "gp-mat", onclick: async e => {
        e.target.disabled = true; e.target.textContent = t("gp_mat_creando");
        try { const r = await api("POST", "/api/practica/material"); G.material = r.ruta; } catch (x) { e.target.disabled = false; e.target.textContent = t("gp_mat_btn"); return; }
        G.ultimo = true; pintarGuia(); } }, t("gp_mat_btn")),
      G.material ? h("div", { class: "gp-ruta" }, h("div", {}, t("gp_mat_ok")), h("b", {}, G.material),
        h("div", { style: "margin-top:6px" }, h("button", { onclick: () => api("POST", "/api/practica/abrir", {}) }, t("gp_abrir1")))) : null) : null,
    p.carp ? h("div", { class: "gp-ruta" }, h("div", {}, t("gp_donde")),
      h("b", {}, [t("gp_docs"), "Vibovapp", FOLD[S.idioma === "en" ? "en" : "es"][0], FOLD[S.idioma === "en" ? "en" : "es"][p.carp]].join(" › ")),
      h("div", { style: "margin-top:6px" }, h("button", { onclick: () => api("POST", "/api/practica/abrir", { sub: p.carp }) }, t("gp_abrir")))) : null,
    !ultimo ? h("div", { class: "gp-estado " + (ok ? "ok" : "") }, ok ? t("gp_listo") : t("gp_espera")) : null,
    h("div", { class: "acciones", style: "justify-content:space-between;margin-top:8px" },
      h("button", { disabled: G.i === 0, onclick: () => ir(G.i - 1) }, t("gp_ant")),
      h("div", { class: "fila", style: "gap:6px" },
        h("button", { id: "gp-ir", onclick: () => { irAPaso(p); setTimeout(marcarObjetivo, 400); } }, t("gp_ir")),
        ultimo ? h("button", { class: "primario", onclick: () => { G.activa = false; clearInterval(G.tm); pintarGuia(); } }, t("gp_terminar"))
          : h("button", { class: ok ? "primario" : "", onclick: () => ir(G.i + 1) }, ok ? t("gp_sig") : t("gp_saltar")))),
    ultimo ? h("button", { class: "link", style: "margin-top:6px", onclick: () => { G.activa = false; clearInterval(G.tm); pintarGuia(); tutorial(); } }, t("gp_ver_temas")) : null,
    ultimo && practica() ? h("div", { style: "margin-top:8px" }, h("div", { class: "chico suave" }, t("gp_no_cuenta")),
      h("button", { class: "chico peligro", style: "margin-top:4px", onclick: borrarPractica }, "🗑 " + t("gp_borrar_prac"))) : null);
}
function ir(i) {
  G.i = Math.max(0, Math.min(PASOS_G.length - 1, i)); G.ultimo = null; G.scrollPara = null;
  irAPaso(PASOS_G[G.i]); pintarGuia(); setTimeout(marcarObjetivo, 500); revisarGuia();
  if (G.i === PASOS_G.length - 1) {                                  // llegó al final: el producto de práctica queda bloqueado para crear más videos
    const pr = practica();
    if (pr && pr.practica) fetch(`/api/productos/${pr.id}/practica/terminar`, { method: "POST" }).then(() => { try { refrescarProductos(); } catch (e) {} }).catch(() => {});
  }
}
let revisando = false;
async function revisarGuia() {
  if (!G.activa || revisando) return;
  revisando = true;
  try {
    await refrescarProductos();
    const i = G.i, ok = await PASOS_G[i].listo();
    if (i === G.i && ok !== !!G.ultimo) { G.ultimo = ok; pintarGuia(); }
    marcarObjetivo();
  } catch (e) {} finally { revisando = false; }
}
// Borra el producto de práctica (no cuenta en el plan, pero así queda limpio para repetirla)
async function borrarPractica() {
  const p = practica(); if (!p) return;
  if (!await confirmar(t("gp_conf_borrar_prac"), t("borrar"))) return;
  try { await api("DELETE", `/api/productos/${p.id}`); } catch (e) { return; }
  guardarPid(null); G.activa = false; clearInterval(G.tm);
  if (S.pid === p.id) { S.pid = null; S.vista = null; }
  await refrescarProductos(); render(); toast(t("gp_borrada"));
}
async function iniciarPractica() {
  if (typeof cerrarModal === "function") cerrarModal();
  G.activa = true; G.min = false; G.descargado = false; G.ultimo = null; G.scrollPara = null;
  // si ya hay producto de práctica, se arranca en el primer paso que falte
  await refrescarProductos();
  G.antes = new Set(S.productos.map(p => p.id));                       // para reconocer el producto que se cree en la práctica
  let i = 0;
  if (practica()) { G.material = G.material || "Documentos\\Vibovapp\\Material de práctica"; i = 1; for (; i < PASOS_G.length - 1; i++) { if (!await PASOS_G[i].listo()) break; }
    if (i >= PASOS_G.length - 1 && practica().practica) {            // la práctica anterior ya estaba completa: se empieza una nueva desde cero
      try { await api("DELETE", `/api/productos/${practica().id}`); } catch (e) {}
      guardarPid(null); await refrescarProductos(); G.antes = new Set(S.productos.map(p => p.id)); i = 0; S.pid = null; S.vista = null; render();
    } }
  G.i = i; clearInterval(G.tm); G.tm = setInterval(revisarGuia, 1500);
  ir(i);
}

// Esc: salir de la práctica guiada sin tener que terminarla (si hay una ventanita abierta, Esc solo cierra la ventanita)
document.addEventListener("keydown", e => {
  if (e.key !== "Escape") return;
  const m = document.getElementById("modal");
  G.escConModal = !!(m && !m.classList.contains("oculto")) || !!document.querySelector(".visor-video, .menu-ctx");
}, true);
document.addEventListener("keydown", e => {
  if (e.key !== "Escape" || !G.activa || G.escConModal) return;
  G.activa = false; clearInterval(G.tm); pintarGuia();
  try { toast(t("gp_salio")); } catch (x) {}
});
