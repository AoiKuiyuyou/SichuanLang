# coding: utf-8
from __future__ import absolute_import

from setuptools import find_packages
from setuptools import setup


setup(
    name='SichuanLang',

    version='0.1.0',

    description=(
        'Sichuan programming language.'
    ),

    long_description="""`Documentation on Github
<https://github.com/AoiKuiyuyou/SichuanLang>`_""",

    url='https://github.com/AoiKuiyuyou/SichuanLang',

    author='Aoi.Kuiyuyou',

    author_email='aoi.kuiyuyou@gmail.com',

    license='MIT',

    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent ',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ],

    keywords=(
        'sichuan programming language'
    ),

    package_dir={'': 'src'},

    packages=find_packages('src'),

    package_data={
        'sichuanlang': [
            'demo/*',
        ],
    },

    entry_points={
        'console_scripts': [
            'sichuanlang=sichuanlang.__main__:main',
        ],
    },
)
