from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QScrollArea, QPlainTextEdit, QMessageBox, QComboBox)
import json
from scripts.CRUD import *

from MyWidgets.CustomDropdown import CustomDropdown

class WinEditComponents(QWidget):
    closed = pyqtSignal()

    def __init__(self, main_win):
        super().__init__()
        self.setWindowTitle("Редактирование списка компонентов")
        self.resize(400, 300)
        self.db_table = "Components"
        self.delete_list = set()
        self.main_win = main_win

        self._init_ui()

    def _delete_row(self, row_widget):
        row_layout = row_widget.layout()
        name_edit = row_layout.itemAt(1).widget()
        desc_edit = row_layout.itemAt(4).widget()

        name = name_edit.toPlainText()
        desc = desc_edit.toPlainText()
        old_name = name_edit.property("OldValue")

        # === Строки, которой в БД ещё нет ===
        if old_name is None:
            if not name.strip() and not desc.strip():
                self._remove_row(row_widget)
                return

            reply = QMessageBox.question(
                self,
                "Подтверждение",
                f"Удалить новую запись «{name}»?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                # В delete_list ничего не добавляем: в БД её ещё нет
                self._remove_row(row_widget)
            return

        # === Строки, которая есть в БД ===
        reply = QMessageBox.question(
            self,
            "Подтверждение",
            f"Вы уверены, что хотите удалить {old_name}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.delete_list.add(old_name)
            self._remove_row(row_widget)

    def _remove_row(self, row_widget):
        """Убирает строку из макета сразу, чтобы индексы не съехали."""
        self.scroll_layout.removeWidget(row_widget)
        row_widget.setParent(None)
        row_widget.deleteLater()

    def _create_row(self, name=None, rare=None, ecosys=None, decs=None):
        maxH = 40

        self.WD_row = QWidget()
        self.HV_row = QHBoxLayout()

        self.buttonX = QPushButton("X")
        self.buttonX.clicked.connect(lambda *args, w=self.WD_row: self._delete_row(w))
        self.buttonX.setMaximumHeight(maxH)
        self.HV_row.addWidget(self.buttonX)

        self.txt = QPlainTextEdit()
        self.txt.setPlainText(name)
        self.txt.setProperty("OldValue", name)
        self.txt.setMaximumHeight(maxH)
        self.txt.setMaximumWidth(200)
        self.HV_row.addWidget(self.txt)

        self.CB_rare = QComboBox()
        self.CB_rare.addItems(["Обычный", "Необычный", "Редкий", "Очень редкий", "Легендарный", "Артефакт"])
        self.CB_rare.setMaximumHeight(maxH)
        self.CB_rare.setMaximumWidth(200)
        self.HV_row.addWidget(self.CB_rare)

        if rare is not None:
            self.CB_rare.setCurrentText(rare)
            self.CB_rare.setProperty("OldValue", rare)
        else:
            self.CB_rare.setCurrentIndex(0)
            self.CB_rare.setProperty("OldValue", "Обычный")

        self.CB_ecsys = CustomDropdown("Экосистемы", self.list_ecosystems)

        if ecosys is not None:
            self.CB_ecsys.setChecks(ecosys)
            self.CB_ecsys.setProperty("OldValue", ecosys)
        else:
            self.CB_ecsys.setProperty("OldValue", [])

        self.HV_row.addWidget(self.CB_ecsys)

        self.desc = QPlainTextEdit()
        self.desc.setPlainText(decs)
        self.desc.setProperty("OldValue", decs)
        self.desc.setMaximumHeight(maxH)
        self.HV_row.addWidget(self.desc)

        self.WD_row.setLayout(self.HV_row)
        self.scroll_layout.addWidget(self.WD_row)

    def _sync_row_old_values(self, row_widget, name, rare, ecsys, desc):
        """Вызывается ПОСЛЕ успешной записи в БД."""
        row_layout = row_widget.layout()
        name_edit = row_layout.itemAt(1).widget()
        rare_cb = row_layout.itemAt(2).widget()
        ecsys_dd = row_layout.itemAt(3).widget()
        desc_edit = row_layout.itemAt(4).widget()

        # Теперь программа знает: эта запись уже в БД под именем name
        name_edit.setProperty("OldValue", name)
        rare_cb.setProperty("OldValue", rare)
        ecsys_dd.setProperty("OldValue", ecsys)
        desc_edit.setProperty("OldValue", desc)

    def _save_list(self):
        NewActionList = {}
        rows_to_sync = []

        for i in range(self.scroll_layout.count()):
            row_widget = self.scroll_layout.itemAt(i).widget()
            if row_widget is None:
                continue

            row = row_widget.layout()
            name_edit = row.itemAt(1).widget()
            rare_cb = row.itemAt(2).widget()
            ecsys_dd = row.itemAt(3).widget()
            desc_edit = row.itemAt(4).widget()

            name = name_edit.toPlainText()
            rare = rare_cb.currentText()
            ecsys = ecsys_dd.getSelectedItems()
            desc = desc_edit.toPlainText()

            old_name = name_edit.property("OldValue")
            old_rare = rare_cb.property("OldValue")
            old_ecsys = ecsys_dd.property("OldValue")
            old_desc = desc_edit.property("OldValue")

            # Пустая строка — игнорируем
            if not name.strip() and not desc.strip():
                continue

            # Проверяем заполненность
            for x in [desc, name, ecsys]:
                is_empty = False
                if isinstance(x, str):
                    is_empty = x.isspace() or len(x) == 0
                elif isinstance(x, list):
                    is_empty = len(x) == 0

                if is_empty:
                    QMessageBox.information(
                        self,
                        "Заполните поле",
                        "В одном из добавляемых объектов вы не заполнили необходимую информацию!",
                        QMessageBox.StandardButton.Ok
                    )
                    self.scroll_area.ensureWidgetVisible(row_widget)
                    return

            if name in NewActionList:
                QMessageBox.information(
                    self,
                    "Название повторяется",
                    f"Название {name} уже было выше!",
                    QMessageBox.StandardButton.Ok
                )
                self.scroll_area.ensureWidgetVisible(row_widget)
                return

            # Проверяем изменения
            has_changes = (
                old_name != name or
                old_rare != rare or
                old_ecsys != ecsys or
                old_desc != desc
            )

            if has_changes:
                NewActionList[name] = (old_name, rare, ecsys, desc)
                rows_to_sync.append((row_widget, name, rare, ecsys, desc))

        ##### СОХРАНЕНИЕ ИЗМЕНЕНИЙ В БД #####
        with open_db() as cursor:
            for old_name in self.delete_list:
                if old_name is not None:
                    delete_of_name(cursor, self.db_table, old_name)

            columns, PK, _ = get_structure_table(cursor, self.db_table)
            for name, values in NewActionList.items():
                upsert(cursor, self.db_table, name, values,
                       columns=columns, primary_key=PK)

            # Только после успешной записи помечаем строки как существующие в БД
            for row_widget, name, rare, ecsys, desc in rows_to_sync:
                self._sync_row_old_values(row_widget, name, rare, ecsys, desc)

        self.delete_list.clear()
        # self.main_win.stack.setCurrentIndex(0)

    def _init_ui(self):
        self.main_layout = QVBoxLayout(self)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)

        scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(scroll_content)
        self.scroll_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.scroll_area.setWidget(scroll_content)

        with open_db() as cursor:
            self.list_ecosystems = [x[0] for x in read_all(cursor, "Ecosystems")]
            for data in read_all(cursor, self.db_table):
                self._create_row(*data)

        controls = QHBoxLayout()

        self.B_NewAcrion = QPushButton("Создать новое")
        self.B_NewAcrion.clicked.connect(lambda: self._create_row())
        self.B_Save = QPushButton("Сохранить изменения")
        self.B_Save.clicked.connect(self._save_list)
        self.B_Close = QPushButton("Отмена | Закрыть")
        self.B_Close.clicked.connect(lambda: self.main_win.stack.setCurrentIndex(0))

        controls.addWidget(self.B_NewAcrion)
        controls.addWidget(self.B_Save)
        controls.addWidget(self.B_Close)

        self.main_layout.addWidget(self.scroll_area)
        self.main_layout.addLayout(controls)

    def closeEvent(self, event):
        self.closed.emit()
        self.main_win._CloseSecondWin(self)
        super().closeEvent(event)