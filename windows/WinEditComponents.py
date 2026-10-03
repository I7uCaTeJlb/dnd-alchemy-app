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
        self.setWindowTitle("Редактирование сиска компонентов")
        self.resize(400, 300)
        self.db_table = "Components"
        self.delete_list = set()                   # Список удаленных name
        self.main_win = main_win

        self._init_ui()

    def _delete_row(self, row_widget):
        name = row_widget.layout().itemAt(1).widget().toPlainText()
        desc = row_widget.layout().itemAt(4).widget().toPlainText()

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

    def _create_row(self, name = None, rare = None, ecosys = None, decs = None):
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

        self.CB_rare = QComboBox()
        self.CB_rare.addItems(["Обычный", "Необычный", "Редкий", "Очень редкий", "Легендарный", "Артефакт"])
        self.CB_rare.setMaximumHeight(maxH)                 # Задаем максимальную высоту
        self.CB_rare.setMaximumWidth(200)                   # Задаем максимальную ширину
        self.HV_row.addWidget(self.CB_rare)                 # Добавляем в строку

        if rare != None:
            self.CB_rare.setCurrentText(rare)
            self.CB_rare.setProperty("OldValue", rare)
        else:
            self.CB_rare.setCurrentIndex(0)
            self.CB_rare.setProperty("OldValue", "Обычный")


        self.CB_ecsys = CustomDropdown("Экосистемы", self.list_ecosystems)

        if ecosys != None:
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

    def _save_list(self):

        SA = self.main_layout.itemAt(0).widget()
        required_layout = SA.widget().layout()

        NewActionList = {}

        for i in range(required_layout.count()):
            row = required_layout.itemAt(i).widget().layout()

            name = row.itemAt(1).widget().toPlainText()
            rare = row.itemAt(2).widget().currentText()
            ecsys = row.itemAt(3).widget().getSelectedItems()
            desc = row.itemAt(4).widget().toPlainText()

            if (name.isspace() or len(name) == 0) and (desc.isspace() or len(desc) == 0):
                continue
            #####################################
            for x in [desc, name, ecsys]:  # Если только часть полей пустые обращаем на это внимание
                if isinstance(x, str):
                    if not (x.isspace() or len(x) == 0): return True
                else:
                     if len(x) != 0: return True
                _ = QMessageBox.information(
                    self,
                    "Заполните поле",
                    f"В одном из добавляемых объектов вы не заполнили необходимую информацию!",
                    QMessageBox.StandardButton.Ok
                )
                SA.ensureWidgetVisible(required_layout.itemAt(i).widget())
                return False
            ####################################
            else:

                if any([row.itemAt(k).widget().property("OldValue") != name for k in range(1, row.count())]):
                    if name in NewActionList.keys():
                        _ = QMessageBox.information(
                            self,
                            "Название повторяется",
                            f"Название {name} уже было выше!",
                            QMessageBox.StandardButton.Ok
                        )
                        SA.ensureWidgetVisible(required_layout.itemAt(i).widget())
                        return
                    else:
                        NewActionList[name] = (row.itemAt(1).widget().property("OldValue"), rare, ecsys, desc)

        with open_db() as cursor:

            for name in self.delete_list: delete_of_name(cursor, self.db_table, name)

            columns, PK, _ = get_structure_table(cursor, self.db_table)

            for name, values in NewActionList.items(): upsert(cursor, self.db_table, name, values,
                                                              columns = columns, primary_key = PK)

    def _init_ui(self):
        self.main_layout = QVBoxLayout(self)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)

        scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(scroll_content)
        self.scroll_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.scroll_area.setWidget(scroll_content)

        with open_db() as cursor:
            self.list_ecosystems = [x[0] for x in read_all("Ecosystems", cursor)]
            for data in read_all(self.db_table, cursor):
                self._create_row(data[0], data[1], json.loads(data[2]), data[3])

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
