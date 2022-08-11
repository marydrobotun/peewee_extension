# -*- coding: utf-8 -*-
"""console tool, compares database with python models"""
import sys

from peewee_extension.migration.generator import MigrationGenerator
from peewee_extension.utils import CreateMigrationConfigurator
from termcolor import colored


def do_create(
        db_url: str, models: str, migrations_path: str,
        migration_name: str = None, make_empty_migration: bool = False,
        only_tables: list = None,
):
    generator = MigrationGenerator(
        db_url=db_url,
        models=models,
        make_empty_migration=make_empty_migration,
    )
    generator.generate(only_tables=only_tables)
    filename = generator.write_in_file(
        migrations_path=migrations_path,
        migration_name=migration_name,
    )
    print('Wrote', colored(filename, color='red'))


def main():
    sys.path.append('')
    configurator = CreateMigrationConfigurator()
    configurator.run()
    do_create(
        configurator.get_dburl(),
        configurator.get_models(),
        configurator.get_filepath(),
        configurator.migration_name,
        configurator.is_empty_migration(),
        only_tables=configurator.only_tables,
    )


if __name__ == '__main__':
    main()
