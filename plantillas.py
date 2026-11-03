"""Plantillas de temas y palabras clave: unas de arranque (editables) y las que guarda cada usuario."""
# Cada plantilla: id -> {"es": (nombre, {tema: palabras}), "en": (nombre, {tema: palabras})}
# Son solo un punto de partida: al aplicarlas el usuario las edita como quiera.
BASE = {
    "inmobiliaria": {
        "es": ("Inmobiliaria", {
            "casas": "casa casas departamento depa propiedad inmueble vivienda hogar terreno",
            "dinero": "dinero precio presupuesto credito hipoteca enganche pago comision inversion",
            "clientes": "cliente clientes prospecto prospectos comprador vendedor lead",
            "celular": "mensaje mensajes whatsapp celular llamada responder seguimiento",
            "cierre": "cierre cerrar venta ventas firma contrato escritura"}),
        "en": ("Real estate", {
            "houses": "house houses home apartment property listing land",
            "money": "money price budget mortgage loan deposit payment commission investment",
            "clients": "client clients buyer seller prospect lead",
            "phone": "message messages whatsapp phone call reply follow",
            "closing": "close closing sale sales sign contract deed"})},
    "restaurante": {
        "es": ("Restaurante y comida", {
            "comida": "comida platillo plato receta cocina menu comer hambre",
            "cocina": "cocinero chef cocina ingredientes sazon horno parrilla",
            "clientes": "cliente clientes mesa reservacion reserva comensal servicio",
            "dinero": "precio costo ganancia venta ventas propina cuenta",
            "bebidas": "bebida bebidas cafe cerveza vino coctel jugo"}),
        "en": ("Restaurant & food", {
            "food": "food dish plate recipe kitchen menu eat hungry",
            "kitchen": "cook chef ingredients flavor oven grill",
            "customers": "customer customers table reservation booking guest service",
            "money": "price cost profit sale sales tip bill",
            "drinks": "drink drinks coffee beer wine cocktail juice"})},
    "cursos": {
        "es": ("Cursos y educación", {
            "estudio": "estudiar estudio aprender aprendizaje clase clases curso cursos",
            "escuela": "escuela maestro maestra alumno alumnos tarea examen",
            "tecnologia": "computadora laptop internet app aplicacion programa digital",
            "metas": "meta metas objetivo exito logro certificado diploma",
            "dinero": "dinero precio beca pago inversion ingresos"}),
        "en": ("Courses & education", {
            "study": "study learn learning class classes course courses lesson",
            "school": "school teacher student students homework exam",
            "technology": "computer laptop internet app software digital",
            "goals": "goal goals objective success achievement certificate diploma",
            "money": "money price scholarship payment investment income"})},
    "belleza": {
        "es": ("Belleza y salud", {
            "belleza": "belleza maquillaje piel cabello uñas estetica spa cuidado",
            "salud": "salud ejercicio gimnasio dieta nutricion peso bienestar",
            "clientes": "cliente clientes cita citas servicio tratamiento resultados",
            "dinero": "precio paquete promocion descuento pago ganancias"}),
        "en": ("Beauty & health", {
            "beauty": "beauty makeup skin hair nails salon spa care",
            "health": "health exercise gym diet nutrition weight wellness",
            "clients": "client clients appointment appointments service treatment results",
            "money": "price package promotion discount payment profit"})},
    "negocios": {
        "es": ("Negocios y emprendimiento", {
            "negocio": "negocio empresa emprender emprendedor marca producto tienda",
            "dinero": "dinero ventas ingresos ganancia precio inversion ahorro",
            "clientes": "cliente clientes prospecto seguimiento cierre propuesta",
            "redes": "instagram tiktok youtube video reel contenido seguidores anuncio",
            "tiempo": "tiempo rapido automatico automatizar sistema proceso"}),
        "en": ("Business & entrepreneurship", {
            "business": "business company startup entrepreneur brand product store",
            "money": "money sales income profit price investment savings",
            "clients": "client clients prospect follow-up closing proposal",
            "social": "instagram tiktok youtube video reel content followers ad",
            "time": "time fast automatic automate system process"})},
}


def listar_base(idioma):
    idioma = "en" if idioma == "en" else "es"
    return [{"id": k, "nombre": v[idioma][0], "tipo": "base"} for k, v in BASE.items()]


def contenido_base(pid, idioma):
    idioma = "en" if idioma == "en" else "es"
    nombre, temas = BASE[pid][idioma]
    return nombre, {t: p.split() for t, p in temas.items()}
