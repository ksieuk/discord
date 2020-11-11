import sys
import sqlite3

from PyQt5 import uic
from PyQt5.QtWidgets import QWidget, QTableWidgetItem, QApplication
from PyQt5.QtGui import QPixmap

from PyQt5.QtWidgets import QApplication, QWidget, QPushButton
from PyQt5.QtWidgets import QLabel, QLineEdit, QLCDNumber
import user_info

class TitlePage(QWidget):
    def __init__(self, database_name):
        super().__init__()
        uic.loadUi(r'materials\main.ui', self)
        self.pixmap = QPixmap(r'materials\background.jpg')  # установка фона
        self.background.setPixmap(self.pixmap)

        self.base_discord = sqlite3.connect(database_name)  # подключение к бд
        cur = self.base_discord.cursor()
        self.users = cur.execute("SELECT nickname, id FROM users").fetchall()  # получение данных

        self.users_all.activated[int].connect(self.add_user)
        self.list_users.itemClicked.connect(self.remove_user)
        self.pushButton_add_everyone.clicked.connect(self.add_all_users)
        self.pushButton_remove_everyone.clicked.connect(self.remove_all_users)
        self.pushButton_remove_everyone_info.clicked.connect(self.get_users_info)

        self.selected_users = {}  # выбранные пользователи (id: nick)

        self.load_base()

    def load_base(self):
        """добавление всех юзеров в выпадающий список"""

        for elem in self.users:
            self.users_all.addItem(elem[0], [elem[1]])

    def add_user(self, index):
        """отображение выбранных юзеров"""

        user_id = self.users_all.itemData(index)
        if user_id not in self.selected_users.values():
            item = self.users_all.itemText(index)
            self.selected_users[item] = user_id
            self.list_users.addItem(item)

    def add_all_users(self):
        """отображение всех юзеров"""

        for i in range(len(self.users)):
            user_id = self.users_all.itemData(i)
            if user_id not in self.selected_users.values():
                nick = self.users_all.itemText(i)
                self.list_users.addItem(nick)
                self.selected_users[nick] = user_id

    def remove_user(self, item):
        """удаление выбранных юзеров"""

        del self.selected_users[item.text()]
        self.list_users.takeItem(self.list_users.row(item))

    def remove_all_users(self):
        """удаление всех юзеров"""

        self.list_users.clear()
        self.selected_users.clear()

    def get_users_info(self):
        # self.close()
        # self.twoWindow = Example()
        # self.twoWindow.show()
        self.pages.setCurrentIndex(1)

# import test2
# main_window.pushButton.clicked.connect(lambda: test2.new_form(main_window))

BASE_NAME = r"materials\discord.db"

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = TitlePage(BASE_NAME)
    ex.show()
    sys.exit(app.exec())
