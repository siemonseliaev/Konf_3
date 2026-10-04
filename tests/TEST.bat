@echo off
chcp 65001 >nul
cd /d "%~dp0.."

python src\Konf_3.py --vfs vfs.csv --script tests\startup.txt

pause
