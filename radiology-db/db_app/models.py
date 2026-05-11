from django.db import models

# Create your models here.

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
    NOT_REPORTED = 'NR', 'Not Reported'

class TherapyType(models.TextChoices):
    HORMONE  = 'hormone_therapy', 'Hormone Therapy'
    CHEMO  = 'chemotherapy', 'Chemotherapy'
    IMMUNO = 'immunotherapy', 'Immunotherapy'
    RADIATION = 'system_radiation_therapy', 'Systemic Radiation Therapy'
    LIVER_DIR = 'liver_directed_therapy',  'Liver Directed Therapy'

class Ecog(models.TextChoices):
    ECOG_0 = '0', 'ECOG 0'
    ECOG_1 = '1', 'ECOG 1'
    ECOG_2 = '2', 'ECOG 2'
    ECOG_3 = '3', 'ECOG 3'
    ECOG_4 = '4', 'ECOG 4'
    ECOG_5 = '5', 'ECOG 5'

class Target(models.TextChoices):
    LIVER = 'liver', 'Liver'
    KIDNEYS = 'kidneys', 'Kidneys'
    MARROW  = 'marrow', 'Marrow'
    SALIVARY_GLANDS = 'salivary_glands', 'Salivary Glands'
    LUNGS  = 'lungs', 'Lungs'
    SPLEEN = 'spleen', 'Spleen'
    BODY = 'rest_of_body', 'Rest of Body'
    LESION = 'lesion', 'Lesion'

class Modality(models.TextChoices):
    PET   = 'PET',   'PET'
    CT    = 'CT',    'CT'
    SPECT = 'SPECT', 'SPECT'
    MRI   = 'MRI',   'MRI'

class DosimetryMethod(models.TextChoices):
    MIRD  = 'MIRD',            'MIRD'
    VOXEL = 'voxel_dosimetry', 'Voxel Dosimetry'
    MC    = 'monte_carlo',     'Monte Carlo'
    OTHER = 'Other',           'Other'

class Response(models.TextChoices):
    COMPLETE    = 'complete_response',  'Complete Response'
    PARTIAL     = 'partial_response',   'Partial Response'
    STABLE      = 'stable_disease',     'Stable Disease'
    PROGRESSIVE = 'progressive_disease','Progressive Disease'
    NA          = 'not_evaluable',      'Not Evaluable'

class ToxicityGrade(models.TextChoices):
    ONE   = 'grade_1', 'Grade 1'
    TWO   = 'grade_2', 'Grade 2'
    THREE = 'grade_3', 'Grade 3'
    FOUR  = 'grade_4', 'Grade 4'
    FIVE  = 'grade_5', 'Grade 5'

class Patient(models.Model):
    submitter_id = models.CharField(max_length=500)
    subject_id = models.CharField(max_length=500, primary_key=True)
    residence_country = models.CharField(max_length=500)
    race = models.CharField(max_length=500)
    sex = models.CharField(max_length=10, choices=Sex.choices, default=Sex.NOT_REPORTED)

class TreatmentCycle(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="treatment_cycles")
    cycle_number = models.IntegerField(default=1)
    radiopharmaceutical = models.CharField(max_length=500)
    therapy_type = models.CharField(max_length=10, choices=Therapy.choices, default=Therapy.NOT_REPORTED)
    net_injected_activity = models.DecimalField(max_digits=12,decimal_places=4)
    therapeutic_target = models.CharField(max_length=500)
    pre_sstr_pet = models.DecimalField(max_digits=12,decimal_places=4, null=True, blank=True)
    post_sstr_pet = models.DecimalField(max_digits=12,decimal_places=4, null=True, blank=True)
    pre_chromogranin_a = models.DecimalField(max_digits=12,decimal_places=4, null=True, blank=True)
    post_chromogranin_a= models.DecimalField(max_digits=12,decimal_places=4, null=True, blank=True)
    overall_survival = models.IntegerField()
    # there can be multiple treatment cycles per patient 

class CaseID(models.Model):
    treatment_cycle = models.ForeignKey(TreatmentCycle, on_delete=models.CASCADE, related_name="case_ids")
    case_submitter_id = models.CharField(max_length=500)

class LabTest(models.Model):
    treatment_cycle = models.ForeignKey(TreatmentCycle, on_delete=models.CASCADE, related_name="lab_tests")
    loinc_code = models.CharField(max_length=100)
    lab_value = models.DecimalField(max_digits=12,decimal_places=4)
    lab_unit = models.CharField(max_length=100)
    collection_time = models.DateTimeField(null=True, blank=True)
    creatinine_clearance = models.DecimalField(max_digits=12,decimal_places=4,null=True, blank=True)
    # want to add a connection where there can be multiple lab tests per treatment cycle

class Surgery(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="surgeries")
    date_of_surgery = models.DateTimeField()
    primary_tumor_removal = models.BooleanField(default=False)
    time_between_RPT_surgery = models.DecimalField(max_digits=12,decimal_places=4)
    pre_tumor_volume = models.DecimalField(max_digits=12,decimal_places=4)
    post_tumor_volume = models.DecimalField(max_digits=12,decimal_places=4)
    debulking_threshold = models.DecimalField(max_digits=12,decimal_places=4, null=True, blank=True)

class TherapyTreatment(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="therapy_treatments")
    therapy_type = models.CharField(choices=TherapyType.choices, max_length=100)
    start_therapy_date = models.DateTimeField()
    end_therapy_date = models.DateTimeField()
    time_between_rpt_other = models.DecimalField(max_digits=12,decimal_places=4)
    pre_tumor_volume = models.DecimalField(max_digits=12,decimal_places=4)
    post_tumor_volume = models.DecimalField(max_digits=12,decimal_places=4)

class MedicalHistory(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="medical_history")
    condition_name = models.CharField(max_length=500)
    condition_code = models.CharField(max_length=100)
    days_to_condition_start = models.IntegerField(null=True, blank=True)
    days_to_condition_end = models.IntegerField(null=True, blank=True)
    performance_ecog = models.CharField(choices=Ecog.choices, max_length=100, null=True, blank=True)

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
    age_at_imaging = models.IntegerField()
    loinc_code = models.CharField(max_length=100)
    loinc_contrast = models.CharField(max_length=100)
    loinc_modality = models.CharField(max_length=100)
    modality = models.CharField(choices=Modality.choices, max_length=100)
    year_of_study = models.DateField()
    scan_timepoint = models.DateTimeField()

class AbsorbedDose(models.Model):
    imaging_study = models.ForeignKey(ImagingStudy, on_delete=models.CASCADE, related_name="absorbed_dose_imaging")
    target = models.CharField(choices=Target.choices, max_length=100)
    target_id = models.CharField(max_length=100)
    mean = models.DecimalField(max_digits=12,decimal_places=4)
    stdev = models.DecimalField(max_digits=12,decimal_places=4)
    d50 = models.DecimalField(max_digits=12,decimal_places=4)
    d90 = models.DecimalField(max_digits=12,decimal_places=4)
    lesion_vol = models.DecimalField(max_digits=12,decimal_places=4)
    dosimetry_method = models.CharField(max_length=100, choices=DosimetryMethod.choices)
    software_used = models.CharField(max_length=100)
    time_activity_curve_fit = models.CharField(max_length=100)

class ClinicalOutcome(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="clinical_outcomes")
    treatment_response = models.CharField(choices=Response.choices, max_length=100)
    progression_free_survival = models.IntegerField()
    overall_survival = models.IntegerField()
    toxicity_grade = models.CharField(choices=ToxicityGrade.choices, max_length=100)
    toxicity_organ = models.CharField(choices=Target.choices, max_length=100)
    days_to_progression = models.IntegerField()

class DicomFile(models.Model):
    imaging_study = models.ForeignKey(ImagingStudy, on_delete=models.CASCADE, related_name="dicom_files")
    file_name = models.CharField(max_length=200)
    file_size = models.DecimalField(max_digits=12,decimal_places=4)
    md5sum = models.CharField(max_length=200)
    modality = models.CharField(choices=Modality.choices, max_length=50)
    series_description = models.CharField(max_length=500)
    manufacturer = models.CharField(max_length=200)
    model_name = models.CharField(max_length=200)
    software_version = models.CharField(max_length=200)
    collimator = models.CharField(max_length=200, default="NA")
    attenuation_correction = models.CharField(max_length=200, default="NA")
    convolution_kernel = models.CharField(max_length=200, default="NA")
    energy_window = models.CharField(max_length=200, default="NA")
