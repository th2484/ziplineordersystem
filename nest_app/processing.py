import random

from nest_app.models import Product, ProductInventory, OrderedItem, Order

MAX_SHIPMENT_MASS = 1800


def init_catalog(product_info):
    """Initialize the Product and ProductInventory table using passed in product_info json"""

    for product in product_info:
        Product.objects.create(
            id=product["product_id"],
            name=product["product_name"],
            mass_g=product["mass_g"]
        )

    for product in Product.objects.all():
        ProductInventory.objects.create(
            id=(str(random.randint(100000, 999999))),
            product=product,
            quantity=0
        )


def process_restock(restock):
    """Restock products by increasing quantity available in ProductInventory table"""

    for restocked_product in restock:
        product = Product.objects.get(id=restocked_product["product_id"])

        inventory_product = ProductInventory.objects.get(product=product)
        inventory_product.quantity = restocked_product["quantity"]
        inventory_product.save()

        # checks for pending ordered items
        order_items = OrderedItem.objects.filter(product=product)
        pending_order_items = [item for item in order_items if not item.shipped]

        for item in pending_order_items:
            # sufficient inventory to fill order
            if inventory_product.quantity >= item.quantity_needed:
                fulfill_item_order(item, inventory_product)
            # non zero inventory but not sufficient to complete order
            elif inventory_product.quantity > 0:
                partial_fulfill_item_order(item, inventory_product)
            else:
                break


def process_order(order):
    """Process incoming order json, ship available items"""

    order_obj = Order.objects.create(
        id=order["order_id"]
    )

    not_available = []

    for item in order["requested"]:
        product = Product.objects.get(id=item["product_id"])
        ordered_item = OrderedItem.objects.create(
            id=str(random.randint(100000, 999999)),
            product=product,
            order=order_obj,
            quantity=item["quantity"],
            shipped_quantity=0
        )
        available_quantity = ProductInventory.objects.get(product=product).quantity
        if ordered_item.quantity_needed > available_quantity:
            not_available.append(ordered_item)

    order_obj.save()

    if not not_available and order_obj.total_mass <= MAX_SHIPMENT_MASS:
        order_obj.ship()
    else:
        order_items = OrderedItem.objects.filter(order=order_obj)
        pending_order_items = [item for item in order_items if not item.shipped]

        for item in pending_order_items:
            inventory_product = ProductInventory.objects.get(product=item.product)
            # sufficient inventory to fill order
            if inventory_product.quantity >= item.quantity_needed:
                fulfill_item_order(item, inventory_product)
            # non zero inventory but not sufficient to complete order
            elif inventory_product.quantity > 0:
                partial_fulfill_item_order(item, inventory_product)
            else:
                continue


def fulfill_item_order(item, inventory_product):
    item.ship(item.quantity_needed)
    inventory_product.quantity -= item.quantity_needed
    inventory_product.save()


def partial_fulfill_item_order(item, inventory_product):
    item.ship(inventory_product.quantity)
    inventory_product.quantity = 0
    inventory_product.save()
