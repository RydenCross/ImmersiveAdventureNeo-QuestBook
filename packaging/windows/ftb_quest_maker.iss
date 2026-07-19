#ifndef AppVersion
  #define AppVersion "0.0.0"
#endif
#ifndef SourceBinary
  #define SourceBinary "dist/native/FTBQuestMaker.exe"
#endif
#ifndef OutputDir
  #define OutputDir "dist/packages"
#endif
#ifndef OutputBaseFilename
  #define OutputBaseFilename "FTBQuestMaker-Setup"
#endif

[Setup]
AppId={{93BB02A0-5221-46EA-B30C-5E7C36EE7FB1}
AppName=FTB Quest Maker
AppVersion={#AppVersion}
AppPublisher=FTB Quest Maker
DefaultDirName={autopf}\FTB Quest Maker
DefaultGroupName=FTB Quest Maker
OutputDir={#OutputDir}
OutputBaseFilename={#OutputBaseFilename}
Compression=lzma2
SolidCompression=yes
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=lowest
WizardStyle=modern
UninstallDisplayIcon={app}\FTBQuestMaker.exe

[Files]
Source: "{#SourceBinary}"; DestDir: "{app}"; DestName: "FTBQuestMaker.exe"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\FTB Quest Maker"; Filename: "{app}\FTBQuestMaker.exe"
Name: "{autodesktop}\FTB Quest Maker"; Filename: "{app}\FTBQuestMaker.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional icons:"

[Run]
Filename: "{app}\FTBQuestMaker.exe"; Description: "Launch FTB Quest Maker"; Flags: nowait postinstall skipifsilent
