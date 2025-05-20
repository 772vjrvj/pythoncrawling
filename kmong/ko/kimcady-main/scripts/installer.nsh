; scripts/installer.nsh - Custom NSIS script for PandoK

; CRC 검사 비활성화 (테스트용)
CRCCheck off
SetDatablockOptimize off

; 언인스톨 로직
!macro customUnInstall
  ; 프로그램 설치 디렉토리 삭제
  DetailPrint "Removing installation directory: $INSTDIR"
  Delete "$INSTDIR\Uninstall PandoK.exe"
  RMDir /r "$INSTDIR"

  ; 앱 데이터 디렉토리 삭제
  DetailPrint "Removing app data directory: $APPDATA\PandoK"
  RMDir /r "$APPDATA\PandoK"
  DetailPrint "Removing local app data directory: $LOCALAPPDATA\PandoK"
  RMDir /r "$LOCALAPPDATA\PandoK"

  ; 바탕화면 바로 가기 삭제
  DetailPrint "Removing desktop shortcut: $DESKTOP\PandoK.lnk"
  Delete "$DESKTOP\PandoK.lnk"

  ; 시작 메뉴 바로 가기 삭제
  DetailPrint "Removing start menu shortcut: $SMPROGRAMS\PandoK\PandoK.lnk"
  Delete "$SMPROGRAMS\PandoK\PandoK.lnk"
  RMDir "$SMPROGRAMS\PandoK"

  ; 레지스트리 항목 삭제
  DetailPrint "Removing registry key: HKCU\Software\PandoK"
  DeleteRegKey HKCU "Software\PandoK"
  DetailPrint "Removing registry key: HKLM\Software\Microsoft\Windows\CurrentVersion\Uninstall\com.PandoK"
  DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\com.PandoK"
!macroend

; 설치 전 초기화
!macro preInit
  ; 이전 앱 데이터 정리 (선택적)
  DetailPrint "Checking for previous app data: $APPDATA\PandoK"
  IfFileExists "$APPDATA\PandoK\*.*" 0 +2
    RMDir /r "$APPDATA\PandoK"

  ; 이전 레지스트리 항목 정리
  ReadRegStr $0 HKCU "Software\PandoK" "InstallLocation"
  ${If} $0 != ""
    DetailPrint "Removing previous installation at: $0"
    RMDir /r "$0"
    DeleteRegKey HKCU "Software\PandoK"
  ${EndIf}
!macroend