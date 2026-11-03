# -*- coding: utf-8 -*-
"""Pruebas rapidas del catalogo de ajustes (no generan video). Uso:  python pruebas.py"""
import pathlib
import tempfile

import catalogo
import generar_diario as g

errores = []


def comprobar(cond, msg):
    if not cond:
        errores.append(msg)


# 1) cada ajuste tiene categoria valida, textos y un valor por defecto que pasa su propia validacion
cats = {c[0] for c in catalogo.CATEGORIAS}
for a in catalogo.AJUSTES:
    comprobar(a["categoria"] in cats, f"{a['clave']}: categoria desconocida")
    comprobar(a["es"] and a["en"], f"{a['clave']}: falta nombre en es/en")
    v, e = catalogo.validar(a["clave"], catalogo.a_texto(a, a["defecto"]))
    comprobar(e is None, f"{a['clave']}: su valor por defecto no es valido ({e})")
    comprobar(v == a["defecto"], f"{a['clave']}: valor por defecto no sobrevive ida y vuelta ({v!r} != {a['defecto']!r})")

# 2) claves unicas
claves = [a["clave"] for a in catalogo.AJUSTES]
comprobar(len(claves) == len(set(claves)), "hay claves repetidas")

# 3) ajustes.txt generado se vuelve a leer igual (en espanol y en ingles)
for idioma in ("es", "en"):
    valores = catalogo.defectos()
    valores.update({"cta": 'Escribe “HOLA”: ya', "usuario": "@x", "oscurecer_min": 33, "titulo_segundos": 4.5,
                    "pantalla_completa": False, "efectos_clip": "zoom_in,punch", "color_texto": "#112233"})
    with tempfile.TemporaryDirectory() as d:
        ruta = pathlib.Path(d) / "ajustes.txt"
        ruta.write_text(catalogo.texto_ajustes(valores, idioma), encoding="utf-8-sig")
        leido = catalogo.defectos()
        avisos = g.leer_ajustes(ruta, leido)
        comprobar(not avisos, f"[{idioma}] avisos al releer: {avisos}")
        for k, v in valores.items():
            comprobar(leido[k] == v, f"[{idioma}] {k}: {leido[k]!r} != {v!r}")

# 4) valores malos se rechazan con mensaje
for k, v in [("oscurecer_min", "mucho"), ("color_texto", "nocolor"), ("pantalla_completa", "quizas"),
             ("transiciones", "raras"), ("efectos_clip", "volar")]:
    _, e = catalogo.validar(k, v)
    comprobar(e is not None, f"{k}={v} debio rechazarse")

# 5) numeros fuera de rango se acercan al limite
comprobar(catalogo.validar("tam_cta", "9999")[0] == 200, "tam_cta no se limito")

if errores:
    print("FALLARON", len(errores), "pruebas:")
    for e in errores:
        print(" -", e)
    raise SystemExit(1)
print(f"Todo bien: {len(catalogo.AJUSTES)} ajustes revisados.")
