from django.urls import include, path, re_path
from . import views

app_name = 'abilityhub'
urlpatterns = [
    # Security Logging and Monitoring Failures (fix)
    #path('accounts/login/', views.ExtendedLoginView.as_view(), name='login'),
    path('accounts/', include('django.contrib.auth.urls')),
    path('accounts/register/', views.RegisterView.as_view(), name='register'),
    path('', views.HomePageView.as_view(), name='home'),
    path('<int:pk>/myprofile/', views.showMyProfile, name='myprofile'), # Broken Access Control
    path('<int:pk>/profile/', views.ProfileView.as_view(), name='profile'),
    path('upload/', views.UploadView.as_view(), name='upload'),
    path('images/set_privacy/<int:image_id>', views.setImagePrivacy, name='set_image_privacy'),
    path('images/delete/<int:image_id>', views.deleteImage, name='delete_image'),
    path('messages/', views.MessagesView.as_view(), name='messages'),
    path('messages/<int:pk>/', views.MessagesView.as_view(), name='chat'),
    path('messages/person/<int:person_id>/', views.openchat, name='openchat'),
    path('transactions/', views.TransactionsView.as_view(), name='transactions'),
    path('deposit/', views.DepositView.as_view(), name='deposit'),
    path('description/', views.DescriptionView.as_view(), name='description'),
    path('<int:pk>/send/', views.SendView.as_view(), name='send'),
    path('sendsuccess/', views.SendSuccessView.as_view(), name='sendsuccess'),
    path('depositsuccess/', views.DepositSuccessView.as_view(), name='depositsuccess'),
    path('navbar/', views.navbar, name='navbar'),
    re_path(r'^.*/navbar/$', views.navbar, name="navbar")
]