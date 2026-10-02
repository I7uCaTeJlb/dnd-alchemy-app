import sqlite3
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QScrollArea, QPlainTextEdit, QMessageBox, QComboBox,
                             QListWidget, QListWidgetItem, QListView)
from PyQt5.QtWidgets import QApplication, QMainWindow, QLineEdit, QVBoxLayout, QWidget
from PyQt5.QtCore import QRegularExpression
from PyQt5.QtGui import QRegularExpressionValidator
import json
from scripts.CRUD import *

from MyWidgets.CustomDropdown import CustomDropdown

class WinEditEfects(QWidget):
    closed = pyqtSignal()

    def __init__(self, main_win):
        super().__init__()
        self.setWindowTitle("Редактирование сиска эффектов")
        self.resize(400, 300)
        self.db = "./data/alchemy_database.db"
        self.db_table = "Effects"
        self.delete_list = set()                   # Список удаленных name
        self.main_win = main_win

        self._init_ui()

    def _get_other_data(self, table):
        connection = sqlite3.connect(self.db)
        cursor = connection.cursor()
        cursor.execute(f"SELECT name, desc FROM {table}")
        result = []
        for data in cursor.fetchall():
            result.append(data)
        connection.close()
        return result

    def _get_components(self, table):
        connection = sqlite3.connect(self.db)
        cursor = connection.cursor()
        cursor.execute(f"SELECT name, desc, rare FROM {table}")
        result = []
        abbreviations = {"Обычный":"[Об]", "Необычный":"[Не]",
                         "Редкий":"[Ре]", "Очень редкий":"[Ор]",
                         "Легендарный":"[Ле]", "Артефакт":"[Ар]"}
        for data in cursor.fetchall():
            result.append((data[0], data[1], abbreviations[data[2]]))
        connection.close()
        return result

    def _get_data(self):
        connection = sqlite3.connect(self.db)
        cursor = connection.cursor()
        cursor.execute(f"SELECT * FROM Effects")
        result = []
        for data in cursor.fetchall():
            result.append(data)
        connection.close()
        return result

    def _delete_row(self, row_widget):
        desc = row_widget.layout().itemAt(8).widget().toPlainText()

        StartName = row_widget.layout().itemAt(2).widget().property("OldValue")

        if StartName == None:
            if desc.isspace() or len(desc) == 0:
                row_widget.deleteLater()
                return
            else:
                text = f"Вы уверены, что хотите удалить эффект компонента с следующим описанием: {desc}"
        else:
            text = f"Вы уверены, что хотите удалить {StartName}?"

        reply = QMessageBox.question(
            self,
            "Подтверждение",
            f"{text}",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No  # Кнопка по умолчанию
        )

        if reply == QMessageBox.Yes:
            self.delete_list.add(StartName)
            row_widget.deleteLater()

    def _create_row(self, component = None, state = None, part = None,
                    cost = None, action = None, MT = None, AT = None, desc = None):
        maxH = 40

        self.WD_row = QWidget()                  # Виджет для макета
        self.HV_row = QHBoxLayout()              #

        self.buttonX = QPushButton("X")
        self.buttonX.clicked.connect(lambda *args, w=self.WD_row: self._delete_row(w))
        self.buttonX.setMaximumHeight(maxH)
        self.HV_row.addWidget(self.buttonX)

        self.buttonClone = QPushButton("⤷")
        #self.buttonX.clicked.connect(lambda *args, w=self.WD_row: self._delete_row(w))
        self.buttonClone.setMaximumHeight(maxH)
        self.HV_row.addWidget(self.buttonClone)

        self.CB_components = QComboBox()
        for i in range(len(self.components)):
            self.CB_components.addItem(f"{self.components[i][0]} {self.components[i][2]}")
            self.CB_components.setItemData(i, self.components[i][1], Qt.ToolTipRole)

        self.CB_components.setProperty("OldValue", component)
        self.CB_components.setMaximumHeight(maxH)                 # Задаем максимальную высоту
        self.CB_components.setMaximumWidth(200)                   # Задаем максимальную ширину
        self.HV_row.addWidget(self.CB_components)                 # Добавляем в строку

        self.CB_states = QComboBox()

        for i in range(len(self.states)):
            self.CB_states.addItem(self.states[i][0])
            self.CB_states.setItemData(i, self.states[i][1], Qt.ToolTipRole)

        self.CB_states.setMaximumHeight(maxH)                 # Задаем максимальную высоту
        self.CB_states.setMaximumWidth(200)                   # Задаем максимальную ширину
        self.HV_row.addWidget(self.CB_states)                 # Добавляем в строку

        regex = QRegularExpression(r"^[0-9]+(\.[0-9]+)?$")
        validator = QRegularExpressionValidator(regex)

        self.cost = QLineEdit()                          # Текстовое поле для названия действия
        self.cost.setText(cost)                     # Заполняем его
        self.cost.setMaximumHeight(maxH)                 # Задаем максимальную высоту
        self.cost.setMaximumWidth(200)                   # Задаем максимальную ширину
        self.cost.setValidator(validator)
        self.HV_row.addWidget(self.cost)                 # Добавляем в строку

        self.CB_actions = QComboBox()

        for i in range(len(self.actions)):
            self.CB_actions.addItem(self.actions[i][0])
            self.CB_actions.setItemData(i, self.actions[i][1], Qt.ToolTipRole)

        self.CB_actions.setMaximumHeight(maxH)                 # Задаем максимальную высоту
        self.CB_actions.setMaximumWidth(200)                   # Задаем максимальную ширину
        self.HV_row.addWidget(self.CB_actions)                 # Добавляем в строку

        self.CB_MTags = QComboBox()
        self.CB_MTags.addItems(self.MTags)
        self.CB_MTags.setMaximumHeight(maxH)  # Задаем максимальную высоту
        self.CB_MTags.setMaximumWidth(200)  # Задаем максимальную ширину
        self.HV_row.addWidget(self.CB_MTags)  # Добавляем в строку

        self.CB_ATags = CustomDropdown("Доп. эффект", self.ATags)

        # if ecosys != None:
        #     self.CB_ATags.setChecks(ecosys)
        #     self.CB_ATags.setProperty("OldValue", ecosys)
        # else:
        #     self.CB_ATags.setProperty("OldValue", [])

        self.HV_row.addWidget(self.CB_ATags)

        self.desc = QPlainTextEdit()
        self.desc.setMaximumHeight(maxH)
        self.HV_row.addWidget(self.desc)

        self.WD_row.setLayout(self.HV_row)
        self.scroll_layout.addWidget(self.WD_row)

    def _data_verification_1(self, SA, required_layout, index, *data):
        if all([x.isspace() or len(x) == 0 for x in data]):     # Если все необходимые поля пустые - игнорируем
            return False
        for x in data:                                # Если только часть полей пустые обращаем на это внимание
            if x.isspace() or len(x) == 0:
                _ = QMessageBox.information(
                    self,
                    "Заполните поле",
                    f"В одном из добавляемых объектов вы не заполнили необходимую информацию!",
                    QMessageBox.Ok
                )
                SA.ensureWidgetVisible(required_layout.itemAt(index).widget())
                return False

        return True

    def _save_list(self):
        SA = self.main_layout.itemAt(0).widget()
        required_layout = SA.widget().layout()
        NewActionList = {}
        for i in range(required_layout.count()):
            row = required_layout.itemAt(i).widget().layout()
            name = row.itemAt(2).widget().currentText()
            state = row.itemAt(3).widget().currentText()
            cost = row.itemAt(4).widget().text() #
            action = row.itemAt(5).widget().currentText()
            Mtag = row.itemAt(6).widget().currentText()
            Atag = row.itemAt(7).widget().getSelectedItems()
            desc = row.itemAt(8).widget().toPlainText() #

            if self._data_verification_1(SA, required_layout, i, cost, desc):
                if any([row.itemAt(k).widget().property("OldValue") != name for k in range(2, row.count())]):
                    if (name, state, action) in NewActionList.keys():
                        _ = QMessageBox.information(
                            self,
                            "Комбинация повторяется",
                            f"Комбинация {name} {state} {action} уже было!",
                            QMessageBox.Ok
                        )
                        SA.ensureWidgetVisible(required_layout.itemAt(i).widget())
                        return
                    else:
                        NewActionList[(name, state, action)] = (
                            (row.itemAt(2).widget().property("OldValue"),
                             row.itemAt(3).widget().property("OldValue"),
                             row.itemAt(5).widget().property("OldValue")),
                            cost, Mtag, Atag, desc)
        return
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
        self.scroll_layout.setAlignment(Qt.AlignTop)

        self.scroll_area.setWidget(scroll_content)
        self.components = self._get_components("Components")
        self.states = self._get_other_data("State")
        self.actions = self._get_other_data("Actions")
        self.MTags = ["Токсин", "Умение", "Усиление",  "Ослабление", "Модификатор", "Восстановление"]
        self.ATags = ["Загуститель", "Растворитель", "Стабилизатор", "Возмутитель", "Усилитель", "Потеря"]

        # for data in self._get_data():
        #     self._create_row(data[0], data[1], json.loads(data[2]), data[3])

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
