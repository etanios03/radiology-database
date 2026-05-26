from django.http import HttpResponse, HttpRequest
from django.shortcuts import redirect, render
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
import base64
from asgiref.sync import sync_to_async
import asyncio
from django.forms import BaseModelForm
from typing import Any
# activate the virtual env
# python manage.py runserver
# uvicorn db_project.asgi:application --reload

'''
tests: for algorithm (put before async refactoring), django test for views 
(see testing framework) test the context for the rendering of templates
templates ** good for testing
'''

# https://pydicom.github.io/pydicom/stable/index.html
# https://pydicom.github.io/pydicom/1.1/working_with_pixel_data.html
# inspiration: https://github.com/ZviBaratz/django_dicom
async def view_dicom(request: HttpRequest, dicom_id: int) -> HttpResponse:
    try:        
        dicom_record = await sync_to_async(DicomFile.objects.get)(id=dicom_id)
    except DicomFile.DoesNotExist:
        return HttpResponse("DICOM file not found", status=404)

    # put the image stuff to a thread too
    img_b64, meta = await asyncio.to_thread(prepare_image, dicom_record.file.path)
    seg = None
    seg_error = None
    if request.method =='POST' and 'run_segmentation' in request.POST:
        try:
            seg = await segment_dicom(dicom_record.file.path) 
        except Exception as e:
            seg_error = str(e)
    # need the render return in django to be sync
    # https://stackoverflow.com/questions/61926359/django-synchronousonlyoperation-you-cannot-call-this-from-an-async-context-u
    return await sync_to_async(render)(request, 'dicom_viewer.html', {
        'dicom': dicom_record,
        'img_b64': img_b64,
        'meta': meta,
        'seg': seg,
        'seg_error': seg_error,
    })

# called by thread 
def prepare_image(path: str) -> tuple[str, dict]:
    ds = pydicom.dcmread(path)
    pixel_array = ds.pixel_array.astype(float)
    if pixel_array.ndim == 3:
        pixel_array = pixel_array[pixel_array.shape[0] // 2]
    # pydicom cant know if the return will be None or a return val
    
    slope = float(getattr(ds, 'RescaleSlope',1)) # type: ignore[arg-type] 
    intercept= float(getattr(ds, 'RescaleIntercept', 0)) # type: ignore[arg-type]
    pixel_array= pixel_array * slope +intercept

    if hasattr(ds, 'WindowCenter') and hasattr(ds, 'WindowWidth'):
        center = float(ds.WindowCenter[0] if isinstance(ds.WindowCenter, pydicom.multival.MultiValue) else ds.WindowCenter) # type: ignore[arg-type]
        width  = float(ds.WindowWidth[0]  if isinstance(ds.WindowWidth,  pydicom.multival.MultiValue) else ds.WindowWidth) # type: ignore[arg-type]
        low, high = center - width / 2, center + width / 2
        clipped = np.clip(pixel_array, low, high)
        pixel_array = (clipped - low) / (high - low) * 255 if clipped.max() > clipped.min() else pixel_array
    else:
        pmin, pmax = pixel_array.min(), pixel_array.max()
        if pmax > pmin:
            pixel_array = (pixel_array - pmin) / (pmax - pmin) * 255

    pixel_array = pixel_array.astype(np.uint8)
    image  = Image.fromarray(pixel_array)
    buffer = io.BytesIO()
    image.save(buffer, format='PNG')
    encoded = base64.b64encode(buffer.getvalue()).decode('utf-8')

    meta: dict[str, Any] = {
        'patient_id': getattr(ds, 'PatientID', 'N/A'),
        'modality': getattr(ds, 'Modality', 'N/A'),
        'study_description': getattr(ds, 'StudyDescription', 'N/A'),
        'manufacturer': getattr(ds, 'Manufacturer', 'N/A'),
        'slice_thickness': getattr(ds,'SliceThickness', 'N/A'),
        'pixel_spacing': getattr(ds,'PixelSpacing','N/A'),
        'rows': getattr(ds, 'Rows', 'N/A'),
        'columns': getattr(ds, 'Columns', 'N/A'),
        'bits_allocated': getattr(ds, 'BitsAllocated', 'N/A'),
        'window_center':getattr(ds, 'WindowCenter', 'N/A'),
        'window_width': getattr(ds, 'WindowWidth', 'N/A'),
    }
    return encoded, meta

# return an html table so to add to final html return in full patient details view
def make_table(title: str, headers: list[str], rows: str | None, url: str|None=None) -> str:
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

def make_view(request: HttpRequest, form_class: type[BaseModelForm], redirect_name: str, title: str) -> HttpResponse:
    form = form_class(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect(redirect_name)
    return render(request, 'form.html', {'form':form, 'title':title})


# this is the patient list by patient id
def index(request: HttpRequest) -> HttpResponse:
    patients = Patient.objects.all()
    return render(request, 'index.html', {'patients': patients})

# this has all of the patient info from all the other tables in the database
def patient_detail(request: HttpRequest, subject_id: str) -> HttpResponse:
    try:
        patient = Patient.objects.get(subject_id=subject_id)
    except Patient.DoesNotExist:
        return HttpResponse("<h2>Patient not found</h2>", status=404)
    # for the html file tmeplate, but in all the tables as context
    # all the objects get put into the html rendering
    context = {
        'patient': patient,
        'cycles': TreatmentCycle.objects.filter(patient=patient),
        'therapies': TherapyTreatment.objects.filter(patient=patient),
        'tumors': TumorInformation.objects.filter(patient=patient),
        'studies': ImagingStudy.objects.filter(treatment_cycle__patient=patient),
        'doses': AbsorbedDose.objects.filter(imaging_study__treatment_cycle__patient=patient),
        'outcomes': ClinicalOutcome.objects.filter(patient=patient),
        'dicoms': DicomFile.objects.filter(imaging_study__treatment_cycle__patient=patient),
    }
    return render(request, 'patient_detail.html', context)


def create_patient(request: HttpRequest) -> HttpResponse:
    return make_view(request, PatientForm, 'index', 'Patient')

def create_treatment_cycle(request: HttpRequest) -> HttpResponse:
    return make_view(request, TreatmentCycleForm, 'index', 'Treatment Cycle')

def create_therapy_treatment(request: HttpRequest) -> HttpResponse:
    return make_view(request, TherapyTreatmentForm, 'index', 'Therapy Treatment')

def create_tumor_information(request: HttpRequest) -> HttpResponse:
    return make_view(request, TumorInformationForm, 'index', 'Tumor Information')

def create_imaging_study(request: HttpRequest) -> HttpResponse:
    return make_view(request, ImagingStudyForm, 'index', 'Imaging Study')

def create_absorbed_dose(request: HttpRequest) -> HttpResponse:
    return make_view(request, AbsorbedDoseForm, 'index', 'Absorbed Dose')

def create_clinical_outcome(request: HttpRequest) -> HttpResponse:
    return make_view(request, ClinicalOutcomeForm, 'index', 'Clinical Outcome')

def create_dicom(request: HttpRequest) -> HttpResponse:
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
                    saved_path_field = saved_path
                    file_label = uploaded_file.name
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

            return render(request, 'dicom_form.html', {
                'form': form,
                'title': 'Create DICOM File',
                'saved_path': saved_path_field,
                'file_label': file_label,
                'file_label_ok': uploaded_file is not None and saved_path_field != '',
            })
        # Save data from form (final sub of form)
        else:
            # check if file is already saved to "media" 
            saved_path_media: str | None = request.POST.get('saved_path')
            if saved_path_media:
                # build POST data with the file field pointing to saved path
                post_data = request.POST.copy()
                form = DicomForm(post_data, request.FILES)
                # the file is saved on disk!! so we dont need to check it again
                form.fields['file'].required = False
                if form.is_valid():
                    instance = form.save(commit=False)
                    # if the file is already there then just use the saved one
                    instance.file = saved_path_media
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
    return render(request, 'dicom_form.html', {
        'form': form,
        'title': 'Create DICOM File',
        'saved_path': '',
        'file_label': '',
        'file_label_ok': False,
    })