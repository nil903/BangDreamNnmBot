@echo off
setlocal

:: 项目名称和仓库地址
set REPO_NAME=BangDreamNnmBot
set REPO_URL=https://github.com/nil903/BangDreamNnmBot.git

:: 设置项目保存目录（你可以修改成你想放的位置）
set SAVE_DIR=C:\Users\Administrator\Desktop

cd /d %SAVE_DIR%

:: 检查项目是否已存在
if exist "%REPO_NAME%\" (
    echo 项目已存在，执行更新...
    cd "%REPO_NAME%"
    git pull
) else (
    echo 项目不存在，正在克隆仓库...
    git clone %REPO_URL%
)

echo.
echo 操作完成，按任意键退出...
pause >nul