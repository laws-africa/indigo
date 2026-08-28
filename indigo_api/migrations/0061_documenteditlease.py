import uuid

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ('indigo_api', '0060_publicationdocument_start_page'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='DocumentEditLease',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('token', models.UUIDField(default=uuid.uuid4, editable=False, unique=True, verbose_name='token')),
                ('client_id', models.UUIDField(verbose_name='client id')),
                ('document_updated_at', models.DateTimeField(verbose_name='document updated at')),
                ('acquired_at', models.DateTimeField(auto_now_add=True, verbose_name='acquired at')),
                ('renewed_at', models.DateTimeField(auto_now=True, verbose_name='renewed at')),
                ('expires_at', models.DateTimeField(verbose_name='expires at')),
                ('document', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='edit_lease', to='indigo_api.document', verbose_name='document')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='document_edit_leases', to=settings.AUTH_USER_MODEL, verbose_name='user')),
            ],
            options={
                'verbose_name': 'document edit lease',
                'verbose_name_plural': 'document edit leases',
            },
        ),
    ]
