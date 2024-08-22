from django.shortcuts import render
from django.http import JsonResponse
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils import timezone
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.db.models import Sum
from django.middleware import csrf
from django.core.exceptions import ObjectDoesNotExist

# Restframework
from rest_framework import status, viewsets
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.decorators import api_view, APIView, permission_classes
from rest_framework.response import Response
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework import generics
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from datetime import datetime

from django.shortcuts import get_object_or_404
from django.db.models import F

# Others
import json
import random
import os

# Custom Imports
from api import serializer as api_serializer
from api import models as api_models
from openai import OpenAI
from django.conf import settings
from api.pinecone_client import query_pinecone 
from api.openai_client import get_embedding
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    api_key="sk-vgLu1doy0UFV1BaLFtlsVFNTYcRMQylp",
    base_url="https://api.proxyapi.ru/openai/v1",
)

def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }

class LoginView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request, format=None):
        print('request.data: ',request.data)
        data = request.data
        response = Response()
        email = data.get('email', None)
        password = data.get('password', None)
        user = authenticate(email=email, password=password)
        
        if user is not None:
            if user.is_active:
                tokens = get_tokens_for_user(user)
                response.set_cookie(
                    key = settings.SIMPLE_JWT['AUTH_COOKIE'],
                    value = tokens['access'],
                    expires = settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'],
                    secure = settings.SIMPLE_JWT['AUTH_COOKIE_SECURE'],
                    httponly = False,
                    samesite = settings.SIMPLE_JWT['AUTH_COOKIE_SAMESITE']
                )
                response.set_cookie(
                    key=settings.SIMPLE_JWT['AUTH_COOKIE_REFRESH'],
                    value=tokens['refresh'],
                    expires=settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'],
                    secure=settings.SIMPLE_JWT['AUTH_COOKIE_SECURE'],
                    httponly=settings.SIMPLE_JWT['AUTH_COOKIE_HTTP_ONLY'],
                    samesite=settings.SIMPLE_JWT['AUTH_COOKIE_SAMESITE']
                )
                csrf.get_token(request)
                response.data = {'Success': 'Login successfully', 'access': tokens['access']}
                return response
            else:
                return Response({'No active': 'This account is not active!'}, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({'Invalid': 'Invalid email or password!'}, status=status.HTTP_404_NOT_FOUND)
        
class RefreshTokenView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request, format=None):
        refresh_token = request.COOKIES.get(settings.SIMPLE_JWT['AUTH_COOKIE_REFRESH'])
        if refresh_token is None:
            return Response({'Error': 'No refresh token provided'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            refresh = RefreshToken(refresh_token)
            access_token = refresh.access_token
            response = Response()
            response.set_cookie(
                key=settings.SIMPLE_JWT['AUTH_COOKIE'],
                value=str(access_token),
                expires=settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'],
                secure=settings.SIMPLE_JWT['AUTH_COOKIE_SECURE'],
                httponly=settings.SIMPLE_JWT['AUTH_COOKIE_HTTP_ONLY'],
                samesite=settings.SIMPLE_JWT['AUTH_COOKIE_SAMESITE']
            )
            response.data = {'access': str(access_token)}
            return response
        except Exception as e:
            return Response({'Error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, format=None):
        response = Response()
        response.delete_cookie(settings.SIMPLE_JWT['AUTH_COOKIE'])
        response.delete_cookie(settings.SIMPLE_JWT['AUTH_COOKIE_REFRESH'])
        response.data = {'Success': 'Logged out successfully'}
        return response

# class MyTokenObtainPairView(TokenObtainPairView):
#     serializer_class = api_serializer.MyTokenObtainPairSerializer

# class MyTokenObtainPairView(TokenObtainPairView):
#     serializer_class = api_serializer.MyTokenObtainPairSerializer

    # def post(self, request, *args, **kwargs):
    #     serializer = self.get_serializer(data=request.data)
    #     try:
    #         serializer.is_valid(raise_exception=True)
    #     except:
    #         return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
        
    #     data = serializer.validated_data
    #     user = serializer.user
    #     refresh = data['refresh']
    #     access = data['access']
        
    #     refresh_token = serializer.get_token(user)
    #     exp_timestamp = refresh_token.payload['exp']
    #     exp_date = datetime.fromtimestamp(exp_timestamp, timezone.utc)
        
    #     response = Response(data={'access': access}, status=status.HTTP_200_OK)
        
    #     response.set_cookie(
    #         key='refresh',
    #         value=refresh,
    #         expires=exp_date,
    #         secure=False,  # True для production с HTTPS
    #         httponly=True,
    #         samesite='Lax'  # Изменено с 'Strict' на 'Lax'
    #     )

    #     return response

    # def post(self, request, *args, **kwargs):
    #     response = super().post(request, *args, **kwargs)
    #     print('response: ', response.data)
    #     refresh_token = response.data.get('refresh')
    #     access_token = response.data.get('access')

    #     # if refresh_token:
    #     #     expires_in = timezone.now() + settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME']
    #     #     response.set_cookie(
    #     #         key=settings.SIMPLE_JWT['AUTH_COOKIE'],
    #     #         value=refresh_token,
    #     #         expires=expires_in,
    #     #         secure=settings.SIMPLE_JWT['AUTH_COOKIE_SECURE'],
    #     #         httponly=True,
    #     #         samesite=settings.SIMPLE_JWT['AUTH_COOKIE_SAMESITE'],
    #     #     )
    #         # Убираем refresh token из тела ответа
    #     del response.data['refresh']

    #     # Проверка наличия access токена
    #     if not access_token:
    #         return Response({"detail": "Access token not found"}, status=status.HTTP_400_BAD_REQUEST)

    #     return response

class RegisterView(generics.CreateAPIView):
    queryset = api_models.User.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = api_serializer.RegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)

        response_data = {
            'access': access_token,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
            }
        }

        response = Response(response_data, status=status.HTTP_201_CREATED)
        expires_in = timezone.now() + settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME']
        response.set_cookie(
            key=settings.SIMPLE_JWT['AUTH_COOKIE'],
            value=refresh_token,
            expires=expires_in,
            secure=settings.SIMPLE_JWT['AUTH_COOKIE_SECURE'],
            httponly=True,
            samesite=settings.SIMPLE_JWT['AUTH_COOKIE_SAMESITE'],
        )
        return response

# class TokenRefreshView(APIView):
#     def post(self, request, *args, **kwargs):
#         refresh_token = request.COOKIES.get(settings.SIMPLE_JWT['AUTH_COOKIE'])
#         print('refresh_token: ', refresh_token)
#         if not refresh_token:
#             return Response({"detail": "Refresh token not found in cookies"}, status=status.HTTP_400_BAD_REQUEST)

#         try:
#             refresh = RefreshToken(refresh_token)
#             print('refresh: ', refresh)
#             access_token = refresh.access_token
#             response_data = {'access': str(access_token)}
#             return Response(response_data, status=status.HTTP_200_OK)
#         except TokenError as e:
#             raise InvalidToken(e.args[0])

# class LogoutView(APIView):
#     permission_classes = (AllowAny,)

#     @swagger_auto_schema(
#         request_body=openapi.Schema(
#             type=openapi.TYPE_OBJECT,
#             properties={
#                 'refresh': openapi.Schema(type=openapi.TYPE_STRING, description='Refresh token'),
#             },
#             required=['refresh'],
#         ),
#         responses={
#             204: 'No Content',
#             400: 'Bad Request'
#         }
#     )
#     def post(self, request, *args, **kwargs):
#         refresh_token = request.data.get('refresh')
#         if not refresh_token:
#             return Response({"error": "Refresh token is required"}, status=status.HTTP_400_BAD_REQUEST)

#         try:
#             token = RefreshToken(refresh_token)
#             token.blacklist()
#             return Response(status=status.HTTP_204_NO_CONTENT)
#         except TokenError as e:
#             return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class UserView(generics.RetrieveUpdateAPIView):
    serializer_class = api_serializer.UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        # Получаем текущего пользователя
        return self.request.user

    def get(self, request, *args, **kwargs):
        user = self.get_object()
        user_data = self.get_serializer(user).data

        # Обрабатываем связанные данные: details и subscription
        try:
            details_serializer = api_serializer.UserDetailsSerializer(user.details)
            user_data['details'] = details_serializer.data
        except ObjectDoesNotExist:
            user_data['details'] = None  # Или другой подходящий способ обработки отсутствия данных

        try:
            subscription_serializer = api_serializer.SubscriptionSerializer(user.subscription)
            user_data['subscription'] = subscription_serializer.data
        except ObjectDoesNotExist:
            user_data['subscription'] = None  # Или другой подходящий способ обработки отсутствия данных

        return Response(user_data)

    def put(self, request, *args, **kwargs):
        user = self.get_object()

        # Создаем копию данных запроса
        data = request.data.copy()

        # Десериализация поля details, если оно строка
        if 'details' in data and isinstance(data['details'], str):
            try:
                data['details'] = json.loads(data['details'])
            except json.JSONDecodeError:
                return Response({'error': 'Invalid JSON in details field.'}, status=status.HTTP_400_BAD_REQUEST)

        # Обновляем данные пользователя, исключая subscription
        user_serializer = self.get_serializer(user, data=data, partial=True)

        try:
            user_serializer.is_valid(raise_exception=True)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        user_serializer.save()

        # Обновляем данные деталей пользователя, если они предоставлены
        if 'details' in data:
            details_serializer = api_serializer.UserDetailsSerializer(
                user.details, data=data['details'], partial=True
            )
            try:
                details_serializer.is_valid(raise_exception=True)
                details_serializer.save()
            except Exception as e:
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        response_data = user_serializer.data

        # Обрабатываем связанные данные: details и subscription
        try:
            details_serializer = api_serializer.UserDetailsSerializer(user.details)
            response_data['details'] = details_serializer.data
        except ObjectDoesNotExist:
            response_data['details'] = None  # Или другой подходящий способ обработки отсутствия данных

        try:
            subscription_serializer = api_serializer.SubscriptionSerializer(user.subscription)
            response_data['subscription'] = subscription_serializer.data
        except ObjectDoesNotExist:
            response_data['subscription'] = None  # Или другой подходящий способ обработки отсутствия данных

        return Response(response_data)
    
    def save(self, *args, **kwargs):
        # Проверяем, есть ли у пользователя связанные детали
        if not hasattr(self, 'details'):
            # Если нет, создаем их
            from .models import UserDetails  # или импортируйте модель наверху файла
            self.details = UserDetails.objects.create(user=self)

        super().save(*args, **kwargs)
    
class FileUploadView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, folder, *args, **kwargs):
        file = request.FILES.get('file')
        if not file:
            return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)

        folder_path = os.path.join(settings.MEDIA_ROOT, folder)
        os.makedirs(folder_path, exist_ok=True)

        file_path = os.path.join(folder_path, file.name)
        with open(file_path, 'wb+') as destination:
            for chunk in file.chunks():
                destination.write(chunk)

        file_url = os.path.join(settings.MEDIA_URL, folder, file.name)
        return Response({'file_url': file_url}, status=status.HTTP_201_CREATED)
    
class AvatarUploadView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        avatar_img = request.data.get('avatar_img')

        if avatar_img:
            user_profile = api_models.User.objects.get(user=request.user)
            user_profile.avatar_img = avatar_img
            user_profile.save()
            return Response({'message': 'Avatar uploaded successfully!'}, status=status.HTTP_200_OK)
        return Response({'error': 'Failed to upload avatar'}, status=status.HTTP_400_BAD_REQUEST)

    
class ChatCreateView(generics.CreateAPIView):
    queryset = api_models.Chat.objects.all()
    serializer_class = api_serializer.ChatSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ChatDetailView(generics.RetrieveAPIView):
    queryset = api_models.Chat.objects.all()
    serializer_class = api_serializer.ChatSerializer
    permission_classes = [IsAuthenticated]


class ChatListView(generics.ListAPIView):
    serializer_class = api_serializer.ChatSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return api_models.Chat.objects.filter(user=self.request.user)


class MessageListView(generics.ListAPIView):
    serializer_class = api_serializer.MessageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        chat_id = self.kwargs['chat_id']
        return api_models.Message.objects.filter(chat_id=chat_id)

class DeleteChatView(generics.DestroyAPIView):
    queryset = api_models.Chat.objects.all()
    permission_classes = [IsAuthenticated]

    def perform_destroy(self, instance):
        instance.messages.all().delete()
        instance.delete()


class UpdateChatView(generics.UpdateAPIView):
    queryset = api_models.Chat.objects.all()
    serializer_class = api_serializer.ChatSerializer
    permission_classes = [IsAuthenticated]

    def update(self, request, *args, **kwargs):
        chat_id = kwargs.get('pk')
        content = request.data.get('content')
        user = request.user
        
        # Get existing chat instance
        instance = get_object_or_404(api_models.Chat, id=chat_id)
        
        if instance.user != user:
            return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
        
        # Check user subscription
        if user.subscription.chat_requests <= 0:
            return Response({'error': 'No chat requests left'}, status=status.HTTP_403_FORBIDDEN)

        # Decrease the number of chat requests
        user.subscription.chat_requests = F('chat_requests') - 1
        user.subscription.save()

        # Save user's new message
        instance.messages.create(role='user', content=content)

        # Get messages and embeddings
        messages = instance.messages.all().order_by('-created_at')[:6]
        last_messages = list(messages)
        embedding = get_embedding(" ".join([msg.content for msg in messages]))

        # Query Pinecone with embedding
        response = query_pinecone(index_name='gpt-viewing-calories', vector=embedding, top_k=4, filter={'userId': user.id})

        # Construct the system message and conversation history
        system_message = {
            "role": "system",
            "content": (
                "Ты помогаешь пользователю советами по тренировкам. Ты можешь создавать тренировки, просто следуй шаблону \n\n"
                "Если пользователь просит создать тренировку, используй следующий шаблон:\n\n"
                "/create_workout: {\n"
                "  \"title\": \"string\",  # Название тренировки, например, 'Morning Cardio'.\n"
                "  \"description\": \"string\",  # Описание тренировки, например, 'A quick morning workout to start your day.'.\n"
                "  \"level\": \"string\",  # Уровень сложности: 'low', 'medium', 'high'.\n"
                "  \"type\": [\"string\"],  # Тип тренировки, например, ['Cardio', 'Endurance'].\n"
                "  \"duration\": integer,  # Продолжительность тренировки в минутах, например, 30.\n"
                "  \"tags\": [\"string\"],  # Теги, описывающие тренировку, например, ['Morning', 'Quick', 'No Equipment'].\n"
                "  \"completed\": boolean,  # Статус завершенности тренировки, true или false.\n"
                "  \"is_favorite\": boolean,  # Отметка о том, что тренировка в избранном, true или false.\n"
                "  \"exercises\": [  # Список упражнений в тренировке.\n"
                "    {\n"
                "      \"title\": \"string\",  # Название упражнения, например, 'Jumping Jacks'.\n"
                "      \"sets\": integer,  # Количество сетов, например, 3.\n"
                "      \"reps\": integer  # Количество повторений, например, 15.\n"
                "    },\n"
                "    {\n"
                "      \"title\": \"string\",  # Название упражнения, например, 'Push-ups'.\n"
                "      \"sets\": integer,  # Количество сетов, например, 3.\n"
                "      \"reps\": integer  # Количество повторений, например, 10.\n"
                "    }\n"
                "    // Добавляй больше упражнений по необходимости\n"
                "  ]\n"
                "}\nПерепроверь шаблон и удали из ответа все свои комментарии #"
            )
        }


        all_messages = [
            system_message,
            *[{"role": msg.role, "content": msg.content} for msg in last_messages],
            {"role": "user", "content": content}
        ]

        # Create completion response from OpenAI
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=all_messages
        )

        # Check if response indicates a workout creation request
        response_content = response.choices[0].message.content
        print('response_content: ',response_content)

        if response_content.startswith('/create_workout:'):
            workout_data_str = response_content.replace('/create_workout:', '').strip()
            try:
                workout_data = json.loads(workout_data_str)
            except json.JSONDecodeError as e:
                return Response({'error': f'Invalid JSON: {e}'}, status=status.HTTP_400_BAD_REQUEST)

            # Создание тренировки
            workout = api_models.Workout.objects.create(
                workout_img='default/workout-image.jpg',
                title=workout_data['title'],
                description=workout_data['description'],
                level=workout_data['level'],
                type=workout_data['type'],
                duration=workout_data['duration'],
                tags=workout_data['tags'],
                completed=workout_data['completed'],
                is_favorite=workout_data['is_favorite'],
                exercises=workout_data['exercises'],  # Сохраняем упражнения в JSONField
                user=user
            )

            return Response({'message': 'Workout created successfully'}, status=status.HTTP_201_CREATED)
        else:
            # Обновление чата новым сообщением
            bot_message = {"role": "assistant", "content": response_content}
            instance.messages.create(role='assistant', content=bot_message['content'])

        return Response({'message': response.choices[0].message})


class WorkoutViewSet(viewsets.ModelViewSet):
    queryset = api_models.Workout.objects.all()
    serializer_class = api_serializer.WorkoutSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class WorkoutCompletedCreateView(generics.CreateAPIView):
    queryset = api_models.WorkoutCompleted.objects.all()
    serializer_class = api_serializer.WorkoutCompletedSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        # Добавьте любую дополнительную логику, если требуется
        print('workout=self.request ',self.request)
        serializer.save()

class WorkoutCompletedListView(generics.ListAPIView):
    serializer_class = api_serializer.WorkoutCompletedSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Фильтруем записи по текущему пользователю, если требуется
        return api_models.WorkoutCompleted.objects.all()
    
class WorkoutCompletedDetailView(generics.RetrieveAPIView):
    queryset = api_models.WorkoutCompleted.objects.all()
    serializer_class = api_serializer.WorkoutCompletedSerializer
    permission_classes = [IsAuthenticated]

    
# class GoalCreateView(generics.CreateAPIView):
#     queryset = api_models.Goal.objects.all()
#     serializer_class = api_serializer.GoalSerializer
#     permission_classes = [IsAuthenticated]

#     def perform_create(self, serializer):
#         serializer.save(user=self.request.user)

# class GoalUpdateView(generics.UpdateAPIView):
#     queryset = api_models.Goal.objects.all()
#     serializer_class = api_serializer.GoalSerializer
#     permission_classes = [IsAuthenticated]

# class GoalDeleteView(generics.DestroyAPIView):
#     queryset = api_models.Goal.objects.all()
#     serializer_class = api_serializer.GoalSerializer
#     permission_classes = [IsAuthenticated]

# class GoalListView(generics.ListAPIView):
#     serializer_class = api_serializer.GoalSerializer
#     permission_classes = [IsAuthenticated]

#     def get_queryset(self):
#         return api_models.Goal.objects.filter(user=self.request.user)
    
# class GoalDetailView(generics.RetrieveAPIView):
#     queryset = api_models.Goal.objects.all()
#     serializer_class = api_serializer.GoalSerializer
#     permission_classes = [IsAuthenticated]

class GoalViewSet(viewsets.ModelViewSet):
    queryset = api_models.Goal.objects.all()
    serializer_class = api_serializer.GoalSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)