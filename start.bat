@echo off
chcp 65001 >nul
echo ==========================================
echo   Social Content Creator Platform
echo ==========================================
echo.

echo [1/4] Checking environment...
node --version >nul 2>&1
if errorlevel 1 (
    echo [Error] Node.js not installed. Please install Node.js 20+
    pause
    exit /b 1
)
echo [OK] Node.js installed

echo.
echo [2/4] Starting database services...
docker-compose up -d postgres redis mongodb
if errorlevel 1 (
    echo [Warning] Docker failed to start. Please start database manually.
)
timeout /t 5 /nobreak >nul
echo [OK] Database services started

echo.
echo [3/4] Starting backend service...
start "Backend" cmd /k "cd src\backend && npm install && npm run dev"

echo.
echo [4/4] Starting frontend service...
start "Frontend" cmd /k "cd src\frontend && npm install && npm run dev"

echo.
echo ==========================================
echo   Services starting...
echo ==========================================
echo.
echo Please wait for installation to complete.
echo Then visit:
echo   Frontend: http://localhost:5173
echo   Backend: http://localhost:3000
echo.
pause
start http://localhost:5173
