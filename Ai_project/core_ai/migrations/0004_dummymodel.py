
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core_ai', '0003_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='DummyModel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
        ),
    ]
