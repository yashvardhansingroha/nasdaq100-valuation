@echo off
cd /d "%~dp0"
python main.py --mode full
echo Pipeline finished at %date% %time%
