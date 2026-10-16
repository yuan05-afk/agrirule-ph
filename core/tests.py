from unittest import mock

from django.contrib.auth import get_user_model
from django.db import connection
from django.db.utils import OperationalError
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from expert_system.models import Consultation, ConsultationResult, Crop


class CorePerformanceTests(TestCase):
    def setUp(self):
        self.crop_a = Crop.objects.create(name='Rice', category=Crop.Category.STAPLES_ROOT, is_active=True)
        self.crop_b = Crop.objects.create(name='Corn', category=Crop.Category.STAPLES_ROOT, is_active=True)
        self.form_payload = {
            'season': 'wet',
            'soil_type': 'loam',
            'water_availability': 'moderate',
            'farm_type': 'irrigated',
            'soil_ph_category': 'neutral',
            'budget_level': 'medium',
            'crop_preference': 'staple',
        }

    def _make_consultation_with_results(self, idx):
        consultation = Consultation.objects.create(**self.form_payload)
        ConsultationResult.objects.create(consultation=consultation, crop=self.crop_a, score=60 + idx, is_recommended=True, rank_order=1)
        ConsultationResult.objects.create(consultation=consultation, crop=self.crop_b, score=40 + idx, is_recommended=False, rank_order=2)
        return consultation

    def _query_count_for(self, url):
        with CaptureQueriesContext(connection) as ctx:
            response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        return len(ctx)

    def test_consult_post_creates_results_for_all_active_crops(self):
        response = self.client.post(reverse('consult'), data=self.form_payload)
        self.assertEqual(response.status_code, 302)
        consultation = Consultation.objects.latest('id')
        self.assertEqual(
            ConsultationResult.objects.filter(consultation=consultation).count(),
            Crop.objects.filter(is_active=True).count(),
        )

    def test_history_query_count_stays_bounded(self):
        self._make_consultation_with_results(1)
        low_volume = self._query_count_for(reverse('history'))

        for idx in range(2, 22):
            self._make_consultation_with_results(idx)
        high_volume = self._query_count_for(reverse('history'))

        self.assertLessEqual(high_volume, low_volume + 2)
        self.assertLessEqual(high_volume, 10)

    def test_analytics_data_contract(self):
        consultation = self._make_consultation_with_results(1)
        response = self.client.get(reverse('result_analytics_data', args=[consultation.id]))
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        required_keys = {
            'summary',
            'top_recommendation_podium',
            'category_opportunity_chart',
            'condition_match_strength',
            'what_if_scenarios',
            'suitability_tiers',
            'tradeoff_comparison',
            'field_adjustments',
            'insights_rows',
            'interpretations',
        }
        self.assertTrue(required_keys.issubset(payload.keys()))


class DashboardPerformanceTests(TestCase):
    def setUp(self):
        self.crop_a = Crop.objects.create(name='Tomato', category=Crop.Category.VEGETABLE_SPICE, is_active=True)
        self.crop_b = Crop.objects.create(name='Onion', category=Crop.Category.VEGETABLE_SPICE, is_active=True)
        self.form_payload = {
            'season': 'dry',
            'soil_type': 'sandy',
            'water_availability': 'low',
            'farm_type': 'rainfed',
            'soil_ph_category': 'acidic',
            'budget_level': 'low',
            'crop_preference': 'vegetable',
        }
        User = get_user_model()
        self.staff = User.objects.create_user('staff', 'staff@example.com', 'secret123', is_staff=True)
        self.client.force_login(self.staff)

    def _make_consultation_with_results(self, idx):
        consultation = Consultation.objects.create(**self.form_payload)
        ConsultationResult.objects.create(consultation=consultation, crop=self.crop_a, score=70 + idx, is_recommended=True, rank_order=1)
        ConsultationResult.objects.create(consultation=consultation, crop=self.crop_b, score=50 + idx, is_recommended=False, rank_order=2)
        return consultation

    def test_dashboard_consultations_query_count_stays_bounded(self):
        self._make_consultation_with_results(1)
        with CaptureQueriesContext(connection) as low_ctx:
            response = self.client.get(reverse('dashboard_consultations'))
        self.assertEqual(response.status_code, 200)
        low_volume = len(low_ctx)

        for idx in range(2, 40):
            self._make_consultation_with_results(idx)
        with CaptureQueriesContext(connection) as high_ctx:
            response = self.client.get(reverse('dashboard_consultations'))
        self.assertEqual(response.status_code, 200)
        high_volume = len(high_ctx)

        self.assertLessEqual(high_volume, low_volume + 2)
        self.assertLessEqual(high_volume, 12)


class ResilienceTests(TestCase):
    """A database outage must degrade to a fast, readable 503 rather than a bare 500."""

    def test_healthz_reports_ok_when_database_is_reachable(self):
        response = self.client.get(reverse('healthz'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'status': 'ok', 'database': 'ok'})

    def test_healthz_reports_503_when_database_is_down(self):
        with mock.patch('core.views.connection.cursor', side_effect=OperationalError('db down')):
            response = self.client.get(reverse('healthz'))
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()['database'], 'unavailable')

    def test_page_shows_503_instead_of_500_when_database_is_down(self):
        with mock.patch('core.views._grouped_crops', side_effect=OperationalError('db down')):
            response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response['Retry-After'], '30')
        self.assertContains(response, 'temporarily unavailable', status_code=503)

    def test_json_endpoint_returns_json_503_when_database_is_down(self):
        with mock.patch('core.views.get_object_or_404', side_effect=OperationalError('db down')):
            response = self.client.get(reverse('result_analytics_data', args=[1]))
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json(), {'error': 'database_unavailable'})

    def test_unrelated_exceptions_are_not_swallowed(self):
        client = self.client_class(raise_request_exception=False)
        with mock.patch('core.views._grouped_crops', side_effect=ValueError('bug')):
            response = client.get(reverse('home'))
        self.assertEqual(response.status_code, 500)
