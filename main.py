import sys
import os
import sentry_sdk
from PyQt6 import QtWidgets, QtGui
from PyQt6.QtWidgets import QStackedWidget
from PyQt6.QtCore import Qt, QTimer
from math import ceil
from scripts.CRUD import *

from windows.WinEdit_ActionState import WinEditActions, WinEditState
from windows.WinEdit_BaseEcosystems import WinEditEcosystem, WinEditBase
from windows.WinEditComponents import WinEditComponents
from windows.WinEditEfects import WinEditEfects

from updater import run_updater_check

sentry_sdk.init(
    dsn="https://a10abfaaa786e2427331a2dbc9796cb7@o4512323346890752.ingest.de.sentry.io/4512323440738384",
    release="dnd-alchemy-app@1.0.1",
    environment="production",
    traces_sample_rate=1.0,
)

def trigger_test_error():
    sentry_sdk.capture_message("Тестовое сообщение из DnD Alchemy App - пользователь нажал кнопку теста")
    raise ValueError("Тестовая ошибка: деление на ноль в алхимическом котле!")


class Ui_MainWindow(object):

    def _filter_effects(self):
        with (open_db() as cursor):
            rare_mapping = {
                "Обычный": "Об",
                "Необычный": "Не",
                "Редкий": "Ре",
                "Очень редкий": "Ор",
                "Легендарный": "Ле",
                "Артефакт": "Ар"
            }
            component_mapping = {}
            for data in read_all(cursor, "Components", ["Name", "Rare"]):
                component_mapping[data[0]] = data[1]

            # ('Гиацинт лекарственный', 'Свежий / целый', 'Добавить', {}, {}, 2.0, 'Восстановление', [], 'Восстановите 1d4 Хитов')
            for data in read_all(cursor, "Effects"):
                self.LW_all_components.addItem(
                    f"{data[0]} [{rare_mapping[component_mapping[data[0]]]}] "
                    f"{data[1]}{'*' if len(data[3]) > 0 else ''} "
                    f"{data[2]}{'*' if len(data[4]) > 0 else ''}"
                    f": [{data[6]}] {data[8]}"
                )

    def _OpenNewWindow(self, WindowClass):
        """
        Всегда создаём новое окно, добавляем в стек и переключаемся на него.
        """
        try:
            window = WindowClass(self)
            # Добавляем в стек главного окна
            self.stack.addWidget(window)
            self.stack.setCurrentWidget(window)

            # Важно: соединяем сигнал закрытия, чтобы удалить виджет из стека
            if hasattr(window, 'closed'):
                window.closed.connect(lambda w=window: self._on_window_closed(w))

        except Exception as e:
            print(f"Error opening window {WindowClass.__name__}: {e}")
            import traceback
            traceback.print_exc()
            # Отправляем ошибку в Sentry
            sentry_sdk.capture_exception(e)

    def _on_window_closed(self, window):
        """Вызывается, когда дочернее окно испускает сигнал closed."""
        # Убираем из текущего индекса, если оно там
        if self.stack.currentWidget() == window:
            self.stack.setCurrentIndex(0)  # Возвращаемся к главному экрану

        # Удаляем из стека
        self.stack.removeWidget(window)
        window.deleteLater()

    def _CloseSecondWin(self, close_win):
        self.stack.removeWidget(close_win)
        close_win.deleteLater()

    def _UpdateCBBase(self):
        self.CB_base.clear()
        base_list = self._GetInfoDB("Base")

        for i in base_list:
            self.CB_base.addItem(i[0])
            # Устанавливаем tooltip для конкретного элемента
            index = self.CB_base.count() - 1
            self.CB_base.setItemData(index, i[1], Qt.ItemDataRole.ToolTipRole)

    def _UpdateListEcosystems(self):
        m = self._GetInfoDB("Ecosystems")

        for i in range(self.GL_ecosys.count()):
            self.GL_ecosys.itemAt(i).widget().deleteLater()

        for i in range(ceil(len(m) / 3)):
            for j in range(3):
                if i * 3 + j == len(m): break
                CH = QtWidgets.QCheckBox(m[i * 3 + j][0])
                CH.setToolTip(m[i * 3 + j][1])

                self.GL_ecosys.addWidget(CH, i, j)

    def _GetInfoDB(self, table):
        connection = sqlite3.connect("data/alchemy_database.db")
        cursor = connection.cursor()
        cursor.execute(f"SELECT * FROM {table}")
        result = []
        for data in cursor.fetchall():
            result.append(data)
        connection.close()
        return result

    def setupUi(self, MainWindow):

        self.wins_list = {}

        MainWindow.setWindowTitle("Alchemist's Workshop Pre_alpha")
        # УСТАНАВЛИВАЕМ ИКОНКУ
        MainWindow.setWindowIcon(QtGui.QIcon('images/main_icon.png'))

        # ===СОЗДАНИЕ МЕНЮ===

        self.menu_bar = MainWindow.menuBar()

        self.file_menu = self.menu_bar.addMenu('Файл')

        self.file_menu_A_open = QtGui.QAction("Открыть")
        self.file_menu_A_save = QtGui.QAction("Сохранить")
        self.file_menu_A_save_as = QtGui.QAction("Сохранить как...")
        self.file_menu_M_work_data = QtWidgets.QMenu("Работа с данными")

        self.M_work_data_M_list_effects = QtGui.QAction("Редактировать список эффектов")
        self.M_work_data_M_list_effects.triggered.connect(lambda: self._OpenNewWindow(WinEditEfects))

        self.M_work_data_M_list_components = QtGui.QAction("Редактировать список компонентов")
        self.M_work_data_M_list_components.triggered.connect(lambda: self._OpenNewWindow(WinEditComponents))

        self.M_work_data_M_list_bases = QtGui.QAction("Редактировать список основ")
        self.M_work_data_M_list_bases.triggered.connect(lambda: self._OpenNewWindow(WinEditBase))

        self.M_work_data_M_list_ecosystem = QtGui.QAction("Редактировать список экосистем")
        self.M_work_data_M_list_ecosystem.triggered.connect(lambda: self._OpenNewWindow(WinEditEcosystem))

        self.M_work_data_M_list_actions = QtGui.QAction("Редактировать список действий")
        self.M_work_data_M_list_actions.triggered.connect(lambda: self._OpenNewWindow(WinEditActions))

        self.M_work_data_M_list_state = QtGui.QAction("Редактировать список состояний ингредиентов")
        self.M_work_data_M_list_state.triggered.connect(lambda: self._OpenNewWindow(WinEditState))

        self.file_menu_M_import = QtWidgets.QMenu("Импорт данных")
        self.M_import_M_list_components = QtGui.QAction("Список компонентов")
        self.M_import_M_list_bases = QtGui.QAction("Список основ")
        self.M_import_M_list_ecosystem = QtGui.QAction("Список экосистем")
        self.M_import_M_list_actions = QtGui.QAction("Список действий")
        self.M_import_M_list_state = QtGui.QAction("Список состояний ингредиентов")

        self.file_menu_M_export = QtWidgets.QMenu("Экспорт данных")
        self.M_export_M_list_components = QtGui.QAction("Список компонентов")
        self.M_export_M_list_bases = QtGui.QAction("Список основ")
        self.M_export_M_list_ecosystem = QtGui.QAction("Список экосистем")
        self.M_export_M_list_actions = QtGui.QAction("Список действий")
        self.M_export_M_list_state = QtGui.QAction("Список состояний ингредиентов")

        self.file_menu_A_setting = QtGui.QAction("Настройки")
        # self.file_menu_A_setting.triggered.connect(lambda: self._OpenNewWindow(WinSettings))

        self.file_menu_A_exit = QtGui.QAction("Выход")
        self.file_menu.addAction(self.file_menu_A_open)
        self.file_menu.addAction(self.file_menu_A_save)
        self.file_menu.addAction(self.file_menu_A_save_as)
        self.file_menu.addSeparator()
        self.file_menu.addMenu(self.file_menu_M_work_data)

        self.file_menu_M_work_data.addAction(self.M_work_data_M_list_effects)
        self.file_menu_M_work_data.addAction(self.M_work_data_M_list_components)
        self.file_menu_M_work_data.addAction(self.M_work_data_M_list_bases)
        self.file_menu_M_work_data.addAction(self.M_work_data_M_list_ecosystem)
        self.file_menu_M_work_data.addAction(self.M_work_data_M_list_actions)
        self.file_menu_M_work_data.addAction(self.M_work_data_M_list_state)

        self.file_menu.addMenu(self.file_menu_M_import)
        self.file_menu_M_import.addAction(self.M_import_M_list_components)
        self.file_menu_M_import.addAction(self.M_import_M_list_bases)
        self.file_menu_M_import.addAction(self.M_import_M_list_ecosystem)
        self.file_menu_M_import.addAction(self.M_import_M_list_actions)
        self.file_menu_M_import.addAction(self.M_import_M_list_state)

        self.file_menu.addMenu(self.file_menu_M_export)
        self.file_menu_M_export.addAction(self.M_export_M_list_components)
        self.file_menu_M_export.addAction(self.M_export_M_list_bases)
        self.file_menu_M_export.addAction(self.M_export_M_list_ecosystem)
        self.file_menu_M_export.addAction(self.M_export_M_list_actions)
        self.file_menu_M_export.addAction(self.M_export_M_list_state)

        self.file_menu.addSeparator()
        self.file_menu.addAction(self.file_menu_A_setting)
        self.file_menu.addAction(self.file_menu_A_exit)

        # self.A_edit_list_components = QtGui.QAction("132")
        # self.file_menu_A_work_data.ac

        self.db_menu = self.menu_bar.addMenu('Правила')

        self.help_menu = self.menu_bar.addMenu('Руководство пользователя')

        # === МЕНЮ СПРАВКА С КНОПКОЙ ТЕСТА SENTRY ===
        self.info_menu = self.menu_bar.addMenu('Справка')

        # Добавляем действие для тестирования Sentry
        self.test_sentry_action = QtGui.QAction("🐛 Тест Sentry (вызвать ошибку)")
        self.test_sentry_action.triggered.connect(lambda: trigger_test_error())
        self.info_menu.addAction(self.test_sentry_action)

        self.info_menu.addSeparator()  # Разделитель

        self.info_menu_A_about = QtGui.QAction("О программе")
        self.info_menu.addAction(self.info_menu_A_about)

        # ===ОСНОВНОЙ ХОЛСТ===

        self.SA_l = QtWidgets.QScrollArea()  # SA для левого VL
        self.SA_c = QtWidgets.QScrollArea()  # SA для среднего VL
        self.SA_r = QtWidgets.QScrollArea()  # SA для правого VL

        self.VL_main_l = QtWidgets.QVBoxLayout()  # Левый VL
        self.VL_main_c = QtWidgets.QVBoxLayout()  # Серединый VL
        self.VL_main_r = QtWidgets.QVBoxLayout()  # Правый VL

        # ===ЛЕВАЯ ЧАСТЬ===
        self.Q = QtWidgets.QLabel

        self.GB_rary = QtWidgets.QGroupBox("Редкость ингредиента зелий")
        self.GL_rary = QtWidgets.QGridLayout()
        self.GL_rary.setSpacing(3)

        self.VL_rary = QtWidgets.QVBoxLayout()  # макет чтобы добавить макет для кнопок
        self.HL_rary = QtWidgets.QHBoxLayout()  # макет для кнопок

        self.CH_rary_component_OB = QtWidgets.QCheckBox("Обычный")
        self.CH_rary_component_HE = QtWidgets.QCheckBox("Необычный")
        self.CH_rary_component_RE = QtWidgets.QCheckBox("Редкий")
        self.CH_rary_component_OR = QtWidgets.QCheckBox("Очень редкий")
        self.CH_rary_component_LE = QtWidgets.QCheckBox("Легендарный")
        self.CH_rary_component_AR = QtWidgets.QCheckBox("Артефакт")

        self.GL_rary.addWidget(self.CH_rary_component_OB, 0, 0)
        self.GL_rary.addWidget(self.CH_rary_component_HE, 1, 0)
        self.GL_rary.addWidget(self.CH_rary_component_RE, 0, 1)
        self.GL_rary.addWidget(self.CH_rary_component_OR, 1, 1)
        self.GL_rary.addWidget(self.CH_rary_component_LE, 0, 2)
        self.GL_rary.addWidget(self.CH_rary_component_AR, 1, 2)

        def Function_B_rary(state):
            self.CH_rary_component_OB.setChecked(state)
            self.CH_rary_component_HE.setChecked(state)
            self.CH_rary_component_RE.setChecked(state)
            self.CH_rary_component_OR.setChecked(state)
            self.CH_rary_component_LE.setChecked(state)
            self.CH_rary_component_AR.setChecked(state)

        self.B_rary_select = QtWidgets.QPushButton("Выбрать все")
        self.B_rary_select.clicked.connect(lambda: Function_B_rary(True))

        self.B_rary_clear = QtWidgets.QPushButton("Очистить все")
        self.B_rary_clear.clicked.connect(lambda: Function_B_rary(False))

        self.HL_rary.addWidget(self.B_rary_select)
        self.HL_rary.addWidget(self.B_rary_clear)

        self.VL_rary.addLayout(self.HL_rary)
        self.VL_rary.addLayout(self.GL_rary)

        self.GB_rary.setLayout(self.VL_rary)
        self.VL_main_l.addWidget(self.GB_rary)

        self.GB_effect = QtWidgets.QGroupBox("Тип эффекта ингредиента")
        self.GL_effect = QtWidgets.QGridLayout()
        self.GL_effect.setSpacing(3)

        self.CH_effect_TOXIN = QtWidgets.QCheckBox("Токсин")
        self.CH_effect_SKILL = QtWidgets.QCheckBox("Умение")
        self.CH_effect_BUFF = QtWidgets.QCheckBox("Усиление")
        self.CH_effect_DEBUFF = QtWidgets.QCheckBox("Ослабление")
        self.CH_effect_MOD = QtWidgets.QCheckBox("Модификатор")
        self.CH_effect_HILL = QtWidgets.QCheckBox("Восстановление")

        def F_B_effect_1(status):
            self.CH_effect_TOXIN.setChecked(status)
            self.CH_effect_SKILL.setChecked(status)
            self.CH_effect_BUFF.setChecked(status)
            self.CH_effect_DEBUFF.setChecked(status)
            self.CH_effect_MOD.setChecked(status)
            self.CH_effect_HILL.setChecked(status)

        self.B_effect_select_1 = QtWidgets.QPushButton("Выбрать все")
        self.B_effect_select_1.clicked.connect(lambda: F_B_effect_1(True))
        self.B_effect_clear_1 = QtWidgets.QPushButton("Очистить все")
        self.B_effect_clear_1.clicked.connect(lambda: F_B_effect_1(False))

        self.GL_effect.addWidget(self.B_effect_select_1, 0, 0)
        self.GL_effect.addWidget(self.B_effect_clear_1, 1, 0)
        self.GL_effect.addWidget(self.CH_effect_TOXIN, 2, 0)
        self.GL_effect.addWidget(self.CH_effect_SKILL, 3, 0)
        self.GL_effect.addWidget(self.CH_effect_BUFF, 4, 0)
        self.GL_effect.addWidget(self.CH_effect_DEBUFF, 5, 0)
        self.GL_effect.addWidget(self.CH_effect_MOD, 6, 0)
        self.GL_effect.addWidget(self.CH_effect_HILL, 7, 0)

        self.CH_effect_Z = QtWidgets.QCheckBox("Загуститель")
        self.CH_effect_R = QtWidgets.QCheckBox("Растворитель")
        self.CH_effect_S = QtWidgets.QCheckBox("Стабилизатор")
        self.CH_effect_V = QtWidgets.QCheckBox("Возмутитель")
        self.CH_effect_Y = QtWidgets.QCheckBox("Усилитель")
        self.CH_effect_P = QtWidgets.QCheckBox("Потеря")

        def F_B_effect_2(status):
            self.CH_effect_Z.setChecked(status)
            self.CH_effect_R.setChecked(status)
            self.CH_effect_S.setChecked(status)
            self.CH_effect_V.setChecked(status)
            self.CH_effect_Y.setChecked(status)
            self.CH_effect_P.setChecked(status)

        self.B_effect_select_2 = QtWidgets.QPushButton("Выбрать все")
        self.B_effect_select_2.clicked.connect(lambda: F_B_effect_2(True))
        self.B_effect_clear_2 = QtWidgets.QPushButton("Очистить все")
        self.B_effect_clear_2.clicked.connect(lambda: F_B_effect_2(False))

        self.GL_effect.addWidget(self.B_effect_select_2, 0, 1)
        self.GL_effect.addWidget(self.B_effect_clear_2, 1, 1)
        self.GL_effect.addWidget(self.CH_effect_Z, 2, 1)
        self.GL_effect.addWidget(self.CH_effect_R, 3, 1)
        self.GL_effect.addWidget(self.CH_effect_S, 4, 1)
        self.GL_effect.addWidget(self.CH_effect_V, 5, 1)
        self.GL_effect.addWidget(self.CH_effect_Y, 6, 1)
        self.GL_effect.addWidget(self.CH_effect_P, 7, 1)

        self.GB_effect.setLayout(self.GL_effect)
        self.VL_main_l.addWidget(self.GB_effect)

        self.GB_ecosys = QtWidgets.QGroupBox("Экосистема")

        self.SA_ecosys = QtWidgets.QScrollArea()
        self.SA_ecosys.setMaximumHeight(100)
        self.SA_ecosys.setWidgetResizable(True)
        self.WD_for_SA_ecosys = QtWidgets.QWidget()
        self.GL_ecosys = QtWidgets.QGridLayout()
        self.GL_ecosys.setSpacing(3)
        self._UpdateListEcosystems()

        self.WD_for_SA_ecosys.setLayout(self.GL_ecosys)
        self.SA_ecosys.setWidget(self.WD_for_SA_ecosys)

        self.VL_ecosys = QtWidgets.QVBoxLayout()
        self.HL_ecosys = QtWidgets.QHBoxLayout()

        self.B_ecosys_select = QtWidgets.QPushButton("Выбрать все")
        self.B_ecosys_clear = QtWidgets.QPushButton("Стереть все")

        self.HL_ecosys.addWidget(self.B_ecosys_select)
        self.HL_ecosys.addWidget(self.B_ecosys_clear)

        self.VL_ecosys.addLayout(self.HL_ecosys)
        self.VL_ecosys.addWidget(self.SA_ecosys)

        self.GB_ecosys.setLayout(self.VL_ecosys)
        self.VL_main_l.addWidget(self.GB_ecosys)

        self.GB_dop_rools = QtWidgets.QGroupBox("Дополнительные настройки / фильтры")
        self.GL_dop_rools = QtWidgets.QGridLayout()

        self.CH_dop_rools_color = QtWidgets.QCheckBox("Цвет зелья")
        self.B_dop_rools_color = QtWidgets.QPushButton("Настроить")

        self.CH_dop_rools_taste = QtWidgets.QCheckBox("Вкус зелья")
        self.B_dop_rools_taste = QtWidgets.QPushButton("Настроить")

        self.CH_dop_rools_smell = QtWidgets.QCheckBox("Запах зелья")
        self.B_dop_rools_smell = QtWidgets.QPushButton("Настроить")

        self.GL_dop_rools.addWidget(self.CH_dop_rools_color, 0, 0)
        self.GL_dop_rools.addWidget(self.B_dop_rools_color, 0, 1)
        self.GL_dop_rools.addWidget(self.CH_dop_rools_taste, 1, 0)
        self.GL_dop_rools.addWidget(self.B_dop_rools_taste, 1, 1)
        self.GL_dop_rools.addWidget(self.CH_dop_rools_smell, 2, 0)
        self.GL_dop_rools.addWidget(self.B_dop_rools_smell, 2, 1)

        self.VL_dop_rools = QtWidgets.QVBoxLayout()
        self.B_state_compopent = QtWidgets.QPushButton("Состояние компонента и действия")

        self.VL_dop_rools.addWidget(self.B_state_compopent)
        self.VL_dop_rools.addLayout(self.GL_dop_rools)

        self.GB_dop_rools.setLayout(self.VL_dop_rools)
        self.VL_main_l.addWidget(self.GB_dop_rools)

        self.VL_main_l.addWidget(QtWidgets.QPushButton("Фильтр"))

        # ===СЕРЕДИНА===

        self.HL_center = QtWidgets.QHBoxLayout()

        self.T_poisk_component = QtWidgets.QTextEdit()
        self.T_poisk_component.setMaximumSize(10000, 37)
        self.T_poisk_component.setPlaceholderText("Введите название ингредиента, который хотите найти")

        self.B_poisk_component = QtWidgets.QPushButton("Искать")

        self.HL_center.addWidget(self.T_poisk_component)
        self.HL_center.addWidget(self.B_poisk_component)

        self.LW_all_components = QtWidgets.QListWidget()
        self.LW_all_components.size()
        self.LW_all_components.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding,
                                             QtWidgets.QSizePolicy.Policy.Expanding)

        self._filter_effects()

        self.VL_main_c.addLayout(self.HL_center)
        self.VL_main_c.addWidget(self.LW_all_components)

        # ===ПРАВАЯ ЧАСТЬ===
        ##### ОКОШКО #####
        self.stack = QStackedWidget()

        # Главный виджет (индекс 0)
        self.LW_added_components = QtWidgets.QListWidget()
        self.LW_added_components.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding,
                                               QtWidgets.QSizePolicy.Policy.Expanding)
        self.stack.addWidget(self.LW_added_components)

        # Кэш: класс окна → индекс в stack
        self._window_cache = {}

        ##### ----- #####
        self.L_text_base = QtWidgets.QLabel("Основа для проведения алхимического опыта:")

        self.CB_base = QtWidgets.QComboBox()
        self._UpdateCBBase()

        self.L_rez_RAO = QtWidgets.QLabel("Результат алхимического опыта: Мазь")

        self.HL_rez_RAO = QtWidgets.QHBoxLayout()

        self.B_effects_RAO = QtWidgets.QPushButton("Посмотреть эффекты РАО")
        self.B_dop_effects_RAO = QtWidgets.QPushButton("Посмотреть дополнительне параметры РАО")

        self.HL_rez_RAO.addWidget(self.B_effects_RAO)
        self.HL_rez_RAO.addWidget(self.B_dop_effects_RAO)

        self.B_save_RAO = QtWidgets.QPushButton("Сохранить результат алхимического опыта")

        self.VL_main_r.addWidget(self.stack)
        self.VL_main_r.addWidget(self.L_text_base)
        self.VL_main_r.addWidget(self.CB_base)
        self.VL_main_r.addWidget(self.L_rez_RAO)
        self.VL_main_r.addLayout(self.HL_rez_RAO)
        self.VL_main_r.addWidget(self.B_save_RAO)

        # ===ПРИВЯЗКИ===
        self.WD_for_SA_l = QtWidgets.QWidget()  # Виджет для левого SA
        self.WD_for_SA_l.setLayout(self.VL_main_l)  # Левый VL положили в виджет для левого SA

        self.WD_for_SA_c = QtWidgets.QWidget()  # Виджет для среднего SA
        self.WD_for_SA_c.setLayout(self.VL_main_c)

        self.WD_for_SA_r = QtWidgets.QWidget()  # Виджет для правого SA
        self.WD_for_SA_r.setLayout(self.VL_main_r)  # Правый VL положили в виджет для левого SA

        self.SA_l.setWidget(self.WD_for_SA_l)
        self.SA_c.setWidget(self.WD_for_SA_c)
        self.SA_r.setWidget(self.WD_for_SA_r)

        # self.SA_l.setWidgetResizable(True)
        self.SA_c.setWidgetResizable(True)
        self.SA_r.setWidgetResizable(True)

        self.SP_main = QtWidgets.QSplitter()
        self.SP_main.addWidget(self.SA_l)
        self.SP_main.addWidget(self.SA_c)
        self.SP_main.addWidget(self.SA_r)

        MainWindow.setCentralWidget(self.SP_main)  # говорим, что главный виджет является центральныm


if __name__ == "__main__":
    os.environ[
        "QT_AUTO_SCREEN_SCALE_FACTOR"] = "0"  # автоматическим определением коэффициента масштабирования на основе DPI монитора
    os.environ["QT_SCALE_FACTOR"] = "0.8"  # Применяет глобальный множитель ко всем элементам интерфейса

    app = QtWidgets.QApplication(sys.argv)

    with open("data/styles.qss", "r", encoding="utf-8") as f:
        app.setStyleSheet(f.read())

    window = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(window)

    # Автоматическая проверка обновлений через 1 секунду после запуска
    QTimer.singleShot(1000, run_updater_check)

    window.show()
    sys.exit(app.exec())