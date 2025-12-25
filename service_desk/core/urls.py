from django.urls import path
from . import views
from .views import OrderListView, AssignOrderView, StatsView

urlpatterns = [
    # Public
    path("order/new/", views.create_order, name="create_order"),
    path("order/success/<int:order_id>/", views.order_success, name="order_success"),

    # CBV примеры
    path("orders/", OrderListView.as_view(), name="order_list"),
    path("orders/<int:pk>/assign/", AssignOrderView.as_view(), name="assign_order"),
    path("analytics/stats/", StatsView.as_view(), name="order_stats"),

    # Dispatcher
    path("dispatcher/", views.dispatcher_orders, name="dispatcher_orders"),
    path("dispatcher/new_count/", views.dispatcher_new_count, name="dispatcher_new_count"),
    path("dispatcher/order/<int:order_id>/", views.dispatcher_order_detail, name="dispatcher_order_detail"),

    # Master
    path("master/", views.master_orders, name="master_orders"),
    path("master/order/<int:order_id>/", views.master_order_detail, name="master_order_detail"),
    path("master/order/<int:order_id>/start/", views.master_start, name="master_start"),
    path("master/order/<int:order_id>/complete/", views.master_complete, name="master_complete"),
]

