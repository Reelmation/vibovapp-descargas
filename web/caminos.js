// CAMINOS: la persona elige qué quiere hacer y la app le muestra solo lo que necesita.
// Cada tema de ayuda dice primero «¿Para qué sirve?» y luego «¿Cómo se hace?».
const CAMINOS = [
  { id: "guion", ico: "📝", pest: ["guiones", "clips", "musica", "estilo", "generar", "videos"], lec: ["subir", "guion", "palabras", "musica", "estilo", "generar", "guardados"] },
  { id: "presentador", ico: "🎤", pest: ["guiones", "clips", "musica", "estilo", "generar", "videos"], lec: ["subir", "presentador", "marcas", "palabras", "estilo", "generar", "guardados"] },
  { id: "musica", ico: "🎵", pest: ["escenas", "clips", "musica", "estilo", "generar", "videos"], lec: ["subir", "palabras", "musica", "escenas", "estilo", "generar", "guardados"] },
  { id: "todo", ico: "🧰", pest: null, lec: ["subir", "guion", "palabras", "presentador", "marcas", "musica", "sonidos", "capas", "estilo", "generar", "guardados"] }
];
const LEC_DE_PEST = { escenas: ["escenas"], guiones: ["guion", "marcas"], clips: ["palabras", "presentador"], musica: ["musica", "sonidos"], capas: ["capas"], estilo: ["estilo"], generar: ["generar"], videos: ["guardados"], papelera: ["guardados"] };

Object.assign(TEXTOS.es, {
  cm_titulo: "¿Qué quieres hacer?", cm_sub: "Elige una opción y te mostramos solo lo que necesitas. Puedes cambiarla cuando quieras.",
  cm_guion: "Video con guion", cm_guion_d: "Un texto o una voz, con subtítulos y videos de apoyo que aparecen solos.",
  cm_presentador: "Video con persona hablando", cm_presentador_d: "Presentador, podcast o blogger: alguien habla en cámara y la app pone subtítulos, textos e imágenes.", cm_hablando_para: "Aquí van los videos donde alguien habla (tú, tu equipo o tus clientes). La app los escucha, quita los silencios, pone los subtítulos y los combina con tu guion y tus videos de apoyo.",
  cm_musica: "Video con música", cm_musica_d: "Sin que nadie hable: clips y textos al ritmo de una canción.",
  cm_todo: "Quiero verlo todo", cm_todo_d: "Todas las opciones a la vista.",
  cm_actual: "Estás en: {c}", cm_cambiar: "Cambiar", cm_mas: "＋ Ver todas las herramientas", cm_menos: "－ Ver solo lo de mi tipo de video", cm_mas_ayuda: "Ahora ves solo las pestañas que necesitas para tu tipo de video. Este botón muestra todas las demás herramientas de la app.", cm_menos_ayuda: "Ahora ves todas las pestañas. Este botón deja solo las que necesitas para tu tipo de video.",
  cm_ayuda_btn: "❓ ¿Para qué sirve esto?", cm_ayuda_t: "Esta pantalla", cm_recorrido: "Mi recorrido", cm_recorrido_ayuda: "Los pasos de «{c}», uno por uno.",
  cm_para: "💡 ¿Para qué sirve?", cm_como: "🛠 ¿Cómo se hace?", cm_llevame: "Llévame ahí", cm_sig: "Siguiente →", cm_ant: "← Anterior", cm_fin: "Terminar", cm_paso: "Paso {a} de {b}",
  cm_otras: "Otras lecciones", cm_guiame: "Guíame paso a paso", cm_saltar: "Saltar esta lección", cm_sig_lec: "Siguiente lección →", cm_salir: "Salir", cm_abre_proy: "Abre un proyecto para que te guíe.", cm_elegir: "Elegir qué quiero hacer", cm_pronto: "Las escenas para este tipo de video llegan pronto; por ahora usa tus clips y tu música."
});
Object.assign(TEXTOS.en, {
  cm_titulo: "What do you want to do?", cm_sub: "Pick one and we'll show only what you need. You can change it anytime.",
  cm_guion: "Video with a script", cm_guion_d: "A text or a voice, with subtitles and support videos that appear on their own.",
  cm_presentador: "Video with a person talking", cm_presentador_d: "Presenter, podcast or vlogger: someone talks to camera and the app adds subtitles, texts and images.", cm_hablando_para: "Videos where someone talks go here (you, your team or your clients). The app listens, cuts the silences, adds subtitles and combines them with your script and support videos.",
  cm_musica: "Video with music", cm_musica_d: "Nobody talks: clips and texts to the beat of a song.",
  cm_todo: "Show me everything", cm_todo_d: "All options in view.",
  cm_actual: "You're on: {c}", cm_cambiar: "Change", cm_mas: "＋ Show all tools", cm_menos: "－ Show only what my video type needs", cm_mas_ayuda: "You now see only the tabs you need for your video type. This button shows all the other tools in the app.", cm_menos_ayuda: "You now see every tab. This button keeps only the ones you need for your video type.",
  cm_ayuda_btn: "❓ What is this for?", cm_ayuda_t: "This screen", cm_recorrido: "My tour", cm_recorrido_ayuda: "The steps of “{c}”, one by one.",
  cm_para: "💡 What is it for?", cm_como: "🛠 How is it done?", cm_llevame: "Take me there", cm_sig: "Next →", cm_ant: "← Back", cm_fin: "Finish", cm_paso: "Step {a} of {b}",
  cm_otras: "Other lessons", cm_guiame: "Guide me step by step", cm_saltar: "Skip this lesson", cm_sig_lec: "Next lesson →", cm_salir: "Exit", cm_abre_proy: "Open a project so I can guide you.", cm_elegir: "Choose what I want to do", cm_pronto: "Scenes for this kind of video are coming soon; for now use your clips and your music."
});

// Lecciones (por ahora en español). para = qué hace la app con esto (por qué importa); pasos = acciones concretas, cada una lleva a su pantalla y resalta dónde.
const _q = (sel, n) => () => { const l = [...document.querySelectorAll(sel)]; return l[n || 0] || null; };
const _tab = g => () => document.querySelector(`.pestanas:not(.sub) button[data-g="${g}"]`);
const _sub = p => () => document.querySelector(`.pestanas.sub button[data-p="${p}"]`);
const _txt = (re, sel) => () => [...document.querySelectorAll(sel || "#contenido button, #contenido summary, #contenido h3")].find(e => re.test(e.textContent)) || null;
const _o = (...fs) => () => { for (const f of fs) { const e = f(); if (e) return e; } return null; };
const LECCIONES = {
  subir: { t: "Subir archivos",
    para: "Todo lo que subes es la materia prima: la app arma cada video combinando TUS archivos. Mientras más variados sean, más diferentes salen los videos.",
    pasos: [
      { x: "Busca el cuadro con borde punteado de la pantalla en la que estés: ahí se sueltan los archivos.", pest: null, f: _q("#contenido .soltar"), e: "Aquí se suben" },
      { x: "Arrastra tus archivos ahí, o presiona el cuadro para elegirlos. Para escoger varios, mantén presionada la tecla Ctrl.", pest: null, f: _q("#contenido .soltar"), e: "Suelta aquí tus archivos" },
      { x: "No tienes que guardarlos en otro lado: se quedan dentro de la app y los puedes quitar con la × cuando quieras.", pest: null, f: _q("#contenido .soltar"), e: "Se guardan solos" }] },
  guion: { t: "El guion", pest: "guiones",
    para: "El guion le dice a la app QUÉ se dice y CUÁNDO. De él salen la voz, los subtítulos y el momento exacto en que aparece cada video de apoyo, texto o imagen.",
    pasos: [
      { x: "Entra a «Guion».", pest: "guiones", f: _tab("guiones"), e: "Entra aquí" },
      { x: "Si ya tienes el audio, arrástralo aquí junto con su texto (un archivo .txt con el mismo nombre).", pest: "guiones", f: _q("#contenido .soltar"), e: "Sube tu audio y su texto" },
      { x: "Si no tienes audio, presiona «＋ Escribir un guion nuevo», escribe el texto y genera la voz: la computadora lo narra.", pest: "guiones", f: _q("#contenido .btn-nuevo-guion"), e: "O escribe uno nuevo" },
      { x: "La primera línea del guion es el título: sale arriba al inicio del video y no se dice.", pest: "guiones", f: _q("#contenido .btn-nuevo-guion"), e: "El título es la 1.ª línea" }] },
  escenas: { t: "Escenas (video sin voz)", pest: "escenas",
    para: "Cuando nadie habla, las escenas hacen de guion: tú dices qué carpeta se ve, cuánto dura y qué texto lleva cada escena, y la app arma el video con tu música. Como cada escena toma un clip distinto de la carpeta, todos los videos salen diferentes. Las piezas guardadas (intros, cierres…) se reutilizan en todos tus proyectos.",
    pasos: [
      { x: "Entra a «Escenas».", pest: "escenas", f: _tab("guiones"), e: "Entra aquí" },
      { x: "Crea una plantilla (puedes empezar con un ejemplo).", pest: "escenas", f: _o(_q("#contenido .esc-ejemplo"), _q("#contenido .esc-sel")), e: "Crea tu plantilla" },
      { x: "En cada escena elige qué se ve (una carpeta de tus clips o un archivo) y cuántos segundos dura.", pest: "escenas", f: _q("#contenido .esc-fuente"), e: "Elige qué se ve" },
      { x: "Si quieres, escribe un texto para esa escena (precio, nombre, oferta…).", pest: "escenas", f: _q("#contenido .esc-escena input[type=text]", 1), e: "Texto opcional" },
      { x: "Si una escena te gusta (por ejemplo una intro con descuento), presiona «Guardar como pieza»: la podrás usar en otras plantillas y en otros proyectos.", pest: "escenas", f: _q("#contenido .esc-guardar-pieza"), e: "Guárdala como pieza" },
      { x: "Agrega las escenas que necesites (o una pieza guardada) y, en «Crear videos», elige tu plantilla.", pest: "escenas", f: _q("#contenido .esc-agregar"), e: "Agrega escenas" }] },
  palabras: { t: "Palabras clave y videos de apoyo (dentro de Multimedia)", pest: "clips",
    para: "La app lee tu guion y, cuando encuentra una palabra clave, pone en pantalla un video de esa carpeta. Así se crean las escenas sin que tú las armes, y cada video sale distinto porque elige otro clip de la carpeta.",
    pasos: [
      { x: "Entra a «Multimedia».", pest: "clips", f: _tab("musica"), e: "Entra aquí" },
      { x: "Abre «Clips y palabras clave».", pest: "clips", f: _sub("clips"), e: "Y aquí" },
      { x: "Escribe el tema (por ejemplo «casas») y presiona «Nuevo tema». El nombre de la carpeta ya es una palabra clave.", pest: "clips", f: _q("#contenido input", 0), e: "Escribe el tema aquí" },
      { x: "Abre la carpeta y agrega más palabras clave en su cuadro de palabras (escribe una y presiona Enter).", pest: "clips", f: _q("#contenido input", 0), e: "Después abre la carpeta" },
      { x: "Arrastra a la carpeta los videos de ese tema. Cuando el guion diga esas palabras, saldrá uno de ellos.", pest: "clips", f: _q("#contenido input", 0), e: "Y sube sus videos" }] },
  presentador: { t: "Mis videos en cámara", pest: "clips",
    para: "Son los videos de la persona que habla. La app los escucha, quita los silencios, pone los subtítulos y los combina con tu guion y tus videos de apoyo para crear las escenas. Grabas una vez; la app arma muchas versiones.",
    pasos: [
      { x: "Entra a «Multimedia».", pest: "clips", f: _tab("musica"), e: "Entra aquí" },
      { x: "Abre la sección «Mis videos en cámara» (arriba de tus carpetas).", pest: "clips", f: _txt(/en cámara|on-camera/i, "#contenido summary"), e: "Ábrela aquí" },
      { x: "Sube tu video con el botón «Subir videos…» del presentador (si no hay ninguno, primero agrégalo con «+ Agregar presentador»).", pest: "clips", f: _txt(/subir|upload|agregar|add/i, "#contenido .seccion-hablando button"), e: "Sube tu video" },
      { x: "Presiona «Sacar el texto»: la app escucha el video y escribe lo que se dijo.", pest: "clips", f: _o(_txt(/sacar el texto|get the text/i), _txt(/subir|upload|agregar|add/i, "#contenido .seccion-hablando button")), e: "Saca el texto" },
      { x: "Después, en «Crear videos», elige el guion y la app arma los videos.", pest: "generar", f: _tab("generar"), e: "Luego, aquí" }] },
  marcas: { t: "Añadir textos, imágenes y sonidos a una palabra", pest: "guiones",
    para: "Las marcas le dicen a la app: «justo en esta palabra, pon esto». Así personalizas cada escena (un texto, una imagen, un sonido) sin editar video.",
    pasos: [
      { x: "Abre el guion o el texto del video en el que quieras trabajar.", pest: "guiones", f: _o(_q("#contenido textarea"), _txt(/▸/)), e: "Abre un guion" },
      { x: "Haz clic en una palabra, o arrastra sobre varias para seleccionar una frase.", pest: "guiones", f: _o(_q("#contenido textarea"), _txt(/▸/)), e: "Selecciona una frase" },
      { x: "Aparece un cuadrito: elige mostrar un texto, ocultar la frase de los subtítulos, un sonido «pop», «＋ Texto que nadie dice», «＋ Imagen» (puedes juntar hasta 4 en un collage), «＋ Figura» (flecha, círculo, subrayado o destello) o «＋ Burbuja de chat».", pest: "guiones", f: _o(_q("#contenido .marcas-panel"), _q("#contenido textarea"), _txt(/▸/)), e: "Elige qué añadir" }] },
  musica: { t: "Música de fondo", pest: "musica",
    para: "La app elige una de estas canciones para cada video y la baja de volumen cuando alguien habla, para que se entienda lo que dices. Mientras más canciones, más variedad.",
    pasos: [
      { x: "Entra a «Multimedia».", pest: "musica", f: _tab("musica"), e: "Entra aquí" },
      { x: "Abre «Música».", pest: "musica", f: _sub("musica"), e: "Y aquí" },
      { x: "Arrastra tus canciones al primer cuadro (mp3, wav, m4a…).", pest: "musica", f: _q("#contenido .soltar", 0), e: "Sube tu música" }] },
  sonidos: { t: "Sonidos de efecto", pest: "musica",
    para: "La app los usa en los momentos que tú marcas (un texto que aparece, un cambio) para darle ritmo al video. Sin ellos, el video suena plano.",
    pasos: [
      { x: "Entra a «Multimedia» y luego a «Música».", pest: "musica", f: _sub("musica"), e: "Entra aquí" },
      { x: "Baja hasta «Sonidos de efectos» y arrastra ahí los que quieras usar.", pest: "musica", f: _q("#contenido .soltar", 1), e: "Sube tus sonidos" }] },
  capas: { t: "Logo y elementos fijos", pest: "capas",
    para: "Se pegan encima de cada video que crea la app, siempre en el mismo lugar, para que todos lleven tu marca.",
    pasos: [
      { x: "Entra a «Estilo y diseño» y luego a «Capas».", pest: "capas", f: _sub("capas"), e: "Entra aquí" },
      { x: "Arrastra tu logo (mejor PNG con fondo transparente).", pest: "capas", f: _q("#contenido .soltar"), e: "Sube tu logo" }] },
  estilo: { t: "Estilo y diseño", pest: "estilo",
    para: "Es la plantilla visual: la app la aplica a todos los videos para que se vean iguales y como tuyos. La configuras una vez.",
    pasos: [
      { x: "Entra a «Estilo y diseño».", pest: "estilo", f: _tab("estilo"), e: "Entra aquí" },
      { x: "Elige un estilo listo para empezar, o abre una sección (Título, Subtítulos…) y cambia lo que quieras.", pest: "estilo", f: _q("#contenido summary", 0), e: "Cambia lo que quieras" },
      { x: "Mira la vista previa de la derecha: los cambios se guardan solos.", pest: "estilo", f: _txt(/preview|vista previa/i, "#contenido h3, #contenido h4, #contenido summary, #contenido b"), e: "Así se verá" },
      { x: "¿Quieres el look de los reels de noticias? Arriba, elige el estilo listo «Noticia»: palabras clave grandes y rojas, la frase en una caja y una barra de avance.", pest: "estilo", f: _q("#contenido select, #contenido .estilos-listos button, #contenido details summary", 0), e: "Elige «Noticia»" },
      { x: "¿Para qué? Para dejar cada texto justo donde quieres sin buscar números. Arrastra un texto para moverlo, usa el punto de la esquina para cambiar su tamaño y los de los lados para su ancho. Con Shift + clic eliges varios y se mueven juntos. Marca «Mostrar ejemplo de textos e imágenes del guion» para acomodar también esos.", pest: "estilo", f: _q("#contenido .previa-lienzo"), e: "Arrastra aquí" }] },
  generar: { t: "Crear videos", pest: "generar",
    para: "Aquí la app junta todo (guion, presentador, videos de apoyo, música y estilo) y crea los videos, cambiando las combinaciones en cada uno. Tu plan define cuántos archivos puedes crear por tanda.",
    pasos: [
      { x: "Entra a «Crear videos».", pest: "generar", f: _tab("generar"), e: "Entra aquí" },
      { x: "Marca los formatos que quieras (vertical, cuadrado…).", pest: "generar", f: _q("#contenido input[type=checkbox]"), e: "Elige formatos" },
      { x: "Escribe cuántos videos quieres y presiona «Crear videos». El avance se ve a la derecha.", pest: "generar", f: _q("#contenido button.primario"), e: "Presiona aquí" }] },
  guardados: { t: "Dónde quedan mis videos", pest: "videos",
    para: "Es donde la app deja los videos ya terminados, listos para publicar. No tienes que buscarlos en tu computadora.",
    pasos: [
      { x: "Entra a «Carpeta».", pest: "videos", f: _tab("videos"), e: "Entra aquí" },
      { x: "Mira, renombra o borra tus videos. Con «📂 Abrir carpeta» se abre la carpeta de tu computadora para arrastrarlos a Instagram, TikTok, WhatsApp…", pest: "videos", f: _q("#contenido button", 0), e: "Abre la carpeta" }] }
};

const cmCamino = () => CAMINOS.find(c => c.id === (S.camino === "podcast" ? "presentador" : S.camino)) || null;
const cmNombre = c => t("cm_" + c.id);
const cmLeccion = id => LECCIONES[id];

// pestañas que se ven según el camino (null = todas)
function pestanasVisibles() {
  const c = cmCamino();
  if (!c || !c.pest || S.verTodo) return null;
  if (typeof G !== "undefined" && G.activa) return null;   // la práctica guiada necesita todo a la vista
  return new Set([...c.pest, S.pestana, "papelera"]);
}
function gruposVisibles() {
  const v = pestanasVisibles();
  if (!v) return GRUPOS;
  return GRUPOS.map(([k, ps, tt]) => { const f = ps.filter(p => v.has(p)); return [k, f, f.length === 1 && f[0] === "escenas" ? "t_escenas" : tt]; }).filter(g => g[1].length);
}
// botón «Más / Menos opciones» al final de las pestañas (solo si hay un camino con filtro)
function cmBotonMas() {
  const c = cmCamino();
  if (!c || !c.pest) return null;
  return h("button", { class: "cm-mas", title: S.verTodo ? t("cm_menos_ayuda") : t("cm_mas_ayuda"), onclick: () => { S.verTodo = !S.verTodo; producto(); } }, S.verTodo ? t("cm_menos") : t("cm_mas"));
}
// franja con el camino actual y los botones de ayuda
function cmBarra() {
  const c = cmCamino();
  return h("div", { class: "cm-barra" },
    c ? h("span", { class: "suave chico" }, c.ico + " " + t("cm_actual", { c: cmNombre(c) })) : null,
    h("button", { class: "link chico", onclick: elegirCamino }, c ? t("cm_cambiar") : t("cm_elegir")),
    h("div", { class: "espacio" }),
    c ? h("button", { class: "chico", onclick: () => recorrido(0) }, "🧭 " + t("cm_recorrido")) : null,
    h("button", { class: "chico", onclick: ayudaPantalla }, t("cm_ayuda_btn")));
}

async function elegirCamino() {
  const pone = async id => {
    S.camino = id; S.verTodo = false;
    try { await api("POST", "/api/config", { camino: id }); } catch (e) {}
    cerrarModal(); render();
  };
  modal([h("h2", {}, t("cm_titulo")), h("p", { class: "suave" }, t("cm_sub")),
    h("div", { class: "cm-lista" }, CAMINOS.map(c => h("button", { class: "cm-op" + (S.camino === c.id ? " on" : ""), onclick: () => pone(c.id) },
      h("span", { class: "cm-ico" }, c.ico), h("span", {}, h("b", {}, cmNombre(c)), h("br", {}), h("span", { class: "suave chico" }, t("cm_" + c.id + "_d"))))))], {});
}

// al empezar un proyecto nuevo: primero se pregunta qué quiere hacer; devuelve false si se cancela
function elegirCaminoNuevo() {
  return new Promise(res => {
    const pone = async id => {
      S.camino0 = id; S.verTodo = false;      // se guarda para el proyecto nuevo, no cambia el del proyecto actual
      try { await api("POST", "/api/config", { camino: id }); } catch (e) {}
      cerrarModal(); res(true);
    };
    modal([h("h2", {}, t("cm_titulo")), h("p", { class: "suave" }, t("cm_sub")),
      h("div", { class: "cm-lista" }, CAMINOS.map(c => h("button", { class: "cm-op", onclick: () => pone(c.id) },
        h("span", { class: "cm-ico" }, c.ico), h("span", {}, h("b", {}, cmNombre(c)), h("br", {}), h("span", { class: "suave chico" }, t("cm_" + c.id + "_d")))))),
      h("div", { class: "acciones" }, h("button", { onclick: () => { cerrarModal(); res(false); } }, t("cancelar")))], {});
  });
}

// una lección: primero PARA QUÉ (qué hace la app con esto), luego CÓMO (acciones concretas)
function bloqueLeccion(id) {
  const L = cmLeccion(id);
  return h("div", { class: "cm-lec" }, h("h3", { style: "margin:0 0 8px" }, L.t),
    h("div", { class: "cm-para" }, h("b", {}, t("cm_para")), h("p", { style: "margin:4px 0 0" }, L.para)),
    h("div", { class: "cm-como" }, h("b", {}, t("cm_como")), h("ol", { style: "margin:4px 0 0 18px;padding:0" }, L.pasos.map(p => h("li", { style: "margin:3px 0" }, p.x)))),
    h("button", { class: "primario", style: "margin-top:8px", onclick: () => guiar(id, 0) }, t("cm_guiame")));
}
function ayudaPantalla() {
  const ids = LEC_DE_PEST[S.pestana] || [];
  const otras = ["subir"].filter(x => !ids.includes(x));
  modal([h("div", { class: "fila" }, h("h2", { style: "margin:0" }, t("cm_ayuda_t")), h("div", { class: "espacio" }), h("button", { class: "link", onclick: cerrarModal }, t("cerrar") + " ✕")),
    ...ids.map(bloqueLeccion),
    otras.length ? h("h3", { class: "suave", style: "margin:16px 0 6px" }, t("cm_otras")) : null,
    ...otras.map(id => h("details", {}, h("summary", { style: "cursor:pointer" }, cmLeccion(id).t), bloqueLeccion(id)))], { sinX: true });
}
// recorrido: cada lección abre con su «para qué»; luego «Guíame» lleva paso a paso, a la pantalla y al lugar exacto
function recorrido(i) {
  const c = cmCamino(); if (!c) return elegirCamino();
  const ids = c.lec, id = ids[i], L = cmLeccion(id);
  salirGuia();
  modal([h("div", { class: "fila" }, h("span", { class: "insignia" }, t("cm_paso", { a: i + 1, b: ids.length })), h("div", { class: "espacio" }), h("button", { class: "link", onclick: cerrarModal }, t("cerrar") + " ✕")),
    h("p", { class: "suave chico", style: "margin:6px 0" }, c.ico + " " + cmNombre(c)),
    h("h3", { style: "margin:0 0 8px" }, L.t),
    h("div", { class: "cm-para" }, h("b", {}, t("cm_para")), h("p", { style: "margin:4px 0 0" }, L.para)),
    h("div", { class: "acciones", style: "margin-top:14px" },
      i > 0 ? h("button", { onclick: () => recorrido(i - 1) }, t("cm_ant")) : null,
      i < ids.length - 1 ? h("button", { onclick: () => recorrido(i + 1) }, t("cm_saltar")) : null,
      h("button", { class: "primario", onclick: () => guiar(id, 0, i) }, t("cm_guiame")))], { sinX: true });
}
// guía paso a paso: tarjeta flotante + aro amarillo en el lugar exacto (no bloquea la pantalla)
const CG = { id: null, k: 0, i: null, tm: null, el: null };
function salirGuia() {
  clearInterval(CG.tm); CG.tm = null; CG.id = null; CG.el = null;
  ["cm-guia", "cm-aro", "cm-etq"].forEach(x => { const e = document.getElementById(x); if (e) e.remove(); });
}
async function guiar(id, k, i) {
  cerrarModal();
  const L = cmLeccion(id), P = L.pasos[k];
  if (!S.pid) { toast(t("cm_abre_proy")); return; }
  CG.id = id; CG.k = k; CG.i = i === undefined ? null : i; CG.el = null;
  if (P.pest && P.pest !== S.pestana) { S.pestana = P.pest; guardarSesion(); producto(); barra(); }
  const c = cmCamino(), ids = c ? c.lec : [], haySig = CG.i !== null && CG.i < ids.length - 1;
  let tar = document.getElementById("cm-guia"); if (tar) tar.remove();
  tar = h("div", { id: "cm-guia" },
    h("div", { class: "fila" }, h("span", { class: "insignia" }, `${L.t} · ${t("cm_paso", { a: k + 1, b: L.pasos.length })}`), h("div", { class: "espacio" }), h("button", { class: "link chico", onclick: salirGuia }, t("cm_salir") + " ✕")),
    h("details", { class: "chico", open: k === 0 }, h("summary", { style: "cursor:pointer" }, t("cm_para")), h("p", { style: "margin:4px 0 0" }, L.para)),
    h("p", { style: "margin:8px 0;font-weight:600" }, P.x),
    h("div", { class: "acciones", style: "margin-top:8px;display:flex;gap:8px;justify-content:flex-end" },
      k > 0 ? h("button", { class: "chico", onclick: () => guiar(id, k - 1, CG.i === null ? undefined : CG.i) }, t("cm_ant")) : null,
      k < L.pasos.length - 1 ? h("button", { class: "primario chico", onclick: () => guiar(id, k + 1, CG.i === null ? undefined : CG.i) }, t("cm_sig"))
        : haySig ? h("button", { class: "primario chico", onclick: () => recorrido(CG.i + 1) }, t("cm_sig_lec"))
        : h("button", { class: "primario chico", onclick: salirGuia }, t("cm_fin"))));
  document.body.append(tar);
  clearInterval(CG.tm); CG.tm = setInterval(pintarAro, 300); setTimeout(pintarAro, 600);
}
function pintarAro() {
  if (!CG.id) return;
  const P = cmLeccion(CG.id).pasos[CG.k];
  let a = document.getElementById("cm-aro"), e = document.getElementById("cm-etq");
  const ocultar = () => { if (a) a.style.display = "none"; if (e) e.style.display = "none"; };
  let el = null; try { el = P.f ? P.f() : null; } catch (x) {}
  if (!el || !el.isConnected) return ocultar();
  const r = el.getBoundingClientRect(), vw = innerWidth, vh = innerHeight;
  if (r.width < 2 || r.height < 2) return ocultar();
  if (el !== CG.el) { CG.el = el; if (r.top < 90 || r.bottom > vh - 30) el.scrollIntoView({ block: "center", behavior: "smooth" }); }
  if (!a) { a = h("div", { id: "cm-aro" }); e = h("div", { id: "cm-etq" }); document.body.append(a, e); }
  const m = 8, x1 = Math.max(0, r.left - m), y1 = Math.max(0, r.top - m), x2 = Math.min(vw, r.right + m), y2 = Math.min(vh, r.bottom + m);
  Object.assign(a.style, { display: "block", left: x1 + "px", top: y1 + "px", width: (x2 - x1) + "px", height: (y2 - y1) + "px" });
  const abajo = y2 + 70 < vh || y1 < 90;
  if (e.dataset.k !== P.e + abajo) { e.dataset.k = P.e + abajo; e.textContent = ""; e.append(h("span", { class: "flecha" }, abajo ? "👆" : "👇"), h("span", {}, P.e)); }
  e.style.display = "flex";
  const w = e.offsetWidth, hh = e.offsetHeight;
  e.style.left = Math.max(8, Math.min(vw - w - 8, (x1 + x2) / 2 - w / 2)) + "px";
  e.style.top = Math.max(8, Math.min(vh - hh - 8, abajo ? y2 + 10 : y1 - hh - 10)) + "px";
}
// al abrir un proyecto por primera vez sin camino elegido, se ofrece elegir (sin chocar con otra ventana)
function cmOfrecer() {
  if (S.camino || S.caminoPreg) return;
  const m = $("#modal"); if (m && !m.classList.contains("oculto")) return;
  if (typeof G !== "undefined" && G.activa) return;
  S.caminoPreg = true; setTimeout(elegirCamino, 250);
}

Object.assign(TEXTOS.es, { gui_ej_texto: "Hola, hoy te cuento por qué tu video necesita un buen inicio. Comenta GUIONES y te envío el enlace." });
Object.assign(TEXTOS.en, { gui_ej_texto: "Hi, today I'll tell you why your video needs a strong start. Comment SCRIPTS and I'll send you the link." });
