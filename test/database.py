import sqlite3
from PyQt5.QtCore import QDate

class Database:
    _instance = None

    def __new__(cls, db_name='supply_progress.db'):
        if cls._instance is None:
            cls._instance = super(Database, cls).__new__(cls)
            cls._instance.conn = sqlite3.connect(db_name)
            cls._instance.c = cls._instance.conn.cursor()
            cls._instance.initialize_database()
        return cls._instance

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.conn.close()
        Database._instance = None

    def initialize_database(self):
        self.create_tables()
        self.add_amount_column_if_not_exists()

    def create_tables(self):
        CREATE_ORDERS_TABLE = '''CREATE TABLE IF NOT EXISTS orders (
                                    order_id INTEGER PRIMARY KEY,
                                    order_name TEXT NOT NULL,
                                    customer_name TEXT NOT NULL,
                                    delivery_date DATE NOT NULL,
                                    salesperson TEXT NOT NULL,
                                    order_amount REAL)'''  # Added order_amount column
        CREATE_ORDER_PARTS_TABLE = '''CREATE TABLE IF NOT EXISTS order_parts (
                                        part_id INTEGER PRIMARY KEY,
                                        order_id INTEGER NOT NULL,
                                        part_name TEXT NOT NULL,
                                        supplier TEXT NOT NULL,
                                        planned_delivery_date DATE NOT NULL,
                                        actual_delivery_date DATE,
                                        delivery_status TEXT NOT NULL,
                                        delivery_deviation REAL,
                                        FOREIGN KEY(order_id) REFERENCES orders(order_id))'''

        self.c.execute(CREATE_ORDERS_TABLE)
        self.c.execute(CREATE_ORDER_PARTS_TABLE)
        self.conn.commit()

    def add_amount_column_if_not_exists(self):
        try:
            self.c.execute('ALTER TABLE orders ADD COLUMN order_amount REAL')
            self.conn.commit()
        except sqlite3.OperationalError:
            # Column already exists, ignore the error
            pass

    def fetch_order_names(self):
        self.c.execute('SELECT order_id, order_name FROM orders')
        orders = self.c.fetchall()
        return {order_id: order_name for order_id, order_name in orders}

    def fetch_order_parts(self, order_id):
        self.c.execute(
            'SELECT part_id, part_name, supplier, planned_delivery_date, actual_delivery_date, delivery_status, delivery_deviation FROM order_parts WHERE order_id = ?',
            (order_id,))
        parts = self.c.fetchall()
        return parts

    def add_order(self, order_name, customer_name, delivery_date, salesperson, order_amount):
        try:
            self.c.execute(
                'INSERT INTO orders (order_name, customer_name, delivery_date, salesperson, order_amount) VALUES (?, ?, ?, ?, ?)',
                (order_name, customer_name, delivery_date, salesperson, order_amount))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Error adding order: {e}")

    def calculate_delivery_deviation(self, planned_date, actual_date):
        if planned_date and actual_date:
            planned_date_dt = QDate.fromString(planned_date, 'yyyy-MM-dd')
            actual_date_dt = QDate.fromString(actual_date, 'yyyy-MM-dd')
            deviation = (actual_date_dt.toJulianDay() - planned_date_dt.toJulianDay()) / 30.0
            return max(deviation, 0.0)
        return 0.0

    def add_order_part(self, order_id, part_name, supplier, planned_delivery_date, actual_delivery_date,
                       delivery_status):
        delivery_deviation = self.calculate_delivery_deviation(planned_delivery_date, actual_delivery_date)

        self.c.execute(
            'INSERT INTO order_parts (order_id, part_name, supplier, planned_delivery_date, actual_delivery_date, delivery_status, delivery_deviation) VALUES (?, ?, ?, ?, ?, ?, ?)',
            (order_id, part_name, supplier, planned_delivery_date, actual_delivery_date, delivery_status,
             delivery_deviation))
        self.conn.commit()
        return True

    def update_order_part(self, part_id, part_name, supplier, planned_delivery_date, actual_delivery_date,
                          delivery_status):
        self.c.execute('SELECT planned_delivery_date, actual_delivery_date FROM order_parts WHERE part_id = ?',
                       (part_id,))
        result = self.c.fetchone()

        if result:
            stored_planned_delivery_date, stored_actual_delivery_date = result

            planned_delivery_date = planned_delivery_date if planned_delivery_date else stored_planned_delivery_date
            actual_delivery_date = actual_delivery_date if actual_delivery_date else stored_actual_delivery_date

            delivery_deviation = self.calculate_delivery_deviation(planned_delivery_date, actual_delivery_date)

            self.c.execute(
                'UPDATE order_parts SET part_name = ?, supplier = ?, planned_delivery_date = ?, actual_delivery_date = ?, delivery_status = ?, delivery_deviation = ? WHERE part_id = ?',
                (part_name, supplier, planned_delivery_date, actual_delivery_date, delivery_status, delivery_deviation,
                 part_id))
            self.conn.commit()
            return True
        else:
            return False

    def delete_order_part(self, part_id):
        self.c.execute('DELETE FROM order_parts WHERE part_id = ?', (part_id,))
        self.conn.commit()

    def get_order_deviation_data(self):
        self.c.execute('''
            SELECT orders.order_name, order_parts.part_name, order_parts.delivery_deviation 
            FROM orders 
            JOIN order_parts ON orders.order_id = order_parts.order_id
        ''')
        data = self.c.fetchall()

        order_data = {}
        for order_name, part_name, deviation in data:
            if order_name not in order_data:
                order_data[order_name] = []
            order_data[order_name].append((part_name, deviation))

        result = [(order_name, parts) for order_name, parts in order_data.items()]
        return result

    def delete_order(self, order_id):
        try:
            self.c.execute('DELETE FROM order_parts WHERE order_id = ?', (order_id,))
            self.c.execute('DELETE FROM orders WHERE order_id = ?', (order_id,))
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"Error deleting order: {e}")
