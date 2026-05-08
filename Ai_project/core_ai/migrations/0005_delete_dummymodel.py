
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core_ai', '0004_dummymodel'),
    ]

    operations = [
        migrations.DeleteModel(
            name='DummyModel',
        ),
    ]
