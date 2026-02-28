import os
import shutil
import subprocess
import platform
from tkinter import *
from tkinter import ttk, messagebox, filedialog


class SimpleExplorer:
    def __init__(self, root):
        self.root = root
        self.root.title("Проводник")
        self.root.geometry("900x550")

        # Текущий путь
        self.current_path = os.path.expanduser("~")  # Домашняя папка
        self.clipboard = None  # Для копирования/вырезания
        self.clipboard_action = None  # 'copy' или 'cut'

        # Создаем интерфейс
        self.setup_ui()
        self.update_file_list()

    def setup_ui(self):
        # Верхняя панель с кнопками
        toolbar = Frame(self.root, bg='lightgray', height=40)
        toolbar.pack(fill=X, padx=2, pady=2)

        # Кнопки навигации
        btn_up = Button(toolbar, text="⬆ Вверх", command=self.go_up)
        btn_up.pack(side=LEFT, padx=2)

        btn_refresh = Button(toolbar, text="🔄 Обновить", command=self.update_file_list)
        btn_refresh.pack(side=LEFT, padx=2)

        # Разделитель
        Frame(toolbar, width=2, bg='gray').pack(side=LEFT, padx=5, fill=Y)

        # Кнопки операций
        btn_new_folder = Button(toolbar, text="📁 Новая папка", command=self.create_folder)
        btn_new_folder.pack(side=LEFT, padx=2)

        btn_copy = Button(toolbar, text="📋 Копировать", command=self.copy_selected)
        btn_copy.pack(side=LEFT, padx=2)

        btn_cut = Button(toolbar, text="✂ Вырезать", command=self.cut_selected)
        btn_cut.pack(side=LEFT, padx=2)

        btn_paste = Button(toolbar, text="📌 Вставить", command=self.paste)
        btn_paste.pack(side=LEFT, padx=2)

        btn_rename = Button(toolbar, text="✏ Переименовать", command=self.rename_selected)
        btn_rename.pack(side=LEFT, padx=2)

        btn_delete = Button(toolbar, text="❌ Удалить", command=self.delete_selected)
        btn_delete.pack(side=LEFT, padx=2)

        # Разделитель
        Frame(toolbar, width=2, bg='gray').pack(side=LEFT, padx=5, fill=Y)

        btn_open = Button(toolbar, text="📂 Открыть", command=self.open_selected)
        btn_open.pack(side=LEFT, padx=2)

        # Адресная строка
        self.path_label = Label(toolbar, text=self.current_path, bg='white', relief=SUNKEN)
        self.path_label.pack(side=LEFT, fill=X, expand=True, padx=5)

        # Статусная строка
        self.status_bar = Label(self.root, text="Готов", bd=1, relief=SUNKEN, anchor=W)
        self.status_bar.pack(side=BOTTOM, fill=X)

        # Основная область с файлами
        main_frame = Frame(self.root)
        main_frame.pack(fill=BOTH, expand=True, padx=5, pady=5)

        # Создаем таблицу для файлов
        columns = ('name', 'type', 'size', 'modified')
        self.file_list = ttk.Treeview(main_frame, columns=columns, show='headings', height=20)

        # Заголовки колонок
        self.file_list.heading('name', text='Имя')
        self.file_list.heading('type', text='Тип')
        self.file_list.heading('size', text='Размер')
        self.file_list.heading('modified', text='Изменен')

        # Настройка ширины колонок
        self.file_list.column('name', width=350)
        self.file_list.column('type', width=120)
        self.file_list.column('size', width=100)
        self.file_list.column('modified', width=150)

        # Добавляем скроллбар
        scrollbar = ttk.Scrollbar(main_frame, orient=VERTICAL, command=self.file_list.yview)
        self.file_list.configure(yscrollcommand=scrollbar.set)

        # Размещаем таблицу и скроллбар
        self.file_list.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar.pack(side=RIGHT, fill=Y)

        # Обработчик двойного клика
        self.file_list.bind('<Double-Button-1>', self.on_double_click)

        # Контекстное меню
        self.create_context_menu()

    def create_context_menu(self):
        self.context_menu = Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="Открыть", command=self.open_selected)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Копировать", command=self.copy_selected)
        self.context_menu.add_command(label="Вырезать", command=self.cut_selected)
        self.context_menu.add_command(label="Вставить", command=self.paste)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Переименовать", command=self.rename_selected)
        self.context_menu.add_command(label="Удалить", command=self.delete_selected)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Обновить", command=self.update_file_list)

        # Привязываем контекстное меню
        self.file_list.bind('<Button-3>', self.show_context_menu)

    def show_context_menu(self, event):
        item = self.file_list.identify_row(event.y)
        if item:
            self.file_list.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)
        else:
            # Если клик не по элементу, показываем меню для вставки
            self.context_menu.delete(0, END)
            self.context_menu.add_command(label="Вставить", command=self.paste)
            self.context_menu.add_command(label="Обновить", command=self.update_file_list)
            self.context_menu.post(event.x_root, event.y_root)
            self.create_context_menu()  # Восстанавливаем полное меню

    def update_file_list(self):
        # Очищаем список
        for item in self.file_list.get_children():
            self.file_list.delete(item)

        # Обновляем адресную строку
        self.path_label.config(text=self.current_path)
        self.update_status(f"Текущая папка: {self.current_path}")

        try:
            # Добавляем папку "Наверх" если не в корне
            if os.path.dirname(self.current_path) != self.current_path:
                self.file_list.insert('', 'end', values=('📁 ..', 'Папка', '', ''),
                                      tags=('folder', 'parent'))

            # Получаем список файлов и папок
            items = os.listdir(self.current_path)

            # Сортируем: сначала папки, потом файлы
            folders = []
            files = []

            for item in items:
                item_path = os.path.join(self.current_path, item)
                if os.path.isdir(item_path):
                    folders.append(('📁 ' + item, 'Папка', '',
                                    self.get_mod_time(item_path)))
                else:
                    size = self.get_size(item_path)
                    file_type = self.get_file_type(item)
                    files.append((item, file_type, size,
                                  self.get_mod_time(item_path)))

            # Добавляем все в список
            for folder in sorted(folders):
                self.file_list.insert('', 'end', values=folder, tags=('folder',))

            for file in sorted(files):
                self.file_list.insert('', 'end', values=file, tags=('file',))

            self.update_status(f"Загружено: {len(folders)} папок, {len(files)} файлов")

        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось открыть папку: {e}")
            self.update_status("Ошибка загрузки")

    def get_file_type(self, filename):
        ext = os.path.splitext(filename)[1].lower()

        if ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.ico', '.svg']:
            return '🖼 Изображение'
        elif ext in ['.txt', '.doc', '.docx', '.pdf', '.rtf', '.odt']:
            return '📄 Документ'
        elif ext in ['.mp3', '.wav', '.flac', '.aac', '.ogg']:
            return '🎵 Аудио'
        elif ext in ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv']:
            return '🎬 Видео'
        elif ext in ['.zip', '.rar', '.7z', '.tar', '.gz']:
            return '📦 Архив'
        elif ext in ['.exe', '.msi', '.bat', '.sh']:
            return '⚙ Программа'
        elif ext in ['.py', '.js', '.html', '.css', '.cpp', '.java']:
            return '💻 Код'
        else:
            return '📄 Файл'

    def get_size(self, path):
        try:
            size = os.path.getsize(path)
            for unit in ['Б', 'КБ', 'МБ', 'ГБ']:
                if size < 1024:
                    return f"{size:.1f} {unit}"
                size /= 1024
            return f"{size:.1f} ТБ"
        except:
            return ""

    def get_mod_time(self, path):
        try:
            from datetime import datetime
            t = os.path.getmtime(path)
            return datetime.fromtimestamp(t).strftime('%d.%m.%Y %H:%M')
        except:
            return ""

    def get_selected_path(self):
        """Возвращает путь к выбранному элементу"""
        selection = self.file_list.selection()
        if not selection:
            return None

        item = self.file_list.item(selection[0])
        values = item['values']

        if not values or values[0] == '📁 ..':
            return None

        name = values[0]
        if name.startswith('📁 '):
            name = name[2:]

        return os.path.join(self.current_path, name)

    def on_double_click(self, event):
        self.open_selected()

    def open_file(self, file_path):
        try:
            if platform.system() == 'Windows':
                os.startfile(file_path)
            elif platform.system() == 'Darwin':
                subprocess.run(['open', file_path])
            else:
                subprocess.run(['xdg-open', file_path])
            self.update_status(f"Открыт: {os.path.basename(file_path)}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось открыть файл: {e}")

    def open_selected(self):
        path = self.get_selected_path()
        if not path:
            return

        if os.path.isdir(path):
            self.current_path = path
            self.update_file_list()
        else:
            self.open_file(path)

    def go_up(self):
        parent = os.path.dirname(self.current_path)
        if parent and parent != self.current_path:
            self.current_path = parent
            self.update_file_list()

    def copy_selected(self):
        """Копировать выбранный элемент"""
        path = self.get_selected_path()
        if path:
            self.clipboard = path
            self.clipboard_action = 'copy'
            self.update_status(f"Скопировано: {os.path.basename(path)}")

    def cut_selected(self):
        """Вырезать выбранный элемент"""
        path = self.get_selected_path()
        if path:
            self.clipboard = path
            self.clipboard_action = 'cut'
            self.update_status(f"Вырезано: {os.path.basename(path)}")

    def paste(self):
        """Вставить элемент из буфера"""
        if not self.clipboard:
            messagebox.showinfo("Информация", "Нет элемента для вставки")
            return

        try:
            dest_path = os.path.join(self.current_path, os.path.basename(self.clipboard))

            # Если файл уже существует, спрашиваем что делать
            if os.path.exists(dest_path):
                if not messagebox.askyesno("Подтверждение",
                                           f"Файл {os.path.basename(self.clipboard)} уже существует. Заменить?"):
                    return

            if self.clipboard_action == 'copy':
                if os.path.isdir(self.clipboard):
                    shutil.copytree(self.clipboard, dest_path)
                else:
                    shutil.copy2(self.clipboard, dest_path)
                action = "Скопирован"
            else:  # cut
                shutil.move(self.clipboard, dest_path)
                action = "Перемещен"

            self.update_status(f"{action}: {os.path.basename(self.clipboard)}")
            self.clipboard = None
            self.clipboard_action = None
            self.update_file_list()

        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось вставить: {e}")

    def rename_selected(self):
        """Переименовать выбранный элемент"""
        path = self.get_selected_path()
        if not path:
            return

        old_name = os.path.basename(path)

        # Диалог переименования
        dialog = Toplevel(self.root)
        dialog.title("Переименовать")
        dialog.geometry("400x160")
        dialog.resizable(False, False)

        Label(dialog, text="Старое имя:").pack(pady=2)
        Label(dialog, text=old_name, bg='lightgray', relief=SUNKEN).pack(pady=2, padx=10, fill=X)

        Label(dialog, text="Новое имя:").pack(pady=2)
        entry = Entry(dialog, width=50)
        entry.pack(pady=2, padx=10)
        entry.insert(0, old_name)
        entry.focus()
        entry.select_range(0, END)

        def rename():
            new_name = entry.get().strip()
            if new_name and new_name != old_name:
                new_path = os.path.join(os.path.dirname(path), new_name)
                try:
                    os.rename(path, new_path)
                    self.update_status(f"Переименован: {old_name} → {new_name}")
                    self.update_file_list()
                    dialog.destroy()
                except Exception as e:
                    messagebox.showerror("Ошибка", f"Не удалось переименовать: {e}")

        Button(dialog, text="Переименовать", command=rename).pack(pady=10)
        entry.bind('<Return>', lambda e: rename())

    def delete_selected(self):
        path = self.get_selected_path()
        if not path:
            return

        name = os.path.basename(path)

        if messagebox.askyesno("Подтверждение", f"Удалить '{name}'?"):
            try:
                if os.path.isdir(path):
                    shutil.rmtree(path)
                else:
                    os.remove(path)
                self.update_status(f"Удалено: {name}")
                self.update_file_list()
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось удалить: {e}")

    def create_folder(self):
        dialog = Toplevel(self.root)
        dialog.title("Новая папка")
        dialog.geometry("300x120")
        dialog.resizable(False, False)

        Label(dialog, text="Имя новой папки:").pack(pady=10)

        entry = Entry(dialog, width=30)
        entry.pack(pady=5)
        entry.focus()

        def create():
            name = entry.get().strip()
            if name:
                try:
                    new_path = os.path.join(self.current_path, name)
                    os.mkdir(new_path)
                    self.update_status(f"Создана папка: {name}")
                    self.update_file_list()
                    dialog.destroy()
                except Exception as e:
                    messagebox.showerror("Ошибка", f"Не удалось создать папку: {e}")

        Button(dialog, text="Создать", command=create).pack(pady=10)
        entry.bind('<Return>', lambda e: create())

    def update_status(self, message):
        self.status_bar.config(text=message)


# Запуск программы
if __name__ == "__main__":
    root = Tk()
    app = SimpleExplorer(root)
    root.mainloop()