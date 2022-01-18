from rest_framework.generics import ListCreateAPIView

from . import models
from .serializers import ProductInventorySerializer, OrdersSerializer


class ProductInventoryView(ListCreateAPIView):
    queryset = models.ProductInventory.objects.all()
    serializer_class = ProductInventorySerializer

    # view current inventory
    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    # restock
    def post(self, request, *args, **kwargs):
        pass


class OrdersView(ListCreateAPIView):
    queryset = models.Order.objects.all()
    serializer_class = OrdersSerializer

    # current orders
    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    # create order
    def post(self, request, *args, **kwargs):
        pass
