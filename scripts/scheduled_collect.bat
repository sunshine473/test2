@echo off
REM 素材采集定时任务脚本
REM 由 Windows 任务计划程序调用，每天自动执行一次

setlocal

set PROJECT_DIR=D:\0、学习\6、test_公众号
set PYTHON=C:\Users\dora111\AppData\Local\Programs\Python\Python312\python.exe
set LOG_DIR=%PROJECT_DIR%\logs
set LOG_FILE=%LOG_DIR%\collect_%date:~0,4%%date:~5,2%%date:~8,2%.log

REM 创建日志目录
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

echo ========================================>> "%LOG_FILE%"
echo [%date% %time%] 开始采集>> "%LOG_FILE%"
echo ========================================>> "%LOG_FILE%"

cd /d "%PROJECT_DIR%"
"%PYTHON%" src/collector/main.py >> "%LOG_FILE%" 2>&1

if %ERRORLEVEL% EQU 0 (
    echo [%date% %time%] 采集完成>> "%LOG_FILE%"
) else (
    echo [%date% %time%] 采集失败，退出码: %ERRORLEVEL%>> "%LOG_FILE%"
)

endlocal
