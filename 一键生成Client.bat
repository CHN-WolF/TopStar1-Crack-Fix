@echo off
chcp 936 >nul
cd /d "%~dp0"

if not exist "程序" mkdir "程序"
if not exist "程序\Client.exe" (
    echo 程序 文件夹里缺少未打补丁的 Client.exe。
    pause
    exit /b 1
)
if not exist "脚本\apply_client_patches.py" (
    echo 脚本 文件夹里缺少 apply_client_patches.py。
    pause
    exit /b 1
)

call :find_python
if defined PY_CMD goto :run_patch

for %%F in ("程序\python-*.exe") do (
    if not defined PY_CMD call :try_install "%%~fF"
)

if not defined PY_CMD (
    echo 找不到 Python 3。请安装 Python 3（或将官方安装包放入 程序 文件夹）后重新双击本文件。
    pause
    exit /b 1
)

:run_patch
echo 读取 程序\Client.exe，生成补丁后的 Client.exe 到当前文件夹。
%PY_CMD% "脚本\apply_client_patches.py" --write
if errorlevel 1 (
    echo 生成失败。若目标 Client.exe 正在运行或被占用，关掉后再试一次。
    pause
    exit /b 1
)
if not exist "Client.exe" (
    echo 生成失败：未找到生成的 Client.exe。
    pause
    exit /b 1
)
echo 已生成当前文件夹下的 Client.exe，请将其复制到游戏目录覆盖原文件。
pause
exit /b 0

:try_install
echo 未检测到 Python 3，正在静默安装: %~1
"%~1" /passive InstallAllUsers=0 PrependPath=1 Include_tcltk=1 Include_test=0
call :find_python
goto :eof

:find_python
set "PY_CMD="
for /f "delims=" %%I in ('where python 2^>nul') do (
    echo "%%I" | findstr /i "WindowsApps" >nul
    if errorlevel 1 (
        "%%I" -c "import sys; assert sys.version_info >= (3, 6)" >nul 2>&1
        if not errorlevel 1 (
            set "PY_CMD="%%I""
            goto :eof
        )
    )
)
for /d %%D in ("C:\Python3*") do (
    if exist "%%D\python.exe" (
        "%%D\python.exe" -c "import sys; assert sys.version_info >= (3, 6)" >nul 2>&1
        if not errorlevel 1 (
            set "PY_CMD="%%D\python.exe""
            goto :eof
        )
    )
)
for /d %%D in ("%LOCALAPPDATA%\Programs\Python\Python3*") do (
    if exist "%%D\python.exe" (
        "%%D\python.exe" -c "import sys; assert sys.version_info >= (3, 6)" >nul 2>&1
        if not errorlevel 1 (
            set "PY_CMD="%%D\python.exe""
            goto :eof
        )
    )
)
for /d %%D in ("%LOCALAPPDATA%\Python\pythoncore-3.*") do (
    if exist "%%D\python.exe" (
        "%%D\python.exe" -c "import sys; assert sys.version_info >= (3, 6)" >nul 2>&1
        if not errorlevel 1 (
            set "PY_CMD="%%D\python.exe""
            goto :eof
        )
    )
)
if exist "%LOCALAPPDATA%\Python\bin\python.exe" (
    "%LOCALAPPDATA%\Python\bin\python.exe" -c "import sys; assert sys.version_info >= (3, 6)" >nul 2>&1
    if not errorlevel 1 (
        set "PY_CMD="%LOCALAPPDATA%\Python\bin\python.exe""
        goto :eof
    )
)
for /d %%D in ("%ProgramFiles%\Python3*") do (
    if exist "%%D\python.exe" (
        "%%D\python.exe" -c "import sys; assert sys.version_info >= (3, 6)" >nul 2>&1
        if not errorlevel 1 (
            set "PY_CMD="%%D\python.exe""
            goto :eof
        )
    )
)
for /f "delims=" %%I in ('where py 2^>nul') do (
    echo "%%I" | findstr /i "WindowsApps" >nul
    if errorlevel 1 (
        "%%I" -3 -c "import sys; assert sys.version_info >= (3, 6)" >nul 2>&1
        if not errorlevel 1 (
            set "PY_CMD="%%I" -3"
            goto :eof
        )
    )
)
goto :eof
