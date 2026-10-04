import argparse
import base64
import csv
import os
import shlex
import tkinter as tk


class VFS:
    """Класс для управления виртуальной файловой системой в памяти."""

    def __init__(self, csv_path: str):
        self.csv_path = csv_path
        # Хранилище файловой системы в памяти: {path: {'type': 'file'/'dir', 'content': bytes}}
        self.fs = {}
        self.current_dir = "/"
        self.load_vfs()

    def load_vfs(self):
        """Загрузка VFS из CSV-файла в память."""
        self.fs = {"/": {"type": "dir", "content": b""}}
        if not os.path.exists(self.csv_path):
            self.create_default_csv()

        try:
            with open(self.csv_path, mode="r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    path = self.normalize_path(row["path"])
                    item_type = row["type"]
                    raw_content = row.get("content", "")

                    if item_type == "file":
                        content = base64.b64decode(raw_content.encode("utf-8"))
                    else:
                        content = b""

                    self.fs[path] = {"type": item_type, "content": content}
        except Exception as e:
            print(f"Ошибка загрузки CSV VFS: {e}")

    def create_default_csv(self):
        """Создает дефолтный CSV-файл с начальной структурой (3 уровня файлов/папок)."""
        default_data = [
            {"path": "/", "type": "dir", "content": ""},
            {"path": "/home", "type": "dir", "content": ""},
            {"path": "/home/user", "type": "dir", "content": ""},
            {
                "path": "/home/user/welcome.txt",
                "type": "file",
                "content": base64.b64encode(b"Welcome to VFS!").decode("utf-8"),
            },
            {"path": "/var", "type": "dir", "content": ""},
            {"path": "/var/log", "type": "dir", "content": ""},
            {
                "path": "/var/log/system.log",
                "type": "file",
                "content": base64.b64encode(b"System log initialized").decode(
                    "utf-8"
                ),
            },
        ]
        with open(self.csv_path, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["path", "type", "content"])
            writer.writeheader()
            writer.writerows(default_data)

    def normalize_path(self, path: str) -> str:
        """Приводит путь к каноническому виду (абсолютный путь)."""
        if not path.startswith("/"):
            path = os.path.normpath(os.path.join(self.current_dir, path))
        else:
            path = os.path.normpath(path)

        path = path.replace("\\", "/")
        if not path.startswith("/"):
            path = "/" + path
        return path

    def list_dir(self, path: str = None) -> list:
        """Возвращает список файлов и папок в указанной директории."""
        target_dir = self.normalize_path(path) if path else self.current_dir

        if target_dir not in self.fs or self.fs[target_dir]["type"] != "dir":
            raise ValueError(f"Директория '{target_dir}' не найдена")

        items = set()
        prefix = target_dir if target_dir.endswith("/") else target_dir + "/"

        for p in self.fs:
            if p != target_dir and p.startswith(prefix):
                relative = p[len(prefix) :]
                parts = relative.split("/")
                items.add(parts[0])

        return sorted(list(items))

    def change_dir(self, path: str):
        """Изменяет текущую рабочую директорию."""
        target_dir = self.normalize_path(path)
        if target_dir in self.fs and self.fs[target_dir]["type"] == "dir":
            self.current_dir = target_dir
        else:
            raise ValueError(
                f"cd: no such file or directory: {path}"
            )

    def reset_to_default(self):
        """Очищает физическое представление VFS и сбрасывает на базовую VFS."""
        self.create_default_csv()
        self.load_vfs()
        self.current_dir = "/"


class Emulator(tk.Tk):

    def __init__(self, vfs_path: str, script_path: str = None):
        super().__init__()

        self.vfs_path = vfs_path
        self.script_path = script_path
        self.vfs = VFS(vfs_path)

        self.vfs_name = os.path.basename(vfs_path) if vfs_path else "vfs.csv"
        self.title(f"Эмулятор VFS — {self.vfs_name}")

        self.output = tk.Text(self, height=20, width=80, bg="black", fg="white")
        self.output.pack(fill=tk.BOTH, expand=True)

        self.entry = tk.Entry(
            self, bg="white", fg="black", insertbackground="black"
        )
        self.entry.pack(fill=tk.X)
        self.entry.bind("<Return>", self.on_enter)

        self.print_debug_info()
        if self.script_path:
            self.run_startup_script(self.script_path)

        self.show_prompt()

    @property
    def prompt(self) -> str:
        return f"[{self.vfs_name}:{self.vfs.current_dir}]$ "

    def print_debug_info(self):
        self.output.insert(tk.END, f"Путь к VFS (CSV): {self.vfs_path}\n")
        self.output.insert(
            tk.END, f"Путь к стартовому скрипту: {self.script_path}\n"
        )
        self.output.insert(tk.END, "\n")

    def show_prompt(self):
        self.output.insert(tk.END, self.prompt)
        self.output.see(tk.END)

    def execute_command(self, user_input: str):
        self.output.insert(tk.END, user_input + "\n")
        try:
            args = shlex.split(user_input)
        except Exception as e:
            self.output.insert(tk.END, f"Ошибка синтаксиса: {e}\n")
            return

        if not args:
            return

        command = args[0]
        command_args = args[1:]

        self.parser(command, command_args)

    def run_startup_script(self, script_path: str):
        self.output.insert(
            tk.END, f"--- Запуск стартового скрипта: {script_path} ---\n"
        )
        if not os.path.exists(script_path):
            self.output.insert(
                tk.END, f"Ошибка: скрипт '{script_path}' не найден\n\n"
            )
            return

        try:
            with open(script_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            for line in lines:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue

                self.output.insert(tk.END, self.prompt)
                self.execute_command(line)

            self.output.insert(tk.END, "Завершение стартового скрипта\n\n")

        except Exception as e:
            self.output.insert(
                tk.END, f"Ошибка при чтении скрипта: {e}\n\n"
            )

    def on_enter(self, event=None):
        user_input = self.entry.get()
        self.entry.delete(0, tk.END)

        self.execute_command(user_input)
        self.show_prompt()

    def parser(self, command, args):
        if command == "help":
            self.output.insert(
                tk.END,
                "Доступные команды:\n"
                "  ls [path]   - вывести содержимое директории\n"
                "  cd <path>   - сменить директорию\n"
                "  vfs-init    - сбросить VFS на VFS по умолчанию\n"
                "  help        - показать справку\n"
                "  exit        - завершить работу\n",
            )

        elif command == "cd":
            if len(args) != 1:
                self.output.insert(
                    tk.END, "Ошибка: cd требует ровно 1 аргумент\n"
                )
            else:
                try:
                    self.vfs.change_dir(args[0])
                except Exception as e:
                    self.output.insert(tk.END, f"Ошибка: {e}\n")

        elif command == "ls":
            target_path = args[0] if len(args) > 0 else None
            try:
                items = self.vfs.list_dir(target_path)
                if items:
                    self.output.insert(tk.END, "  ".join(items) + "\n")
            except Exception as e:
                self.output.insert(tk.END, f"Ошибка: {e}\n")

        elif command == "vfs-init":
            if len(args) > 0:
                self.output.insert(
                    tk.END, "Ошибка: vfs-init не принимает аргументов\n"
                )
                return
            self.vfs.reset_to_default()
            self.output.insert(
                tk.END, "VFS сброшена до конфигурации по умолчанию.\n"
            )

        elif command == "exit":
            if len(args) > 0:
                self.output.insert(
                    tk.END, "Ошибка: команда exit не принимает аргументов\n"
                )
                return
            self.destroy()

        else:
            self.output.insert(
                tk.END, f"Ошибка: неизвестная команда '{command}'\n"
            )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Эмулятор VFS")
    parser.add_argument(
        "--vfs",
        type=str,
        default="vfs.csv",
        help="Путь к CSV-файлу виртуальной файловой системы",
    )
    parser.add_argument(
        "--script",
        type=str,
        default=None,
        help="Путь к стартовому скрипту с командами",
    )

    parsed_args = parser.parse_args()

    app = Emulator(vfs_path=parsed_args.vfs, script_path=parsed_args.script)
    app.mainloop()