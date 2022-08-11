# -*- coding: utf-8 -*-
import os
from pathlib import Path

import setuptools

# allow setup.py to be run from any path
BASE_PATH = Path(__file__).parent
os.chdir(BASE_PATH)

README = open(BASE_PATH / 'README.md').read()

with open(BASE_PATH / 'requirements.txt') as ff:
    install_requires = [line for line in ff.read().splitlines() if len(line) > 0]


setuptools.setup(
    name='peewee_extension',
    version='1.0.28',
    include_package_data=True,
    package_data = {'peewee_extension.templates': ['*']},
    packages=setuptools.find_packages(exclude=('tests*',)),
    url='http://gitlab.web-tech.moex.com/harbour/peewee_mysql_extension',
    license='',
    author='Mariya Drobotun',
    author_email='Mariya.Drobotun@moex.com',
    description='Peewee extension for MySQL',
    long_description=README,
    long_description_content_type='text/markdown',
    # if error Unknown distribution option: 'long_description_content_type'
    # see https://dustingram.com/articles/2018/03/16/markdown-descriptions-on-pypi/
    entry_points={
        'console_scripts': [
            'create_migration = peewee_extension.create_migration:main',
            'migrate = peewee_extension.migrate:main',
            'inspectdb = peewee_extension.inspect_db:main',
            'comparedb = peewee_extension.compare_db:main',
        ],
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.6',
    ],
    python_requires='>=3.6',
    install_requires=install_requires,
)
