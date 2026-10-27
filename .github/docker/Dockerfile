FROM python:3.13-slim

LABEL maintainer="l7uCaTeJlb"
LABEL description="Build environment for dnd-alchemy-app (Linux)"

RUN apt-get update && apt-get install -y --no-install-recommends \
    binutils \
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

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt pyinstaller

COPY . .

CMD ["bash", ".github/scripts/build_linux.sh"]