from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core_upm', '0008_merge_20260326_0529'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='project',
            index=models.Index(
                fields=['user', '-creation_date'],
                name='project_user_date_idx'
            ),
        ),
    ]