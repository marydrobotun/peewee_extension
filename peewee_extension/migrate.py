# -*- coding: utf-8 -*-
"""console tool, compares database with python models"""
import datetime
import importlib
import sys
from os import chdir
from pathlib import Path


from peewee_extension.migration import models_migration_table
from peewee_extension.migration.models_migration_table import Migration
from peewee_extension.utils import MigrateConfigurator
from playhouse.db_url import connect
from termcolor import colored, cprint


def do_migrate(migration_module, db):
    # put' k papke s migraciey ili nazvanie modulya .py c migracieydb
    try:
        migration = importlib.import_module(migration_module)
    except ImportError as err:
        raise Exception(err)
    if not hasattr(migration, 'apply'):
        raise Exception('Migration must contain apply()')
    if not hasattr(migration, 'db'):
        raise Exception('Migration must contain db attr')
    migration.db.initialize(db)
    migration.apply()

    Migration.create(
        name=migration_module, is_applied=True,
        created_at=datetime.datetime.now(),
        applied_at=datetime.datetime.now(),
    )


def main():
    sys.path.append('')
    # db_url i path to migrations peredat params
    conf = MigrateConfigurator()
    conf.run()
    # connect to database
    db = connect(conf.get_dburl())
    models_migration_table.db.initialize(db)
    if 'pe_migrations' not in db.get_tables():
        db.create_tables([Migration])
    migrations_path = Path(conf.get_filepath())
    unapplied_migrations = {f.name[:-3] for f in migrations_path.iterdir() if f.is_file()}
    # TODO: testing протестировать применение нескольких миграций из папки
    print('Migrations from directory:', unapplied_migrations)
    migrations_from_db = {
        migration_name.name for migration_name in Migration.select(Migration.name)
    }
    if migrations_from_db:
        print('Migrations from db: ', migrations_from_db)
        unapplied_migrations -= set(migrations_from_db)
    print('to apply: ', unapplied_migrations)
    if conf.options.name:
        unapplied_migrations &= {conf.options.name}
    if not unapplied_migrations:
        cprint('Nothing to do', color='yellow')
        return
    chdir(migrations_path)
    for filename in unapplied_migrations:
        need_apply = True
        if conf.ask_user:
            red_filename = colored(filename, color='red')
            feedback = input(
                f'Migration {red_filename} is not applied, do you want to apply it? [y/N]',
            )
            need_apply = feedback.upper() == 'Y'
        if need_apply:
            do_migrate(filename, db)
            cprint(f'Applied {filename}', color='green')
        else:
            cprint(f'Skipped {filename}', color='yellow')


if __name__ == '__main__':
    main()
