from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QComboBox, QDateEdit, QTableWidget, QTableWidgetItem, QHBoxLayout
from PyQt5.QtCore import QDate, Qt
from PyQt5.QtGui import QFont
from qfluentwidgets import InfoBar

class AddOrderInterface(QWidget):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        font = QFont()
        font.setPointSize(12)

        order_info_layout = QVBoxLayout()
        order_info_label = QLabel('订单信息')
        order_info_label.setFont(font)
        order_info_layout.addWidget(order_info_label)

        form_layout = QHBoxLayout()
        form_layout.addWidget(QLabel('订单名称'))
        self.order_name_input = QLineEdit()
        form_layout.addWidget(self.order_name_input)

        form_layout.addWidget(QLabel('客户名称'))
        self.customer_name_input = QLineEdit()
        form_layout.addWidget(self.customer_name_input)

        form_layout.addWidget(QLabel('交货日期'))
        self.delivery_date_input = QDateEdit()
        self.delivery_date_input.setCalendarPopup(True)
        self.delivery_date_input.setDate(QDate.currentDate())
        form_layout.addWidget(self.delivery_date_input)

        form_layout.addWidget(QLabel('销售员'))
        self.salesperson_input = QLineEdit()
        form_layout.addWidget(self.salesperson_input)

        order_info_layout.addLayout(form_layout)
        self.add_order_button = QPushButton('新增订单')
        self.add_order_button.clicked.connect(self.add_order)
        order_info_layout.addWidget(self.add_order_button)

        layout.addLayout(order_info_layout)
        self.setLayout(layout)

    def add_order(self):
        order_name = self.order_name_input.text()
        customer_name = self.customer_name_input.text()
        delivery_date = self.delivery_date_input.date().toString('yyyy-MM-dd')
        salesperson = self.salesperson_input.text()

        self.db.add_order(order_name, customer_name, delivery_date, salesperson)
        InfoBar.success(
            title='成功',
            content='订单添加成功！',
            orient=Qt.Horizontal,
            isClosable=True,
            duration=2000,
            parent=self
        )
        self.update_order_names()

    def update_order_names(self):
        # Your implementation to update order names
        pass

class MaintenanceInterface(QWidget):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        font = QFont()
        font.setPointSize(12)

        maintenance_layout = QVBoxLayout()
        maintenance_label = QLabel('数据维护')
        maintenance_label.setFont(font)
        maintenance_layout.addWidget(maintenance_label)

        form_layout = QHBoxLayout()
        form_layout.addWidget(QLabel('订单名称'))
        self.maintenance_order_combobox = QComboBox()
        form_layout.addWidget(self.maintenance_order_combobox)

        self.load_parts_button = QPushButton('加载零件')
        self.load_parts_button.clicked.connect(self.load_order_parts)
        form_layout.addWidget(self.load_parts_button)

        maintenance_layout.addLayout(form_layout)

        self.parts_table = QTableWidget()
        self.parts_table.setColumnCount(6)
        self.parts_table.setHorizontalHeaderLabels(
            ['零件ID', '零件名称', '供应商', '计划交期', '实际交货日期', '交货情况'])
        maintenance_layout.addWidget(self.parts_table)

        layout.addLayout(maintenance_layout)
        self.setLayout(layout)

    def load_order_parts(self):
        order_name = self.maintenance_order_combobox.currentText()
        order_id = list(self.db.fetch_order_names().keys())[
            list(self.db.fetch_order_names().values()).index(order_name)]
        parts = self.db.fetch_order_parts(order_id)

        self.parts_table.setRowCount(0)
        for part in parts:
            row_position = self.parts_table.rowCount()
            self.parts_table.insertRow(row_position)
            for i, item in enumerate(part):
                self.parts_table.setItem(row_position, i, QTableWidgetItem(str(item)))
