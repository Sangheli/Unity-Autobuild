set exepath=%buildpath%Windows\%name%.exe
set logpath=%buildpath%logWindows.txt

%unityEditorPath% -quit -batchmode -nographics -projectpath %projectPath% -buildWindowsPlayer %exepath% -logFile %logpath%