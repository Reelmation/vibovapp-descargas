// Cuadrito de marcas: selecciona una palabra o frase del guion (clic y arrastrar, doble clic o Shift + flechas) y elige qué pasa con ella.
// En el guion se guarda como [[frase|opciones]] — todo se puede volver a abrir y cambiar.
Object.assign(TEXTOS.es, {
  mk_titulo: "✨ Marcar esta frase", mk_ayuda: "Selecciona una palabra o frase del guion con el mouse o con Shift + flechas.",
  mk_txt: "Texto en pantalla", mk_nosub: "No sale en los subtítulos", mk_pop: "Sonido «pop»",
  mk_dice: "Qué pasa con lo que dice el video", mk_dice_si: "Se dice normal", mk_dice_nadie: "Nadie lo dice (solo se ve el texto)", mk_dice_corta: "Se dice, pero cortar ese pedazo del video",
  mk_mas: "Más opciones del texto", mk_tam: "Tamaño", mk_color: "Color", mk_efecto: "Cómo entra", mk_pos: "Dónde", mk_seg: "Segundos en pantalla",
  mk_e_fundido: "Aparece suave", mk_e_subir: "Sube", mk_e_rebote: "Rebota", mk_e_izquierda: "Entra por la izquierda", mk_e_derecha: "Entra por la derecha", mk_e_ninguna: "De golpe",
  mk_p_arriba: "Arriba", mk_p_centro: "Centro", mk_p_abajo: "Abajo", mk_aplicar: "Aplicar", mk_quitar: "Quitar la marca", mk_nuevo: "+ Texto que nadie dice", mk_nuevo_ph: "Escribe tu texto",
  mk_burbuja: "Burbuja de chat", mk_b_no: "Ninguna", mk_b_emisor: "Burbuja emisor", mk_b_receptor: "Burbuja receptor", mk_img: "Imagen encima", mk_img_no: "Ninguna", mk_prev_ayuda: "Así se verá. Toca la imagen arriba, en medio o abajo para moverlo.", mk_estilo: "Estilo de subtítulo de esta frase", mk_s_color: "Color", mk_s_caja: "Caja", mk_s_grande: "Grande", mk_s_doble: "Dos niveles", mk_s_una: "Una palabra a la vez", mk_nuevo_f: "+ Figura", mk_img_otra: "Otra imagen (collage)", mk_collage: "+ Agregar otra imagen (collage)", mk_fig: "Figura encima", mk_fig_no: "Ninguna", mk_f_flecha: "↓ Flecha", mk_f_circulo: "◯ Círculo", mk_f_subrayado: "▬ Subrayado", mk_f_destello: "✸ Destello", mk_img_ayuda: "Vienen de «Imágenes del proyecto». El tamaño de la imagen es el % del ancho.", mk_nuevo_b: "+ Burbuja de chat", mk_nuevo_i: "+ Imagen", mk_nuevo_b_ph: "Escribe el mensaje",
  mk_solo_hablando: "Las marcas funcionan en guiones de texto para «Mis videos en cámara». En los guiones con voz usa las burbujas.", mk_igual: "Igual que el estilo"
});
Object.assign(TEXTOS.en, {
  mk_titulo: "✨ Mark this phrase", mk_ayuda: "Select a word or phrase in the script with the mouse or Shift + arrow keys.",
  mk_txt: "On-screen text", mk_nosub: "Not in the subtitles", mk_pop: "“Pop” sound",
  mk_dice: "What happens with what the video says", mk_dice_si: "Said as normal", mk_dice_nadie: "Nobody says it (only the text shows)", mk_dice_corta: "It is said, but cut that part out of the video",
  mk_mas: "More text options", mk_tam: "Size", mk_color: "Color", mk_efecto: "How it enters", mk_pos: "Where", mk_seg: "Seconds on screen",
  mk_e_fundido: "Fades in", mk_e_subir: "Slides up", mk_e_rebote: "Bounces", mk_e_izquierda: "From the left", mk_e_derecha: "From the right", mk_e_ninguna: "Instant",
  mk_p_arriba: "Top", mk_p_centro: "Middle", mk_p_abajo: "Bottom", mk_aplicar: "Apply", mk_quitar: "Remove the mark", mk_nuevo: "+ Text nobody says", mk_nuevo_ph: "Type your text",
  mk_burbuja: "Chat bubble", mk_b_no: "None", mk_b_emisor: "Sender bubble", mk_b_receptor: "Receiver bubble", mk_img: "Image on top", mk_img_no: "None", mk_prev_ayuda: "This is how it will look. Tap the image at the top, middle or bottom to move it.", mk_estilo: "Subtitle style for this phrase", mk_s_color: "Color", mk_s_caja: "Box", mk_s_grande: "Big", mk_s_doble: "Two levels", mk_s_una: "One word at a time", mk_nuevo_f: "+ Shape", mk_img_otra: "Another image (collage)", mk_collage: "+ Add another image (collage)", mk_fig: "Shape on top", mk_fig_no: "None", mk_f_flecha: "↓ Arrow", mk_f_circulo: "◯ Circle", mk_f_subrayado: "▬ Underline", mk_f_destello: "✸ Sparkle", mk_img_ayuda: "They come from the project images. Image size is the % of the width.", mk_nuevo_b: "+ Chat bubble", mk_nuevo_i: "+ Image", mk_nuevo_b_ph: "Type the message",
  mk_solo_hablando: "Marks work in text scripts for “My on-camera videos”. In scripts with a voice use the bubbles.", mk_igual: "Same as the style"
});
const MK_RE = /\[\[[^\]]*\]\]/g;
function mkLeer(txt) {   // «frase|-sub txt pop tam=80» -> estado del cuadrito
  const i = txt.indexOf("|"), frase = (i < 0 ? txt : txt.slice(0, i)).trim(), op = i < 0 ? "" : txt.slice(i + 1);
  const E = { frase, txt: false, nosub: false, pop: false, dice: "si", tam: "", color: "", efecto: "", pos: "", seg: "", burbuja: "", img: "", fig: "", estilo: "" };
  op.split(/[\s,]+/).filter(Boolean).forEach(o => {
    const [k, v = ""] = o.split("=");
    if (k === "txt" || k === "texto") E.txt = true; else if (k === "-sub") E.nosub = true; else if (k === "pop") E.pop = true;
    else if (k === "-dice") E.dice = "nadie"; else if (k === "corta") E.dice = "corta";
    else if (k === "burbuja") E.burbuja = /^(receptor|receptora|cliente|client|them|ellos|otro|otra)$/i.test(v) ? "receptor" : "emisor";
    else if (k === "img") { E.img = v.split("+").map(x => { try { return decodeURIComponent(x); } catch (e) { return x; } }).join("+"); }
    else if (k === "fig") E.fig = v;
    else if (["tam", "color", "efecto", "pos", "seg", "estilo"].includes(k)) E[k] = v;
  });
  return E;
}
function mkEscribir(E) {
  const o = [];
  if (E.txt) o.push("txt"); if (E.nosub) o.push("-sub"); if (E.pop) o.push("pop");
  if (E.dice === "nadie") o.push("-dice"); if (E.dice === "corta") o.push("corta");
  if (E.burbuja) o.push("burbuja=" + E.burbuja);
  if (E.img) o.push("img=" + E.img.split("+").map(encodeURIComponent).join("+"));
  if (E.fig) o.push("fig=" + E.fig);
  ["tam", "color", "efecto", "pos", "seg", "estilo"].forEach(k => { if (String(E[k] || "").trim()) o.push(`${k}=${String(E[k]).trim()}`); });
  return `[[${E.frase.replace(/[\[\]|]/g, " ").replace(/\s+/g, " ").trim()}${o.length ? "|" + o.join(" ") : ""}]]`;
}
// ta = el cuadro de texto del guion · cambio = lo que hay que llamar cuando el texto cambia (guarda solo)
function panelMarcas(ta, cambio) {
  const caja = h("div", { class: "tarjeta marcas-panel", style: "margin:8px 0" });
  let imagenes = [];      // imágenes del proyecto (carpeta «Imágenes del proyecto»)
  api("GET", `${base()}/archivos/kit`).then(l => { imagenes = (l || []).filter(x => x.tipo === "imagen").map(x => x.nombre); if (E) pintar(); }).catch(() => {});
  let rango = null, E = null;      // rango = lo que se va a reemplazar en el texto [desde, hasta]
  // vista previa de la marca: se ve cómo quedará y, al tocar la imagen, se mueve arriba / centro / abajo
  const prev = h("img", { class: "mk-prev", alt: "", style: "width:120px;border-radius:8px;cursor:pointer;display:none;border:1px solid var(--borde,#4a5a86)", title: "" });
  let tPrev = null;
  const refrescarPrev = () => {
    clearTimeout(tPrev);
    tPrev = setTimeout(async () => {
      if (!E || !(E.txt || E.img || E.fig)) { prev.style.display = "none"; return; }
      try {
        const r = await fetch(`${base()}/previa_marca`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ marca: mkEscribir(E).slice(2, -2) }) });
        if (!r.ok) { prev.style.display = "none"; return; }
        const u = URL.createObjectURL(await r.blob()); const viejo = prev.src; prev.src = u; prev.style.display = "block"; if (viejo.startsWith("blob:")) URL.revokeObjectURL(viejo);
      } catch (e) { prev.style.display = "none"; }
    }, 250);
  };
  prev.addEventListener("click", ev => {
    if (!E) return;
    const f = (ev.offsetY || 0) / (prev.clientHeight || 1);
    E.pos = f < 0.33 ? "arriba" : f > 0.66 ? "abajo" : ""; aplicar(); pintar();
  });
  const pintar = () => {
    caja.innerHTML = "";
    if (!E) { caja.append(h("b", {}, t("mk_titulo")), h("div", { class: "chico suave", style: "margin:2px 0 8px" }, t("mk_ayuda")),
      h("div", { class: "fila", style: "gap:6px;flex-wrap:wrap" },
        h("button", { class: "chico btn-mk-nuevo", onclick: nuevo }, t("mk_nuevo")),
        h("button", { class: "chico btn-mk-burbuja", onclick: nuevoBurbuja }, t("mk_nuevo_b")),
        h("button", { class: "chico btn-mk-imagen", onclick: nuevaImagen }, t("mk_nuevo_i")),
        h("button", { class: "chico btn-mk-figura", onclick: nuevaFigura }, t("mk_nuevo_f")))); return; }
    const chk = (k, etq) => h("label", { style: "display:flex;gap:8px;align-items:center;margin:4px 0" }, h("input", { type: "checkbox", checked: E[k], onchange: e => { E[k] = e.target.checked; aplicar(); } }), t(etq));
    const sel = (k, ops) => h("select", { onchange: e => { E[k] = e.target.value; aplicar(); } }, ops.map(([v, tx]) => h("option", { value: v, selected: E[k] === v }, tx)));
    const num = (k, w) => h("input", { type: "number", value: E[k], style: `width:${w || 80}px`, onchange: e => { E[k] = e.target.value; aplicar(); } });
    const fila = (l, c) => h("div", { class: "fila", style: "margin:6px 0;gap:8px" }, h("span", { class: "chico suave", style: "min-width:120px" }, l), c);
    const color = h("input", { type: "color", value: /^#[0-9a-f]{6}$/i.test(E.color) ? E.color : "#ffffff", oninput: e => { E.color = e.target.value; aplicar(); } });
    caja.append(h("b", {}, t("mk_titulo") + " «" + E.frase + "»"),
      fila(t("mk_burbuja"), h("select", { class: "sel-mk-burbuja", onchange: e => { E.burbuja = e.target.value; if (E.burbuja) { E.dice = "nadie"; E.txt = false; } aplicar(); pintar(); } },
        [["", t("mk_b_no")], ["emisor", t("mk_b_emisor")], ["receptor", t("mk_b_receptor")]].map(([v, tx]) => h("option", { value: v, selected: E.burbuja === v }, tx)))),
      ...(() => {      // una imagen, o hasta 4 juntas (collage)
        const lista = E.img ? E.img.split("+") : [""];
        const cambiar = (i, v) => { lista[i] = v; E.img = lista.filter(Boolean).join("+"); aplicar(); pintar(); };
        const filas = lista.map((nom, i) => fila(i === 0 ? t("mk_img") : t("mk_img_otra"), h("select", { class: "sel-mk-img", onchange: e => cambiar(i, e.target.value) },
          [["", t("mk_img_no")]].concat(imagenes.concat(nom && !imagenes.includes(nom) ? [nom] : []).map(n => [n, n])).map(([v, tx]) => h("option", { value: v, selected: nom === v }, tx)))));
        return [...filas, E.img ? h("div", { class: "chico suave" }, t("mk_img_ayuda")) : null,
          E.img && lista.length < 4 ? h("button", { class: "chico btn-mk-collage", style: "margin:4px 0", onclick: () => { lista.push(imagenes.find(x => !lista.includes(x)) || imagenes[0] || ""); E.img = lista.filter(Boolean).join("+"); aplicar(); pintar(); } }, t("mk_collage")) : null].filter(Boolean);
      })(),
      fila(t("mk_fig"), h("select", { class: "sel-mk-fig", onchange: e => { E.fig = e.target.value; aplicar(); } },
        [["", t("mk_fig_no")]].concat(["flecha", "circulo", "subrayado", "destello"].map(x => [x, t("mk_f_" + x)])).map(([v, tx]) => h("option", { value: v, selected: E.fig === v }, tx)))),
      E.burbuja ? null : chk("txt", "mk_txt"), chk("nosub", "mk_nosub"), chk("pop", "mk_pop"),
      fila(t("mk_estilo"), sel("estilo", [["", t("mk_igual")], ["color", t("mk_s_color")], ["caja", t("mk_s_caja")], ["grande", t("mk_s_grande")], ["una", t("mk_s_una")], ["doble", t("mk_s_doble")]])),
      fila(t("mk_dice"), sel("dice", [["si", t("mk_dice_si")], ["nadie", t("mk_dice_nadie")], ["corta", t("mk_dice_corta")]])),
      h("details", { open: !!(E.tam || E.color || E.efecto || E.pos || E.seg) }, h("summary", { style: "cursor:pointer;font-weight:600" }, t("mk_mas")),
        fila(t("mk_tam"), num("tam")), fila(t("mk_color"), h("div", { class: "ctl" }, color, h("button", { class: "chico", title: t("mk_igual"), onclick: () => { E.color = ""; aplicar(); pintar(); } }, "↺"))),
        fila(t("mk_efecto"), sel("efecto", [["", t("mk_igual")]].concat(["fundido", "subir", "rebote", "izquierda", "derecha", "ninguna"].map(x => [x, t("mk_e_" + x)])))),
        fila(t("mk_pos"), sel("pos", [["", t("mk_p_centro")]].concat(["arriba", "abajo"].map(x => [x, t("mk_p_" + x)])))), fila(t("mk_seg"), num("seg"))),
      h("div", { class: "fila", style: "margin:8px 0;gap:10px;align-items:flex-start" }, prev, h("div", { class: "chico suave mk-prev-ayuda" }, t("mk_prev_ayuda"))),
      h("div", { class: "fila", style: "margin-top:8px" }, h("button", { class: "chico peligro", onclick: quitar }, t("mk_quitar")), h("button", { class: "chico", onclick: () => { E = null; rango = null; pintar(); } }, "✕")));
    refrescarPrev();
  };
  const aplicar = () => {      // escribe la marca en el guion al instante (se guarda solo)
    if (!E || !rango) return;
    const m = mkEscribir(E), v = ta.value;
    ta.value = v.slice(0, rango[0]) + m + v.slice(rango[1]);
    rango = [rango[0], rango[0] + m.length];
    ta.dispatchEvent(new Event("input")); cambio && cambio(); refrescarPrev();
  };
  const quitar = () => {
    if (!rango) return;
    const v = ta.value;
    ta.value = v.slice(0, rango[0]) + E.frase + v.slice(rango[1]);
    ta.dispatchEvent(new Event("input")); cambio && cambio(); E = null; rango = null; pintar();
  };
  const nuevo = () => {      // texto que nadie dice: se mete donde está el cursor
    const p = ta.selectionStart || 0;
    E = { frase: t("mk_nuevo_ph"), txt: true, nosub: false, pop: false, dice: "nadie", tam: "", color: "", efecto: "", pos: "", seg: "", burbuja: "", img: "" };
    const m = mkEscribir(E); ta.value = ta.value.slice(0, p) + m + ta.value.slice(p);
    rango = [p, p + m.length]; ta.dispatchEvent(new Event("input")); cambio && cambio(); pintar();
  };
  const insertar = (nuevoE, sel) => {      // mete una marca nueva donde está el cursor y la deja abierta para editarla
    const p = ta.selectionStart || 0;
    E = nuevoE;
    const m = mkEscribir(E); ta.value = ta.value.slice(0, p) + m + ta.value.slice(p);
    rango = [p, p + m.length]; ta.dispatchEvent(new Event("input")); cambio && cambio(); pintar();
  };
  const nuevoBurbuja = () => insertar({ frase: t("mk_nuevo_b_ph"), txt: false, nosub: false, pop: false, dice: "nadie", tam: "", color: "", efecto: "", pos: "", seg: "", burbuja: "receptor", img: "", fig: "" });
  const nuevaFigura = () => insertar({ frase: "", txt: false, nosub: false, pop: false, dice: "nadie", tam: "", color: "", efecto: "", pos: "", seg: "", burbuja: "", img: "", fig: "flecha" });
  const nuevaImagen = () => insertar({ frase: "", txt: false, nosub: false, pop: false, dice: "nadie", tam: "", color: "", efecto: "", pos: "", seg: "", burbuja: "", img: imagenes[0] || "", fig: "" });
  const mirar = () => {
    const a = ta.selectionStart, b = ta.selectionEnd, v = ta.value;
    let dentro = null; MK_RE.lastIndex = 0; let m;
    while ((m = MK_RE.exec(v))) if (a >= m.index && b <= m.index + m[0].length) { dentro = [m.index, m.index + m[0].length, m[0]]; break; }
    if (dentro) { rango = [dentro[0], dentro[1]]; E = mkLeer(dentro[2].slice(2, -2)); pintar(); return; }
    if (b > a && v.slice(a, b).trim()) {
      const sel = v.slice(a, b), ini = a + (sel.length - sel.trimStart().length), fin = b - (sel.length - sel.trimEnd().length);
      if (/[\[\]]/.test(v.slice(ini, fin))) return;
      rango = [ini, fin]; E = { frase: v.slice(ini, fin), txt: true, nosub: false, pop: false, dice: "si", tam: "", color: "", efecto: "", pos: "", seg: "", burbuja: "", img: "" };
      pintar();
    }
  };
  ["mouseup", "keyup", "select"].forEach(ev => ta.addEventListener(ev, () => setTimeout(mirar, 0)));
  pintar();
  return caja;
}
