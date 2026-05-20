from django.http import HttpResponse
from django.shortcuts import redirect
from .models import Patient, TreatmentCycle, \
    TherapyTreatment, TumorInformation, ImagingStudy,\
    AbsorbedDose, ClinicalOutcome, DicomFile
from .forms import PatientForm, TreatmentCycleForm,\
    TherapyTreatmentForm, TumorInformationForm,\
    ImagingStudyForm, AbsorbedDoseForm, ClinicalOutcomeForm, DicomForm
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import pydicom
from .segmentation import segment_dicom
import numpy as np
from PIL import Image
import io
import os
import base64
# activate the virtual env
# python manage.py runserver

'''
tests: for algorithm (put before async refactoring), django test for views 
(see testing framework) test the context for the rendering of templates
templates ** good for testing
1) make it look pretty 
'''

# https://pydicom.github.io/pydicom/stable/index.html
# https://pydicom.github.io/pydicom/1.1/working_with_pixel_data.html
# inspiration: https://github.com/ZviBaratz/django_dicom
def view_dicom(request, dicom_id):
    try:
        dicom_record = DicomFile.objects.get(id=dicom_id)
    except DicomFile.DoesNotExist:
        return HttpResponse("DICOM file not found", status=404)

    ds = pydicom.dcmread(dicom_record.file.path)

    pixel_array = ds.pixel_array.astype(float)
    # take the middle slice if there are multiple parts to the dicom file
    if pixel_array.ndim == 3:
        frame_index = pixel_array.shape[0] // 2
        pixel_array = pixel_array[frame_index]
    # use the dicom metadata for the slope and intercept for rescaling pixels
    slope = float(getattr(ds, 'RescaleSlope', 1))
    intercept = float(getattr(ds, 'RescaleIntercept', 0))
    pixel_array = pixel_array * slope + intercept

    # ** WINDOW **
    # get the window center and width from dicom metadata
    if hasattr(ds, 'WindowCenter') and hasattr(ds, 'WindowWidth'):
        # if has multiple window values in the metadata then pick the first one
        center = float(ds.WindowCenter) if not isinstance(ds.WindowCenter, pydicom.multival.MultiValue) else float(ds.WindowCenter[0])
        width  = float(ds.WindowWidth)  if not isinstance(ds.WindowWidth,  pydicom.multival.MultiValue) else float(ds.WindowWidth[0])
        # normalize to 255 for the window display
        low  = center - width / 2
        high = center + width / 2
        clipped = np.clip(pixel_array, low, high)
        if clipped.max() > clipped.min():
            pixel_array = (clipped - low) / (high - low) * 255
        else:
            pmin, pmax = pixel_array.min(), pixel_array.max()
            pixel_array = (pixel_array - pmin)/(pmax - pmin) * 255
    else:
        pmin, pmax = pixel_array.min(), pixel_array.max()
        if pmax > pmin:
            pixel_array = (pixel_array - pmin)/(pmax - pmin) * 255
    # integers for making the actual image for pillow bc its fancy 
    pixel_array = pixel_array.astype(np.uint8)
    image = Image.fromarray(pixel_array)
    # put the img into the html 
    # https://stackoverflow.com/questions/70848602/how-can-i-display-pil-image-to-html-with-render-template-flask
    # ^ this is for Flask, but I used the same idea here
    buffer = io.BytesIO()
    image.save(buffer, format='PNG')
    encoded = base64.b64encode(buffer.getvalue()).decode('utf-8')
    img_tag = f'<img src="data:image/png;base64,{encoded}" style="max-width:600px; border:1px solid #ccc;">'

    metadata_table = f"""
    <table border="1" cellpadding="5" cellspacing="0">
        {f"<tr><td><strong>{'Patient ID'}</strong></td><td>{getattr(ds, "PatientID", 'N/A')}</td></tr>"}
        {f"<tr><td><strong>{'Modality'}</strong></td><td>{getattr(ds, "Modality", 'N/A')}</td></tr>"}
        {f"<tr><td><strong>{'Study Description'}</strong></td><td>{getattr(ds, "StudyDescription", 'N/A')}</td></tr>"}
        {f"<tr><td><strong>{'Manufacturer'}</strong></td><td>{getattr(ds, "Manufacturer", 'N/A')}</td></tr>"}
        {f"<tr><td><strong>{'Slice Thickness'}</strong></td><td>{getattr(ds, "SliceThickness", 'N/A')}</td></tr>"}
        {f"<tr><td><strong>{'Pixel Spacing'}</strong></td><td>{getattr(ds, "PixelSpacing", 'N/A')}</td></tr>"}
        {f"<tr><td><strong>{'Rows'}</strong></td><td>{getattr(ds, "Rows", 'N/A')}</td></tr>"}
        {f"<tr><td><strong>{'Columns'}</strong></td><td>{getattr(ds, "Columns", 'N/A')}</td></tr>"}
        {f"<tr><td><strong>{'Bits Allocated'}</strong></td><td>{getattr(ds, "BitsAllocated", 'N/A')}</td></tr>"}
        {f"<tr><td><strong>{'Window Center'}</strong></td><td>{getattr(ds, "WindowCenter", 'N/A')}</td></tr>"}
        {f"<tr><td><strong>{'Window Width'}</strong></td><td>{getattr(ds, "WindowWidth", 'N/A')}</td></tr>"}
    </table>
    """
    # run segmentation if button was clicked
    seg_html = ""
    if request.method == 'POST' and 'run_segmentation' in request.POST:
        try:
            # sci kit segmentation in segmentation.py file
            result = segment_dicom(dicom_record.file.path)
            seg_html = f"""
            <div style="margin-top:20px; padding:10px; border:1px solid #4caf50; background:#f1fff1;">
                <strong>Segmentation Result</strong><br>
                Lesion Volume: <strong>{result['lesion_volume_mL']} mL</strong><br>
                Voxel Volume: {result['voxel_volume']} mm³<br>
                Threshold: {result['otsu_threshold']}<br>
                Slice Thickness: {result['slice_thickness_mm']} mm<br>
            </div>
            """
            # we don't want to crash the pg!!! so put the exception instead
        except Exception as e:
            seg_html = f'<p style="color:red;">segmentation didnt work: {e}</p>'

    # final html to return with the titles, body, table and the segmentation button/result on POST
    html = f"""
    <html>
    <head><title>DICOM Viewer — {dicom_record.file_name}</title></head>
    <body>
        <a href="/patients/{dicom_record.imaging_study.treatment_cycle.patient.subject_id}/">&larr; Back to Patient</a>
        <h2>DICOM Viewer: {dicom_record.file_name}</h2>
        <div style="display:flex; gap:40px; align-items:flex-start;">
            <div>{img_tag}</div>
            <div>
                <h3>Metadata</h3>
                {metadata_table}
                <h3>Lesion Segmentation</h3>
                <form method="post">
                    <input type="hidden" name="run_segmentation" value="1">
                    <button type="submit">Calculate Lesion Volume</button>
                </form>
                {seg_html}
            </div>
        </div>
    </body>
    </html>
    """
    return HttpResponse(html)

# return an html table so to add to final html return in full patient details view
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
        # django splits into the FILES and the text (POST) so need both 
        form = form(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect(redirect_name)
    else:
        form = form()
    # disabled the csrf token in settings!
    # https://www.geeksforgeeks.org/python/csrf-token-in-django/
    # multipart/form-data tells browser to split form data into sections 
    # so that the file gets sent to the server
    html = f"""
    <html><body>
        <h2>Create {title}</h2>
        <form method="post" enctype="multipart/form-data">
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
        <table border="1" cellpadding="5" cellspacing="0">
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
        <a href="/patients/new/">Add Patient</a>
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
        ["Patient ID","Treatment Response","PFS (days)", "OS (days)", "Toxicity Grade", "Days to Progression"],
        outcome_rows,
        url="/clinical-outcomes/new/"
    )

    # DICOM images 
    # have to do the foreign key traversal again 
    dicoms = DicomFile.objects.filter(imaging_study__treatment_cycle__patient=patient)
    dicom_rows = "".join(
    f"<tr>"
    f"<td>{d.imaging_study}</td>"
    f"<td><a href='/dicom/{d.id}/view/'>{d.file_name}</a></td>"
    f"<td>{d.modality}</td>"
    f"<td>{d.series_description}</td>"
    f"<td>{d.manufacturer}</td>"
    f"<td>{d.collimator}</td>"
    f"<td>{d.attenuation_correction}</td>"
    f"<td>{d.convolution_kernel}</td>"
    f"</tr>"
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
    # submitting form
    if request.method == 'POST':
        if 'autofill' in request.POST:
            uploaded_file = request.FILES.get('file')
            if uploaded_file:
                # save to media/dicom/ directly so the path is already correct
                saved_path = default_storage.save(
                    f'dicom/{uploaded_file.name}',
                    ContentFile(uploaded_file.read())
                )
                full_path = default_storage.path(saved_path)
                # now try reading the saved file into pydicom
                try:
                    ds = pydicom.dcmread(full_path)
                    initial = {
                        'file_name':uploaded_file.name,
                        'modality': getattr(ds, 'Modality',''),
                        'series_description':getattr(ds, 'SeriesDescription',''),
                        'manufacturer':getattr(ds, 'Manufacturer', ''),
                        'collimator':getattr(ds,'CollimatorType', 'NA'),
                        'attenuation_correction':getattr(ds, 'AttenuationCorrectionMethod', 'NA'),
                        'convolution_kernel': getattr(ds, 'ConvolutionKernel', 'NA'),
                    }
                    # fills out the form with the dicom metadata
                    form = DicomForm(initial=initial)
                    # this should be carrying the file path for the next submission
                    # so shouldn't need to reupload, but we have to anyway....? fix bug
                    saved_path_field = f'<input type="hidden" name="saved_path" value="{saved_path}">'
                    file_label = f'<p style="color:green;">✓ File uploaded: <strong>{uploaded_file.name}</strong></p>'
                # file upload and autofill failed
                except Exception as e:
                    form = DicomForm()
                    saved_path_field = ''
                    file_label = f'<p style="color:red;">Could not read DICOM tags: {e}</p>'
            # if no file upload, show blank form
            else:
                form = DicomForm()
                saved_path_field = ''
                file_label = ''

            html = f"""
            <html><body>
                <h2>Create DICOM File</h2>
                {file_label}
                <form method="post" enctype="multipart/form-data">
                    {saved_path_field}
                    {form.as_p()}
                    <button type="submit">Save</button>
                </form>
            </body></html>
            """
            return HttpResponse(html)
        # Save data from form (final sub of form)
        else:
            # check if file is already saved to "media" 
            saved_path = request.POST.get('saved_path')
            if saved_path:
                # build POST data with the file field pointing to saved path
                post_data = request.POST.copy()
                form = DicomForm(post_data, request.FILES)
                if form.is_valid():
                    instance = form.save(commit=False)
                    # if the file is already there then just use the saved one
                    instance.file = saved_path 
                    instance.save()
                    return redirect('index')
            # file not in media 
            else:
                # just do this without the file 
                form = DicomForm(request.POST, request.FILES)
                if form.is_valid():
                    form.save()
                    return redirect('index')
    # GET request so just make the pg as normal
    else:
        form = DicomForm()
        saved_path_field = ''
    # https://developer.mozilla.org/en-US/docs/Learn_web_development/Extensions/Forms/Sending_forms_through_JavaScript
    # using javascript to submit the form after the file is uploaded in order to autopopulate
    # "autofill" is sent so that in our create_dicom function, we can fill out the other sections
    html = f"""
    <html><body>
        <h2>Create DICOM File</h2>
        <p style="color:gray;">Upload a .dcm file to auto-populate fields, then fill in any remaining fields and save.</p>
        <form method="post" enctype="multipart/form-data">
            <input type="hidden" name="autofill" value="1">
            {form.as_p()}
            <button type="submit">Load DICOM Tags</button>
        </form>
        <script>
            document.querySelector('input[type=file]').addEventListener('change', function() {{
                this.form.submit();
            }});
        </script>
    </body></html>
    """
    return HttpResponse(html)