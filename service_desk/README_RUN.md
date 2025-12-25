# Запуск проекта Service Desk

1) Установите виртуальное окружение и зависимости:
```
python -m venv .venv
source .venv/bin/activate  # Windows: .\.venv\Scripts\activate
pip install -r requirements.txt
```

2) Примените миграции и создайте суперпользователя:
```
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
```

3) Запустите сервер разработки:
```
python manage.py runserver
```

Доступные страницы:
- Публичная форма: http://127.0.0.1:8000/order/new/
- Админка: http://127.0.0.1:8000/admin/
- Вход: http://127.0.0.1:8000/auth/login/
- Диспетчер: http://127.0.0.1:8000/dispatcher/
- Мастер: http://127.0.0.1:8000/master/
# Запуск проекта Service Desk (минимальный пример)

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .\.venv\Scripts\activate
pip install -r requirements.txt

python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser

python manage.py runserver
```

Открыть:
- Публичная форма: http://127.0.0.1:8000/order/new/
- Админка: http://127.0.0.1:8000/admin/
- Вход: http://127.0.0.1:8000/auth/login/
- Диспетчер: http://127.0.0.1:8000/dispatcher/
- Мастер: http://127.0.0.1:8000/master/

