
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core_ai', '0006_mongoaitask_mongoanalysisjob_mongoanalysisresult_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='MongoDocumentationFile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('filename', models.CharField(blank=True, max_length=255, null=True)),
                ('file_type', models.CharField(blank=True, max_length=50, null=True)),
                ('content', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(blank=True, null=True)),
                ('updated_at', models.DateTimeField(blank=True, null=True)),
                ('category', models.CharField(blank=True, max_length=100, null=True)),
                ('tags', models.TextField(blank=True, null=True)),
            ],
            options={
                'verbose_name': 'Documentation File (MongoDB)',
                'verbose_name_plural': 'Documentation Files (MongoDB)',
                'db_table': 'fake_documentation_files',
                'managed': False,
            },
        ),
    ]
