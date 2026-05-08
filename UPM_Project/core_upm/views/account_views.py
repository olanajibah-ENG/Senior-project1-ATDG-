import logging

from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core_upm.models.user import UserProfile
from core_upm.permissions import IsAdminRole, IsAdminOrReviewer
from core_upm.serializers.user_serializer import (
    UserDetailSerializer,
    ReviewerCreateSerializer,
    ChangePasswordSerializer,
)

logger = logging.getLogger(__name__)


class AdminUserListView(APIView):
    permission_classes = [IsAdminRole]

    def get(self, request):
        queryset = User.objects.select_related('profile__role').all()

        role_filter = request.query_params.get('role')
        if role_filter:
            queryset = queryset.filter(profile__role__role_type=role_filter)

        online_filter = request.query_params.get('online')
        if online_filter == 'true':
            from django.utils import timezone
            from datetime import timedelta

            cutoff = timezone.now() - timedelta(minutes=5)
            queryset = queryset.filter(profile__last_seen__gte=cutoff)

        serializer = UserDetailSerializer(queryset, many=True)
        return Response(serializer.data)


class AdminCreateReviewerView(APIView):
    permission_classes = [IsAdminRole]

    def post(self, request):
        serializer = ReviewerCreateSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response(
                {
                    'message': 'Reviewer account created successfully.',
                    'user': UserDetailSerializer(user).data,
                },
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AdminToggleUserActiveView(APIView):
    permission_classes = [IsAdminRole]

    def patch(self, request, user_id):
        target_user = get_object_or_404(User, id=user_id)

        try:
            if target_user.profile.role_type == 'ADMIN':
                return Response(
                    {'detail': 'Cannot deactivate another Admin account.'},
                    status=status.HTTP_403_FORBIDDEN,
                )
        except Exception:
            pass

        if target_user == request.user:
            return Response(
                {'detail': 'Cannot deactivate your own account.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        target_user.is_active = not target_user.is_active
        target_user.save()

        action = 'activated' if target_user.is_active else 'deactivated'
        return Response(
            {
                'message': f'User {target_user.username} has been {action}.',
                'is_active': target_user.is_active,
            }
        )


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = request.user
        old_password = serializer.validated_data['old_password']
        new_password = serializer.validated_data['new_password']

        if not user.check_password(old_password):
            return Response(
                {'detail': 'Current password is incorrect.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.set_password(new_password)
        user.save()

        # Note: token_blacklist is not enabled in settings.
        # If you enable it later, you can blacklist the refresh token with:
        # RefreshToken(request.data.get('refresh')).blacklist()

        return Response({'message': 'Password changed successfully.'})


class OnlineUsersView(APIView):
    permission_classes = [IsAdminOrReviewer]

    def get(self, request):
        from django.utils import timezone
        from datetime import timedelta

        cutoff = timezone.now() - timedelta(minutes=5)

        online_profiles = UserProfile.objects.filter(
            last_seen__gte=cutoff
        ).select_related('user', 'role')

        users_data = [
            {
                'username': p.user.username,
                'full_name': p.full_name,
                'role_type': p.role_type,
                'last_seen': p.last_seen,
            }
            for p in online_profiles
        ]

        return Response({'online_count': len(users_data), 'users': users_data})
