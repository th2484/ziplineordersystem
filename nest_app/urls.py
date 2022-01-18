from django.urls import path, include
from rest_framework import routers

from . import views

router = routers.DefaultRouter()

urlpatterns = [
    path('', include(router.urls), name="view_sets"),
    path(r"orders", views.OrdersView.as_view()),
    path(r"inventory", views.ProductInventoryView.as_view()),
]
