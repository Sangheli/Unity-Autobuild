set exepath=%buildpath%Windows\%name%.exe
set logpath=%buildpath%Log\logWindows.txt

%unityEditorPath% -quit -batchmode -nographics -projectpath %projectPath% -buildWindowsPlayer %exepath% -logFile %logpath%