; Inno Setup Script for Bluestreak Box Uploader
; Run this on Windows after building with PyInstaller

#define MyAppName "Bluestreak Box Uploader"
#define MyAppVersion "0.1.0"
#define MyAppPublisher "Burton Industries"
#define MyAppExeName "Bluestreak Box Uploader.exe"

[Setup]
AppId={{B1C2D3E4-F5A6-7890-BCDE-123456789ABC}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
OutputDir=installer_output
OutputBaseFilename=BluestreakBoxUploader_Setup_{#MyAppVersion}
SetupIconFile=app.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\{#MyAppExeName}
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Include all files from PyInstaller output
Source: "dist\Bluestreak Box Uploader\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[Code]
procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  AppDataPath: String;
begin
  if CurUninstallStep = usPostUninstall then
  begin
    AppDataPath := ExpandConstant('{userappdata}\BluestreakBoxUploader');
    if DirExists(AppDataPath) then
    begin
      if MsgBox('Do you want to delete your settings and data?' + #13#10 + #13#10 +
                'This will remove your saved configuration, including database credentials and preferences.',
                mbConfirmation, MB_YESNO) = IDYES then
      begin
        DelTree(AppDataPath, True, True, True);
      end;
    end;
  end;
end;
