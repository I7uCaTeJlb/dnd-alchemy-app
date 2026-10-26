# DnD Alchemy App — Алхимическая Мастерская для D&D

**Кросс-платформенное десктопное приложение для мастеров Dungeons & Dragons**, позволяющее управлять алхимическими рецептами, компонентами, эффектами и экосистемами в рамках настольной ролевой игры.

![Python](https://img.shields.io/badge/Python-3.13-blue?logo=python)
![PyQt6](https://img.shields.io/badge/PyQt6-6.11-green?logo=qt)
![License](https://img.shields.io/badge/License-MIT-yellow)
![Release](https://img.shields.io/github/v/release/l7uCaTeJlb/dnd-alchemy-app?label=latest%20release)

---

##  Возможности

- 🧪 **Управление алхимической базой данных**: компоненты, основы, экосистемы, эффекты, действия, состояния
-  **Фильтрация и поиск** ингредиентов по редкости, типу эффекта, экосистеме
-  **Редакторы данных** для каждого типа сущностей (CRUD-операции)
- 🎨 **Кастомизируемый интерфейс** через QSS-стили
- 🔄 **Автоматические обновления** через GitHub Releases API
- 🛡️ **Мониторинг стабильности** через Sentry
- 🔐 **Цифровая подпись кода** (Windows + macOS)
- 🐳 **Воспроизводимая сборка** Linux-версии в Docker

---

## ️ Архитектура проекта

```text
dnd-alchemy-app/
├── .github/
│   ├── docker/
│   │   ├── Dockerfile              # Изолированная среда для Linux-сборки
│   │   └── .dockerignore
│   ├── scripts/
│   │   ├── build_windows.ps1       # Скрипт сборки Windows
│   │   ├── build_macos.sh          # Скрипт сборки macOS
│   │   ├── build_linux.sh          # Скрипт сборки Linux
│   │   ├── sign_windows.ps1        # Подпись Windows через signtool
│   │   ── sign_macos.sh           # Подпись macOS через codesign
│   └── workflows/
│       └── build.yml               # GitHub Actions CI/CD пайплайн
├── data/
│   ├── alchemy_database.db         # SQLite база данных
│   └── styles.qss                  # Стили интерфейса
├── images/                         # Графические ресурсы
├── scripts/
│   └── CRUD.py                     # CRUD-операции с БД
├── windows/                        # Модули окон приложения
│   ├── WinEdit_ActionState.py
│   ├── WinEdit_BaseEcosystems.py
│   ├── WinEditComponents.py
│   └── WinEditEfects.py
├── MyWidgets/                      # Кастомные виджеты
├── main.py                         # Точка входа + Sentry + Updater
── updater.py                      # Модуль автообновлений
├── requirements.txt                # Python-зависимости
└── README.md
