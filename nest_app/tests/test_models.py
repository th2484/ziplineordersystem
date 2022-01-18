from django.test import TestCase

from nest_app.models import ProductInventory, Product, Order, Shipment, ShippedItem, OrderedItem, ship_package, \
    log_shipment
from nest_app.processing import init_catalog, process_restock, process_order
import json

product_info = json.loads(open('./test_inventory.json').read())


def initialize_inventory():
    init_catalog(product_info)


def restock(restock_info):
    process_restock(restock_info)


def ship(package):
    ship_package(package)


def order(order_info):
    process_order(order_info)


class TestInitializeInventory(TestCase):
    def test_no_data_before_initialize_inventory(self):
        expected = 0
        actual = len(ProductInventory.objects.all())
        self.assertEqual(expected, actual)

    def test_no_shipments_before_init(self):
        expected = 0
        actual = len(Shipment.objects.all())
        self.assertEqual(expected, actual)

    def test_no_shipment_items_before_init(self):
        expected = 0
        actual = len(ShippedItem.objects.all())
        self.assertEqual(expected, actual)

    def test_no_orders_before_init(self):
        expected = 0
        actual = len(Order.objects.all())
        self.assertEqual(expected, actual)

    def test_no_order_items_before_init(self):
        expected = 0
        actual = len(OrderedItem.objects.all())
        self.assertEqual(expected, actual)


class TestProductInventory(TestCase):
    def setUp(self):
        initialize_inventory()

    def test_product_inventory_objects_present_after_init(self):
        expected = len(product_info)
        actual = len(ProductInventory.objects.all())
        self.assertEqual(expected, actual)

    def test_product_objects_present_after_init(self):
        expected = len(product_info)
        actual = len(Product.objects.all())
        self.assertEqual(expected, actual)


class TestRestock(TestCase):
    def setUp(self):
        initialize_inventory()
        self.product_id_0 = {"product_id": 0, "quantity": 30}
        self.product_id_0_partial_restock_1 = {"product_id": 0, "quantity": 1}
        self.product_id_0_partial_restock_4 = {"product_id": 0, "quantity": 4}
        self.product_id_6 = {"product_id": 6, "quantity": 8}
        self.non_existent_product = {"product_id": 100, "quantity": 8}

    def test_restock_product_that_is_not_present_in_inventory(self):
        try:
            restock([self.non_existent_product])
            self.assertTrue(False) # do not get here
        except Product.DoesNotExist as e:
            pass

    def test_inventory_quantity_incremented_on_restock_1_product(self):
        restock([self.product_id_0])

        product = Product.objects.get(id=0)
        actual = ProductInventory.objects.get(product=product).quantity

        expected = 30
        self.assertEqual(expected, actual)

    def test_inventory_quantity_incremented_on_restock_multiple_products(self):
        restock([self.product_id_0, self.product_id_6])

        product = Product.objects.get(id=0)
        actual_id_0 = ProductInventory.objects.get(product=product).quantity

        product = Product.objects.get(id=6)
        actual_id_6 = ProductInventory.objects.get(product=product).quantity

        expected_id_0 = 30
        expected_id_6 = 8
        self.assertEqual(expected_id_0, actual_id_0)
        self.assertEqual(expected_id_6, actual_id_6)

    def test_no_shipment_created_on_restock_if_no_pending_order_items(self):
        restock([self.product_id_0, self.product_id_6])
        expected = 0
        actual = len(Shipment.objects.all())
        self.assertEqual(expected, actual)

    def test_1_shipment_created_on_restock_if_1_pending_order_item_restocked(self):
        product = Product.objects.get(id=0)
        order1 = Order.objects.create(id=1234)
        ordered_item = OrderedItem.objects.create(
            id=123,
            product=product,
            order=order1,
            quantity=2,
            shipped_quantity=0
        )

        restock([self.product_id_0])
        expected = 1
        actual = len(Shipment.objects.all())
        self.assertEqual(expected, actual)

    def test_2_shipments_created_on_restock_if_1_pending_order_item_restocked_for_order_requiring_2_shipments_due_to_weight(self):
        product = Product.objects.get(id=0)
        order1 = Order.objects.create(id=1234)
        ordered_item = OrderedItem.objects.create(
            id=123,
            product=product,
            order=order1,
            quantity=4,
            shipped_quantity=0
        )

        restock([self.product_id_0])
        expected = 2
        actual = len(Shipment.objects.all())
        self.assertEqual(expected, actual)

    def test_3_shipments_created_on_restock_if_1_pending_order_item_restocked_for_order_requiring_3_shipments_due_to_weight(self):
        product = Product.objects.get(id=0)
        order1 = Order.objects.create(id=1234)
        ordered_item = OrderedItem.objects.create(
            id=123,
            product=product,
            order=order1,
            quantity=5,
            shipped_quantity=0
        )

        restock([self.product_id_0])
        expected = 3
        actual = len(Shipment.objects.all())
        self.assertEqual(expected, actual)

    def test_2_shipments_created_on_restock_if_2_pending_order_items_restocked(self):
        product1 = Product.objects.get(id=0)
        order1 = Order.objects.create(id=1234)
        ordered_item = OrderedItem.objects.create(
            id=123,
            product=product1,
            order=order1,
            quantity=2,
            shipped_quantity=0
        )

        product2 = Product.objects.get(id=6)
        order2 = Order.objects.create(id=12345)
        ordered_item = OrderedItem.objects.create(
            id=321,
            product=product2,
            order=order2,
            quantity=2,
            shipped_quantity=0
        )

        restock([self.product_id_0, self.product_id_6])
        expected = 2
        actual = len(Shipment.objects.all())
        self.assertEqual(expected, actual)

    def test_correct_item_is_added_to_order_on_restock(self):
        product = Product.objects.get(id=0)
        order1 = Order.objects.create(id=1234)
        ordered_item = OrderedItem.objects.create(
            id=123,
            product=product,
            order=order1,
            quantity=2,
            shipped_quantity=0
        )

        restock([self.product_id_0])
        expected = product.name
        items = Shipment.objects.get(order_id=1234).items
        actual = "".join(item.product.name for item in items)
        self.assertEqual(expected, actual)

    def test_order_shipped_quantity_updated_on_restock_when_pending_item_ships(self):
        product = Product.objects.get(id=0)
        order1 = Order.objects.create(id=1234)
        ordered_item = OrderedItem.objects.create(
            id=123,
            product=product,
            order=order1,
            quantity=2,
            shipped_quantity=0
        )

        restock([self.product_id_0])
        expected = 2
        actual = OrderedItem.objects.get(id=123).shipped_quantity
        self.assertEqual(expected, actual)

    def test_order_shipped_quantity_updated_on_restock_when_pending_item_ships_in_multiple_shipments_to_partially_fulfill_order(self):
        product = Product.objects.get(id=0)
        order1 = Order.objects.create(id=1234)
        ordered_item = OrderedItem.objects.create(
            id=123,
            product=product,
            order=order1,
            quantity=5,
            shipped_quantity=0
        )

        restock([self.product_id_0_partial_restock_4])
        expected = 4
        actual = OrderedItem.objects.get(id=123).shipped_quantity
        self.assertEqual(expected, actual)

    def test_order_quantity_needed_updated_on_restock_when_pending_item_ships_in_multiple_shipments_to_partially_fulfill_order(self):
        product = Product.objects.get(id=0)
        order1 = Order.objects.create(id=1234)
        ordered_item = OrderedItem.objects.create(
            id=123,
            product=product,
            order=order1,
            quantity=5,
            shipped_quantity=0
        )

        restock([self.product_id_0_partial_restock_4])
        expected = 1
        actual = OrderedItem.objects.get(id=123).quantity_needed
        self.assertEqual(expected, actual)

    def test_order_shipped_field_updated_to_true_on_restock_when_pending_item_ships_total_needed_quantity(self):
        product = Product.objects.get(id=0)
        order1 = Order.objects.create(id=1234)
        ordered_item = OrderedItem.objects.create(
            id=123,
            product=product,
            order=order1,
            quantity=2,
            shipped_quantity=0
        )

        restock([self.product_id_0])
        expected = True
        actual = OrderedItem.objects.get(id=123).shipped
        self.assertEqual(expected, actual)

    def test_1_shipment_created_for_partial_fulfillment_on_restock_if_1_pending_order_item_partially_restocked(self):
        product = Product.objects.get(id=0)
        order1 = Order.objects.create(id=1234)
        ordered_item = OrderedItem.objects.create(
            id=123,
            product=product,
            order=order1,
            quantity=2,
            shipped_quantity=0
        )

        restock([self.product_id_0_partial_restock_1])
        expected = 1
        actual = len(Shipment.objects.all())
        self.assertEqual(expected, actual)

    def test_quantity_needed_updated_after_partial_fulfillment_on_restock_if_1_pending_order_item_partially_restocked(self):
        product = Product.objects.get(id=0)
        order1 = Order.objects.create(id=1234)
        ordered_item = OrderedItem.objects.create(
            id=123,
            product=product,
            order=order1,
            quantity=2,
            shipped_quantity=0
        )

        restock([self.product_id_0_partial_restock_1])
        expected = 1
        actual = OrderedItem.objects.get(id=123).quantity_needed
        self.assertEqual(expected, actual)

    def test_2_shipment_objects_linked_to_order_object_when_order_shipped_in_2_shipments(self):
        product = Product.objects.get(id=0)
        order1 = Order.objects.create(id=1234)
        ordered_item = OrderedItem.objects.create(
            id=123,
            product=product,
            order=order1,
            quantity=2,
            shipped_quantity=0
        )
        # quantity of 1 restocked -> shipment 1 should deploy
        restock([self.product_id_0_partial_restock_1])

        # quantity of 1 restocked again -> shipment 2 should deploy
        restock([self.product_id_0_partial_restock_1])

        expected = 2
        actual = len(Order.objects.get(id=1234).shipments.all())
        self.assertEqual(expected, actual)


class TestOrder(TestCase):
    def setUp(self):
        initialize_inventory()
        self.test_order = {
            "order_id": 123,
            "requested": [
               {"product_id": 0, "quantity": 2},
               {"product_id": 10, "quantity": 4}
            ]
        }
        self.product_id_0 = {"product_id": 0, "quantity": 30}
        self.product_id_10 = {"product_id": 10, "quantity": 4}
        self.nonexistent_order = {
            "order_id": 111,
            "requested": [
               {"product_id": 100, "quantity": 2},
            ]
        }

    def test_order_product_that_is_not_present_in_inventory(self):
        try:
            order(self.nonexistent_order)
            self.assertTrue(False) # do not get here
        except Product.DoesNotExist as e:
            pass

    def test_order_object_created_when_process_order_called(self):
        order(self.test_order)

        expected = 1
        actual = len(Order.objects.all())
        self.assertEqual(expected, actual)

    def test_order_object_created_with_correct_ordered_items_when_process_order_called(self):
        order(self.test_order)
        product_id_0 = Product.objects.get(id=0)
        product_id_10 = Product.objects.get(id=10)
        expected = [product_id_0, product_id_10]
        ordered = Order.objects.get(id=123)
        actual = [item.product for item in ordered.items]
        self.assertEqual(expected, actual)

    def test_order_object_items_remain_pending_when_inventory_empty(self):
        order(self.test_order)

        expected = [False, False]
        ordered = Order.objects.get(id=123)
        ordered_items = OrderedItem.objects.filter(order=ordered)
        actual = [item.shipped for item in ordered_items]
        self.assertEqual(expected, actual)

    def test_order_object_items_marked_shipped_when_inventory_available(self):
        restock([self.product_id_0, self.product_id_10])

        order(self.test_order)

        expected = [True, True]
        ordered = Order.objects.get(id=123)
        ordered_items = OrderedItem.objects.filter(order=ordered)
        actual = [item.shipped for item in ordered_items]
        self.assertEqual(expected, actual)

    def test_order_object_items_marked_shipped_for_available_product_only_when_inventory_partially_available(self):
        restock([self.product_id_0])

        order(self.test_order)

        expected = [True, False]
        ordered = Order.objects.get(id=123)
        ordered_items = OrderedItem.objects.filter(order=ordered)
        actual = [item.shipped for item in ordered_items]
        self.assertEqual(expected, actual)

    def test_shipment_objects_are_created_when_available_items_are_ordered(self):
        restock([self.product_id_0, self.product_id_10])

        order(self.test_order)

        expected = 2
        ordered = Order.objects.get(id=123)
        actual = len(Shipment.objects.filter(order=ordered))
        self.assertEqual(expected, actual)


class TestShipment(TestCase):
    def setUp(self):
        initialize_inventory()
        self.product = Product.objects.get(id=1)
        self.product_id_7 = {"product_id": 7, "quantity": 30}
        self.order = Order.objects.create(
            id=123
        )
        self.ordered_items = OrderedItem.objects.create(
            id=123,
            product=self.product,
            order=self.order,
            quantity=2,
            shipped_quantity=0
        )
        self.test_package = {
            "order_id": 123,
            "shipped": [
                {
                    "product_id": 1,
                    "quantity": 2
                }
            ]
        }
        self.test_order1 = {
            "order_id": 137,
            "requested": [
                {"product_id": 7, "quantity": 1},
            ]
        }


    def test_shipment_object_is_created_when_ship_package_is_called(self):
        ship(self.test_package)

        expected = 1
        actual = len(Shipment.objects.all())
        self.assertEqual(expected, actual)

    def test_shipment_object_is_created_with_correct_shipped_item_when_ship_package_is_called_for_order_with_1_item(self):
        ship(self.test_package)

        expected = " ".join(item.product.name for item in self.order.items)
        actual = " ".join(item.product.name for item in Shipment.objects.get(order=self.order).items)
        self.assertEqual(expected, actual)


class E2E(TestCase):
    def setUp(self):
        self.test_order1 = {
            "order_id": 123,
            "requested": [
                {"product_id": 0, "quantity": 2},
            ]
        }
        self.test_order2 = {
            "order_id": 124,
            "requested": [
                {"product_id": 0, "quantity": 2},
                {"product_id": 10, "quantity": 8},
                {"product_id": 6, "quantity": 4}
            ]
        }
        self.product_id_0 = {"product_id": 0, "quantity": 30}
        self.product_id_10_partial_restock = {"product_id": 10, "quantity": 4}
        self.product_id_6 = {"product_id": 6, "quantity": 7}

    def test_full_workflow(self):
        initialize_inventory()
        restock([self.product_id_0, self.product_id_10_partial_restock])

        order(self.test_order1)
        expected = True
        actual = Order.objects.get(id=123).completed
        self.assertEqual(expected, actual)

        order(self.test_order2)
        expected = False
        actual = Order.objects.get(id=124).completed
        self.assertEqual(expected, actual)

        expected = [True, False, False]
        actual = [item.shipped for item in Order.objects.get(id=124).items]
        self.assertEqual(expected, actual)

        expected = [0,4,4]
        actual = [item.quantity_needed for item in Order.objects.get(id=124).items]
        self.assertEqual(expected, actual)

        expected = 3
        shipments_so_far = len(Shipment.objects.all())
        self.assertEqual(expected, shipments_so_far)

        restock([self.product_id_10_partial_restock])

        expected = [True, True, False]
        actual = [item.shipped for item in Order.objects.get(id=124).items]
        self.assertEqual(expected, actual)

        expected = 4
        shipments_so_far_again = len(Shipment.objects.all())
        self.assertEqual(expected, shipments_so_far_again)

        restock([self.product_id_6])

        expected = [True, True, True]
        actual = [item.shipped for item in Order.objects.get(id=124).items]
        self.assertEqual(expected, actual)

        expected = 5
        all_shipments = len(Shipment.objects.all())
        self.assertEqual(expected, all_shipments)

        shipments = Shipment.objects.all()
        masses = [shipment.total_mass for shipment in shipments]
        self.assertTrue(mass <= 1800 for mass in masses)
