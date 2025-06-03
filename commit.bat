@echo off

:: Ask for the commit description
set /p commitMsg="Enter commit message: "

:: Run git commands
git add .
git commit -S -m "%commitMsg%"
git push origin main