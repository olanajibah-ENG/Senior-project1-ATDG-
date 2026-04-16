
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('core_ai', '0002_remove_analysisresult_analysis_job_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='MongoAIExplanation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('analysis_id', models.CharField(blank=True, max_length=255, null=True)),
                ('explanation_type', models.CharField(blank=True, max_length=100, null=True)),
                ('content', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(blank=True, null=True)),
            ],
            options={
                'verbose_name': 'AI Explanation (MongoDB)',
                'verbose_name_plural': 'AI Explanations (MongoDB)',
                'managed': False,
            },
        ),
    ]
