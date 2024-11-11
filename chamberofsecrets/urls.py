from django.urls import path
from . import views

app_name = 'chamberofsecrets'
urlpatterns = [
    path('cookies/', views.CookiesView.as_view(), name='cookies')
]