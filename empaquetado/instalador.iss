; Inno Setup: crea Vibovapp-Setup.exe con el programa de la carpeta dist\Vibovapp
#define Nombre "Vibovapp"
#ifndef Version
  #define Version "0.0.0"
#endif
[Setup]
AppId={{516C0F18-E97B-4156-9BE1-0F3C2F0A6848}
AppName={#Nombre}
AppVersion={#Version}
AppPublisher=Vibovapp
DefaultDirName={autopf}\{#Nombre}
DefaultGroupName={#Nombre}
OutputDir=salida
OutputBaseFilename=Vibovapp-Setup
SetupIconFile=..\vibovapp.ico
UninstallDisplayIcon={app}\Vibovapp.exe
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
CloseApplications=yes
RestartApplications=no
[Languages]
Name: "es"; MessagesFile: "compiler:Languages\Spanish.isl"
[Tasks]
Name: "icono"; Description: "Crear acceso directo en el escritorio"; GroupDescription: "Accesos directos:"
[Files]
Source: "..\dist\Vibovapp\*"; DestDir: "{app}"; Flags: recursesubdirs ignoreversion
[Icons]
Name: "{group}\{#Nombre}"; Filename: "{app}\Vibovapp.exe"
Name: "{autodesktop}\{#Nombre}"; Filename: "{app}\Vibovapp.exe"; Tasks: icono
[Run]
Filename: "{app}\Vibovapp.exe"; Description: "Abrir Vibovapp"; Flags: nowait postinstall skipifsilent
; Al actualizar desde el programa (instalación silenciosa) se vuelve a abrir solo:
Filename: "{app}\Vibovapp.exe"; Flags: nowait; Check: WizardSilent
