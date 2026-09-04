@echo off
chcp 65001 > nul
echo ======================================================
echo    Live Movie Auto Cutter (ドラッグ＆ドロップ実行)
echo ======================================================

if "%~1"=="" (
    echo [使い方] 動画ファイル (.mp4, .mkv など) をこのバッチファイルの上にドラッグ＆ドロップしてください。
    echo.
    pause
    exit /b
)

echo 入力動画: %~1
echo.
python "%~dp0main.py" "%~1"
echo.
pause
