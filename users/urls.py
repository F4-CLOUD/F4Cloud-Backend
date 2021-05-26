from django.urls import path
from users import views

urlpatterns = [
    path('sign_up/', views.SignUp.as_view()),
    path('confirm_sign_up/', views.ConfirmSignUp.as_view()),
    path('sign_in/', views.SignIn.as_view()),
    path('sign_out/', views.SignOut.as_view()),
    path('change_password/', views.ChangePassword.as_view()),
    path('forgot_password/', views.ForgotPassword.as_view()),
    path('confirm_forgot_password/', views.ConfirmForgotPassword().as_view()),
    path('delete_user/', views.DeleteUser.as_view())
]
