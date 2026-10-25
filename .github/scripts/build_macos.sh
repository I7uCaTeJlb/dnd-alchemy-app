#!/bin/bash
# Скрипт сборки macOS-версии приложения dnd-alchemy-app
# Используется в GitHub Actions (матричная сборка)

set -e  # Прерывать скрипт при любой ошибке

echo "========================================="
echo "Starting macOS build..."
echo "========================================="

# Параметры PyInstaller для macOS:
# --noconfirm    — не спрашивать подтверждение при перезаписи dist/
# --windowed     — создать .app bundle (без консольного окна)
# --name         — имя выходного файла/приложения
# --add-data     — упаковать ресурсы (формат macOS: "источник:назначение")
# --hidden-import — явно указать PyQt6, т.к. PyInstaller может её пропустить
# main.py        — точка входа приложения

pyinstaller --noconfirm \
    --windowed \
    --name "Alchemy-macOS" \
    --add-data "data:data" \
    --add-data "images:images" \
    --add-data "windows:windows" \
    --add-data "MyWidgets:MyWidgets" \
    --hidden-import PyQt6 \
    main.py

echo "Packaging .app bundle into zip..."

# Проверяем, что .app действительно создан
if [ ! -d "dist/Alchemy-macOS.app" ]; then
    echo "ERROR: dist/Alchemy-macOS.app not found!"
    exit 1
fi

# Переходим в dist/ и упаковываем
cd dist
zip -r Alchemy-macOS.zip Alchemy-macOS.app
cd ..