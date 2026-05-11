from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from .models import Patient, TreatmentCycle,\
    TherapyTreatment,TumorInformation, ImagingStudy,\
    AbsorbedDose, ClinicalOutcome, DicomFile
from .forms import PatientForm, TreatmentCycleForm, \
    TherapyTreatmentForm, TumorInformationForm, \
    ImagingStudyForm, AbsorbedDoseForm, ClinicalOutcomeForm, DicomForm
from django.views.decorators.csrf import csrf_exempt
# python manage.py runserver


def make_table(title, headers, rows, url=None):
    header_cells = "".join(f"<th>{h}</th>" for h in headers)
    add_link = f'<a href="{url}">+ Add</a>' if url else ""
    return f"""
    <h3>{title}</h3>
    {add_link}
    <table border="1" cellpadding="6" cellspacing="0">
        <tr>{header_cells}</tr>
        {rows or '<tr><td colspan="{len(headers)}">No records found.</td></tr>'}
    </table>
    """

def make_view(request, form, redirect, title):
    if request.method == 'POST':
        form = form(request.POST)
        if form.is_valid():
            form.save()
            return redirect(redirect)
    else:
        form = form()
    html = f"""
    <html><body>
        <h2>Create {title}</h2>
        <form method="post">
            {form.as_p()}
            <button type="submit">Save</button>
        </form>
    </body></html>
    """
    return HttpResponse(html)

# https://www.w3schools.com/html/html_tables.asp
def index(request):
    patients = Patient.objects.all()
    
    rows = ""
    for patient in patients:
        rows += f"""
        <tr>
            <td><a href="/patients/{patient.subject_id}/">{patient.subject_id}</a></td>
            <td>{patient.sex}</td>
            <td>{patient.race}</td>
            <td>{patient.residence_country}</td>
        </tr>
        """
    
    html = f"""
    <html>
    <body>
        <h2>Patients</h2>
        <table border="1">
            <tr>
                <th></th>
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

# more details about the patients, all the data model aspects on one page
def patient_full_info(request, subject_id):
    try:
        patient = Patient.objects.get(subject_id=subject_id)
    except Patient.DoesNotExist:
        return HttpResponse("Patient not found", status=404)



@csrf_exempt
def create_patient(request):
    if request.method == 'POST':
        form = PatientForm(request.POST)
        # if all parts in the form properly
        if form.is_valid():
            form.save()
            return redirect('index')
    else:
        # empty form to return 
        form = PatientForm()

    html = f"""
        <html>
        <body>
            <h2>Create Patient</h2>
            <form method="post">
                {form.as_p()}
                <button type="submit">Save</button>
            </form>
        </body>
        </html>
        """
    return HttpResponse(html)