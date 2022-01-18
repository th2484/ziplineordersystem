import random

from django.db import models

MAX_SHIPMENT_MASS = 1800


class Product(models.Model):
    id = models.CharField(max_length=50, primary_key=True)
    name = models.CharField(max_length=50)
    mass_g = models.IntegerField(default=0)


class ProductInventory(models.Model):
    id = models.CharField(max_length=50, primary_key=True)
    product = models.ForeignKey(Product, on_delete=models.DO_NOTHING, null=False)
    quantity = models.IntegerField(default=0)


class Order(models.Model):
    id = models.CharField(max_length=50, primary_key=True)

    @property
    def items(self):
        return OrderedItem.objects.filter(order_id=self.id)

    @property
    def completed(self):
        for item in self.items:
            if not item.shipped:
                return False
        return True

    @property
    def total_mass(self):
        masses = [item.total_mass for item in self.items]
        return sum(masses, 0)

    def ship(self):
        if self.total_mass <= MAX_SHIPMENT_MASS:
            shipped = []
            for item in self.items:
                shipped_item = {"product_id": item.product.id, "quantity": item.quantity_needed}
                item.update_quantity(item.quantity_needed)
                shipped.append(shipped_item)

            shipment = {"order_id": self.id, "shipped": shipped}
            ship_package(shipment)
        else:
            raise Exception


class OrderedItem(models.Model):
    id = models.CharField(max_length=50, primary_key=True)
    product = models.ForeignKey(Product, on_delete=models.DO_NOTHING, null=False)
    order = models.ForeignKey(Order, on_delete=models.DO_NOTHING, null=False)
    quantity = models.IntegerField(default=1)
    shipped_quantity = models.IntegerField(default=0)

    @property
    def total_mass(self):
        if self.quantity == 1:
            return self.product.mass_g
        else:
            return self.product.mass_g * self.quantity

    @property
    def shipped(self):
        return self.quantity == self.shipped_quantity

    def ship(self, quantity):
        if (self.product.mass_g * quantity) < MAX_SHIPMENT_MASS:
            self.update_quantity(quantity)
            shipment = {"order_id": self.order.id,
                        "shipped": [
                            {"product_id": self.product.id, "quantity": quantity}
                        ]}
            ship_package(shipment)
        else:
            shipment_mass = 0
            quantity_in_shipment = 0

            for q in range(0, quantity):
                if (shipment_mass + self.product.mass_g) < MAX_SHIPMENT_MASS:
                    shipment_mass += self.product.mass_g
                    quantity_in_shipment += 1
                else:
                    break

            if quantity_in_shipment > 0:
                self.update_quantity(quantity_in_shipment)
                shipped_item = {"product_id": self.product.id, "quantity": quantity_in_shipment}
                shipment = {"order_id": self.order.id, "shipped": [shipped_item]}
                ship_package(shipment)
                remaining_to_ship = quantity - quantity_in_shipment
                if remaining_to_ship != 0:
                    self.ship(remaining_to_ship)

            else:
                print("Item is too heavy to ship")
                raise Exception

    @property
    def quantity_needed(self):
        return self.quantity - self.shipped_quantity

    def update_quantity(self, quantity_shipped):
        self.shipped_quantity += quantity_shipped
        self.save()


class Shipment(models.Model):
    id = models.CharField(max_length=50, primary_key=True)
    order = models.ForeignKey(Order, on_delete=models.DO_NOTHING, related_name="shipments")

    @property
    def items(self):
        return ShippedItem.objects.filter(shipment=self.id)

    @property
    def total_mass(self):
        return sum([item.total_mass for item in self.items], 0)


class ShippedItem(models.Model):
    id = models.CharField(max_length=50, primary_key=True)
    product = models.ForeignKey(Product, on_delete=models.DO_NOTHING, null=False)
    order = models.ForeignKey(Order, on_delete=models.DO_NOTHING, null=False)
    shipment = models.ForeignKey(Shipment, on_delete=models.DO_NOTHING, null=False)
    quantity = models.IntegerField(default=1)

    @property
    def total_mass(self):
        if self.quantity == 1:
            return self.product.mass_g
        else:
            return self.product.mass_g * self.quantity


def ship_package(shipment):
    order = Order.objects.get(id=shipment["order_id"])
    shipment_obj = Shipment.objects.create(
        id=(str(random.randint(100000, 999999))),
        order=order
    )

    for shipped_item in shipment["shipped"]:
        product = Product.objects.get(id=shipped_item["product_id"])
        ShippedItem.objects.create(
            id=(str(random.randint(100000, 999999))),
            product=product,
            order=order,
            shipment=shipment_obj,
            quantity=shipped_item["quantity"]
        )
    shipment_items = [(shipment_item.product.name, shipment_item.quantity) for shipment_item in shipment_obj.items]

    if shipment_obj.total_mass < MAX_SHIPMENT_MASS:
        output = log_shipment(shipment_obj, shipment_items)
        print(output)
    else:
        raise Exception('Shipment could not be deployed. Shipment weight greater than max capacity.')


def log_shipment(shipment_obj, shipment_items):
    output = (f"\n=====================================\n"
              f"Shipment deployed: \n"
              f"ID - {shipment_obj.id}\n"
              f"ORDER ID- {shipment_obj.order.id}\n"
              f"ITEMS/QUANTITY: {shipment_items}\n"
              f"SHIPMENT WEIGHT (g): {shipment_obj.total_mass}\n"
              f"=====================================\n")
    return output
