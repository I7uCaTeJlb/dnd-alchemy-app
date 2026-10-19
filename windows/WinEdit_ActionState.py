from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit,
                             QScrollArea, QPlainTextEdit, QMessageBox, QStackedWidget,
                             QRadioButton, QLayout, QGridLayout, QComboBox)
from sqlalchemy.testing.config import options

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

    def _delete_option(self, layout: QLayout, WD_option: QWidget):
        layout.removeWidget(WD_option)
        WD_option.setParent(None)  # опционально, чтобы виджет полностью отсоединился
        WD_option.deleteLater()  # опционально, чтобы освободить память

    def _fun_button_option(self, button: QPushButton, row):  # Функция для кнопки "+ опции"
        self.BTN = button
        self.ROW = row

        B_options = button.property("TypeOption")
        R_options = button.property("OldValue")

        if options != None:
            for name in B_options.keys():
                self._create_option(name, B_options[name])

        if R_options != None:
            for name in R_options.keys():
                self._create_option(name, R_options[name])

        self.stack.setCurrentIndex(1)

    def _Function1(self, check: bool, dependency: QLayout):  # Тип описания опции - при выборе разблокировать варианты
        for i in range(0, dependency.count(), 2):
            WD = dependency.itemAt(i).widget()
            if WD == None: continue
            if check:
                WD.setStyleSheet("color: rgb(0, 0, 0);")
                if WD.isChecked(): dependency.itemAt(i + 1).widget().show()
            else:
                dependency.itemAt(i + 1).widget().hide()
                WD.setStyleSheet("color: rgb(127, 127, 127);")
            WD.setEnabled(check)

    def _create_option(self, name=None, data=None):

        maxH = 40

        self.WD_option = QWidget()  # Виджет для макета
        self.VL_option = QVBoxLayout()  # Макет/строка со всеми заполняемыми полями

        self.Layout1 = QHBoxLayout()
        self.Layout2 = QGridLayout()

        self.buttonX = QPushButton("X")
        self.buttonX.setMaximumWidth(100)
        self.buttonX.clicked.connect(lambda *args, l=self.VL_additional_properies,
                                            w=self.WD_option:
                                     self._delete_option(l, w))
        self.buttonX.setMaximumHeight(maxH)
        self.Layout1.addWidget(self.buttonX)

        self.name = QLineEdit()  # Текстовое поле для названия действия
        self.name.setText(name)  # Заполняем его
        self.name.setMaximumHeight(maxH)  # Задаем максимальную высоту
        self.Layout1.addWidget(self.name)  # Добавляем в строку

        self.RB_text_desc = QRadioButton("Текстовое описание")

        self.RB_text_desc.setProperty("TypeOption", ["text", None])

        if data == None:
            self.RB_text_desc.setChecked(True)
        else:
            if data[0] == "text": self.RB_text_desc.setChecked(True)

        self.Layout2.addWidget(self.RB_text_desc, 0, 0)

        list_option = ["Выбор одного", "Выбор нескольких"]
        list_tags = ["combobox", "multiselect"]
        for i in range(len(list_option)):
            self.HL_CBDV = QHBoxLayout()

            self.RB_combobox_desc = QRadioButton(list_option[i])

            self.RB_combobox_desc.setProperty("TypeOption", [list_tags[i], None])
            self.RB_combobox_desc.toggled.connect(lambda check, layout=self.HL_CBDV:
                                                  self._Function1(check, layout))

            self.RB_CBDV1 = QRadioButton("Из таблиц механики")

            self.CB_CBDV1 = QComboBox()
            self.CB_CBDV1.addItems(["Состояния", "Действия", "База", "Экосистемы"])
            self.RB_CBDV1.toggled.connect(lambda *_, rbtn=self.RB_combobox_desc,
                                                 text=self.CB_CBDV1.currentText(), j=i:
                                          rbtn.setProperty("TypeOption", [list_tags[j], text]))
            self.CB_CBDV1.currentTextChanged.connect(lambda *txt, rbtn=self.RB_combobox_desc, j=i:
                                                     rbtn.setProperty("TypeOption", [list_tags[j], *txt]))

            self.CB_CBDV1.hide()
            self.RB_CBDV1.toggled.connect(lambda check, widget=self.CB_CBDV1:
                                          widget.show() if check else widget.hide())

            self.RB_CBDV2 = QRadioButton("Собстенный список")
            self.list = MyPlainTextEdit()
            self.list.focus_lost.connect(lambda text, rbtn=self.RB_combobox_desc, j=i:
                                         rbtn.setProperty("TypeOption", [list_tags[j], text]))
            self.list.setMaximumHeight(maxH)
            self.list.hide()
            self.RB_CBDV2.toggled.connect(lambda check, widget=self.list:
                                          widget.show() if check else widget.hide())

            if data != None:
                if data[0] == list_tags[i]:
                    self.RB_combobox_desc.setChecked(True)
                    if ',' in data[1]:
                        self.RB_CBDV2.setChecked(True)
                        self.list.insertPlainText(data[1])
                    else:
                        self.RB_CBDV1.setChecked(True)
                        index = self.CB_CBDV1.findText(data[1])
                        if index != -1:
                            self.CB_CBDV1.setCurrentIndex(index)  # Устанавливаем элемент выбранным
                        else:
                            self.RB_CBDV2.setChecked(True)
                            self.list.insertPlainText(data[1])

            self.WD_CBDV2 = QWidget()
            self.HL_CBDV.addWidget(self.RB_CBDV1)
            self.HL_CBDV.addWidget(self.CB_CBDV1)
            self.HL_CBDV.addWidget(self.RB_CBDV2)
            self.HL_CBDV.addWidget(self.list)
            self.HL_CBDV.addStretch()
            self.WD_CBDV2.setLayout(self.HL_CBDV)

            self._Function1(self.RB_combobox_desc.isChecked(), self.HL_CBDV)  # Чтоб при иницилизации было не
            # доступно до выбора
            self.Layout2.addWidget(self.RB_combobox_desc, i + 1, 0)
            self.Layout2.addWidget(self.WD_CBDV2, i + 1, 1)

        self.VL_option.addLayout(self.Layout1)
        self.VL_option.addLayout(self.Layout2)

        self.WD_option.setLayout(self.VL_option)
        self.VL_additional_properies.addWidget(self.WD_option)

        if data != None:
            pass

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

    def _create_row(self, name=None, decs=None, optional=None):
        maxH = 40

        self.WD_row = QWidget()  # Виджет для макета
        self.HV_row = QHBoxLayout()  # Макет/строка со всеми заполняемыми полями
        self.HV_row.setProperty("OldValue", optional)  # Стартовый (выкаченный из БД) словарь опций

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

        self.BT = QPushButton("+ опции")
        self.BT.setProperty("OldValue", optional)  # Нынешний словарь опций
        self.BT.clicked.connect(lambda *e, btn=self.BT, row=self.HV_row:
                                self._fun_button_option(btn, row))

        self.BT.setMaximumHeight(maxH)
        self.HV_row.addWidget(self.BT)

        self.WD_row.setLayout(self.HV_row)
        self.scroll_layout.addWidget(self.WD_row)

    def _save_option(self, layout: QLayout):

        option_dict = dict()

        for i in range(layout.count()):
            item = layout.itemAt(i).widget().layout()  # Область опции
            name_option = item.itemAt(0).itemAt(1).widget().text()  # Название опции

            if name_option in option_dict.keys():
                _ = QMessageBox.information(
                    self,
                    "Два одинаковых названия опций",
                    f'Название "{name_option}" повторяется!',
                    QMessageBox.StandardButton.Ok
                )
                return

            desc_option = item.itemAt(1)  # Описание для опции

            for j in range(desc_option.rowCount()):  # Проходимся по всем вариантам
                if desc_option.itemAtPosition(j, 0).widget().isChecked():  # Если дошли до выбранного варианта
                    desc = desc_option.itemAtPosition(j, 0).widget().property("TypeOption")
                    if desc[1] == None and desc[0] != "text":
                        _ = QMessageBox.information(
                            self,
                            "Не выбран список",
                            f'У опции "{name_option}" не выбран список выбора!',
                            QMessageBox.StandardButton.Ok
                        )
                        return
                    option_dict[name_option] = desc_option.itemAtPosition(j, 0).widget().property("TypeOption")

        self.BTN.setProperty("TypeOption", option_dict)

        # Возврат на главный экран после сохранения опций
        self.stack.setCurrentIndex(0)

    def _sync_row_old_values(self, row_widget, name, desc, optionals):
        """Вызывается ПОСЛЕ успешной записи в БД."""
        row_layout = row_widget.layout()
        name_edit = row_layout.itemAt(1).widget()
        desc_edit = row_layout.itemAt(2).widget()
        btn = row_layout.itemAt(3).widget()

        # Теперь программа знает: эта запись уже в БД под именем name
        name_edit.setProperty("OldValue", name)
        desc_edit.setProperty("OldValue", desc)

        # И знает, какие опции уже сохранены
        btn.setProperty("OldValue", optionals)
        btn.setProperty("TypeOption", None)  # несохранённых изменений больше нет
        row_layout.setProperty("OldValue", optionals)

    def _save_list(self):
        NewActionList = {}
        rows_to_sync = []  # что нужно пометить как "уже сохранено"

        # Идём напрямую по scroll_layout — не лезем через stack/SА/widget()
        for i in range(self.scroll_layout.count()):
            row_widget = self.scroll_layout.itemAt(i).widget()
            if row_widget is None:
                continue

            row = row_widget.layout()
            name_edit = row.itemAt(1).widget()
            desc_edit = row.itemAt(2).widget()
            btn = row.itemAt(3).widget()

            name = name_edit.toPlainText()
            desc = desc_edit.toPlainText()
            old_name = name_edit.property("OldValue")

            # Если опции меняли и сохранили в окне опций — берём TypeOption,
            # иначе — то, что приехало из БД
            optionals = btn.property("TypeOption")
            if optionals is None:
                optionals = btn.property("OldValue")

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
            old_optionals = row.property("OldValue")

            if old_name != name or old_desc != desc or optionals != old_optionals:
                NewActionList[name] = (old_name, desc, optionals)
                rows_to_sync.append((row_widget, name, desc, optionals))

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
            for row_widget, name, desc, optionals in rows_to_sync:
                self._sync_row_old_values(row_widget, name, desc, optionals)

        self.delete_list.clear()  # обработано — больше не удаляем
        # self.main_win.stack.setCurrentIndex(0)  # возврат на главный экран

    def _init_ui(self):
        self.main_layout = QVBoxLayout(self)    # Главный макет, благодаря переданному self
        self.stack = QStackedWidget()           # Стек для подмены содержимого

        # ===ГЛАВНОЕ ОКНО: СОЗДАНИЕ НОВОГО===
        self.BTN = None  # Чтобы программа знала для какого нового делаем опции
        self.ROW = None  # Чтобы программа знала для какого нового делаем опции

        self.VL_create_new = QVBoxLayout()  # Макет для окна создания нового
        self.WD_create_new = QWidget()  # Виджет для окна создания нового

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(scroll_content)
        self.scroll_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.scroll_area.setWidget(scroll_content)

        with open_db() as cursor:
            for data in read_all(self.db_table, cursor):
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

        self.VL_create_new.addWidget(self.scroll_area)
        self.VL_create_new.addLayout(controls)

        self.WD_create_new.setLayout(self.VL_create_new)

        # ===ОКНО ОПЦИЙ===

        self.WD_main = QWidget()
        self.VL_main = QVBoxLayout()

        self.row = None  # Для кого делаются опции

        self.VL_additional_properies = QVBoxLayout()  # Макет где содержатся все опции
        self.WD_additional_properies = QWidget()  # Виджет для макета

        self.SA_option = QScrollArea()  # Область прокрутки
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

class WinEditActions(EditWin):
    def __init__(self, main_win):
        super().__init__("Редактирование действий", "Actions", main_win)


class WinEditState(EditWin):
    def __init__(self, main_win):
        super().__init__("Редактирование состояний компонентов", "State", main_win)