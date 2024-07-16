# coding:utf-8
import os
import sys

from PyQt5.QtCore import QRect, QDate
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtGui import QPainter, QImage, QColor, QBrush, QDesktopServices
from PyQt5.QtWidgets import QApplication, QFrame, QStackedWidget, QHBoxLayout, QLabel, QVBoxLayout, QTableWidget, \
    QTableWidgetItem, QWidget, QSizePolicy, QDialog, QStyledItemDelegate, QDateEdit
from PyQt5.QtWidgets import QGridLayout
from matplotlib import rcParams
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.ticker import MaxNLocator
from qframelesswindow import FramelessWindow, TitleBar

from database import Database
from qfluentwidgets import FluentIcon as FIF, ScrollArea, PrimaryPushButton
from qfluentwidgets import (LineEdit, PushButton, ComboBox, CalendarPicker)
from qfluentwidgets import (NavigationInterface, NavigationItemPosition, NavigationWidget, MessageBox, InfoBar,
                            isDarkTheme, qrouter)


# coding:utf-8

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


class Widget(QFrame):

    def __init__(self, text: str, parent=None):
        super().__init__(parent=parent)
        self.setObjectName(text.replace(' ', '-'))
        self.label = QLabel(text, self)
        self.label.setAlignment(Qt.AlignCenter)
        self.hBoxLayout = QHBoxLayout(self)
        self.hBoxLayout.addWidget(self.label, 1, Qt.AlignCenter)

        # leave some space for title bar
        self.hBoxLayout.setContentsMargins(0, 32, 0, 0)


class AvatarWidget(NavigationWidget):
    """ Avatar widget """

    def __init__(self, parent=None):
        super().__init__(isSelectable=False, parent=parent)
        shoko_path = resource_path('resource/shoko.png')
        self.avatar = QImage(shoko_path).scaled(
            24, 24, Qt.KeepAspectRatio, Qt.SmoothTransformation)

    def paintEvent(self, e):
        painter = QPainter(self)
        painter.setRenderHints(
            QPainter.SmoothPixmapTransform | QPainter.Antialiasing)

        painter.setPen(Qt.NoPen)

        if self.isPressed:
            painter.setOpacity(0.7)

        # draw background
        if self.isEnter:
            c = 255 if isDarkTheme() else 0
            painter.setBrush(QColor(c, c, c, 10))
            painter.drawRoundedRect(self.rect(), 5, 5)

        # draw avatar
        painter.setBrush(QBrush(self.avatar))
        painter.translate(8, 6)
        painter.drawEllipse(0, 0, 24, 24)
        painter.translate(-8, -6)

        if not self.isCompacted:
            painter.setPen(Qt.white if isDarkTheme() else Qt.black)
            font = QFont()
            font.setPixelSize(14)
            painter.setFont(font)
            painter.drawText(QRect(44, 0, 255, 36), Qt.AlignVCenter, 'a奥巴熊🐻')


class CustomTitleBar(TitleBar):
    """ Title bar with icon and title """

    def __init__(self, parent):
        super().__init__(parent)
        # add window icon
        self.iconLabel = QLabel(self)
        self.iconLabel.setFixedSize(18, 18)
        self.hBoxLayout.insertSpacing(0, 10)
        self.hBoxLayout.insertWidget(1, self.iconLabel, 0, Qt.AlignLeft | Qt.AlignBottom)
        self.window().windowIconChanged.connect(self.setIcon)

        # add title label
        self.titleLabel = QLabel(self)
        self.hBoxLayout.insertWidget(2, self.titleLabel, 0, Qt.AlignLeft | Qt.AlignBottom)
        self.titleLabel.setObjectName('titleLabel')
        self.window().windowTitleChanged.connect(self.setTitle)

    def setTitle(self, title):
        self.titleLabel.setText(title)
        self.titleLabel.adjustSize()

    def setIcon(self, icon):
        self.iconLabel.setPixmap(QIcon(icon).pixmap(18, 18))


class AddOrderInterface(QWidget):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.setObjectName('AddOrderInterface')
        self.db = db
        self.initUI1()

    def initUI1(self):
        self.setWindowTitle('供应商供货进度表')
        self.setGeometry(100, 100, 1000, 600)

        main_layout = QVBoxLayout()

        font = QFont()

        font.setPointSize(14)  # 设置字体大小
        font.setBold(True)
        # 订单信息部分
        order_info_layout = QVBoxLayout()
        order_info_label = QLabel('订单信息')
        order_info_label.setFont(font)
        order_info_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        order_info_layout.addWidget(order_info_label)
        order_info_layout.setContentsMargins(10, 20, 10, 10)

        font.setPointSize(12)

        form_layout = QGridLayout()
        form_layout.setHorizontalSpacing(10)
        form_layout.setVerticalSpacing(20)
        form_layout.setContentsMargins(30, 0, 30, 30)

        form_layout.addWidget(QLabel('订单名称'), 0, 0)
        self.order_name_input = LineEdit()
        form_layout.addWidget(self.order_name_input, 0, 1)

        form_layout.addWidget(QLabel('客户名称'), 0, 2)
        self.customer_name_input = LineEdit()
        form_layout.addWidget(self.customer_name_input, 0, 3)

        form_layout.addWidget(QLabel('交货日期'), 1, 0)
        self.delivery_date_input = CalendarPicker(self)
        form_layout.addWidget(self.delivery_date_input, 1, 1)

        form_layout.addWidget(QLabel('销售员'), 1, 2)
        self.salesperson_input = LineEdit()
        form_layout.addWidget(self.salesperson_input, 1, 3)

        form_layout.addWidget(QLabel('订单金额'), 2, 0)
        self.order_amount_input = LineEdit()
        form_layout.addWidget(self.order_amount_input, 2, 1)

        order_info_layout.addLayout(form_layout)
        self.add_order_button = PrimaryPushButton(FIF.ADD, '新增订单')
        self.add_order_button.setFixedSize(110, 30)
        self.add_order_button.clicked.connect(self.add_order)
        form_layout.addWidget(self.add_order_button, 2, 3, alignment=Qt.AlignRight)

        main_layout.addLayout(order_info_layout)

        # 零件信息部分
        part_info_layout = QVBoxLayout()
        part_info_label = QLabel('零件信息')
        part_info_label.setFont(font)
        part_info_layout.addWidget(part_info_label)
        part_info_layout.setContentsMargins(10, 20, 10, 10)

        form_layout = QGridLayout()
        form_layout.setHorizontalSpacing(10)
        form_layout.setVerticalSpacing(20)
        form_layout.setContentsMargins(30, 0, 30, 30)

        form_layout.addWidget(QLabel('订单名称'), 0, 0)
        self.order_name_combobox = ComboBox()
        form_layout.addWidget(self.order_name_combobox, 0, 1)
        self.order_name_combobox.setCurrentIndex(-1)

        form_layout.addWidget(QLabel('部件名称'), 0, 2)
        self.part_name_input = LineEdit()
        form_layout.addWidget(self.part_name_input, 0, 3)

        form_layout.addWidget(QLabel('供应商'), 1, 0)
        self.supplier_input = LineEdit()
        form_layout.addWidget(self.supplier_input, 1, 1)

        form_layout.addWidget(QLabel('计划交期'), 1, 2)
        self.planned_delivery_date_input = CalendarPicker(self)
        form_layout.addWidget(self.planned_delivery_date_input, 1, 3)
        self.planned_delivery_date_input.dateChanged.connect(self.sync_actual_delivery_date)

        form_layout.addWidget(QLabel('实际交货日期'), 2, 0)
        self.actual_delivery_date_input = CalendarPicker(self)
        form_layout.addWidget(self.actual_delivery_date_input, 2, 1)

        form_layout.addWidget(QLabel('交货情况'), 2, 2)
        self.delivery_status_combobox = ComboBox()
        self.delivery_status_combobox.addItems(['交货', '未交货'])
        form_layout.addWidget(self.delivery_status_combobox, 2, 3)


        # order_info_layout.addLayout(form_layout)
        # self.add_order_button = PrimaryPushButton(FIF.ADD, '新增订单')
        # self.add_order_button.setFixedSize(110, 30)
        # self.add_order_button.clicked.connect(self.add_order)
        # form_layout.addWidget(self.add_order_button, 2, 3, alignment=Qt.AlignRight)

        part_info_layout.addLayout(form_layout)
        self.add_part_button = PrimaryPushButton(FIF.ADD, '新增部件')
        self.add_order_button.setFixedSize(110, 30)
        self.add_part_button.clicked.connect(self.add_order_part)
        form_layout.addWidget(self.add_part_button, 3, 3, alignment=Qt.AlignRight)

        main_layout.addLayout(part_info_layout)

        container = QWidget()
        container.setLayout(main_layout)
        self.setLayout(main_layout)

        self.update_order_names()

    def sync_actual_delivery_date(self, date):
        self.actual_delivery_date_input.setDate(date)

    def update_order_names(self):
        order_names = self.db.fetch_order_names()
        self.order_name_combobox.clear()
        for name in order_names.values():
            self.order_name_combobox.addItem(name)
        self.order_name_combobox.setCurrentIndex(-1)

    def add_order(self):
        order_name = self.order_name_input.text()
        customer_name = self.customer_name_input.text()
        delivery_date = self.delivery_date_input.getDate().toString('yyyy-MM-dd')
        salesperson = self.salesperson_input.text()
        order_amount = self.order_amount_input.text()
        if not order_name:
            InfoBar.error(
                title='错误',
                content='订单名称不能为空！',
                orient=Qt.Horizontal,
                isClosable=True,
                duration=2000,
                parent=self
            )
            return
        success = self.db.add_order(order_name, customer_name, delivery_date, salesperson, order_amount)
        if success:
            InfoBar.success(
                title='成功',
                content='订单添加成功！',
                orient=Qt.Horizontal,
                isClosable=True,
                duration=2000,
                parent=self
            )
            self.order_name_input.clear()
            self.customer_name_input.clear()
            self.delivery_date_input.setDate(QDate())  # 设置为空白日期
            self.salesperson_input.clear()
            self.update_order_names()

    def add_order_part(self):
        order_name = self.order_name_combobox.currentText()
        if not order_name:
            InfoBar.error(
                title='错误',
                content='订单名称不能为空！',
                orient=Qt.Horizontal,
                isClosable=True,
                duration=2000,
                parent=self
            )
            return
        order_id = list(self.db.fetch_order_names().keys())[
            list(self.db.fetch_order_names().values()).index(order_name)]
        part_name = self.part_name_input.text()
        supplier = self.supplier_input.text()
        planned_delivery_date = self.planned_delivery_date_input.getDate().toString('yyyy-MM-dd')
        actual_delivery_date = self.actual_delivery_date_input.getDate().toString('yyyy-MM-dd')
        delivery_status = self.delivery_status_combobox.currentText()
        if not part_name:
            InfoBar.error(
                title='错误',
                content='零件名称不能为空！',
                orient=Qt.Horizontal,
                isClosable=True,
                duration=2000,
                parent=self
            )
            return
        success = self.db.add_order_part(order_id, part_name, supplier, planned_delivery_date, actual_delivery_date,
                                         delivery_status)
        if success:
            InfoBar.success(
                title='成功',
                content='部件添加成功！',
                orient=Qt.Horizontal,
                isClosable=True,
                duration=2000,
                parent=self
            )
            self.order_name_combobox.setCurrentIndex(-1)
            self.part_name_input.clear()
            self.supplier_input.clear()
            self.planned_delivery_date_input.setDate(QDate())
            self.actual_delivery_date_input.setDate(QDate())
            self.delivery_status_combobox.setCurrentIndex(-1)
        else:
            InfoBar.error(
                title='错误',
                content='未找到订单编号对应的交货日期',
                orient=Qt.Horizontal,
                isClosable=True,
                duration=2000,
                parent=self
            )


class DateDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        editor = QDateEdit(parent)
        editor.setDisplayFormat('yyyy-MM-dd')
        editor.setCalendarPopup(True)
        return editor

    def setEditorData(self, editor, index):
        date_str = index.model().data(index, Qt.EditRole)
        if date_str:
            editor.setDate(QDate.fromString(date_str, 'yyyy-MM-dd'))
        else:
            editor.setDate(QDate.currentDate())

    def setModelData(self, editor, model, index):
        date = editor.date().toString('yyyy-MM-dd')
        model.setData(index, date, Qt.EditRole)

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)


class MaintenanceInterface(QWidget):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.setObjectName('MaintenanceInterface')
        self.db = db
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        font = QFont()
        font.setPointSize(12)

        # 订单信息部分
        order_info_layout = QVBoxLayout()

        form_layout = QGridLayout()
        form_layout.setHorizontalSpacing(10)
        form_layout.setVerticalSpacing(20)
        form_layout.setContentsMargins(30, 30, 30, 30)

        form_layout.addWidget(QLabel('订单名称'), 0, 0, Qt.AlignRight)
        self.maintenance_order_combobox = ComboBox()
        form_layout.addWidget(self.maintenance_order_combobox, 0, 1)
        self.maintenance_order_combobox.currentIndexChanged.connect(self.load_order_parts)

        form_layout.setColumnStretch(1, 2)  # 设置第2列的伸展因子

        order_info_layout.addLayout(form_layout)
        layout.addLayout(order_info_layout)

        self.tableView = QTableWidget()
        self.tableView.setColumnCount(7)
        self.tableView.setHorizontalHeaderLabels(
            ['零件ID', '零件名称', '供应商', '计划交期', '实际交货日期', '交货情况', '交期偏差率'])
        self.tableView.setWordWrap(False)

        # 设置日期委托
        date_delegate = DateDelegate()
        self.tableView.setItemDelegateForColumn(3, date_delegate)
        self.tableView.setItemDelegateForColumn(4, date_delegate)

        layout.addWidget(self.tableView)

        buttons_layout = QHBoxLayout()
        self.save_button = PushButton('保存信息')
        self.save_button.clicked.connect(self.save_data)
        self.delete_order_button = PushButton('删除订单')
        self.delete_order_button.clicked.connect(self.delete_order)
        self.delete_part_button = PushButton('删除零件')
        self.delete_part_button.clicked.connect(self.delete_selected_part)

        buttons_layout.addWidget(self.save_button)
        buttons_layout.addWidget(self.delete_order_button)
        buttons_layout.addWidget(self.delete_part_button)
        layout.addLayout(buttons_layout)

        self.setLayout(layout)
        self.update_order_names()

        # 设置样式表
        self.tableView.setStyleSheet("""
            QTableWidget {
                border: 1px solid #dcdcdc;
                border-radius: 8px;
            }
        """)

    def update_order_names(self):
        order_names = self.db.fetch_order_names()
        self.maintenance_order_combobox.clear()
        self.maintenance_order_combobox.addItem('')  # 添加一个空选项
        for name in order_names.values():
            self.maintenance_order_combobox.addItem(name)
        self.maintenance_order_combobox.setCurrentIndex(-1)  # 设置默认值为空

    def load_order_parts(self):
        order_name = self.maintenance_order_combobox.currentText()
        if not order_name:
            self.tableView.setRowCount(0)
            return

        order_id = list(self.db.fetch_order_names().keys())[
            list(self.db.fetch_order_names().values()).index(order_name)]
        parts = self.db.fetch_order_parts(order_id)

        self.tableView.setRowCount(0)
        for part in parts:
            row_position = self.tableView.rowCount()
            self.tableView.insertRow(row_position)
            for i, item in enumerate(part):
                self.tableView.setItem(row_position, i, QTableWidgetItem(str(item)))

    def save_data(self):
        for row in range(self.tableView.rowCount()):
            part_id = self.tableView.item(row, 0).text()
            part_name = self.tableView.item(row, 1).text()
            supplier = self.tableView.item(row, 2).text()
            planned_delivery_date = self.tableView.item(row, 3).text()
            actual_delivery_date = self.tableView.item(row, 4).text()
            delivery_status = self.tableView.item(row, 5).text()

            self.db.update_order_part(part_id, part_name, supplier, planned_delivery_date, actual_delivery_date,
                                      delivery_status)
        self.load_order_parts()

        InfoBar.success(
            title='成功',
            content='数据保存成功！',
            orient=Qt.Horizontal,
            isClosable=True,
            duration=2000,
            parent=self
        )

    def delete_order(self):
        order_name = self.maintenance_order_combobox.currentText()
        if not order_name:
            InfoBar.error(
                title='错误',
                content='请选择一个订单',
                orient=Qt.Horizontal,
                isClosable=True,
                duration=2000,
                parent=self
            )
            return

        w = MessageBox(
            '确认删除',
            '删除订单会将订单以及对应零件信息都删除掉，确定要删除吗？',
            self
        )
        w.yesButton.setText('确定')
        w.cancelButton.setText('取消')

        if w.exec_() == QDialog.Accepted:
            order_id = list(self.db.fetch_order_names().keys())[
                list(self.db.fetch_order_names().values()).index(order_name)]
            self.db.delete_order(order_id)
            self.update_order_names()
            self.tableView.setRowCount(0)
            InfoBar.success(
                title='成功',
                content='订单及对应零件信息删除成功！',
                orient=Qt.Horizontal,
                isClosable=True,
                duration=2000,
                parent=self
            )

    def delete_selected_part(self):
        selected_row = self.tableView.currentRow()
        if selected_row >= 0:
            part_id = self.tableView.item(selected_row, 0).text()
            self.db.delete_order_part(part_id)
            self.tableView.removeRow(selected_row)
            InfoBar.success(
                title='成功',
                content='零件删除成功！',
                orient=Qt.Horizontal,
                isClosable=True,
                duration=2000,
                parent=self
            )


class OverviewPage(QWidget):
    def __init__(self, db, parent=None):
        super().__init__(parent=parent)
        self.setObjectName('OverviewPage')
        self.db = db
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout(self)

        # 创建滚动区域
        scroll_area = ScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("QScrollArea { border: none; }")  # 隐藏边框
        scroll_content = QWidget(scroll_area)
        scroll_layout = QGridLayout(scroll_content)
        scroll_content.setLayout(scroll_layout)
        scroll_area.setWidget(scroll_content)

        # 添加滚动区域到主布局
        layout.addWidget(scroll_area)

        self.setLayout(layout)
        self.plot_data(scroll_layout)

    def plot_data(self, layout=None):
        # 设置字体
        rcParams['font.sans-serif'] = ['SimHei']  # 使用SimHei字体
        rcParams['axes.unicode_minus'] = False  # 正常显示负号

        if layout is None:
            layout = self.layout().itemAt(0).widget().widget().layout()

            # 清空布局中的所有控件
        for i in reversed(range(layout.count())):
            widget_to_remove = layout.itemAt(i).widget()
            layout.removeWidget(widget_to_remove)
            widget_to_remove.setParent(None)

        data = self.db.get_order_deviation_data()

        max_plots_per_page = 6
        cols = 2  # 每行显示两个图表

        for index, order_data in enumerate(data):
            order_name = order_data[0]
            part_deviations = order_data[1]  # 假设 part_deviations 是一个列表，每个元素是 (零件名, 偏差率)

            part_names = [part[0] for part in part_deviations]
            deviations = [part[1] for part in part_deviations]

            figure = Figure(figsize=(5, 4))
            canvas = FigureCanvas(figure)

            ax = figure.add_subplot(1, 1, 1)
            ax.clear()

            # 绘制条形图
            bars = ax.bar(part_names, deviations, color='#1f77b4')

            # 添加数据标签
            for bar in bars:
                yval = bar.get_height()
                ax.text(bar.get_x() + bar.get_width() / 2, yval, round(yval, 2), va='bottom')  # va: vertical alignment

            # 添加网格线
            ax.yaxis.set_major_locator(MaxNLocator(integer=True))
            ax.grid(True, which='both', linestyle='--', linewidth=0.5)

            # 设置标签和标题
            ax.set_xlabel('零件名称', fontsize=10)
            ax.set_ylabel('交期偏差率', fontsize=10)
            ax.set_title(f'订单{order_name}的零部件交期偏差率', fontsize=12, fontweight='bold')

            # 设置上下边距
            plot_widget = QWidget()
            plot_layout = QVBoxLayout()
            plot_layout.addWidget(canvas)
            plot_layout.setContentsMargins(0, 20, 0, 20)  # 设置上下边距
            plot_widget.setLayout(plot_layout)
            plot_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

            row = index // cols
            col = index % cols
            layout.addWidget(plot_widget, row, col)

        layout.setRowStretch((len(data) + 1) // cols, 1)


class Window(FramelessWindow):

    def __init__(self):
        super().__init__()
        self.setTitleBar(CustomTitleBar(self))

        # use dark theme mode
        # setTheme(Theme.DARK)

        self.db = Database()

        self.hBoxLayout = QHBoxLayout(self)
        self.navigationInterface = NavigationInterface(
            self, showMenuButton=True, showReturnButton=True)
        self.stackWidget = QStackedWidget(self)

        # create sub interface
        self.overviewInterface = OverviewPage(self.db, self)
        self.addOrderInterface = AddOrderInterface(self.db, self)
        self.maintenanceInterface = MaintenanceInterface(self.db, self)

        # initialize layout
        self.initLayout()

        # add items to navigation interface
        self.initNavigation()

        self.initWindow()

    def initLayout(self):
        self.hBoxLayout.setSpacing(0)
        self.hBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.hBoxLayout.addWidget(self.navigationInterface)
        self.hBoxLayout.addWidget(self.stackWidget)
        self.hBoxLayout.setStretchFactor(self.stackWidget, 1)

        self.titleBar.raise_()
        self.navigationInterface.displayModeChanged.connect(self.titleBar.raise_)

    def initNavigation(self):
        # enable acrylic effect
        # self.navigationInterface.setAcrylicEnabled(True)

        self.addSubInterface(self.overviewInterface, FIF.HOME, '数据总览', NavigationItemPosition.SCROLL)
        self.addSubInterface(self.addOrderInterface, FIF.ADD, '新增订单', NavigationItemPosition.SCROLL)
        self.addSubInterface(self.maintenanceInterface, FIF.LABEL, '数据维护', NavigationItemPosition.SCROLL)

        self.navigationInterface.addSeparator()

        # add custom widget to bottom
        self.navigationInterface.addWidget(
            routeKey='avatar',
            widget=AvatarWidget(),
            onClick=self.showMessageBox,
            position=NavigationItemPosition.BOTTOM
        )

        # !IMPORTANT: don't forget to set the default route key
        qrouter.setDefaultRouteKey(self.stackWidget, self.overviewInterface.objectName())

        self.stackWidget.currentChanged.connect(self.onCurrentInterfaceChanged)
        self.stackWidget.setCurrentIndex(0)

    def initWindow(self):
        self.resize(900, 700)
        qico_path = resource_path('resource/logo.png')
        self.setWindowIcon(QIcon(qico_path))
        self.setWindowTitle('供应商供货进度表')
        self.titleBar.setAttribute(Qt.WA_StyledBackground)

        desktop = QApplication.desktop().availableGeometry()
        w, h = desktop.width(), desktop.height()
        self.move(w // 2 - self.width() // 2, h // 2 - self.height() // 2)

        self.setQss()

    def addSubInterface(self, interface, icon, text: str, position=NavigationItemPosition.TOP):
        print(interface.objectName())
        print(1)
        """ add sub interface """
        self.stackWidget.addWidget(interface)
        self.navigationInterface.addItem(
            routeKey=interface.objectName(),
            icon=icon,
            text=text,
            onClick=lambda: self.switchTo(interface),
            position=position,
            tooltip=text
        )

    def setQss(self):
        color = 'dark' if isDarkTheme() else 'light'
        color_path = resource_path(f'resource/{color}/demo.qss')
        with open(color_path, encoding='utf-8') as f:
            self.setStyleSheet(f.read())

    def switchTo(self, widget):
        self.stackWidget.setCurrentWidget(widget)
        if widget.objectName() == 'MaintenanceInterface':
            widget.update_order_names()
        if widget.objectName() == 'OverviewPage':
            widget.plot_data()  # 切换到数据总览界面时刷新图表

    def onCurrentInterfaceChanged(self, index):
        widget = self.stackWidget.widget(index)
        self.navigationInterface.setCurrentItem(widget.objectName())
        qrouter.push(self.stackWidget, widget.objectName())

    def showMessageBox(self):
        w = MessageBox(
            '问题反馈作者🥰',
            '如果这个项目遇到任何问题可以直接反馈作者。您的支持就是作者开发和维护项目的动力🚀',
            self
        )
        w.yesButton.setText('来啦老弟')
        w.cancelButton.setText('真棒')

        if w.exec():
            QDesktopServices.openUrl(QUrl("https://github.com/robertshuai"))

    def resizeEvent(self, e):
        self.titleBar.move(46, 0)
        self.titleBar.resize(self.width() - 46, self.titleBar.height())


if __name__ == '__main__':
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)

    app = QApplication(sys.argv)
    w = Window()
    w.show()
    app.exec_()
