"""Voz sintética con las voces que YA trae Windows (gratis, sin internet, sin claves).

Usa PowerShell + System.Speech (viene con Windows). El texto viaja en un archivo y los datos en variables de
entorno, así no hay problemas con comillas, acentos ni saltos de línea."""
import json
import os
import shutil
import subprocess
import tempfile
import urllib.error
import urllib.request
from pathlib import Path

import generar_diario as gd

_SCRIPT = r'''
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
Add-Type -AssemblyName System.Speech
$s = New-Object System.Speech.Synthesis.SpeechSynthesizer
try {
  if ($env:VIBOVAPP_VOZ_ACCION -eq 'listar') {
    foreach ($v in $s.GetInstalledVoices()) {
      if ($v.Enabled) { $i = $v.VoiceInfo; ('{0}|{1}|{2}' -f $i.Name, $i.Culture.Name, $i.Gender) }
    }
  } else {
    $texto = [System.IO.File]::ReadAllText($env:VIBOVAPP_VOZ_TEXTO, [System.Text.Encoding]::UTF8)
    if ($env:VIBOVAPP_VOZ_NOMBRE) { $s.SelectVoice($env:VIBOVAPP_VOZ_NOMBRE) }
    $s.Rate = [int]$env:VIBOVAPP_VOZ_VEL
    $s.Volume = 100
    $s.SetOutputToWaveFile($env:VIBOVAPP_VOZ_SALIDA)
    $s.Speak($texto)
  }
} finally { $s.Dispose() }
'''

_cache = {"voces": None}


def _powershell():
    raiz = os.environ.get("SystemRoot")
    if raiz:
        p = Path(raiz) / "System32" / "WindowsPowerShell" / "v1.0" / "powershell.exe"
        if p.exists():
            return str(p)
    return shutil.which("powershell")


def disponible():
    return _powershell() is not None


def _correr(env_extra, tiempo):
    ps = _powershell()
    if not ps:
        raise gd.ErrorMotor("Las voces de Windows solo funcionan en Windows. En este equipo no se encontró PowerShell.")
    fd, ruta = tempfile.mkstemp(suffix=".ps1", prefix="vibovapp_voz_")
    try:
        with os.fdopen(fd, "w", encoding="utf-8-sig") as f:
            f.write(_SCRIPT)
        env = {**os.environ, **{k: str(v) for k, v in env_extra.items()}}
        banderas = getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0
        try:
            r = subprocess.run([ps, "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-File", ruta],
                               env=env, capture_output=True, timeout=tiempo, creationflags=banderas)
        except subprocess.TimeoutExpired:
            raise gd.ErrorMotor("La voz tardó demasiado en generarse. Prueba con un texto más corto.")
    finally:
        try:
            os.remove(ruta)
        except OSError:
            pass
    salida = r.stdout.decode("utf-8", "replace")
    if r.returncode != 0:
        detalle = (r.stderr.decode("utf-8", "replace") or salida).strip().splitlines()
        raise gd.ErrorMotor("Windows no pudo generar la voz. " + (detalle[0][:200] if detalle else ""))
    return salida


def listar_voces(forzar=False):
    """Voces instaladas en Windows, con las de español primero (México antes que las demás)."""
    if _cache["voces"] is not None and not forzar:
        return _cache["voces"]
    voces = []
    for linea in _correr({"VIBOVAPP_VOZ_ACCION": "listar"}, 40).splitlines():
        partes = linea.strip().split("|")
        if len(partes) >= 2 and partes[0]:
            cultura = partes[1]
            voces.append({"nombre": partes[0], "cultura": cultura, "genero": partes[2] if len(partes) > 2 else "",
                          "es": cultura.lower().startswith("es")})
    voces.sort(key=lambda v: (not v["es"], not v["cultura"].lower().startswith("es-mx"), v["nombre"]))
    _cache["voces"] = voces
    return voces


def sintetizar(texto, salida, voz="", velocidad=0):
    """Escribe un .wav con el texto narrado. Falla con un mensaje claro si no se pudo."""
    texto = " ".join(str(texto or "").split())
    if not texto:
        raise gd.ErrorMotor("Escribe primero el texto del guion.")
    try:
        vel = max(-5, min(5, int(velocidad)))
    except (TypeError, ValueError):
        vel = 0
    salida = Path(salida)
    salida.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_txt = tempfile.mkstemp(suffix=".txt", prefix="vibovapp_voz_")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(texto)
        salida.unlink(missing_ok=True)
        _correr({"VIBOVAPP_VOZ_ACCION": "hablar", "VIBOVAPP_VOZ_TEXTO": tmp_txt, "VIBOVAPP_VOZ_SALIDA": str(salida),
                 "VIBOVAPP_VOZ_NOMBRE": voz or "", "VIBOVAPP_VOZ_VEL": vel}, 180)
    finally:
        try:
            os.remove(tmp_txt)
        except OSError:
            pass
    if not salida.exists() or salida.stat().st_size < 2000:
        salida.unlink(missing_ok=True)
        raise gd.ErrorMotor("No se generó el audio. Revisa que la voz elegida siga instalada en Windows.")
    return salida


# ----------------------------------------------------------------------------
# ElevenLabs (opcional, planes de pago): cada usuario usa SU PROPIA cuenta y clave; se paga aparte a ElevenLabs
# ----------------------------------------------------------------------------
URL_EL = os.environ.get("VIBOVAPP_ELEVENLABS_URL", "https://api.elevenlabs.io/v1")
MODELO_EL = "eleven_multilingual_v2"


def _error_el(e):
    """Traduce los errores de ElevenLabs a mensajes que se entienden."""
    try:
        cuerpo = json.loads(e.read().decode("utf-8", "ignore"))
        det = cuerpo.get("detail", cuerpo)
        estado = det.get("status", "") if isinstance(det, dict) else ""
        texto = det.get("message", "") if isinstance(det, dict) else str(det)
    except Exception:
        estado, texto = "", ""
    if estado == "quota_exceeded" or e.code == 402:      # ElevenLabs avisa la falta de créditos a veces con código 401
        return "Ya no te quedan créditos en tu cuenta de ElevenLabs (o tu plan no incluye esta función). Revisa tu cuenta en elevenlabs.io."
    if e.code == 401 or estado in ("invalid_api_key", "needs_authorization"):
        return "ElevenLabs no aceptó tu clave. Revisa que la copiaste completa y que tiene permiso para generar voz."
    if e.code == 429:
        return "ElevenLabs recibió demasiadas peticiones. Espera un momento y vuelve a intentar."
    if e.code == 404:
        return "ElevenLabs no encontró esa voz. Elige otra de la lista."
    return "ElevenLabs respondió con un error (" + str(e.code) + "). " + str(texto)[:160]


def _pedir_el(metodo, ruta, clave, cuerpo=None, tiempo=30):
    datos = json.dumps(cuerpo).encode("utf-8") if cuerpo is not None else None
    req = urllib.request.Request(URL_EL + ruta, data=datos, method=metodo,
                                 headers={"xi-api-key": clave, "Content-Type": "application/json", "Accept": "*/*"})
    try:
        with urllib.request.urlopen(req, timeout=tiempo) as r:
            return r.read()
    except urllib.error.HTTPError as e:
        raise gd.ErrorMotor(_error_el(e))
    except (urllib.error.URLError, TimeoutError, OSError):
        raise gd.ErrorMotor("No hay conexión con ElevenLabs. Revisa tu internet e intenta de nuevo.")


def el_voces(clave):
    """Voces de la cuenta del usuario (incluye las suyas, por ejemplo una voz clonada propia)."""
    datos = json.loads(_pedir_el("GET", "/voices", clave).decode("utf-8", "ignore") or "{}")
    voces = [{"id": v.get("voice_id", ""), "nombre": v.get("name", ""), "categoria": v.get("category", "")}
             for v in datos.get("voices", []) if v.get("voice_id")]
    # primero las propias (clonadas / generadas), luego las de la biblioteca
    voces.sort(key=lambda v: (v["categoria"] == "premade", v["nombre"].lower()))
    return voces


def el_cuota(clave):
    """(usados, limite) de caracteres del mes, o None si la clave no tiene permiso para verlo."""
    try:
        d = json.loads(_pedir_el("GET", "/user/subscription", clave, tiempo=15).decode("utf-8", "ignore") or "{}")
        return {"usados": int(d.get("character_count", 0)), "limite": int(d.get("character_limit", 0))}
    except Exception:
        return None


def el_sintetizar(texto, salida, clave, voz_id, velocidad=0):
    texto = " ".join(str(texto or "").split())
    if not texto:
        raise gd.ErrorMotor("Escribe primero el texto del guion.")
    if not voz_id:
        raise gd.ErrorMotor("Elige una voz de ElevenLabs.")
    try:
        vel = max(-5, min(5, int(velocidad)))
    except (TypeError, ValueError):
        vel = 0
    cuerpo = {"text": texto, "model_id": MODELO_EL}
    if vel:
        cuerpo["voice_settings"] = {"speed": round(1 + vel * 0.04, 2)}      # 0.8 a 1.2
    ruta = f"/text-to-speech/{urllib.request.quote(str(voz_id), safe='')}?output_format=mp3_44100_128"
    try:
        audio = _pedir_el("POST", ruta, clave, cuerpo, tiempo=180)
    except gd.ErrorMotor:
        if "voice_settings" not in cuerpo:
            raise
        cuerpo.pop("voice_settings")          # por si esa voz o modelo no admite cambiar la velocidad
        audio = _pedir_el("POST", ruta, clave, cuerpo, tiempo=180)
    salida = Path(salida)
    salida.parent.mkdir(parents=True, exist_ok=True)
    if len(audio) < 2000:
        raise gd.ErrorMotor("ElevenLabs no devolvió audio. Intenta de nuevo.")
    salida.write_bytes(audio)
    return salida
