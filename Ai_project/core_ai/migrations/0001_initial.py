
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='AnalysisJob',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(default='PENDING', max_length=50)),
                ('started_at', models.DateTimeField(auto_now_add=True)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
                ('celery_task_id', models.CharField(blank=True, max_length=255, null=True)),
            ],
            options={
                'db_table': 'analysis_jobs',
            },
        ),
        migrations.CreateModel(
            name='CodeFile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('filename', models.CharField(max_length=255)),
                ('file_type', models.CharField(blank=True, max_length=50, null=True)),
                ('content', models.TextField()),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
                ('source_project_id', models.CharField(blank=True, max_length=255, null=True)),
            ],
            options={
                'db_table': 'code_files',
            },
        ),
        migrations.CreateModel(
            name='AnalysisResult',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ast_structure', models.JSONField(blank=True, null=True)),
                ('features_extracted', models.JSONField(blank=True, null=True)),
                ('dependencies_graph', models.JSONField(blank=True, null=True)),
                ('semantic_analysis_output', models.JSONField(blank=True, null=True)),
                ('class_diagram_data', models.JSONField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('analysis_job', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core_ai.analysisjob')),
            ],
            options={
                'db_table': 'analysis_results',
            },
        ),
        migrations.AddField(
            model_name='analysisjob',
            name='code_file',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core_ai.codefile'),
        ),
    ]
