from django.urls import path

from . import views
# https://docs.djangoproject.com/en/6.0/topics/templates/
urlpatterns = [
    path("", views.index, name="index"),
    path('patients/new/', views.create_patient, name='create-patient'),
]