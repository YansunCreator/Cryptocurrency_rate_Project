"""
CryptoPanel — итоговый проект (версия с комментариями)
------------------------------------------------------
Функционал:
- Получение курса криптовалют с CoinGecko API.
- Конвертация в RUB / USD / EUR.
- Сохранение истории запросов во вкладках.
- Возможность показа / очистки вкладок.
- Тёмный минималистичный интерфейс в стиле панели задач.
"""

# Импорт стандартных библиотек
import threading                # Для фонового запроса (чтобы не зависал интерфейс)
import requests                 # Для HTTP-запросов к API CoinGecko
from tkinter import *            # Основные виджеты Tkinter
from tkinter import ttk, messagebox
from datetime import datetime # Для вывода времени получения курса

# Базовый URL CoinGecko API
COINGECKO_SIMPLE = "https://api.coingecko.com/api/v3/simple/price"

# Краткие символы криптовалют -> ID CoinGecko
SYMBOL_MAP = {
    "btc": "bitcoin", "eth": "ethereum", "usdt": "tether", "bnb": "binancecoin",
    "ada": "cardano", "doge": "dogecoin", "ltc": "litecoin", "xrp": "ripple"
}

# --- Основной класс приложения ---
class CryptoPanel:
    def __init__(self, root):
        # Инициализация главного окна
        self.root = root
        root.title("Crypto Panel")        # Заголовок окна
        root.configure(bg="black")        # Чёрный фон
        root.resizable(False, False)      # Запрет изменения размеров
        root.iconphoto(False, PhotoImage(file="logo_cp.png")) # Логотип вместо пера

        # Переменные состояния
        self.fiat = "usd"                 # Валюта по умолчанию
        self.coin_var = StringVar(value="bitcoin")  # Криптовалюта
        self.amount_var = StringVar(value="1")      # Количество для конвертации
        self.result_var = StringVar(value="—")      # Поле вывода результата
        self.notebook_visible = False               # Флаг видимости вкладок
        self.tab_refs = []                          # Список сохранённых запросов

        # Построение интерфейса
        self._build_ui()
        self._create_notebook_window()

    # --- Построение панели интерфейса ---
    def _build_ui(self):
        pad = 4

        # === Первая строка ===
        top = Frame(self.root, bg="black")
        top.pack(fill="x", pady=(6, 0))

        # Кнопки выбора фиатной валюты
        self.btn_rub = Button(top, text="RUB", width=6, bg="black", fg="white",
                              command=lambda: self._set_fiat("rub"))
        self.btn_usd = Button(top, text="USD", width=6, bg="#4caf50", fg="black",
                              command=lambda: self._set_fiat("usd"))
        self.btn_eur = Button(top, text="EUR", width=6, bg="black", fg="white",
                              command=lambda: self._set_fiat("eur"))

        for b in (self.btn_rub, self.btn_usd, self.btn_eur):
            b.pack(side="left", padx=pad)

        # Метка с текущей валютой
        self.fiat_label = Label(top, text=f"Курс к: {self.fiat.upper()}",
                                bg="black", fg="white", font=("Segoe UI", 9, "bold"))
        self.fiat_label.pack(side="left", padx=10)

        # Заголовок панели
        Label(top, text="Crypto Exchange", bg="black", fg="white",
              font=("Segoe UI", 10, "bold")).pack(side="left", padx=10)

        # Управление вкладками
        self.toggle_btn = Button(top, text="Показать вкладки", bg="#333333", fg="white",
                                 command=self._toggle_notebook)
        self.toggle_btn.pack(side="left", padx=6)

        self.clear_btn = Button(top, text="Очистить всё", bg="#333333", fg="white",
                                command=self._clear_tabs)
        self.clear_btn.pack(side="left", padx=6)

        # === Вторая строка ===
        bottom = Frame(self.root, bg="black")
        bottom.pack(fill="x", pady=6)

        # Метка "Криптовалюта"
        Label(bottom, text="Криптовалюта", bg="black", fg="white").pack(side="left", padx=4)

        # Выпадающий список (Combobox) — можно выбрать или ввести вручную
        self.coin_cb = ttk.Combobox(bottom, values=list(SYMBOL_MAP.keys()),
                                    textvariable=self.coin_var, width=12)
        self.coin_cb.pack(side="left", padx=4)

        # Кнопка получения курса
        self.get_btn = Button(bottom, text="Получить курс", bg="#222222", fg="white",
                              command=self._on_get_rate)
        self.get_btn.pack(side="left", padx=6)

        # Метка и поле для ввода количества
        Label(bottom, text="Кол-во:", bg="black", fg="white").pack(side="left", padx=4)
        self.amount_entry = Entry(bottom, textvariable=self.amount_var, width=8,
                                  bg="#111111", fg="white", insertbackground="white")
        self.amount_entry.pack(side="left", padx=4)

        # Кнопка конвертации
        self.conv_btn = Button(bottom, text="Конвертировать", bg="#222222", fg="white",
                               command=self._on_convert)
        self.conv_btn.pack(side="left", padx=6)

        # Метка результата
        Label(bottom, text="Результат:", bg="black", fg="white").pack(side="left", padx=4)
        Label(bottom, textvariable=self.result_var, bg="black", fg="#4caf50",
              width=36, anchor="w").pack(side="left", padx=6)

    # --- Создание окна вкладок ---
    def _create_notebook_window(self):
        self.top = Toplevel(self.root)
        self.top.title("История запросов")
        self.top.configure(bg="black")
        self.top.withdraw()  # Скрываем при запуске
        self.notebook = ttk.Notebook(self.top)
        self.notebook.pack(expand=True, fill="both", padx=6, pady=6)

    # --- Показ / скрытие вкладок ---
    def _toggle_notebook(self):
        if self.notebook_visible:
            self.top.withdraw()
            self.notebook_visible = False
            self.toggle_btn.config(text="Показать вкладки")
        else:
            self.top.deiconify()
            self.notebook_visible = True
            self.toggle_btn.config(text="Скрыть вкладки")

    # --- Очистка вкладок ---
    def _clear_tabs(self):
        for tab in self.notebook.tabs():
            self.notebook.forget(tab)
        self.tab_refs.clear()
        self.result_var.set("—")
        messagebox.showinfo("Очистка", "Все вкладки удалены")

    # --- Установка фиатной валюты ---
    def _set_fiat(self, code):
        self.fiat = code
        self.fiat_label.config(text=f"Курс к: {self.fiat.upper()}")
        # Подсветка активной кнопки
        for b in (self.btn_rub, self.btn_usd, self.btn_eur):
            b.config(bg="black", fg="white")
        if code == "usd":
            self.btn_usd.config(bg="#4caf50", fg="black")
        elif code == "rub":
            self.btn_rub.config(bg="#4caf50", fg="black")
        else:
            self.btn_eur.config(bg="#4caf50", fg="black")

    # --- Обработка нажатия "Получить курс" ---
    def _on_get_rate(self):
        coin_input = self.coin_var.get().strip().lower()
        if not coin_input:
            messagebox.showwarning("Внимание", "Введите криптовалюту!")
            return
        coin_id = SYMBOL_MAP.get(coin_input, coin_input)

        # Индикация загрузки (жёлтый цвет)
        self.get_btn.config(text="Загрузка...", bg="#f0c444", fg="black", state="disabled")
        # Запуск фонового потока
        threading.Thread(target=self._fetch_rate_thread, args=(coin_id,), daemon=True).start()

    # --- Поток загрузки курса ---
    def _fetch_rate_thread(self, coin_id):
        try:
            resp = requests.get(COINGECKO_SIMPLE,
                                params={"ids": coin_id, "vs_currencies": self.fiat},
                                timeout=10)
            resp.raise_for_status()
            data = resp.json()
            if coin_id not in data:
                raise ValueError(f"Криптовалюта '{coin_id}' не найдена.")
            price = data[coin_id][self.fiat]
            txt = f"1 {coin_id} = {price:.3f} {self.fiat.upper()} ({datetime.now().strftime('%H:%M:%S')})"
            self.root.after(0, lambda: self._on_success(coin_id, price, txt))
        except Exception as e:
            # В случае ошибки передаём текст в обработчик
            self.root.after(0, lambda msg=str(e): self._on_error(msg))

    # --- Успешный ответ от API ---
    def _on_success(self, coin_id, price, txt):
        self.result_var.set(txt)
        # Добавляем вкладку с результатом
        tab = ttk.Frame(self.notebook)
        Label(tab, text=txt, bg="black", fg="white").pack(padx=10, pady=10)
        self.notebook.add(tab, text=f"{coin_id} → {self.fiat.upper()}")

        # Зелёная индикация «Готово»
        self.get_btn.config(text="✅ Готово", bg="#4caf50", fg="white")
        self.root.after(1200, lambda: self.get_btn.config(text="Получить курс", bg="#222222", fg="white", state="normal"))

        if not self.notebook_visible:
            self._toggle_notebook()

        # Сохраняем данные во внутренний список
        self.tab_refs.append((coin_id, self.fiat, price))

    # --- Обработка ошибок ---
    def _on_error(self, msg):
        self.result_var.set("Ошибка")
        self.get_btn.config(text="Получить курс", bg="#222222", fg="white", state="normal")
        messagebox.showerror("Ошибка", msg)

    # --- Конвертация ---
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


# --- Точка входа ---
if __name__ == "__main__":
    root = Tk()
    app = CryptoPanel(root)
    # Центрируем окно по ширине
    root.update_idletasks()
    w = root.winfo_width()
    x = (root.winfo_screenwidth() - w) // 2
    root.geometry(f"+{x}+10")
    root.mainloop()
