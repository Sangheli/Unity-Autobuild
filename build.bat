set name=

SET baseDir=%cd%

set unityPath=
set unityEditorPath=%unityPath%Editor\Unity.exe

set projectPath=
set projectPathAndroid=

set buildpath=

cd %baseDir%
call buildWin.bat

cd %baseDir%
call buildAndroid.bat

cd %baseDir%
call archive.bat

cd %buildpath%
dir