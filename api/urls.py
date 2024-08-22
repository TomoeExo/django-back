from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from api import views as api_views
from rest_framework.routers import DefaultRouter
from django.conf import settings
from django.conf.urls.static import static

router = DefaultRouter()
router.register(r'user/goal', api_views.GoalViewSet, basename='goal')
router.register(r'user/workout', api_views.WorkoutViewSet, basename='workout')

urlpatterns = [
    # JWT Token endpoints
    path('user/login/', api_views.LoginView.as_view(), name='token_obtain_pair'),
    path('user/token/refresh/', api_views.RefreshTokenView.as_view(), name='token_refresh'),

    # User endpoints
    path('user/register/', api_views.RegisterView.as_view(), name='register_user'),
	path('user/logout/', api_views.LogoutView.as_view(), name='logout'),
    path('user/profile/', api_views.UserView.as_view(), name='user_detail'),

    # Chat endpoints
    path('user/chat/', api_views.ChatListView.as_view(), name='chat_list'),
    path('user/chat/create/', api_views.ChatCreateView.as_view(), name='create_chat'),
    path('user/chat/<int:pk>/', api_views.ChatDetailView.as_view(), name='chat_detail'),
    path('user/chat/<int:chat_id>/messages/', api_views.MessageListView.as_view(), name='chat_messages'),
    path('user/chat/<int:pk>/update/', api_views.UpdateChatView.as_view(), name='update_chat'),
    path('user/chat/<int:pk>/delete/', api_views.DeleteChatView.as_view(), name='delete_chat'),
		
    path('user/workout/workout_completed/create/', api_views.WorkoutCompletedCreateView.as_view(), name='workout_completed_create'),
    path('user/workout/workout_completed/', api_views.WorkoutCompletedListView.as_view(), name='workout_completed_list'),
    path('user/workout/workout_completed/<int:pk>/', api_views.WorkoutCompletedDetailView.as_view(), name='workout_completed_detail'),
		
    path('upload-avatar/', api_views.AvatarUploadView.as_view(), name='upload-avatar'),
	
    # Goal endpoints
	# path('user/goal-create/', api_views.GoalCreateView.as_view(), name='goal-create'),
    # path('user/goal-update/<int:pk>/', api_views.GoalUpdateView.as_view(), name='goal-update'),
    # path('user/goal-delete/<int:pk>/', api_views.GoalDeleteView.as_view(), name='goal-delete'),
    # path('user/goals/', api_views.GoalListView.as_view(), name='goal-list'),
    # path('user/goal/<int:pk>/', api_views.GoalDetailView.as_view(), name='goal-detail'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

urlpatterns += router.urls
