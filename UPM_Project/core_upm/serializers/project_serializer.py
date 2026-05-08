from rest_framework import serializers
from core_upm.models.project import Project


class ProjectListCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for listing and creating projects.
    Maps API fields (id, title, description, created_at, updated_at) 
    to model fields (project_id, project_name, project_description, creation_date, last_modified_date).
    """
    id = serializers.UUIDField(source='project_id', read_only=True)
    title = serializers.CharField(source='project_name', max_length=255)
    description = serializers.CharField(source='project_description', required=False, allow_blank=True)
    created_at = serializers.DateTimeField(source='creation_date', read_only=True)
    updated_at = serializers.DateTimeField(source='last_modified_date', read_only=True)
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = Project
        fields = ['id', 'title', 'description', 'user', 'username', 'created_at', 'updated_at']
        read_only_fields = ['id', 'user', 'username', 'created_at', 'updated_at']


    def validate_title(self, value):
        """Validate that title is provided and not empty."""
        if not value or not value.strip():
            raise serializers.ValidationError("Title is required and cannot be empty.")
        return value.strip()


class ProjectRetrieveUpdateDestroySerializer(serializers.ModelSerializer):
    """
    Serializer for retrieving, updating, and deleting projects.
    Maps API fields (id, title, description, created_at, updated_at) 
    to model fields (project_id, project_name, project_description, creation_date, last_modified_date).
    """
    id = serializers.UUIDField(source='project_id', read_only=True)
    title = serializers.CharField(source='project_name', max_length=255, required=False)
    description = serializers.CharField(source='project_description', required=False, allow_blank=True)
    created_at = serializers.DateTimeField(source='creation_date', read_only=True)
    updated_at = serializers.DateTimeField(source='last_modified_date', read_only=True)
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = Project
        fields = ['id', 'title', 'description', 'user', 'username', 'created_at', 'updated_at']
        read_only_fields = ['id', 'user', 'username', 'created_at', 'updated_at']

    def validate_title(self, value):
        """Validate that title is not empty if provided."""
        if value is not None and (not value or not value.strip()):
            raise serializers.ValidationError("Title cannot be empty.")
        return value.strip() if value else value
