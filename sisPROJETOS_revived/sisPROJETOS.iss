; sisPROJETOS - Inno Setup Script
; Professional Installer for Power Distribution Engineering Tool

[Setup]
AppId={{C6E2A3C4-7B1E-4E5D-B6C2-F0E1D2C3B4A5}
AppName=sisPROJETOS
AppVersion=2.0
DefaultDirName={autopf}\sisPROJETOS
DefaultGroupName=sisPROJETOS
OutputDir=installer_output
OutputBaseFilename=sisPROJETOS_v2.0_Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "g:\Meu Drive\backup-02-2026\App\sisPROJETOS_v1.1\sisPROJETOS_revived\dist\sisPROJETOS\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; The database and resources should be handled by PyInstaller --add-data, 
; but we can also ensure they are present if needed.

[Icons]
Name: "{group}\sisPROJETOS"; Filename: "{app}\sisPROJETOS.exe"
Name: "{autodesktop}\sisPROJETOS"; Filename: "{app}\sisPROJETOS.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\sisPROJETOS.exe"; Description: "{cm:LaunchProgram,sisPROJETOS}"; Flags: nowait postinstall skipifsilent
