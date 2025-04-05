from django.urls import path
from . import views
from world.views import profile_view

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/<int:user_id>/', profile_view, name='profile'),  # يُستخدم لبروفايل الآخرين
    path('profile/', profile_view, name='current_profile'),  # اختياري: لبروفايل المستخدم الحالي
    path('create-post/', views.create_post_view, name='create_post'),
    path('like-post/', views.like_post, name='like_post'),
    path('add-comment/', views.add_comment, name='add_comment'),
    path('update-profile-picture/', views.update_profile_picture, name='update_profile_picture'),
    path('follow-user/', views.follow_user, name='follow_user'),
    path('notifications/', views.notifications_view, name='notifications'),
    path('mark-notifications-read/', views.mark_notifications_read, name='mark_notifications_read'),
]