# 🚀 Инструкция по деплою бота на сервер

> **📘 Для подробного пошагового мануала см. [DEPLOY_MANUAL.md](DEPLOY_MANUAL.md)**
> 
> Этот файл содержит краткую инструкцию. Полный мануал с детальными шагами, рекомендациями по выбору сервера и решением проблем находится в `DEPLOY_MANUAL.md`.

## ⚠️ Важно: Перед запуском бота

После клонирования проекта и перед первым запуском необходимо выполнить миграции базы данных:

```bash
# Миграция для добавления полей языка и связанных категорий
python migrate_db.py

# Миграция для добавления системы аутентификации через external_id
python migrate_auth.py

# Миграция для добавления поля disclaimer_accepted
python migrate_disclaimer.py
```

Эти миграции нужно выполнить только один раз при первом развертывании.

## 📋 Требования к серверу

### Минимальные требования:
- **ОС**: Linux (Ubuntu 20.04+ / Debian 11+ / CentOS 8+)
- **RAM**: 512 MB (рекомендуется 1 GB)
- **CPU**: 1 ядро (рекомендуется 2 ядра)
- **Диск**: 5 GB свободного места
- **Python**: 3.11+ (или Docker)

### Рекомендуемые требования:
- **RAM**: 2 GB
- **CPU**: 2 ядра
- **Диск**: 10 GB SSD
- **Сеть**: стабильное интернет-соединение

## 🔧 Вариант 1: Деплой с Docker (рекомендуется)

### Шаг 1: Установка Docker

```bash
# Ubuntu/Debian
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Перезайдите в систему или выполните:
newgrp docker
```

### Шаг 2: Клонирование проекта

```bash
# На сервере создайте директорию
mkdir -p ~/telegram-bot
cd ~/telegram-bot

# Загрузите файлы проекта (через git, scp или другой способ)
# Убедитесь, что все файлы на месте:
# - main.py
# - requirements.txt
# - Dockerfile
# - docker-compose.yml
# - .env (с BOT_TOKEN)
# - все папки (handlers, database, keyboards, etc.)
```

### Шаг 3: Настройка .env

```bash
# Создайте файл .env
nano .env

# Добавьте:
BOT_TOKEN=ваш_токен_бота_здесь
DATABASE_URL=sqlite+aiosqlite:///./data/bot.db
```

### Шаг 4: Запуск бота

```bash
# Запуск через docker-compose
docker-compose up -d

# Проверка логов
docker-compose logs -f

# Остановка
docker-compose down
```

## 🔧 Вариант 2: Деплой без Docker

### Шаг 1: Установка Python

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3.11 python3.11-venv python3-pip -y

# Проверка
python3.11 --version
```

### Шаг 2: Создание виртуального окружения

```bash
# Создайте директорию проекта
mkdir -p ~/telegram-bot
cd ~/telegram-bot

# Создайте виртуальное окружение
python3.11 -m venv venv

# Активируйте
source venv/bin/activate
```

### Шаг 3: Установка зависимостей

```bash
# Установите зависимости
pip install -r requirements.txt
```

### Шаг 4: Настройка .env

```bash
# Создайте файл .env
nano .env

# Добавьте:
BOT_TOKEN=ваш_токен_бота_здесь
DATABASE_URL=sqlite+aiosqlite:///./bot.db
```

### Шаг 5: Запуск бота

```bash
# Запуск напрямую
python main.py

# Или через systemd (см. ниже)
```

## 🔄 Автозапуск через systemd (без Docker)

### Создание сервиса

```bash
# Создайте файл сервиса
sudo nano /etc/systemd/system/telegram-bot.service
```

### Содержимое файла:

```ini
[Unit]
Description=Telegram Bot
After=network.target

[Service]
Type=simple
User=ваш_пользователь
WorkingDirectory=/home/ваш_пользователь/telegram-bot
Environment="PATH=/home/ваш_пользователь/telegram-bot/venv/bin"
ExecStart=/home/ваш_пользователь/telegram-bot/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Управление сервисом

```bash
# Перезагрузите systemd
sudo systemctl daemon-reload

# Запустите бота
sudo systemctl start telegram-bot

# Автозапуск при загрузке
sudo systemctl enable telegram-bot

# Проверка статуса
sudo systemctl status telegram-bot

# Просмотр логов
sudo journalctl -u telegram-bot -f
```

## 📊 Мониторинг

### Проверка работы бота

```bash
# Docker
docker-compose ps
docker-compose logs -f --tail=50

# Systemd
sudo systemctl status telegram-bot
sudo journalctl -u telegram-bot -f
```

### Проверка БД

```bash
# Если используете SQLite
sqlite3 data/bot.db "SELECT COUNT(*) FROM users;"
```

## 🔒 Безопасность

1. **Не храните .env в git**
   ```bash
   echo ".env" >> .gitignore
   ```

2. **Ограничьте доступ к файлам**
   ```bash
   chmod 600 .env
   chmod 700 ~/telegram-bot
   ```

3. **Используйте firewall**
   ```bash
   sudo ufw allow 22/tcp  # SSH
   sudo ufw enable
   ```

## 🐛 Решение проблем

### Бот не запускается

1. Проверьте токен в .env
2. Проверьте логи: `docker-compose logs` или `journalctl -u telegram-bot`
3. Проверьте права доступа к файлам

### Ошибки БД

1. Проверьте права на директорию data/
2. Убедитесь, что DATABASE_URL правильный
3. Проверьте логи

### Бот не отвечает

1. Проверьте интернет-соединение
2. Проверьте, что бот запущен: `docker-compose ps` или `systemctl status`
3. Проверьте логи на ошибки

## 📝 Обновление бота

```bash
# Docker
cd ~/telegram-bot
git pull  # или загрузите новые файлы
docker-compose down
docker-compose build
docker-compose up -d

# Systemd
cd ~/telegram-bot
git pull  # или загрузите новые файлы
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart telegram-bot
```

## 💡 Полезные команды

```bash
# Просмотр использования ресурсов
docker stats  # для Docker
htop  # общее использование

# Очистка логов Docker
docker-compose logs --tail=0 -f

# Бэкап БД
cp data/bot.db data/bot.db.backup
```

---

**Готово! Бот должен работать на сервере.** 🎉

