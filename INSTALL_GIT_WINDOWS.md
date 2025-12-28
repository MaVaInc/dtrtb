# 📥 Установка Git на Windows

## 🎯 Способ 1: Установка через установщик (рекомендуется)

### Шаг 1: Скачивание установщика

1. Откройте браузер и перейдите на: https://git-scm.com/download/win
2. Скачайте установщик (автоматически выберется 64-bit версия)
3. Или скачайте напрямую: https://github.com/git-for-windows/git/releases/latest
   - Найдите файл `Git-x.x.x-64-bit.exe` (последняя версия)

### Шаг 2: Установка

1. Запустите скачанный файл `Git-x.x.x-64-bit.exe`
2. Нажмите **"Next"** на всех экранах с настройками по умолчанию
3. **Важные настройки:**
   - **Editor**: Выберите ваш любимый редактор (VS Code, Notepad++, или оставьте Vim)
   - **Default branch name**: `main` (рекомендуется)
   - **PATH environment**: Оставьте "Git from the command line and also from 3rd-party software"
   - **Line ending conversions**: Оставьте "Checkout Windows-style, commit Unix-style line endings"
4. Нажмите **"Install"**
5. Дождитесь завершения установки
6. Нажмите **"Finish"**

### Шаг 3: Проверка установки

Откройте **новый** PowerShell или Command Prompt и выполните:

```powershell
git --version
```

Должно вывести что-то вроде: `git version 2.42.0.windows.2`

---

## 🚀 Способ 2: Установка через winget (Windows 11/10 с обновлениями)

### Шаг 1: Проверка winget

```powershell
winget --version
```

Если команда не найдена, используйте Способ 1.

### Шаг 2: Установка Git

```powershell
winget install --id Git.Git -e --source winget
```

### Шаг 3: Проверка

Закройте и откройте PowerShell заново, затем:

```powershell
git --version
```

---

## 🎨 Способ 3: Установка через Chocolatey (если установлен)

### Шаг 1: Проверка Chocolatey

```powershell
choco --version
```

Если не установлен, используйте Способ 1.

### Шаг 2: Установка Git

```powershell
choco install git -y
```

### Шаг 3: Проверка

Закройте и откройте PowerShell заново, затем:

```powershell
git --version
```

---

## ⚙️ Настройка Git после установки

### Шаг 1: Настройка имени и email

Откройте PowerShell и выполните:

```powershell
# Установите ваше имя
git config --global user.name "Ваше Имя"

# Установите ваш email (должен совпадать с GitHub)
git config --global user.email "ваш_email@example.com"

# Проверьте настройки
git config --list
```

### Шаг 2: Настройка редактора (опционально)

Если хотите использовать VS Code:

```powershell
git config --global core.editor "code --wait"
```

Или Notepad++:

```powershell
git config --global core.editor "'C:/Program Files/Notepad++/notepad++.exe' -multiInst -notabbar -nosession -noPlugin"
```

### Шаг 3: Настройка окончаний строк (уже настроено при установке)

```powershell
# Проверьте текущую настройку
git config --global core.autocrlf

# Должно быть: true (для Windows)
```

---

## 🔧 Решение проблем

### Проблема: "git не распознан" после установки

**Решение:**

1. **Закройте и откройте PowerShell/Command Prompt заново**
   - Git добавляется в PATH, но текущая сессия не видит изменения

2. **Проверьте PATH вручную:**
   ```powershell
   $env:PATH -split ';' | Select-String git
   ```
   
   Должна быть строка с `C:\Program Files\Git\cmd` или похожая

3. **Если Git не в PATH:**
   - Откройте "Параметры системы" → "Переменные среды"
   - В "Системные переменные" найдите `Path`
   - Добавьте: `C:\Program Files\Git\cmd`
   - Перезапустите PowerShell

4. **Или используйте Git Bash:**
   - Найдите "Git Bash" в меню Пуск
   - Запустите его
   - Git Bash всегда работает с Git

### Проблема: Нужно переустановить Git

```powershell
# Удалите через winget (если устанавливали так)
winget uninstall Git.Git

# Или через Панель управления:
# Панель управления → Программы → Удаление программы → Git → Удалить
```

Затем установите заново через Способ 1.

### Проблема: Конфликт версий Git

Если установлено несколько версий Git:

```powershell
# Проверьте, какая версия используется
where.exe git

# Должен показать путь к Git
# Если показывает несколько путей, удалите старые версии
```

---

## ✅ Проверка готовности

После установки выполните:

```powershell
# Проверка версии
git --version

# Проверка конфигурации
git config --list

# Проверка, что Git работает
git help
```

Все команды должны работать без ошибок.

---

## 🎯 Следующие шаги

После установки Git:

1. **Настройте Git** (имя и email) - см. выше
2. **Следуйте мануалу** `GITHUB_DEPLOY.md` для выкладывания проекта на GitHub
3. **Или используйте GitHub Desktop** (GUI для Git): https://desktop.github.com/

---

## 📚 Полезные ссылки

- [Официальный сайт Git](https://git-scm.com/)
- [Документация Git для Windows](https://git-scm.com/download/win)
- [GitHub Desktop](https://desktop.github.com/) - графический интерфейс
- [Обучающие материалы Git](https://git-scm.com/doc)

---

## 💡 Совет

После установки Git рекомендуется установить **GitHub Desktop** для удобной работы с репозиториями через графический интерфейс. Это особенно удобно для начинающих.

**Удачной установки!** 🚀


