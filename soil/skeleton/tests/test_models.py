import datetime

from django.test import TestCase
from django.utils import timezone
from django.contrib.auth.models import User

from skeleton.models import Site
from skeleton.models import Farm

class FarmModelTests(TestCase):
    @classmethod
    def setUp(cls):
        User.objects.create_superuser(username='test', password='test', email='')
        user = User.objects.get(username='test')
        Farm.objects.create(name='Farm1', owner='Joe Bloggs', created_date=timezone.now(), created_by=user)

    def test_first_name_label(self):
        farm = Farm.objects.get(id=1)
        field_label = farm._meta.get_field('name').verbose_name
        self.assertEquals(field_label, 'name')

#class SiteModelTests(TestCase):
#
#    def test_
