from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit,
                             QScrollArea, QPlainTextEdit, QMessageBox, QStackedWidget,
                             QRadioButton, QLayout, QGridLayout, QComboBox)
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

    def _fun_button_option(self, options):      # Функция для кнопки "+ опции"
        if options != None:
            pass

        self.stack.setCurrentIndex(1)

    def _Function1(self, check: bool, dependency: QLayout):    # Тип описания опции - при выборе разблокировать варианты
        for i in range(0, dependency.count(), 2):
            WD = dependency.itemAt(i).widget()
            if WD == None: continue
            if check:
                WD.setStyleSheet("color: rgb(0, 0, 0);")
                if WD.isChecked(): dependency.itemAt(i+1).widget().show()
            else:
                dependency.itemAt(i+1).widget().hide()
                WD.setStyleSheet("color: rgb(127, 127, 127);")
            WD.setEnabled(check)

    def _create_option(self, name = None, data = None):
        maxH = 40

        self.WD_option = QWidget()          # Виджет для макета
        self.VL_option = QVBoxLayout()      # Макет/строка со всеми заполняемыми полями

        self.Layout1 = QHBoxLayout()
        self.Layout2 = QGridLayout()

        self.buttonX = QPushButton("X")
        self.buttonX.setMaximumWidth(100)
        #self.buttonX.clicked.connect(lambda *args, w=self.WD_row: self._delete_row(w))
        self.buttonX.setMaximumHeight(maxH)
        self.Layout1.addWidget(self.buttonX)

        self.name = QLineEdit()                          # Текстовое поле для названия действия
        self.name.setText(name)                          # Заполняем его
        self.name.setMaximumHeight(maxH)                 # Задаем максимальную высоту
        self.Layout1.addWidget(self.name)                # Добавляем в строку

        self.RB_text_desc = QRadioButton("Текстовое описание")
        self.RB_text_desc.setProperty("TypeOption", ["text", None])
        self.RB_text_desc.setChecked(True)
        self.Layout2.addWidget(self.RB_text_desc, 0, 0)

        list_option = ["Выбор одного", "Выбор нескольких"]
        list_tags   = ["combobox", "multiselect"]
        for i in range(len(list_option)):
            self.HL_CBDV = QHBoxLayout()
            self.RB_combobox_desc = QRadioButton(list_option[i])
            self.RB_combobox_desc.setProperty("TypeOption", [list_tags[i], None])
            self.RB_combobox_desc.toggled.connect(lambda check, layout = self.HL_CBDV:
                                                  self._Function1(check, layout))

            self.RB_CBDV1 = QRadioButton("Из таблиц механики")
            self.CB_CBDV1 = QComboBox()
            self.CB_CBDV1.addItems(["Состояния", "Действия", "База", "Экосистемы"])
            self.RB_CBDV1.toggled.connect(lambda *_, rbtn=self.RB_combobox_desc,
                                                 text = self.CB_CBDV1.currentText(), j=i:
                                          rbtn.setProperty("TypeOption", [list_tags[j], text, 0]))
            self.CB_CBDV1.currentTextChanged.connect(lambda *txt, rbtn = self.RB_combobox_desc, j = i:
                                                     rbtn.setProperty("TypeOption", [list_tags[j], *txt]))

            self.CB_CBDV1.hide()
            self.RB_CBDV1.toggled.connect(lambda check, widget=self.CB_CBDV1:
                                          widget.show() if check else widget.hide())

            self.RB_CBDV2 = QRadioButton("Собстенный список")
            self.list = MyPlainTextEdit()
            self.list.focus_lost.connect(lambda text, rbtn = self.RB_combobox_desc, j = i:
                                         rbtn.setProperty("TypeOption", [list_tags[j], text, 1]))
            self.list.setMaximumHeight(maxH)
            self.list.hide()
            self.RB_CBDV2.toggled.connect(lambda check, widget=self.list:
                                          widget.show() if check else widget.hide())

            self.WD_CBDV2 = QWidget()
            self.HL_CBDV.addWidget(self.RB_CBDV1)
            self.HL_CBDV.addWidget(self.CB_CBDV1)
            self.HL_CBDV.addWidget(self.RB_CBDV2)
            self.HL_CBDV.addWidget(self.list)
            self.HL_CBDV.addStretch()
            self.WD_CBDV2.setLayout(self.HL_CBDV)

            self._Function1(self.RB_combobox_desc.isChecked(), self.HL_CBDV)    # Чтоб при иницилизации было не
                                                                                # доступно до выбора
            self.Layout2.addWidget(self.RB_combobox_desc, i + 1, 0)
            self.Layout2.addWidget(self.WD_CBDV2, i + 1, 1)

        self.VL_option.addLayout(self.Layout1)
        self.VL_option.addLayout(self.Layout2)

        self.WD_option.setLayout(self.VL_option)
        self.VL_additional_properies.addWidget(self.WD_option)

    def _clear_layout(self, layout: QLayout):
        if layout is None:
            return
        while layout.count() > 0:
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
            else:
                child_layout = item.layout()
                if child_layout is not None:
                    self.clear_layout(child_layout)

    def _create_row(self, name = None, decs = None, optional = None):
        maxH = 40

        self.WD_row = QWidget()                         # Виджет для макета
        self.HV_row = QHBoxLayout()                     # Макет/строка со всеми заполняемыми полями
        self.HV_row.setProperty("OldValue", optional)   # Стартовый (выкаченный из БД) словарь опций

        self.buttonX = QPushButton("X")
        self.buttonX.clicked.connect(lambda *args, w=self.WD_row: self._delete_row(w))
        self.buttonX.setMaximumHeight(maxH)
        self.HV_row.addWidget(self.buttonX)

        self.txt = QPlainTextEdit()                     # Текстовое поле для названия действия
        self.txt.setPlainText(name)                     # Заполняем его
        self.txt.setProperty("OldValue", name)          # Делаем новое свойство для отсеживания изменений
        self.txt.setMaximumHeight(maxH)                 # Задаем максимальную высоту
        self.txt.setMaximumWidth(200)                   # Задаем максимальную ширину
        self.HV_row.addWidget(self.txt)                 # Добавляем в строку

        self.desc = QPlainTextEdit()
        self.desc.setPlainText(decs)
        self.desc.setProperty("OldValue", decs)
        self.desc.setMaximumHeight(maxH)
        self.HV_row.addWidget(self.desc)

        self.BT = QPushButton("+ опции")
        self.BT.setProperty("OldValue", optional)                       # Нынешний словарь опций
        self.BT.clicked.connect(lambda: self._fun_button_option(self.BT.property("OldValue")))

        self.BT.setMaximumHeight(maxH)
        self.HV_row.addWidget(self.BT)

        self.WD_row.setLayout(self.HV_row)
        self.scroll_layout.addWidget(self.WD_row)

    def _save_option(self, layout: QLayout):
        option_dict = dict()

        for i in range(layout.count()):
            item = layout.itemAt(i).widget().layout()                       # Область опции
            name_option = item.itemAt(0).itemAt(1).widget().text()          # Название опции
            desc_option = item.itemAt(1)                                    # Описание для опции
            for j in range(desc_option.rowCount()):                         # Проходимся по всем вариантам
                if desc_option.itemAtPosition(j, 0).widget().isChecked():   # Если дошли до выбранного варианта
                    option_dict[name_option] = desc_option.itemAtPosition(j, 0).widget().property("TypeOption")

        print(option_dict)

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

        # with open_db() as cursor:
        #
        #     for name in self.delete_list: delete_of_name(cursor, self.db_table, name)
        #
        #     columns, PK, _ = get_structure_table(cursor, self.db_table)
        #     for name, values in NewActionList.items(): upsert(cursor, self.db_table, name, values,
        #                                                       columns = columns, primary_key = PK)

    def _init_ui(self):
        self.main_layout = QVBoxLayout(self)            # Главный макет, благодаря переданному self
        self.stack = QStackedWidget()                   # Стек для подмены содержимого

        # ===ГЛАВНОЕ ОКНО: СОЗДАНИЕ НОВОГО===

        self.VL_create_new = QVBoxLayout()              # Макет для окна создания нового
        self.WD_create_new = QWidget()                  # Виджет для окна создания нового

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
        #self.B_Close.clicked.connect()

        controls.addWidget(self.B_NewAcrion)
        controls.addWidget(self.B_Save)
        controls.addWidget(self.B_Close)

        self.VL_create_new.addWidget(self.scroll_area)
        self.VL_create_new.addLayout(controls)

        self.WD_create_new.setLayout(self.VL_create_new)

        # ===ОКНО ОПЦИЙ===

        self.WD_main = QWidget()
        self.VL_main = QVBoxLayout()

        self.row = None                               # Для кого делаются опции

        self.VL_additional_properies = QVBoxLayout()  # Макет где содержатся все опции
        self.WD_additional_properies = QWidget()      # Виджет для макета

        self.SA_option = QScrollArea()                # Область прокрутки
        self.SA_option.setWidgetResizable(True)

        controls = QHBoxLayout()

        self.B_NewOption = QPushButton("Создать новое")
        self.B_NewOption.clicked.connect(lambda: self._create_option())
        self.B_SaveOption = QPushButton("Сохранить изменения")
        self.B_SaveOption.clicked.connect(lambda: self._save_option(self.VL_additional_properies))
        self.B_CloseOption = QPushButton("Отмена")
        self.B_CloseOption.clicked.connect(lambda: (self.stack.setCurrentIndex(0),
                                              self._clear_layout(self.VL_additional_properies)))

        controls.addWidget(self.B_NewOption)
        controls.addWidget(self.B_SaveOption)
        controls.addWidget(self.B_CloseOption)

        self.WD_additional_properies.setLayout(self.VL_additional_properies)
        self.SA_option.setWidget(self.WD_additional_properies)

        self.VL_main.addWidget(self.SA_option)
        self.VL_main.addLayout(controls)
        self.WD_main.setLayout(self.VL_main)

        # ===ЗАПОЛНЯЕМ ОКНО===

        self.stack.addWidget(self.WD_create_new)
        self.stack.addWidget(self.WD_main)
        self.stack.setCurrentIndex(0)
        self.main_layout.addWidget(self.stack)

    def closeEvent(self, event):
        self.closed.emit()

        self.main_win._CloseSecondWin(self)

        super().closeEvent(event)

class MyPlainTextEdit(QPlainTextEdit):
    focus_lost = pyqtSignal(str)  # собственный сигнал

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def focusOutEvent(self, event):
        super().focusOutEvent(event)  # ← обязательно вызвать родительский!
        text = self.toPlainText()
        self.focus_lost.emit(text)  # ← испускаем сигнал

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