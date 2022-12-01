![example workflow](https://github.com/tinkofoxil/foodgram-project-react/actions/workflows/foodgram_workflow.yml/badge.svg)

Доступ к серверу: http://84.201.154.246/

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
- Перейдите в директорию foodgram-project-react/infra и выполните команды для запуска приложения в контейнерах

    - Собрать и запустить контейнеры:
        ```
        docker-compose up -d --build
        ```
    - Выполнить миграции:
        ```
        docker-compose exec web python manage.py migrate
        ```
    - Создать суперпользователя:
        ```
        docker-compose exec web python manage.py createsuperuser
        ```
    - Собрать статику:
        ```
        docker-compose exec web python manage.py collectstatic --no-input
        ```
    - Загрузить данные в БД:
        ```
        docker-compose exec backend python manage.py load_ingredients
        ```
    - Остановить контейнеры:
        ```
        docker-compose down -v 
        ```
### Запуск проекта на удаленном сервере
- Установите docker на сервер:
    ```
    sudo apt install docker.io
    ```
- Установите docker-compose на сервер:
    ```
    sudo curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    ```
- Отредактируйте файл nginx.conf, вписав в server_name IP сервера
- Скопируйте файлы docker-compose.yml и nginx.conf из репозитория на сервер:
    ```
    scp docker-compose.yml <username>@<host>:/home/<username>/
    scp nginx.conf <username>@<host>:/home/<username>/
    ```

- Создайте файл .env в дериктории infra:

    ```bash
    touch .env
    ```
- Заполнить в настройках репозитория секреты .env

    ```
    DB_ENGINE='django.db.backends.postgresql'
    DB_NAME=
    POSTGRES_USER=
    POSTGRES_PASSWORD=
    DB_HOST=db
    DB_PORT='5432'
    SECRET_KEY=
    ```
- Запустите контейнеры:
    ```bash
    sudo docker-compose up -d
    ```
    ```bash
    sudo docker-compose exec backend python manage.py makemigrations
    ```
    ```bash
    sudo docker-compose exec backend python manage.py migrate --noinput
    ```
    ```bash
    sudo docker-compose exec backend python manage.py createsuperuser
    ```
    ```bash
    sudo docker-compose exec backend python manage.py collectstatic --no-input
    ```

Автор: [Кабачков Герман](https://github.com/tinkofoxil/foodgram-project-react)
