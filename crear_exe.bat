@echo off
rem Arma el ejecutable: dist\Pokemanic\Pokemanic.exe (la carpeta dist\Pokemanic entera es el juego: se puede copiar o comprimir).
rem Hace falta una vez: python -m pip install pyinstaller
cd /d "%~dp0"
python herramientas.py icono
python -m PyInstaller --noconfirm --clean --windowed --name Pokemanic --icon assets\interfaz\icono.ico ^
    --add-data "assets;assets" --add-data "datos_pokeapi.json;." main.py
echo.
echo Listo: dist\Pokemanic\Pokemanic.exe
pause
