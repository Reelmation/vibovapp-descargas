// Videos de referencia: subes un video que te gusta y la app te dice cómo hacer algo parecido con sus herramientas.
const REF_PREG = [
  { id: "titulo", lec: "estilo", q: "¿Hay un título fijo que se queda arriba casi todo el video?", ej: "Por ejemplo: una pastilla o cuadro con una frase que no cambia." },
  { id: "subs", lec: "estilo", q: "¿Los subtítulos van apareciendo palabra por palabra o en frases cortas?", ej: "Letras grandes que cambian cada pocas palabras." },
  { id: "acento", lec: "estilo", q: "¿Alguna palabra clave se ve distinta (otra letra, otro color)?", ej: "Por ejemplo: una palabra en cursiva o en amarillo." },
  { id: "etiquetas", lec: "marcas", q: "¿Aparecen etiquetas, textos o imágenes justo cuando se dice algo?", ej: "Por ejemplo: un cuadrito con «entró» o un logo que sale un momento." },
  { id: "fondo", lec: "capas", q: "¿Hay un fondo distinto al de la persona (nubes, color, video)?", ej: "Por ejemplo: un cielo o un color detrás de todo." },
  { id: "persona", lec: "presentador", q: "¿Se ve a una persona hablando a la cámara?", ej: "Presentador, podcast o blogger." },
  { id: "clips", lec: "palabras", q: "¿Las imágenes de apoyo cambian según lo que se dice?", ej: "Cada vez que menciona algo, aparece un clip relacionado." },
  { id: "musica", lec: "musica", q: "¿Se oye música de fondo?", ej: "Una canción suave o con ritmo debajo de la voz." },
  { id: "sonidos", lec: "sonidos", q: "¿Hay sonidos de efecto (clic, aplausos, «pop»)?", ej: "Sonidos cortos cuando sale algo en pantalla." },
  { id: "tres_d", lec: null, q: "¿Salen objetos que se mueven o giran en 3D?", ej: "Cajas, pantallas o tarjetas que entran con efecto." },
];
const REF = { datos: null, resp: {} };

Object.assign(TEXTOS.es, {
  ref_btn: "Videos de referencia", ref_t: "Videos de referencia",
  ref_para: "Sube un video que te gusta y te decimos cómo hacer algo parecido con esta app: qué herramientas usar, en qué orden y qué cosas no se pueden.",
  ref_elegir: "Elegir un video de referencia", ref_subiendo: "Revisando el video…", ref_aviso: "El video solo se usa para mirarlo aquí; no sale de tu computadora.",
  ref_resumen: "Lo que vimos del video", ref_dur: "Dura {n} segundos.", ref_vert: "Es vertical (como un Reel).", ref_hor: "Es horizontal; para Reels conviene vertical.",
  ref_cortes: "Cambia de imagen unas {n} veces, más o menos cada {c} segundos.", ref_sincortes: "Casi no cambia de imagen: es una toma continua.",
  ref_voz: "Tiene sonido.", ref_novoz: "No tiene sonido.", ref_preg: "Ahora contesta mirando el video", ref_si: "Sí", ref_no: "No", ref_nose: "No sé",
  ref_plan_btn: "Ver mi plan", ref_plan_t: "Tu plan para hacer un video parecido", ref_si_hace: "Lo que sí puedes hacer con la app", ref_no_hace: "Lo que esta app no hace",
  ref_3d: "Los objetos que se mueven o giran en 3D no se crean en la app. Puedes hacerlos en otro programa (por ejemplo CapCut), guardarlos como imagen o video corto y subirlos como marca: aparecerán en el momento justo, sin el movimiento 3D si son imagen.",
  ref_pct: "Con esta app puedes lograr aproximadamente el {n}% de este video.", ref_nada: "Marca al menos una respuesta con «Sí» para armar tu plan.",
  ref_crear: "Crear mi proyecto con este plan", ref_nombre: "Nombre de tu proyecto", ref_otro: "Subir otro video", ref_ver: "Ver cómo hacerlo",
});
Object.assign(TEXTOS.en, {
  ref_btn: "Reference videos", ref_t: "Reference videos",
  ref_para: "Upload a video you like and we'll tell you how to make something similar with this app: which tools to use, in what order, and what can't be done.",
  ref_elegir: "Choose a reference video", ref_subiendo: "Checking the video…", ref_aviso: "The video is only used to look at it here; it never leaves your computer.",
  ref_resumen: "What we saw in the video", ref_dur: "It lasts {n} seconds.", ref_vert: "It's vertical (like a Reel).", ref_hor: "It's horizontal; vertical works better for Reels.",
  ref_cortes: "The picture changes about {n} times, roughly every {c} seconds.", ref_sincortes: "The picture barely changes: it's one continuous shot.",
  ref_voz: "It has sound.", ref_novoz: "It has no sound.", ref_preg: "Now answer while watching the video", ref_si: "Yes", ref_no: "No", ref_nose: "Not sure",
  ref_plan_btn: "See my plan", ref_plan_t: "Your plan to make a similar video", ref_si_hace: "What you can do with the app", ref_no_hace: "What this app doesn't do",
  ref_3d: "3D moving or spinning objects aren't created in the app. You can make them in another program (for example CapCut), save them as an image or short video and upload them as a mark: they'll appear at the right moment, without the 3D movement if they're images.",
  ref_pct: "With this app you can get about {n}% of this video.", ref_nada: "Mark at least one answer «Yes» to build your plan.",
  ref_crear: "Create my project with this plan", ref_nombre: "Your project name", ref_otro: "Upload another video", ref_ver: "See how",
});
// preguntas en inglés
const REF_EN = { titulo: "Is there a fixed title that stays on top most of the video?", subs: "Do subtitles appear word by word or in short phrases?", acento: "Does a key word look different (another font or color)?",
  etiquetas: "Do labels, texts or images appear right when something is said?", fondo: "Is there a background different from the person's (clouds, color, video)?",
  persona: "Do we see a person talking to the camera?", clips: "Do the supporting images change with what is said?", musica: "Is there background music?",
  sonidos: "Are there sound effects (click, applause, pop)?", tres_d: "Do 3D objects move or spin on screen?" };

function referencias() {
  REF.datos = null; REF.resp = {};
  const ent = h("input", { type: "file", accept: "video/*", style: "display:none", onchange: async e => {
    const f = e.target.files[0]; if (!f) return;
    cuerpo.innerHTML = ""; cuerpo.append(h("p", {}, "⏳ " + t("ref_subiendo")));
    const fd = new FormData(); fd.append("archivo", f);
    try { REF.datos = await enviarConProgreso("/api/referencia", fd, null); refPreguntas(); }
    catch (er) { referencias(); } } });
  const cuerpo = h("div", {});
  cuerpo.append(h("p", { class: "cm-para" }, h("b", {}, t("cm_para")), h("p", { style: "margin:4px 0 0" }, t("ref_para"))),
    h("button", { class: "primario", style: "width:100%;margin-top:10px", onclick: () => ent.click() }, "🎯 " + t("ref_elegir")),
    h("p", { class: "suave chico", style: "margin-top:8px" }, t("ref_aviso")), ent);
  modal([h("h2", {}, "🎯 " + t("ref_t")), cuerpo, h("div", { class: "acciones" }, h("button", { onclick: cerrarModal }, t("cerrar")))], { ancha: true });
}
function refPreguntas() {
  const d = REF.datos, en = S.idioma === "en";
  // respuestas que la app puede adelantar con lo medido
  if (!d.voz) { REF.resp.persona = REF.resp.persona || "no"; REF.resp.musica = REF.resp.musica || "nose"; }
  if (d.cortes >= 5) REF.resp.clips = REF.resp.clips || "si";
  const lineas = [t("ref_dur", { n: d.duracion }), d.vertical ? t("ref_vert") : t("ref_hor"),
    d.cortes ? t("ref_cortes", { n: d.cortes + 1, c: d.cada }) : t("ref_sincortes"), d.voz ? t("ref_voz") : t("ref_novoz")];
  const filas = REF_PREG.map(p => {
    const bs = [];
    ["si", "no", "nose"].forEach((v, k) => {
      const b = h("button", { class: "chico" + (REF.resp[p.id] === v ? " primario" : ""), onclick: () => { REF.resp[p.id] = v; bs.forEach(x => x.classList.remove("primario")); b.classList.add("primario"); } }, t(["ref_si", "ref_no", "ref_nose"][k]));
      bs.push(b); });
    return h("div", { style: "margin:10px 0;padding-bottom:8px;border-bottom:1px solid var(--borde, #3333)" },
      h("div", { style: "font-weight:600" }, en ? REF_EN[p.id] : p.q), h("div", { class: "suave chico", style: "margin:2px 0 6px" }, en ? "" : p.ej), h("div", { style: "display:flex;gap:6px" }, bs)); });
  modal([h("h2", {}, "🎯 " + t("ref_t")),
    h("div", { style: "display:flex;gap:16px;align-items:flex-start;flex-wrap:wrap" },
      h("div", { style: "flex:0 0 220px" }, h("video", { src: "/api/referencia/video", controls: true, style: "width:220px;border-radius:10px;background:#000" }),
        h("div", { class: "suave chico", style: "margin-top:8px" }, h("b", {}, t("ref_resumen")), lineas.map(l => h("div", {}, "• " + l)))),
      h("div", { style: "flex:1;min-width:260px;max-height:62vh;overflow:auto" }, h("h3", { style: "margin:0" }, t("ref_preg")), filas)),
    h("div", { class: "acciones" }, h("button", { onclick: referencias }, t("ref_otro")), h("button", { class: "primario", onclick: refPlan }, t("ref_plan_btn")))], { ancha: true });
}
function refPlan() {
  const sis = REF_PREG.filter(p => REF.resp[p.id] === "si");
  if (!sis.length) { toast(t("ref_nada"), true); return; }
  const si = sis.filter(p => p.lec), no = sis.filter(p => !p.lec);
  const lecs = []; si.forEach(p => { if (!lecs.includes(p.lec)) lecs.push(p.lec); });
  const pct = Math.round(100 * si.length / sis.length);
  const camino = REF.resp.persona === "si" ? "presentador" : (REF.resp.musica === "si" && REF.resp.persona !== "si" && !(REF.datos && REF.datos.voz && REF.resp.clips !== "si") ? "musica" : "guion");
  modal([h("h2", {}, "🎯 " + t("ref_plan_t")), h("p", { style: "font-weight:600" }, t("ref_pct", { n: pct })),
    h("div", { style: "max-height:56vh;overflow:auto" },
      h("h3", {}, "✅ " + t("ref_si_hace")),
      ...lecs.map(id => h("details", { style: "margin:6px 0" }, h("summary", { style: "cursor:pointer;font-weight:600" }, cmLeccion(id).t + " — " + si.filter(p => p.lec === id).map(p => (S.idioma === "en" ? REF_EN[p.id] : p.q).replace(/^¿|\?$/g, "")).join(" · ")), bloqueLeccion(id))),
      no.length ? [h("h3", {}, "⚠ " + t("ref_no_hace")), h("p", {}, t("ref_3d"))] : null),
    h("div", { class: "acciones" }, h("button", { onclick: refPreguntas }, t("cm_ant")),
      h("button", { class: "primario", onclick: async () => {
        const r = await pedirTexto(t("ref_crear"), t("ref_nombre"), ""); if (!r) return;
        const { id } = await api("POST", "/api/productos", { nombre: r.valor, practica: false });
        await refrescarProductos(); S.camino0 = camino; S.caminos[id] = camino; api("POST", "/api/config", { camino, caminos: S.caminos }).catch(() => {});
        S.pid = id; S.pestana = camino === "musica" ? "escenas" : "guiones"; cerrarModal(); render(); } }, t("ref_crear")))], { ancha: true });
}
