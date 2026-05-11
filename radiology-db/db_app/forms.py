from django import forms
from .models import Patient, TreatmentCycle, \
    TherapyTreatment, TumorInformation, ImagingStudy, \
        AbsorbedDose, ClinicalOutcome, DicomFile
# https://docs.djangoproject.com/en/6.0/topics/forms/
# https://medium.com/@colinatjku/creating-and-linking-forms-with-models-in-django-6e3dce382441

class PatientForm(forms.ModelForm):
    class Meta:
        model = Patient
        fields = '__all__'
        
class TreatmentCycleForm(forms.ModelForm):
    class Meta:
        model = TreatmentCycle
        fields = '__all__'

class TherapyTreatmentForm(forms.ModelForm):
    class Meta:
        model = TherapyTreatment
        fields = '__all__'

class TumorInformationForm(forms.ModelForm):
    class Meta:
        model = TumorInformation
        fields = '__all__'

class ImagingStudyForm(forms.ModelForm):
    class Meta:
        model = ImagingStudy
        fields = '__all__'

class AbsorbedDoseForm(forms.ModelForm):
    class Meta:
        model = AbsorbedDose
        fields = '__all__'

class ClinicalOutcomeForm(forms.ModelForm):
    class Meta:
        model = ClinicalOutcome
        fields = '__all__'

class DicomForm(forms.ModelForm):
    class Meta:
        model = DicomFile
        fields = '__all__'