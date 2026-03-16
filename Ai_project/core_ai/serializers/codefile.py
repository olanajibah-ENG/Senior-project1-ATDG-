from rest_framework import serializers
from core_ai.models.codefile import CodeFile, PyObjectId

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

