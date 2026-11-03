"""Guiones de ejemplo listos para usar: unos con burbujas de WhatsApp y otros básicos (solo texto y voz).
Son generales: sirven para cualquier negocio y el cliente cambia los datos. Cada uno: id -> tipo, nombre, texto y burbujas, en español e inglés.
En el texto, *1 /1 *2 son las marcas de las burbujas (donde sale cada mensaje)."""

LISTOS = {
    "precio": {
        "tipo": "burbujas",
        "es": ("Cliente que pregunta el precio", "Cuando te preguntan el precio",
               "Esto pasa todos los días: llega un mensaje y la primera pregunta es el precio. *1 No contestes solo con una cifra. /1 Primero cuenta qué incluye y para quién es. *2 Después das el precio y propones el siguiente paso. Así la conversación sigue y no se enfría.",
               [("emisor", "Hola, ¿cuánto cuesta?"), ("receptor", "¡Hola! Te cuento qué incluye y te doy el precio."), ("emisor", "Perfecto, ¿cómo seguimos?")]),
        "en": ("Customer asking the price", "When they ask for the price",
               "This happens every day: a message arrives and the first question is the price. *1 Don't answer with just a number. /1 First explain what's included and who it's for. *2 Then give the price and suggest the next step. That keeps the conversation going.",
               [("emisor", "Hi, how much is it?"), ("receptor", "Hi! Let me tell you what's included and the price."), ("emisor", "Great, what's next?")]),
    },
    "seguimiento": {
        "tipo": "burbujas",
        "es": ("Seguimiento a un prospecto", "El seguimiento que sí responden",
               "Muchos clientes no te dicen que no: solo dejan de contestar. *1 Un mensaje corto a tiempo lo cambia todo. /1 No preguntes si ya decidió; pregunta si le quedó alguna duda. *2 Y deja la puerta abierta con una fecha.",
               [("receptor", "Hola, ¿pudiste revisar la información que te mandé?"), ("emisor", "Sí, me quedó una duda."), ("receptor", "Dime, con gusto te ayudo.")]),
        "en": ("Following up with a lead", "The follow-up they answer",
               "Many customers never say no: they just stop replying. *1 A short message sent in time changes everything. /1 Don't ask if they decided; ask if they have any doubt. *2 And leave the door open with a date.",
               [("receptor", "Hi, were you able to review the information I sent?"), ("emisor", "Yes, I have one question."), ("receptor", "Tell me, happy to help.")]),
    },
    "cita": {
        "tipo": "burbujas",
        "es": ("Confirmar una cita", "Evita las citas canceladas",
               "Una cita sin confirmar es una cita que se puede perder. *1 Confirma el día antes con un mensaje corto. /1 Pon la hora y el lugar, y pide que respondan con un sí. *2 Es un minuto de trabajo que te ahorra horas.",
               [("receptor", "Hola, te confirmo tu cita de mañana a las 5 pm."), ("emisor", "Confirmado, ahí estaré."), ("receptor", "¡Excelente! Te esperamos.")]),
        "en": ("Confirming an appointment", "Avoid cancelled appointments",
               "An unconfirmed appointment is one you can lose. *1 Confirm the day before with a short message. /1 Include the time and place, and ask for a yes. *2 It takes a minute and saves you hours.",
               [("receptor", "Hi, confirming your appointment tomorrow at 5 pm."), ("emisor", "Confirmed, I'll be there."), ("receptor", "Great! See you then.")]),
    },
    "consejos": {
        "tipo": "basico",
        "es": ("Tres consejos rápidos", "3 consejos que te conviene saber",
               "Te comparto tres consejos rápidos. El primero: define bien lo que ofreces antes de publicar. El segundo: muestra resultados reales, no promesas. Y el tercero: termina siempre diciendo qué quieres que haga quien te ve. Si te sirvió, guarda este video."),
        "en": ("Three quick tips", "3 tips worth knowing",
               "Here are three quick tips. First: define clearly what you offer before you post. Second: show real results, not promises. And third: always end by saying what you want the viewer to do. If it helped, save this video."),
    },
    "servicio": {
        "tipo": "basico",
        "es": ("Presenta tu servicio", "Esto es lo que hacemos",
               "¿A quién ayudamos? A personas que quieren resultados sin complicarse. ¿Cómo lo hacemos? Con un proceso claro, paso a paso. ¿Y qué ganas tú? Tiempo, tranquilidad y un resultado que se nota. Escríbenos hoy y te explicamos cómo empezar."),
        "en": ("Introduce your service", "This is what we do",
               "Who do we help? People who want results without the hassle. How? With a clear, step-by-step process. What do you get? Time, peace of mind and a result you can see. Message us today and we'll explain how to start."),
    },
    "oferta": {
        "tipo": "basico",
        "es": ("Oferta de la semana", "Esta semana tenemos una oferta",
               "Esta semana tenemos una oferta especial. Incluye lo más pedido por nuestros clientes y solo está disponible por tiempo limitado. No dejes pasar la oportunidad. Escríbenos ahora y reserva el tuyo."),
        "en": ("This week's offer", "This week we have an offer",
               "This week we have a special offer. It includes what our customers ask for most and is available for a limited time. Don't miss it. Message us now and reserve yours."),
    },
    "caso": {
        "tipo": "basico",
        "es": ("Caso de éxito", "Así lo logró un cliente",
               "Un cliente llegó con un problema que le quitaba el tiempo. Trabajamos juntos, ajustamos lo necesario y en pocas semanas empezó a ver resultados. Lo mejor es que no fue magia: fue un proceso. Si quieres algo parecido, escríbenos."),
        "en": ("Success story", "How a customer did it",
               "A customer came to us with a problem that was eating their time. We worked together, adjusted what was needed and within weeks they saw results. The best part: it wasn't magic, it was a process. If you want something similar, message us."),
    },
}


def listar(idioma="es"):
    i = "en" if idioma == "en" else "es"
    return [{"id": k, "tipo": v["tipo"], "nombre": v[i][0], "titulo": v[i][1], "texto": v[i][2],
             "burbujas": len(v[i][3]) if v["tipo"] == "burbujas" else 0} for k, v in LISTOS.items()]


def obtener(id_, idioma="es"):
    v = LISTOS.get(id_)
    if not v:
        return None
    i = v["en" if idioma == "en" else "es"]
    return {"tipo": v["tipo"], "nombre": i[0], "titulo": i[1], "texto": i[2], "burbujas": i[3] if v["tipo"] == "burbujas" else []}
