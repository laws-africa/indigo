import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('indigo_api', '0058_amendmentinstruction_amended_document_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProvisionTaxonomyTopic',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('provision_eid', models.CharField(max_length=2048, verbose_name='provision eid')),
                ('taxonomy_topic', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                                                     related_name='provision_taxonomy_topics',
                                                     to='indigo_api.taxonomytopic',
                                                     verbose_name='taxonomy topic')),
                ('work', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                                          related_name='provision_taxonomy_topics',
                                          to='indigo_api.work',
                                          verbose_name='work')),
            ],
            options={
                'verbose_name': 'provision taxonomy topic',
                'verbose_name_plural': 'provision taxonomy topics',
            },
        ),
        migrations.AlterUniqueTogether(
            name='provisiontaxonomytopic',
            unique_together={('work', 'taxonomy_topic', 'provision_eid')},
        ),
    ]
