from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from .models import CustomUser, Post
from .forms import CustomUserCreationForm, PostForm

def home(request):
    if not request.user.is_authenticated:
        return redirect('login')
    posts = Post.objects.all().order_by('-created_at').prefetch_related('comments')
    unread_notifications_count = Notification.objects.filter(
        recipient=request.user, 
        is_read=False
    ).count()
    return render(request, 'home.html', {
        'posts': posts,
        'unread_notifications_count': unread_notifications_count
    })

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import CustomUser, Post

def profile_view(request, user_id):
    profile_user = get_object_or_404(CustomUser, id=user_id)
    user_posts = Post.objects.filter(author=profile_user).order_by('-created_at')
    context = {
        'profile_user': profile_user,
        'user_posts': user_posts,
    }
    return render(request, 'profile.html', context)

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'اسم المستخدم أو كلمة المرور غير صحيحة')
    return render(request, 'login.html')

def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = CustomUserCreationForm()
    return render(request, 'register.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login')


from django.http import JsonResponse
from .models import Comment
# views.py
from .models import Notification

def like_post(request):
    if request.method == 'POST' and request.user.is_authenticated:
        post_id = request.POST.get('post_id')
        post = Post.objects.get(id=post_id)
        
        if request.user in post.likes.all():
            post.likes.remove(request.user)
            liked = False
        else:
            post.likes.add(request.user)
            liked = True
            # إنشاء إشعار للمؤلف إذا كان المستخدم الحالي ليس المؤلف
            if request.user != post.author:
                Notification.objects.create(
                    recipient=post.author,
                    sender=request.user,
                    post=post,
                    notification_type='like',
                    text=f'{request.user.full_name} أعجب بمنشورك'
                )
            
        return JsonResponse({
            'likes_count': post.likes.count(),
            'liked': liked
        })
    return JsonResponse({'error': 'Invalid request'}, status=400)

def add_comment(request):
    if request.method == 'POST' and request.user.is_authenticated:
        post_id = request.POST.get('post_id')
        text = request.POST.get('text')
        
        if not text:
            return JsonResponse({'error': 'النص مطلوب'}, status=400)
            
        try:
            post = Post.objects.get(id=post_id)
            comment = Comment.objects.create(
                post=post,
                author=request.user,
                text=text
            )
            
            # إنشاء إشعار للمؤلف إذا كان المستخدم الحالي ليس المؤلف
            if request.user != post.author:
                Notification.objects.create(
                    recipient=post.author,
                    sender=request.user,
                    post=post,
                    notification_type='comment',
                    text=f'{request.user.full_name} علق على منشورك: {text[:30]}...'
                )
            
            return JsonResponse({
                'author': request.user.username,
                'text': text
            })
        except Post.DoesNotExist:
            return JsonResponse({'error': 'المنشور غير موجود'}, status=404)
            
    return JsonResponse({'error': 'طلب غير صالح'}, status=400)

def create_post_view(request):
    if not request.user.is_authenticated:
        return redirect('login')
    if request.method == 'POST':
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            
            # إرسال إشعارات للمتابعين
            followers = request.user.followers.all()
            for follower in followers:
                Notification.objects.create(
                    recipient=follower,
                    sender=request.user,
                    post=post,
                    notification_type='new_post',
                    text=f'{request.user.full_name} نشر منشور جديد'
                )
            
            return redirect('home')
    else:
        form = PostForm()
    return render(request, 'create_post.html', {'form': form})

# views.py
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Profile
from django.http import JsonResponse

@login_required
def update_profile_picture(request):
    if request.method == 'POST' and request.FILES.get('image'):
        profile, created = Profile.objects.get_or_create(user=request.user)
        profile.image = request.FILES['image']
        profile.save()
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=400)

# context_processors.py
from .models import Profile

def profile_pic(request):
    if request.user.is_authenticated:
        profile = Profile.objects.get_or_create(user=request.user)[0]
        return {'profile_pic': profile.image}
    return {}

def follow_user(request):
    if request.method == 'POST' and request.user.is_authenticated:
        user_id = request.POST.get('user_id')
        try:
            user_to_follow = CustomUser.objects.get(id=user_id)
            if request.user != user_to_follow:
                if request.user in user_to_follow.followers.all():
                    user_to_follow.followers.remove(request.user)
                    is_following = False
                else:
                    user_to_follow.followers.add(request.user)
                    is_following = True
                
                return JsonResponse({
                    'status': 'success',
                    'is_following': is_following,
                    'followers_count': user_to_follow.followers.count()
                })
        except CustomUser.DoesNotExist:
            return JsonResponse({'error': 'المستخدم غير موجود'}, status=404)
    return JsonResponse({'error': 'طلب غير صالح'}, status=400)

# views.py
@login_required
def notifications_view(request):
    notifications = Notification.objects.filter(recipient=request.user).order_by('-created_at')
    # تحديث الإشعارات كمقروءة عند عرضها
    notifications.update(is_read=True)
    return render(request, 'notifications.html', {'notifications': notifications})

# views.py
@login_required
def mark_notifications_read(request):
    if request.method == 'POST':
        try:
            # تحديث جميع الإشعارات غير المقروءة للمستخدم الحالي
            updated = Notification.objects.filter(
                recipient=request.user,
                is_read=False
            ).update(is_read=True)
            
            return JsonResponse({
                'status': 'success',
                'updated_count': updated
            })
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=500)
    return JsonResponse({
        'status': 'error',
        'message': 'الطلب غير مسموح به'
    }, status=405)