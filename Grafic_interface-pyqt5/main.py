import sys
import sqlite3
from loguru import logger

from PyQt5 import uic
from PyQt5.QtCore import QSize, QTimer
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtGui import QPixmap, QIcon


class TitlePage(QMainWindow):
    def __init__(self):
        database_name = r"materials\discord.db"
        super().__init__()

        self.database_name = database_name
        self.selected_users = {}  # выбранные пользователи (id: nick)

        self.base_discord = sqlite3.connect(self.database_name)  # подключение к бд
        cur = self.base_discord.cursor()
        self.users_base = cur.execute("SELECT * FROM users").fetchall()  # получение данных

        self.initUI()

    def initUI(self):
        """Подключение виджетов из UI файла"""

        uic.loadUi(r'materials\main.ui', self)  # подключение UI
        pixmap = QPixmap(r'materials\background.jpg')  # установка фона
        self.background.setPixmap(pixmap)

        self.users_all.activated[int].connect(self.add_user)
        self.list_users.itemClicked.connect(self.remove_user)
        self.pb_add_everyone.clicked.connect(self.add_all_users)
        self.pb_remove_everyone.clicked.connect(self.remove_all_users)
        self.pb_info_about_all.clicked.connect(self.get_users_info)
        self.pb_exit.clicked.connect(self.finish)

        self.load_base()

    def load_base(self):
        """добавление всех юзеров в выпадающий список"""

        for elem in self.users_base:
            self.users_all.addItem(elem[1], [elem[0]])

    def add_user(self, index: int):
        """отображение выбранных юзеров"""

        user_id = self.users_all.itemData(index)[0]
        if user_id not in self.selected_users.values():
            item = self.users_all.itemText(index)
            self.selected_users[item] = user_id  # запись в список выбранных пользователей
            self.list_users.addItem(item)  # отображение на экране

    def add_all_users(self):
        """отображение всех юзеров"""

        for i in range(len(self.users_base)):
            user_id = self.users_all.itemData(i)[0]
            if user_id not in self.selected_users.values():
                nick = self.users_all.itemText(i)
                self.list_users.addItem(nick)  # отображение на экране
                self.selected_users[nick] = user_id  # запись в список выбранных пользователей

    def remove_user(self, item):
        """удаление выбранных юзеров"""

        del self.selected_users[item.text()]  # удаление пользователя из списка выбранных
        self.list_users.takeItem(self.list_users.row(item))

    def remove_all_users(self):
        """удаление всех юзеров"""

        self.list_users.clear()
        self.selected_users.clear()

    def get_users_info(self):
        """Открывает окно с информацией о пользователях"""

        for user in self.selected_users.items():  # user - пользователь из списка выбранных
            # информация о пользователе из базы данных
            user_info = tuple(filter(lambda x: user[1] in x, self.users_base))[0]
            ex1 = UserInfo(self, user_info=user_info, database=self.base_discord)
            ex1.setWindowTitle(user[0])
            ex1.show()

    def finish(self):
        """Завершение программы"""

        self.base_discord.close()
        logger.info("Выполнение программы завершено\n")
        app.quit()


class UserInfo(QMainWindow):
    def __init__(self, *args, user_info: list, database):

        super().__init__(*args)
        self.user_info, self.database = user_info, database
        self.xp = self.lvl = self.money = None

        self.is_balance_error = self.is_xp_error = self.is_big_level_error = False
        self.initUI()

    def initUI(self):
        """Подключение виджетов из UI файла"""

        uic.loadUi(r'materials\user_info.ui', self)  # подключение UI
        pixmap = QPixmap(r'materials\widget_bg.jpg')  # установка фона
        self.background.setPixmap(pixmap)
        self.pb_money.setIcon(QIcon(r'materials/fastener.png'))  # установка застежки для кошелька
        self.pb_money.setIconSize(QSize(295, 113))

        self.label_nickname.setText(self.user_info[1])  # ник пользователя
        self.label_lvl_now.setText(str(self.user_info[6]))  # уровень сейчас
        self.label_lvl_up.setText(str(self.user_info[6] + 1))  # уровень сейчас + 1
        self.label_lvl_now.setStyleSheet('color: white')
        self.label_lvl_up.setStyleSheet('color: white')
        # твой прогресс на данном уровне
        self.progress_xp.setValue(self.get_xp_percent(self.user_info[7])[1])
        self.te_balance.setText(str(self.user_info[3]))  # баланс сейчас
        self.te_xp.setText(str(self.user_info[7]))  # xp сейчас

        self.pb_money.clicked.connect(self.show_balance)  # при нажатии show_balance()
        self.pb_all_commit.clicked.connect(self.save_changes)  # при нажатии show_balance()
        self.te_xp.textChanged.connect(self.set_xp)  # при изменении show_balance()
        self.te_balance.textChanged.connect(self.set_balance)  # при изменении show_balance()

    def show_balance(self):
        """Показать баланс"""

        self.pb_money.hide()  # открывает застежку (убирает)

    def set_balance(self):
        """Установить новый баланс"""

        balance = self.te_balance.toPlainText()  # баланс, указанный сейчас
        if not balance.isdigit() and balance: # ошибка: не цифры
            self.label_balance_error.setText('Циферками, пожалуйста 🙏')
            self.label_balance_error.adjustSize()
            self.label_balance_error.setStyleSheet("background-color: yellow")
            self.is_balance_error = True

        elif len(balance) > 9:  # ошибка: слишком много
            self.label_balance_error.setText('Даже в банке стольке денег нет!')
            self.label_balance_error.adjustSize()
            self.label_balance_error.setStyleSheet("background-color: red")
            self.is_balance_error = True

        elif self.is_balance_error:  # если была ошибка - убрать
            self.label_balance_error.setText('Теперь всё хорошо!')
            self.label_balance_error.adjustSize()
            self.label_balance_error.setStyleSheet("background-color: lightgreen")
            self.is_balance_error = False
            self.money = balance
            QTimer.singleShot(3000, self.disable_error_balance)  # исчезновение надписи

        else:
            self.money = balance if balance else 0  # сразу все хорошо

    def set_xp(self):
        """Установить новое количество xp"""

        xp = self.te_xp.toPlainText()
        # ошибка: только цифры
        if not xp.isdigit() and xp:
            self.label_xp_error.setText('Циферками, пожалуйста 🙏')
            self.label_xp_error.adjustSize()
            self.label_xp_error.setStyleSheet("background-color: yellow")
            self.is_xp_error = True

        # ошибка: слишком много
        elif len(xp) > 12:
            self.label_xp_error.setText('Не много ли ты хочешь?')
            self.label_xp_error.adjustSize()
            self.label_xp_error.setStyleSheet("background-color: red")
            self.is_xp_error = True

        else:
            # если введено корретно
            xp = int(xp) if xp else 0
            # расчет текущего уровня, по введеному количеству xp и определние прогресса
            new_level, xp_ratio = self.get_xp_percent(xp)
            level_now = int(self.label_lvl_now.text())

            if self.is_xp_error:  # если была ошибка - убрать
                self.disable_error_xp()
                self.is_xp_error = False

            if new_level > 99:  # ошибка: слишком большой уровень
                self.label_xp_error.setText('У тебя слишком большой уровень')
                self.label_xp_error.adjustSize()
                self.label_xp_error.setStyleSheet("background-color: cyan")
                self.is_big_level_error = True

                self.label_lvl_now.setText('99')
                self.label_lvl_up.setText('😨')

                self.progress_xp.setValue(100)

            else:
                if self.is_big_level_error:  # если была ошибка - убрать
                    self.disable_error_xp()
                    self.is_big_level_error = False

                # отображение нового значения lvl и xp
                self.label_lvl_now.setText(str(new_level))
                self.label_lvl_up.setText(str(new_level + 1))
                self.progress_xp.setValue(xp_ratio)
                # сохранение значений lvl и xp
                self.xp = xp
                self.lvl = new_level

    def disable_error_balance(self):
        """Исчезновение ошибки 'Баланс'"""

        if not self.is_balance_error:
            self.label_balance_error.setText('')
            self.label_balance_error.setStyleSheet("background-color: none")

    def get_xp_percent(self, xp: int) -> tuple:
        """Возращает уровень на текущем количестве xp и
         отношение xp к xp на следующем уровне"""

        level_now = int(xp ** (1 / 4))  # слишком сложная формула для вычисления текущего уровня
        # определение количества xp
        xp_ratio = (xp - level_now ** 4) / ((level_now + 1) ** 4 - level_now ** 4)
        return level_now, int(xp_ratio * 100)

    def disable_error_xp(self):
        """Исправление ошибки"""

        self.label_xp_error.setText('Теперь всё хорошо!')
        self.label_xp_error.adjustSize()
        self.label_xp_error.setStyleSheet("background-color: lightgreen")
        QTimer.singleShot(3000, self.hide_error_xp)

    def hide_error_xp(self):
        """Исчезновение ошибки 'xp'"""

        if not self.is_xp_error and not self.is_big_level_error:
            self.label_xp_error.setText('')
            self.label_xp_error.setStyleSheet("background-color: none")

    def save_changes(self):
        """Сохранение изменений в базу данных"""

        cur = self.database.cursor()

        # о изменении уровня и xp
        if self.xp and not self.is_big_level_error and not self.is_xp_error:

            # запись изменений в logs
            xp_before, lvl_before = tuple(cur.execute(f"""SELECT xp, lvl from users
                                                        WHERE id={self.user_info[0]}""").fetchone())
            logger.info(f"{self.user_info[1]}\tXP\t{'{'}{xp_before}{'}'}\t—\t{'{'}{self.xp}{'}'}")
            logger.info(f"{self.user_info[1]}\tLVL\t{'{'}{lvl_before}{'}'}\t—\t{'{'}{self.lvl}{'}'}")

            # запись в базу данных
            cur.execute(f"""UPDATE users
                            SET xp = {self.xp},
                                lvl = {self.lvl}
                            WHERE id={self.user_info[0]}""")

        # о изменении баланся
        if self.money and not self.is_balance_error:

            # запись изменений в logs
            balance_before = cur.execute(f"""SELECT money from users
                                            WHERE id={self.user_info[0]}""").fetchone()[0]
            logger.info(f"{self.user_info[1]}\tБаланс:\t{'{'}{balance_before}{'}'}\t—\t{'{'}{self.money}{'}'}")

            # запись в базу данных
            cur.execute(f"""UPDATE users
                            SET money = {self.money}
                            WHERE id={self.user_info[0]}""")
        self.database.commit()  # сохранение изменений в бд


BASE_NAME = r"materials\discord.db"

if __name__ == '__main__':
    logger.add("debug.log", format="{time} {level} {message}", level="INFO",
               rotation="10 KB", compression="zip", encoding="utf-8")

    app = QApplication(sys.argv)
    ex = TitlePage()
    ex.show()
    ex.setWindowTitle("Discord")
    sys.exit(app.exec())
