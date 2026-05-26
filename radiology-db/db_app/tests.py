from django.test import TestCase, Client
from django.urls import reverse
from .models import (
    Patient, TreatmentCycle, ImagingStudy,
    AbsorbedDose, ClinicalOutcome, TumorInformation,
    TherapyTreatment, DicomFile
)

# https://medium.com/an-engineer-a-reader-a-guy/django-test-fixture-setup-setupclass-and-setuptestdata-72b6d944cdef

class IndexViewTest(TestCase):
    def setUp(self) -> None:
        # setUp runs before every test
        # create a patient to populate the db
        self.client = Client()
        self.patient = Patient.objects.create(
            subject_id='P001',
            submitter_id='SUB001',
            residence_country='USA',
            race='White',
            age=55,
            sex='F'
        )

    def test_index_status_code(self) -> None:
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_index_uses_correct_template(self) -> None:
        response = self.client.get('/')
        self.assertTemplateUsed(response, 'index.html')

    def test_index_context_contains_patients(self) -> None:
        response = self.client.get('/')
        # check the key exists in the context
        self.assertIn('patients', response.context)

    def test_index_context_patient_count(self) -> None:
        response = self.client.get('/')
        # check the right number of patients came back
        self.assertEqual(len(response.context['patients']), 1)

    def test_index_context_patient_data(self) -> None:
        response = self.client.get('/')
        patient = response.context['patients'][0]
        self.assertEqual(patient.subject_id, 'P001')
        self.assertEqual(patient.age, 55)