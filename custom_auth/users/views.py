from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden, HttpResponse
from .forms import MyUserCreationForm, MyUserChangeForm
from functools import wraps
from rbac.models import Role


def home(request):
    context = {}
    if request.user.is_authenticated:
        return redirect('users:profile')
    return render(request, 'users/home.html', context)


def permission_required(resource, action):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                if request.path.startswith('/rbac/api/'):
                    return HttpResponse('Unauthorized: Login required.', status=401)
                messages.error(request, 'Доступ запрещён: Не авторизованы.')
                return redirect('users:login')
            
            if not request.user.has_permission(resource, action):
                if request.path.startswith('/rbac/api/'):
                    return HttpResponseForbidden('Forbidden: No permission.')
                messages.error(request, f'Доступ запрещён: Нет прав на {action} {resource}.')
                return redirect('users:home')
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


def register(request):
    if request.method == 'POST':
        form = MyUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            default_role, created = Role.objects.get_or_create(
                name='User',
                defaults={'description': 'Обычный пользователь (базовый доступ к профилю)'}
            )
            user.roles.add(default_role)
            email = form.cleaned_data['email']
            password = form.cleaned_data['password1']
            user = authenticate(request, email=email, password=password)
            if user:
                login(request, user)
                messages.success(request, 'Регистрация успешна!')
                return redirect('users:profile')
            else:
                messages.error(request, 'Ошибка аутентификации после регистрации.')
    else:
        form = MyUserCreationForm()
    return render(request, 'users/register.html', {'form': form})


def user_login(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        if email and password:
            user = authenticate(request, email=email, password=password)
            if user:
                login(request, user)
                return redirect('users:profile')
            messages.error(request, 'Неверный email или пароль.')
        else:
            messages.error(request, 'Введите email и пароль.')
    return render(request, 'users/login.html')


def user_logout(request):
    logout(request)
    messages.success(request, 'Вы вышли из системы.')
    return redirect('users:login')

@login_required
def profile(request):
    user = request.user
    
    context = {
        'user': user,
    }
    
    return render(request, 'users/profile.html', context)

@login_required
def profile_update(request):
    user = request.user
    if request.method == 'POST':
        form = MyUserChangeForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Профиль обновлён.')
            return redirect('users:profile')
    else:
        form = MyUserChangeForm(instance=user)
    return render(request, 'users/profile_update.html', {'form': form})

@login_required
def profile_delete(request):
    user = request.user
    if request.method == 'POST':
        user.soft_delete()
        logout(request)
        messages.success(request, 'Аккаунт удалён. Вы вышли из системы.')
        return redirect('users:home')
    return render(request, 'users/delete_confirm.html', {'user': user})
