import logging
import threading
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.core.exceptions import ValidationError, PermissionDenied
from core_upm.tokens import RoleAwareRefreshToken
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

logger = logging.getLogger(__name__)

from core_upm.business_logic import UserService
from core_upm.serializers import UserRegistrationSerializer, UserSerializer
from rest_framework import viewsets
from django.contrib.auth.models import User


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]


# ── إرسال notification في الخلفية بعد التسجيل ───────────────────────────────
def _send_signup_notification_async(user_email: str, user_name: str):
    """
    يُشغَّل في thread منفصل — لو الـ Notification Service بطيئة
    ما يأثر على سرعة الـ signup.
    """
    try:
        from core_upm.notification_utils import NotificationClient
        NotificationClient.send_user_notification(
            user_email=user_email,
            action='registered',
            user_name=user_name
        )
    except Exception as e:
        logger.warning(f"Signup notification failed (non-critical): {e}")


@method_decorator(csrf_exempt, name='dispatch')
class UserRegistrationAPIView(APIView):
    permission_classes = [AllowAny]
    user_service = UserService()

    def post(self, request):
        try:
            # ✅ نقرأ request.data مرة واحدة فقط ونحفظها
            request_data = request.data

            serializer = UserRegistrationSerializer(data=request_data)
            if serializer.is_valid():
                try:
                    password = serializer.validated_data.pop('password')
                    user = self.user_service.register_new_user(
                        serializer.validated_data, password
                    )

                    logger.info(f"Signup successful for user: {user.username}")

                    # ✅ إرسال الـ notification في thread منفصل — يرجع الرد فوراً
                    threading.Thread(
                        target=_send_signup_notification_async,
                        args=(user.email, user.username),
                        daemon=True
                    ).start()

                    return Response(
                        UserSerializer(user).data,
                        status=status.HTTP_201_CREATED
                    )

                except ValidationError as e:
                    logger.warning(f"Signup validation error: {str(e)}")
                    return Response(
                        {'detail': str(e)},
                        status=status.HTTP_400_BAD_REQUEST
                    )

            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        except Exception as e:
            logger.error(f"Unexpected error in signup: {e}", exc_info=True)
            return Response(
                {'detail': f'An unexpected error occurred: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@method_decorator(csrf_exempt, name='dispatch')
class UserLoginAPIView(APIView):
    permission_classes = [AllowAny]
    user_service = UserService()

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')

        logger.info(f"Login attempt: {username}")

        try:
            user = self.user_service.authenticate_user(username, password)

            # تحديث last_seen
            try:
                from django.utils import timezone
                profile = user.profile
                profile.last_seen = timezone.now()
                profile.is_online = True
                profile.save(update_fields=['last_seen', 'is_online'])
            except Exception:
                pass

            refresh = RoleAwareRefreshToken.for_user(user)

            logger.info(f"Login successful: {username}")
            return Response({
                'refresh':   str(refresh),
                'access':    str(refresh.access_token),
                'role_type': refresh.payload.get('role_type', 'DEVELOPER'),
                'full_name': refresh.payload.get('full_name', ''),
                'user':      UserSerializer(user).data
            }, status=status.HTTP_200_OK)

        except PermissionDenied as e:
            logger.warning(f"Login failed for '{username}': {str(e)}")
            return Response(
                {'detail': str(e)},
                status=status.HTTP_401_UNAUTHORIZED
            )

        except Exception as e:
            logger.error(f"Login unexpected error: {e}")
            return Response(
                {'detail': 'An unexpected error occurred during login.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )