from PyQt6.QtCore import Qt, pyqtSignal, QRegularExpression
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QScrollArea, QPlainTextEdit, QMessageBox, QComboBox,
                             QStackedWidget, QLineEdit, QLabel)
from PyQt6.QtGui import QRegularExpressionValidator
import json
from scripts.CRUD import *
from MyWidgets.CustomDropdown import CustomDropdown


def get_options_from_db(cursor, table: str, name: str):
    """Получить актуальную структуру опций из справочника (State/Actions).
    Формат: {'название': ['тип', 'источник']}"""
    cursor.execute(f'SELECT * FROM "{table}" WHERE "name" = ?', (name,))
    row = cursor.fetchone()
    if row and len(row) > 2 and row[2] is not None:
        options = row[2]
        if isinstance(options, str):
            try:
                options = json.loads(options)
            except Exception:
                return None
        if isinstance(options, dict):
            return options
    return None


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


def normalize_options(options):
    """Нормализует опции в формат {'name': ['type', 'value']}.
    Поддерживает старые форматы:
    - {'name': {'type': ..., 'source': ..., 'value': ...}}
    - {'name': ['type', 'source']} (без значения)
    - {'name': 'value'} (просто значение)
    """
    if not isinstance(options, dict):
        return {}

    normalized = {}
    for name, val in options.items():
        if isinstance(val, dict) and "type" in val:
            # Формат {'type': ..., 'source': ..., 'value': ...}
            opt_type = val.get("type", "text")
            opt_value = val.get("value", "")
            normalized[name] = [opt_type, opt_value]
        elif isinstance(val, (list, tuple)) and len(val) >= 2:
            # Формат ['type', 'value'] - оставляем как есть
            normalized[name] = [val[0], val[1]]
        elif isinstance(val, (list, tuple)) and len(val) == 1:
            # Формат ['type'] - без значения
            normalized[name] = [val[0], ""]
        else:
            # Просто значение
            normalized[name] = ["text", val]

    return normalized


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
            if component is not None and state is not None and action is not None:
                try:
                    with open_db() as temp_cursor:
                        _, PK_list, _ = get_structure_table(temp_cursor, self.db_table)

                    pk_dict = {
                        'name': component,
                        'state': state,
                        'action': action,
                        'state_options': json.dumps(state_options, ensure_ascii=False),
                        'action_options': json.dumps(action_options, ensure_ascii=False)
                    }
                    old_pk = tuple(pk_dict[col] for col in PK_list)

                    with open_db() as cursor:
                        delete_of_name(cursor, self.db_table, old_pk)
                except Exception as e:
                    import traceback
                    traceback.print_exc()
                    QMessageBox.critical(
                        self, "Ошибка удаления",
                        f"Не удалось удалить запись из БД: {e}",
                        QMessageBox.StandardButton.Ok
                    )
                    return

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
            cloned_state_cb.setProperty("OldOptions", "{}")
            cloned_action_cb.setProperty("OldOptions", "{}")

        except Exception as e:
            import traceback
            traceback.print_exc()

    def _create_row(self, component=None, state=None, state_options=None,
                    cost=None, action=None, action_options=None,
                    MT=None, AT=None, desc=None):
        try:
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

            # === СОСТОЯНИЯ ===
            self.CB_states = QComboBox()
            for i in range(len(self.states)):
                state_data = self.states[i]
                state_name = state_data[0]
                state_desc = state_data[1]
                state_optional = state_data[2] if len(state_data) > 2 else None

                if state_optional is None:
                    self.CB_states.addItem(state_name, userData=None)
                else:
                    self.CB_states.addItem(state_name, userData=state_optional)
                self.CB_states.setItemData(i, state_desc, Qt.ItemDataRole.ToolTipRole)

            self.CB_states.setMaximumHeight(maxH)
            self.CB_states.setMaximumWidth(200)
            self.HV_row.addWidget(self.CB_states)

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

            # === СТОИМОСТЬ ===
            regex = QRegularExpression(r"^[0-9]+(\.[0-9]+)?$")
            validator = QRegularExpressionValidator(regex)

            self.cost = QLineEdit()
            self.cost.setPlaceholderText("ЗМ")
            self.cost.setMaximumHeight(maxH)
            self.cost.setMaximumWidth(200)
            self.cost.setValidator(validator)
            self.HV_row.addWidget(self.cost)

            # === ДЕЙСТВИЯ ===
            self.CB_actions = QComboBox()
            for i in range(len(self.actions)):
                action_data = self.actions[i]
                action_name = action_data[0]
                action_desc = action_data[1]
                action_optional = action_data[2] if len(action_data) > 2 else None

                self.CB_actions.addItem(action_name, userData=action_optional)
                self.CB_actions.setItemData(i, action_desc, Qt.ItemDataRole.ToolTipRole)

            self.CB_actions.setMaximumHeight(maxH)
            self.CB_actions.setMaximumWidth(200)
            self.HV_row.addWidget(self.CB_actions)

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

            # === ТЕГИ ===
            self.CB_MTags = QComboBox()
            self.CB_MTags.addItems(self.MTags)
            self.CB_MTags.setMaximumHeight(maxH)
            self.CB_MTags.setMaximumWidth(200)
            self.HV_row.addWidget(self.CB_MTags)

            self.CB_ATags = CustomDropdown("Доп. эффект", self.ATags)
            self.HV_row.addWidget(self.CB_ATags)

            # === ОПИСАНИЕ ===
            self.desc = QPlainTextEdit()
            self.desc.setMaximumHeight(maxH)
            self.HV_row.addWidget(self.desc)

            self.WD_row.setLayout(self.HV_row)
            self.scroll_layout.addWidget(self.WD_row)

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

            # Состояние
            if state is not None:
                idx = self.CB_states.findText(state)
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

                    # Нормализуем опции в формат {'name': ['type', 'value']}
                    state_options = normalize_options(state_options)

                    if state_options:
                        self.CB_states.setItemData(idx, state_options)
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

            # Стоимость
            if cost is not None:
                self.cost.setText(str(cost))
                self.cost.setProperty("OldValue", str(cost))
            else:
                self.cost.setProperty("OldValue", None)

            # Действие
            if action is not None:
                idx = self.CB_actions.findText(action)
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

                    # Нормализуем опции в формат {'name': ['type', 'value']}
                    action_options = normalize_options(action_options)

                    if action_options:
                        self.CB_actions.setItemData(idx, action_options)
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

            # Основной тег
            if MT is not None:
                self.CB_MTags.setCurrentText(MT)
                self.CB_MTags.setProperty("OldValue", MT)
            else:
                self.CB_MTags.setProperty("OldValue", None)

            # Дополнительный тег
            if AT is not None:
                if isinstance(AT, str):
                    try:
                        AT = json.loads(AT)
                    except Exception:
                        AT = []
                if isinstance(AT, list):
                    self.CB_ATags.setChecks(AT)
                self.CB_ATags.setProperty("OldValue",
                                          json.dumps(AT if isinstance(AT, list) else [], ensure_ascii=False))
            else:
                self.CB_ATags.setProperty("OldValue", "[]")

            # Описание
            if desc is not None:
                self.desc.setPlainText(desc)
                self.desc.setProperty("OldValue", desc)
            else:
                self.desc.setProperty("OldValue", None)

            self._toggle_options_button(self.B_edit_state_options, self.CB_states)
            self._toggle_options_button(self.B_edit_action_options, self.CB_actions)

        except Exception as e:
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
        """Открывает редактор опций.
        Структура опций берётся из БД (State/Actions), значения — из OldOptions."""
        try:
            self.current_options_source = source_type
            self.current_options_combobox = combobox

            selected_text = combobox.currentText()

            if source_type == "state":
                title = "Редактирование опций состояния"
                table_name = "State"
            else:
                title = "Редактирование опций действия"
                table_name = "Actions"

            # Получаем структуру опций из справочника
            with open_db() as cursor:
                options_structure = get_options_from_db(cursor, table_name, selected_text)

            # Получаем сохранённые значения из OldOptions
            old_options_str = combobox.property("OldOptions")
            saved_values = {}
            if old_options_str:
                try:
                    saved_values = json.loads(old_options_str)
                except Exception:
                    saved_values = {}

            self.L_options_title.setText(title)

            # Очищаем старые виджеты
            self._clear_layout(self.scroll_layout_options)
            self.current_options_widgets = {}

            # Создаём виджеты на основе структуры из справочника
            if options_structure is not None and isinstance(options_structure, dict):
                for name, struct_data in options_structure.items():
                    # struct_data может быть ['type', 'source'] или просто 'type'
                    if isinstance(struct_data, (list, tuple)) and len(struct_data) >= 2:
                        opt_type = struct_data[0]
                        opt_source = struct_data[1]
                    elif isinstance(struct_data, (list, tuple)) and len(struct_data) == 1:
                        opt_type = struct_data[0]
                        opt_source = None
                    elif isinstance(struct_data, str):
                        opt_type = struct_data
                        opt_source = None
                    else:
                        continue

                    # Ищем сохранённое значение
                    current_value = ""
                    if name in saved_values:
                        val_data = saved_values[name]
                        if isinstance(val_data, (list, tuple)) and len(val_data) >= 2:
                            current_value = val_data[1]
                        elif isinstance(val_data, (list, tuple)) and len(val_data) == 1:
                            current_value = val_data[0]
                        else:
                            current_value = val_data

                    self._create_option_widget_simple(name, opt_type, opt_source, current_value)

            self.stack.setCurrentIndex(1)

        except Exception as e:
            import traceback
            traceback.print_exc()

    def _create_option_widget_simple(self, name, opt_type, opt_source, current_value):
        """Создаёт виджет для редактирования одной опции."""
        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(5, 5, 5, 5)

        label = QLabel(f"{name}:")
        label.setMinimumWidth(150)
        row_layout.addWidget(label)

        widget = None

        table_mapping = {
            "Состояния": "State",
            "Действия": "Actions",
            "База": "Base",
            "Экосистемы": "Ecosystems"
        }

        if opt_type == "text":
            widget = QLineEdit()
            widget.setPlaceholderText("Введите значение")
            if current_value is not None:
                widget.setText(str(current_value))

        elif opt_type == "combobox":
            widget = QComboBox()
            items = []
            if opt_source:
                if "," in str(opt_source):
                    items = [x.strip() for x in str(opt_source).split(",")]
                else:
                    t_name = table_mapping.get(opt_source, opt_source)
                    try:
                        with open_db() as c:
                            data = read_all(c, t_name)
                            items = [row[0] for row in data]
                    except Exception:
                        items = []
            widget.addItems(items)
            if current_value:
                idx = widget.findText(str(current_value))
                if idx != -1:
                    widget.setCurrentIndex(idx)

        elif opt_type == "multiselect":
            items = []
            if opt_source:
                if "," in str(opt_source):
                    items = [x.strip() for x in str(opt_source).split(",")]
                else:
                    t_name = table_mapping.get(opt_source, opt_source)
                    try:
                        with open_db() as c:
                            data = read_all(c, t_name)
                            items = [row[0] for row in data]
                    except Exception:
                        items = []
            widget = CustomDropdown(name, items)
            if current_value:
                if isinstance(current_value, list):
                    widget.setChecks(current_value)
                elif isinstance(current_value, str) and current_value:
                    widget.setChecks([current_value])

        if widget:
            widget.setProperty("OptionType", opt_type)
            row_layout.addWidget(widget)
            self.current_options_widgets[name] = widget

        row_layout.addStretch()
        self.scroll_layout_options.addWidget(row_widget)

    def _save_options(self):
        """Сохраняет опции в формат {'name': ['type', 'value']}."""
        try:
            collected_data = {}

            for name, widget in self.current_options_widgets.items():
                opt_type = widget.property("OptionType") or "text"
                val = None

                if isinstance(widget, QLineEdit):
                    val = widget.text()
                elif isinstance(widget, QComboBox):
                    val = widget.currentText()
                elif isinstance(widget, CustomDropdown):
                    val = widget.getSelectedItems()

                collected_data[name] = [opt_type, val]

            combobox = self.current_options_combobox

            # Обновляем userData комбобокса
            combobox.setItemData(combobox.currentIndex(), collected_data)

            # Обновляем OldOptions (JSON-строка)
            combobox.setProperty("OldOptions", json.dumps(collected_data, ensure_ascii=False))

            self.stack.setCurrentIndex(0)

        except Exception as e:
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
        """Сохраняет только изменения и новые записи."""
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

            old_Atag_str = row.itemAt(9).widget().property("OldValue")
            old_Atag = []
            if old_Atag_str:
                try:
                    old_Atag = json.loads(old_Atag_str)
                except Exception:
                    old_Atag = []
            if not isinstance(old_Atag, list):
                old_Atag = []

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

                for pk_db, (old_pk_db, values) in NewActionList.items():
                    upsert(cursor, self.db_table, pk_db, (old_pk_db, *values),
                           columns=columns, primary_key=PK)

                for row_widget, component, state, state_options, cost, action, action_options, Mtag, Atag, desc in rows_to_sync:
                    row = row_widget.layout()
                    row.itemAt(2).widget().setProperty("OldValue", component)
                    row.itemAt(3).widget().setProperty("OldValue", state)
                    row.itemAt(5).widget().setProperty("OldValue", cost)
                    row.itemAt(6).widget().setProperty("OldValue", action)
                    row.itemAt(8).widget().setProperty("OldValue", Mtag)
                    row.itemAt(9).widget().setProperty("OldValue", json.dumps(Atag if isinstance(Atag, list) else [],
                                                                              ensure_ascii=False))
                    row.itemAt(10).widget().setProperty("OldValue", desc)
                    row.itemAt(3).widget().setProperty("OldOptions", json.dumps(state_options, ensure_ascii=False))
                    row.itemAt(6).widget().setProperty("OldOptions", json.dumps(action_options, ensure_ascii=False))
                    row.itemAt(3).widget().setItemData(row.itemAt(3).widget().currentIndex(), state_options)
                    row.itemAt(6).widget().setItemData(row.itemAt(6).widget().currentIndex(), action_options)

        except Exception as e:
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Ошибка сохранения",
                                 f"Произошла ошибка при сохранении: {e}",
                                 QMessageBox.StandardButton.Ok)

    def _init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.stack = QStackedWidget()

        self.MTags = ["Токсин", "Умение", "Усиление", "Ослабление", "Модификатор", "Восстановление"]
        self.ATags = ["Загуститель", "Растворитель", "Стабилизатор", "Возмутитель", "Усилитель", "Потеря"]

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)

        scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(scroll_content)
        self.scroll_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.scroll_area.setWidget(scroll_content)

        with open_db() as cursor:
            self.components = read_all(cursor, "Components")
            self.states = read_all(cursor, "State")
            self.actions = read_all(cursor, "Actions")

            effects_data = read_effects(cursor)
            for data in effects_data:
                component = data[0] if len(data) > 0 else None
                state = data[1] if len(data) > 1 else None
                action = data[2] if len(data) > 2 else None
                state_options = data[3] if len(data) > 3 else None
                action_options = data[4] if len(data) > 4 else None
                cost = data[5] if len(data) > 5 else None
                MT = data[6] if len(data) > 6 else None
                AT = data[7] if len(data) > 7 else None
                desc = data[8] if len(data) > 8 else None

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

        self.B_SaveOption = QPushButton("Сохранить изменения")
        self.B_SaveOption.clicked.connect(self._save_options)
        self.B_CloseOption = QPushButton("Отмена | Выход")
        self.B_CloseOption.clicked.connect(lambda: self.stack.setCurrentIndex(0))

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