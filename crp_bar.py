import threading
from tkinter import Tk, Label, StringVar, DoubleVar, Button, Entry, Toplevel
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
import requests

# Популярные криптовалюты / валюты
POPULAR = ["bitcoin", "ethereum", "dogecoin", "solana", "tether", "usd", "eur", "rub"]

# Отображения для названий
NAMES = {
    "bitcoin": "Bitcoin",
    "ethereum": "Ethereum",
    "dogecoin": "Dogecoin",
    "solana": "Solana",
    "tether": "Tether",
    "usd": "Доллар США",
    "eur": "Евро",
    "rub": "Российский рубль",
    }

def cg_convert(base: str, target: str, amount: float = 1.0):
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {
        "ids": base.lower(),
        "vs_currencies": target.lower()
    }
    resp = requests.get(url, params=params, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    # Пример: data = {"bitcoin": {"usd": 27000}}
    if base.lower() in data and target.lower() in data[base.lower()]:
        rate = data[base.lower()][target.lower()]
        return rate * amount
    else:
        raise ValueError("Курс не найден: " + str(data))


class CGApp:
    def __init__(self, root):
        self.root = root
        root.title("Конвертер — CoinGecko")
        root.geometry("380x200")
        root.resizable(False, False)

        self.base_var = StringVar(value="bitcoin")
        self.target_var = StringVar(value="usd")
        self.amount_var = DoubleVar(value=1.0)
        self.result_var = StringVar(value="")

        self._build_ui()

    def _build_ui(self):
        ttk.Label(self.root, text="Список (код Id валюты):").place(x=10, y=10)
        self.base_cb = ttk.Combobox(self.root, values=POPULAR, textvariable=self.base_var, width=12)
        self.base_cb.place(x=180, y=10)
        Label(self.root, textvariable=lambda: NAMES.get(self.base_var.get(), "")).place(x=180, y=35)

        ttk.Label(self.root, text="Список (код Id валюты):").place(x=10, y=50)
        self.target_cb = ttk.Combobox(self.root, values=POPULAR, textvariable=self.target_var, width=12)
        self.target_cb.place(x=180, y=50)
        Label(self.root, textvariable=lambda: NAMES.get(self.target_var.get(), "")).place(x=180, y=75)

        ttk.Label(self.root, text="Сумма:").place(x=10, y=90)
        self.amount_entry = Entry(self.root, textvariable=self.amount_var, width=15)
        self.amount_entry.place(x=180, y=90)

        self.btn = Button(self.root, text="Получить курс", command=self.on_convert)
        self.btn.place(x=10, y=130)

        self.res_label = ttk.Label(self.root, textvariable=self.result_var, relief="sunken", width=40)
        self.res_label.place(x=10, y=160)

    def on_convert(self):
        try:
            amt = float(self.amount_var.get())
        except:
            messagebox.showerror("Ошибка", "Сумма должна быть числом")
            return
        base = self.base_var.get().lower().strip()
        target = self.target_var.get().lower().strip()
        if not base or not target:
            messagebox.showwarning("Внимание", "Выберите базу и цель")
            return

        self.btn.config(state="disabled", text="Загружаю...")
        threading.Thread(target=self.thread_convert, args=(base, target, amt), daemon=True).start()

    def thread_convert(self, base, target, amt):
        try:
            res = cg_convert(base, target, amt)
            text = f"{amt} {NAMES.get(base, base)} = {res:.6f} {NAMES.get(target, target)}"
            self.root.after(0, lambda: self.result_var.set(text))
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Ошибка", str(e)))
        finally:
            self.root.after(0, lambda: self.btn.config(state="normal", text="Получить курс"))


if __name__ == "__main__":
    root = Tk()
    app = CGApp(root)
    root.mainloop()
