from rest_framework import serializers
from core_upm.models import CodeArtifact 

class CodeArtifactSerializer(serializers.ModelSerializer):
    """
    Serializer for CodeArtifact listing/upload. 
    Uses storage_reference instead of code_content.
    """
    project_name = serializers.CharField(source='project.project_name', read_only=True)
    # version_number مأخوذ من الـ FK بدل code_version اللي اتحذف من الموديل
    version_number = serializers.IntegerField(source='version.version_number', read_only=True)

    class Meta:
        model = CodeArtifact
        fields = [
            'code_id', 'project_name', 'file_name',
            'upload_date', 'code_language', 'version_number', 'storage_reference'
        ]
        read_only_fields = ['code_id', 'project_name', 'upload_date', 'storage_reference', 'version_number']


class CodeArtifactDetailSerializer(serializers.ModelSerializer):
    """
    Serializer to show full artifact details, including the storage reference.
    """
    project_name = serializers.CharField(source='project.project_name', read_only=True)
    # version_number مأخوذ من الـ FK بدل code_version اللي اتحذف من الموديل
    version_number = serializers.IntegerField(source='version.version_number', read_only=True)

    class Meta:
        model = CodeArtifact
        fields = [
            'code_id', 'project_name', 'file_name', 'upload_date',
            'code_language', 'version_number', 'storage_reference'
        ]
        read_only_fields = [
            'code_id', 'project_name', 'upload_date',
            'code_language', 'version_number', 'storage_reference'
        ]