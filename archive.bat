@echo off

set app="C:\Program Files\7-Zip\7z.exe"

set archivepath=%buildpath%build.7z
set filespath=%buildpath%Windows\

if not exist %filespath% (
    @echo on
    echo Folder [%filespath%] does not exist
    @echo off
    exit /b
)

cd %filespath%

@echo on

%app% a %archivepath%

@echo off