# Тестовое задание Яндекс ревьювер DE
## Задание
Используя API [exchangerate.host](https://exchangerate.host/) подготовьте ETL процесс с помощью Airflow на python, для выгрузки данных по валютной паре BTC/USD (Биткоин к доллару), выгружать следует с шагом 3 часа и записывать данные в БД (валютная пара, дата, текущий курс).

В качестве задания со звёздочкой можете учесть вариант заполнения базы историческими данными (API предоставляет специальный endpoint для выгрузки исторических данных).

## Реализация
### Структура проекта
| Файл   | Примечание          | 
|--------|---------------------|
| docker | Докер образы и env  |
| db     | DDL для PG          |
| dags   | Python dags Airflow |
| variables.json   | variables Airflow |

### Архитектура
#### Сервисы
Были развернуты следующие сервисы в докер:

| Сервис   | Порт | Логин | Пароль | 
|--------|---------------------|---------------------|---------------------|
| Airflow (workers, redis) | 8080  |root  |root  |
| postgres     | 5432  |postgres  |postgres  |
| pgadmin   | 5080 |admin@admin.com  |root  |
| portainer   | 9000 | -  |  -  |

#### Хранение в БД
Для хранения информации о котировках был выбрал postgres, что бы не тащить дополнительные зависимости.  Хранение котировок сделано в виде целого числа для нивилирования проблем арифметики дробгных чисел, например:	26959.102564  будет хранится в postgres как 26959102564. 
Схема для хранения описана в скриптах ddl

#### Airflow dags:

| Файл   | Описание          | 
|--------|---------------------|
| exchange_loader.py | Загрузка текущих котировок  |
| exchange_loader_hist.py     | Загрузка исторических котировок  |

Параметеризация exchange_loader_hist сделана через Airflow Variables.

## Запуск
### Сервисы и предварительные настройки
1. Склонируйте содержимое репозитория на сервер
2. `cd docker ` `sudo docker-compose up -d` - должны поднятся все сервисы + примонитороваться volumes в директории запуска `/airflow-data/dags/`
3. `cd docker ` `init_airflow_setup.sh` - первоначальная настройка Airflow
4. Через pgadmin создать таблицу, используя `db\ddl.sql`
5. Импортировать в Airflow Variables `variables.json`
6. Создать Airflow подключения postgress и http по аналогии:
[![img\http.png](img\http.png "img\http.png")](http://img\http.png "img\http.png")
[![img\http.png](img\pg.png "img\http.png")](http://img\pg.png "img\http.png")
1.  Скопировать даги в `/airflow-data/dags/`

### Прогрузка котировок
#### Описание Variables
| Параметр   | Описание          | 
|--------|---------------------|
| base | Базования валюта  |
| symbols     | Целевая валюта (поддерживается только одно значение, нельзя передать несколько через ` ,`)  |
| pg_table    | Таблица в  postgres |
| from_dt     | С какой даты загруждать исторические данные  |
| to_dt     | По какую дату загруждать исторические данные |

#### Прогрузка актуальных данных
Прогрузка актуальных данных происходит раз в 3 часа. 
Критерий успешности - даг выполняется успещно и в таблице появляются данные.
#### Прогрузка исторических данных
Прогрузка исторических данных происходит в ручном режиме. Берется диапазон дат между `from_dt` `to_dt` включительно. Генерируется многопоточная загрузка. Критерий успешности - даг выполняется успещно и в таблице появляются данные.