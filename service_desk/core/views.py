from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.db.models import Count
from django.http import JsonResponse, HttpResponseForbidden, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views import View
from django.views.generic import ListView, TemplateView

from .forms import PublicOrderForm, AssignOrderForm, OrderForm
from .models import Order, OrderStatus, User
from .services import assign_master, start_order, complete_order

# ---------- Auth ----------


def home_redirect(request):
    if request.user.is_authenticated:
        if getattr(request.user, "role", None) == "dispatcher":
            return redirect("dispatcher_orders")
        return redirect("master_orders")
    return redirect("create_order")


def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username", "")
        password = request.POST.get("password", "")
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return home_redirect(request)
        messages.error(request, "Неверный логин или пароль.")
    return render(request, "auth/login.html")


def logout_view(request):
    logout(request)
    return redirect("login")


def require_role(user, role: str) -> bool:
    return user.is_authenticated and getattr(user, "role", None) == role


# ---------- CBV по описанию (OrderListView, AssignOrderView, StatsView) ----------


class OrderListView(LoginRequiredMixin, ListView):
    """
    OrderListView – показать список всех заявок.
    Берёт все объекты Order и отдаёт их в шаблон orders/order_list.html
    под именем 'orders'.
    """

    model = Order
    template_name = "orders/order_list.html"
    context_object_name = "orders"


class AssignOrderView(LoginRequiredMixin, View):
    """
    AssignOrderView – назначить мастера на заявку.
    Ожидает POST с полем master_id.
    """

    def post(self, request, pk):
        order = get_object_or_404(Order, pk=pk)

        if not require_role(request.user, "dispatcher"):
            return HttpResponseForbidden("Доступ только для диспетчера.")

        master_id = request.POST.get("master_id")
        master = get_object_or_404(User, pk=master_id, role="master")

        # Используем уже существующую бизнес-логику
        assign_master(order, request.user, master)

        # по смыслу — вернуть пользователя к списку заявок
        return redirect("order_list")


class StatsView(LoginRequiredMixin, TemplateView):
    """
    StatsView – страница статистики по заявкам.
    """

    template_name = "analytics/stats.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["order_counts"] = (
            Order.objects.values("status")
            .annotate(count=Count("id"))
            .order_by("status")
        )
        return context


# ---------- Public ----------


def create_order(request):
    if request.method == "POST":
        form = PublicOrderForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.status = OrderStatus.NEW
            order.save()
            return redirect("order_success", order_id=order.id)
    else:
        form = PublicOrderForm()

    return render(request, "public/order_form.html", {"form": form})


def order_success(request, order_id: int):
    order = get_object_or_404(Order, id=order_id)
    return render(request, "public/order_success.html", {"order": order})


# ---------- Dispatcher ----------


@login_required
def dispatcher_orders(request):
    if not require_role(request.user, "dispatcher"):
        return HttpResponseForbidden("Доступ только для диспетчера.")

    qs = Order.objects.select_related("assigned_master").order_by("-created_at")

    status = request.GET.get("status")
    if status in [s[0] for s in OrderStatus.choices]:
        qs = qs.filter(status=status)

    paginator = Paginator(qs, 20)
    page = paginator.get_page(request.GET.get("page", 1))

    return render(request, "dispatcher/orders_list.html", {
        "page": page,
        "status_filter": status or "",
        "statuses": OrderStatus.choices,
    })


@login_required
def dispatcher_new_count(request):
    if not require_role(request.user, "dispatcher"):
        return JsonResponse({"error": "forbidden"}, status=403)
    cnt = Order.objects.filter(status=OrderStatus.NEW).count()
    return JsonResponse({"new_count": cnt})


@login_required
def dispatcher_order_detail(request, order_id: int):
    if not require_role(request.user, "dispatcher"):
        return HttpResponseForbidden("Доступ только для диспетчера.")

    order = get_object_or_404(Order.objects.select_related("assigned_master", "dispatcher"), id=order_id)
    masters = User.objects.filter(role="master", is_active=True).order_by("first_name", "username")

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "assign":
            form = AssignOrderForm(request.POST)
            if not form.is_valid():
                return HttpResponseBadRequest("Некорректные данные назначения.")

            master = get_object_or_404(User, id=form.cleaned_data["master_id"], role="master")
            planned_date = form.cleaned_data.get("planned_date")
            try:
                assign_master(order, request.user, master, planned_date=planned_date)
                messages.success(request, f"Заявка #{order.id} назначена мастеру {master.username}.")
            except Exception as e:
                messages.error(request, f"Ошибка назначения: {e}")

            return redirect("dispatcher_order_detail", order_id=order.id)

        if action == "cancel":
            if order.status in [OrderStatus.DONE]:
                messages.error(request, "Нельзя отменить завершенную заявку.")
            else:
                old = order.status
                order.status = OrderStatus.CANCELLED
                order.dispatcher = request.user
                order.save(update_fields=["status", "dispatcher"])
                from .services import log_status_change
                log_status_change(order, request.user, old, order.status, comment="Отменено диспетчером")
                messages.success(request, f"Заявка #{order.id} отменена.")
            return redirect("dispatcher_order_detail", order_id=order.id)

    return render(request, "dispatcher/order_detail.html", {
        "order": order,
        "history": order.history.all(),
        "masters": masters,
        "statuses": OrderStatus,
        "map_url": f"https://yandex.ru/maps/?text={order.address}" if order.address else "",
    })


# ---------- Master ----------


@login_required
def master_orders(request):
    if not require_role(request.user, "master"):
        return HttpResponseForbidden("Доступ только для мастера.")

    qs = (Order.objects
          .filter(assigned_master=request.user)
          .exclude(status=OrderStatus.DONE)
          .order_by("-created_at"))

    return render(request, "master/orders_list.html", {"orders": qs})


@login_required
def master_order_detail(request, order_id: int):
    if not require_role(request.user, "master"):
        return HttpResponseForbidden("Доступ только для мастера.")

    order = get_object_or_404(Order, id=order_id, assigned_master=request.user)
    return render(request, "master/order_detail.html", {
        "order": order,
        "history": order.history.all(),
        "statuses": OrderStatus,
        "map_url": f"https://yandex.ru/maps/?text={order.address}" if order.address else "",
    })


@login_required
def master_start(request, order_id: int):
    if not require_role(request.user, "master"):
        return JsonResponse({"error": "forbidden"}, status=403)
    if request.method != "POST":
        return JsonResponse({"error": "method"}, status=405)

    order = get_object_or_404(Order, id=order_id)
    try:
        start_order(order, request.user)
        return JsonResponse({"ok": True})
    except Exception as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=400)


@login_required
def master_complete(request, order_id: int):
    if not require_role(request.user, "master"):
        return JsonResponse({"error": "forbidden"}, status=403)
    if request.method != "POST":
        return JsonResponse({"error": "method"}, status=405)

    order = get_object_or_404(Order, id=order_id)
    try:
        complete_order(order, request.user)
        return JsonResponse({"ok": True})
    except Exception as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=400)

