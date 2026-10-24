from rest_framework import serializers
from core_ai.models.analysis import  AnalysisJob, AnalysisResult
from core_ai.serializers.codefile import ObjectIdField

class AnalysisJobSerializer(serializers.Serializer):
    id = ObjectIdField(read_only=True)
    code_file_id = ObjectIdField()
    status = serializers.CharField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    started_at = serializers.DateTimeField(read_only=True, allow_null=True)
    completed_at = serializers.DateTimeField(read_only=True, allow_null=True)
    error_message = serializers.CharField(required=False, allow_null=True)

    def create(self, validated_data):
        return AnalysisJob(**validated_data)

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        return instance


class AnalysisResultSerializer(serializers.Serializer):
    id = ObjectIdField(read_only=True)
    code_file_id = ObjectIdField()
    analysis_started_at = serializers.DateTimeField(read_only=True)
    analysis_completed_at = serializers.DateTimeField(read_only=True, allow_null=True)
    status = serializers.CharField(read_only=True)
    ast_structure = serializers.JSONField(required=False, allow_null=True)
    extracted_features = serializers.JSONField(required=False, allow_null=True)
    dependencies = serializers.ListField(required=False, allow_null=True,child=serializers.CharField(),default=[])
    dependency_graph = serializers.JSONField(required=False, allow_null=True,default=None)
    semantic_analysis_data = serializers.JSONField(required=False, allow_null=True)
    class_diagram_data = serializers.JSONField(required=False, allow_null=True)

    def create(self, validated_data):
        return AnalysisResult(**validated_data)

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        return instance
