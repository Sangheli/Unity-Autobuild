set app="C:\Program Files\7-Zip\7z.exe"

set archivepath=%buildpath%build.7z
set filespath=%buildpath%Windows\

cd %filespath%
%app% a %archivepath%