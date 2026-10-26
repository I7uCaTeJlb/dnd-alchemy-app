# ============================================================
# Dockerfile для сборки Linux-версии dnd-alchemy-app
# Используется в GitHub Actions (Этап 2: CI)
# ============================================================
# Обеспечивает воспроизводимость сборки:
# - Фиксированная версия Python (3.13)
# - Фиксированные системные библиотеки для PyQt6
# - Изоляция от обновлений GitHub Actions runner'ов
# ============================================================

FROM python:3.13-slim

# Метаданные образа
LABEL maintainer="l7uCaTeJlb"
LABEL description="Build environment for dnd-alchemy-app (Linux)"

# Устанавливаем системные зависимости, необходимые для работы PyQt6
# и сборки через PyInstaller
# ВАЖНО: libgl1-mesa-glx заменён на libgl1 и libegl1, так как он устарел в новых Debian
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libegl1 \
    libxkbcommon0 \
    libxcb-xinerama0 \
    libxcb-cursor0 \
    libx11-xcb1 \
    libasound2 \
    libnss3 \
    libatk-bridge2.0-0 \
    libgtk-3-0 \
    libsm6 \
    libice6 \
    zip \
    && rm -rf /var/lib/apt/lists/*

# Рабочая директория внутри контейнера
WORKDIR /app

# Сначала копируем только requirements.txt — это оптимизирует кэширование слоёв Docker
COPY requirements.txt .

# Устанавливаем Python-зависимости и PyInstaller
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt pyinstaller

# Копируем весь исходный код проекта
COPY . .

# Команда по умолчанию — запуск скрипта сборки Linux
CMD ["bash", ".github/scripts/build_linux.sh"]