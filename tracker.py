import customtkinter as ctk
from tkinter import ttk, filedialog, Toplevel, Label
from tkcalendar import DateEntry
import sqlite3
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from datetime import datetime


# Функция для отображения всплывающих подсказок
def create_tooltip(widget, text):
    tooltip = Toplevel(widget)
    tooltip.wm_overrideredirect(True)
    tooltip.geometry(f"+{widget.winfo_rootx() + 20}+{widget.winfo_rooty() + 20}")
    label = Label(tooltip, text=text, background="lightyellow", relief="solid", borderwidth=1)
    label.pack(padx=5, pady=5)
    tooltip.withdraw()

    def on_enter(event):
        tooltip.deiconify()

    def on_leave(event):
        tooltip.withdraw()

    widget.bind("<Enter>", on_enter)
    widget.bind("<Leave>", on_leave)


# Создание базы данных
conn = sqlite3.connect("expenses.db")
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    category TEXT NOT NULL,
    amount REAL NOT NULL
)
""")
conn.commit()


# Функции приложения
def add_expense():
    date = date_entry.get()
    category = category_entry.get()
    amount = amount_entry.get()

    if not date or not category or not amount:
        ctk.CTkMessagebox.show_error("Ошибка", "Все поля должны быть заполнены!")
        return

    try:
        amount = float(amount)
    except ValueError:
        ctk.CTkMessagebox.show_error("Ошибка", "Сумма должна быть числом!")
        return

    # Проверка формата даты
    try:
        datetime.strptime(date, "%Y-%m-%d")  # Проверка на корректность даты
    except ValueError:
        ctk.CTkMessagebox.show_error("Ошибка", "Неверный формат даты! Используйте yyyy-mm-dd.")
        return

    # Добавление записи в базу данных
    cursor.execute("INSERT INTO expenses (date, category, amount) VALUES (?, ?, ?)", (date, category, amount))
    conn.commit()
    update_expense_list()
    ctk.CTkMessagebox.show_info("Успех", "Расход добавлен!")


def update_expense_list(start_date=None, end_date=None, category=None):
    expense_list.delete(*expense_list.get_children())

    query = "SELECT * FROM expenses"
    params = []

    if start_date and end_date:
        query += " WHERE date BETWEEN ? AND ?"
        params.extend([start_date, end_date])

    if category:
        query += " AND category = ?"
        params.append(category)

    cursor.execute(query, tuple(params))
    rows = cursor.fetchall()
    for row in rows:
        expense_list.insert("", "end", values=row)


def delete_expense():
    selected_items = expense_list.selection()
    if not selected_items:
        ctk.CTkMessagebox.show_error("Ошибка", "Выберите записи для удаления!")
        return

    def confirm_delete():
        for item in selected_items:
            expense_id = expense_list.item(item, "values")[0]
            cursor.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
            conn.commit()
            expense_list.delete(item)
        ctk.CTkMessagebox.show_info("Успех", "Расходы удалены!")

    def cancel_delete():
        confirm_window.destroy()

    confirm_window = Toplevel(app)
    confirm_window.title("Подтверждение удаления")
    confirm_window.geometry("300x150")

    label = ctk.CTkLabel(confirm_window, text="Вы уверены, что хотите удалить выбранные расходы?")
    label.pack(pady=20)

    yes_button = ctk.CTkButton(confirm_window, text="Да", command=confirm_delete)
    yes_button.pack(side="left", padx=20)

    no_button = ctk.CTkButton(confirm_window, text="Нет", command=cancel_delete)
    no_button.pack(side="right", padx=20)


def analyze_expenses():
    cursor.execute("SELECT category, SUM(amount) FROM expenses GROUP BY category")
    data = cursor.fetchall()

    if not data:
        ctk.CTkMessagebox.show_error("Ошибка", "Нет данных для анализа!")
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
        conn_backup = sqlite3.connect(file_path)
        with open('expenses.db', 'rb') as source:
            conn_backup.write(source.read())
        conn_backup.close()
        ctk.CTkMessagebox.show_info("Успех", "База данных сохранена!")


def load_database():
    file_path = filedialog.askopenfilename(defaultextension=".db", filetypes=[("SQLite Database", "*.db")])
    if file_path:
        global conn, cursor
        conn.close()
        conn = sqlite3.connect(file_path)
        cursor = conn.cursor()
        update_expense_list()
        ctk.CTkMessagebox.show_info("Успех", "База данных загружена!")


# Интерфейс приложения
app = ctk.CTk()
app.title("Трекер расходов")
app.geometry("800x600")

# Адаптация сетки
app.grid_rowconfigure(6, weight=1)
app.grid_columnconfigure(1, weight=1)

# Поля для ввода
ctk.CTkLabel(app, text="Дата:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
date_entry = DateEntry(app, date_pattern="yyyy-mm-dd", background="darkblue", foreground="white", borderwidth=2)
date_entry.grid(row=0, column=1, padx=10, pady=5, sticky="ew")

ctk.CTkLabel(app, text="Категория:").grid(row=1, column=0, padx=10, pady=5, sticky="w")
category_entry = ctk.CTkEntry(app)
category_entry.grid(row=1, column=1, padx=10, pady=5, sticky="ew")

ctk.CTkLabel(app, text="Сумма:").grid(row=2, column=0, padx=10, pady=5, sticky="w")
amount_entry = ctk.CTkEntry(app)
amount_entry.grid(row=2, column=1, padx=10, pady=5, sticky="ew")

# Кнопки
add_button = ctk.CTkButton(app, text="Добавить", command=add_expense)
add_button.grid(row=3, column=0, padx=10, pady=10, sticky="ew")
create_tooltip(add_button, "Нажмите для добавления нового расхода.")

delete_button = ctk.CTkButton(app, text="Удалить", command=delete_expense)
delete_button.grid(row=3, column=1, padx=10, pady=10, sticky="ew")
create_tooltip(delete_button, "Нажмите для удаления выбранных расходов.")

analyze_button = ctk.CTkButton(app, text="Анализировать", command=analyze_expenses)
analyze_button.grid(row=3, column=2, padx=10, pady=10, sticky="ew")
create_tooltip(analyze_button, "Нажмите для анализа расходов.")

# Фильтрация по датам
ctk.CTkLabel(app, text="Начальная дата:").grid(row=4, column=0, padx=10, pady=5, sticky="w")
start_date_entry = DateEntry(app, date_pattern="yyyy-mm-dd", background="darkblue", foreground="white", borderwidth=2)
start_date_entry.grid(row=4, column=1, padx=10, pady=5, sticky="ew")

ctk.CTkLabel(app, text="Конечная дата:").grid(row=5, column=0, padx=10, pady=5, sticky="w")
end_date_entry = DateEntry(app, date_pattern="yyyy-mm-dd", background="darkblue", foreground="white", borderwidth=2)
end_date_entry.grid(row=5, column=1, padx=10, pady=5, sticky="ew")

filter_button = ctk.CTkButton(app, text="Применить фильтр",
                              command=lambda: update_expense_list(start_date=start_date_entry.get(),
                                                                  end_date=end_date_entry.get()))
filter_button.grid(row=5, column=2, padx=10, pady=10, sticky="ew")
create_tooltip(filter_button, "Примените фильтр для дат.")

# Кнопка для сброса фильтра
reset_filter_button = ctk.CTkButton(app, text="Сбросить фильтр", command=lambda: update_expense_list())
reset_filter_button.grid(row=5, column=3, padx=10, pady=10, sticky="ew")
create_tooltip(reset_filter_button, "Сбросить все фильтры.")

# Таблица расходов
columns = ("id", "date", "category", "amount")
expense_list = ttk.Treeview(app, columns=columns, show="headings", height=10)
expense_list.heading("id", text="ID")
expense_list.heading("date", text="Дата")
expense_list.heading("category", text="Категория")
expense_list.heading("amount", text="Сумма")
expense_list.grid(row=6, column=0, columnspan=4, padx=10, pady=10, sticky="nsew")

# Прокрутка для таблицы
scrollbar = ttk.Scrollbar(app, orient="vertical", command=expense_list.yview)
expense_list.configure(yscroll=scrollbar.set)
scrollbar.grid(row=6, column=4, sticky="ns")

# Кнопки для сохранения и загрузки базы данных
save_button = ctk.CTkButton(app, text="Сохранить базу данных", command=save_database)
save_button.grid(row=7, column=0, padx=10, pady=10, sticky="ew")
create_tooltip(save_button, "Сохранить текущую базу данных.")

load_button = ctk.CTkButton(app, text="Загрузить базу данных", command=load_database)
load_button.grid(row=7, column=1, padx=10, pady=10, sticky="ew")
create_tooltip(load_button, "Загрузить базу данных из файла.")

update_expense_list()

# Закрытие соединения с базой данных
conn.close()

app.mainloop()
