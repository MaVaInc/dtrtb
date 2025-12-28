# 🚀 Как запушить изменения с ПК на сервер

## 📋 Быстрая инструкция

### Шаг 1: Закоммитить и запушить изменения на GitHub

На вашем ПК (Windows):

```powershell
# 1. Проверить статус изменений
git status

# 2. Добавить измененные файлы
git add handlers/auth.py middleware/auth.py

# Или добавить все изменения:
git add .

# 3. Создать коммит с описанием
git commit -m "Исправлена обработка команды /start и добавлено логирование"

# 4. Отправить на GitHub
git push
```

**Если запросит авторизацию:**
- Введите ваш GitHub username
- Введите Personal Access Token (не пароль!)
  - Создать токен: https://github.com/settings/tokens
  - Нажмите "Generate new token (classic)"
  - Выберите scope: `repo`
  - Скопируйте токен и используйте его как пароль

---

### Шаг 2: Получить изменения на сервере

Подключитесь к серверу через SSH:

```bash
# Подключение к серверу
ssh botuser@ваш_ip_сервера

# Перейдите в директорию проекта
cd ~/telegram-bot
# или
cd /home/botuser/telegram-bot

# Получить последние изменения с GitHub
git pull

# Проверить, что изменения получены
git log --oneline -5
```

---

### Шаг 3: Перезапустить бота на сервере

```bash
# Остановить бота (если запущен через systemd)
sudo systemctl stop telegram-bot

# Или если запущен вручную, нажмите Ctrl+C в терминале

# Запустить бота заново
sudo systemctl start telegram-bot

# Проверить статус
sudo systemctl status telegram-bot

# Посмотреть логи
sudo journalctl -u telegram-bot -f
```

---

## 🔄 Полный workflow (от ПК до сервера)

### На вашем ПК:

```powershell
# 1. Проверить, что изменилось
git status

# 2. Добавить изменения
git add .

# 3. Закоммитить
git commit -m "Описание ваших изменений"

# 4. Отправить на GitHub
git push
```

### На сервере:

```bash
# 1. Подключиться к серверу
ssh botuser@ваш_ip

# 2. Перейти в директорию проекта
cd ~/telegram-bot

# 3. Получить изменения
git pull

# 4. Установить новые зависимости (если requirements.txt изменился)
source venv/bin/activate  # Активировать виртуальное окружение
pip install -r requirements.txt

# 5. Выполнить миграции БД (если были изменения в моделях)
python migrate_db.py
python migrate_auth.py
python migrate_disclaimer.py

# 6. Перезапустить бота
sudo systemctl restart telegram-bot

# 7. Проверить, что бот работает
sudo systemctl status telegram-bot
```

---

## 🎯 Автоматический деплой (опционально)

### Вариант 1: Скрипт для автоматического деплоя

Создайте файл `deploy.sh` на сервере:

```bash
#!/bin/bash
# Файл: ~/telegram-bot/deploy.sh

cd ~/telegram-bot
git pull
source venv/bin/activate
pip install -r requirements.txt --quiet
sudo systemctl restart telegram-bot
echo "✅ Деплой завершен!"
```

Сделайте его исполняемым:

```bash
chmod +x ~/telegram-bot/deploy.sh
```

Теперь на сервере можно просто выполнить:

```bash
~/telegram-bot/deploy.sh
```

### Вариант 2: GitHub Actions (продвинутый вариант)

Создайте файл `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Server

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to server
        uses: appleboy/ssh-action@master
        with:
          host: ${{ secrets.SERVER_HOST }}
          username: ${{ secrets.SERVER_USER }}
          key: ${{ secrets.SSH_PRIVATE_KEY }}
          script: |
            cd ~/telegram-bot
            git pull
            source venv/bin/activate
            pip install -r requirements.txt
            sudo systemctl restart telegram-bot
```

**Настройка секретов на GitHub:**
1. Откройте репозиторий на GitHub
2. Settings → Secrets and variables → Actions
3. Добавьте:
   - `SERVER_HOST` - IP адрес сервера
   - `SERVER_USER` - имя пользователя (например, `botuser`)
   - `SSH_PRIVATE_KEY` - приватный SSH ключ для доступа к серверу

Теперь при каждом `git push` изменения автоматически применятся на сервере!

---

## 🔍 Проверка изменений

### На ПК (перед push):

```powershell
# Посмотреть, что изменилось
git diff

# Посмотреть историю коммитов
git log --oneline -10
```

### На сервере (после pull):

```bash
# Посмотреть последние коммиты
git log --oneline -5

# Посмотреть изменения в конкретном файле
git diff HEAD~1 handlers/auth.py

# Проверить статус
git status
```

---

## ⚠️ Важные моменты

### 1. Не коммитьте секретные файлы

Убедитесь, что `.env` и `bot.db` в `.gitignore`:

```powershell
# Проверить .gitignore
cat .gitignore

# Должны быть строки:
# .env
# bot.db
```

### 2. Не забывайте про миграции БД

Если изменили модели в `database/models.py`, на сервере нужно выполнить миграции:

```bash
python migrate_db.py
python migrate_auth.py
python migrate_disclaimer.py
```

### 3. Проверяйте логи после деплоя

```bash
# На сервере
sudo journalctl -u telegram-bot -n 50
# или
tail -f /var/log/telegram-bot.log
```

### 4. Делайте бэкап перед обновлением

```bash
# На сервере
cp bot.db bot.db.backup
cp .env .env.backup
```

---

## 🆘 Решение проблем

### Ошибка: "Your branch is ahead of 'origin/main'"

```powershell
# Просто запушите изменения
git push
```

### Ошибка: "Updates were rejected"

```powershell
# Получите последние изменения с GitHub
git pull

# Разрешите конфликты (если есть)
# Затем снова
git push
```

### Ошибка на сервере: "Permission denied"

```bash
# Проверьте права доступа
ls -la ~/telegram-bot

# Если нужно, исправьте владельца
sudo chown -R botuser:botuser ~/telegram-bot
```

### Бот не запускается после обновления

```bash
# Проверьте логи
sudo journalctl -u telegram-bot -n 100

# Проверьте синтаксис Python
python -m py_compile main.py

# Проверьте зависимости
source venv/bin/activate
pip check
```

---

## 📚 Полезные команды

### На ПК:

```powershell
# Посмотреть все изменения
git status

# Добавить все изменения
git add .

# Закоммитить
git commit -m "Описание"

# Отправить на GitHub
git push

# Получить изменения с GitHub
git pull
```

### На сервере:

```bash
# Получить изменения
git pull

# Посмотреть историю
git log --oneline -10

# Откатить изменения (если что-то пошло не так)
git reset --hard HEAD~1

# Перезапустить бота
sudo systemctl restart telegram-bot
```

---

## ✅ Чеклист перед деплоем

- [ ] Изменения протестированы локально
- [ ] Все файлы добавлены в git (`git add .`)
- [ ] Создан коммит с понятным описанием
- [ ] Изменения отправлены на GitHub (`git push`)
- [ ] На сервере получены изменения (`git pull`)
- [ ] Установлены новые зависимости (если нужно)
- [ ] Выполнены миграции БД (если нужно)
- [ ] Бот перезапущен
- [ ] Проверены логи - бот работает

---

**Готово!** Теперь вы знаете, как деплоить изменения с ПК на сервер! 🚀

