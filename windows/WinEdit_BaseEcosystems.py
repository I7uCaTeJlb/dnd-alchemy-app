from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit,
                             QScrollArea, QPlainTextEdit, QMessageBox)

from scripts.CRUD import *

class EditWin(QWidget):
    closed = pyqtSignal()

    def __init__(self, name_win, db_table, main_win):
        super().__init__()
        self.setWindowTitle(name_win)
        self.resize(400, 300)
        self.delete_list = set()  # Список удаленных name

        self.db_table = db_table
        self.main_win = main_win

        self._init_ui()

    def _delete_row(self, row_widget):
        name = row_widget.layout().itemAt(1).widget().toPlainText()
        desc = row_widget.layout().itemAt(2).widget().toPlainText()

        OldValue = row_widget.layout().itemAt(1).widget().property("OldValue")

        if OldValue == None:
            if (name.isspace() or len(name) == 0) and (desc.isspace() or len(desc) == 0):
                row_widget.deleteLater()
                return
            else:
                text = f"Вы уверены, что хотите удалить {name} с следующим описанием: {desc}"
        else:
            text = f"Вы уверены, что хотите удалить {OldValue}?"

        reply = QMessageBox.question(
            self,
            "Подтверждение",
            f"{text}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No  # Кнопка по умолчанию
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.delete_list.add(OldValue)
            row_widget.deleteLater()

    def _create_row(self, name=None, decs=None):
        maxH = 40

        self.WD_row = QWidget()  # Виджет для макета
        self.HV_row = QHBoxLayout()  # Макет/строка со всеми заполняемыми полями

        self.buttonX = QPushButton("X")
        self.buttonX.clicked.connect(lambda *args, w=self.WD_row: self._delete_row(w))
        self.buttonX.setMaximumHeight(maxH)
        self.HV_row.addWidget(self.buttonX)

        self.txt = QPlainTextEdit()  # Текстовое поле для названия действия
        self.txt.setPlainText(name)  # Заполняем его
        self.txt.setProperty("OldValue", name)  # Делаем новое свойство для отсеживания изменений
        self.txt.setMaximumHeight(maxH)  # Задаем максимальную высоту
        self.txt.setMaximumWidth(200)  # Задаем максимальную ширину
        self.HV_row.addWidget(self.txt)  # Добавляем в строку

        self.desc = QPlainTextEdit()
        self.desc.setPlainText(decs)
        self.desc.setProperty("OldValue", decs)
        self.desc.setMaximumHeight(maxH)
        self.HV_row.addWidget(self.desc)

        self.WD_row.setLayout(self.HV_row)
        self.scroll_layout.addWidget(self.WD_row)

    def _save_list(self):
        NewActionList = {}
        rows_to_sync = []  # что нужно пометить как "уже сохранено"

        # Идём напрямую по scroll_layout
        for i in range(self.scroll_layout.count()):
            row_widget = self.scroll_layout.itemAt(i).widget()
            if row_widget is None:
                continue

            row = row_widget.layout()
            name_edit = row.itemAt(1).widget()
            desc_edit = row.itemAt(2).widget()

            name = name_edit.toPlainText()
            desc = desc_edit.toPlainText()
            old_name = name_edit.property("OldValue")

            # Пустая строка — игнорируем
            if not name.strip() and not desc.strip():
                continue

            if not desc.strip():
                QMessageBox.information(
                    self, "Добавьте описание",
                    f"Добавьте описание для {name}",
                    QMessageBox.StandardButton.Ok
                )
                self.scroll_area.ensureWidgetVisible(row_widget)
                return

            if not name.strip():
                QMessageBox.information(
                    self, "Дайте название описанию",
                    f"Следующее описание не имеет название: {desc}",
                    QMessageBox.StandardButton.Ok
                )
                self.scroll_area.ensureWidgetVisible(row_widget)
                return

            if name in NewActionList:
                QMessageBox.information(
                    self, "Название повторяется",
                    f"Название {name} уже было выше!",
                    QMessageBox.StandardButton.Ok
                )
                self.scroll_area.ensureWidgetVisible(row_widget)
                return

            old_desc = desc_edit.property("OldValue")

            if old_name != name or old_desc != desc:
                NewActionList[name] = (old_name, desc)
                rows_to_sync.append((row_widget, name, desc))

        ##### СОХРАНЕНИЕ ИЗМЕНЕНИЙ В БД #####
        with open_db() as cursor:

            for old_name in self.delete_list:
                if old_name is not None:  # защита от None
                    delete_of_name(cursor, self.db_table, old_name)

            columns, PK, _ = get_structure_table(cursor, self.db_table)
            for name, values in NewActionList.items():
                upsert(cursor, self.db_table, name, values,
                       columns=columns, primary_key=PK)

            # Только после успешной записи помечаем строки как существующие в БД
            for row_widget, name, desc in rows_to_sync:
                row_layout = row_widget.layout()
                name_edit = row_layout.itemAt(1).widget()
                desc_edit = row_layout.itemAt(2).widget()

                name_edit.setProperty("OldValue", name)
                desc_edit.setProperty("OldValue", desc)

        self.delete_list.clear()  # обработано — больше не удаляем

    def _init_ui(self):
        self.main_layout = QVBoxLayout(self)    # Главный макет, благодаря переданному self

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(scroll_content)
        self.scroll_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.scroll_area.setWidget(scroll_content)

        with open_db() as cursor:
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

class WinEditEcosystem(EditWin):
    def __init__(self, main_win):
        super().__init__("Редактирование экосистем", "Ecosystems", main_win)

    def _save_list(self):
        super()._save_list()
        self.main_win._UpdateListEcosystems()


class WinEditBase(EditWin):
    def __init__(self, main_win):
        super().__init__("Редактирование основ для АО", "Base", main_win)

    def _save_list(self):
        super()._save_list()
        self.main_win._UpdateCBBase()