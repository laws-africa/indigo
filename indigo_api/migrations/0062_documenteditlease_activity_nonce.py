from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('indigo_api', '0061_documenteditlease'),
    ]

    operations = [
        migrations.AddField(
            model_name='documenteditlease',
            name='activity_nonce',
            field=models.CharField(blank=True, max_length=10, null=True, verbose_name='activity nonce'),
        ),
    ]
