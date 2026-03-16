from django.contrib import admin
from django.db import models
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from .mongo_utils import get_mongo_db
from django.template.loader import render_to_string
from django.http import HttpResponse
import json
from datetime import datetime
from django.conf import settings

class MongoAIExplanation(models.Model):
    analysis_id = models.CharField(max_length=255, blank=True, null=True)
    explanation_type = models.CharField(max_length=100, blank=True, null=True)
    content = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        verbose_name = "AI Explanation (MongoDB)"
        verbose_name_plural = "AI Explanations (MongoDB)"
        managed = False
        app_label = 'core_ai'
        db_table = 'fake_ai_explanations'  # جدول وهمي

    def __str__(self):
        return f"AI Explanation {self.analysis_id}"


class MongoCodeFile(models.Model):
    filename = models.CharField(max_length=255, blank=True, null=True)
    file_type = models.CharField(max_length=50, blank=True, null=True)
    content = models.TextField(blank=True, null=True)
    uploaded_at = models.DateTimeField(blank=True, null=True)
    analysis_status = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        verbose_name = "Code File (MongoDB)"
        verbose_name_plural = "Code Files (MongoDB)"
        managed = False
        app_label = 'core_ai'
        db_table = 'fake_code_files'  # جدول وهمي

    def __str__(self):
        return f"Code File: {self.filename}"


class MongoAnalysisResult(models.Model):
    code_file_id = models.CharField(max_length=255, blank=True, null=True)
    analysis_started_at = models.DateTimeField(blank=True, null=True)
    analysis_completed_at = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        verbose_name = "Analysis Result (MongoDB)"
        verbose_name_plural = "Analysis Results (MongoDB)"
        managed = False
        app_label = 'core_ai'
        db_table = 'fake_analysis_results'  # جدول وهمي

    def __str__(self):
        return f"Analysis Result {self.code_file_id}"


class MongoAnalysisJob(models.Model):
    code_file_id = models.CharField(max_length=255, blank=True, null=True)
    status = models.CharField(max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    started_at = models.DateTimeField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        verbose_name = "Analysis Job (MongoDB)"
        verbose_name_plural = "Analysis Jobs (MongoDB)"
        managed = False
        app_label = 'core_ai'
        db_table = 'fake_analysis_jobs'  # جدول وهمي

    def __str__(self):
        return f"Analysis Job {self.code_file_id}"


class MongoAITask(models.Model):
    task_id = models.CharField(max_length=255, blank=True, null=True)
    analysis_id = models.CharField(max_length=255, blank=True, null=True)
    exp_type = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        verbose_name = "AI Task (MongoDB)"
        verbose_name_plural = "AI Tasks (MongoDB)"
        managed = False
        app_label = 'core_ai'
        db_table = 'fake_ai_tasks'  # جدول وهمي

    def __str__(self):
        return f"AI Task {self.task_id}"


class BaseMongoAdmin(admin.ModelAdmin):
    def get_queryset(self, request):
        return self.model.objects.none()

    def has_add_permission(self, request):
        return True  # السماح بالإضافة

    def has_change_permission(self, request, obj=None):
        return True  # السماح بالتعديل

    def has_delete_permission(self, request, obj=None):
        return True  # السماح بالحذف

    def has_view_permission(self, request, obj=None):
        return True  # السماح بالعرض

    def has_module_permission(self, request):
        return True  # السماح بظهور الـ app في الصفحة الرئيسية

    def get_actions(self, request):
        """إرجاع قائمة فارغة من الإجراءات لتجنب مشاكل Django ORM"""
        return {}

    def delete_model(self, request, obj):
        """حذف عنصر واحد من MongoDB - لا نستخدم هذه الطريقة"""
        pass

    def delete_queryset(self, request, queryset):
        """حذف عدة عناصر من MongoDB - لا نستخدم هذه الطريقة"""
        pass

    def save_model(self, request, obj, form, change):
        """حفظ النموذج - لا نستخدم هذه الطريقة"""
        pass


class AIExplanationAdmin(BaseMongoAdmin):
    change_list_template = 'admin/core_ai/mongoaiexplanation/change_list.html'
    list_display = ('analysis_id_display', 'explanation_type', 'created_at_display', 'content_preview')
    list_filter = ('explanation_type',)
    search_fields = ('analysis_id',)
    ordering = ('-created_at',)

    def analysis_id_display(self, obj):
        analysis_id = obj.get('analysis_id', 'N/A') if hasattr(obj, 'get') else getattr(obj, 'analysis_id', 'N/A')
        return str(analysis_id)[:8] + '...' if analysis_id != 'N/A' else analysis_id
    analysis_id_display.short_description = 'Analysis ID'

    def created_at_display(self, obj):
        created_at = obj.get('created_at') if hasattr(obj, 'get') else getattr(obj, 'created_at', None)
        if created_at:
            if isinstance(created_at, str):
                return created_at
            elif hasattr(created_at, 'strftime'):
                return created_at.strftime('%Y-%m-%d %H:%M:%S')
        return 'N/A'
    created_at_display.short_description = 'Created At'

    def content_preview(self, obj):
        content = obj.get('content', '') if hasattr(obj, 'get') else getattr(obj, 'content', '')
        if content:
            preview = content[:100] + '...' if len(content) > 100 else content
            return preview.replace('\n', ' ')
        return 'No content'
    content_preview.short_description = 'Content Preview'

    def changelist_view(self, request, extra_context=None):
        if request.method == 'POST':
            action = request.POST.get('action')
            if action == 'delete_selected':
                selected_ids = request.POST.getlist('_selected_action')
                if selected_ids:
                    deleted_count = self._delete_selected_items(selected_ids)
                    if deleted_count > 0:
                        self.message_user(request, f'Successfully deleted {deleted_count} AI explanation(s).')
                    else:
                        self.message_user(request, 'No items were deleted.', level='warning')
            elif action == 'add_new_item':
                self._handle_add_item(request)
        
        extra_context = extra_context or {}
        db = get_mongo_db()
        
        if db is None:
            extra_context['title'] = 'AI Explanations - MongoDB Not Available'
            extra_context['mongodb_error'] = 'MongoDB connection failed. Please check database configuration.'
        else:
            try:
                data = list(db[settings.AI_EXPLANATIONS_COLLECTION].find().sort('_id', -1).limit(100))
                
                processed_data = []
                for item in data:
                    if '_id' in item:
                        item['id'] = str(item['_id'])  # إضافة id للـ template
                        item['_id'] = str(item['_id'])
                    for key, value in item.items():
                        if hasattr(value, '__class__') and 'ObjectId' in str(value.__class__):
                            item[key] = str(value)
                    processed_data.append(item)
                
                extra_context['title'] = f'AI Explanations from MongoDB ({len(processed_data)} records)'
                extra_context['mongodb_data'] = processed_data
                extra_context['has_mongodb_data'] = True
                
            except Exception as e:
                extra_context['title'] = 'AI Explanations - Error'
                extra_context['mongodb_error'] = f'Error loading AI explanations: {str(e)}'
                print(f"Debug - AI Explanations error: {e}")
        
        return super().changelist_view(request, extra_context=extra_context)

    def _handle_add_item(self, request):
        """معالجة إضافة عنصر جديد"""
        try:
            db = get_mongo_db()
            if db is None:
                self.message_user(request, 'MongoDB connection failed.', level='error')
                return
            
            new_item = {
                'analysis_id': request.POST.get('analysis_id', '').strip(),
                'explanation_type': request.POST.get('explanation_type', 'high_level'),
                'content': request.POST.get('content', '').strip(),
                'created_at': datetime.utcnow()
            }
            
            if not new_item['analysis_id'] or not new_item['content']:
                self.message_user(request, 'Analysis ID and Content are required.', level='error')
                return
            
            result = db[settings.AI_EXPLANATIONS_COLLECTION].insert_one(new_item)
            if result.inserted_id:
                self.message_user(request, f'AI Explanation added successfully! ID: {str(result.inserted_id)}')
                print(f"Debug - Added AI explanation with ID: {result.inserted_id}")
            else:
                self.message_user(request, 'Failed to add AI Explanation.', level='error')
                
        except Exception as e:
            self.message_user(request, f'Error adding AI Explanation: {str(e)}', level='error')
            print(f"Debug - Error in _handle_add_item: {e}")

    def _delete_selected_items(self, selected_ids):
        """حذف العناصر المحددة من MongoDB"""
        try:
            db = get_mongo_db()
            if db is None:
                print("Debug - MongoDB connection failed in delete")
                return 0
            
            from bson import ObjectId
            deleted_count = 0
            
            for id_str in selected_ids:
                try:
                    if len(id_str) == 24:  # ObjectId length
                        object_id = ObjectId(id_str)
                    else:
                        object_id = id_str
                    
                    result = db[settings.AI_EXPLANATIONS_COLLECTION].delete_one({"_id": object_id})
                    if result.deleted_count > 0:
                        deleted_count += 1
                        print(f"Debug - Deleted AI explanation with ID: {id_str}")
                    else:
                        print(f"Debug - Failed to delete AI explanation with ID: {id_str}")
                        
                except Exception as e:
                    print(f"Debug - Error deleting AI explanation {id_str}: {e}")
                    continue
            
            print(f"Debug - Total deleted AI explanations: {deleted_count}")
            return deleted_count
            
        except Exception as e:
            print(f"Debug - Error in _delete_selected_items: {e}")
            return 0


class CodeFileAdmin(BaseMongoAdmin):
    change_list_template = 'admin/core_ai/mongocodefile/change_list.html'
    list_display = ('filename_display', 'file_type', 'analysis_status', 'uploaded_at_display', 'content_size')
    list_filter = ('file_type', 'analysis_status')
    search_fields = ('filename',)
    ordering = ('-uploaded_at',)

    def filename_display(self, obj):
        filename = obj.get('filename', 'N/A') if hasattr(obj, 'get') else getattr(obj, 'filename', 'N/A')
        return filename
    filename_display.short_description = 'File Name'

    def uploaded_at_display(self, obj):
        uploaded_at = obj.get('uploaded_at') if hasattr(obj, 'get') else getattr(obj, 'uploaded_at', None)
        if uploaded_at:
            if isinstance(uploaded_at, str):
                return uploaded_at
            elif hasattr(uploaded_at, 'strftime'):
                return uploaded_at.strftime('%Y-%m-%d %H:%M:%S')
        return 'N/A'
    uploaded_at_display.short_description = 'Uploaded At'

    def content_size(self, obj):
        content = obj.get('content', '') if hasattr(obj, 'get') else getattr(obj, 'content', '')
        if content:
            size = len(content)
            if size > 1024:
                return f"{size // 1024} KB"
            return f"{size} bytes"
        return '0 bytes'
    content_size.short_description = 'Content Size'

    def changelist_view(self, request, extra_context=None):
        if request.method == 'POST':
            action = request.POST.get('action')
            if action == 'delete_selected':
                selected_ids = request.POST.getlist('_selected_action')
                if selected_ids:
                    deleted_count = self._delete_selected_items(selected_ids)
                    if deleted_count > 0:
                        self.message_user(request, f'Successfully deleted {deleted_count} code file(s).')
                    else:
                        self.message_user(request, 'No items were deleted.', level='warning')
            elif action == 'add_new_item':
                self._handle_add_item(request)

        extra_context = extra_context or {}
        db = get_mongo_db()

        if db is None:
            extra_context['title'] = 'Code Files - MongoDB Not Available'
            extra_context['mongodb_error'] = 'MongoDB connection failed. Please check database configuration.'
        else:
            try:
                data = list(db[settings.CODE_FILES_COLLECTION].find().sort('_id', -1).limit(100))

                processed_data = []
                for item in data:
                    if '_id' in item:
                        item['id'] = str(item['_id'])  # إضافة id للـ template
                        item['_id'] = str(item['_id'])
                    for key, value in item.items():
                        if hasattr(value, '__class__') and 'ObjectId' in str(value.__class__):
                            item[key] = str(value)
                    processed_data.append(item)

                extra_context['title'] = f'Code Files from MongoDB ({len(processed_data)} records)'
                extra_context['mongodb_data'] = processed_data
                extra_context['has_mongodb_data'] = True

            except Exception as e:
                extra_context['title'] = 'Code Files - Error'
                extra_context['mongodb_error'] = f'Error loading code files: {str(e)}'

        return super().changelist_view(request, extra_context=extra_context)

    def _handle_add_item(self, request):
        """معالجة إضافة عنصر جديد"""
        try:
            db = get_mongo_db()
            if db is None:
                self.message_user(request, 'MongoDB connection failed.', level='error')
                return

            new_item = {
                'filename': request.POST.get('filename', ''),
                'file_type': request.POST.get('file_type', 'python'),
                'content': request.POST.get('content', ''),
                'uploaded_at': datetime.utcnow(),
                'analysis_status': 'PENDING'
            }

            result = db[settings.CODE_FILES_COLLECTION].insert_one(new_item)
            if result.inserted_id:
                self.message_user(request, 'Code File added successfully!')
            else:
                self.message_user(request, 'Failed to add Code File.', level='error')

        except Exception as e:
            self.message_user(request, f'Error adding Code File: {str(e)}', level='error')

    def _delete_selected_items(self, selected_ids):
        """حذف العناصر المحددة من MongoDB"""
        try:
            db = get_mongo_db()
            if db is None:
                return 0
            
            from bson import ObjectId
            object_ids = []
            for id_str in selected_ids:
                try:
                    object_ids.append(ObjectId(id_str))
                except:
                    object_ids.append(id_str)
            
            result = db[settings.CODE_FILES_COLLECTION].delete_many({"_id": {"$in": object_ids}})
            return result.deleted_count
            
        except Exception as e:
            print(f"Error deleting code files: {e}")
            return 0


class AnalysisResultAdmin(BaseMongoAdmin):
    change_list_template = 'admin/core_ai/mongoanalysisresult/change_list.html'
    list_display = ('code_file_id_display', 'status', 'analysis_started_at_display', 
                   'analysis_completed_at_display', 'duration', 'features_count')
    readonly_fields = ('code_file_id', 'status', 'analysis_started_at', 'analysis_completed_at')
    list_filter = ('status',)
    search_fields = ('code_file_id',)
    ordering = ('-analysis_started_at',)

    def code_file_id_display(self, obj):
        if hasattr(obj, 'get') and callable(obj.get):
            code_file_id = obj.get('code_file_id', 'N/A')
        else:
            code_file_id = getattr(obj, 'code_file_id', 'N/A')
        
        if code_file_id != 'N/A':
            return str(code_file_id)[:8] + '...'
        return code_file_id
    code_file_id_display.short_description = 'Code File ID'

    def analysis_started_at_display(self, obj):
        if hasattr(obj, 'get') and callable(obj.get):
            started_at = obj.get('analysis_started_at')
        else:
            started_at = getattr(obj, 'analysis_started_at', None)
            
        if started_at:
            if isinstance(started_at, str):
                return started_at
            elif hasattr(started_at, 'strftime'):
                return started_at.strftime('%Y-%m-%d %H:%M:%S')
        return 'N/A'
    analysis_started_at_display.short_description = 'Started At'

    def analysis_completed_at_display(self, obj):
        if hasattr(obj, 'get') and callable(obj.get):
            completed_at = obj.get('analysis_completed_at')
        else:
            completed_at = getattr(obj, 'analysis_completed_at', None)
            
        if completed_at:
            if isinstance(completed_at, str):
                return completed_at
            elif hasattr(completed_at, 'strftime'):
                return completed_at.strftime('%Y-%m-%d %H:%M:%S')
        return 'N/A'
    analysis_completed_at_display.short_description = 'Completed At'

    def duration(self, obj):
        if hasattr(obj, 'get') and callable(obj.get):
            started = obj.get('analysis_started_at')
            completed = obj.get('analysis_completed_at')
        else:
            started = getattr(obj, 'analysis_started_at', None)
            completed = getattr(obj, 'analysis_completed_at', None)
            
        if started and completed:
            try:
                if isinstance(started, str):
                    started = datetime.fromisoformat(started.replace('Z', '+00:00'))
                if isinstance(completed, str):
                    completed = datetime.fromisoformat(completed.replace('Z', '+00:00'))
                
                duration = completed - started
                return f"{duration.total_seconds():.2f}s"
            except:
                return 'N/A'
        return 'N/A'
    duration.short_description = 'Duration'

    def features_count(self, obj):
        if hasattr(obj, 'get') and callable(obj.get):
            features = obj.get('extracted_features', {})
        else:
            features = getattr(obj, 'extracted_features', {})
            
        if features and isinstance(features, dict):
            return len(features)
        return 0
    features_count.short_description = 'Features Count'

    def changelist_view(self, request, extra_context=None):
        if request.method == 'POST' and 'action' in request.POST:
            action = request.POST.get('action')
            if action == 'delete_selected':
                selected_ids = request.POST.getlist('_selected_action')
                if selected_ids:
                    deleted_count = self._delete_selected_items(selected_ids)
                    if deleted_count > 0:
                        self.message_user(request, f'Successfully deleted {deleted_count} analysis result(s).')
                    else:
                        self.message_user(request, 'No items were deleted.', level='warning')
        
    def changelist_view(self, request, extra_context=None):
        if request.method == 'POST' and 'action' in request.POST:
            action = request.POST.get('action')
            if action == 'delete_selected':
                selected_ids = request.POST.getlist('_selected_action')
                if selected_ids:
                    deleted_count = self._delete_selected_items(selected_ids)
                    if deleted_count > 0:
                        self.message_user(request, f'Successfully deleted {deleted_count} analysis result(s).')
                    else:
                        self.message_user(request, 'No items were deleted.', level='warning')
        
        extra_context = extra_context or {}
        db = get_mongo_db()
        
        if db is None:
            extra_context['title'] = 'Analysis Results - MongoDB Not Available'
            extra_context['mongodb_error'] = 'MongoDB connection failed. Please check database configuration.'
        else:
            try:
                data = list(db[settings.ANALYSIS_RESULTS_COLLECTION].find().sort('_id', -1).limit(100))
                
                processed_data = []
                for item in data:
                    if '_id' in item:
                        item['id'] = str(item['_id'])  # إضافة id للـ template
                        item['_id'] = str(item['_id'])
                    for key, value in item.items():
                        if hasattr(value, '__class__') and 'ObjectId' in str(value.__class__):
                            item[key] = str(value)
                    processed_data.append(item)
                
                extra_context['title'] = f'Analysis Results from MongoDB ({len(processed_data)} records)'
                extra_context['mongodb_data'] = processed_data
                extra_context['has_mongodb_data'] = True
                
            except Exception as e:
                extra_context['title'] = 'Analysis Results - Error'
                extra_context['mongodb_error'] = f'Error loading analysis results: {str(e)}'
        
        return super().changelist_view(request, extra_context=extra_context)

    def _delete_selected_items(self, selected_ids):
        """حذف العناصر المحددة من MongoDB"""
        try:
            db = get_mongo_db()
            if db is None:
                return 0
            
            from bson import ObjectId
            object_ids = []
            for id_str in selected_ids:
                try:
                    object_ids.append(ObjectId(id_str))
                except:
                    object_ids.append(id_str)
            
            result = db[settings.ANALYSIS_RESULTS_COLLECTION].delete_many({"_id": {"$in": object_ids}})
            return result.deleted_count
            
        except Exception as e:
            print(f"Error deleting analysis results: {e}")
            return 0


class AnalysisJobAdmin(BaseMongoAdmin):
    change_list_template = 'admin/core_ai/mongoanalysisjob/change_list.html'
    list_display = ('code_file_id_display', 'status', 'created_at_display', 
                   'started_at_display', 'completed_at_display', 'duration')
    readonly_fields = ('code_file_id', 'status', 'created_at', 'started_at', 'completed_at')
    list_filter = ('status',)
    search_fields = ('code_file_id',)
    ordering = ('-created_at',)

    def code_file_id_display(self, obj):
        if hasattr(obj, 'get') and callable(obj.get):
            code_file_id = obj.get('code_file_id', 'N/A')
        else:
            code_file_id = getattr(obj, 'code_file_id', 'N/A')
        
        if code_file_id != 'N/A':
            return str(code_file_id)[:8] + '...'
        return code_file_id
    code_file_id_display.short_description = 'Code File ID'

    def created_at_display(self, obj):
        return self._format_datetime(obj, 'created_at')
    created_at_display.short_description = 'Created At'

    def started_at_display(self, obj):
        return self._format_datetime(obj, 'started_at')
    started_at_display.short_description = 'Started At'

    def completed_at_display(self, obj):
        return self._format_datetime(obj, 'completed_at')
    completed_at_display.short_description = 'Completed At'

    def duration(self, obj):
        if hasattr(obj, 'get') and callable(obj.get):
            started = obj.get('started_at')
            completed = obj.get('completed_at')
        else:
            started = getattr(obj, 'started_at', None)
            completed = getattr(obj, 'completed_at', None)
            
        if started and completed:
            try:
                if isinstance(started, str):
                    started = datetime.fromisoformat(started.replace('Z', '+00:00'))
                if isinstance(completed, str):
                    completed = datetime.fromisoformat(completed.replace('Z', '+00:00'))
                
                duration = completed - started
                return f"{duration.total_seconds():.2f}s"
            except:
                return 'N/A'
        return 'N/A'
    duration.short_description = 'Duration'

    def changelist_view(self, request, extra_context=None):
        if request.method == 'POST' and 'action' in request.POST:
            action = request.POST.get('action')
            if action == 'delete_selected':
                selected_ids = request.POST.getlist('_selected_action')
                if selected_ids:
                    deleted_count = self._delete_selected_items(selected_ids)
                    if deleted_count > 0:
                        self.message_user(request, f'Successfully deleted {deleted_count} analysis job(s).')
                    else:
                        self.message_user(request, 'No items were deleted.', level='warning')
        
    def changelist_view(self, request, extra_context=None):
        if request.method == 'POST' and 'action' in request.POST:
            action = request.POST.get('action')
            if action == 'delete_selected':
                selected_ids = request.POST.getlist('_selected_action')
                if selected_ids:
                    deleted_count = self._delete_selected_items(selected_ids)
                    if deleted_count > 0:
                        self.message_user(request, f'Successfully deleted {deleted_count} analysis job(s).')
                    else:
                        self.message_user(request, 'No items were deleted.', level='warning')
        
        extra_context = extra_context or {}
        db = get_mongo_db()
        
        if db is None:
            extra_context['title'] = 'Analysis Jobs - MongoDB Not Available'
            extra_context['mongodb_error'] = 'MongoDB connection failed. Please check database configuration.'
        else:
            try:
                data = list(db[settings.ANALYSIS_JOBS_COLLECTION].find().sort('_id', -1).limit(100))
                
                processed_data = []
                for item in data:
                    if '_id' in item:
                        item['id'] = str(item['_id'])  # إضافة id للـ template
                        item['_id'] = str(item['_id'])
                    for key, value in item.items():
                        if hasattr(value, '__class__') and 'ObjectId' in str(value.__class__):
                            item[key] = str(value)
                    processed_data.append(item)
                
                extra_context['title'] = f'Analysis Jobs from MongoDB ({len(processed_data)} records)'
                extra_context['mongodb_data'] = processed_data
                extra_context['has_mongodb_data'] = True
                
            except Exception as e:
                extra_context['title'] = 'Analysis Jobs - Error'
                extra_context['mongodb_error'] = f'Error loading analysis jobs: {str(e)}'
        
        return super().changelist_view(request, extra_context=extra_context)

    def _delete_selected_items(self, selected_ids):
        """حذف العناصر المحددة من MongoDB"""
        try:
            db = get_mongo_db()
            if db is None:
                return 0
            
            from bson import ObjectId
            object_ids = []
            for id_str in selected_ids:
                try:
                    object_ids.append(ObjectId(id_str))
                except:
                    object_ids.append(id_str)
            
            result = db[settings.ANALYSIS_JOBS_COLLECTION].delete_many({"_id": {"$in": object_ids}})
            return result.deleted_count
            
        except Exception as e:
            print(f"Error deleting analysis jobs: {e}")
            return 0


class AITaskAdmin(BaseMongoAdmin):
    change_list_template = 'admin/core_ai/mongoaitask/change_list.html'
    list_display = ('task_id_display', 'analysis_id_display', 'exp_type', 'status', 'created_at_display')
    readonly_fields = ('task_id', 'analysis_id', 'exp_type', 'status', 'created_at')
    list_filter = ('status', 'exp_type')
    search_fields = ('task_id', 'analysis_id')
    ordering = ('-created_at',)

    def task_id_display(self, obj):
        if hasattr(obj, 'get') and callable(obj.get):
            task_id = obj.get('task_id', 'N/A')
        else:
            task_id = getattr(obj, 'task_id', 'N/A')
        
        if task_id != 'N/A':
            return str(task_id)[:12] + '...'
        return task_id
    task_id_display.short_description = 'Task ID'

    def analysis_id_display(self, obj):
        if hasattr(obj, 'get') and callable(obj.get):
            analysis_id = obj.get('analysis_id', 'N/A')
        else:
            analysis_id = getattr(obj, 'analysis_id', 'N/A')
        
        if analysis_id != 'N/A':
            return str(analysis_id)[:8] + '...'
        return analysis_id
    analysis_id_display.short_description = 'Analysis ID'

    def created_at_display(self, obj):
        return self._format_datetime(obj, 'created_at')
    created_at_display.short_description = 'Created At'

    def changelist_view(self, request, extra_context=None):
        if request.method == 'POST' and 'action' in request.POST:
            action = request.POST.get('action')
            if action == 'delete_selected':
                selected_ids = request.POST.getlist('_selected_action')
                if selected_ids:
                    deleted_count = self._delete_selected_items(selected_ids)
                    if deleted_count > 0:
                        self.message_user(request, f'Successfully deleted {deleted_count} AI task(s).')
                    else:
                        self.message_user(request, 'No items were deleted.', level='warning')
        
    def changelist_view(self, request, extra_context=None):
        if request.method == 'POST' and 'action' in request.POST:
            action = request.POST.get('action')
            if action == 'delete_selected':
                selected_ids = request.POST.getlist('_selected_action')
                if selected_ids:
                    deleted_count = self._delete_selected_items(selected_ids)
                    if deleted_count > 0:
                        self.message_user(request, f'Successfully deleted {deleted_count} AI task(s).')
                    else:
                        self.message_user(request, 'No items were deleted.', level='warning')
        
        extra_context = extra_context or {}
        db = get_mongo_db()
        
        if db is None:
            extra_context['title'] = 'AI Tasks - MongoDB Not Available'
            extra_context['mongodb_error'] = 'MongoDB connection failed. Please check database configuration.'
        else:
            try:
                data = list(db[settings.AI_TASKS_COLLECTION].find().sort('_id', -1).limit(100))
                
                processed_data = []
                for item in data:
                    if '_id' in item:
                        item['id'] = str(item['_id'])  # إضافة id للـ template
                        item['_id'] = str(item['_id'])
                    for key, value in item.items():
                        if hasattr(value, '__class__') and 'ObjectId' in str(value.__class__):
                            item[key] = str(value)
                    processed_data.append(item)
                
                extra_context['title'] = f'AI Tasks from MongoDB ({len(processed_data)} records)'
                extra_context['mongodb_data'] = processed_data
                extra_context['has_mongodb_data'] = True
                
            except Exception as e:
                extra_context['title'] = 'AI Tasks - Error'
                extra_context['mongodb_error'] = f'Error loading AI tasks: {str(e)}'
        
        return super().changelist_view(request, extra_context=extra_context)

    def _delete_selected_items(self, selected_ids):
        """حذف العناصر المحددة من MongoDB"""
        try:
            db = get_mongo_db()
            if db is None:
                return 0
            
            from bson import ObjectId
            object_ids = []
            for id_str in selected_ids:
                try:
                    object_ids.append(ObjectId(id_str))
                except:
                    object_ids.append(id_str)
            
            result = db[settings.AI_TASKS_COLLECTION].delete_many({"_id": {"$in": object_ids}})
            return result.deleted_count
            
        except Exception as e:
            print(f"Error deleting AI tasks: {e}")
            return 0


BaseMongoAdmin._format_datetime = lambda self, obj, field_name: (
    obj.get(field_name).strftime('%Y-%m-%d %H:%M:%S') 
    if hasattr(obj, 'get') and obj.get(field_name) and hasattr(obj.get(field_name), 'strftime')
    else (getattr(obj, field_name).strftime('%Y-%m-%d %H:%M:%S') 
          if getattr(obj, field_name, None) and hasattr(getattr(obj, field_name), 'strftime')
          else 'N/A')
)

BaseMongoAdmin._get_mongo_changelist_view = lambda self, request, extra_context, collection_name, title: (
    self._mongo_changelist_view_impl(request, extra_context, collection_name, title)
)

def _mongo_changelist_view_impl(self, request, extra_context, collection_name, title):
    """Implementation for MongoDB changelist view"""
    db = get_mongo_db()
    
    extra_context = extra_context or {}
    
    if db is None:
        extra_context['title'] = f'{title} - MongoDB Not Available'
        extra_context['mongodb_error'] = 'MongoDB connection failed. Please check database configuration.'
    else:
        try:
            data = list(db[collection_name].find().sort('_id', -1).limit(100))
            
            processed_data = []
            for item in data:
                if '_id' in item:
                    item['_id'] = str(item['_id'])
                for key, value in item.items():
                    if hasattr(value, '__class__') and 'ObjectId' in str(value.__class__):
                        item[key] = str(value)
                processed_data.append(item)
            
            extra_context['title'] = f'{title} from MongoDB ({len(processed_data)} records)'
            extra_context['mongodb_data'] = processed_data
            extra_context['has_mongodb_data'] = True
            
        except Exception as e:
            extra_context['title'] = f'{title} - Error'
            extra_context['mongodb_error'] = f'Error loading {title.lower()}: {str(e)}'
    
    return super(BaseMongoAdmin, self).changelist_view(request, extra_context=extra_context)

BaseMongoAdmin._mongo_changelist_view_impl = _mongo_changelist_view_impl


class MongoGeneratedFile(models.Model):
    filename = models.CharField(max_length=255, blank=True, null=True)
    file_type = models.CharField(max_length=50, blank=True, null=True)
    explanation_id = models.CharField(max_length=255, blank=True, null=True)
    file_size = models.IntegerField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    downloaded_count = models.IntegerField(blank=True, null=True)

    class Meta:
        verbose_name = "Generated File (MongoDB)"
        verbose_name_plural = "Generated Files (MongoDB)"
        managed = False
        app_label = 'core_ai'
        db_table = 'fake_generated_files'

    def __str__(self):
        return f"Generated: {self.filename}"


class MongoDocumentationFile(models.Model):
    filename = models.CharField(max_length=255, blank=True, null=True)
    file_type = models.CharField(max_length=50, blank=True, null=True)
    content = models.TextField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)  # حقل الشرح الجديد
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    category = models.CharField(max_length=100, blank=True, null=True)
    tags = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Documentation File (MongoDB)"
        verbose_name_plural = "Documentation Files (MongoDB)"
        managed = False
        app_label = 'core_ai'
        db_table = 'fake_documentation_files'

    def __str__(self):
        return f"Documentation: {self.filename}"


class GeneratedFileAdmin(BaseMongoAdmin):
    change_list_template = 'admin/core_ai/mongogeneratedfile/change_list.html'
    list_display = ('filename_display', 'file_type', 'explanation_type_display', 'analysis_id_display',
                   'file_size_display', 'created_at_display', 'downloaded_count', 'download_link', 'view_content_link')
    readonly_fields = ('filename', 'file_type', 'explanation_id', 'file_size', 'created_at', 'downloaded_count')
    list_filter = ('file_type',)
    search_fields = ('filename', 'explanation_id', 'analysis_id')
    ordering = ('-created_at',)

    def filename_display(self, obj):
        if hasattr(obj, 'get') and callable(obj.get):
            filename = obj.get('filename', 'N/A')
        else:
            filename = getattr(obj, 'filename', 'N/A')
        return filename
    filename_display.short_description = 'File Name'

    def explanation_id_display(self, obj):
        if hasattr(obj, 'get') and callable(obj.get):
            exp_id = obj.get('explanation_id', 'N/A')
        else:
            exp_id = getattr(obj, 'explanation_id', 'N/A')

        if exp_id != 'N/A':
            return str(exp_id)[:12] + '...'
        return exp_id
    explanation_id_display.short_description = 'Explanation ID'

    def file_size_display(self, obj):
        if hasattr(obj, 'get') and callable(obj.get):
            size = obj.get('file_size', 0)
        else:
            size = getattr(obj, 'file_size', 0)

        if size:
            if size > 1024 * 1024:
                return f"{size // (1024 * 1024):.1f} MB"
            elif size > 1024:
                return f"{size // 1024:.1f} KB"
            return f"{size} bytes"
        return '0 bytes'
    file_size_display.short_description = 'File Size'

    def created_at_display(self, obj):
        return self._format_datetime(obj, 'created_at')
    created_at_display.short_description = 'Created At'

    def explanation_type_display(self, obj):
        """عرض نوع الشرح (high/low)"""
        if hasattr(obj, 'get') and callable(obj.get):
            explanation_id = obj.get('explanation_id', '')
        else:
            explanation_id = getattr(obj, 'explanation_id', '')

        if explanation_id:
            try:
                db = get_mongo_db()
                if db:
                    explanation = db[settings.AI_EXPLANATIONS_COLLECTION].find_one({'_id': explanation_id})
                    if explanation and 'exp_type' in explanation:
                        exp_type = explanation['exp_type']
                        if 'high' in exp_type.lower():
                            return format_html('<span style="color: #d32f2f; font-weight: bold;">High Level</span>')
                        elif 'low' in exp_type.lower():
                            return format_html('<span style="color: #388e3c; font-weight: bold;">Low Level</span>')
                        else:
                            return exp_type
            except Exception as e:
                pass
        return 'N/A'
    explanation_type_display.short_description = 'Explanation Type'

    def analysis_id_display(self, obj):
        """عرض معرف التحليل"""
        if hasattr(obj, 'get') and callable(obj.get):
            analysis_id = obj.get('analysis_id', 'N/A')
        else:
            analysis_id = getattr(obj, 'analysis_id', 'N/A')

        if analysis_id != 'N/A':
            return str(analysis_id)[:8] + '...'
        return analysis_id
    analysis_id_display.short_description = 'Analysis ID'

    def download_link(self, obj):
        if hasattr(obj, 'get') and callable(obj.get):
            file_id = obj.get('_id', '')
            filename = obj.get('filename', 'file')
            file_type = obj.get('file_type', 'unknown')
        else:
            file_id = getattr(obj, '_id', '')
            filename = getattr(obj, 'filename', 'file')
            file_type = getattr(obj, 'file_type', 'unknown')

        if file_id:
            url = f"/api/analysis/download-generated-file/{file_id}/"
            return format_html('<a href="{}" target="_blank" class="button" style="background: #1976d2; color: white; padding: 5px 10px; text-decoration: none; border-radius: 3px;">📥 Download</a>', url)
        return 'N/A'
    download_link.short_description = 'Download'

    def view_content_link(self, obj):
        """رابط لعرض محتوى الملف"""
        if hasattr(obj, 'get') and callable(obj.get):
            file_id = obj.get('_id', '')
            filename = obj.get('filename', 'Unknown')
            file_type = obj.get('file_type', 'unknown')
        else:
            file_id = getattr(obj, '_id', '')
            filename = getattr(obj, 'filename', 'Unknown')
            file_type = getattr(obj, 'file_type', 'unknown')

        if file_id:
            return format_html('<a href="#" onclick="viewFileContent(\'{}\', \'{}\', \'{}\')" style="color: #ff9800; text-decoration: none; font-weight: bold;">👁️ View</a>', file_id, filename, file_type)
        return 'N/A'
    view_content_link.short_description = 'View Content'

    def changelist_view(self, request, extra_context=None):
        if request.method == 'POST' and 'action' in request.POST:
            action = request.POST.get('action')
            if action == 'delete_selected':
                selected_ids = request.POST.getlist('_selected_action')
                if selected_ids:
                    deleted_count = self._delete_selected_items(selected_ids)
                    if deleted_count > 0:
                        self.message_user(request, f'Successfully deleted {deleted_count} generated file(s).')
                    else:
                        self.message_user(request, 'No items were deleted.', level='warning')

        extra_context = extra_context or {}
        db = get_mongo_db()

        if db is None:
            extra_context['title'] = 'Generated Files - MongoDB Not Available'
            extra_context['mongodb_error'] = 'MongoDB connection failed. Please check database configuration.'
        else:
            try:
                data = list(db[settings.GENERATED_FILES_COLLECTION].find().sort('_id', -1).limit(100))

                processed_data = []
                for item in data:
                    if '_id' in item:
                        item['id'] = str(item['_id'])  # إضافة id للـ template
                        item['_id'] = str(item['_id'])
                    for key, value in item.items():
                        if hasattr(value, '__class__') and 'ObjectId' in str(value.__class__):
                            item[key] = str(value)
                    processed_data.append(item)

                extra_context['title'] = f'Generated Documentation Files ({len(processed_data)} files)'
                extra_context['mongodb_data'] = processed_data
                extra_context['has_mongodb_data'] = len(processed_data) > 0

                extra_context['javascript_code'] = """
                <script>
                function viewFileContent(fileId, filename, fileType) {
                    // فتح نافذة جديدة لعرض المحتوى
                    var win = window.open('', '_blank', 'width=800,height=600,scrollbars=yes,resizable=yes');
                    win.document.write('<html><head><title>' + filename + '</title>');
                    win.document.write('<style>body{font-family: monospace; padding: 20px; background: #f5f5f5;} pre{white-space: pre-wrap; background: white; padding: 15px; border-radius: 5px; border: 1px solid #ddd;} .header{background: #2196f3; color: white; padding: 10px; margin: -20px -20px 20px -20px;}</style>');
                    win.document.write('</head><body>');
                    win.document.write('<div class="header"><h2>' + filename + ' (' + fileType.toUpperCase() + ')</h2></div>');
                    win.document.write('<div id="content">Loading...</div>');
                    win.document.write('</body></html>');

                    // جلب المحتوى من API
                    fetch('/api/analysis/download-generated-file/' + fileId + '/')
                        .then(response => {
                            if (fileType === 'pdf') {
                                return response.blob();
                            } else {
                                return response.text();
                            }
                        })
                        .then(data => {
                            var contentDiv = win.document.getElementById('content');
                            if (fileType === 'pdf') {
                                var url = URL.createObjectURL(data);
                                contentDiv.innerHTML = '<embed src="' + url + '" width="100%" height="500px" type="application/pdf">';
                            } else {
                                contentDiv.innerHTML = '<pre>' + data + '</pre>';
                            }
                        })
                        .catch(error => {
                            win.document.getElementById('content').innerHTML = '<div style="color: red;">Error loading content: ' + error.message + '</div>';
                        });
                }
                </script>
                """

            except Exception as e:
                extra_context['title'] = 'Generated Files - Error'
                extra_context['mongodb_error'] = f'Error loading generated files: {str(e)}'

        return super().changelist_view(request, extra_context=extra_context)

    def _delete_selected_items(self, selected_ids):
        """حذف العناصر المحددة من MongoDB"""
        try:
            db = get_mongo_db()
            if db is None:
                return 0

            from bson import ObjectId
            object_ids = []
            for id_str in selected_ids:
                try:
                    object_ids.append(ObjectId(id_str))
                except:
                    object_ids.append(id_str)

            result = db[settings.GENERATED_FILES_COLLECTION].delete_many({"_id": {"$in": object_ids}})
            return result.deleted_count

        except Exception as e:
            print(f"Error deleting generated files: {e}")
            return 0


class DocumentationFileAdmin(BaseMongoAdmin):
    change_list_template = 'admin/core_ai/mongodocumentationfile/change_list.html'
    list_display = ('filename_display', 'file_type', 'description_display', 'category', 'content_size', 'source_display', 'created_at_display', 'updated_at_display', 'actions_display')
    readonly_fields = ('filename', 'file_type', 'content', 'created_at', 'updated_at', 'category', 'tags', 'description')
    list_filter = ('file_type', 'category')
    search_fields = ('filename', 'category', 'tags', 'description')
    ordering = ('-updated_at', '-created_at')

    def filename_display(self, obj):
        if hasattr(obj, 'get') and callable(obj.get):
            filename = obj.get('filename', 'N/A')
        else:
            filename = getattr(obj, 'filename', 'N/A')
        return filename
    filename_display.short_description = 'File Name'

    def description_display(self, obj):
        if hasattr(obj, 'get') and callable(obj.get):
            description = obj.get('description', '')
        else:
            description = getattr(obj, 'description', '')
        
        if description:
            preview = description[:100] + '...' if len(description) > 100 else description
            return preview.replace('\n', ' ')
        return 'No description'
    description_display.short_description = 'Description'

    def created_at_display(self, obj):
        return self._format_datetime(obj, 'created_at')
    created_at_display.short_description = 'Created At'

    def updated_at_display(self, obj):
        return self._format_datetime(obj, 'updated_at')
    updated_at_display.short_description = 'Updated At'

    def content_size(self, obj):
        if hasattr(obj, 'get') and callable(obj.get):
            content = obj.get('content', '')
        else:
            content = getattr(obj, 'content', '')
            
        if content:
            size = len(content)
            if size > 1024 * 1024:
                return f"{size // (1024 * 1024)} MB"
            elif size > 1024:
                return f"{size // 1024} KB"
            return f"{size} bytes"
        return '0 bytes'
    content_size.short_description = 'Content Size'

    def source_display(self, obj):
        if hasattr(obj, 'get') and callable(obj.get):
            source = obj.get('source', 'documentation_files')
        else:
            source = getattr(obj, 'source', 'documentation_files')
            
        if source == 'code_files':
            return '📁 Code Files'
        return '📚 Documentation'
    source_display.short_description = 'Source'

    def actions_display(self, obj):
        if hasattr(obj, 'get') and callable(obj.get):
            file_id = obj.get('_id', '')
            filename = obj.get('filename', 'Unknown')
            source = obj.get('source', 'documentation_files')
        else:
            file_id = getattr(obj, '_id', '')
            filename = getattr(obj, 'filename', 'Unknown')
            source = getattr(obj, 'source', 'documentation_files')
            
        if file_id:
            actions = f'<a href="#" onclick="viewDocContent(\'{file_id}\', \'{filename}\')" style="color: #417690; text-decoration: none;">👁️ View</a>'
            if source == 'code_files':
                actions += f'<br><a href="/api/analysis/codefiles/{file_id}/" target="_blank" style="color: #ff9800; text-decoration: none; font-size: 11px;">📁 Original</a>'
            return format_html(actions)
        return 'N/A'
    actions_display.short_description = 'Actions'

    def changelist_view(self, request, extra_context=None):
        if request.method == 'POST':
            action = request.POST.get('action')
            if action == 'delete_selected':
                selected_ids = request.POST.getlist('_selected_action')
                if selected_ids:
                    deleted_count = self._delete_selected_items(selected_ids)
                    if deleted_count > 0:
                        self.message_user(request, f'Successfully deleted {deleted_count} documentation file(s).')
                    else:
                        self.message_user(request, 'No items were deleted.', level='warning')
            elif action == 'add_new_item':
                self._handle_add_item(request)
            elif action == 'mark_high_priority':
                selected_ids = request.POST.getlist('_selected_action')
                if selected_ids:
                    updated_count = self._update_priority(selected_ids, 'high')
                    if updated_count > 0:
                        self.message_user(request, f'Successfully marked {updated_count} file(s) as high priority.')
                    else:
                        self.message_user(request, 'No items were updated.', level='warning')
            elif action == 'mark_low_priority':
                selected_ids = request.POST.getlist('_selected_action')
                if selected_ids:
                    updated_count = self._update_priority(selected_ids, 'low')
                    if updated_count > 0:
                        self.message_user(request, f'Successfully marked {updated_count} file(s) as low priority.')
                    else:
                        self.message_user(request, 'No items were updated.', level='warning')
        
        extra_context = extra_context or {}
        db = get_mongo_db()
        
        if db is None:
            extra_context['title'] = 'Documentation Files - MongoDB Not Available'
            extra_context['mongodb_error'] = 'MongoDB connection failed. Please check database configuration.'
        else:
            try:
                documentation_data = []
                
                try:
                    generated_files = list(db[settings.GENERATED_FILES_COLLECTION].find().sort('_id', -1).limit(100))
                    for item in generated_files:
                        item['source'] = 'generated_files'
                        item['category'] = 'Generated Documents'
                        if 'content' not in item and 'file_content' in item:
                            item['content'] = item['file_content']
                        if 'file_type' not in item and 'file_type' in item:
                            pass  # keep existing
                        elif 'filename' in item and item['filename'].endswith('.pdf'):
                            item['file_type'] = 'pdf'
                        elif 'filename' in item and item['filename'].endswith('.md'):
                            item['file_type'] = 'markdown'
                        else:
                            item['file_type'] = 'generated'

                    documentation_data.extend(generated_files)
                    print(f"Debug - Found {len(generated_files)} generated files")
                except Exception as e:
                    print(f"Debug - Error searching generated_files: {e}")

                
                processed_data = []
                for item in documentation_data:
                    if '_id' in item:
                        item['id'] = str(item['_id'])  # إضافة id للـ template
                        item['_id'] = str(item['_id'])
                    for key, value in item.items():
                        if hasattr(value, '__class__') and 'ObjectId' in str(value.__class__):
                            item[key] = str(value)
                    processed_data.append(item)
                
                extra_context['title'] = f'Documentation Files from MongoDB ({len(processed_data)} records)'
                extra_context['mongodb_data'] = processed_data
                extra_context['has_mongodb_data'] = len(processed_data) > 0
                print(f"Debug - Total documentation files processed: {len(processed_data)}")
                
            except Exception as e:
                extra_context['title'] = 'Documentation Files - Error'
                extra_context['mongodb_error'] = f'Error loading documentation files: {str(e)}'
                print(f"Debug - Documentation files error: {e}")
        
        return super().changelist_view(request, extra_context=extra_context)

    def _handle_add_item(self, request):
        """معالجة إضافة عنصر جديد"""
        try:
            db = get_mongo_db()
            if db is None:
                self.message_user(request, 'MongoDB connection failed.', level='error')
                return

            file_type = request.POST.get('file_type', 'text').strip()
            filename = request.POST.get('filename', '').strip()
            content = request.POST.get('content', '').strip()

            if not filename:
                self.message_user(request, 'Filename is required.', level='error')
                return

            if file_type in ['pdf', 'markdown']:
                collection = settings.GENERATED_FILES_COLLECTION
                new_item = {
                    'filename': filename,
                    'file_type': file_type,
                    'file_content': content,
                    'file_size': len(content) if content else 0,
                    'created_at': datetime.utcnow(),
                    'downloaded_count': 0,
                    'source': 'generated_files',
                    'category': 'Generated Documents'
                }
            else:
                collection = settings.DOCUMENTATION_FILES_COLLECTION
                priority = request.POST.get('priority', 'low').strip()

                if priority == 'high' and not filename.upper().startswith('H'):
                    filename = f"[HIGH] {filename}"
                elif priority == 'low' and not filename.upper().startswith('L'):
                    filename = f"[LOW] {filename}"

                new_item = {
                    'filename': filename,
                    'content': content,
                    'description': request.POST.get('description', '').strip(),
                    'category': request.POST.get('category', 'General Documentation').strip(),
                    'file_type': file_type,
                    'priority': priority,
                    'created_at': datetime.utcnow(),
                    'updated_at': datetime.utcnow(),
                    'source': 'documentation_files'
                }

            result = db[collection].insert_one(new_item)
            if result.inserted_id:
                self.message_user(request, f'File added successfully! ID: {str(result.inserted_id)}')
                print(f"Debug - Added file with ID: {result.inserted_id} to {collection}")
            else:
                self.message_user(request, 'Failed to add file.', level='error')

        except Exception as e:
            self.message_user(request, f'Error adding file: {str(e)}', level='error')
            print(f"Debug - Error in _handle_add_item: {e}")

    def _delete_selected_items(self, selected_ids):
        """حذف العناصر المحددة من جميع MongoDB collections"""
        try:
            db = get_mongo_db()
            if db is None:
                print("Debug - MongoDB connection failed in delete")
                return 0

            from bson import ObjectId
            deleted_count = 0

            for id_str in selected_ids:
                try:
                    obj_id = ObjectId(id_str)

                    res1 = db[settings.DOCUMENTATION_FILES_COLLECTION].delete_one({"_id": obj_id})
                    res2 = db[settings.GENERATED_FILES_COLLECTION].delete_one({"_id": obj_id})
                    res3 = db[settings.CODE_FILES_COLLECTION].delete_one({"_id": obj_id})
                    res4 = db[settings.AI_EXPLANATIONS_COLLECTION].delete_one({"_id": obj_id})

                    if res1.deleted_count > 0 or res2.deleted_count > 0 or res3.deleted_count > 0 or res4.deleted_count > 0:
                        deleted_count += 1
                        print(f"Debug - Deleted file with ID: {id_str}")
                    else:
                        print(f"Debug - File with ID: {id_str} not found in any collection")

                except Exception as e:
                    print(f"Debug - Error deleting file {id_str}: {e}")
                    continue

            print(f"Debug - Total deleted files: {deleted_count}")
            return deleted_count

        except Exception as e:
            print(f"Debug - Error in _delete_selected_items: {e}")
            return 0

    def _update_priority(self, selected_ids, priority):
        """تحديث أولوية العناصر المحددة في MongoDB"""
        try:
            db = get_mongo_db()
            if db is None:
                print("Debug - MongoDB connection failed in priority update")
                return 0

            from bson import ObjectId
            updated_count = 0

            for id_str in selected_ids:
                try:
                    obj_id = ObjectId(id_str)

                    current_doc = db[settings.DOCUMENTATION_FILES_COLLECTION].find_one({"_id": obj_id})
                    if not current_doc:
                        current_doc = db[settings.CODE_FILES_COLLECTION].find_one({"_id": obj_id})

                    if current_doc:
                        filename = current_doc.get('filename', '')

                        filename = filename.replace('[HIGH] ', '').replace('[LOW] ', '')

                        if priority == 'high':
                            filename = f"[HIGH] {filename}"
                        else:
                            filename = f"[LOW] {filename}"

                        update_result1 = db[settings.DOCUMENTATION_FILES_COLLECTION].update_one(
                            {"_id": obj_id},
                            {"$set": {"filename": filename, "priority": priority, "updated_at": datetime.utcnow()}}
                        )
                        update_result2 = db[settings.CODE_FILES_COLLECTION].update_one(
                            {"_id": obj_id},
                            {"$set": {"filename": filename, "priority": priority, "updated_at": datetime.utcnow()}}
                        )

                        if update_result1.modified_count > 0 or update_result2.modified_count > 0:
                            updated_count += 1
                            print(f"Debug - Updated priority for file with ID: {id_str}")
                    else:
                        print(f"Debug - File not found with ID: {id_str}")

                except Exception as e:
                    print(f"Debug - Error updating priority for file {id_str}: {e}")
                    continue

            print(f"Debug - Total updated priority files: {updated_count}")
            return updated_count

        except Exception as e:
            print(f"Debug - Error in documentation _update_priority: {e}")
            return 0


admin.site.register(MongoAIExplanation, AIExplanationAdmin)
admin.site.register(MongoCodeFile, CodeFileAdmin)
admin.site.register(MongoAnalysisResult, AnalysisResultAdmin)
admin.site.register(MongoAnalysisJob, AnalysisJobAdmin)
admin.site.register(MongoAITask, AITaskAdmin)
admin.site.register(MongoGeneratedFile, GeneratedFileAdmin)  # تم تفعيل عرض الملفات المولدة
admin.site.register(MongoDocumentationFile, DocumentationFileAdmin)

admin.site.site_header = "AI Project Administration"
admin.site.site_title = "AI Project Admin"
admin.site.index_title = "Welcome to AI Project Administration"