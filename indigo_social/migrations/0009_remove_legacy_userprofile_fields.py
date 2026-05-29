from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('indigo_social', '0008_badgeaward'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='userprofile',
            name='areas_of_law',
        ),
        migrations.RemoveField(
            model_name='userprofile',
            name='bio',
        ),
        migrations.RemoveField(
            model_name='userprofile',
            name='linkedin_profile',
        ),
        migrations.RemoveField(
            model_name='userprofile',
            name='organisations',
        ),
        migrations.RemoveField(
            model_name='userprofile',
            name='qualifications',
        ),
        migrations.RemoveField(
            model_name='userprofile',
            name='skills',
        ),
        migrations.RemoveField(
            model_name='userprofile',
            name='specialisations',
        ),
        migrations.RemoveField(
            model_name='userprofile',
            name='twitter_username',
        ),
    ]
