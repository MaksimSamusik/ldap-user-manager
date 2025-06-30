# LDAPNotify System

Система автоматических уведомлений с интеграцией LDAP

![Django](https://img.shields.io/badge/Django-3.2-green)
![Docker](https://img.shields.io/badge/Docker-✓-blue)


## 📌 Оглавление
1. [Особенности](#-особенности)
2. [Требования](#-требования)
3. [Быстрый старт](#-быстрый-старт)
4. [Настройка конфигурации](#-настройка-конфигурации)
5. [Развертывание](#-развертывание)

## 🌟 Особенности
- Автоматическая отправка email-уведомлений по расписанию
- Интеграция с LDAP для аутентификации
- Конфигурация через JSON-файл
- Готовые Docker-образы для продакшена

## ⚙️ Требования
- Docker 20.10+
- Docker Compose 1.29+
- Python 3.10+ (для локальной разработки)

## 🚀 Быстрый старт
```bash
# 1. Установка Python
python --version  # Проверка версии
# Если нет Python: https://www.python.org/downloads/

# 2. Создание виртуального окружения
# Переходим в папку проекта (если ещё не там)
cd your_project_name  

# Создаём виртуальное окружение (venv)
python -m venv venv  

# Активируем его:  
# Linux/macOS:
source venv/bin/activate  

# Windows:
.\venv\Scripts\activate  

# 3. Клонирование репозитория
git clone https://github.com/yourproject/ldapnotify.git
cd LDAPNotify/LDAPNotify

# 4. Установка зависимостей
pip install -r requirements.txt
```
## Настройка конфигурации
Создайте файл .env и укажите нужные данные 
### Настройки LDAP
| Переменная                  | Описание                                                                 | Пример значения               | Код для Django (`settings.py`)                                                                 |
|-----------------------------|--------------------------------------------------------------------------|-------------------------------|------------------------------------------------------------------------------------------------|
| `LDAP_SERVER`              | Адрес LDAP-сервера с протоколом                                         | `ldaps://dc1.example.com`     | `AUTH_LDAP_SERVER_URI = os.getenv('LDAP_SERVER')`                                             |
| `LDAP_PORT`                | Порт для подключения к LDAP                                             | `636`                         | `AUTH_LDAP_PORT = int(os.getenv('LDAP_PORT', 636))`                                          |
| `LDAP_DOMAIN`              | Домен для формирования логина (user@domain)                             | `example.com`                 | `LDAP_DOMAIN = os.getenv('LDAP_DOMAIN')`                                                     |
| `AUTH_LDAP_BIND_DN`        | Учетные данные для привязки к LDAP                                      | `EXAMPLE\\Administrator`      | `AUTH_LDAP_BIND_DN = os.getenv('AUTH_LDAP_BIND_DN')`                                         |
| `AUTH_LDAP_BIND_PASSWORD`  | Пароль для привязки к LDAP                                              | `P@ssw0rd123!`                | `AUTH_LDAP_BIND_PASSWORD = os.getenv('AUTH_LDAP_BIND_PASSWORD')`                              |
| `AUTH_LDAP_BASE_DN`        | Базовый DN для поиска пользователей                                     | `DC=example,DC=com`           | `AUTH_LDAP_BASE_DN = os.getenv('AUTH_LDAP_BASE_DN')`                                         |
| `AUTH_LDAP_GROUP_TYPE`     | Тип групп LDAP (ActiveDirectory)                                        | `ActiveDirectoryGroupType()`  | `from django_auth_ldap.config import ActiveDirectoryGroupType`<br>`AUTH_LDAP_GROUP_TYPE = ActiveDirectoryGroupType()` |
| `AUTH_LDAP_ALWAYS_UPDATE_USER` | Обновлять данные пользователя при каждом входе                      | `True`                        | `AUTH_LDAP_ALWAYS_UPDATE_USER = True`                                                        |
| `AUTH_LDAP_FIND_GROUP_PERMS` | Искать разрешения в группах LDAP                                     | `True`                        | `AUTH_LDAP_FIND_GROUP_PERMS = True`                                                          |

### Настройки Django
| Переменная          | Описание                                     | Пример значения                          | Код для Django (`settings.py`)               |
|---------------------|----------------------------------------------|------------------------------------------|---------------------------------------------|
| `SECRET_KEY`       | Секретный ключ для подписи данных           | `django-insecure-m^^s@e+%_ikct-&c-...`  | `SECRET_KEY = os.getenv('SECRET_KEY')`      |
| `DEBUG`           | Режим отладки (1 - вкл, 0 - выкл)          | `0`                                      | `DEBUG = bool(int(os.getenv('DEBUG', 0)))`  |
| `ALLOWED_HOSTS`   | Разрешенные хосты (через запятую)           | `localhost,127.0.0.1`                   | `ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS').split(',')` |

### Настройки SMTP
| Переменная            | Описание                          | Пример значения     | Код для Django (`settings.py`)                     |
|-----------------------|-----------------------------------|---------------------|--------------------------------------------------|
| `EMAIL_HOST`         | SMTP-сервер                      | `smtp.yandex.ru`    | `EMAIL_HOST = os.getenv('EMAIL_HOST')`          |
| `EMAIL_PORT`         | Порт SMTP                        | `587`               | `EMAIL_PORT = int(os.getenv('EMAIL_PORT', 587))`|
| `EMAIL_USE_TLS`      | Использовать TLS                 | `True`              | `EMAIL_USE_TLS = bool(int(os.getenv('EMAIL_USE_TLS', 1)))` |
| `EMAIL_HOST_USER`    | Логин для SMTP                   | `example@yandex.ru` | `EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')`|
| `EMAIL_HOST_PASSWORD`| Пароль для SMTP                  | `password`          | `EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')` |

### Конфигурация уведомлений (config.json)
| Переменная                  | Описание                                                                                     |
|-----------------------------|----------------------------------------------------------------------------------------------|
| `notification_days`             | Промежутки проверки пользователей для фоновой отправки уведомления                           |
| `messages`                | Содержимое сообщения для фоновой отправки                                                    |
| `manual_notification_settings`              | Содержимое сообщения отправленного через веб-интерфейс                                       |
| `admin_notifications`        | Содержимое отчета для администраторов                                                        |
| `admin_notification_threshold`        | Фильтрация пользователей для отправки отчета админам (количество дней до истечения аккаунта) |
| `admin_notification_settings`        | Содержимое письма для администраторов                                                        |
| `admin_notification_threshold`        | Время нотификации                                                                            |

## Развертывание

```bash
# Сборка докер-контейнера
docker build -t имя_образа .

# Запуск docker-compose
docker-compose up -d
```
