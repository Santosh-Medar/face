from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages

def login_view(request):
    if request.user.is_authenticated:
        if request.user.is_superuser:
            return redirect('admin_dashboard')
        else:
            return redirect('student_dashboard')

    if request.method == 'POST':
        login_input = request.POST.get('login')    # can be roll_no OR username
        password = request.POST.get('password')
        print(f"Attempting login with: {login_input} / {password}")  # Debugging line
        user = authenticate(request, username=login_input, password=password)

        if user is not None:
            login(request, user)
            if user.is_superuser:
                return redirect('admin_dashboard')
            else:
                return redirect('student_dashboard')
        else:
            messages.error(request, 'Invalid roll number/username or password')

    return render(request, 'accounts/login.html')

def logout_view(request):
    logout(request)
    return redirect('login')