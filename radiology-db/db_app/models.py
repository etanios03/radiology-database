from django.db import models


# enumeration for patient sex
class Sex(models.TextChoices):
    FEMALE = 'F', 'Female'
    MALE = 'M', 'Male'
    OTHER = 'OTHER', 'Other'
    NOT_REPORTED = 'NR', 'Not Reported'

class Therapy(models.TextChoices):
    ALPHA = 'A', 'Alpha'
    BETA = 'B', 'Beta'
    AUGER = 'E', 'Auger Electron'
    NOT_REPORTED ='NR', 'Not Reported'

class OtherTherapyType(models.TextChoices):
    HORMONE = 'hormone_therapy', 'Hormone Therapy'
    CHEMO = 'chemotherapy', 'Chemotherapy'
    IMMUNO = 'immunotherapy', 'Immunotherapy'
    RADIATION = 'system_radiation_therapy', 'Systemic Radiation Therapy'
    LIVER_DIR = 'liver_directed_therapy', 'Liver Directed Therapy'

class Target(models.TextChoices):
    LIVER = 'liver', 'Liver'
    KIDNEYS = 'kidneys', 'Kidneys'
    MARROW = 'marrow', 'Marrow'
    SALIVARY_GLANDS = 'salivary_glands', 'Salivary Glands'
    LUNGS  = 'lungs', 'Lungs'
    SPLEEN = 'spleen', 'Spleen'
    BODY = 'rest_of_body', 'Rest of Body'
    LESION = 'lesion', 'Lesion'

class Modality(models.TextChoices):
    PET = 'PET', 'PET'
    CT = 'CT', 'CT'
    SPECT = 'SPECT','SPECT'
    MRI = 'MRI', 'MRI'

class DosimetryMethod(models.TextChoices):
    MIRD = 'MIRD', 'MIRD'
    VOXEL = 'voxel_dosimetry', 'Voxel Dosimetry'
    MC = 'monte_carlo', 'Monte Carlo'
    OTHER = 'Other', 'Other'

class Response(models.TextChoices):
    COMPLETE = 'complete_response', 'Complete Response'
    PARTIAL = 'partial_response', 'Partial Response'
    STABLE = 'stable_disease', 'Stable Disease'
    PROGRESSIVE = 'progressive_disease','Progressive Disease'
    NA = 'not_evaluable', 'Not Evaluable'

class ToxicityGrade(models.TextChoices):
    ONE= 'grade_1', 'Grade 1'
    TWO = 'grade_2', 'Grade 2'
    THREE = 'grade_3', 'Grade 3'
    FOUR = 'grade_4', 'Grade 4'
    FIVE= 'grade_5', 'Grade 5'

class Patient(models.Model):
    submitter_id = models.CharField(max_length=500)
    subject_id = models.CharField(max_length=500, primary_key=True)
    residence_country = models.CharField(max_length=500)
    race = models.CharField(max_length=500)
    age = models.IntegerField(default=0)
    sex = models.CharField(max_length=10, choices=Sex.choices, default=Sex.NOT_REPORTED)

class TreatmentCycle(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="treatment_cycles")
    cycle_number = models.IntegerField(default=1)
    radiopharmaceutical = models.CharField(max_length=500)
    therapy_type = models.CharField(max_length=10, choices=Therapy.choices, default=Therapy.NOT_REPORTED)
    net_injected_activity = models.DecimalField(max_digits=12,decimal_places=4)
    therapeutic_target = models.CharField(choices=Target.choices, max_length=500)
    # there can be multiple treatment cycles per patient 

class TherapyTreatment(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="therapy_treatments")
    therapy_type = models.CharField(choices=OtherTherapyType.choices, max_length=100)
    start_therapy_date = models.DateTimeField()
    end_therapy_date = models.DateTimeField()
    time_between_rpt_other = models.DecimalField(max_digits=12,decimal_places=4)
    pre_tumor_volume = models.DecimalField(max_digits=12,decimal_places=4)
    post_tumor_volume = models.DecimalField(max_digits=12,decimal_places=4)

class TumorInformation(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="tumor_information")
    tumor_site = models.CharField(max_length=500)
    ajcc_stage = models.CharField(max_length=20)
    tumor_grade = models.CharField(max_length=100)
    liver_mets = models.BooleanField(default=False)
    ki_67 = models.DecimalField(max_digits=12,decimal_places=4)
    pet_tumor_vol = models.DecimalField(max_digits=12,decimal_places=4)

class ImagingStudy(models.Model):
    treatment_cycle = models.ForeignKey(TreatmentCycle, on_delete=models.CASCADE, related_name="imaging_studies")
    loinc_contrast = models.CharField(max_length=100)
    modality = models.CharField(choices=Modality.choices, max_length=100)
    year_of_study = models.DateField()

class AbsorbedDose(models.Model):
    imaging_study = models.ForeignKey(ImagingStudy, on_delete=models.CASCADE, related_name="absorbed_dose_imaging")
    target = models.CharField(choices=Target.choices, max_length=100)
    mean = models.DecimalField(max_digits=12,decimal_places=4)
    d90 = models.DecimalField(max_digits=12,decimal_places=4)
    lesion_vol = models.DecimalField(max_digits=12,decimal_places=4)
    dosimetry_method = models.CharField(max_length=100, choices=DosimetryMethod.choices)
    time_activity_curve_fit = models.CharField(max_length=100)

class ClinicalOutcome(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="clinical_outcomes")
    treatment_response = models.CharField(choices=Response.choices, max_length=100)
    progression_free_survival = models.IntegerField()
    overall_survival = models.IntegerField()
    toxicity_grade = models.CharField(choices=ToxicityGrade.choices, max_length=100)
    days_to_progression = models.IntegerField()

class DicomFile(models.Model):
    imaging_study = models.ForeignKey(ImagingStudy, on_delete=models.CASCADE, related_name="dicom_files")
    file_name = models.CharField(max_length=200)
    # https://docs.djangoproject.com/en/6.0/topics/http/file-uploads/
    file = models.FileField(upload_to='dicom/', default=None)
    modality = models.CharField(choices=Modality.choices, max_length=50)
    series_description = models.CharField(max_length=500)
    manufacturer = models.CharField(max_length=200)
    collimator = models.CharField(max_length=200, default="NA")
    attenuation_correction = models.CharField(max_length=200, default="NA")
    convolution_kernel = models.CharField(max_length=200, default="NA")
