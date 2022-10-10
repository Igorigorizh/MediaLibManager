#!/usr/bin/env python
from setuptools import setup

setup(
    name='MediaLibManager',
    version='2.9.10',
    description='Music metadata managing, navigation and playing Service',
    packages=['medialib'],
    url='https://github.com/Igorigorizh/MediaLibManager.git',
    install_requires=[
        'mutagen',
        'importlib-metadata; python_version == "3.10"',
    ],
)