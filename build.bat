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

cd %baseDir%

if %1 == win
(
    call buildWin.bat
    call archive.bat
)
else if %1 == android
(
   call buildAndroid.bat
)
else
(
    call buildWin.bat
    call archive.bat
    call buildAndroid.bat
)

cd %buildpath%
dir

cd %baseDir%
.venv\scripts\python .\telegramBot.py -folderpath %buildpath% -token %tgToken% -chatid %tgChatid%