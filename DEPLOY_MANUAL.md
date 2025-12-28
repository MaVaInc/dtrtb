# 📘 Полный мануал по деплою Telegram бота на сервер

## 🎯 Рекомендации по выбору сервера

### Варианты серверов:

1. **Hetzner Cloud** (рекомендуется)
   - **Конфигурация**: CX11 (1 vCPU, 2 GB RAM, 20 GB SSD) - ~€4/месяц
   - **Ubuntu**: 22.04 LTS или 24.04 LTS
   - **Почему**: Немецкий провайдер, хорошая цена/качество, низкая латентность в Европе

2. **DigitalOcean**
   - **Конфигурация**: Basic Droplet (1 vCPU, 1 GB RAM, 25 GB SSD) - $6/месяц
   - **Ubuntu**: 22.04 LTS
   - **Почему**: Простота использования, хорошая документация

3. **Vultr**
   - **Конфигурация**: Regular Performance (1 vCPU, 1 GB RAM, 25 GB SSD) - $6/месяц
   - **Ubuntu**: 22.04 LTS
   - **Почему**: Быстрая настройка, хорошая производительность

4. **AWS Lightsail** (для начинающих)
   - **Конфигурация**: $3.50/месяц (512 MB RAM) или $5/месяц (1 GB RAM)
   - **Ubuntu**: 22.04 LTS
   - **Почему**: Простота, интеграция с AWS

### Минимальные требования:
- **RAM**: 1 GB (рекомендуется 2 GB)
- **CPU**: 1 ядро (рекомендуется 2 ядра)
- **Диск**: 20 GB SSD
- **ОС**: Ubuntu 22.04 LTS или 24.04 LTS

---

## 📋 Шаг 1: Создание и настройка сервера

### 1.1 Создание сервера (на примере Hetzner)

1. Зайдите на https://console.hetzner.cloud/
2. Создайте новый проект
3. Нажмите "Add Server"
4. Выберите:
   - **Location**: ближайший к вам (например, Nuremberg, Germany)
   - **Image**: Ubuntu 22.04 или 24.04
   - **Type**: CX11 (2 GB RAM) или CPX11 (2 GB RAM, лучше CPU)
   - **SSH Keys**: добавьте ваш SSH ключ (рекомендуется) или используйте пароль
5. Нажмите "Create & Buy Now"

### 1.2 Подключение к серверу

```bash
# Если используете SSH ключ
ssh root@ваш_ip_адрес

# Если используете пароль
ssh root@ваш_ip_адрес
# Введите пароль, который вы получили при создании сервера
```

### 1.3 Первоначальная настройка сервера

```bash
# Обновляем систему
apt update && apt upgrade -y

# Устанавливаем необходимые пакеты
apt install -y python3 python3-pip python3-venv git curl wget nano ufw

# Создаем пользователя для бота (не используем root)
adduser botuser
# Введите пароль и подтвердите (можно просто нажать Enter для остальных полей)

# Добавляем пользователя в группу sudo
usermod -aG sudo botuser

# Переключаемся на нового пользователя
su - botuser
```

---

## 📋 Шаг 2: Настройка безопасности

### 2.1 Настройка firewall

```bash
# Включаем firewall
sudo ufw enable

# Разрешаем SSH (важно сделать ПЕРВЫМ!)
sudo ufw allow 22/tcp

# Разрешаем HTTP/HTTPS (если нужно)
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Проверяем статус
sudo ufw status
```

### 2.2 Настройка SSH (опционально, но рекомендуется)

```bash
# Редактируем конфиг SSH
sudo nano /etc/ssh/sshd_config

# Измените или добавьте:
# PermitRootLogin no
# PasswordAuthentication no  # если используете только SSH ключи
# Port 2222  # измените порт для безопасности (необязательно)

# Перезапускаем SSH
sudo systemctl restart sshd
```

---

## 📋 Шаг 3: Установка проекта

### 3.1 Клонирование или загрузка файлов

**Вариант A: Через Git (если проект в репозитории)**

```bash
# Создаем директорию для проекта
mkdir -p ~/telegram-bot
cd ~/telegram-bot

# Клонируем репозиторий
git clone https://ваш_репозиторий.git .

# Или если репозиторий приватный:
git clone https://ваш_токен@github.com/username/repo.git .
```

**Вариант B: Через SCP (если проект локально)**

На вашем локальном компьютере:

```bash
# Создайте архив проекта (исключая ненужные файлы)
cd /путь/к/проекту
tar -czf bot.tar.gz --exclude='__pycache__' --exclude='*.pyc' --exclude='.git' --exclude='bot.db' .

# Загрузите на сервер
scp bot.tar.gz botuser@ваш_ip:/home/botuser/

# На сервере распакуйте
ssh botuser@ваш_ip
cd ~
tar -xzf bot.tar.gz -C telegram-bot
cd telegram-bot
```

**Вариант C: Через rsync (рекомендуется для обновлений)**

```bash
# На локальном компьютере
rsync -avz --exclude '__pycache__' --exclude '*.pyc' --exclude '.git' --exclude 'bot.db' \
  /путь/к/проекту/ botuser@ваш_ip:/home/botuser/telegram-bot/
```

### 3.2 Проверка файлов

```bash
cd ~/telegram-bot

# Проверьте, что все файлы на месте
ls -la

# Должны быть:
# - main.py
# - requirements.txt
# - config.py
# - database/
# - handlers/
# - keyboards/
# - middleware/
# - utils/
# - images/
# - migrate_db.py
# - migrate_auth.py
# - migrate_disclaimer.py
```

---

## 📋 Шаг 4: Настройка Python окружения

### 4.1 Создание виртуального окружения

```bash
cd ~/telegram-bot

# Создаем виртуальное окружение
python3 -m venv venv

# Активируем его
source venv/bin/activate

# Обновляем pip
pip install --upgrade pip
```

### 4.2 Установка зависимостей

```bash
# Устанавливаем все зависимости
pip install -r requirements.txt

# Проверяем установку
pip list
```

---

## 📋 Шаг 5: Настройка конфигурации

### 5.1 Создание файла .env

```bash
cd ~/telegram-bot

# Создаем файл .env
nano .env
```

**Содержимое файла .env:**

```env
BOT_TOKEN=ваш_токен_бота_от_BotFather
DATABASE_URL=sqlite+aiosqlite:///./bot.db
```

**Как получить BOT_TOKEN:**
1. Откройте Telegram
2. Найдите @BotFather
3. Отправьте `/newbot`
4. Следуйте инструкциям
5. Скопируйте токен (выглядит как `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`)

### 5.2 Защита файла .env

```bash
# Устанавливаем права доступа (только владелец может читать)
chmod 600 .env

# Проверяем
ls -la .env
# Должно быть: -rw------- (600)
```

### 5.3 Проверка config.py

```bash
# Убедитесь, что config.py правильно читает .env
cat config.py
```

---

## 📋 Шаг 6: Инициализация базы данных

### 6.1 Создание директории для БД

```bash
cd ~/telegram-bot

# Создаем директорию data (если нужно)
mkdir -p data
```

### 6.2 Выполнение миграций

```bash
# Активируем виртуальное окружение (если еще не активировано)
source venv/bin/activate

# Выполняем миграции в правильном порядке
python migrate_db.py
python migrate_auth.py
python migrate_disclaimer.py

# Проверяем, что БД создана
ls -la bot.db
# или
ls -la data/bot.db  # если БД в папке data
```

### 6.3 Добавление разрешенных ID (если нужно)

```bash
# Создайте файл ids.txt с ID пользователей (по одному на строку)
nano ids.txt

# Добавьте ID (например):
# 12345678
# 87654321
# 11223344

# Запустите скрипт для добавления ID в БД
python add_allowed_ids.py
```

---

## 📋 Шаг 7: Тестовый запуск

### 7.1 Первый запуск

```bash
cd ~/telegram-bot
source venv/bin/activate

# Запускаем бота
python main.py
```

**Что должно произойти:**
- Бот должен запуститься без ошибок
- В консоли должны появиться логи
- Бот должен отвечать на команду `/start` в Telegram

### 7.2 Проверка работы

1. Откройте Telegram
2. Найдите вашего бота
3. Отправьте `/start`
4. Проверьте, что бот отвечает

### 7.3 Остановка бота

Нажмите `Ctrl+C` в терминале для остановки.

---

## 📋 Шаг 8: Настройка автозапуска (systemd)

### 8.1 Создание сервиса

```bash
# Создаем файл сервиса
sudo nano /etc/systemd/system/telegram-bot.service
```

**Содержимое файла:**

```ini
[Unit]
Description=Telegram Bot Service
After=network.target

[Service]
Type=simple
User=botuser
Group=botuser
WorkingDirectory=/home/botuser/telegram-bot
Environment="PATH=/home/botuser/telegram-bot/venv/bin"
ExecStart=/home/botuser/telegram-bot/venv/bin/python /home/botuser/telegram-bot/main.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

# Ограничения ресурсов (опционально)
MemoryLimit=512M
CPUQuota=50%

[Install]
WantedBy=multi-user.target
```

**Важно:** Замените `botuser` на имя вашего пользователя, если оно другое!

### 8.2 Активация сервиса

```bash
# Перезагружаем systemd
sudo systemctl daemon-reload

# Включаем автозапуск
sudo systemctl enable telegram-bot

# Запускаем сервис
sudo systemctl start telegram-bot

# Проверяем статус
sudo systemctl status telegram-bot
```

### 8.3 Полезные команды для управления

```bash
# Запустить бота
sudo systemctl start telegram-bot

# Остановить бота
sudo systemctl stop telegram-bot

# Перезапустить бота
sudo systemctl restart telegram-bot

# Посмотреть статус
sudo systemctl status telegram-bot

# Посмотреть логи
sudo journalctl -u telegram-bot -f

# Посмотреть последние 100 строк логов
sudo journalctl -u telegram-bot -n 100
```

---

## 📋 Шаг 9: Настройка логирования

### 9.1 Создание директории для логов

```bash
cd ~/telegram-bot
mkdir -p logs
```

### 9.2 Ротация логов (опционально)

```bash
# Создаем конфиг для ротации логов
sudo nano /etc/logrotate.d/telegram-bot
```

**Содержимое:**

```
/home/botuser/telegram-bot/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    notifempty
    missingok
}
```

---

## 📋 Шаг 10: Мониторинг и обслуживание

### 10.1 Проверка работы бота

```bash
# Проверка статуса
sudo systemctl status telegram-bot

# Проверка использования ресурсов
htop
# или
top

# Проверка использования диска
df -h

# Проверка использования памяти
free -h
```

### 10.2 Бэкап базы данных

```bash
# Создаем директорию для бэкапов
mkdir -p ~/backups

# Создаем скрипт бэкапа
nano ~/backup-bot.sh
```

**Содержимое скрипта:**

```bash
#!/bin/bash
BACKUP_DIR="$HOME/backups"
BOT_DIR="$HOME/telegram-bot"
DATE=$(date +%Y%m%d_%H%M%S)

# Создаем бэкап БД
cp "$BOT_DIR/bot.db" "$BACKUP_DIR/bot_$DATE.db"

# Удаляем старые бэкапы (старше 7 дней)
find "$BACKUP_DIR" -name "bot_*.db" -mtime +7 -delete

echo "Backup created: bot_$DATE.db"
```

```bash
# Делаем скрипт исполняемым
chmod +x ~/backup-bot.sh

# Тестируем
~/backup-bot.sh

# Настраиваем автоматический бэкап (каждый день в 3:00)
crontab -e

# Добавьте строку:
0 3 * * * /home/botuser/backup-bot.sh >> /home/botuser/backups/backup.log 2>&1
```

### 10.3 Обновление бота

```bash
cd ~/telegram-bot

# Останавливаем бота
sudo systemctl stop telegram-bot

# Делаем бэкап
~/backup-bot.sh

# Обновляем код (если через git)
git pull

# Или загружаем новые файлы через rsync/scp

# Обновляем зависимости (если изменился requirements.txt)
source venv/bin/activate
pip install -r requirements.txt

# Выполняем миграции (если есть новые)
python migrate_db.py  # если нужно
python migrate_auth.py  # если нужно
python migrate_disclaimer.py  # если нужно

# Запускаем бота
sudo systemctl start telegram-bot

# Проверяем логи
sudo journalctl -u telegram-bot -f
```

---

## 🐛 Решение проблем

### Проблема: Бот не запускается

```bash
# Проверьте логи
sudo journalctl -u telegram-bot -n 50

# Проверьте токен
cat ~/telegram-bot/.env

# Проверьте права доступа
ls -la ~/telegram-bot/.env

# Проверьте Python
cd ~/telegram-bot
source venv/bin/activate
python --version
python main.py  # запуск вручную для отладки
```

### Проблема: Ошибки БД

```bash
# Проверьте права на файл БД
ls -la ~/telegram-bot/bot.db

# Проверьте место на диске
df -h

# Попробуйте пересоздать БД (ВНИМАНИЕ: удалит все данные!)
cd ~/telegram-bot
rm bot.db
python migrate_db.py
python migrate_auth.py
python migrate_disclaimer.py
```

### Проблема: Бот не отвечает

```bash
# Проверьте, что бот запущен
sudo systemctl status telegram-bot

# Проверьте интернет-соединение
ping 8.8.8.8

# Проверьте логи на ошибки
sudo journalctl -u telegram-bot -f
```

### Проблема: Недостаточно памяти

```bash
# Проверьте использование памяти
free -h

# Если мало памяти, можно:
# 1. Увеличить swap
sudo fallocate -l 1G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# 2. Или обновить сервер до большего тарифа
```

---

## 📊 Рекомендации по оптимизации

### 1. Использование Docker (опционально)

Если хотите использовать Docker, см. файл `DEPLOY.md` в проекте.

### 2. Настройка мониторинга

```bash
# Установка мониторинга (опционально)
# Можно использовать простой скрипт для проверки здоровья бота
```

### 3. Ограничение ресурсов

В файле сервиса уже есть ограничения:
- `MemoryLimit=512M` - максимум памяти
- `CPUQuota=50%` - максимум CPU

Можно изменить под ваши нужды.

---

## ✅ Чек-лист готовности

Перед тем как считать деплой завершенным, проверьте:

- [ ] Сервер создан и настроен
- [ ] Пользователь создан (не root)
- [ ] Firewall настроен
- [ ] Проект загружен на сервер
- [ ] Виртуальное окружение создано
- [ ] Зависимости установлены
- [ ] Файл .env создан с правильным токеном
- [ ] Права на .env установлены (600)
- [ ] Миграции выполнены
- [ ] БД создана
- [ ] Тестовый запуск прошел успешно
- [ ] Systemd сервис создан и активирован
- [ ] Бот запускается автоматически
- [ ] Логи доступны через journalctl
- [ ] Бэкап настроен
- [ ] Бот отвечает в Telegram

---

## 📞 Полезные команды (шпаргалка)

```bash
# Управление сервисом
sudo systemctl start telegram-bot      # Запуск
sudo systemctl stop telegram-bot       # Остановка
sudo systemctl restart telegram-bot     # Перезапуск
sudo systemctl status telegram-bot      # Статус

# Логи
sudo journalctl -u telegram-bot -f     # Следить за логами
sudo journalctl -u telegram-bot -n 100 # Последние 100 строк

# Бэкап
~/backup-bot.sh                         # Ручной бэкап

# Обновление
cd ~/telegram-bot
sudo systemctl stop telegram-bot
git pull  # или загрузите новые файлы
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl start telegram-bot

# Проверка
htop                                     # Использование ресурсов
df -h                                    # Использование диска
free -h                                  # Использование памяти
```

---

## 🎉 Готово!

Ваш бот должен работать на сервере. Если возникнут проблемы, проверьте логи и следуйте разделу "Решение проблем".

**Удачного деплоя!** 🚀

