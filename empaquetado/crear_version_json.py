"""Crea salida/version.json: la versión, lo que cambió (novedades.py), la huella y la FIRMA del instalador.
Ese archivo se publica junto con Vibovapp-Setup.exe (ver GUIA_ACTUALIZACIONES.txt) para que los programas instalados avisen
de la versión nueva y puedan instalarla solos. Se ejecuta automáticamente al crear el instalador."""
import hashlib
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import actualizador
import marca
import novedades

destino = Path(__file__).resolve().parent / "salida"
destino.mkdir(exist_ok=True)
instalador = destino / "Vibovapp-Setup.exe"
sha = hashlib.sha256(instalador.read_bytes()).hexdigest() if instalador.is_file() else ""
repo = os.environ.get("DESCARGAS_REPO", "").strip()            # por ejemplo  TuUsuario/vibovapp-descargas  (repositorio PÚBLICO de descargas)
url = os.environ.get("URL_INSTALADOR", "").strip() or (f"https://github.com/{repo}/releases/download/v{marca.VERSION}/Vibovapp-Setup.exe" if repo else "")
if not url:
    url = "PON_AQUI_EL_ENLACE_DIRECTO_AL_INSTALADOR"
cambios = novedades.de_la_version(marca.VERSION)
if marca.VERSION not in novedades.CAMBIOS:
    print(f"AVISO: novedades.py no tiene una entrada para la versión {marca.VERSION}. Agrégala arriba de las demás; mientras tanto se avisará solo «Mejoras y correcciones generales».")
datos = {"version": marca.VERSION, "descargar": url, "sha256": sha,
         "firma": actualizador.firma(marca.VERSION, sha, url) if sha and url.startswith("https://") else "",
         "cambios": cambios,
         "novedades_es": novedades.frases(cambios, "es"), "novedades_en": novedades.frases(cambios, "en")}
(destino / "version.json").write_text(json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8")
print("version.json creado para la versión", marca.VERSION, "| huella:", sha[:12] or "(no hay instalador)", "| firmado:", bool(datos["firma"]))
if not datos["firma"]:
    print("AVISO: sin enlace directo o sin instalador, las actualizaciones automáticas no se podrán instalar solas (solo se ofrecerá descargar).")
