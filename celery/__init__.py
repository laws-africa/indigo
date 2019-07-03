# NOTE: this is a fake celery.py file to pretend to pinax-badges that
# celery is installed.
#
# This is required because django-background-tasks eagerly auto-discovers
# <app>.tasks modules for all apps in INSTALLED_APPS. That includes pinax-badges,
# which tries to 'import celery' in pinax_badges.tasks.py.
#
# Indigo is currently incompatible with celery.

class Task(object):
    pass
