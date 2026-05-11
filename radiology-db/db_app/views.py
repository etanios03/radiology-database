from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from .models import Patient
from .forms import PatientForm
from django.views.decorators.csrf import csrf_exempt
# python manage.py runserver

# https://www.w3schools.com/html/html_tables.asp
def index(request):
    patients = Patient.objects.values()
    
    rows = ""
    for patient in patients:
        rows += f"""
        <tr>
            <td><input type="checkbox"></td>
            <td>{patient['subject_id']}</td>
            <td>{patient['submitter_id']}</td>
            <td>{patient['sex']}</td>
            <td>{patient['race']}</td>
            <td>{patient['residence_country']}</td>
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