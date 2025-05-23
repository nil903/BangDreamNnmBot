@echo off
cd /d C:\Users\yudong\Desktop\ai\pycharmCode\nnm_oneBot
echo Adding all changes...
git add .

echo.
set /p msg=Enter commit message: 
git commit -m "%msg%"

echo.
echo Pushing to GitHub...
git push

echo.
echo Done! Press any key to exit.
pause >nul