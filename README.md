![example workflow](https://github.com/tinkofoxil/foodgram-project-react/actions/workflows/foodgram_workflow.yml/badge.svg)

# Проект «Foodgram»

### Описание
Проект **Foodgram** собирает **рецепты (Recipes)** пользователей. На этом сайте пользователи могут публиковать свои рецепты, подписываться на публикации других пользователей, добавлять понравившиеся рецепты в список **«Избранное» (Favorites)** и список **«Покупок» (ShoppingCart)**, а также скачивать список продуктов, необходимых для приготовления одного или нескольких выбранных блюд.

Реализован автоматический запуск тестов, обновление образов на Docker Hub, автоматический деплой на сервер при пуше в главную ветку main и при удачном деплое отправка сообщения в телеграмм.

### Стек
- Python
- Django
- REST Api
- PostgreSQL
- nginx
- gunicorn
- Docker

## Запуск проекта

### Начало работы
Клонируйте репозиторий и перейдите в него в командной строке:
```
git clone https://github.com/FedyaevaAS/foodgram-project-react
```
```
cd foodgram-project-react
```
### Запуск проекта локально
- Установите Docker, используя инструкции с официального сайта:
https://www.docker.com/products/docker-desktop/
- Создайте файл .env в директории foodgram-project-react/backend/foodgram/foodgram со следующим содержимым:
    ```
    SECRET_KEY=<секретный ключ проекта django>
    DB_ENGINE=<django.db.backends.postgresql>
    DB_NAME=<имя базы данных postgres>
    POSTGRES_USER=<логин для подключения к базе данных>
    POSTGRES_PASSWORD=<пароль для подключения к базе данных>
    DB_HOST=<название контейнера>
    DB_PORT=<порт для подключения к БД>
    ```