@echo off
cd /d "C:\Users\Administrator\Desktop\JARVIS"
call "C:\Users\Administrator\Desktop\JARVIS\venv\Scripts\activate.bat"
start "" /min pythonw "C:\Users\Administrator\Desktop\JARVIS\main.py" --mode hybrid
