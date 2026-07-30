import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("indigo_api", "0059_alter_annotation_created_by_user_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="publicationdocument",
            name="start_page",
            field=models.PositiveIntegerField(
                blank=True,
                help_text="The page in the publication document where this work starts.",
                null=True,
                validators=[django.core.validators.MinValueValidator(1)],
                verbose_name="start page",
            ),
        ),
    ]
