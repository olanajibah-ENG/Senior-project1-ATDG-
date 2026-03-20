from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core_upm', '0006_alter_folder_repo'),
    ]

    operations = [
        migrations.AddField(
            model_name='repository',
            name='repo_url',
            field=models.URLField(blank=True, max_length=500, null=True, verbose_name='GitHub Repo URL'),
        ),
        migrations.AddField(
            model_name='repository',
            name='branch',
            field=models.CharField(blank=True, default='main', max_length=255, null=True, verbose_name='Branch'),
        ),
        migrations.AddField(
            model_name='repository',
            name='last_commit_sha',
            field=models.CharField(blank=True, max_length=40, null=True, verbose_name='Last Commit SHA'),
        ),
    ]