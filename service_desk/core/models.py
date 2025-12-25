from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class User(AbstractUser):
    ROLE_CHOICES = [
        ("dispatcher", "Диспетчер"),
        ("master", "Мастер"),
    ]
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default="master")

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_role_display()})"


class OrderStatus(models.TextChoices):
    NEW = "new", "Новая"
    ASSIGNED = "assigned", "Назначена"
    IN_PROGRESS = "in_progress", "В работе"
    DONE = "done", "Завершена"
    CANCELLED = "cancelled", "Отменена"


class Order(models.Model):
    category = models.CharField(max_length=100)
    description = models.TextField()
    address = models.CharField(max_length=255, blank=True, default="")
    customer_name = models.CharField(max_length=100)
    customer_contact = models.CharField(max_length=100)  # телефон или email

    status = models.CharField(max_length=20, choices=OrderStatus.choices, default=OrderStatus.NEW)
    created_at = models.DateTimeField(auto_now_add=True)

    assigned_master = models.ForeignKey(
        User,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="assigned_orders",
        limit_choices_to={"role": "master"},
    )
    dispatcher = models.ForeignKey(
        User,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="dispatched_orders",
        limit_choices_to={"role": "dispatcher"},
    )

    planned_date = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def mark_done(self, by_user: User):
        self.status = OrderStatus.DONE
        self.completed_at = timezone.now()
        self.save(update_fields=["status", "completed_at"])

    def __str__(self):
        return f"Заявка #{self.id} — {self.get_status_display()}"


class OrderHistory(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="history")
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    old_status = models.CharField(max_length=20, choices=OrderStatus.choices)
    new_status = models.CharField(max_length=20, choices=OrderStatus.choices)
    timestamp = models.DateTimeField(auto_now_add=True)
    comment = models.TextField(blank=True, default="")

    class Meta:
        ordering = ["-timestamp"]

    def __str__(self):
        return f"#{self.order_id}: {self.old_status} -> {self.new_status}"

