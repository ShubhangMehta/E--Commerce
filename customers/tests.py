from django.test import TestCase

# Create your tests here.
from django.contrib.auth.models import User
from .models import Plan, Subscription, Invoice
from django.utils import timezone

class BillingModelTests(TestCase):
    def setUp(self):
        self.plan = Plan.objects.create(
            name='Test Plan',
            plan_type='basic',
            description='Test description',
            price=29.99,
            billing_cycle='monthly'
        )
        
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

    def test_plan_creation(self):
        self.assertEqual(self.plan.name, 'Test Plan')
        self.assertEqual(self.plan.price, 29.99)
        self.assertTrue(self.plan.is_active)

    def test_subscription_creation(self):
        subscription = Subscription.objects.create(
            tenant=self.user.tenant,
            plan=self.plan,
            status='active',
            start_date=timezone.now(),
            end_date=timezone.now() + timezone.timedelta(days=30)
        )
        self.assertEqual(subscription.plan.name, 'Test Plan')
        self.assertEqual(subscription.status, 'active')

class BillingViewTests(TestCase):
    def test_plans_view(self):
        response = self.client.get('/billing/plans/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'billing/plans.html')