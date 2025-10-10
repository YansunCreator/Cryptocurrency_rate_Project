"""
crypto_panel_modern.py
Обновлённая минималистичная версия CryptoPanel.
— Узкая панель в 2 строки, похожа на панель задач.
— Тёмная тема: чёрный фон, белый текст, аккуратные кнопки.
— Все функции из твоей рабочей версии сохранены.
"""

import threading
import requests
from tkinter import *
from tkinter import ttk, messagebox
from datetime import datetime

COINGECKO_SIMPLE = "https://api.coingecko.com/api/v3/simple/price"

SYMBOL_MAP = {
    "btc": "bitcoin", "eth": "ethereum", "usdt": "tether", "bnb": "binancecoin",
    "ada": "cardano", "doge": "dogecoin", "ltc": "litecoin", "xrp": "ripple"
}


class CryptoPanel:
    def __init__(self, root):
        self.root = root
        root.title("Crypto Panel")
        root.configure(bg="black")
        root.resizable(False, False)

        self.fiat = "usd"
        self.coin_var = StringVar(value="bitcoin")
        self.amount_var = StringVar(value="1")
        self.result_var = StringVar(value="—")
        self.notebook_visible = False
        self.tab_refs = []

        self._build_ui()
        self._create_notebook_window()

    def _build_ui(self):
        """Основной интерфейс — компактная панель"""
        pad = 4

        # === первая строка ===
        top = Frame(self.root, bg="black")
        top.pack(fill="x", pady=(6, 0))

        # кнопки выбора валют
        self.btn_rub = Button(top, text="RUB", width=6, bg="black", fg="white",
                              command=lambda: self._set_fiat("rub"))
        self.btn_usd = Button(top, text="USD", width=6, bg="#4caf50", fg="black",
                              command=lambda: self._set_fiat("usd"))
        self.btn_eur = Button(top, text="EUR", width=6, bg="black", fg="white",
                              command=lambda: self._set_fiat("eur"))
        for b in (self.btn_rub, self.btn_usd, self.btn_eur):
            b.pack(side="left", padx=pad)

        # курс
        self.fiat_label = Label(top, text=f"Курс к: {self.fiat.upper()}",
                                bg="black", fg="white", font=("Segoe UI", 9, "bold"))
        self.fiat_label.pack(side="left", padx=10)

        # метка заголовка
        Label(top, text="Crypto Exchange", bg="black", fg="white",
              font=("Segoe UI", 10, "bold")).pack(side="left", padx=10)

        # управление вкладками
        self.toggle_btn = Button(top, text="Показать вкладки", bg="#333333", fg="white",
                                 command=self._toggle_notebook)
        self.toggle_btn.pack(side="left", padx=6)
        self.clear_btn = Button(top, text="Очистить всё", bg="#333333", fg="white",
                                command=self._clear_tabs)
        self.clear_btn.pack(side="left", padx=6)

        # === вторая строка ===
        bottom = Frame(self.root, bg="black")
        bottom.pack(fill="x", pady=6)

        # криптовалюта
        Label(bottom, text="Криптовалюта", bg="black", fg="white").pack(side="left", padx=4)
        self.coin_entry = Entry(bottom, textvariable=self.coin_var, width=14,
                                bg="#111111", fg="white", insertbackground="white")
        self.coin_entry.pack(side="left", padx=4)

        # кнопка получить курс
        self.get_btn = Button(bottom, text="Получить курс", bg="#222222", fg="white",
                              command=self._on_get_rate)
        self.get_btn.pack(side="left", padx=6)

        # количество
        Label(bottom, text="Кол-во:", bg="black", fg="white").pack(side="left", padx=4)
        self.amount_entry = Entry(bottom, textvariable=self.amount_var, width=8,
                                  bg="#111111", fg="white", insertbackground="white")
        self.amount_entry.pack(side="left", padx=4)

        # конвертация
        self.conv_btn = Button(bottom, text="Конвертировать", bg="#222222", fg="white",
                               command=self._on_convert)
        self.conv_btn.pack(side="left", padx=6)

        # результат
        Label(bottom, text="Результат:", bg="black", fg="white").pack(side="left", padx=4)
        Label(bottom, textvariable=self.result_var, bg="black", fg="#4caf50",
              width=36, anchor="w").pack(side="left", padx=6)


    def _create_notebook_window(self):
        self.top = Toplevel(self.root)
        self.top.title("История запросов")
        self.top.configure(bg="black")
        self.top.withdraw()
        self.notebook = ttk.Notebook(self.top)
        self.notebook.pack(expand=True, fill="both", padx=6, pady=6)

    # --- вспомогательные методы ---
    def _toggle_notebook(self):
        if self.notebook_visible:
            self.top.withdraw()
            self.notebook_visible = False
            self.toggle_btn.config(text="Показать вкладки")
        else:
            self.top.deiconify()
            self.notebook_visible = True
            self.toggle_btn.config(text="Скрыть вкладки")

    def _clear_tabs(self):
        for tab in self.notebook.tabs():
            self.notebook.forget(tab)
        self.tab_refs.clear()
        self.result_var.set("—")
        messagebox.showinfo("Очистка", "Все вкладки удалены")

    def _set_fiat(self, code):
        self.fiat = code
        self.fiat_label.config(text=f"Курс к: {self.fiat.upper()}")
        # визуальная подсветка
        for b in (self.btn_rub, self.btn_usd, self.btn_eur):
            b.config(bg="black", fg="white")
        if code == "usd":
            self.btn_usd.config(bg="#4caf50", fg="black")
        elif code == "rub":
            self.btn_rub.config(bg="#4caf50", fg="black")
        else:
            self.btn_eur.config(bg="#4caf50", fg="black")

    # --- запрос курса ---
    def _on_get_rate(self):
        coin_input = self.coin_var.get().strip().lower()
        if not coin_input:
            messagebox.showwarning("Внимание", "Введите криптовалюту!")
            return
        coin_id = SYMBOL_MAP.get(coin_input, coin_input)

        self.get_btn.config(text="Загрузка...", bg="#f0c444", fg="black", state="disabled")
        threading.Thread(target=self._fetch_rate_thread, args=(coin_id,), daemon=True).start()

    def _fetch_rate_thread(self, coin_id):
        try:
            resp = requests.get(COINGECKO_SIMPLE, params={"ids": coin_id, "vs_currencies": self.fiat}, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            if coin_id not in data:
                raise ValueError(f"Криптовалюта '{coin_id}' не найдена.")
            price = data[coin_id][self.fiat]
            txt = f"1 {coin_id} = {price:.3f} {self.fiat.upper()} ({datetime.now().strftime('%H:%M:%S')})"
            self.root.after(0, lambda: self._on_success(coin_id, price, txt))
        except Exception as e:
            self.root.after(0, lambda msg=str(e): self._on_error(msg))

    def _on_success(self, coin_id, price, txt):
        self.result_var.set(txt)
        tab = ttk.Frame(self.notebook)
        Label(tab, text=txt, bg="black", fg="white").pack(padx=10, pady=10)
        self.notebook.add(tab, text=f"{coin_id} → {self.fiat.upper()}")

        self.get_btn.config(text="✅ Готово", bg="#4caf50", fg="white")
        self.root.after(1200, lambda: self.get_btn.config(text="Получить курс", bg="#222222", fg="white", state="normal"))

        if not self.notebook_visible:
            self._toggle_notebook()

        self.tab_refs.append((coin_id, self.fiat, price))

    def _on_error(self, msg):
        self.result_var.set("Ошибка")
        self.get_btn.config(text="Получить курс", bg="#222222", fg="white", state="normal")
        messagebox.showerror("Ошибка", msg)

    def _on_convert(self):
        try:
            amt = float(self.amount_var.get())
        except Exception:
            messagebox.showwarning("Ошибка", "Введите число для конвертации!")
            return
        if not self.tab_refs:
            messagebox.showwarning("Ошибка", "Сначала получите курс!")
            return
        coin_id, fiat, price = self.tab_refs[-1]
        total = amt * price
        self.result_var.set(f"{amt} {coin_id} = {total:.3f} {fiat.upper()} (по цене {price:.3f})")


if __name__ == "__main__":
    root = Tk()
    app = CryptoPanel(root)
    root.update_idletasks()
    w = root.winfo_width()
    x = (root.winfo_screenwidth() - w) // 2
    root.geometry(f"+{x}+10")
    root.mainloop()
