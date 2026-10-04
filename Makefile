# Переменные
PYTHON = python3
SRC_DIR = src
TEST_DIR = tests
MAIN_SCRIPT = $(SRC_DIR)/main.py
VFS_CSV = vfs.csv
STARTUP_SCRIPT = startup.txt

.PHONY: all run test lint clean help

# Команда по умолчанию
all: test

# Запуск эмулятора с параметрами по умолчанию
run:
	$(PYTHON) $(MAIN_SCRIPT) --vfs $(VFS_CSV)

# Запуск эмулятора со стартовым скриптом
run-script:
	$(PYTHON) $(MAIN_SCRIPT) --vfs $(VFS_CSV) --script $(STARTUP_SCRIPT)

# Запуск автотестов
test:
	$(PYTHON) -m unittest discover -s $(TEST_DIR) -p "test_*.py"

# Проверка стиля кода (если установлен flake8)
lint:
	flake8 $(SRC_DIR) $(TEST_DIR)

# Очистка кэша Python и временных файлов
clean:
	rm -rf __pycache__ $(SRC_DIR)/__pycache__ $(TEST_DIR)/__pycache__
	rm -rf .pytest_cache .coverage
	find . -type f -name "*.pyc" -delete

# Справка по доступным командам
help:
	@echo "Доступные команды:"
	@echo "  make run        - Запустить эмулятор VFS"
	@echo "  make run-script - Запустить эмулятор со стартовым скриптом"
	@echo "  make test       - Запустить юнит-тесты"
	@echo "  make lint       - Проверить код линтером flake8"
	@echo "  make clean      - Удалить кэш Python и временные файлы"
