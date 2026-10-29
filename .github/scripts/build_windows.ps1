Write-Host "Starting Windows build..."

# Параметры PyInstaller:
# --onefile: один исполняемый файл
# --windowed: скрыть консольное окно (важно для GUI)
# --add-data: упаковать папки с ресурсами (формат для Windows: "источник;назначение")
# --hidden-import: явно указываем PyQt6 (или PyQt5, если используешь её), чтобы PyInstaller её не пропустил

pyinstaller --noconfirm `
    --onefile `
    --windowed `
    --name "Alchemy-Windows" `
    --add-data "data;data" `
    --add-data "images;images" `
    --add-data "windows;windows" `
    --add-data "MyWidgets;MyWidgets" `
    --hidden-import PyQt6 `
    main.py

Write-Host "Windows build completed successfully!"