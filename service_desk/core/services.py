import logging
from django.utils import timezone
from django.core.mail import send_mail
from .models import Order, OrderHistory, OrderStatus, User

logger = logging.getLogger(__name__)


def send_email(to: str, subject: str, text: str):
    # Для dev можно оставить консольный backend (или настроить SMTP в settings.py)
    try:
        send_mail(subject, text, None, [to], fail_silently=True)
    except Exception as e:
        logger.warning("send_email failed: %s", e)


def send_sms(phone: str, text: str):
    # Заглушка для диплома
    logger.info("SMS to %s: %s", phone, text)


def log_status_change(order: Order, by_user: User | None, old_status: str, new_status: str, comment: str = ""):
    OrderHistory.objects.create(
        order=order,
        changed_by=by_user,
        old_status=old_status,
        new_status=new_status,
        comment=comment,
    )


def assign_master(order: Order, dispatcher: User, master: User, planned_date=None):
    if dispatcher.role != "dispatcher":
        raise PermissionError("Только диспетчер может назначать мастера.")
    if master.role != "master":
        raise ValueError("Назначаемый пользователь должен быть мастером.")
    if order.status not in [OrderStatus.NEW, OrderStatus.CANCELLED]:
        raise ValueError("Назначение возможно только для новой или отмененной заявки.")

    old = order.status
    order.assigned_master = master
    order.dispatcher = dispatcher
    order.status = OrderStatus.ASSIGNED
    if planned_date:
        order.planned_date = planned_date
    order.save()

    log_status_change(order, dispatcher, old, order.status, comment=f"Назначен мастер: {master.username}")

    # Уведомления (заглушка/минимальная логика)
    send_sms(order.customer_contact, f"Ваша заявка #{order.id} принята. Назначен мастер.")
    send_sms(master.username, f"Вам назначена заявка #{order.id} (адрес: {order.address}).")  # если username = телефон/логин


def start_order(order: Order, user: User):
    if user.role != "master":
        raise PermissionError("Начать работу может только мастер.")
    if order.assigned_master_id != user.id:
        raise PermissionError("Это не ваша заявка.")
    if order.status not in [OrderStatus.ASSIGNED]:
        raise ValueError("Перевод в 'В работе' возможен только из статуса 'Назначена'.")

    old = order.status
    order.status = OrderStatus.IN_PROGRESS
    order.save(update_fields=["status"])
    log_status_change(order, user, old, order.status, comment="Мастер начал работу")


def complete_order(order: Order, user: User):
    # Завершить может мастер (если назначен) или диспетчер (в дипломе допускается)
    if user.role == "master" and order.assigned_master_id != user.id:
        raise PermissionError("Это не ваша заявка.")
    if order.status != OrderStatus.IN_PROGRESS:
        raise ValueError("Завершение возможно только из статуса 'В работе'.")

    old = order.status
    order.status = OrderStatus.DONE
    order.completed_at = timezone.now()
    order.save(update_fields=["status", "completed_at"])
    log_status_change(order, user, old, order.status, comment="Заявка завершена")

