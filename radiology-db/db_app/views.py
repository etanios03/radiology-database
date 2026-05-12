from django.http import HttpResponse
from django.shortcuts import redirect
from django.middleware.csrf import get_token
from .models import Patient, TreatmentCycle, \
    TherapyTreatment, TumorInformation, ImagingStudy,\
    AbsorbedDose, ClinicalOutcome, DicomFile
from .forms import PatientForm, TreatmentCycleForm,\
    TherapyTreatmentForm, TumorInformationForm,\
    ImagingStudyForm, AbsorbedDoseForm, ClinicalOutcomeForm, DicomForm
# activate the virtual env
# python manage.py runserver

def make_table(title, headers, rows, url=None):
    header_cells = "".join(f"<th>{h}</th>" for h in headers)
    add_link = f'<a href="{url}"> Add</a>' if url else ""
    empty_row = f'<tr><td colspan="{len(headers)}">no records found</td></tr>'
    return f"""
    <h3>{title}</h3>
    {add_link}
    <table border="1" cellpadding="5" cellspacing="0">
        <tr>{header_cells}</tr>
        {rows or empty_row}
    </table>
    """
def make_view(request, form, redirect_name, title):
    if request.method == 'POST':
        # https://docs.djangoproject.com/en/5.2/topics/http/file-uploads/
        # need request.FILES so the form accepts the file and submits with it
        form = form(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect(redirect_name)
    else:
        form = form()
    # include CSRF token with the middleware
    # https://www.geeksforgeeks.org/python/csrf-token-in-django/
    # for submitting forms need a token to authenticate the user 
    # enctype needed for the file data to actually send with the form
    html = f"""
    <html><body>
        <h2>Create {title}</h2>
        <form method="post" enctype="multipart/form-data">
            <input type="hidden" name="csrfmiddlewaretoken" value="{get_token(request)}">
            {form.as_p()}
            <button type="submit">Save</button>
        </form>
    </body></html>
    """
    return HttpResponse(html)
# return render(html file) and then make a templates folder 

# this is the patient list by patient id
def index(request):
    patients = Patient.objects.all()
    rows = ""
    for patient in patients:
        rows += f"""
        <tr>
            <td><a href="/patients/{patient.subject_id}/">{patient.subject_id}</a></td>
            <td>{patient.submitter_id}</td>
            <td>{patient.sex}</td>
            <td>{patient.race}</td>
            <td>{patient.residence_country}</td>
        </tr>
        """

    html = f"""
    <html>
    <head><title>Patient Registry</title></head>
    <body>
        <h2>Patient Registry</h2>
        <table border="1" cellpadding="6" cellspacing="0">
            <tr>
                <th>Subject ID</th>
                <th>Submitter ID</th>
                <th>Sex</th>
                <th>Race</th>
                <th>Country</th>
            </tr>
            {rows}
        </table>
        <br>
        <a href="/patients/new/">+ Add Patient</a>
    </body>
    </html>
    """
    return HttpResponse(html)


# this has all of the patient info from all the other tables in the database
def patient_detail(request, subject_id):
    try:
        patient = Patient.objects.get(subject_id=subject_id)
    except Patient.DoesNotExist:
        return HttpResponse("<h2>Patient not found</h2>", status=404)

    # treatment cycle table
    # filter by the patient id in the ORM database
    cycles = TreatmentCycle.objects.filter(patient=patient)
    cycle_rows = "".join(
        f"<tr><td>{c.id}</td><td>{c.cycle_number}</td><td>{c.radiopharmaceutical}</td><td>{c.therapy_type}</td><td>{c.net_injected_activity}</td><td>{c.therapeutic_target}</td></tr>"
        for c in cycles
    )
    cycle_table = make_table(
        "Treatment Cycles",
        ["ID", "Cycle Num", "Radiopharmaceutical", "Therapy Type", "Net Injected Activity (MBq)", "Target"],
        cycle_rows,
        url="/treatment-cycles/new/"
    )

    # therapy treatments table
    therapies = TherapyTreatment.objects.filter(patient=patient)
    therapy_rows = "".join(
        f"<tr><td>{t.id}</td><td>{t.therapy_type}</td><td>{t.start_therapy_date}</td><td>{t.end_therapy_date}</td><td>{t.pre_tumor_volume}</td><td>{t.post_tumor_volume}</td></tr>"
        for t in therapies
    )
    therapy_table = make_table(
        "Therapy Treatments",
        ["ID", "Therapy Type", "Start Date", "End Date", "Pre Tumor Vol", "Post Tumor Vol"],
        therapy_rows,
        url="/therapy-treatments/new/"
    )

    # tumor info 
    tumors = TumorInformation.objects.filter(patient=patient)
    tumor_rows = "".join(
        f"<tr><td>{t.id}</td><td>{t.tumor_site}</td><td>{t.ajcc_stage}</td><td>{t.tumor_grade}</td><td>{t.liver_mets}</td><td>{t.ki_67}</td><td>{t.pet_tumor_vol}</td></tr>"
        for t in tumors
    )
    tumor_table = make_table(
        "Tumor Information",
        ["ID", "Tumor Site", "AJCC Stage", "Grade", "Liver Mets", "Ki-67", "Pet Tumor Vol"],
        tumor_rows,
        url="/tumor-information/new/"
    )

    # Imaging study
    studies = ImagingStudy.objects.filter(treatment_cycle__patient=patient)
    study_rows = "".join(
        f"<tr><td>{s.treatment_cycle}</td><td>{s.loinc_contrast}</td><td>{s.modality}</td><td>{s.year_of_study}</td></tr>"
        for s in studies
    )
    study_table = make_table(
        "Imaging Studies",
        ["Treatment Cycle", "Contrast", "Modality", "Year of Study"],
        study_rows,
        url="/imaging-studies/new/"
    )

    # absorbed dose
    # have to traverse through multiple tables in the ORM through the foreign keys
    # https://docs.djangoproject.com/en/5.2/topics/db/queries/#lookups-that-span-relationships
    doses = AbsorbedDose.objects.filter(imaging_study__treatment_cycle__patient=patient)
    dose_rows = "".join(
        f"<tr><td>{d.imaging_study}</td><td>{d.target}</td><td>{d.mean}</td><td>{d.d90}</td><td>{d.lesion_vol}</td><td>{d.dosimetry_method}</td><td>{d.time_activity_curve_fit}</td></tr>"
        for d in doses
    )
    dose_table = make_table(
        "Absorbed Doses",
        ["Imaging Study", "Target", "Mean Dose (Gy)", "D90", "Lesion Vol", "Dosimetry Method", "TAC Fit"],
        dose_rows,
        url="/absorbed-doses/new/"
    )

    # clinical outcomes 
    outcomes = ClinicalOutcome.objects.filter(patient=patient)
    outcome_rows = "".join(
        f"<tr><td>{o.patient}</td><td>{o.treatment_response}</td><td>{o.progression_free_survival}</td><td>{o.overall_survival}</td><td>{o.toxicity_grade}</td><td>{o.days_to_progression}</td></tr>"
        for o in outcomes
    )
    outcome_table = make_table(
        "Clinical Outcomes",
        ["Patient ID", "Treatment Response", "PFS (days)", "OS (days)", "Toxicity Grade", "Days to Progression"],
        outcome_rows,
        url="/clinical-outcomes/new/"
    )

    # DICOM images 
    # have to do the foreign key traversal again 
    dicoms = DicomFile.objects.filter(imaging_study__treatment_cycle__patient=patient)
    dicom_rows = "".join(
        f"<tr><td>{d.imaging_study}</td><td>{d.file_name}</td><td>{d.modality}</td><td>{d.series_description}</td>td>{d.manufacturer}</td>td>{d.collimator}</td>td>{d.attenuation_correction}</td>td>{d.convolution_kernel}</td></tr>"
        for d in dicoms
    )
    dicom_table = make_table(
        "DICOM Files",
        ["Imaging Study", "File Name", "Modality", "Description", "Manufacturer", "Collimator", "Attenuation Corr", "Convol. Kernel"],
        dicom_rows,
        url="/dicom/new/"
    )

    html = f"""
    <html>
    <head><title>Patient {patient.subject_id}</title></head>
    <body>
        <a href="/">&larr; Back to Patient Registry</a>
        <h2>Patient: {patient.subject_id}</h2>
        <p>
            <strong>Submitter ID:</strong> {patient.submitter_id} &nbsp;|&nbsp;
            <strong>Sex:</strong> {patient.sex} &nbsp;|&nbsp;
            <strong>Race:</strong> {patient.race} &nbsp;|&nbsp;
            <strong>Country:</strong> {patient.residence_country}
        </p>
        <hr>
        {cycle_table}
        <hr>
        {therapy_table}
        <hr>
        {tumor_table}
        <hr>
        {study_table}
        <hr>
        {dose_table}
        <hr>
        {outcome_table}
        <hr>
        {dicom_table}
    </body>
    </html>
    """
    return HttpResponse(html)


def create_patient(request):
    return make_view(request, PatientForm, 'index', 'Patient')

def create_treatment_cycle(request):
    return make_view(request, TreatmentCycleForm, 'index', 'Treatment Cycle')

def create_therapy_treatment(request):
    return make_view(request, TherapyTreatmentForm, 'index', 'Therapy Treatment')

def create_tumor_information(request):
    return make_view(request, TumorInformationForm, 'index', 'Tumor Information')

def create_imaging_study(request):
    return make_view(request, ImagingStudyForm, 'index', 'Imaging Study')

def create_absorbed_dose(request):
    return make_view(request, AbsorbedDoseForm, 'index', 'Absorbed Dose')

def create_clinical_outcome(request):
    return make_view(request, ClinicalOutcomeForm, 'index', 'Clinical Outcome')

def create_dicom(request):
    return make_view(request, DicomForm, 'index', 'DICOM File')