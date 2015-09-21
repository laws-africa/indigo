# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion
from django.conf import settings


def create_editors(apps, schema_editor):
    from indigo_app.models import Editor
    from django.contrib.auth.models import User

    for user in User.objects.all():
        user.editor = Editor()
        user.editor.save()


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('indigo_app', '0006_auto_20150918_1515'),
    ]

    operations = [
        migrations.CreateModel(
            name='Editor',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('country', models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, to='indigo_app.Country', null=True)),
                ('user', models.OneToOneField(to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.RunPython(create_editors, noop),
    ]
