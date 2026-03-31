from django.urls import path
from . import views

app_name = 'symptom_checker'

urlpatterns = [
    path('', views.index, name='index'),
    path('api/analyze/', views.analyze, name='analyze'),
]
