from django.test import TestCase, Client
from django.urls import reverse
from .models import Patient, TreatmentCycle, ImagingStudy

# https://medium.com/an-engineer-a-reader-a-guy/django-test-fixture-setup-setupclass-and-setuptestdata-72b6d944cdef

class PatientDetailViewTest(TestCase):
    # runs before the test, makes a temp database entry for testing
    def setUp(self):
        self.client = Client()
        self.patient = Patient.objects.create(subject_id="P1", submitter_id='university1')
        self.patient2 = Patient.objects.create(subject_id="P2", submitter_id='university2')
        self.cycle2 = TreatmentCycle.objects.create(patient=self.patient2, net_injected_activity=100.0)
        self.study2 = ImagingStudy.objects.create(treatment_cycle=self.cycle2, year_of_study='2026')
        self.cycle = TreatmentCycle.objects.create(patient=self.patient, net_injected_activity=100.0)
        self.study = ImagingStudy.objects.create(treatment_cycle=self.cycle,  year_of_study='2026')

    def test_context_has_correct_patient(self):
        # browser simulating url 
        response = self.client.get(reverse('patient_detail', args=['P1']))
        # response.context is the return from the view 
        self.assertEqual(response.context['patient'], self.patient)

    def test_context_returns_correct_patient_of_two(self):
        response = self.client.get(reverse('patient_detail', args=['P1']))
        self.assertNotEqual(response.context['patient'], self.patient2)

    def test_context_only_contains_correct_patient_data(self):
        response = self.client.get(reverse('patient_detail', args=['P1']))
        self.assertEqual(response.status_code, 200)
        # look for just the patient
        self.assertEqual(response.context['patient'], self.patient)
        # check that only one is here and the other patient is not here anymore in the filter
        self.assertIn(self.cycle, response.context['cycles'])
        self.assertNotIn(self.cycle2, response.context['cycles'])
        # check that only one study is here and the other one is not
        self.assertIn(self.study, response.context['studies'])
        self.assertNotIn(self.study2, response.context['studies'])
    
    def test_patient_not_found(self):
        response = self.client.get(reverse('patient_detail', args=['NOPE']))
        self.assertEqual(response.status_code, 404)

    def test_correct_template(self):
        response = self.client.get(reverse('patient_detail', args=['P1']))
        self.assertTemplateUsed(response, 'patient_detail.html')

    # test if the dicom autofill just gives nothing
    def test_dicom_autofill_no_file_returns_empty(self):
        response = self.client.post(reverse('create_dicom'), {'autofill': '1'})
        self.assertEqual(response.context['saved_path'], '')
        self.assertFalse(response.context['file_label_ok'])