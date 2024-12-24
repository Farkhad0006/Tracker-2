import customtkinter as ctk
from tkinter import ttk, filedialog, messagebox
from tkcalendar import DateEntry
import sqlite3
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from datetime import datetime


# Создание базы данных
def initialize_database():
    connection = sqlite3.connect("expenses.db")
    cursor = connection.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        category TEXT NOT NULL,
        amount REAL NOT NULL
    )
    """)
    connection.commit()
    return connection, cursor


conn, cursor = initialize_database()


# Функции приложения
def add_expense():
    date = date_entry.get()
    category = category_var.get().strip()
    amount = amount_entry.get()

    if not date or not category or not amount:
        messagebox.showerror("Ошибка", "Все поля должны быть заполнены!")
        return

    try:
        amount = float(amount)
    except ValueError:
        messagebox.showerror("Ошибка", "Сумма должна быть числом!")
        return

    try:
        datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        messagebox.showerror("Ошибка", "Неверный формат даты! Используйте yyyy-mm-dd.")
        return

    cursor.execute("INSERT INTO expenses (date, category, amount) VALUES (?, ?, ?)", (date, category, amount))
    conn.commit()
    update_expense_list()
    update_total_label()
    messagebox.showinfo("Успех", "Расход добавлен!")


def update_expense_list(start_date=None, end_date=None, category=None):
    expense_list.delete(*expense_list.get_children())

    query = "SELECT * FROM expenses"
    params = []

    if start_date and end_date:
        query += " WHERE date BETWEEN ? AND ?"
        params.extend([start_date, end_date])

    if category:
        if "WHERE" in query:
            query += " AND category = ?"
        else:
            query += " WHERE category = ?"
        params.append(category)

    cursor.execute(query, tuple(params))
    rows = cursor.fetchall()
    for row in rows:
        expense_list.insert("", "end", values=row)


def update_total_label():
    cursor.execute("SELECT SUM(amount) FROM expenses")
    total = cursor.fetchone()[0] or 0.0
    total_label.configure(text=f"Общая сумма: {total:.2f} руб.")


def delete_expense():
    selected_items = expense_list.selection()
    if not selected_items:
        messagebox.showerror("Ошибка", "Выберите записи для удаления!")
        return

    for item in selected_items:
        expense_id = expense_list.item(item, "values")[0]
        cursor.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
        conn.commit()
        expense_list.delete(item)

    update_total_label()
    messagebox.showinfo("Успех", "Расходы удалены!")


def analyze_expenses():
    cursor.execute("SELECT category, SUM(amount) FROM expenses GROUP BY category")
    data = cursor.fetchall()

    if not data:
        messagebox.showerror("Ошибка", "Нет данных для анализа!")
        return

    categories = [row[0] for row in data]
    amounts = [row[1] for row in data]

    analysis_window = ctk.CTkToplevel(app)
    analysis_window.title("Анализ расходов")
    analysis_window.geometry("600x400")

    figure = plt.Figure(figsize=(6, 4), dpi=100)
    ax = figure.add_subplot(111)
    ax.pie(amounts, labels=categories, autopct='%1.1f%%', startangle=140)
    ax.set_title("Расходы по категориям")

    chart = FigureCanvasTkAgg(figure, analysis_window)
    chart.get_tk_widget().pack(fill='both', expand=True)

    def save_chart():
        file_path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG", "*.png")])
        if file_path:
            figure.savefig(file_path)

    save_button = ctk.CTkButton(analysis_window, text="Сохранить график", command=save_chart)
    save_button.pack(pady=10)


def save_database():
    file_path = filedialog.asksaveasfilename(defaultextension=".db", filetypes=[("SQLite Database", "*.db")])
    if file_path:
        with open('expenses.db', 'rb') as source:
            with open(file_path, 'wb') as target:
                target.write(source.read())
        messagebox.showinfo("Успех", "База данных сохранена!")


def load_database():
    file_path = filedialog.askopenfilename(defaultextension=".db", filetypes=[("SQLite Database", "*.db")])
    if file_path:
        global conn, cursor
        conn.close()
        conn = sqlite3.connect(file_path)
        cursor = conn.cursor()
        update_expense_list()
        update_total_label()
        messagebox.showinfo("Успех", "База данных загружена!")


# Функция проверки, чтобы ввод был числовым
def validate_number_input(char, entry_value):
    if char.isdigit() or char == ".":
        return True
    return False


# Интерфейс приложения
app = ctk.CTk()
app.title("Трекер расходов")
app.geometry("800x600")

app.grid_rowconfigure(6, weight=1)
app.grid_columnconfigure(1, weight=1)

# Поля для ввода
ctk.CTkLabel(app, text="Дата:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
date_entry = DateEntry(app, date_pattern="yyyy-mm-dd", background="darkblue", foreground="white", borderwidth=2)
date_entry.grid(row=0, column=1, padx=10, pady=5, sticky="ew")

ctk.CTkLabel(app, text="Категория:").grid(row=1, column=0, padx=10, pady=5, sticky="w")

# Список категорий
categories_list = ["Продукты", "Транспорт", "Развлечения", "Жилье", "Здоровье", "Другое"]
category_var = ctk.StringVar(value=categories_list[0])  # Default category is the first one

category_option_menu = ctk.CTkOptionMenu(app, variable=category_var, values=categories_list)
category_option_menu.grid(row=1, column=1, padx=10, pady=5, sticky="ew")

ctk.CTkLabel(app, text="Сумма:").grid(row=2, column=0, padx=10, pady=5, sticky="w")

# Настройка валидации для поля "Сумма"
validate_command = (app.register(validate_number_input), '%S', '%P')
amount_entry = ctk.CTkEntry(app, validate='key', validatecommand=validate_command)
amount_entry.grid(row=2, column=1, padx=10, pady=5, sticky="ew")

# Кнопки управления
add_button = ctk.CTkButton(app, text="Добавить", command=add_expense)
add_button.grid(row=3, column=0, padx=10, pady=10, sticky="ew")

delete_button = ctk.CTkButton(app, text="Удалить", command=delete_expense)
delete_button.grid(row=3, column=1, padx=10, pady=10, sticky="ew")

analyze_button = ctk.CTkButton(app, text="Анализировать", command=analyze_expenses)
analyze_button.grid(row=3, column=2, padx=10, pady=10, sticky="ew")

# Фильтры
ctk.CTkLabel(app, text="Начальная дата:").grid(row=4, column=0, padx=10, pady=5, sticky="w")
start_date_entry = DateEntry(app, date_pattern="yyyy-mm-dd", background="darkblue", foreground="white", borderwidth=2)
start_date_entry.grid(row=4, column=1, padx=10, pady=5, sticky="ew")

ctk.CTkLabel(app, text="Конечная дата:").grid(row=5, column=0, padx=10, pady=5, sticky="w")
end_date_entry = DateEntry(app, date_pattern="yyyy-mm-dd", background="darkblue", foreground="white", borderwidth=2)
end_date_entry.grid(row=5, column=1, padx=10, pady=5, sticky="ew")

filter_button = ctk.CTkButton(app, text="Применить фильтр", command=lambda: update_expense_list(start_date=start_date_entry.get(), end_date=end_date_entry.get()))
filter_button.grid(row=5, column=2, padx=10, pady=10, sticky="ew")

reset_filter_button = ctk.CTkButton(app, text="Сбросить фильтр", command=lambda: update_expense_list())
reset_filter_button.grid(row=5, column=3, padx=10, pady=10, sticky="ew")

# Таблица расходов
columns = ("id", "date", "category", "amount")
expense_list = ttk.Treeview(app, columns=columns, show="headings", height=10)
expense_list.heading("id", text="ID")
expense_list.heading("date", text="Дата")
expense_list.heading("category", text="Категория")
expense_list.heading("amount", text="Сумма")
expense_list.grid(row=6, column=0, columnspan=4, padx=10, pady=10, sticky="nsew")

scrollbar = ttk.Scrollbar(app, orient="vertical", command=expense_list.yview)
expense_list.configure(yscroll=scrollbar.set)
scrollbar.grid(row=6, column=4, sticky="ns")

# Общая сумма расходов
total_label = ctk.CTkLabel(app, text="Общая сумма: 0.00 руб.")
total_label.grid(row=7, column=0, columnspan=4, pady=10)

# Кнопки для базы данных
save_button = ctk.CTkButton(app, text="Сохранить базу данных", command=save_database)
save_button.grid(row=8, column=0, padx=10, pady=10, sticky="ew")

load_button = ctk.CTkButton(app, text="Загрузить базу данных", command=load_database)
load_button.grid(row=8, column=1, padx=10, pady=10, sticky="ew")

# Кнопка для смены темы
def toggle_theme():
    current_mode = ctk.get_appearance_mode()
    if current_mode == "Light":
        ctk.set_appearance_mode("Dark")  # Устанавливаем тёмную тему
    else:
        ctk.set_appearance_mode("Light")  # Устанавливаем светлую тему
    update_expense_list()  # Обновление данных, чтобы стиль применился корректно
    update_total_label()  # Обновление общей суммы для корректного отображения

theme_button = ctk.CTkButton(app, text="Сменить тему", command=toggle_theme)
theme_button.grid(row=8, column=2, padx=10, pady=10, sticky="ew")

update_expense_list()
update_total_label()

app.mainloop()
