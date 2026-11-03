"""SOLO PARA EL DUEÑO (no se entrega a clientes).
Doble clic y responde las preguntas: te da la clave de licencia (plan) o de créditos para el comprador.
También sirve desde la terminal:
    python generar_clave.py pro 0001            (clave de plan)
    python generar_clave.py creditos 5 0007     (clave de 5 créditos: 5 videos sueltos con todo lo del plan Pro)
    python generar_clave.py reinicio 0012       (clave para volver a 0 el contador de videos del mes de una computadora)"""
import sys
import planes


def _pedir_serie():
    serie = ""
    while not (4 <= len(serie) <= 12 and serie.isalnum()):
        serie = input("Número o código del comprador (4 a 12 letras o números, ej. 0001): ").strip()
    return serie


def pedir():
    print("=== Generador de claves ===\n")
    print("Tipos de clave:\n   basico   = plan Básico\n   pro      = plan Pro\n   agencia  = plan Agencia\n   creditos = videos sueltos (cada crédito = 1 video con todo lo del plan Pro)\n   reinicio = vuelve a 0 los videos usados este mes (para dar otra prueba)\n")
    print("Precios sugeridos de créditos: " + ", ".join(f"{n} video(s) = {usd} USD" for n, usd in planes.PAQUETES_CREDITOS) + "\n")
    tipo = ""
    while tipo not in ("basico", "pro", "agencia", "creditos", "reinicio"):
        tipo = input("¿Qué tipo? (basico, pro, agencia, creditos o reinicio): ").strip().lower().replace("á", "a").replace("í", "i").replace("é", "e").replace("ó", "o")
    cantidad = None
    if tipo == "creditos":
        while not (cantidad and 1 <= cantidad <= 999):
            texto = input("¿Cuántos créditos incluye? (1 a 999, ej. 1, 5 o 10): ").strip()
            cantidad = int(texto) if texto.isdigit() else None
    return tipo, cantidad, _pedir_serie()


try:
    if len(sys.argv) == 3 and sys.argv[1].lower() in ("basico", "pro", "agencia"):
        tipo, cantidad, serie = sys.argv[1].lower(), None, sys.argv[2]
    elif len(sys.argv) == 3 and sys.argv[1].lower() == "reinicio":
        tipo, cantidad, serie = "reinicio", None, sys.argv[2]
    elif len(sys.argv) == 4 and sys.argv[1].lower() == "creditos":
        tipo, cantidad, serie = "creditos", int(sys.argv[2]), sys.argv[3]
    else:
        tipo, cantidad, serie = pedir()
    if tipo == "reinicio":
        clave = planes.crear_clave_reinicio(serie)
        queda = "reinicio del contador de videos"
    elif tipo == "creditos":
        clave = planes.crear_clave_creditos(cantidad, serie)
        queda = f"{cantidad} crédito(s)"
    else:
        clave = planes.crear_clave(tipo, serie)
        queda = f"plan {tipo}"
    print(f"\nClave para el comprador ({queda}):\n")
    print("   ", clave)
    print("\n(Cópiala y envíasela. Cada comprador debe tener un número distinto. Una clave de créditos o de reinicio se puede canjear una sola vez por computadora.)")
except Exception as e:
    print("\nNo se pudo crear la clave:", e)
input("\nPresiona Enter para cerrar…")
