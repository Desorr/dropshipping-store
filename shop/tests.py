import zoneinfo
from decimal import Decimal
from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone
from .models import Product, Payment, OrderItem, Order


class TestDataBase(TestCase):
    fixtures = [
        "shop/fixtures/data.json"
    ]

    def setUp(self):
        self.user = User.objects.get(username='admin')
        self.p = Product.objects.all().first()

    def test_user_exists(self):
        users = User.objects.all()
        users_number = users.count()
        user = users.first()
        self.assertEqual(users_number, 1)
        self.assertEqual(user.username, 'admin')
        self.assertTrue(user.is_superuser)

    def test_user_check_password(self):
        self.assertTrue(self.user.check_password('admin'))

    def test_all_data(self):
        self.assertGreater(Product.objects.all().count(), 0)
        self.assertEqual(Order.objects.all().count(), 0)
        self.assertEqual(OrderItem.objects.all().count(), 0)
        self.assertEqual(Payment.objects.all().count(), 0)

    def find_cart_number(self):
        cart_number = Order.objects.filter(user=self.user,
                                           status=Order.STATUS_CART
                                           ).count()
        return cart_number

    def test_function_get_cart(self):
        """Check cart number
        1. No carts
        2. Create cart
        3. Get created cart
        """

        # 1
        self.assertEqual(self.find_cart_number(), 0)

        # 2
        Order.get_cart(self.user)
        self.assertEqual(self.find_cart_number(), 1)

        # 3
        Order.get_cart(self.user)
        self.assertEqual(self.find_cart_number(), 1)

    def test_cart_older_7_days(self):
        """if cart older than 7 days it must be deleted
        1. get cart and make it older
        """

        cart = Order.get_cart(self.user)
        cart.creation_time = timezone.datetime(2000, 1, 1, tzinfo=zoneinfo.ZoneInfo('UTC'))
        cart.save()
        cart = Order.get_cart(self.user)
        self.assertEqual((timezone.now() - cart.creation_time).days, 0)

    def test_recalculate_order_amount_after_changing_orderitem(self):
        """Checking cart amount
        1. Get order amount before any changing
        2. -----""----- after adding item
        3. -----""----- after deleting item
        """

        # 1
        cart = Order.get_cart(self.user)
        self.assertEqual(cart.amount, Decimal(0))

        # 2
        i = OrderItem.objects.create(order=cart, product=self.p, price=2, quantity=2)
        i = OrderItem.objects.create(order=cart, product=self.p, price=2, quantity=3)
        cart = Order.get_cart(self.user)
        self.assertEqual(cart.amount, Decimal(10))

        # 3
        i.delete()
        cart = Order.get_cart(self.user)
        self.assertEqual(cart.amount, Decimal(4))

    def test_cart_status_changing_after_applying_make_order(self):
        """Check cart status change after Order.make_order()
        1. Attempt to change the status for on empty cart
        2. Attempt to change the status for on a non-empty cart
        """
        # 1
        cart = Order.get_cart(self.user)
        cart.make_order()
        self.assertEqual(cart.status, Order.STATUS_CART)
        # 2
        OrderItem.objects.create(order=cart, product=self.p, price=2, quantity=2)
        cart.make_order()
        self.assertEqual(cart.status, Order.STATUS_WAITING_FOR_PAYMENT)

    def test_method_get_amount_of_unpaid_orders(self):
        """Check @staticmethod get_amount_of_unpaid_orders() for several cases:
        1. Before creating cart
        2. After creating cart
        3. After cart.make_order()
        4. After order is paid
        5. After delete all orders
        """

        # 1
        amount = Order.get_amount_of_unpaid_orders(self.user)
        self.assertEqual(amount, Decimal(0))

        # 2
        cart = Order.get_cart(self.user)
        OrderItem.objects.create(order=cart, product=self.p, price=2, quantity=2)
        amount = Order.get_amount_of_unpaid_orders(self.user)
        self.assertEqual(amount, Decimal(0))

        # 3
        cart.make_order()
        amount = Order.get_amount_of_unpaid_orders(self.user)
        self.assertEqual(amount, Decimal(4))

        # 4
        cart.status = Order.STATUS_PAID
        cart.save()
        amount = Order.get_amount_of_unpaid_orders(self.user)
        self.assertEqual(amount, Decimal(0))

        # 5
        Order.objects.all().delete()
        amount = Order.get_amount_of_unpaid_orders(self.user)
        self.assertEqual(amount, Decimal(0))

    def test_method_get_balance(self):
        """Check @staticmethod get_balance for several cases:
        1. Before adding payment
        2. After adding payment
        3. After adding some payment
        4. No payment
        """

        # 1
        amount = Payment.get_balance(self.user)
        self.assertEqual(amount, Decimal(0))

        # 2
        Payment.objects.create(user=self.user, amount=100)
        amount = Payment.get_balance(self.user)
        self.assertEqual(amount, Decimal(100))

        # 3
        Payment.objects.create(user=self.user, amount=-50)
        amount = Payment.get_balance(self.user)
        self.assertEqual(amount, Decimal(50))

        # 4
        Payment.objects.all().delete()
        amount = Payment.get_balance(self.user)
        self.assertEqual(amount, Decimal(0))


    def test_auto_payment_after_apply_make_order_true(self):
        """Check auto payment after applying make_order():
        1. There is a required amount
        """
        Order.objects.all().delete()
        cart = Order.get_cart(self.user)
        OrderItem.objects.create(order=cart, product=self.p, price=2, quantity=2)
        self.assertEqual(Payment.get_balance(self.user), Decimal(0))
        cart.make_order()
        self.assertEqual(Payment.get_balance(self.user), Decimal(0))

    def test_auto_payment_after_apply_make_order_false(self):
        """Check auto payment after applying make_order():
        1. There isn`t a required amount
        """
        Order.objects.all().delete()
        cart = Order.get_cart(self.user)
        OrderItem.objects.create(order=cart, product=self.p, price=2, quantity=50000)
        cart.make_order()
        self.assertEqual(Payment.get_balance(self.user), Decimal(0))

    def test_auto_payment_after_add_required_payment(self):
        Payment.objects.create(user=self.user, amount=0)
        self.assertEqual(Payment.get_balance(self.user), Decimal(0))
        amount = Order.get_amount_of_unpaid_orders(self.user)
        self.assertEqual(amount, Decimal(0))

    def test_auto_payment_for_earlier_order(self):
        cart = Order.get_cart(self.user)
        OrderItem.objects.create(order=cart, product=self.p, price=2, quantity=500)
        Payment.objects.create(user=self.user, amount=1000)
        self.assertEqual(Payment.get_balance(self.user), Decimal(1000))
        amount = Order.get_amount_of_unpaid_orders(self.user)
        self.assertEqual(amount, Decimal(0))

    def test_auto_payment_for_earlier_order(self):
        cart = Order.get_cart(self.user)
        OrderItem.objects.create(order=cart, product=self.p, price=2, quantity=500)
        Payment.objects.create(user=self.user, amount=10000)
        self.assertEqual(Payment.get_balance(self.user), Decimal(10000))
        amount = Order.get_amount_of_unpaid_orders(self.user)
        self.assertEqual(amount, Decimal(0))
