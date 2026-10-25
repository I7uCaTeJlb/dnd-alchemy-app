from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QPushButton,
                             QListWidget, QListWidgetItem, QFrame)
from PyQt6.QtCore import Qt, pyqtSignal


class CustomDropdown(QWidget):
    """Кастомный выпадающий список с любым содержимым"""

    itemSelected = pyqtSignal(str)

    def __init__(self, name, items=None):
        super().__init__()
        self.items = items or []
        self.selected_items = []
        self.is_open = False
        self.name = str(name)

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Кнопка для открытия/закрытия
        self.button = QPushButton(self.name)
        self.button.clicked.connect(self.toggle_dropdown)

        layout.addWidget(self.button)

        # Выпадающий фрейм (изначально скрыт)
        self.dropdown_frame = QFrame()
        # В PyQt6: Shape и Shadow — отдельные перечисления
        self.dropdown_frame.setFrameStyle(
            QFrame.Shape.StyledPanel | QFrame.Shadow.Raised
        )
        self.dropdown_frame.setMinimumHeight(120)

        # Список с чекбоксами
        self.listWidget = QListWidget()
        self.listWidget.setFrameStyle(QFrame.Shape.NoFrame)

        for item in self.items:
            list_item = QListWidgetItem(item)
            # В PyQt6: ItemIsUserCheckable → ItemFlag.ItemIsUserCheckable
            list_item.setFlags(list_item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            # В PyQt6: Unchecked → CheckState.Unchecked
            list_item.setCheckState(Qt.CheckState.Unchecked)
            self.listWidget.addItem(list_item)

        self.listWidget.itemChanged.connect(self.on_item_changed)

        frame_layout = QVBoxLayout(self.dropdown_frame)
        frame_layout.setContentsMargins(5, 5, 5, 5)
        frame_layout.addWidget(self.listWidget)

        layout.addWidget(self.dropdown_frame)
        self.dropdown_frame.hide()

        # Устанавливаем фиксированную высоту для dropdown
        self.dropdown_frame.setMaximumHeight(200)

    def toggle_dropdown(self):
        """Открыть/закрыть выпадающий список"""
        self.is_open = not self.is_open
        if self.is_open:
            self.dropdown_frame.show()
        else:
            self.dropdown_frame.hide()

    def on_item_changed(self, item):
        """Обработка изменения выбора"""
        self.selected_items = []
        for i in range(self.listWidget.count()):
            list_item = self.listWidget.item(i)
            # В PyQt6: Checked → CheckState.Checked
            if list_item.checkState() == Qt.CheckState.Checked:
                self.selected_items.append(list_item.text())

        self.itemSelected.emit(', '.join(self.selected_items))

    def getSelectedItems(self):
        """Получить выбранные элементы"""
        return self.selected_items.copy()

    def setItems(self, items):
        """Установить новые элементы"""
        self.items = items
        self.listWidget.clear()
        for item in items:
            list_item = QListWidgetItem(item)
            list_item.setFlags(list_item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            list_item.setCheckState(Qt.CheckState.Unchecked)
            self.listWidget.addItem(list_item)

    def setChecks(self, items):
        for i in range(self.listWidget.count()):
            CB = self.listWidget.item(i)
            if CB.text() in items:
                CB.setCheckState(Qt.CheckState.Checked)
            else:
                CB.setCheckState(Qt.CheckState.Unchecked)


class CustomDropdown2(CustomDropdown):
    """Кастомный выпадающий список с любым содержимым"""

    def __init__(self, name, items=None):
        super().__init__(name, items)

    def setItems(self, items, main_items):
        """Установить новые элементы"""
        self.items = items
        self.main_items = main_items
        self.listWidget.clear()

        for item in items:
            list_item = QListWidgetItem(item)
            list_item.setFlags(list_item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            list_item.setCheckState(Qt.CheckState.Unchecked)
            self.listWidget.addItem(list_item)