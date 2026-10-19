from PyQt6.QtCore import Qt, pyqtSignal, QRegularExpression
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QScrollArea, QPlainTextEdit, QMessageBox, QComboBox,
                             QStackedWidget, QLineEdit, QLabel)
from PyQt6.QtGui import QRegularExpressionValidator
import json
from scripts.CRUD import *
from MyWidgets.CustomDropdown import CustomDropdown


def read_effects(cursor):
    """Чтение таблицы Effects с явным порядком колонок."""
    cursor.execute("""
        SELECT name, state, action, state_options, action_options, cost, 
               main_tag, additional_tag, effect 
        FROM Effects
    """)
    result = []
    for data in cursor.fetchall():
        parsed_data = []
        for value in data:
            if isinstance(value, str):
                try:
                    parsed = json.loads(value)
                    if isinstance(parsed, (dict, list)):
                        parsed_data.append(parsed)
                    else:
                        parsed_data.append(value)
                except Exception:
                    parsed_data.append(value)
            else:
                parsed_data.append(value)
        result.append(tuple(parsed_data))
    return result


class WinEditEfects(QWidget):
    closed = pyqtSignal()

    def __init__(self, main_win):
        super().__init__()
        self.setWindowTitle("Редактирование списка эффектов")
        self.resize(400, 300)
        self.db = "./data/alchemy_database.db"
        self.db_table = "Effects"
        self.main_win = main_win

        self._init_ui()

    def _delete_row(self, row_widget):
        """Удаляет строку: если она есть в БД — сразу удаляет из БД, затем из GUI."""
        desc = row_widget.layout().itemAt(10).widget().toPlainText()

        component = row_widget.layout().itemAt(2).widget().property("OldValue")
        state = row_widget.layout().itemAt(3).widget().property("OldValue")
        action = row_widget.layout().itemAt(6).widget().property("OldValue")

        # Получаем опции из OldOptions (JSON-строки)
        state_options_str = row_widget.layout().itemAt(3).widget().property("OldOptions")
        action_options_str = row_widget.layout().itemAt(6).widget().property("OldOptions")

        state_options = {}
        if state_options_str:
            try:
                state_options = json.loads(state_options_str)
            except Exception:
                state_options = {}

        action_options = {}
        if action_options_str:
            try:
                action_options = json.loads(action_options_str)
            except Exception:
                action_options = {}

        # Если запись ещё не в БД — просто спрашиваем про пустую строку
        if component is None or state is None or action is None:
            if not desc or desc.isspace():
                self._remove_row(row_widget)
                return
            else:
                text = f"Вы уверены, что хотите удалить эффект с описанием: {desc}"
        else:
            text = f"Вы уверены, что хотите удалить {component} + {state} + {action}?"

        reply = QMessageBox.question(
            self,
            "Подтверждение",
            f"{text}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            # Если запись существует в БД — удаляем сразу
            if component is not None and state is not None and action is not None:
                try:
                    # Получаем правильный порядок PK из структуры таблицы
                    with open_db() as temp_cursor:
                        _, PK_list, _ = get_structure_table(temp_cursor, self.db_table)

                    print(f"DEBUG: PK_list = {PK_list}")

                    # Формируем old_pk в ПРАВИЛЬНОМ порядке PK_list
                    pk_dict = {
                        'name': component,
                        'state': state,
                        'action': action,
                        'state_options': json.dumps(state_options, ensure_ascii=False),
                        'action_options': json.dumps(action_options, ensure_ascii=False)
                    }
                    old_pk = tuple(pk_dict[col] for col in PK_list)

                    print(f"DEBUG: old_pk = {old_pk}")

                    with open_db() as cursor:
                        delete_of_name(cursor, self.db_table, old_pk)
                    print(f"DEBUG: Удалено из БД: {old_pk}")
                except Exception as e:
                    print(f"ERROR при удалении из БД: {e}")
                    import traceback
                    traceback.print_exc()
                    QMessageBox.critical(
                        self, "Ошибка удаления",
                        f"Не удалось удалить запись из БД: {e}",
                        QMessageBox.StandardButton.Ok
                    )
                    return  # Не удаляем из GUI, если не удалось удалить из БД

            # Убираем из GUI
            self._remove_row(row_widget)

    def _remove_row(self, row_widget):
        self.scroll_layout.removeWidget(row_widget)
        row_widget.setParent(None)
        row_widget.deleteLater()

    def _clone_row(self, button):
        try:
            row_widget = button.parent()
            row_layout = row_widget.layout()

            component = row_layout.itemAt(2).widget().currentData()
            state = row_layout.itemAt(3).widget().currentText()
            cost = row_layout.itemAt(5).widget().text()
            action = row_layout.itemAt(6).widget().currentText()
            Mtag = row_layout.itemAt(8).widget().currentText()
            Atag = row_layout.itemAt(9).widget().getSelectedItems()
            desc = row_layout.itemAt(10).widget().toPlainText()

            current_index = -1
            for i in range(self.scroll_layout.count()):
                if self.scroll_layout.itemAt(i).widget() == row_widget:
                    current_index = i
                    break

            if current_index == -1:
                return

            self._create_row(component, state, None, cost, action, None, Mtag, Atag, desc)

            cloned_widget = self.scroll_layout.itemAt(self.scroll_layout.count() - 1).widget()
            self.scroll_layout.removeWidget(cloned_widget)
            self.scroll_layout.insertWidget(current_index + 1, cloned_widget)

            cloned_layout = cloned_widget.layout()
            cloned_state_cb = cloned_layout.itemAt(3).widget()
            cloned_action_cb = cloned_layout.itemAt(6).widget()

            state_user_data = row_layout.itemAt(3).widget().currentData()
            cloned_state_cb.setCurrentText(state)
            cloned_state_cb.setItemData(cloned_state_cb.currentIndex(), state_user_data)

            action_user_data = row_layout.itemAt(6).widget().currentData()
            cloned_action_cb.setCurrentText(action)
            cloned_action_cb.setItemData(cloned_action_cb.currentIndex(), action_user_data)

            self._toggle_options_button(cloned_layout.itemAt(4).widget(), cloned_state_cb)
            self._toggle_options_button(cloned_layout.itemAt(7).widget(), cloned_action_cb)

            for i in [2, 3, 5, 6, 8, 9, 10]:
                widget = cloned_layout.itemAt(i).widget()
                if hasattr(widget, 'setProperty'):
                    widget.setProperty("OldValue", None)
            # Сбрасываем OldOptions у клонов
            cloned_state_cb.setProperty("OldOptions", "{}")
            cloned_action_cb.setProperty("OldOptions", "{}")

        except Exception as e:
            print(f"ERROR in _clone_row: {e}")
            import traceback
            traceback.print_exc()

    def _create_row(self, component=None, state=None, state_options=None,
                    cost=None, action=None, action_options=None,
                    MT=None, AT=None, desc=None):
        try:
            print(f"DEBUG _create_row START: component={component}, state={state}, action={action}")

            maxH = 40

            self.WD_row = QWidget()
            self.HV_row = QHBoxLayout()

            self.buttonX = QPushButton("X")
            self.buttonX.clicked.connect(lambda *args, w=self.WD_row: self._delete_row(w))
            self.buttonX.setMaximumHeight(maxH)
            self.HV_row.addWidget(self.buttonX)

            self.buttonClone = QPushButton("⤷")
            self.buttonClone.setMaximumHeight(maxH)
            self.buttonClone.clicked.connect(lambda *args, btn=self.buttonClone: self._clone_row(btn))
            self.HV_row.addWidget(self.buttonClone)

            print("DEBUG: buttons created")

            # === КОМПОНЕНТЫ ===
            self.CB_components = QComboBox()
            rare_mapping = {
                "Обычный": "Об",
                "Необычный": "Не",
                "Редкий": "Ре",
                "Очень редкий": "Ор",
                "Легендарный": "Ле",
                "Артефакт": "Ар"
            }

            for i in range(len(self.components)):
                full_name = self.components[i][0]
                rare = self.components[i][1]
                desc_comp = self.components[i][3]

                display_name = full_name
                if '_[' in full_name:
                    idx = full_name.rfind('_[')
                    display_name = full_name[:idx]

                rare_short = rare_mapping.get(rare, str(rare))
                display_text = f"{display_name} [{rare_short}]"

                self.CB_components.addItem(display_text, userData=display_name)
                self.CB_components.setItemData(i, desc_comp, Qt.ItemDataRole.ToolTipRole)

            self.CB_components.setMaximumHeight(maxH)
            self.CB_components.setMaximumWidth(200)
            self.HV_row.addWidget(self.CB_components)

            print("DEBUG: components combobox created")

            # === СОСТОЯНИЯ ===
            self.CB_states = QComboBox()
            for i in range(len(self.states)):
                state_data = self.states[i]
                state_name = state_data[0]
                state_desc = state_data[1]
                state_optional = state_data[2] if len(state_data) > 2 else None

                print(f"DEBUG: adding state '{state_name}' with optional={state_optional} (type={type(state_optional)})")

                if state_optional is None:
                    self.CB_states.addItem(state_name, userData=None)
                else:
                    self.CB_states.addItem(state_name, userData=state_optional)
                self.CB_states.setItemData(i, state_desc, Qt.ItemDataRole.ToolTipRole)

            self.CB_states.setMaximumHeight(maxH)
            self.CB_states.setMaximumWidth(200)
            self.HV_row.addWidget(self.CB_states)

            print("DEBUG: states combobox created")

            self.B_edit_state_options = QPushButton("Опции")
            self.B_edit_state_options.setMaximumHeight(maxH)
            self.B_edit_state_options.hide()
            self.B_edit_state_options.clicked.connect(
                lambda *args, cb=self.CB_states: self._open_options_editor("state", cb)
            )
            self.HV_row.addWidget(self.B_edit_state_options)

            self.CB_states.currentIndexChanged.connect(
                lambda idx, btn=self.B_edit_state_options, cb=self.CB_states:
                self._toggle_options_button(btn, cb)
            )

            print("DEBUG: state options button created")

            # === СТОИМОСТЬ ===
            regex = QRegularExpression(r"^[0-9]+(\.[0-9]+)?$")
            validator = QRegularExpressionValidator(regex)

            self.cost = QLineEdit()
            self.cost.setPlaceholderText("ЗМ")
            self.cost.setMaximumHeight(maxH)
            self.cost.setMaximumWidth(200)
            self.cost.setValidator(validator)
            self.HV_row.addWidget(self.cost)

            print("DEBUG: cost field created")

            # === ДЕЙСТВИЯ ===
            self.CB_actions = QComboBox()
            for i in range(len(self.actions)):
                action_data = self.actions[i]
                action_name = action_data[0]
                action_desc = action_data[1]
                action_optional = action_data[2] if len(action_data) > 2 else None

                print(f"DEBUG: adding action '{action_name}' with optional={action_optional} (type={type(action_optional)})")

                self.CB_actions.addItem(action_name, userData=action_optional)
                self.CB_actions.setItemData(i, action_desc, Qt.ItemDataRole.ToolTipRole)

            self.CB_actions.setMaximumHeight(maxH)
            self.CB_actions.setMaximumWidth(200)
            self.HV_row.addWidget(self.CB_actions)

            print("DEBUG: actions combobox created")

            self.B_edit_action_options = QPushButton("Опции")
            self.B_edit_action_options.setMaximumHeight(maxH)
            self.B_edit_action_options.hide()
            self.B_edit_action_options.clicked.connect(
                lambda *args, cb=self.CB_actions: self._open_options_editor("action", cb)
            )
            self.HV_row.addWidget(self.B_edit_action_options)

            self.CB_actions.currentIndexChanged.connect(
                lambda idx, btn=self.B_edit_action_options, cb=self.CB_actions:
                self._toggle_options_button(btn, cb)
            )

            print("DEBUG: action options button created")

            # === ТЕГИ ===
            self.CB_MTags = QComboBox()
            self.CB_MTags.addItems(self.MTags)
            self.CB_MTags.setMaximumHeight(maxH)
            self.CB_MTags.setMaximumWidth(200)
            self.HV_row.addWidget(self.CB_MTags)

            self.CB_ATags = CustomDropdown("Доп. эффект", self.ATags)
            self.HV_row.addWidget(self.CB_ATags)

            print("DEBUG: tags created")

            # === ОПИСАНИЕ ===
            self.desc = QPlainTextEdit()
            self.desc.setMaximumHeight(maxH)
            self.HV_row.addWidget(self.desc)

            self.WD_row.setLayout(self.HV_row)
            self.scroll_layout.addWidget(self.WD_row)

            print("DEBUG: row widget added to layout")

            # === УСТАНОВКА ЗНАЧЕНИЙ ===

            # Компонент
            if component is not None:
                for i in range(self.CB_components.count()):
                    if self.CB_components.itemData(i) == component:
                        self.CB_components.setCurrentIndex(i)
                        break
                self.CB_components.setProperty("OldValue", component)
            else:
                self.CB_components.setProperty("OldValue", None)

            print("DEBUG: component value set")

            # Состояние
            if state is not None:
                idx = self.CB_states.findText(state)
                print(f"DEBUG: found state '{state}' at index {idx}")
                if idx != -1:
                    self.CB_states.setCurrentIndex(idx)
                    self.CB_states.setProperty("OldValue", state)
                    if state_options is None:
                        state_options = {}
                    elif isinstance(state_options, str):
                        try:
                            state_options = json.loads(state_options)
                            if not isinstance(state_options, dict):
                                state_options = {}
                        except Exception:
                            state_options = {}
                    if isinstance(state_options, dict):
                        print(f"DEBUG: setting state options userData at index {idx}: {state_options}")
                        self.CB_states.setItemData(idx, state_options)
                        print(f"DEBUG: setting OldOptions property: {json.dumps(state_options, ensure_ascii=False)}")
                        self.CB_states.setProperty("OldOptions", json.dumps(state_options, ensure_ascii=False))
                    else:
                        self.CB_states.setProperty("OldOptions", "{}")
                else:
                    self.CB_states.setCurrentIndex(0)
                    self.CB_states.setProperty("OldValue", None)
                    self.CB_states.setProperty("OldOptions", "{}")
            else:
                self.CB_states.setProperty("OldValue", None)
                self.CB_states.setProperty("OldOptions", "{}")

            print("DEBUG: state value set")

            # Стоимость
            if cost is not None:
                self.cost.setText(str(cost))
                self.cost.setProperty("OldValue", str(cost))
            else:
                self.cost.setProperty("OldValue", None)

            print("DEBUG: cost value set")

            # Действие
            if action is not None:
                idx = self.CB_actions.findText(action)
                print(f"DEBUG: found action '{action}' at index {idx}")
                if idx != -1:
                    self.CB_actions.setCurrentIndex(idx)
                    self.CB_actions.setProperty("OldValue", action)
                    if action_options is None:
                        action_options = {}
                    elif isinstance(action_options, str):
                        try:
                            action_options = json.loads(action_options)
                            if not isinstance(action_options, dict):
                                action_options = {}
                        except Exception:
                            action_options = {}
                    if isinstance(action_options, dict):
                        print(f"DEBUG: setting action options userData at index {idx}: {action_options}")
                        self.CB_actions.setItemData(idx, action_options)
                        print(f"DEBUG: setting OldOptions property: {json.dumps(action_options, ensure_ascii=False)}")
                        self.CB_actions.setProperty("OldOptions", json.dumps(action_options, ensure_ascii=False))
                    else:
                        self.CB_actions.setProperty("OldOptions", "{}")
                else:
                    self.CB_actions.setCurrentIndex(0)
                    self.CB_actions.setProperty("OldValue", None)
                    self.CB_actions.setProperty("OldOptions", "{}")
            else:
                self.CB_actions.setProperty("OldValue", None)
                self.CB_actions.setProperty("OldOptions", "{}")

            print("DEBUG: action value set")

            # Основной тег
            if MT is not None:
                self.CB_MTags.setCurrentText(MT)
                self.CB_MTags.setProperty("OldValue", MT)
            else:
                self.CB_MTags.setProperty("OldValue", None)

            print("DEBUG: main tag set")

            # Дополнительный тег
            if AT is not None:
                if isinstance(AT, str):
                    try:
                        AT = json.loads(AT)
                    except Exception:
                        AT = []
                if isinstance(AT, list):
                    print(f"DEBUG: setting AT checks: {AT}")
                    self.CB_ATags.setChecks(AT)
                print(f"DEBUG: setting AT OldValue: {json.dumps(AT if isinstance(AT, list) else [], ensure_ascii=False)}")
                self.CB_ATags.setProperty("OldValue", json.dumps(AT if isinstance(AT, list) else [], ensure_ascii=False))
            else:
                self.CB_ATags.setProperty("OldValue", "[]")

            print("DEBUG: additional tag set")

            # Описание
            if desc is not None:
                self.desc.setPlainText(desc)
                self.desc.setProperty("OldValue", desc)
            else:
                self.desc.setProperty("OldValue", None)

            print("DEBUG: description set")

            self._toggle_options_button(self.B_edit_state_options, self.CB_states)
            self._toggle_options_button(self.B_edit_action_options, self.CB_actions)

            print("DEBUG _create_row END")

        except Exception as e:
            print(f"ERROR in _create_row: {e}")
            import traceback
            traceback.print_exc()
            raise

    def _toggle_options_button(self, button, combobox):
        current_data = combobox.currentData()
        if current_data is not None and current_data != {} and current_data != "":
            button.show()
        else:
            button.hide()

    def _open_options_editor(self, source_type, combobox):
        try:
            self.current_options_source = source_type
            self.current_options_combobox = combobox

            options_data = combobox.currentData()

            if source_type == "state":
                title = "Редактирование опций состояния"
            else:
                title = "Редактирование опций действия"

            self.L_options_title.setText(title)

            self._clear_layout(self.scroll_layout_options)
            self.current_options_widgets = {}

            if options_data is not None and isinstance(options_data, dict):
                for name, data in options_data.items():
                    self._create_option_widget(name, data)

            self.stack.setCurrentIndex(1)

        except Exception as e:
            print(f"ERROR in _open_options_editor: {e}")
            import traceback
            traceback.print_exc()

    def _create_option_widget(self, name, option_data):
        if isinstance(option_data, dict):
            option_type = option_data.get("type", "text")
            option_value = option_data.get("source")
            saved_value = option_data.get("value")
        else:
            option_type = option_data[0]
            option_value = option_data[1]
            saved_value = None

        table_mapping = {
            "Состояния": "State",
            "Действия": "Actions",
            "База": "Base",
            "Экосистемы": "Ecosystems"
        }

        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(5, 5, 5, 5)

        label = QLabel(f"{name}:")
        label.setMinimumWidth(150)
        row_layout.addWidget(label)

        if option_type == "text":
            widget = QLineEdit()
            widget.setPlaceholderText("Введите значение")
            if saved_value:
                widget.setText(str(saved_value))
            row_layout.addWidget(widget)
            self.current_options_widgets[name] = widget

        elif option_type == "combobox":
            widget = QComboBox()

            if option_value is not None and "," in str(option_value):
                items = [x.strip() for x in option_value.split(",")]
                widget.addItems(items)
            else:
                table_name = table_mapping.get(option_value, option_value)
                try:
                    with open_db() as cursor:
                        data = read_all(table_name, cursor)
                        items = [row[0] for row in data]
                        widget.addItems(items)
                except Exception as e:
                    print(f"DEBUG: Не удалось прочитать таблицу '{table_name}': {e}")
                    widget.addItem("(нет данных)")

            if saved_value:
                index = widget.findText(str(saved_value))
                if index != -1:
                    widget.setCurrentIndex(index)

            row_layout.addWidget(widget)
            self.current_options_widgets[name] = widget

        elif option_type == "multiselect":
            if option_value is not None and "," in str(option_value):
                items = [x.strip() for x in option_value.split(",")]
            else:
                table_name = table_mapping.get(option_value, option_value)
                try:
                    with open_db() as cursor:
                        data = read_all(table_name, cursor)
                        items = [row[0] for row in data]
                except Exception as e:
                    print(f"DEBUG: Не удалось прочитать таблицу '{table_name}': {e}")
                    items = []

            widget = CustomDropdown(name, items)

            if saved_value:
                if isinstance(saved_value, list):
                    widget.setChecks(saved_value)
                elif isinstance(saved_value, str) and saved_value:
                    widget.setChecks([saved_value])

            row_layout.addWidget(widget)
            self.current_options_widgets[name] = widget

        row_layout.addStretch()
        self.scroll_layout_options.addWidget(row_widget)

    def _save_options(self):
        try:
            collected_data = {}

            for name, widget in self.current_options_widgets.items():
                if isinstance(widget, QLineEdit):
                    collected_data[name] = widget.text()
                elif isinstance(widget, QComboBox):
                    collected_data[name] = widget.currentText()
                elif isinstance(widget, CustomDropdown):
                    collected_data[name] = widget.getSelectedItems()

            combobox = self.current_options_combobox
            old_user_data = combobox.currentData()

            new_user_data = {}
            if old_user_data and isinstance(old_user_data, dict):
                for name, option_structure in old_user_data.items():
                    if isinstance(option_structure, dict):
                        option_type = option_structure.get("type", "text")
                        option_source = option_structure.get("source")
                    else:
                        option_type = option_structure[0]
                        option_source = option_structure[1]

                    value = collected_data.get(name, "")
                    new_user_data[name] = {
                        "type": option_type,
                        "source": option_source,
                        "value": value
                    }

            current_index = combobox.currentIndex()
            combobox.setItemData(current_index, new_user_data)

            self.stack.setCurrentIndex(0)

        except Exception as e:
            print(f"ERROR in _save_options: {e}")
            import traceback
            traceback.print_exc()

    def _clear_layout(self, layout):
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
                    self._clear_layout(child_layout)

    def _save_list(self):
        """Сохраняет только изменения и новые записи. Удаления уже произошли сразу через _delete_row."""
        NewActionList = {}
        rows_to_sync = []

        for i in range(self.scroll_layout.count()):
            row_widget = self.scroll_layout.itemAt(i).widget()
            if row_widget is None:
                continue

            row = row_widget.layout()

            component = row.itemAt(2).widget().currentData()
            state = row.itemAt(3).widget().currentText()
            cost = row.itemAt(5).widget().text()
            action = row.itemAt(6).widget().currentText()
            Mtag = row.itemAt(8).widget().currentText()
            Atag = row.itemAt(9).widget().getSelectedItems()
            desc = row.itemAt(10).widget().toPlainText()

            state_options = row.itemAt(3).widget().currentData()
            action_options = row.itemAt(6).widget().currentData()

            if not isinstance(state_options, dict):
                state_options = {}
            if not isinstance(action_options, dict):
                action_options = {}

            old_component = row.itemAt(2).widget().property("OldValue")
            old_state = row.itemAt(3).widget().property("OldValue")
            old_cost = row.itemAt(5).widget().property("OldValue")
            old_action = row.itemAt(6).widget().property("OldValue")
            old_Mtag = row.itemAt(8).widget().property("OldValue")
            old_desc = row.itemAt(10).widget().property("OldValue")

            # OldValue для AT — это JSON-строка, парсим её
            old_Atag_str = row.itemAt(9).widget().property("OldValue")
            old_Atag = []
            if old_Atag_str:
                try:
                    old_Atag = json.loads(old_Atag_str)
                except Exception:
                    old_Atag = []
            if not isinstance(old_Atag, list):
                old_Atag = []

            # Старые опции из OldOptions (JSON-строки)
            old_state_options_str = row.itemAt(3).widget().property("OldOptions")
            old_action_options_str = row.itemAt(6).widget().property("OldOptions")

            old_state_options = {}
            if old_state_options_str:
                try:
                    old_state_options = json.loads(old_state_options_str)
                except Exception:
                    old_state_options = {}

            old_action_options = {}
            if old_action_options_str:
                try:
                    old_action_options = json.loads(old_action_options_str)
                except Exception:
                    old_action_options = {}

            # Проверки заполненности
            if not component or not component.strip():
                QMessageBox.information(self, "Заполните поле", "Выберите компонент!", QMessageBox.StandardButton.Ok)
                self.scroll_area.ensureWidgetVisible(row_widget)
                return

            if not state or not state.strip():
                QMessageBox.information(self, "Заполните поле", "Выберите состояние!", QMessageBox.StandardButton.Ok)
                self.scroll_area.ensureWidgetVisible(row_widget)
                return

            if not action or not action.strip():
                QMessageBox.information(self, "Заполните поле", "Выберите действие!", QMessageBox.StandardButton.Ok)
                self.scroll_area.ensureWidgetVisible(row_widget)
                return

            if not cost or cost.isspace():
                QMessageBox.information(self, "Заполните поле", "Введите стоимость!", QMessageBox.StandardButton.Ok)
                self.scroll_area.ensureWidgetVisible(row_widget)
                return

            if not desc or desc.isspace():
                QMessageBox.information(self, "Заполните поле", "Введите описание эффекта!",
                                        QMessageBox.StandardButton.Ok)
                self.scroll_area.ensureWidgetVisible(row_widget)
                return

            pk_check = (component, state, action)

            if pk_check in NewActionList:
                QMessageBox.information(self, "Комбинация повторяется",
                                        f"Комбинация {component} + {state} + {action} уже была!",
                                        QMessageBox.StandardButton.Ok)
                self.scroll_area.ensureWidgetVisible(row_widget)
                return

            old_pk_check = (old_component, old_state, old_action)

            Atag_str = json.dumps(Atag, ensure_ascii=False) if Atag else "[]"
            old_Atag_str_cmp = json.dumps(old_Atag, ensure_ascii=False) if old_Atag else "[]"

            has_changes = (
                    old_pk_check != pk_check or
                    str(old_cost) != str(cost) or
                    old_Mtag != Mtag or
                    old_Atag_str_cmp != Atag_str or
                    old_desc != desc or
                    old_state_options != state_options or
                    old_action_options != action_options
            )

            if has_changes:
                state_options_json = json.dumps(state_options, ensure_ascii=False)
                action_options_json = json.dumps(action_options, ensure_ascii=False)

                with open_db() as temp_cursor:
                    columns, PK, _ = get_structure_table(temp_cursor, self.db_table)

                pk_dict = {
                    'name': component,
                    'state': state,
                    'action': action,
                    'state_options': state_options_json,
                    'action_options': action_options_json
                }
                pk_db = tuple(pk_dict[col] for col in PK)

                if old_component is None or old_state is None or old_action is None:
                    old_pk_db = tuple(None for _ in PK)
                else:
                    old_pk_dict = {
                        'name': old_component,
                        'state': old_state,
                        'action': old_action,
                        'state_options': json.dumps(old_state_options, ensure_ascii=False),
                        'action_options': json.dumps(old_action_options, ensure_ascii=False)
                    }
                    old_pk_db = tuple(old_pk_dict[col] for col in PK)

                values = (cost, Mtag, Atag, desc)
                NewActionList[pk_db] = (old_pk_db, values)
                rows_to_sync.append((row_widget, component, state, state_options,
                                     cost, action, action_options, Mtag, Atag, desc))

        try:
            with open_db() as cursor:
                columns, PK, _ = get_structure_table(cursor, self.db_table)

                # Вставка/обновление
                for pk_db, (old_pk_db, values) in NewActionList.items():
                    upsert(cursor, self.db_table, pk_db, (old_pk_db, *values),
                           columns=columns, primary_key=PK)

                # Синхронизация OldValue и OldOptions
                for row_widget, component, state, state_options, cost, action, action_options, Mtag, Atag, desc in rows_to_sync:
                    row = row_widget.layout()
                    row.itemAt(2).widget().setProperty("OldValue", component)
                    row.itemAt(3).widget().setProperty("OldValue", state)
                    row.itemAt(5).widget().setProperty("OldValue", cost)
                    row.itemAt(6).widget().setProperty("OldValue", action)
                    row.itemAt(8).widget().setProperty("OldValue", Mtag)
                    # AT — список, храним как JSON-строку
                    row.itemAt(9).widget().setProperty("OldValue", json.dumps(Atag if isinstance(Atag, list) else [],
                                                                              ensure_ascii=False))
                    row.itemAt(10).widget().setProperty("OldValue", desc)
                    # Сохраняем опции как JSON-строки в OldOptions
                    row.itemAt(3).widget().setProperty("OldOptions", json.dumps(state_options, ensure_ascii=False))
                    row.itemAt(6).widget().setProperty("OldOptions", json.dumps(action_options, ensure_ascii=False))
                    row.itemAt(3).widget().setItemData(row.itemAt(3).widget().currentIndex(), state_options)
                    row.itemAt(6).widget().setItemData(row.itemAt(6).widget().currentIndex(), action_options)

            print("DEBUG: Сохранение завершено успешно")

        except Exception as e:
            print(f"КРИТИЧЕСКАЯ ОШИБКА: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Ошибка сохранения",
                                 f"Произошла ошибка при сохранении: {e}",
                                 QMessageBox.StandardButton.Ok)

    def _init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.stack = QStackedWidget()

        # ★★★ Определяем списки ДО загрузки данных ★★★
        self.MTags = ["Токсин", "Умение", "Усиление", "Ослабление", "Модификатор", "Восстановление"]
        self.ATags = ["Загуститель", "Растворитель", "Стабилизатор", "Возмутитель", "Усилитель", "Потеря"]

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)

        scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(scroll_content)
        self.scroll_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.scroll_area.setWidget(scroll_content)

        with open_db() as cursor:
            self.components = read_all("Components", cursor)
            self.states = read_all("State", cursor)
            self.actions = read_all("Actions", cursor)

            effects_data = read_effects(cursor)
            for data in effects_data:
                print(f"DEBUG loading: {data}")

                # Правильный порядок: name(0), state(1), action(2), state_options(3),
                # action_options(4), cost(5), main_tag(6), additional_tag(7), effect(8)
                component = data[0] if len(data) > 0 else None
                state = data[1] if len(data) > 1 else None
                action = data[2] if len(data) > 2 else None
                state_options = data[3] if len(data) > 3 else None
                action_options = data[4] if len(data) > 4 else None
                cost = data[5] if len(data) > 5 else None
                MT = data[6] if len(data) > 6 else None
                AT = data[7] if len(data) > 7 else None
                desc = data[8] if len(data) > 8 else None

                # Надёжный парсинг
                if isinstance(state_options, str):
                    try:
                        state_options = json.loads(state_options)
                    except Exception:
                        state_options = {}
                if not isinstance(state_options, dict):
                    state_options = {}

                if isinstance(action_options, str):
                    try:
                        action_options = json.loads(action_options)
                    except Exception:
                        action_options = {}
                if not isinstance(action_options, dict):
                    action_options = {}

                if isinstance(AT, str):
                    try:
                        AT = json.loads(AT)
                    except Exception:
                        AT = []
                if not isinstance(AT, list):
                    AT = []

                print(f"DEBUG parsed: component={component}, state={state}, action={action}, "
                      f"cost={cost}, state_options={state_options}, action_options={action_options}, "
                      f"MT={MT}, AT={AT}, desc={desc}")

                self._create_row(
                    component=component,
                    state=state,
                    state_options=state_options,
                    cost=cost,
                    action=action,
                    action_options=action_options,
                    MT=MT,
                    AT=AT,
                    desc=desc
                )

        self.WD_main_list = QWidget()
        self.VL_main_list = QVBoxLayout(self.WD_main_list)

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

        self.VL_main_list.addWidget(self.scroll_area)
        self.VL_main_list.addLayout(controls)

        self.WD_options_editor = QWidget()
        self.VL_options_editor = QVBoxLayout(self.WD_options_editor)

        self.L_options_title = QLabel("Редактирование опций")
        self.L_options_title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.scroll_area_options = QScrollArea()
        self.scroll_area_options.setWidgetResizable(True)
        scroll_content_options = QWidget()
        self.scroll_layout_options = QVBoxLayout(scroll_content_options)
        self.scroll_layout_options.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scroll_area_options.setWidget(scroll_content_options)

        controls_options = QHBoxLayout()

        self.B_NewOption = QPushButton("Создать новое")
        self.B_SaveOption = QPushButton("Сохранить изменения")
        self.B_SaveOption.clicked.connect(self._save_options)
        self.B_CloseOption = QPushButton("Отмена | Выход")
        self.B_CloseOption.clicked.connect(lambda: self.stack.setCurrentIndex(0))

        controls_options.addWidget(self.B_NewOption)
        controls_options.addWidget(self.B_SaveOption)
        controls_options.addWidget(self.B_CloseOption)

        self.VL_options_editor.addWidget(self.L_options_title)
        self.VL_options_editor.addWidget(self.scroll_area_options)
        self.VL_options_editor.addLayout(controls_options)

        self.stack.addWidget(self.WD_main_list)
        self.stack.addWidget(self.WD_options_editor)
        self.stack.setCurrentIndex(0)

        self.main_layout.addWidget(self.stack)

    def closeEvent(self, event):
        self.closed.emit()
        self.main_win._CloseSecondWin(self)
        super().closeEvent(event)