import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.core.exceptions import ValidationError, PermissionDenied
from rest_framework_simplejwt.tokens import RefreshToken # لاستخدام نظام التوكن
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
    
@method_decorator(csrf_exempt, name='dispatch')
class UserRegistrationAPIView(APIView):
    # السماح لأي مستخدم (غير مصادق) بالوصول لصفحة التسجيل
    permission_classes = [AllowAny]
    user_service = UserService()

    def post(self, request):
        try:
            logger.info(f"=== SIGNUP REQUEST RECEIVED ===")
            logger.info(f"Signup attempt from {request.META.get('REMOTE_ADDR', 'unknown')}")
            logger.info(f"Request method: {request.method}")
            logger.info(f"Content-Type: {request.content_type}")
            logger.info(f"Request headers: {dict(request.headers)}")
            
            # Try to access request data safely
            try:
                request_data = request.data
                logger.info(f"Request data (parsed): {request_data}")
            except Exception as e:
                logger.error(f"Error parsing request.data: {e}")
                # Fallback to request.POST or request.body
                if hasattr(request, 'POST') and request.POST:
                    request_data = request.POST.dict()
                    logger.info(f"Using request.POST: {request_data}")
                elif hasattr(request, 'body'):
                    logger.info(f"Request body (raw): {request.body}")
                    request_data = {}
                else:
                    request_data = {}
            
            username = request_data.get('username') if isinstance(request_data, dict) else None
            email = request_data.get('email') if isinstance(request_data, dict) else None
            password = request_data.get('password') if isinstance(request_data, dict) else None
            
            logger.info(f"Extracted - Username: {username}, Email: {email}, Password provided: {bool(password)}")
            
            serializer = UserRegistrationSerializer(data=request_data)
            if serializer.is_valid():
                try:
                    # فصل كلمة المرور للتعامل معها بشكل آمن في الـ Service
                    password = serializer.validated_data.pop('password')
                    user = self.user_service.register_new_user(serializer.validated_data, password)
                    
                    logger.info(f"Signup successful for user: {username}")
                    # إرجاع بيانات المستخدم (باستخدام UserSerializer للعرض)
                    return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)
                except ValidationError as e:
                    logger.warning(f"Signup failed for user '{username}': {str(e)}")
                    return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
            
            logger.warning(f"Signup validation failed for user '{username}': {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Unexpected error in signup view: {e}", exc_info=True)
            return Response({'detail': f'An unexpected error occurred: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@method_decorator(csrf_exempt, name='dispatch')
class UserLoginAPIView(APIView):
    permission_classes = [AllowAny]
    user_service = UserService()

    def post(self, request):
        logger.info(f"Login attempt from {request.META.get('REMOTE_ADDR')}")
        logger.info(f"Request data: {request.data}")
        logger.info(f"Request headers: {dict(request.headers)}")

        username = request.data.get('username')
        password = request.data.get('password')

        logger.info(f"Username: {username}, Password provided: {bool(password)}")

        try:
            user = self.user_service.authenticate_user(username, password)

            # إنشاء JWT Tokens (إذا كنت تستخدم Django REST Framework Simple JWT)
            refresh = RefreshToken.for_user(user)

            logger.info(f"Login successful for user: {username}")
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user': UserSerializer(user).data
            }, status=status.HTTP_200_OK)

        except PermissionDenied as e:
            logger.warning(f"Login failed for user '{username}': {str(e)}")
            return Response({'detail': str(e)}, status=status.HTTP_401_UNAUTHORIZED)

        except Exception as e:
            logger.error(f"Login unexpected error: {e}")
            return Response({'detail': 'An unexpected error occurred during login.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)