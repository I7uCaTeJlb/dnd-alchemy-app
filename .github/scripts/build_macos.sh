#!/bin/bash
# Сборка для macOS
echo "Starting macOS build..."

# Параметры PyInstaller для macOS:
# --windowed: создает .app bundle
# --add-data: упаковать папки (формат для macOS/Linux: "источник:назначение" с двоеточием!)

pyinstaller --noconfirm \
    --windowed \
    --name "Alchemy-macOS" \
    --add-data "data:data" \
    --add-data "images:images" \
    --add-data "windows:windows" \
    --add-data "MyWidgets:MyWidgets" \
    --hidden-import PyQt6 \
    main.py

echo "macOS build completed successfully!"