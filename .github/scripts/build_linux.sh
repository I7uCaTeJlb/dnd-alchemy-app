#!/bin/bash
set -e

echo "Starting Linux build..."

# Параметры PyInstaller для Linux:
# --onefile: один исполняемый файл
# --add-data: формат "источник:назначение" (в Linux используется двоеточие)

pyinstaller --noconfirm \
    --onefile \
    --name "Alchemy-Linux" \
    --add-data "data:data" \
    --add-data "images:images" \
    --add-data "windows:windows" \
    --add-data "MyWidgets:MyWidgets" \
    --hidden-import PyQt6 \
    main.py

echo "Linux build completed successfully!"