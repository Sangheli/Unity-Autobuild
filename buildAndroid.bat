set exepath=%buildpath%%name%.apk
set logpath=%buildpath%Log\logAndroid.txt

%unityEditorPath% -quit -batchmode -nographics -projectPath %projectPathAndroid% -logFile %logpath% -executeMethod BuildScript.PerformBuild %exepath%