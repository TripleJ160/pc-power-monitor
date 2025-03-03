@echo off
echo Starting PC Power Monitor...

:: Set .NET configuration to allow loading assemblies from network locations
set COMPLUS_LoadFromRemoteSources=1

:: Run the application
python main.py

pause