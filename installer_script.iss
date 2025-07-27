[Setup]
; Application Information
AppName=Portal das Finanças Receipts
AppVersion=1.0.0
AppPublisher=LuciaBytes
AppPublisherURL=https://github.com/luciaBytes/receipts
AppSupportURL=https://github.com/luciaBytes/receipts/issues
AppUpdatesURL=https://github.com/luciaBytes/receipts/releases
AppCopyright=Copyright © 2025 LuciaBytes

; Installation Configuration
DefaultDirName={autopf}\PortalReceiptsApp
DefaultGroupName=Portal das Finanças Receipts
AllowNoIcons=yes
LicenseFile=LICENSE.txt
OutputDir=installer_output
OutputBaseFilename=PortalReceiptsApp_Setup_v1.0.0
SetupIconFile=assets\app_icon.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern

; System Requirements
VersionInfoVersion=1.0.0.0
VersionInfoCompany=LuciaBytes
VersionInfoDescription=Portal das Finanças Receipt Automation Installer
VersionInfoCopyright=Copyright © 2025 LuciaBytes
VersionInfoProductName=Portal das Finanças Receipts
VersionInfoProductVersion=1.0.0

; Architecture Support
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

; Security
PrivilegesRequired=lowest
DisableProgramGroupPage=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "portuguese"; MessagesFile: "compiler:Languages\Portuguese.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Main application files
Source: "dist\PortalReceiptsApp\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

; Documentation
Source: "README.md"; DestDir: "{app}\docs"; Flags: ignoreversion
Source: "SENSITIVE_DATA_CLEANUP.md"; DestDir: "{app}\docs"; Flags: ignoreversion
Source: "credentials.example"; DestDir: "{app}"; Flags: ignoreversion

; Visual C++ Redistributable (if needed)
; Source: "vcredist_x64.exe"; DestDir: "{tmp}"; Flags: deleteafterinstall

[Icons]
Name: "{group}\Portal das Finanças Receipts"; Filename: "{app}\PortalReceiptsApp.exe"
Name: "{group}\User Guide"; Filename: "{app}\docs\README.md"
Name: "{group}\{cm:UninstallProgram,Portal das Finanças Receipts}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\Portal das Finanças Receipts"; Filename: "{app}\PortalReceiptsApp.exe"; Tasks: desktopicon

[Run]
; Install Visual C++ Redistributable if needed
; Filename: "{tmp}\vcredist_x64.exe"; Parameters: "/install /quiet /norestart"; Check: VCRedistNeedsInstall

Filename: "{app}\PortalReceiptsApp.exe"; Description: "{cm:LaunchProgram,Portal das Finanças Receipts}"; Flags: nowait postinstall skipifsilent

[Code]
function VCRedistNeedsInstall: Boolean;
begin
  // Add logic to check if VC++ Redistributable is needed
  Result := False;
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    // Create credentials file from example if it doesn't exist
    if not FileExists(ExpandConstant('{app}\credentials')) then
    begin
      FileCopy(ExpandConstant('{app}\credentials.example'), 
               ExpandConstant('{app}\credentials'), False);
    end;
  end;
end;

[UninstallDelete]
Type: files; Name: "{app}\logs\*"
Type: dirifempty; Name: "{app}\logs"
