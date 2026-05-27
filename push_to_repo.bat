@echo off
rem ==== Push Project to GitHub Repository ====
rem Set your GitHub username and repository URL
set REPO_URL=https://github.com/matheoglg/SiniestroSQR.git

rem OPTIONAL: set your name and email if not configured
git config user.name "Your Name"
git config user.email "you@example.com"

rem Add remote named "origin" if it does not exist
git remote get-url origin >nul 2>&1
if errorlevel 1 (
    echo Adding remote origin %REPO_URL%
    git remote add origin %REPO_URL%
) else (
    echo Remote origin already exists
)

rem Stage all changes
git add .

rem Commit changes (you can edit the message)
set /p COMMIT_MSG="Enter commit message: "
if "%COMMIT_MSG%"=="" set COMMIT_MSG=Update project files
git commit -m "%COMMIT_MSG%"

rem Push to the main branch (change if your default branch is different)
git push origin main --set-upstream

echo Done.
pause
