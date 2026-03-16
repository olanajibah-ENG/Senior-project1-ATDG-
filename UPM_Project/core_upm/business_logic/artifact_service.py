from django.core.exceptions import PermissionDenied, ValidationError
from core_upm.repositories import ArtifactRepository, ProjectRepository
from django.contrib.auth.models import User
from core_upm.models.artifact import CodeArtifact

class ArtifactService:
    """
    Handles CodeArtifact business logic, ensuring content is saved externally.
    Uses ArtifactRepository and ProjectRepository for data access.
    """
    def __init__(self):
        self.project_repo = ProjectRepository()
        self.artifact_repo = ArtifactRepository()
    
    def create_artifact_in_project(self, project_id: str, user: User, artifact_data: dict) -> CodeArtifact:
     
        # 1. Retrieve project and check permission (using project repo)
        project = self.project_repo.get_project_by_id(project_id)
        
        if project.user != user:
            raise PermissionDenied("Permission denied: You do not own this project.")

        content = artifact_data.pop('code_content') 
        file_name=artifact_data['file_name']  
        code_language = artifact_data['code_language'] 
        if not content:
            raise ValidationError("Code content cannot be empty.")
            
        # 2. Save content to external storage (using artifact repo)
        storage_ref = self.artifact_repo.save_content_externally(content,project_id,file_name,code_language)

        # 3. Save artifact metadata (using artifact repo)
        artifact = self.artifact_repo.create_artifact(
            project=project,
            file_name=file_name,
            code_language=code_language,
            code_version=artifact_data.get('code_version', None),
            storage_reference=storage_ref 
        )
        return artifact

    def get_project_artifacts(self, project_id: str, user: User):
        """Retrieves artifact metadata, ensuring user access to the project."""
        project = self.project_repo.get_project_by_id(project_id)
        
        if project.user != user:
            raise PermissionDenied("Access denied to artifacts in this project.")
            
        return self.artifact_repo.get_artifacts_by_project(project)

    def retrieve_artifact_with_content(self, code_id: str, user: User):
        """Retrieves artifact and fetches content from external storage."""
        artifact = self.artifact_repo.get_artifact_by_id(code_id)

        # Business Logic: Check project ownership
        if artifact.project.user != user:
            raise PermissionDenied("Access denied to this artifact.")
            
        # Repository task: Fetch actual code content
        content = self.artifact_repo.fetch_content_externally(artifact.storage_reference)
        
        # Attach the content temporarily for the View layer
        artifact.code_content = content 

        return artifact

    def get_artifact_by_id_if_authorized(self, code_id: str, user: User) -> CodeArtifact:
        """
        Retrieves artifact and checks project ownership.
        """
        artifact = self.artifact_repo.get_artifact_by_id(code_id)

        if artifact.project.user != user:
            raise PermissionDenied("Access denied: You do not own this artifact.")
            
        return artifact
        
    def update_artifact_metadata(self, artifact: CodeArtifact, new_data: dict) -> CodeArtifact:
        """
        Updates artifact metadata using validated data (no content update here).
        """
        # إذا تم تمرير project_id، تأكد أنه يتطابق مع المشروع الحالي (لا يُسمح بتغيير المشروع عبر تحديث الـ metadata)
        if 'project' in new_data:
            del new_data['project'] # منع تحديث حقل المشروع عبر الـ PUT/PATCH

        # يمكن استخدام دالة save في Django Model مباشرة بعد تحديث الحقول
        for key, value in new_data.items():
            setattr(artifact, key, value)
            
        artifact.save()
        return artifact

    def delete_artifact(self, code_id: str, user: User) -> None:
        """
        Deletes the artifact after checking permission and handling external storage cleanup.
        """
        artifact = self.get_artifact_by_id_if_authorized(code_id, user)
        # الـ Repository الآن سيتولى حذف MongoDB ثم MySQL
        self.artifact_repo.delete_artifact(artifact)