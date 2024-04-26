@echo off

set exepath=%buildpath%Windows\%name%.exe
set logpath=%buildpath%Log\logWindows.txt

@echo on

%unityEditorPath% -quit -batchmode -nographics -projectpath %projectPath% -buildWindowsPlayer %exepath% -logFile %logpath%

@echo off