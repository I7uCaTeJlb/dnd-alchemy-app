import sys
import os
import requests
import subprocess
import webbrowser
from PyQt6.QtWidgets import QMessageBox, QApplication

# Текущая версия приложения (будем обновлять её при новых релизах)
APP_VERSION = "1.0.2"
GITHUB_REPO = "I7uCaTeJlb/dnd-alchemy-app"

def get_latest_release_info():
    """Получает информацию о последнем релизе с GitHub"""
    url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
    try:
        response = requests.get(url, timeout=10)  # Увеличили таймаут до 10 секунд
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return None


def check_for_updates():
    """Проверяет наличие обновлений и предлагает пользователю скачать"""
    release_info = get_latest_release_info()

    if not release_info:
        return  # Не удалось проверить, просто продолжаем работу

    latest_version = release_info.get("tag_name", "v0.0.0").lstrip("v")

    # Сравниваем версии (простое строковое сравнение работает для формата X.Y.Z)
    if latest_version > APP_VERSION:
        app_name = release_info.get("name", "Новая версия")
        release_url = release_info.get("html_url", f"https://github.com/{GITHUB_REPO}/releases")

        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setWindowTitle("Доступно обновление")
        msg.setText(f"Доступна новая версия: {app_name}\n\nВаша текущая версия: {APP_VERSION}")
        msg.setInformativeText("Хотите перейти на страницу загрузки для обновления?")
        msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msg.setDefaultButton(QMessageBox.StandardButton.Yes)

        reply = msg.exec()

        if reply == QMessageBox.StandardButton.Yes:
            # Открываем страницу релизов в браузере
            webbrowser.open(release_url)


def run_updater_check():
    """Обёртка для безопасного запуска проверки (требует активного QApplication)"""
    # Проверка обновлений должна происходить после инициализации QApplication
    # Мы вызовем эту функцию из main.py
    check_for_updates()