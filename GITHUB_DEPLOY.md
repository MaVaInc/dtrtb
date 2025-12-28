# 📤 Мануал по выкладыванию проекта на GitHub

## 📋 Содержание

1. [Подготовка проекта](#подготовка-проекта)
2. [Создание репозитория на GitHub](#создание-репозитория-на-github)
3. [Настройка Git](#настройка-git)
4. [Инициализация репозитория](#инициализация-репозитория)
5. [Первый коммит и push](#первый-коммит-и-push)
6. [Работа с репозиторием](#работа-с-репозиторием)
7. [Безопасность](#безопасность)

---

## 🔧 Подготовка проекта

### Шаг 1: Проверка .gitignore

Убедитесь, что у вас есть файл `.gitignore` в корне проекта. Он должен исключать:

- Секретные файлы (`.env`, токены)
- Базы данных (`bot.db`, `*.db`)
- Кэш Python (`__pycache__/`, `*.pyc`)
- Виртуальное окружение (`venv/`, `.venv/`)
- Логи и временные файлы

**Проверьте файл `.gitignore`:**

```bash
cat .gitignore
```

Если файла нет или он неполный, создайте/обновите его (см. ниже).

### Шаг 2: Создание/обновление .gitignore

```bash
# Создайте или откройте файл .gitignore
nano .gitignore
```

**Содержимое `.gitignore` (полная версия):**

```gitignore
# Секретные файлы и конфигурация
.env
.env.local
.env.*.local
config.local.py
*.key
*.pem

# Базы данных
*.db
*.sqlite
*.sqlite3
data/
bot.db
*.db-journal

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Виртуальное окружение
venv/
env/
ENV/
.venv/
virtualenv/

# IDE и редакторы
.vscode/
.idea/
*.swp
*.swo
*~
.DS_Store
Thumbs.db

# Логи
*.log
logs/
*.log.*

# Временные файлы
*.tmp
*.temp
.cache/

# Docker (если используете)
.dockerignore

# Миграции (опционально - можно оставить в репозитории)
# migrate_*.py

# Изображения с личными данными (если есть)
# images/personal/
# images/users/
```

**Сохраните файл:**

- В nano: `Ctrl+O` (сохранить), `Enter` (подтвердить), `Ctrl+X` (выйти)
- В VS Code: просто сохраните файл

### Шаг 3: Проверка секретных файлов

**ВАЖНО!** Убедитесь, что в репозиторий не попадут секретные данные:

```bash
# Проверьте, что .env не отслеживается
git check-ignore .env
# Должно вывести: .env

# Проверьте, что БД не отслеживается
git check-ignore bot.db
# Должно вывести: bot.db

# Если файлы уже были добавлены в git ранее, удалите их из индекса:
git rm --cached .env
git rm --cached bot.db
```

### Шаг 4: Создание примера конфигурации

Создайте файл `.env.example` для других разработчиков:

```bash
nano .env.example
```

**Содержимое `.env.example`:**

```env
BOT_TOKEN=your_bot_token_here
DATABASE_URL=sqlite+aiosqlite:///./bot.db
```

Этот файл можно безопасно коммитить в репозиторий.

---

## 🌐 Создание репозитория на GitHub

### Шаг 1: Вход в GitHub

1. Откройте https://github.com
2. Войдите в свой аккаунт (или создайте новый)

### Шаг 2: Создание нового репозитория

1. Нажмите на **"+"** в правом верхнем углу
2. Выберите **"New repository"**

3. Заполните форму:
   - **Repository name**: `telegram-bot` (или другое имя)
   - **Description**: "Telegram bot with admin panel and multi-language support"
   - **Visibility**: 
     - **Public** - если хотите открытый репозиторий
     - **Private** - если хотите приватный (рекомендуется для коммерческих проектов)
   - **НЕ** ставьте галочки:
     - ❌ Add a README file (мы создадим свой)
     - ❌ Add .gitignore (у нас уже есть)
     - ❌ Choose a license (можно добавить позже)

4. Нажмите **"Create repository"**

### Шаг 3: Копирование URL репозитория

После создания репозитория GitHub покажет страницу с инструкциями. Скопируйте URL репозитория:

- **HTTPS**: `https://github.com/ваш_username/telegram-bot.git`
- **SSH**: `git@github.com:ваш_username/telegram-bot.git`

**Рекомендация:** Используйте HTTPS для начала (проще настройка).

---

## ⚙️ Настройка Git

### Шаг 1: Проверка установки Git

```bash
# Проверьте, установлен ли Git
git --version

# Если не установлен:

# Windows:
# См. подробную инструкцию в INSTALL_GIT_WINDOWS.md
# Или скачайте с https://git-scm.com/download/win

# Linux (Ubuntu/Debian):
sudo apt update
sudo apt install git -y

# macOS:
# Установите через Homebrew: brew install git
# Или скачайте с https://git-scm.com/download/mac
```

### Шаг 2: Настройка имени и email

```bash
# Установите ваше имя (будет видно в коммитах)
git config --global user.name "Ваше Имя"

# Установите ваш email (будет видно в коммитах)
git config --global user.email "ваш_email@example.com"

# Проверьте настройки
git config --list
```

**Важно:** Email должен совпадать с email в вашем GitHub аккаунте (для правильного отображения аватара).

### Шаг 3: Настройка SSH ключа (опционально, но рекомендуется)

Если хотите использовать SSH вместо HTTPS:

```bash
# Проверьте, есть ли уже SSH ключ
ls -al ~/.ssh

# Если нет, создайте новый:
ssh-keygen -t ed25519 -C "ваш_email@example.com"

# Нажмите Enter для всех вопросов (или введите пароль)

# Скопируйте публичный ключ
cat ~/.ssh/id_ed25519.pub

# Скопируйте весь вывод (начинается с ssh-ed25519...)
```

**Добавление ключа на GitHub:**

1. Откройте https://github.com/settings/keys
2. Нажмите **"New SSH key"**
3. Вставьте скопированный ключ
4. Нажмите **"Add SSH key"**

---

## 📦 Инициализация репозитория

### Шаг 1: Переход в директорию проекта

```bash
# Перейдите в корневую директорию проекта
cd C:\bot  # Windows
# или
cd ~/bot   # Linux/macOS
```

### Шаг 2: Инициализация Git

```bash
# Инициализируйте репозиторий
git init

# Проверьте статус
git status
```

### Шаг 3: Добавление файлов

```bash
# Добавьте все файлы (кроме тех, что в .gitignore)
git add .

# Проверьте, что добавлено
git status

# Должны увидеть список файлов, готовых к коммиту
# НЕ должны видеть: .env, bot.db, __pycache__, venv/
```

### Шаг 4: Первый коммит

```bash
# Создайте первый коммит
git commit -m "Initial commit: Telegram bot with admin panel"

# Проверьте историю
git log
```

---

## 🚀 Первый коммит и push

### Шаг 1: Добавление remote репозитория

```bash
# Добавьте GitHub репозиторий как remote (HTTPS)
git remote add origin https://github.com/ваш_username/telegram-bot.git

# Или если используете SSH:
# git remote add origin git@github.com:ваш_username/telegram-bot.git

# Проверьте
git remote -v
```

### Шаг 2: Переименование основной ветки (опционально)

```bash
# Переименуйте ветку в main (современный стандарт)
git branch -M main

# Или оставьте master (старый стандарт)
```

### Шаг 3: Push на GitHub

```bash
# Отправьте код на GitHub
git push -u origin main

# Если используете master:
# git push -u origin master
```

**Если запросит авторизацию:**

- **HTTPS**: Введите ваш GitHub username и Personal Access Token (не пароль!)
  - Создайте токен: https://github.com/settings/tokens
  - Нажмите "Generate new token (classic)"
  - Выберите scope: `repo`
  - Скопируйте токен и используйте его как пароль

- **SSH**: Должно работать автоматически, если ключ добавлен

### Шаг 4: Проверка на GitHub

1. Откройте ваш репозиторий на GitHub
2. Убедитесь, что все файлы загружены
3. Проверьте, что `.env` и `bot.db` **НЕ** видны в репозитории

---

## 💻 Работа с репозиторием

### Основные команды Git

```bash
# Проверить статус
git status

# Добавить изменения
git add .                    # Все файлы
git add file.py              # Конкретный файл
git add folder/               # Папку

# Создать коммит
git commit -m "Описание изменений"

# Отправить на GitHub
git push

# Получить изменения с GitHub
git pull

# Посмотреть историю
git log
git log --oneline            # Краткая версия

# Посмотреть изменения
git diff                     # Несохраненные изменения
git diff --staged            # Изменения в staging area
```

### Типичный workflow

```bash
# 1. Получите последние изменения
git pull

# 2. Внесите изменения в код

# 3. Проверьте статус
git status

# 4. Добавьте изменения
git add .

# 5. Создайте коммит
git commit -m "Добавлена новая функция поиска"

# 6. Отправьте на GitHub
git push
```

### Создание веток (branches)

```bash
# Создать новую ветку
git checkout -b feature/new-feature

# Или (новый синтаксис)
git switch -c feature/new-feature

# Переключиться на ветку
git checkout main
git switch main

# Посмотреть все ветки
git branch

# Отправить ветку на GitHub
git push -u origin feature/new-feature
```

### Слияние веток

```bash
# Переключитесь на основную ветку
git checkout main

# Получите последние изменения
git pull

# Слейте ветку
git merge feature/new-feature

# Отправьте изменения
git push
```

---

## 🔒 Безопасность

### ✅ Что МОЖНО коммитить:

- ✅ Весь код проекта (`.py` файлы)
- ✅ Конфигурационные файлы (кроме `.env`)
- ✅ `requirements.txt`
- ✅ `README.md`, `DEPLOY.md`, документация
- ✅ `.gitignore`
- ✅ `.env.example` (без реальных токенов!)
- ✅ Миграции (`migrate_*.py`)
- ✅ Изображения (кроме личных данных)

### ❌ Что НИКОГДА нельзя коммитить:

- ❌ `.env` файл с реальными токенами
- ❌ Базы данных (`bot.db`, `*.db`)
- ❌ Личные ключи и сертификаты
- ❌ Пароли и секреты
- ❌ Логи с личными данными
- ❌ Файлы с реальными ID пользователей

### Проверка перед коммитом

```bash
# Проверьте, что не добавляете секреты
git status

# Проверьте содержимое коммита
git diff --cached

# Если случайно добавили .env, удалите из индекса:
git reset HEAD .env
git rm --cached .env
```

### Если секреты уже попали в репозиторий

**КРИТИЧЕСКИЕ ДЕЙСТВИЯ:**

1. **Немедленно смените все токены/пароли:**
   - Создайте новый BOT_TOKEN в BotFather
   - Обновите `.env` на сервере

2. **Удалите секреты из истории Git:**
   ```bash
   # Используйте git-filter-repo или BFG Repo-Cleaner
   # Или создайте новый репозиторий
   ```

3. **Используйте GitHub Secrets для CI/CD:**
   - Settings → Secrets → Actions
   - Добавьте секреты там

---

## 📝 Создание README.md

Создайте файл `README.md` для описания проекта:

```bash
nano README.md
```

**Пример содержимого:**

```markdown
# Telegram Bot

Telegram бот с админ-панелью и поддержкой нескольких языков.

## Возможности

- 🔐 Аутентификация через external ID
- 🌐 Поддержка русского и немецкого языков
- 🔧 Интерактивная админ-панель
- 📋 Система категорий и контента
- 🔍 Поиск по категориям и контенту
- ⭐ Избранное
- 📊 Аналитика

## Установка

1. Клонируйте репозиторий:
```bash
git clone https://github.com/ваш_username/telegram-bot.git
cd telegram-bot
```

2. Установите зависимости:
```bash
pip install -r requirements.txt
```

3. Создайте файл `.env`:
```bash
cp .env.example .env
nano .env
```

4. Выполните миграции:
```bash
python migrate_db.py
python migrate_auth.py
python migrate_disclaimer.py
```

5. Запустите бота:
```bash
python main.py
```

## Настройка

См. [DEPLOY_MANUAL.md](DEPLOY_MANUAL.md) для подробной инструкции по деплою.

## Лицензия

[Укажите лицензию, если есть]
```

---

## 🎯 Чек-лист перед push

Перед отправкой кода на GitHub проверьте:

- [ ] `.gitignore` настроен правильно
- [ ] `.env` файл не отслеживается Git
- [ ] `bot.db` не отслеживается Git
- [ ] Все секреты удалены из кода
- [ ] Создан `.env.example` (без реальных токенов)
- [ ] `README.md` создан и заполнен
- [ ] Код протестирован локально
- [ ] Коммиты имеют понятные сообщения

---

## 🆘 Решение проблем

### Ошибка: "fatal: remote origin already exists"

```bash
# Удалите существующий remote
git remote remove origin

# Добавьте заново
git remote add origin https://github.com/ваш_username/telegram-bot.git
```

### Ошибка: "Permission denied (publickey)"

```bash
# Проверьте SSH ключ
ssh -T git@github.com

# Или используйте HTTPS вместо SSH
git remote set-url origin https://github.com/ваш_username/telegram-bot.git
```

### Ошибка: "failed to push some refs"

```bash
# Получите последние изменения
git pull origin main --rebase

# Или
git pull origin main

# Затем попробуйте снова
git push
```

### Отменить последний коммит (еще не push)

```bash
# Отменить коммит, но оставить изменения
git reset --soft HEAD~1

# Отменить коммит и изменения
git reset --hard HEAD~1
```

### Удалить файл из Git, но оставить локально

```bash
git rm --cached file.txt
git commit -m "Remove file.txt from tracking"
git push
```

---

## 📚 Полезные ссылки

- [Официальная документация Git](https://git-scm.com/doc)
- [GitHub Guides](https://guides.github.com/)
- [Git Cheat Sheet](https://education.github.com/git-cheat-sheet-education.pdf)
- [GitHub Desktop](https://desktop.github.com/) - GUI для Git

---

## ✅ Готово!

Ваш проект теперь на GitHub! 🎉

**Следующие шаги:**
1. Добавьте описание проекта на странице репозитория
2. Настройте GitHub Actions для CI/CD (опционально)
3. Добавьте Issues и Projects для управления задачами
4. Пригласите соавторов (Settings → Collaborators)

**Удачной работы с Git!** 🚀

