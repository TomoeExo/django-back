from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from api import models as api_models

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = api_models.User
        fields = '__all__'

class UserDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = api_models.UserDetails
        fields = '__all__'

class SubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = api_models.Subscription
        fields = '__all__'

class ChatSerializer(serializers.ModelSerializer):
    messages = serializers.SerializerMethodField()
    user = serializers.PrimaryKeyRelatedField(read_only=True, default=serializers.CurrentUserDefault())

    class Meta:
        model = api_models.Chat
        fields = ('id', 'user', 'messages', 'created_at', 'updated_at')

    def get_messages(self, obj):
        messages = obj.messages.all()
        return MessageSerializer(messages, many=True).data


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = api_models.Message
        fields = ('id', 'chat', 'content', 'role', 'created_at', 'updated_at')

class WorkoutSerializer(serializers.ModelSerializer):
    exercises = serializers.JSONField()
    user = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = api_models.Workout
        fields = ('id', 'user', 'workout_img', 'title', 'description', 'level', 'type', 'duration', 'tags', 'completed', 'is_favorite', 'exercises', 'created_at', 'updated_at')

class WorkoutCompletedSerializer(serializers.ModelSerializer):
    workout = serializers.PrimaryKeyRelatedField(queryset=api_models.Workout.objects.all())

    class Meta:
        model = api_models.WorkoutCompleted
        fields = ('id', 'workout', 'total_seconds', 'completed_at', 'created_at', 'updated_at')

class GoalSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = api_models.Goal
        fields = ('id', 'user', 'title', 'description', 'deadline', 'completed', 'created_at', 'updated_at')

# Custom Serializers
class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    # @classmethod
    # def get_token(cls, user):
    #     token = super().get_token(user)
    #     token['username'] = user.username
    #     token['email'] = user.email
    #     token['role'] = user.role
    #     return token

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['username'] = user.username
        token['email'] = user.email
        token['role'] = user.role
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        refresh = self.get_token(self.user)
        data['refresh'] = str(refresh)
        data['access'] = str(refresh.access_token)
        return data

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = api_models.User
        fields = ('username', 'email', 'password', 'password2')

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Passwords do not match."})
        return attrs

    def create(self, validated_data):
        user = api_models.User.objects.create(
            username=validated_data['username'],
            email=validated_data['email'],
        )
        user.set_password(validated_data['password'])
        user.save()
        return user

class PasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField()