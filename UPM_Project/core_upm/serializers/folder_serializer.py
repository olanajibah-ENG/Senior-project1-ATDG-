from rest_framework import serializers
from core_upm.models.folder import Folder


class FolderSerializer(serializers.ModelSerializer):
    """
    Serializer للـ Folder — يدعم CRUD كامل.
    """
    # حقول read-only لعرض أسماء العلاقات بدل الـ IDs فقط
    repo_name = serializers.CharField(source='repo.repo_name', read_only=True, default=None)
    project_name = serializers.CharField(source='project.project_name', read_only=True)
    parent_folder_name = serializers.CharField(source='parent_folder.folder_name', read_only=True, default=None)

    class Meta:
        model = Folder
        fields = [
            'folder_id',
            'folder_name',
            'folder_path',
            'project',
            'project_name',
            'repo',
            'repo_name',
            'parent_folder',
            'parent_folder_name',
        ]
        read_only_fields = ['folder_id', 'project_name', 'repo_name', 'parent_folder_name']