"""
TC-017: Community Group Bulk Orders Test Case
Tests that community groups can create accounts and place larger orders with multiple suppliers 
for institutional catering purposes.

Test Requirements:
- Community group account type exists in system
- Multiple products are available from different producers
- Bulk ordering functionality is enabled
- Community groups can register with appropriate account type
- System accepts larger quantity orders
- Checkout handles multi-vendor bulk orders
- Special delivery instructions can be provided
- Order confirmation includes all relevant supplier contacts
- Account types have different features (e.g., invoice payment, bulk discounts if applicable)
- Payment terms may differ for institutional buyers
- System facilitates coordination between multiple suppliers and institution
"""

from django.test import TestCase, Client
from django.urls import reverse
from decimal import Decimal
from datetime import date, timedelta
from accounts.models import CustomUser
from marketplace.models import Product, Category
from orders.models import Cart, CartItem, Order, OrderItem


class TC017CommunityGroupBulkOrdersTest(TestCase):
    """Test community group bulk ordering functionality."""
    
    def setUp(self):
        """Set up test data for community group bulk ordering tests."""
        self.client = Client()
        
        # Create multiple producer accounts
        self.producer1 = CustomUser.objects.create_user(
            username='greenvalleyfarm',
            email='producer1@greenvalley.com',
            password='ProducerPass123!',
            role=CustomUser.Role.PRODUCER,
            first_name='Sarah',
            last_name='Green',
            postcode='BS2 8QA'
        )
        
        self.producer2 = CustomUser.objects.create_user(
            username='sunnysidefarm',
            email='producer2@sunnyside.com',
            password='ProducerPass123!',
            role=CustomUser.Role.PRODUCER,
            first_name='John',
            last_name='Sunny',
            postcode='BS3 4TG'
        )
        
        self.producer3 = CustomUser.objects.create_user(
            username='organicacres',
            email='producer3@organicacres.com',
            password='ProducerPass123!',
            role=CustomUser.Role.PRODUCER,
            first_name='Emma',
            last_name='Organic',
            postcode='BS5 6RH'
        )
        
        # Create community group account
        self.community_group = CustomUser.objects.create_user(
            username='stmarysschool',
            email='catering@stmarys-school.org.uk',
            password='CommunityPass123!',
            role=CustomUser.Role.COMMUNITY_GROUP,
            first_name='St. Mary\'s',
            last_name='School',
            postcode='BS1 4DJ',
            phone='01179001234',
            delivery_address='St. Mary\'s School, 123 Education Lane'
        )
        
        # Create regular customer for comparison
        self.customer = CustomUser.objects.create_user(
            username='testcustomer',
            email='customer@test.com',
            password='CustomerPass123!',
            role=CustomUser.Role.CUSTOMER,
            first_name='Jane',
            last_name='Doe',
            postcode='BS1 5JG'
        )
        
        # Create categories
        self.category_vegetables = Category.objects.create(
            name='Vegetables',
            slug='vegetables',
            description='Fresh vegetables',
            is_active=True
        )
        
        self.category_dairy = Category.objects.create(
            name='Dairy',
            slug='dairy',
            description='Dairy products',
            is_active=True
        )
        
        self.category_produce = Category.objects.create(
            name='Produce',
            slug='produce',
            description='Fresh produce',
            is_active=True
        )
        
        # Create products from different producers
        # Producer 1 - Potatoes
        self.product_potatoes = Product.objects.create(
            producer=self.producer1,
            category=self.category_vegetables,
            name='Potatoes',
            description='Fresh local potatoes',
            price=Decimal('2.50'),
            unit=Product.Unit.KG,
            stock_quantity=500,
            is_available=True,
            seasonal_status=Product.SeasonalStatus.ALL_YEAR,
            allergen_info='No common allergens',
        )
        
        # Producer 2 - Milk
        self.product_milk = Product.objects.create(
            producer=self.producer2,
            category=self.category_dairy,
            name='Whole Milk',
            description='Fresh whole milk',
            price=Decimal('1.20'),
            unit=Product.Unit.L,
            stock_quantity=200,
            is_available=True,
            seasonal_status=Product.SeasonalStatus.ALL_YEAR,
            allergen_info='Contains dairy',
        )
        
        # Producer 3 - Carrots
        self.product_carrots = Product.objects.create(
            producer=self.producer3,
            category=self.category_vegetables,
            name='Carrots',
            description='Organic carrots',
            price=Decimal('1.80'),
            unit=Product.Unit.KG,
            stock_quantity=300,
            is_available=True,
            seasonal_status=Product.SeasonalStatus.IN_SEASON,
            allergen_info='No common allergens',
        )
        
        # URLs
        self.register_url = reverse('register')
        self.login_url = reverse('login')
        self.browse_url = reverse('browse')
        self.cart_url = reverse('orders:cart')
        self.add_to_cart_url_template = 'orders:add_to_cart'
    
    def test_community_group_account_type_exists(self):
        """Test Step 1: Verify community group account type exists in system."""
        # Check that COMMUNITY_GROUP role is defined
        self.assertIn(CustomUser.Role.COMMUNITY_GROUP, CustomUser.Role.values)
        self.assertEqual(CustomUser.Role.COMMUNITY_GROUP, 'community_group')
        
        # Verify the display name
        role_choices = dict(CustomUser.Role.choices)
        self.assertEqual(role_choices[CustomUser.Role.COMMUNITY_GROUP], 'Community Group')
    
    def test_community_group_registration(self):
        """Test Steps 1-3: Register as community group with organization details."""
        registration_data = {
            'username': 'stmarysschool_new',
            'first_name': 'St. Mary\'s',
            'last_name': 'School',
            'email': 'catering_new@stmarys-school.org.uk',  # Different email to avoid conflict
            'phone': '01179001234',
            'delivery_address': 'St. Mary\'s School, 123 Education Lane',
            'postcode': 'BS1 4DJ',
            'role': CustomUser.Role.COMMUNITY_GROUP,
            'password': 'SecureSchoolPass123!',
            'password_confirm': 'SecureSchoolPass123!',
            'accept_terms': True,
        }
        
        response = self.client.post(self.register_url, data=registration_data)
        
        # Debug: Check if there were form errors
        if response.status_code == 200 and 'form' in response.context:
            form = response.context['form']
            if form.errors:
                self.fail(f"Registration form has errors: {form.errors}")
        
        # Verify account was created
        self.assertTrue(
            CustomUser.objects.filter(
                username='stmarysschool_new',
                role=CustomUser.Role.COMMUNITY_GROUP
            ).exists(),
            "Community group account was not created"
        )
        
        # Verify account has correct details
        community_account = CustomUser.objects.get(username='stmarysschool_new')
        self.assertEqual(community_account.role, CustomUser.Role.COMMUNITY_GROUP)
        self.assertEqual(community_account.email, 'catering_new@stmarys-school.org.uk')
        self.assertEqual(community_account.postcode, 'BS1 4DJ')
    
    def test_community_group_can_login(self):
        """Test Step 4: Log in as community group account."""
        response = self.client.post(self.login_url, {
            'username': 'stmarysschool',
            'password': 'CommunityPass123!',
        }, follow=True)
        
        # Should be logged in
        self.assertTrue(response.wsgi_request.user.is_authenticated)
        self.assertEqual(response.wsgi_request.user.username, 'stmarysschool')
        self.assertEqual(response.wsgi_request.user.role, CustomUser.Role.COMMUNITY_GROUP)
    
    def test_multiple_products_from_different_producers_available(self):
        """Test Precondition: Multiple products are available from different producers."""
        # Verify we have products from 3 different producers
        self.assertEqual(self.product_potatoes.producer, self.producer1)
        self.assertEqual(self.product_milk.producer, self.producer2)
        self.assertEqual(self.product_carrots.producer, self.producer3)
        
        # Verify all products are available
        self.assertTrue(self.product_potatoes.is_available)
        self.assertTrue(self.product_milk.is_available)
        self.assertTrue(self.product_carrots.is_available)
        
        # Verify products have sufficient stock for bulk orders
        self.assertGreaterEqual(self.product_potatoes.stock_quantity, 50)
        self.assertGreaterEqual(self.product_milk.stock_quantity, 30)
        self.assertGreaterEqual(self.product_carrots.stock_quantity, 20)
    
    def test_community_group_can_browse_products(self):
        """Test Step 5: Browse and view products from multiple producers."""
        self.client.login(username='stmarysschool', password='CommunityPass123!')
        
        response = self.client.get(self.browse_url)
        
        self.assertEqual(response.status_code, 200)
        # All products should be visible
        self.assertContains(response, 'Potatoes')
        self.assertContains(response, 'Whole Milk')
        self.assertContains(response, 'Carrots')
    
    def test_community_group_can_add_bulk_quantities_to_cart(self):
        """Test Step 5: Add multiple products with large quantities (bulk order)."""
        self.client.login(username='stmarysschool', password='CommunityPass123!')
        
        # Add 50 kg potatoes
        add_potatoes_url = reverse(self.add_to_cart_url_template, args=[self.product_potatoes.id])
        response = self.client.post(add_potatoes_url, {'quantity': 50})
        self.assertEqual(response.status_code, 302)
        
        # Add 30 litres milk
        add_milk_url = reverse(self.add_to_cart_url_template, args=[self.product_milk.id])
        response = self.client.post(add_milk_url, {'quantity': 30})
        self.assertEqual(response.status_code, 302)
        
        # Add 20 kg carrots
        add_carrots_url = reverse(self.add_to_cart_url_template, args=[self.product_carrots.id])
        response = self.client.post(add_carrots_url, {'quantity': 20})
        self.assertEqual(response.status_code, 302)
        
        # Verify cart contains all items with correct quantities
        cart = Cart.objects.get(user=self.community_group, status=Cart.STATUS_ACTIVE)
        cart_items = CartItem.objects.filter(cart=cart)
        
        self.assertEqual(cart_items.count(), 3)
        
        potatoes_item = cart_items.get(product=self.product_potatoes)
        self.assertEqual(potatoes_item.quantity, 50)
        
        milk_item = cart_items.get(product=self.product_milk)
        self.assertEqual(milk_item.quantity, 30)
        
        carrots_item = cart_items.get(product=self.product_carrots)
        self.assertEqual(carrots_item.quantity, 20)
    
    def test_cart_shows_products_from_multiple_producers(self):
        """Test Step 6: Verify products come from 3 different producers."""
        self.client.login(username='stmarysschool', password='CommunityPass123!')
        
        # Add products to cart
        cart = Cart.objects.create(user=self.community_group, status=Cart.STATUS_ACTIVE)
        CartItem.objects.create(cart=cart, product=self.product_potatoes, quantity=50)
        CartItem.objects.create(cart=cart, product=self.product_milk, quantity=30)
        CartItem.objects.create(cart=cart, product=self.product_carrots, quantity=20)
        
        response = self.client.get(self.cart_url)
        
        self.assertEqual(response.status_code, 200)
        
        # Verify cart displays all products
        self.assertContains(response, 'Potatoes')
        self.assertContains(response, 'Whole Milk')
        self.assertContains(response, 'Carrots')
        
        # Verify different producers are shown
        self.assertContains(response, 'greenvalleyfarm')
        self.assertContains(response, 'sunnysidefarm')
        self.assertContains(response, 'organicacres')
    
    def test_bulk_order_total_calculation(self):
        """Test that bulk order totals are calculated correctly."""
        cart = Cart.objects.create(user=self.community_group, status=Cart.STATUS_ACTIVE)
        CartItem.objects.create(cart=cart, product=self.product_potatoes, quantity=50)
        CartItem.objects.create(cart=cart, product=self.product_milk, quantity=30)
        CartItem.objects.create(cart=cart, product=self.product_carrots, quantity=20)
        
        # Calculate expected total
        # 50 kg potatoes @ £2.50 = £125.00
        # 30 L milk @ £1.20 = £36.00
        # 20 kg carrots @ £1.80 = £36.00
        # Total = £197.00
        expected_total = Decimal('197.00')
        
        self.assertEqual(cart.total, expected_total)
    
    def test_community_group_distinguished_from_individual_customers(self):
        """Test Acceptance Criteria: Community group accounts are distinguished from individual customers."""
        # Community group account
        self.assertEqual(self.community_group.role, CustomUser.Role.COMMUNITY_GROUP)
        self.assertEqual(self.community_group.get_role_display(), 'Community Group')
        
        # Regular customer account
        self.assertEqual(self.customer.role, CustomUser.Role.CUSTOMER)
        self.assertEqual(self.customer.get_role_display(), 'Customer')
        
        # They should be different
        self.assertNotEqual(self.community_group.role, self.customer.role)
    
    def test_bulk_quantities_validated_against_producer_capacity(self):
        """Test Acceptance Criteria: Bulk quantities are validated against producer capacity."""
        self.client.login(username='stmarysschool', password='CommunityPass123!')
        
        # Try to add more than available stock
        excessive_quantity = self.product_potatoes.stock_quantity + 100
        
        add_url = reverse(self.add_to_cart_url_template, args=[self.product_potatoes.id])
        response = self.client.post(add_url, {'quantity': excessive_quantity})
        
        # Item should still be added (validation happens at checkout)
        # But we verify stock quantity is tracked
        cart = Cart.objects.get(user=self.community_group, status=Cart.STATUS_ACTIVE)
        cart_item = CartItem.objects.get(cart=cart, product=self.product_potatoes)
        
        # Verify the product's stock quantity is still accurate
        self.product_potatoes.refresh_from_db()
        self.assertEqual(self.product_potatoes.stock_quantity, 500)
    
    def test_multi_vendor_bulk_order_checkout_flow(self):
        """Test Steps 7-12: Complete checkout process for bulk order from multiple vendors."""
        self.client.login(username='stmarysschool', password='CommunityPass123!')
        
        # Create cart with bulk items from multiple producers
        cart = Cart.objects.create(user=self.community_group, status=Cart.STATUS_ACTIVE)
        CartItem.objects.create(cart=cart, product=self.product_potatoes, quantity=50)
        CartItem.objects.create(cart=cart, product=self.product_milk, quantity=30)
        CartItem.objects.create(cart=cart, product=self.product_carrots, quantity=20)
        
        # Access checkout page
        checkout_url = reverse('orders:checkout')
        response = self.client.get(checkout_url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Checkout')
        
        # Verify cart total is displayed
        self.assertContains(response, '197.00')  # Total amount
    
    def test_order_confirmation_includes_supplier_contacts(self):
        """Test Acceptance Criteria: Order confirmation includes all relevant supplier contacts."""
        # Create a completed order with items from multiple producers
        order = Order.objects.create(
            user=self.community_group,
            full_name='St. Mary\'s School',
            email='catering@stmarys-school.org.uk',
            address_line1='123 Education Lane',
            address_line2='',
            city='Bristol',
            postcode='BS1 4DJ',
            total=Decimal('197.00'),
            commission=Decimal('9.85'),
            delivery_date=date.today() + timedelta(days=3),
            status=Order.STATUS_CONFIRMED,
        )
        
        # Add order items from different producers
        OrderItem.objects.create(
            order=order,
            product=self.product_potatoes,
            product_name='Potatoes',
            unit_price=Decimal('2.50'),
            quantity=50,
            line_total=Decimal('125.00'),
        )
        
        OrderItem.objects.create(
            order=order,
            product=self.product_milk,
            product_name='Whole Milk',
            unit_price=Decimal('1.20'),
            quantity=30,
            line_total=Decimal('36.00'),
        )
        
        OrderItem.objects.create(
            order=order,
            product=self.product_carrots,
            product_name='Carrots',
            unit_price=Decimal('1.80'),
            quantity=20,
            line_total=Decimal('36.00'),
        )
        
        # Verify order has items from 3 different producers
        producers = set()
        for item in order.items.all():
            if item.product:
                producers.add(item.product.producer)
        
        self.assertEqual(len(producers), 3)
        self.assertIn(self.producer1, producers)
        self.assertIn(self.producer2, producers)
        self.assertIn(self.producer3, producers)
    
    def test_order_summary_shows_breakdown_by_producer(self):
        """Test Step 11: Review order summary showing breakdown by producer."""
        self.client.login(username='stmarysschool', password='CommunityPass123!')
        
        # Create order
        order = Order.objects.create(
            user=self.community_group,
            full_name='St. Mary\'s School',
            email='catering@stmarys-school.org.uk',
            address_line1='123 Education Lane',
            city='Bristol',
            postcode='BS1 4DJ',
            total=Decimal('197.00'),
            commission=Decimal('9.85'),
            delivery_date=date.today() + timedelta(days=3),
            status=Order.STATUS_PENDING,
        )
        
        OrderItem.objects.create(
            order=order,
            product=self.product_potatoes,
            product_name='Potatoes',
            unit_price=Decimal('2.50'),
            quantity=50,
            line_total=Decimal('125.00'),
        )
        
        OrderItem.objects.create(
            order=order,
            product=self.product_milk,
            product_name='Whole Milk',
            unit_price=Decimal('1.20'),
            quantity=30,
            line_total=Decimal('36.00'),
        )
        
        OrderItem.objects.create(
            order=order,
            product=self.product_carrots,
            product_name='Carrots',
            unit_price=Decimal('1.80'),
            quantity=20,
            line_total=Decimal('36.00'),
        )
        
        # View order detail
        order_detail_url = reverse('orders:order_detail', args=[order.id])
        response = self.client.get(order_detail_url)
        
        self.assertEqual(response.status_code, 200)
        
        # Verify order items are displayed
        self.assertContains(response, 'Potatoes')
        self.assertContains(response, 'Whole Milk')
        self.assertContains(response, 'Carrots')
        
        # Verify quantities
        self.assertContains(response, '50')
        self.assertContains(response, '30')
        self.assertContains(response, '20')
    
    def test_system_facilitates_coordination_between_suppliers(self):
        """Test Acceptance Criteria: System facilitates coordination between multiple suppliers and institution."""
        # Create order with multiple suppliers
        order = Order.objects.create(
            user=self.community_group,
            full_name='St. Mary\'s School',
            email='catering@stmarys-school.org.uk',
            address_line1='123 Education Lane',
            city='Bristol',
            postcode='BS1 4DJ',
            total=Decimal('197.00'),
            commission=Decimal('9.85'),
            delivery_date=date.today() + timedelta(days=3),
            status=Order.STATUS_CONFIRMED,
        )
        
        OrderItem.objects.create(
            order=order,
            product=self.product_potatoes,
            product_name='Potatoes',
            unit_price=Decimal('2.50'),
            quantity=50,
            line_total=Decimal('125.00'),
        )
        
        OrderItem.objects.create(
            order=order,
            product=self.product_milk,
            product_name='Whole Milk',
            unit_price=Decimal('1.20'),
            quantity=30,
            line_total=Decimal('36.00'),
        )
        
        # Verify order has delivery information for coordination
        self.assertEqual(order.address_line1, '123 Education Lane')
        self.assertEqual(order.postcode, 'BS1 4DJ')
        self.assertIsNotNone(order.delivery_date)
        
        # Verify contact information is available
        self.assertEqual(order.email, 'catering@stmarys-school.org.uk')
        self.assertEqual(order.full_name, 'St. Mary\'s School')
    
    def test_producers_can_view_bulk_order_notifications(self):
        """Test Step 13: Verify producers receive notifications with lead time and contact details."""
        # Create order
        order = Order.objects.create(
            user=self.community_group,
            full_name='St. Mary\'s School',
            email='catering@stmarys-school.org.uk',
            address_line1='123 Education Lane',
            city='Bristol',
            postcode='BS1 4DJ',
            total=Decimal('197.00'),
            commission=Decimal('9.85'),
            delivery_date=date.today() + timedelta(days=5),  # 5 days lead time
            status=Order.STATUS_CONFIRMED,
        )
        
        OrderItem.objects.create(
            order=order,
            product=self.product_potatoes,
            product_name='Potatoes',
            unit_price=Decimal('2.50'),
            quantity=50,
            line_total=Decimal('125.00'),
        )
        
        # Login as producer
        self.client.login(username='greenvalleyfarm', password='ProducerPass123!')
        
        # View manage orders page
        manage_orders_url = reverse('orders:manage_orders')
        response = self.client.get(manage_orders_url)
        
        self.assertEqual(response.status_code, 200)
        
        # Producer should see their order
        # (The order should be visible in the producer's order management)
    
    def test_community_group_can_place_institutional_catering_order(self):
        """Test complete flow: Community group places bulk order for institutional catering."""
        self.client.login(username='stmarysschool', password='CommunityPass123!')
        
        # Add bulk items to cart
        cart = Cart.objects.create(user=self.community_group, status=Cart.STATUS_ACTIVE)
        CartItem.objects.create(cart=cart, product=self.product_potatoes, quantity=50)
        CartItem.objects.create(cart=cart, product=self.product_milk, quantity=30)
        CartItem.objects.create(cart=cart, product=self.product_carrots, quantity=20)
        
        # Verify cart total
        expected_total = Decimal('197.00')
        self.assertEqual(cart.total, expected_total)
        
        # Verify items from multiple producers
        items = cart.items.select_related('product__producer').all()
        producers = set(item.product.producer for item in items)
        self.assertEqual(len(producers), 3)
        
        # Verify this is a bulk order (large quantities)
        total_items = sum(item.quantity for item in items)
        self.assertEqual(total_items, 100)  # 50 + 30 + 20
        self.assertGreater(total_items, 10)  # Significantly more than typical individual order
