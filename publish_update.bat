@echo off
setlocal

cd /d D:\codex\options\option_wall_publish

echo.
echo ========================================
echo  Option Wall publish update
echo ========================================
echo.

where git >nul 2>nul
if errorlevel 1 goto NO_GIT

git rev-parse --is-inside-work-tree >nul 2>nul
if errorlevel 1 goto NOT_REPO

if not exist daily_data\index.csv goto NO_DATA

git add daily_data publish_app.py requirements.txt README.md start_publish_dashboard.bat publish_update.bat

git diff --cached --quiet
if not errorlevel 1 goto NO_CHANGES

for /f %%i in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd_HHmmss"') do set TS=%%i

git commit -m "update published option wall data %TS%"
if errorlevel 1 goto COMMIT_FAILED

git push
if errorlevel 1 goto PUSH_FAILED

echo.
echo [OK] Published data was pushed to GitHub.
echo Streamlit Cloud should update shortly.
goto END

:NO_GIT
echo.
echo [ERROR] Git was not found.
echo Please install Git for Windows first.
goto END

:NOT_REPO
echo.
echo [ERROR] This folder is not a Git repository:
echo D:\codex\options\option_wall_publish
echo.
echo First-time setup is required:
echo   git init
echo   git add .
echo   git commit -m "initial publish app"
echo   git branch -M main
echo   git remote add origin YOUR_GITHUB_REPO_URL
echo   git push -u origin main
goto END

:NO_DATA
echo.
echo [ERROR] daily_data\index.csv was not found.
echo Please run the main dashboard and click Save All first.
goto END

:NO_CHANGES
echo.
echo [INFO] No new changes to publish.
goto END

:COMMIT_FAILED
echo.
echo [ERROR] git commit failed. Please check the message above.
goto END

:PUSH_FAILED
echo.
echo [ERROR] git push failed. Please check remote repo, login, or network.
goto END

:END
echo.
pause
