from rest_framework import serializers

from nest_app import models


class ProductInventorySerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ProductInventory
        fields = "__all__"


class OrdersSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Order
        fields = "__all__"

