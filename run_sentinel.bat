@echo off
REM Sentinel-RAG V5 Quick Launcher
REM Double-click this file to run Sentinel-RAG V5

echo ================================================================================
echo SENTINEL-RAG V5 LAUNCHER
echo ================================================================================
echo.

:menu
echo Choose an option:
echo.
echo [1] Analyze a single PDF file
echo [2] Run test suite on all test resumes
echo [3] Launch web interface
echo [4] Exit
echo.

set /p choice="Enter choice (1-4): "

if "%choice%"=="1" goto analyze
if "%choice%"=="2" goto test
if "%choice%"=="3" goto web
if "%choice%"=="4" goto end

echo Invalid choice. Please try again.
echo.
goto menu

:analyze
echo.
set /p filepath="Enter path to PDF file: "
echo.
echo Running detection on %filepath%...
echo.
python run_sentinel_v5.py --file "%filepath%"
echo.
pause
goto menu

:test
echo.
echo Running test suite...
echo.
python run_sentinel_v5.py --test
echo.
pause
goto menu

:web
echo.
echo Launching web interface...
echo Open your browser to: http://localhost:5000
echo.
echo Press Ctrl+C to stop the server when done.
echo.
python run_sentinel_v5.py --web
goto menu

:end
echo.
echo Goodbye!
timeout /t 2