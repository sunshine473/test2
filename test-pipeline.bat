@echo off
REM 本地测试全自动流水线
REM 用法: test-pipeline.bat

echo ==========================================
echo   本地测试全自动流水线
echo ==========================================
echo.

REM 检查环境变量
echo 检查环境变量...
if "%ANTHROPIC_API_KEY%"=="" (
    echo ❌ 缺少 ANTHROPIC_API_KEY
    exit /b 1
)

if "%TELEGRAM_BOT_TOKEN%"=="" (
    echo ⚠️  缺少 TELEGRAM_BOT_TOKEN（可选）
)

echo ✅ 环境变量检查通过
echo.

REM 运行流水线
echo 开始执行流水线...
echo.

cd src

python -m pipeline.main ^
    --auto ^
    --sources hn,github ^
    --direction tech_ai ^
    --no-cards ^
    --platforms wechat

echo.
echo ==========================================
echo   流水线执行完成
echo ==========================================
echo.

REM 显示状态
echo 流水线状态:
python -m pipeline.main --status

echo.
echo 查看生成的草稿:
dir /b /o-d ..\content\drafts\*.md | findstr /r "^2026"

cd ..
