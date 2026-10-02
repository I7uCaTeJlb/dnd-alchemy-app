from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QScrollArea, QPlainTextEdit, QMessageBox, QStackedWidget)
from scripts.CRUD import *

class EditWin(QWidget):
    closed = pyqtSignal()

    def __init__(self, name_win, db_table, main_win):
        super().__init__()
        self.setWindowTitle(name_win)
        self.resize(400, 300)
        self.delete_list = set()                   # Список удаленных name

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
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No  # Кнопка по умолчанию
        )

        if reply == QMessageBox.Yes:
            self.delete_list.add(OldValue)
            row_widget.deleteLater()

    def _create_row(self, name = None, decs = None):
        maxH = 40

        self.WD_row = QWidget()                  # Виджет для макета
        self.HV_row = QHBoxLayout()              #

        self.buttonX = QPushButton("X")
        self.buttonX.clicked.connect(lambda *args, w=self.WD_row: self._delete_row(w))
        self.buttonX.setMaximumHeight(maxH)
        self.HV_row.addWidget(self.buttonX)

        self.txt = QPlainTextEdit()                     # Текстовое поле для названия действия
        self.txt.setPlainText(name)                     # Заполняем его
        self.txt.setProperty("OldValue", name)         # Делаем новое свойство для отсеживания изменений
        self.txt.setMaximumHeight(maxH)                 # Задаем максимальную высоту
        self.txt.setMaximumWidth(200)                   # Задаем максимальную ширину
        self.HV_row.addWidget(self.txt)                 # Добавляем в строку

        self.desc = QPlainTextEdit()
        self.desc.setPlainText(decs)
        self.desc.setProperty("OldValue", decs)
        self.desc.setMaximumHeight(maxH)
        self.HV_row.addWidget(self.desc)

        if self.db_table == "State":
            self.BT = QPushButton("Доп. настройки")
            self.BT.setProperty("OldValue", decs)
            self.BT.setMaximumHeight(maxH)
            self.HV_row.addWidget(self.BT)

        self.WD_row.setLayout(self.HV_row)
        self.scroll_layout.addWidget(self.WD_row)

    def _save_list(self):

        SA = self.main_layout.itemAt(0).widget()
        required_layout = SA.widget().layout()

        NewActionList = {}

        for i in range(required_layout.count()):
            row = required_layout.itemAt(i).widget().layout()
            name = row.itemAt(1).widget().toPlainText()
            desc = row.itemAt(2).widget().toPlainText()

            if (name.isspace() or len(name) == 0) and (desc.isspace() or len(desc) == 0):
                continue
            elif desc.isspace() or len(desc) == 0:
                _ = QMessageBox.information(
                    self,
                    "Добавьте описание",
                    f"Добавьте описание для {name}",
                    QMessageBox.Ok
                )
                SA.ensureWidgetVisible(required_layout.itemAt(i).widget())
                return

            elif name.isspace() or len(name) == 0:
                _ = QMessageBox.information(
                    self,
                    "Дайте название описанию",
                    f"Следующее описание не имеет название: {desc}",
                    QMessageBox.Ok
                )
                SA.ensureWidgetVisible(required_layout.itemAt(i).widget())
                return
            else:
                if (row.itemAt(1).widget().property("OldValue") != name) \
                    or (row.itemAt(2).widget().property("OldValue") != desc):

                    if name in NewActionList.keys():
                        _ = QMessageBox.information(
                            self,
                            "Название повторяется",
                            f"Название {name} уже было выше!",
                            QMessageBox.Ok
                        )
                        SA.ensureWidgetVisible(required_layout.itemAt(i).widget())
                        return
                    else:
                        NewActionList[name] = (row.itemAt(1).widget().property("OldValue"), desc)

        with open_db() as cursor:

            for name in self.delete_list: delete_of_name(cursor, self.db_table, name)

            columns, PK, _ = get_structure_table(cursor, self.db_table)
            for name, values in NewActionList.items(): upsert(cursor, self.db_table, name, values,
                                                              columns = columns, primary_key = PK)

    def _init_ui(self):
        self.main_layout = QVBoxLayout(self)

        #self.stack = QStackedWidget()           # Стек для подмены содержимого

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)

        scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(scroll_content)
        self.scroll_layout.setAlignment(Qt.AlignTop)

        self.scroll_area.setWidget(scroll_content)

        with open_db() as cursor:
            for data in read_all(self.db_table, cursor):

                self._create_row(data[0], data[1])

        controls = QHBoxLayout()

        self.B_NewAcrion = QPushButton("Создать новое")
        self.B_NewAcrion.clicked.connect(lambda: self._create_row())
        self.B_Save      = QPushButton("Сохранить изменения")
        self.B_Save.clicked.connect(self._save_list)
        self.B_Close     = QPushButton("Отмена")

        controls.addWidget(self.B_NewAcrion)
        controls.addWidget(self.B_Save)
        controls.addWidget(self.B_Close)

        self.main_layout.addWidget(self.scroll_area)
        self.main_layout.addLayout(controls)

    def closeEvent(self, event):
        self.closed.emit()

        self.main_win._CloseSecondWin(self)

        super().closeEvent(event)

class AdditionalProperties(QWidget):
    pass

class WinEditActions(EditWin):
    def __init__(self, main_win):
        super().__init__("Редактирование действий", "Actions", main_win)

class WinEditState(EditWin):
    def __init__(self, main_win):
        super().__init__("Редактирование состояний компонентов", "State", main_win)

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