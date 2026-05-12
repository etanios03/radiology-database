from django.urls import path

from . import views
# https://docs.djangoproject.com/en/6.0/topics/templates/
urlpatterns = [
    # patients at index
    path('', views.index, name='index'),

    # had an issue with matching the url: need the patients/new (less specific) to be first
    # https://www.mostlypython.com/does-order-matter-in-urlspy/
    path('patients/new/', views.create_patient, name='create_patient'),
    # patient details by subject id
    path('patients/<str:subject_id>/', views.patient_detail, name='patient_detail'),
    # places to create all parts of the data model
    path('treatment-cycles/new/', views.create_treatment_cycle, name='create_treatment_cycle'),
    path('therapy-treatments/new/', views.create_therapy_treatment, name='create_therapy_treatment'),
    path('tumor-information/new/', views.create_tumor_information, name='create_tumor_information'),
    path('imaging-studies/new/', views.create_imaging_study, name='create_imaging_study'),
    path('absorbed-doses/new/', views.create_absorbed_dose, name='create_absorbed_dose'),
    path('clinical-outcomes/new/', views.create_clinical_outcome, name='create_clinical_outcome'),
    path('dicom/new/', views.create_dicom, name='create_dicom'),
]