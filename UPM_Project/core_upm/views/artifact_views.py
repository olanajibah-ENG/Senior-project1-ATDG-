from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.core.exceptions import PermissionDenied, ValidationError
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from core_upm.business_logic import artifact_service_instance
from core_upm.business_logic import artifact_service_instance
from core_upm.serializers import CodeArtifactSerializer, CodeArtifactDetailSerializer
from core_upm.models.artifact import CodeArtifact
from core_upm.notification_utils import NotificationClient 

@method_decorator(csrf_exempt, name='dispatch')
class ArtifactRetrieveUpdateDestroyAPIView(APIView):
    """View for retrieving, updating, and deleting individual code artifacts."""
    permission_classes = [IsAuthenticated]

    def __init__(self, **kwargs):
       super().__init__(**kwargs)
       self.artifact_service = artifact_service_instance

    def get(self, request, code_id):
        # Retrieve the Artifact
        try:
            artifact = self.artifact_service.retrieve_artifact_with_content(code_id, request.user)
            serializer = CodeArtifactDetailSerializer(artifact) 
            return Response(serializer.data)
        except PermissionDenied as e:
            return Response({"detail": str(e)}, status=status.HTTP_403_FORBIDDEN)
        except CodeArtifact.DoesNotExist: 
            return Response({"detail": "Artifact not found."}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, code_id):
        # To update the Artifact
        try:
            # 1. Get the Artifact and check permissions (added in service layer)
            artifact = self.artifact_service.get_artifact_by_id_if_authorized(code_id, request.user)
            
            # 2. Use CodeArtifactSerializer to modify metadata only
            # Use partial=True to allow partial updates
            serializer = CodeArtifactSerializer(artifact, data=request.data, partial=True) 
            
            if serializer.is_valid():
                # 3. Pass data to service layer for update (added in service layer)
                updated_artifact = self.artifact_service.update_artifact_metadata(artifact, serializer.validated_data) 
                return Response(CodeArtifactSerializer(updated_artifact).data)
                
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except PermissionDenied as e:
            return Response({"detail": str(e)}, status=status.HTTP_403_FORBIDDEN)
        except ValidationError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except CodeArtifact.DoesNotExist:
            return Response({"detail": "Artifact not found."}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, code_id):
        # To delete the Artifact (Destroy)
        try:
            # Get code information before deletion for notification
            artifact = self.artifact_service.get_artifact_by_id_if_authorized(code_id, request.user)
            code_name = artifact.code_name or f"Code {artifact.code_id}"

            # Service layer handles deletion and ownership verification (added in service layer)
            self.artifact_service.delete_artifact(code_id, request.user)

            # Send code deletion notification
            try:
                NotificationClient.send_code_notification(
                    user_email=request.user.email,
                    action='deleted',
                    code_name=code_name,
                    project_name="",  # We may need to get the project name
                    code_id=str(code_id),
                    user_name=request.user.username
                )
            except Exception as e:
                # We don't want notification failure to affect the success of the main operation
                pass

            return Response(status=status.HTTP_204_NO_CONTENT)
        except PermissionDenied as e:
            return Response({"detail": str(e)}, status=status.HTTP_403_FORBIDDEN)
        except CodeArtifact.DoesNotExist:
            return Response({"detail": "Artifact not found."}, status=status.HTTP_404_NOT_FOUND)

@method_decorator(csrf_exempt, name='dispatch')
class ArtifactListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.artifact_service = artifact_service_instance

    def get(self, request, project_id):
        # Get all Artifacts for a specific project
        try:
            artifacts = self.artifact_service.get_project_artifacts(project_id, request.user)
            serializer = CodeArtifactSerializer(artifacts, many=True)
            return Response(serializer.data)
        except PermissionDenied as e:
            return Response({"detail": str(e)}, status=status.HTTP_403_FORBIDDEN)
        except ValidationError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    # core_upm/views/artifact_views.py (continuation of post function)

    def post(self, request, project_id):
        # 1. Extract code content first (since it's not part of CodeArtifactSerializer)
        data = request.data.copy()
        code_content = data.pop('code_content', None) # Assume JSON, so use None

        # 2. Create Serializer with remaining data (Metadata)
        serializer = CodeArtifactSerializer(data=data)

        # 3. Double validation of data (Metadata + Content/File)
        is_metadata_valid = serializer.is_valid()

        # Check if content exists either from code_content or uploaded_file
        has_code_content = code_content is not None and code_content.strip()
        has_uploaded_file = 'uploaded_file' in request.data and request.data['uploaded_file']
        is_content_provided = has_code_content or has_uploaded_file

        # Validate data
        if is_metadata_valid and is_content_provided:
            try:
                validated_data = serializer.validated_data

                # Handle uploaded file if present
                if has_uploaded_file:
                    uploaded_file = request.data['uploaded_file']
                    try:
                        file_content = uploaded_file.read().decode('utf-8')
                        validated_data['code_content'] = file_content
                    except Exception as e:
                        return Response({"error": f"Failed to read uploaded file: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
                else:
                    # Use direct code_content from JSON
                    validated_data['code_content'] = code_content 
                
                # Call service layer that handles saving external content and local metadata
                artifact = self.artifact_service.create_artifact_in_project(
                    project_id,
                    request.user,
                    validated_data
                )

                # Send code addition success notification
                try:
                    NotificationClient.send_code_notification(
                        user_email=request.user.email,
                        action='added',
                        code_name=artifact.code_name or f"Code {artifact.code_id}",
                        project_name="",  # We may need to get the project name
                        code_id=str(artifact.code_id),
                        user_name=request.user.username
                    )
                except Exception as e:
                    # We don't want notification failure to affect the success of the main operation
                    pass

                return Response(CodeArtifactSerializer(artifact).data, status=status.HTTP_201_CREATED)
            
            except PermissionDenied as e:
                return Response({"detail": str(e)}, status=status.HTTP_403_FORBIDDEN)
            
            # Catch ValidationError from either Serializer (if error occurs after is_valid)
            # or from Service/Repository layer (external connection failure or internal validation)
            except ValidationError as e:
                # If the problem is AI service connection failure, Repo raises ValidationError
                return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        # 4. Handle errors if Serializer is invalid or content is missing
        if not is_content_provided:
            # Add custom error if content was not provided
            if not is_metadata_valid:
                # If Serializer is also invalid, add 'code_content' field to existing error list
                serializer.errors['code_content'] = ["Either 'code_content' (raw text) or 'uploaded_file' must be provided."]
            else:
                # If Serializer is valid but content is missing, create new error dict
                return Response({'code_content': ["Either 'code_content' (raw text) or 'uploaded_file' must be provided."]}, status=status.HTTP_400_BAD_REQUEST)

        # Respond with standard Serializer errors
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)