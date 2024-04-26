@echo off

set name=

set tgToken=
set tgChatid=

SET baseDir=%cd%

set unityPath=
set unityEditorPath=%unityPath%Editor\Unity.exe

set projectPath=
set projectPathAndroid=

set buildpath=

REM commands

del /S /Q %buildpath%
CD  %buildpath%
RMDIR /S /Q .

if %1 == win (
    CD  %baseDir%
    call buildWin.bat
    call archive.bat
) else if %1 == android (
    CD  %baseDir%
    call buildAndroid.bat
) else (
    CD  %baseDir%
    call buildWin.bat
    call archive.bat
    CD  %baseDir%
    call buildAndroid.bat
)

cd %buildpath%

@echo on

dir

@echo off
cd %baseDir%
@echo on

@echo UPLOAD TO TELEGRAM [UnityBuilds]

@echo off
.venv\scripts\python .\telegramBot.py -folderpath %buildpath% -token %tgToken% -chatid %tgChatid%