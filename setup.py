from setuptools import setup, find_packages
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the relevant file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

with open(path.join(here, 'VERSION')) as f:
    version = f.read().strip()


setup(
    name='indigo',
    version=version,
    description='A Django framework for publishing legislation using Akoma Ntoso',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url='https://github.com/OpenUpSA/indigo',

    # Author details
    author='OpenUp',
    author_email='greg@openup.org.za',

    # See https://pypi.org/classifiers/
    classifiers=[
        'Development Status :: 4 - Beta',
        'Framework :: Django :: 1.11',
        'Intended Audience :: Legal Industry',
        'License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
    ],

    packages=find_packages(exclude=['docs']),
    include_package_data=True,

    python_requires='~=2.7',
    install_requires=[
        'django==1.11',
        'arrow>=0.5',
        'boto3>=1.7',
        'cobalt>=1.0.0',
        'django-ckeditor>=5.3.1',
        'dj-database-url>=0.3.0',
        'django-allauth>=0.36.0',
        'django-compressor>=2.2',
        'django-cors-headers>1.3.1',
        'django-countries-plus==1.1',  # 1.2 breaks migrations
        'django-filter>=1.0,<2',
        'django-languages-plus==0.1.5',  # 1.x doesn't play with django-countries-plus < 1.2
        'django-pipeline>=1.6.11',
        'django-recaptcha>=1.4.0',
        'django-reversion>=1.10.2,<2',
        'django-sass-processor>=0.6',
        'django-storages>=1.6.6',
        'django-taggit-serializer>=0.1.5',
        'django-taggit>=0.22.0',
        'django-wkhtmltopdf>=2.0.3,<2.1',
        'djangorestframework-xml>=1.3.0',
        'djangorestframework>=3.6.2,<3.7',
        'EbookLib>=0.15',
        'jsonpatch>=1.23',
        'libsass==0.14.2',  # 0.14.3 upwards changes imports for .css
        'lxml>=3.4.1',
        'mammoth>=1.4.4',
        'psycopg2==2.7.3.2',  # 2.7.4 began using psycopg2-binary
        'requests>=2',
        'unicodecsv>=0.14.1',
        'whitenoise<2,>=1.0.6',

        # for indigo_social
        'pillow>=5.2.0',
        'pinax-badges>=2.0.0',
    ],
    extras_require={
        'dev': [
            'nose',
            'flake8',
            'django-nose>=1.4.4',
            'mock>=1.3.0',
        ],
        'test': [
            'nose',
            'flake8',
            'django-nose>=1.4.4',
            'mock>=1.3.0',
            'coveralls',
        ],
    },
)

