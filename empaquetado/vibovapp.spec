# -*- mode: python ; coding: utf-8 -*-
# Receta de PyInstaller: junta Python + programa + web + ffmpeg en una carpeta.
import os
raiz = os.path.abspath(os.path.join(SPECPATH, ".."))
datos = [(os.path.join(raiz, "web"), "web"), (os.path.join(raiz, "vibovapp.ico"), ".")]
bin_dir = os.path.join(SPECPATH, "bin")
if os.path.isdir(bin_dir):
    datos.append((bin_dir, "bin"))
fuentes = os.path.join(raiz, "fuentes")
if os.path.isdir(fuentes):
    datos.append((fuentes, "fuentes"))

a = Analysis([os.path.join(raiz, "iniciar.py")], pathex=[raiz], datas=datos,
             hiddenimports=["webview", "flask", "PIL", "planes", "gumroad", "gumroad_config", "actualizador", "novedades", "errores", "voz", "hablado", "ventana", "pymupdf", "fitz"], noarchive=False)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name="Vibovapp", console=False,
          icon=os.path.join(raiz, "vibovapp.ico"))
coll = COLLECT(exe, a.binaries, a.datas, name="Vibovapp")
