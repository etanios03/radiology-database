from django import forms
from .models import Patient, TreatmentCycle, CaseID, LabTest, Surgery, \
    TherapyTreatment, MedicalHistory, TumorInformation, ImagingStudy, \
        AbsorbedDose, ClinicalOutcome, DicomFile
# https://docs.djangoproject.com/en/6.0/topics/forms/
# https://medium.com/@colinatjku/creating-and-linking-forms-with-models-in-django-6e3dce382441

class PatientForm(forms.ModelForm):
    class Meta:
        model = Patient
        fields = '__all__'
        

