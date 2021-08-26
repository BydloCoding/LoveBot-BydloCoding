from SDK.user import User
from SDK.keyboard import Keyboard
from vk_api import keyboard
from SDK.database import ProtectedProperty, Struct
from SDK.cmd import command
from main import MainThread


class UserProfile(Struct):
    def __init__(self, *args, **kwargs):
        self.save_by = ProtectedProperty("user_id")
        self.user_id = 0
        self.balance = 0
        super().__init__(*args, **kwargs)


@command("пополнить баланс")
def replenish_balance(self):
    k = Keyboard()
    def generate_balance_link(
        x): return f"https://qiwi.com/payment/form/99?extra%5B%27account%27%5D={self.qiwi_wallet}&amountInteger={x}&amountFraction=0&extra%5B%27comment%27%5D=lovebot:{self.user.id}&currency=643&blocked[0]=account&blocked[1]=comment"
    k.add_openlink_button("50 ₽", generate_balance_link(50))
    k.add_openlink_button("100 ₽", generate_balance_link(100))
    k.add_line()
    k.add_openlink_button("200 ₽", generate_balance_link(200))
    k.add_openlink_button("300 ₽", generate_balance_link(300))
    k.add_line()
    k.add_openlink_button("400 ₽", generate_balance_link(400))
    k.add_openlink_button("500 ₽", generate_balance_link(500))
    k.add_line().add_button("В меню", Keyboard.colors["green"])
    self.reply("Суммы, на которые можно пополнить баланс:", keyboard=k)

@command("баланс")
def balance(self):
    self.reply(f"Баланс: {UserProfile(user_id = self.user.id).balance}")

menu_kb = {"В меню": "blue", "Баланс":"green"}

@command("начать", aliases=["в меню"])
def start(self: MainThread):
    selected = self.db.select_all_structs(
        "select * from user_history where user_id = ?", [self.user.id])
    if len(selected) == 0:
        return self.reply("Похоже, Вы еще не установили скрипт для браузера для просмотра страниц или не зашли ни на одну страницу.")
    visited = self.db.select_all_structs(
        "select * from user_history where visited_id = ?", [self.user.id])
    if len(visited) == 0:
        return self.reply("Пока что еще никто не заходил на Вашу страницу.", keyboard = menu_kb)
    user_profile = UserProfile(user_id=self.user.id)
    balance = user_profile.balance
    substract = 100 if visited.all(lambda it: it.viewed_counter == 0) else 20
    a = []
    for visit in visited:
        if visit.viewed_counter < visit.counter:
            a.append([visit.user_id, visit.counter - visit.viewed_counter])
            visit.viewed_counter = visit.counter
    a.sort(key=lambda it: it[1], reverse=True)
    if len(a) == 0:
        return self.reply("Пока что еще никто не заходил на вашу страницу.", keyboard = menu_kb)
    if balance < substract:
        return self.reply("Для первого запросы информации необходимо 100 рублей." if substract == 100 else f"Для последующих запросов информации необходимо {substract} рублей.", keyboard={"Пополнить баланс": "green"})
    user_profile.balance -= substract
    m = "Топ просмотров:\n\n"
    for i in a:
        user = User(self.vk, i[0])
        m += f"[id{i[0]}|{user.user_name}] - {i[1]}\n"
    self.reply(m, keyboard=menu_kb)
