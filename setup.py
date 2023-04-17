import os

from setuptools import setup, find_packages

PREFIX = 'crowdom'

setup_py_dir = os.path.dirname(__file__)
version_module_path = os.path.join(setup_py_dir, 'src', '__version__.py')

about = {}

with open(version_module_path) as f:
    exec(f.read(), about)

with open('README.md') as f:
    readme = f.read()

setup(
    name=about['__title__'],
    package_dir={PREFIX: 'src'},
    packages=['crowdom', *(f'{PREFIX}.{package}' for package in find_packages('src'))],
    version=about['__version__'],
    description='Crowdom',
    long_description=readme,
    long_description_content_type='text/markdown',
    license=about['__license__'],
    author='Oleg Gulyaev',
    author_email='o-gulyaev@yandex-team.ru',
    python_requires='>=3.8.0',
    install_requires=[
        'toloka-kit==1.1.3',
        'crowd-kit==1.0.0',
        'python-dateutil>=2.8.2',
        'beautifulsoup4>=4.8.2',
        'matplotlib>=3.5.0',
        'pylzy>=1.10.1',
        'pure-protobuf>=2.2.2',
        'ipywidgets==7.7.0',
        'seaborn>=0.12.2',
        'plotly>=5.14.0',
    ],
    include_package_data=True,
)
