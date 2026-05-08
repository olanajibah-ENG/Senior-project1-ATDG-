
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core_ai', '0005_delete_dummymodel'),
    ]

    operations = [
        migrations.CreateModel(
            name='MongoAITask',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('task_id', models.CharField(blank=True, max_length=255, null=True)),
                ('analysis_id', models.CharField(blank=True, max_length=255, null=True)),
                ('exp_type', models.CharField(blank=True, max_length=100, null=True)),
                ('status', models.CharField(blank=True, max_length=50, null=True)),
                ('created_at', models.DateTimeField(blank=True, null=True)),
            ],
            options={
                'verbose_name': 'AI Task (MongoDB)',
                'verbose_name_plural': 'AI Tasks (MongoDB)',
                'db_table': 'fake_ai_tasks',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='MongoAnalysisJob',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code_file_id', models.CharField(blank=True, max_length=255, null=True)),
                ('status', models.CharField(blank=True, max_length=50, null=True)),
                ('created_at', models.DateTimeField(blank=True, null=True)),
                ('started_at', models.DateTimeField(blank=True, null=True)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
            ],
            options={
                'verbose_name': 'Analysis Job (MongoDB)',
                'verbose_name_plural': 'Analysis Jobs (MongoDB)',
                'db_table': 'fake_analysis_jobs',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='MongoAnalysisResult',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code_file_id', models.CharField(blank=True, max_length=255, null=True)),
                ('analysis_started_at', models.DateTimeField(blank=True, null=True)),
                ('analysis_completed_at', models.DateTimeField(blank=True, null=True)),
                ('status', models.CharField(blank=True, max_length=50, null=True)),
            ],
            options={
                'verbose_name': 'Analysis Result (MongoDB)',
                'verbose_name_plural': 'Analysis Results (MongoDB)',
                'db_table': 'fake_analysis_results',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='MongoCodeFile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('filename', models.CharField(blank=True, max_length=255, null=True)),
                ('file_type', models.CharField(blank=True, max_length=50, null=True)),
                ('content', models.TextField(blank=True, null=True)),
                ('uploaded_at', models.DateTimeField(blank=True, null=True)),
                ('analysis_status', models.CharField(blank=True, max_length=50, null=True)),
            ],
            options={
                'verbose_name': 'Code File (MongoDB)',
                'verbose_name_plural': 'Code Files (MongoDB)',
                'db_table': 'fake_code_files',
                'managed': False,
            },
        ),
        migrations.AlterModelTable(
            name='mongoaiexplanation',
            table='fake_ai_explanations',
        ),
    ]
