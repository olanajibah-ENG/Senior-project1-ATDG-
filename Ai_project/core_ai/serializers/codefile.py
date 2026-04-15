from rest_framework import serializers
from core_ai.models.codefile import CodeFile, PyObjectId
from core_ai.mongo_utils import get_mongo_db
from django.conf import settings
from bson import ObjectId

class ObjectIdField(serializers.Field):
    """
    Serializer field for MongoDB ObjectId.
    """
    def to_representation(self, value):
        return str(value)

    def to_internal_value(self, data):
        try:
            return PyObjectId(data)
        except ValueError:
            raise serializers.ValidationError("Invalid ObjectId format.")

class CodeFileSerializer(serializers.Serializer):
    id = ObjectIdField(read_only=True)
    filename = serializers.CharField(max_length=255)
    file_type = serializers.CharField(max_length=50)
    content = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    code_content = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    uploaded_at = serializers.DateTimeField(read_only=True)
    source_project_id = serializers.CharField(max_length=255, required=False, allow_null=True)
    analysis_status = serializers.CharField(read_only=True)
    uploaded_file = serializers.FileField(required=False, write_only=True)
    # الحقل الجديد الذي استدعيناه
    analysis_id = serializers.SerializerMethodField()

    def get_analysis_id(self, obj):
        try:
            # التحقق من وجود المعرف
            file_id = getattr(obj, 'id', None)
            if not file_id:
                if isinstance(obj, dict):
                    file_id = obj.get('id') or obj.get('_id')
            
            if not file_id:
                return None

            db = get_mongo_db()
            if db is not None:
                collection_name = getattr(settings, 'ANALYSIS_RESULTS_COLLECTION', 'analysis_results')
                collection = db[collection_name]
                
                # البحث عن النتيجة التي ترتبط بهذا الملف
                # code_file_id قد يكون ObjectId أو String، نأخذ الحالتين بالاعتبار
                result = collection.find_one({
                    "$or": [
                        {"code_file_id": ObjectId(file_id)},
                        {"code_file_id": str(file_id)}
                    ]
                })
                
                if result and '_id' in result:
                    return str(result['_id'])
                    
        except Exception as e:
            # في حال حدوث أي خطأ، نعيد null
            print(f"Error fetching analysis_id in CodeFileSerializer: {str(e)}")
            return None
            
        return None

    def validate(self, data):
        """
        التحقق المخصص للتأكد من وجود إما content أو code_content أو uploaded_file
        """
        content_provided = ('content' in data and data.get('content') is not None) or \
                          ('code_content' in data and data.get('code_content') is not None)
        file_provided = 'uploaded_file' in data and data.get('uploaded_file')

        if content_provided and file_provided:
            raise serializers.ValidationError(
                "Please provide either 'content'/'code_content' or 'uploaded_file', not both."
            )

        if not content_provided and not file_provided:
            raise serializers.ValidationError(
                "Either 'content'/'code_content' (raw text) or 'uploaded_file' must be provided."
            )

        return data

    def create(self, validated_data):
    
        if 'code_content' in validated_data and validated_data.get('code_content'):
            validated_data['content'] = validated_data.pop('code_content')

        return CodeFile(**validated_data)

    def update(self, instance, validated_data):
       
        if 'code_content' in validated_data and validated_data.get('code_content'):
            validated_data['content'] = validated_data.pop('code_content')

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        return instance
