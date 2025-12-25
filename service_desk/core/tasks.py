from celery import shared_task

from .models import Order
from .services import send_sms, send_email


@shared_task
def send_notification(order_id: int, event_type: str) -> None:
    """
    Фоновая задача отправки уведомлений по заявке.
    event_type может быть, например: 'assigned', 'in_progress', 'done'.
    """
    try:
        order = Order.objects.get(id=order_id)
    except Order.DoesNotExist:
        return

    # Простейшая логика уведомлений; при необходимости можно расширить.
    subject = f"Заявка #{order.id}: {event_type}"
    text = f"Статус вашей заявки #{order.id} изменился: {order.get_status_display()}."

    if order.customer_contact:
        # Попробуем отправить и как SMS, и как email (для диплома это достаточно как заглушка)
        send_sms(order.customer_contact, text)
        send_email(order.customer_contact, subject, text)


