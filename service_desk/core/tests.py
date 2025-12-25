from django.test import TestCase
from django.utils import timezone
from .models import User, Order, OrderStatus
from .services import assign_master


class AssignMasterTests(TestCase):
    def setUp(self):
        self.dispatcher = User.objects.create_user(username="disp", password="123", role="dispatcher")
        self.master = User.objects.create_user(username="mast", password="123", role="master")
        self.order = Order.objects.create(
            category="Сантехника",
            description="Течет кран",
            address="Москва",
            customer_name="Иван",
            customer_contact="+79990000000",
            status=OrderStatus.NEW
        )

    def test_assign_changes_status(self):
        assign_master(self.order, self.dispatcher, self.master, planned_date=timezone.now())
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, OrderStatus.ASSIGNED)
        self.assertEqual(self.order.assigned_master_id, self.master.id)
        self.assertEqual(self.order.dispatcher_id, self.dispatcher.id)

