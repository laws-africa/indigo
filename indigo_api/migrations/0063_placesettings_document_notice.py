from django.db import migrations, models
from django.utils.translation import gettext_lazy as _


class Migration(migrations.Migration):

    dependencies = [
        ('indigo_api', '0062_documenteditlease_activity_nonce'),
    ]

    operations = [
        migrations.AddField(
            model_name='placesettings',
            name='document_notice',
            field=models.TextField(blank=True, default='', help_text=_("Notice shown on every document in this place"), verbose_name='document notice'),
        ),
    ]
