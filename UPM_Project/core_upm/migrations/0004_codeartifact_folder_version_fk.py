"""
Migration: إضافة folder_id و version_id إلى CodeArtifact

الخطأ المُصلَح:
    الموديل يحتوي على:
        folder = ForeignKey(Folder, ...)
        version = ForeignKey(Version, ...)
    لكن كانت هاتين الـ FK غائبتين تماماً عن جميع الـ migrations السابقة،
    مما يعني أن العمودين غير موجودَين في قاعدة البيانات الفعلية.
    أي محاولة لـ create/filter على CodeArtifact ستؤدي إلى:
        django.db.utils.OperationalError: no such column: core_upm_codeartifact.folder_id
        django.db.utils.OperationalError: no such column: core_upm_codeartifact.version_id

الحل:
    إضافة العمودَين بـ null=True مبدئياً حتى لا يكسر البيانات الموجودة،
    مع إمكانية تشديدها لاحقاً بعد تعبئة البيانات.
"""

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core_upm', '0003_codeartifact_version_number'),
    ]

    operations = [
        # 1. إنشاء جدول Repository إن لم يكن موجوداً
        migrations.CreateModel(
            name='Repository',
            fields=[
                ('repo_id', models.UUIDField(
                    primary_key=True, serialize=False,
                    editable=False, verbose_name='Repo ID'
                )),
                ('repo_name', models.CharField(max_length=255, verbose_name='Repo Name')),
                ('source_type', models.CharField(
                    max_length=50, blank=True, null=True, verbose_name='Source Type'
                )),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created At')),
                ('project', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='repositories',
                    to='core_upm.project',
                    verbose_name='Project'
                )),
            ],
            options={
                'verbose_name': 'Repository',
                'verbose_name_plural': 'Repositories',
                'ordering': ['-created_at'],
            },
        ),

        # 2. إنشاء جدول Version إن لم يكن موجوداً
        migrations.CreateModel(
            name='Version',
            fields=[
                ('version_id', models.UUIDField(
                    primary_key=True, serialize=False,
                    editable=False, verbose_name='Version ID'
                )),
                ('version_number', models.IntegerField(default=1, verbose_name='Version Number')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created At')),
                ('description', models.TextField(blank=True, null=True, verbose_name='Description')),
                ('project', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='versions',
                    to='core_upm.project',
                    verbose_name='Project'
                )),
            ],
            options={
                'verbose_name': 'Version',
                'verbose_name_plural': 'Versions',
                'ordering': ['-created_at'],
                'unique_together': {('project', 'version_number')},
            },
        ),

        # 3. إنشاء جدول Folder إن لم يكن موجوداً
        migrations.CreateModel(
            name='Folder',
            fields=[
                ('folder_id', models.UUIDField(
                    primary_key=True, serialize=False,
                    editable=False, verbose_name='Folder ID'
                )),
                ('folder_name', models.CharField(max_length=255, verbose_name='Folder Name')),
                ('folder_path', models.CharField(max_length=1024, verbose_name='Folder Path')),
                ('repo', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='folders',
                    to='core_upm.repository',
                    verbose_name='Repository',
                    null=True, blank=True,   # nullable كما يشير ERD (zero-or-one)
                )),
                ('project', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='folders',
                    to='core_upm.project',
                    verbose_name='Project'
                )),
                ('parent_folder', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='subfolders',
                    to='core_upm.folder',
                    verbose_name='Parent Folder',
                    null=True, blank=True,
                )),
            ],
            options={
                'verbose_name': 'Folder',
                'verbose_name_plural': 'Folders',
                'ordering': ['folder_path'],
            },
        ),

        # 4. إضافة FK لـ folder في CodeArtifact
        #    null=True لأن الصفوف الموجودة في DB ليس لها folder بعد
        migrations.AddField(
            model_name='codeartifact',
            name='folder',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='code_artifacts',
                to='core_upm.folder',
                verbose_name='Folder',
                null=True,
                blank=True,
            ),
        ),

        # 5. إضافة FK لـ version في CodeArtifact
        #    null=True لنفس السبب — البيانات القديمة ليس لها version FK
        migrations.AddField(
            model_name='codeartifact',
            name='version',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='code_artifacts',
                to='core_upm.version',
                verbose_name='Version',
                null=True,
                blank=True,
            ),
        ),

        # 6. إضافة source_type لجدول Project (موجود في ERD لكن غائب عن migration الأول)
        migrations.AddField(
            model_name='project',
            name='source_type',
            field=models.CharField(
                max_length=50, blank=True, null=True,
                verbose_name='Source Type'
            ),
        ),
    ]