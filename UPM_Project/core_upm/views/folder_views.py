from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from core_upm.permissions import IsDeveloperRole
from core_upm.models.folder import Folder
from core_upm.models.project import Project
from core_upm.serializers.folder_serializer import FolderSerializer


@method_decorator(csrf_exempt, name='dispatch')
class FolderListCreateAPIView(APIView):
    """
    GET  /projects/<project_id>/folders/  — قائمة كل الـ folders في مشروع
    POST /projects/<project_id>/folders/  — إنشاء folder جديد
    """
    permission_classes = [IsAuthenticated,IsDeveloperRole]

    def get(self, request, project_id):
        # التحقق إن المشروع موجود وتابع للمستخدم
        project = get_object_or_404(Project, project_id=project_id)
        if project.user != request.user:
            return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)

        folders = Folder.objects.filter(project=project)
        serializer = FolderSerializer(folders, many=True)
        return Response(serializer.data)

    def post(self, request, project_id):
        # التحقق إن المشروع موجود وتابع للمستخدم
        project = get_object_or_404(Project, project_id=project_id)
        if project.user != request.user:
            return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)

        # نضيف الـ project تلقائياً من الـ URL
        data = request.data.copy()
        data['project'] = str(project_id)

        serializer = FolderSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@method_decorator(csrf_exempt, name='dispatch')
class FolderRetrieveUpdateDestroyAPIView(APIView):
    """
    GET    /folders/<folder_id>/  — تفاصيل folder معين
    PUT    /folders/<folder_id>/  — تعديل folder
    DELETE /folders/<folder_id>/  — حذف folder
    """
    permission_classes = [IsAuthenticated,IsDeveloperRole]

    def _get_folder(self, folder_id, user):
        """جلب الـ folder والتحقق من الصلاحية."""
        folder = get_object_or_404(Folder, folder_id=folder_id)
        if folder.project.user != user:
            raise PermissionDenied("Permission denied.")
        return folder

    def get(self, request, folder_id):
        try:
            folder = self._get_folder(folder_id, request.user)
            serializer = FolderSerializer(folder)
            return Response(serializer.data)
        except PermissionDenied as e:
            return Response({"detail": str(e)}, status=status.HTTP_403_FORBIDDEN)

    def put(self, request, folder_id):
        try:
            folder = self._get_folder(folder_id, request.user)
            serializer = FolderSerializer(folder, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except PermissionDenied as e:
            return Response({"detail": str(e)}, status=status.HTTP_403_FORBIDDEN)

    def delete(self, request, folder_id):
        try:
            folder = self._get_folder(folder_id, request.user)
            folder.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except PermissionDenied as e:
            return Response({"detail": str(e)}, status=status.HTTP_403_FORBIDDEN)