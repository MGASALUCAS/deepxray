from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required


def home_view(request):
    """Main landing page for DeepXRAY"""
    return render(request, "home/index.html")


def signup_view(request):
    """User registration"""
    context = {}
    if request.POST:
        username = request.POST["username"]
        email = request.POST["email"]
        password = request.POST["password"]
        first_name = request.POST.get("first_name", "")
        last_name = request.POST.get("last_name", "")

        # Check for existing username or email (case-insensitive)
        if User.objects.filter(username__iexact=username).exists():
            context["form_errors"] = "Username already exists"
        elif User.objects.filter(email__iexact=email).exists():
            context["form_errors"] = "Email already exists"
        else:
            user = User.objects.create_user(
                username=username, 
                email=email, 
                password=password,
                first_name=first_name,
                last_name=last_name
            )
            user.save()
            return redirect("/detection/register")

    return render(request, "home/signup.html", context)


def logout_view(request):
    """User logout"""
    logout(request)
    return redirect("/")


def process_login(request, redirect_path="/"):
    """Process user login with smart user lookup"""
    from django.db.models import Q

    identifier = request.POST.get("email")
    password = request.POST.get("password")

    user = None

    if identifier and password:
        try:
            # Smart user lookup: prioritize exact username match first, then email
            user_obj = None
            
            # First, try to find by exact username match
            try:
                user_obj = User.objects.get(username=identifier)
            except User.DoesNotExist:
                # If username not found, try email match
                try:
                    user_obj = User.objects.get(email=identifier)
                except User.DoesNotExist:
                    return False
                except User.MultipleObjectsReturned:
                    # If multiple users with same email, get the first one
                    user_obj = User.objects.filter(email=identifier).first()
            except User.MultipleObjectsReturned:
                # If multiple users with same username, get the first one
                user_obj = User.objects.filter(username=identifier).first()
            
            if user_obj:
                user = authenticate(username=user_obj.username, password=password)
            
        except Exception as e:
            # Log the error for debugging (optional)
            print(f"Login error: {e}")
            return False

    if user is not None:
        login(request, user)
        return redirect(redirect_path)
    else:
        return False


def login_view(request):
    """User login"""
    context = {}
    if request.POST:
        success = process_login(request, "/detection/")
        if success is False:
            context["form_errors"] = "Invalid username or password"
        else:
            return success

    return render(request, "home/login.html", context)


def password_reset_view(request):
    """Password reset"""
    from django.db.models import Q
    from django.contrib.auth.hashers import make_password

    context = {}

    if request.method == "POST":
        identifier = request.POST.get("identifier")
        password1 = request.POST.get("password1")
        password2 = request.POST.get("password2")

        if not identifier or not password1 or not password2:
            context["form_errors"] = "All fields are required"
        elif password1 != password2:
            context["form_errors"] = "Passwords do not match"
        else:
            try:
                # Smart user lookup for password reset
                user = None
                
                # First, try to find by exact username match
                try:
                    user = User.objects.get(username=identifier)
                except User.DoesNotExist:
                    # If username not found, try email match
                    try:
                        user = User.objects.get(email=identifier)
                    except User.DoesNotExist:
                        context["form_errors"] = "No user with that username or email found"
                        return render(request, "home/reset.html", context)
                    except User.MultipleObjectsReturned:
                        # If multiple users with same email, get the first one
                        user = User.objects.filter(email=identifier).first()
                except User.MultipleObjectsReturned:
                    # If multiple users with same username, get the first one
                    user = User.objects.filter(username=identifier).first()
                
                if user:
                    user.password = make_password(password1)
                    user.save()
                    context["success_message"] = "Password has been reset successfully"
                    return redirect("/login")
                else:
                    context["form_errors"] = "No user with that username or email found"
                    
            except Exception as e:
                print(f"Password reset error: {e}")
                context["form_errors"] = "An error occurred during password reset"

    return render(request, "home/reset.html", context)