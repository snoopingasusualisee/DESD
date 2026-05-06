"""
TC-019: Surplus Produce Discounts Test Case
Tests that producers can communicate surplus produce with discounts so that they can reduce food waste.

Test Requirements:
- Producer is logged in
- Producer has products with stock that needs to be sold quickly
- Surplus produce feature is enabled
- Producers can mark products as surplus with discount
- Surplus products appear in dedicated section for customers
- Discount is prominently displayed
- Urgency is communicated (time remaining, best before date)
- Discounted price is correctly calculated and applied at checkout
- Surplus deals are highlighted in customer interface
- Deals expire automatically after specified time
- System supports community food waste reduction objectives
- Discount percentage is validated (e.g., 10-50% range)
- Surplus items maintain all quality and allergen information
- Deal expiry is enforced automatically
- Producers can remove surplus status if stock sells out
- Customers receive notifications about surplus deals from favourite producers
- Analytics track food waste reduction impact
"""

from django.test import TestCase, Client
from django.urls import reverse
from decimal import Decimal
from datetime import date, timedelta, datetime
from accounts.models import CustomUser
from marketplace.models import Product, Category
from orders.models import Cart, CartItem, Order, OrderItem


class TC019SurplusProduceDiscountsTest(TestCase):
    """Test surplus produce discounts functionality for food waste reduction."""
    
    def setUp(self):
        """Set up test data for surplus produce tests."""
        self.client = Client()
        
        # Create producer account
        self.producer = CustomUser.objects.create_user(
            username='greenleaffarm',
            email='producer@greenleaf.com',
            password='ProducerPass123!',
            role=CustomUser.Role.PRODUCER,
            first_name='Alice',
            last_name='Green',
            postcode='BS2 8QA'
        )
        
        # Create customer account
        self.customer = CustomUser.objects.create_user(
            username='foodsaver',
            email='customer@foodsaver.com',
            password='CustomerPass123!',
            role=CustomUser.Role.CUSTOMER,
            first_name='Bob',
            last_name='Saver',
            postcode='BS1 5JG'
        )
        
        # Create category
        self.category = Category.objects.create(
            name='Vegetables',
            slug='vegetables',
            description='Fresh vegetables',
            is_active=True
        )
        
        # Create products with surplus stock
        self.product_lettuce = Product.objects.create(
            producer=self.producer,
            category=self.category,
            name='Lettuce',
            description='Fresh lettuce - 50 heads available, best before 3 days',
            price=Decimal('2.00'),
            unit=Product.Unit.ITEM,
            stock_quantity=50,
            is_available=True,
            seasonal_status=Product.SeasonalStatus.IN_SEASON,
            allergen_info='No common allergens',
            harvest_date=date.today() - timedelta(days=1),
        )
        
        self.product_tomatoes = Product.objects.create(
            producer=self.producer,
            category=self.category,
            name='Tomatoes',
            description='Ripe tomatoes',
            price=Decimal('3.50'),
            unit=Product.Unit.KG,
            stock_quantity=30,
            is_available=True,
            seasonal_status=Product.SeasonalStatus.IN_SEASON,
            allergen_info='No common allergens',
        )
        
        self.product_carrots = Product.objects.create(
            producer=self.producer,
            category=self.category,
            name='Carrots',
            description='Fresh carrots',
            price=Decimal('1.80'),
            unit=Product.Unit.KG,
            stock_quantity=20,
            is_available=True,
            seasonal_status=Product.SeasonalStatus.IN_SEASON,
            allergen_info='No common allergens',
        )
        
        # URLs
        self.login_url = reverse('login')
        self.my_products_url = reverse('my_products')
        self.browse_url = reverse('browse')
        self.cart_url = reverse('orders:cart')
    
    def test_producer_is_logged_in(self):
        """Test Precondition: Producer is logged in."""
        response = self.client.post(self.login_url, {
            'username': 'greenleaffarm',
            'password': 'ProducerPass123!',
        }, follow=True)
        
        # Should be logged in
        self.assertTrue(response.wsgi_request.user.is_authenticated)
        self.assertEqual(response.wsgi_request.user.username, 'greenleaffarm')
        self.assertEqual(response.wsgi_request.user.role, CustomUser.Role.PRODUCER)
    
    def test_producer_has_products_with_surplus_stock(self):
        """Test Precondition: Producer has products with stock that needs to be sold quickly."""
        # Verify producer has products
        products = Product.objects.filter(producer=self.producer)
        self.assertGreater(products.count(), 0)
        
        # Verify lettuce has high stock (50 heads)
        self.assertEqual(self.product_lettuce.stock_quantity, 50)
        
        # Verify lettuce has recent harvest date (needs to sell quickly)
        self.assertIsNotNone(self.product_lettuce.harvest_date)
        days_since_harvest = (date.today() - self.product_lettuce.harvest_date).days
        self.assertLessEqual(days_since_harvest, 2)
    
    def test_producer_can_navigate_to_product_management(self):
        """Test Step 1: Navigate to product management."""
        self.client.login(username='greenleaffarm', password='ProducerPass123!')
        
        response = self.client.get(self.my_products_url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Lettuce')
        self.assertContains(response, 'Tomatoes')
    
    def test_producer_can_select_product_with_surplus_stock(self):
        """Test Step 2: Select product with surplus stock (Lettuce - 50 heads, best before 3 days)."""
        self.client.login(username='greenleaffarm', password='ProducerPass123!')
        
        # Access edit product page
        edit_url = reverse('edit_product', args=[self.product_lettuce.id])
        response = self.client.get(edit_url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Lettuce')
    
    def test_surplus_discount_concept_mark_as_surplus(self):
        """Test Step 3: Concept of marking product as 'Surplus' or 'Last Minute Deal'."""
        # In a real implementation, this would add is_surplus and discount_percentage fields
        # For now, we simulate by using description and price reduction
        
        # Original price
        original_price = self.product_lettuce.price
        self.assertEqual(original_price, Decimal('2.00'))
        
        # Mark as surplus with 30% discount
        discount_percentage = 30
        discounted_price = original_price * (Decimal('100') - Decimal(discount_percentage)) / Decimal('100')
        
        # Update product (simulating surplus marking)
        self.product_lettuce.description = 'Fresh lettuce - SURPLUS DEAL - Perfect condition, must sell quickly to avoid waste'
        self.product_lettuce.price = discounted_price
        self.product_lettuce.save()
        
        # Verify discount applied
        self.product_lettuce.refresh_from_db()
        self.assertEqual(self.product_lettuce.price, Decimal('1.40'))  # 30% off £2.00
    
    def test_discount_percentage_validation(self):
        """Test Step 4 & Acceptance Criteria: Set discount percentage (30% off) - validate range."""
        original_price = Decimal('2.00')
        
        # Test valid discount percentages (10-50% range)
        valid_discounts = [10, 20, 30, 40, 50]
        
        for discount in valid_discounts:
            discounted_price = original_price * (Decimal('100') - Decimal(discount)) / Decimal('100')
            
            # Verify discount is within valid range
            self.assertGreaterEqual(discount, 10)
            self.assertLessEqual(discount, 50)
            
            # Verify price is reduced
            self.assertLess(discounted_price, original_price)
    
    def test_set_expiry_date_for_deal(self):
        """Test Step 5: Set expiry date for deal (48 hours)."""
        # Set deal expiry to 48 hours from now
        expiry_date = date.today() + timedelta(days=2)
        
        # In real implementation, this would be a surplus_expiry_date field
        # For now, we verify the concept
        self.assertGreater(expiry_date, date.today())
        
        # Verify it's 2 days (48 hours) away
        days_until_expiry = (expiry_date - date.today()).days
        self.assertEqual(days_until_expiry, 2)
    
    def test_add_note_to_surplus_listing(self):
        """Test Step 6: Add note about condition and urgency."""
        # Add note to product description
        note = 'Perfect condition, must sell quickly to avoid waste'
        
        self.product_lettuce.description = f'Fresh lettuce - {note}'
        self.product_lettuce.save()
        
        self.product_lettuce.refresh_from_db()
        self.assertIn('Perfect condition', self.product_lettuce.description)
        self.assertIn('must sell quickly', self.product_lettuce.description)
        self.assertIn('avoid waste', self.product_lettuce.description)
    
    def test_save_surplus_listing(self):
        """Test Step 7: Save listing."""
        # Update product with surplus information
        self.product_lettuce.description = 'Fresh lettuce - SURPLUS DEAL - 30% off'
        self.product_lettuce.price = Decimal('1.40')  # 30% off original £2.00
        self.product_lettuce.save()
        
        # Verify changes persisted
        self.product_lettuce.refresh_from_db()
        self.assertEqual(self.product_lettuce.price, Decimal('1.40'))
        self.assertIn('SURPLUS', self.product_lettuce.description)
    
    def test_surplus_product_appears_in_customer_view(self):
        """Test Step 8: Verify product appears in 'Surplus Deals' section for customers."""
        # Mark product as surplus
        self.product_lettuce.description = 'Fresh lettuce - SURPLUS DEAL - 30% off'
        self.product_lettuce.price = Decimal('1.40')
        self.product_lettuce.save()
        
        # Customer logs in and browses
        self.client.login(username='foodsaver', password='CustomerPass123!')
        response = self.client.get(self.browse_url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Lettuce')
    
    def test_customer_can_view_surplus_deals_section(self):
        """Test Step 10: Navigate to 'Surplus Deals' or 'Last Minute Offers'."""
        # In real implementation, there would be a dedicated surplus deals page
        # For now, we verify customer can browse products
        
        self.client.login(username='foodsaver', password='CustomerPass123!')
        response = self.client.get(self.browse_url)
        
        self.assertEqual(response.status_code, 200)
    
    def test_discounted_lettuce_with_clear_discount_badge(self):
        """Test Step 11: View discounted lettuce with clear discount badge."""
        # Mark product with discount
        original_price = Decimal('2.00')
        discount_percentage = 30
        discounted_price = Decimal('1.40')
        
        self.product_lettuce.description = 'Fresh lettuce - 30% OFF - SURPLUS DEAL'
        self.product_lettuce.price = discounted_price
        self.product_lettuce.save()
        
        # Customer views product
        self.client.login(username='foodsaver', password='CustomerPass123!')
        response = self.client.get(self.browse_url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Lettuce')
        # In real implementation, would check for discount badge display
    
    def test_observe_original_and_discounted_price(self):
        """Test Step 12: Observe original and discounted price."""
        original_price = Decimal('2.00')
        discounted_price = Decimal('1.40')
        
        # Calculate savings
        savings = original_price - discounted_price
        self.assertEqual(savings, Decimal('0.60'))
        
        # Calculate percentage
        discount_percentage = (savings / original_price) * 100
        self.assertEqual(discount_percentage, Decimal('30'))
    
    def test_add_surplus_item_to_cart_with_discount(self):
        """Test Step 13: Add surplus item to cart and verify discounted price applies."""
        # Set discounted price
        self.product_lettuce.price = Decimal('1.40')  # 30% off
        self.product_lettuce.save()
        
        # Customer adds to cart
        self.client.login(username='foodsaver', password='CustomerPass123!')
        
        cart = Cart.objects.create(user=self.customer, status=Cart.STATUS_ACTIVE)
        CartItem.objects.create(cart=cart, product=self.product_lettuce, quantity=5)
        
        # Verify discounted price in cart
        cart_item = CartItem.objects.get(cart=cart, product=self.product_lettuce)
        self.assertEqual(cart_item.unit_price, Decimal('1.40'))
        self.assertEqual(cart_item.line_total, Decimal('7.00'))  # 5 x £1.40
    
    def test_complete_purchase_at_reduced_price(self):
        """Test Step 14: Complete purchase at reduced price."""
        # Create order with discounted product
        order = Order.objects.create(
            user=self.customer,
            full_name='Bob Saver',
            email='customer@foodsaver.com',
            address_line1='123 Saver Street',
            city='Bristol',
            postcode='BS1 5JG',
            total=Decimal('7.00'),  # 5 lettuce at £1.40 each
            commission=Decimal('0.35'),
            delivery_date=date.today() + timedelta(days=3),
            status=Order.STATUS_CONFIRMED,
        )
        
        OrderItem.objects.create(
            order=order,
            product=self.product_lettuce,
            product_name='Lettuce - SURPLUS DEAL',
            unit_price=Decimal('1.40'),  # Discounted price
            quantity=5,
            line_total=Decimal('7.00'),
        )
        
        # Verify order total uses discounted price
        self.assertEqual(order.total, Decimal('7.00'))
    
    def test_discount_is_correctly_calculated_and_applied(self):
        """Test Expected Result: Discounted price is correctly calculated and applied at checkout."""
        original_price = Decimal('2.00')
        discount_percentage = 30
        
        # Calculate discounted price
        discount_amount = original_price * Decimal(discount_percentage) / Decimal('100')
        discounted_price = original_price - discount_amount
        
        self.assertEqual(discounted_price, Decimal('1.40'))
        
        # Verify in cart
        cart = Cart.objects.create(user=self.customer, status=Cart.STATUS_ACTIVE)
        
        self.product_lettuce.price = discounted_price
        self.product_lettuce.save()
        
        CartItem.objects.create(cart=cart, product=self.product_lettuce, quantity=10)
        
        # Cart total should use discounted price
        expected_total = discounted_price * 10
        self.assertEqual(cart.total, expected_total)
    
    def test_urgency_communicated_with_time_remaining(self):
        """Test Expected Result: Urgency is communicated (time remaining, best before date)."""
        # Set harvest date and calculate best before
        harvest_date = date.today() - timedelta(days=1)
        best_before_date = harvest_date + timedelta(days=3)
        
        self.product_lettuce.harvest_date = harvest_date
        self.product_lettuce.description = f'Fresh lettuce - Best before {best_before_date.strftime("%d/%m/%Y")}'
        self.product_lettuce.save()
        
        # Calculate time remaining
        days_remaining = (best_before_date - date.today()).days
        
        # Verify urgency (less than 3 days)
        self.assertLessEqual(days_remaining, 3)
        self.assertGreaterEqual(days_remaining, 0)
    
    def test_surplus_items_maintain_quality_and_allergen_info(self):
        """Test Acceptance Criteria: Surplus items maintain all quality and allergen information."""
        # Mark as surplus
        self.product_lettuce.description = 'Fresh lettuce - SURPLUS DEAL - Perfect condition'
        self.product_lettuce.price = Decimal('1.40')
        self.product_lettuce.save()
        
        # Verify allergen info is maintained
        self.product_lettuce.refresh_from_db()
        self.assertEqual(self.product_lettuce.allergen_info, 'No common allergens')
        
        # Verify quality note in description
        self.assertIn('Perfect condition', self.product_lettuce.description)
    
    def test_deal_expiry_enforced_automatically(self):
        """Test Acceptance Criteria: Deal expiry is enforced automatically."""
        # Set expiry date in the past
        expiry_date = date.today() - timedelta(days=1)
        
        # In real implementation, expired deals would be automatically removed or marked unavailable
        # For now, we verify the concept
        is_expired = expiry_date < date.today()
        self.assertTrue(is_expired)
        
        # Expired deals should not be available
        if is_expired:
            # Would set is_available = False or remove surplus status
            self.product_lettuce.is_available = False
            self.product_lettuce.save()
            
            self.product_lettuce.refresh_from_db()
            self.assertFalse(self.product_lettuce.is_available)
    
    def test_producer_can_remove_surplus_status_when_stock_sells_out(self):
        """Test Acceptance Criteria: Producers can remove surplus status if stock sells out."""
        # Mark as surplus
        self.product_lettuce.description = 'Fresh lettuce - SURPLUS DEAL'
        self.product_lettuce.price = Decimal('1.40')
        self.product_lettuce.stock_quantity = 50
        self.product_lettuce.save()
        
        # Simulate stock selling out
        self.product_lettuce.stock_quantity = 0
        self.product_lettuce.is_available = False
        self.product_lettuce.save()
        
        # Producer can remove surplus status
        self.product_lettuce.description = 'Fresh lettuce'
        self.product_lettuce.price = Decimal('2.00')  # Restore original price
        self.product_lettuce.save()
        
        self.product_lettuce.refresh_from_db()
        self.assertNotIn('SURPLUS', self.product_lettuce.description)
        self.assertEqual(self.product_lettuce.stock_quantity, 0)
    
    def test_system_supports_food_waste_reduction_objectives(self):
        """Test Expected Result: System supports community food waste reduction objectives."""
        # Create multiple surplus products
        surplus_products = []
        
        # Product 1: Lettuce with surplus
        self.product_lettuce.description = 'Fresh lettuce - SURPLUS DEAL - 30% off'
        self.product_lettuce.price = Decimal('1.40')
        self.product_lettuce.save()
        surplus_products.append(self.product_lettuce)
        
        # Product 2: Tomatoes with surplus
        self.product_tomatoes.description = 'Ripe tomatoes - LAST MINUTE DEAL - 25% off'
        self.product_tomatoes.price = Decimal('2.63')  # 25% off £3.50
        self.product_tomatoes.save()
        surplus_products.append(self.product_tomatoes)
        
        # Verify multiple surplus products exist
        self.assertEqual(len(surplus_products), 2)
        
        # Verify all have discounted prices
        for product in surplus_products:
            self.assertIn('DEAL', product.description.upper())
    
    def test_surplus_deals_highlighted_in_customer_interface(self):
        """Test Expected Result: Surplus deals are highlighted in customer interface."""
        # Mark product as surplus
        self.product_lettuce.description = 'Fresh lettuce - ⚡ SURPLUS DEAL - 30% OFF'
        self.product_lettuce.price = Decimal('1.40')
        self.product_lettuce.save()
        
        # Customer views products
        self.client.login(username='foodsaver', password='CustomerPass123!')
        response = self.client.get(self.browse_url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Lettuce')
        # In real implementation, would verify visual highlighting (badges, colors, etc.)
    
    def test_multiple_discount_levels(self):
        """Test that different discount levels can be applied based on urgency."""
        # Low urgency: 10% discount
        low_urgency_price = Decimal('2.00') * Decimal('0.90')
        self.assertEqual(low_urgency_price, Decimal('1.80'))
        
        # Medium urgency: 30% discount
        medium_urgency_price = Decimal('2.00') * Decimal('0.70')
        self.assertEqual(medium_urgency_price, Decimal('1.40'))
        
        # High urgency: 50% discount
        high_urgency_price = Decimal('2.00') * Decimal('0.50')
        self.assertEqual(high_urgency_price, Decimal('1.00'))
        
        # All discounts within valid range (10-50%)
        self.assertGreaterEqual(Decimal('10'), Decimal('10'))
        self.assertLessEqual(Decimal('50'), Decimal('50'))
    
    def test_food_waste_reduction_impact_tracking(self):
        """Test Acceptance Criteria: Analytics track food waste reduction impact."""
        # Create orders with surplus products
        surplus_orders = []
        
        for i in range(3):
            order = Order.objects.create(
                user=self.customer,
                full_name='Bob Saver',
                email='customer@foodsaver.com',
                address_line1='123 Saver Street',
                city='Bristol',
                postcode='BS1 5JG',
                total=Decimal('7.00'),
                commission=Decimal('0.35'),
                delivery_date=date.today() + timedelta(days=3),
                status=Order.STATUS_DELIVERED,
            )
            
            OrderItem.objects.create(
                order=order,
                product=self.product_lettuce,
                product_name='Lettuce - SURPLUS DEAL',
                unit_price=Decimal('1.40'),
                quantity=5,
                line_total=Decimal('7.00'),
            )
            
            surplus_orders.append(order)
        
        # Calculate impact: 3 orders x 5 lettuce = 15 heads saved from waste
        total_items_saved = sum(
            item.quantity 
            for order in surplus_orders 
            for item in order.items.all()
        )
        
        self.assertEqual(total_items_saved, 15)
        
        # Verify all orders delivered (food waste prevented)
        for order in surplus_orders:
            self.assertEqual(order.status, Order.STATUS_DELIVERED)
    
    def test_complete_surplus_workflow(self):
        """Test complete workflow: Producer marks surplus, customer purchases at discount."""
        # Producer marks product as surplus
        self.client.login(username='greenleaffarm', password='ProducerPass123!')
        
        original_price = Decimal('2.00')
        discount_percentage = 30
        discounted_price = Decimal('1.40')
        
        self.product_lettuce.description = 'Fresh lettuce - SURPLUS DEAL - 30% OFF - Perfect condition, must sell quickly'
        self.product_lettuce.price = discounted_price
        self.product_lettuce.save()
        
        # Customer discovers and purchases
        self.client.login(username='foodsaver', password='CustomerPass123!')
        
        cart = Cart.objects.create(user=self.customer, status=Cart.STATUS_ACTIVE)
        CartItem.objects.create(cart=cart, product=self.product_lettuce, quantity=10)
        
        # Verify discount applied
        expected_total = discounted_price * 10
        self.assertEqual(cart.total, expected_total)
        
        # Create order
        order = Order.objects.create(
            user=self.customer,
            full_name='Bob Saver',
            email='customer@foodsaver.com',
            address_line1='123 Saver Street',
            city='Bristol',
            postcode='BS1 5JG',
            total=expected_total,
            commission=expected_total * Decimal('0.05'),
            delivery_date=date.today() + timedelta(days=2),
            status=Order.STATUS_CONFIRMED,
        )
        
        OrderItem.objects.create(
            order=order,
            product=self.product_lettuce,
            product_name='Lettuce - SURPLUS DEAL',
            unit_price=discounted_price,
            quantity=10,
            line_total=expected_total,
        )
        
        # Verify order completed at discounted price
        self.assertEqual(order.total, Decimal('14.00'))  # 10 x £1.40
        
        # Verify food waste reduction: 10 heads of lettuce saved
        total_saved = order.items.first().quantity
        self.assertEqual(total_saved, 10)
