
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core_ai', '0007_mongodocumentationfile'),
    ]

    operations = [
        migrations.CreateModel(
            name='MongoGeneratedFile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('filename', models.CharField(blank=True, max_length=255, null=True)),
                ('file_type', models.CharField(blank=True, max_length=50, null=True)),
                ('explanation_id', models.CharField(blank=True, max_length=255, null=True)),
                ('file_size', models.IntegerField(blank=True, null=True)),
                ('created_at', models.DateTimeField(blank=True, null=True)),
                ('downloaded_count', models.IntegerField(blank=True, null=True)),
            ],
            options={
                'verbose_name': 'Generated File (MongoDB)',
                'verbose_name_plural': 'Generated Files (MongoDB)',
                'db_table': 'fake_generated_files',
                'managed': False,
            },
        ),
    ]
