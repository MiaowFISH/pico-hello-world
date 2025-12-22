@echo off
REM Pico部署助手 - 交互式菜单
chcp 65001 >nul
cls

:MENU
echo.
echo ==========================================
echo    Pico2W 舵机控制系统 - 部署助手
echo ==========================================
echo.
echo 请选择操作:
echo.
echo   1. 增量部署 (推荐)
echo   2. 查看部署状态
echo   3. 部署并清理旧文件
echo   4. 强制重新部署所有文件
echo   5. 检查需要清理的文件
echo   6. 退出
echo.
echo ==========================================
echo.

set /p choice="请输入选项 (1-6): "

if "%choice%"=="1" goto DEPLOY
if "%choice%"=="2" goto STATUS
if "%choice%"=="3" goto DEPLOY_CLEAN
if "%choice%"=="4" goto FORCE
if "%choice%"=="5" goto CHECK_CLEAN
if "%choice%"=="6" goto EXIT

echo.
echo 无效的选项，请重新选择
timeout /t 2 >nul
goto MENU

:DEPLOY
echo.
echo ========================================
echo 正在执行增量部署...
echo ========================================
python tools\deploy.py
if %errorlevel% neq 0 (
    echo.
    echo 部署失败！
    pause
    goto MENU
)
echo.
echo 部署成功！
pause
goto MENU

:STATUS
echo.
echo ========================================
echo 查看部署状态...
echo ========================================
python tools\deploy.py --status
pause
goto MENU

:DEPLOY_CLEAN
echo.
echo ========================================
echo 部署并清理旧文件...
echo ========================================
python tools\deploy.py --clean
if %errorlevel% neq 0 (
    echo.
    echo 部署失败！
    pause
    goto MENU
)
echo.
echo 部署和清理完成！
pause
goto MENU

:FORCE
echo.
echo ========================================
echo 强制重新部署所有文件...
echo ========================================
echo 警告: 这将重新复制所有文件
set /p confirm="确认执行? (Y/N): "
if /i not "%confirm%"=="Y" (
    echo 已取消
    timeout /t 2 >nul
    goto MENU
)
python tools\deploy.py --force
if %errorlevel% neq 0 (
    echo.
    echo 部署失败！
    pause
    goto MENU
)
echo.
echo 强制部署完成！
pause
goto MENU

:CHECK_CLEAN
echo.
echo ========================================
echo 检查需要清理的文件...
echo ========================================
python tools\deploy.py --check-clean
pause
goto MENU

:EXIT
echo.
echo 再见！
timeout /t 1 >nul
exit /b 0
