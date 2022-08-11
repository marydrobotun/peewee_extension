# **Peewee-MySQL-Extension**
## Пакет для работы с MySQL через peewee


### Основной функционал

- Расширенная система типов, поддержка типов MySQL, которые отсутствуют в оригинальной peewee
- Генерация файлов моделей по БД с использованием расширенной системы типов 
- Возможность сравнения базы данных и файла моделей
- Генерация скрипта миграции peewee, который может быть использован для приведения схемы БД к схеме файла с моделями

## Установка
```sh
pip install peewee-mysql-extension
```
 

## Генерация моделей
Пакет позволяет генерировать файл моделей ORM peewee с использованием расширенной системы типов

**Пример использования:**
```sh
inspectdb -c path_to_your_config_file
```
**path_to_your_config_file** - путь к файлу конфигурации. Может быть представлени в виде yml, ini, json. Должен содержать [db_url - строку коннекта для подключения к базе данных](http://docs.peewee-orm.com/en/latest/peewee/playhouse.html#db-url), для которой требуется создать модели.
Пример содержания файла конфигурации в формате yml:
*config.yml*
```yml
db_url: mysql://root:rasswd@localhost:3306/test_db
```
Начиная с версии **0.1.1**, возможно напрямую передать строку коннекта, без использования файла конфигурации:

```sh
inspectdb -d mysql://root:rasswd@localhost:3306/test_db
```

Для вывода справочной информации о параметрах доступна команда:

```sh
migrate -h
```


## Создание миграции
Пакет позволяет генерировать скрипт миграции для приведения схемы БД к виду схемы файла с моделями

**Пример использования:**
```sh
migrate -c path_to_your_config_file
```
**path_to_your_config_file** - путь к файлу конфигурации. Может быть представлени в виде yml, ini, json. Должен содержать следующие обязательные параметры:
- **db_url** - [строку коннекта для подключения к базе данных](http://docs.peewee-orm.com/en/latest/peewee/playhouse.html#db-url), которую требуется сравнить с файлом моделей
- **models** - путь к файлу моделей, с которым нужно сравнить целевую БД
- **filepath** - путь к папке, куда требуется сохранить сгенерированный файл


Пример содержания файла конфигурации в формате yml:

*config.yml*
```yml
db_url: mysql://root:rasswd@localhost:3306/test_db
models: models.testdb
filepath: 'generated/'
```
Начиная с версии **0.1.1**, возможно напрямую передать параметры, без использования файла конфигурации:

```sh
migrate -d mysql://root:rasswd@localhost:3306/test_db -p generated/ -m models.testdb
```

Для вывода справочной информации о параметрах доступна команда:

```sh
migrate -h
```

Пример сгенерированного скрипта миграции:

*20210804114259_testdb_fields.py*

```python
from playhouse.migrate import MySQLMigrator, migrate
from peewee import CharField

from playhouse.db_url import connect


db_url = 'mysql://root:rasswd@localhost:3306/test_db'
my_db = connect(db_url)
migrator = MySQLMigrator(my_db)


migrate(
    migrator.add_column("fields", "new_column", CharField(max_length=63, null=True)),
)
```