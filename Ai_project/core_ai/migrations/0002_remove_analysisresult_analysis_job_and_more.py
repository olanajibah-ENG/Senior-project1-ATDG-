
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core_ai', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='analysisresult',
            name='analysis_job',
        ),
        migrations.DeleteModel(
            name='AnalysisJob',
        ),
        migrations.DeleteModel(
            name='AnalysisResult',
        ),
        migrations.DeleteModel(
            name='CodeFile',
        ),
    ]
