"""
TC-016: Seasonal Availability Management Test Case
Tests that producers can set seasonal availability for products so customers know when items are in season.

Test Requirements:
- Producers can easily set seasonal availability
- Seasonal indicators are displayed to customers
- Out-of-season products are marked appropriately
- System supports different seasonal patterns (in season, out of season, all year, limited)
- Seasonal information educates customers about local food systems
"""

from django.test import TestCase, Client
from django.urls import reverse
from decimal import Decimal
from accounts.models import CustomUser
from marketplace.models import Product, Category
from marketplace.forms import ProductForm


class TC016SeasonalAvailabilityTest(TestCase):
    """Test seasonal availability management for products."""
    
    def setUp(self):
        """Set up test data for seasonal availability tests."""
        self.client = Client()
        
        # Create producer account
        self.producer = CustomUser.objects.create_user(
            username='greenvalleyfarm',
            email='producer@greenvalley.com',
            password='ProducerPass123!',
            role=CustomUser.Role.PRODUCER,
            first_name='Sarah',
            last_name='Green'
        )
        
        # Create customer account
        self.customer = CustomUser.objects.create_user(
            username='testcustomer',
            email='customer@test.com',
            password='CustomerPass123!',
            role=CustomUser.Role.CUSTOMER,
            first_name='John',
            last_name='Doe'
        )
        
        # Create category
        self.category = Category.objects.create(
            name='Fruits',
            slug='fruits',
            description='Fresh seasonal fruits',
            is_active=True
        )
        
        # URLs
        self.add_product_url = reverse('add_product')
        self.browse_url = reverse('browse')
        self.my_products_url = reverse('my_products')
    
    def test_producer_can_set_seasonal_availability_in_season(self):
        """Test that producers can set products as 'In Season'."""
        self.client.login(username='greenvalleyfarm', password='ProducerPass123!')
        
        product_data = {
            'name': 'Strawberries',
            'category': self.category.id,
            'description': 'Fresh local strawberries',
            'price': Decimal('4.50'),
            'unit': Product.Unit.PACK,
            'stock_quantity': 30,
            'is_available': True,
            'seasonal_status': Product.SeasonalStatus.IN_SEASON,
            'allergen_info': 'No common allergens',
        }
        
        response = self.client.post(self.add_product_url, data=product_data)
        
        # Verify product was created
        self.assertEqual(Product.objects.count(), 1)
        
        product = Product.objects.get(name='Strawberries')
        self.assertEqual(product.seasonal_status, Product.SeasonalStatus.IN_SEASON)
        self.assertEqual(product.get_seasonal_status_display(), 'In Season')
    
    def test_producer_can_set_seasonal_availability_all_year(self):
        """Test that producers can set products as 'Available All Year'."""
        self.client.login(username='greenvalleyfarm', password='ProducerPass123!')
        
        product_data = {
            'name': 'Stored Potatoes',
            'category': self.category.id,
            'description': 'Year-round stored potatoes',
            'price': Decimal('2.50'),
            'unit': Product.Unit.KG,
            'stock_quantity': 100,
            'is_available': True,
            'seasonal_status': Product.SeasonalStatus.ALL_YEAR,
            'allergen_info': 'No common allergens',
        }
        
        response = self.client.post(self.add_product_url, data=product_data)
        
        product = Product.objects.get(name='Stored Potatoes')
        self.assertEqual(product.seasonal_status, Product.SeasonalStatus.ALL_YEAR)
        self.assertEqual(product.get_seasonal_status_display(), 'Available All Year')
    
    def test_producer_can_set_seasonal_availability_out_of_season(self):
        """Test that producers can mark products as 'Out of Season'."""
        self.client.login(username='greenvalleyfarm', password='ProducerPass123!')
        
        product_data = {
            'name': 'Asparagus',
            'category': self.category.id,
            'description': 'Spring asparagus (currently out of season)',
            'price': Decimal('6.00'),
            'unit': Product.Unit.BUNCH,
            'stock_quantity': 0,
            'is_available': False,
            'seasonal_status': Product.SeasonalStatus.OUT_OF_SEASON,
            'allergen_info': 'No common allergens',
        }
        
        response = self.client.post(self.add_product_url, data=product_data)
        
        product = Product.objects.get(name='Asparagus')
        self.assertEqual(product.seasonal_status, Product.SeasonalStatus.OUT_OF_SEASON)
        self.assertEqual(product.get_seasonal_status_display(), 'Out of Season')
    
    def test_producer_can_set_seasonal_availability_limited(self):
        """Test that producers can mark products as 'Limited Availability'."""
        self.client.login(username='greenvalleyfarm', password='ProducerPass123!')
        
        product_data = {
            'name': 'Wild Mushrooms',
            'category': self.category.id,
            'description': 'Foraged wild mushrooms - limited availability',
            'price': Decimal('8.00'),
            'unit': Product.Unit.PACK,
            'stock_quantity': 5,
            'is_available': True,
            'seasonal_status': Product.SeasonalStatus.LIMITED,
            'allergen_info': 'No common allergens',
        }
        
        response = self.client.post(self.add_product_url, data=product_data)
        
        product = Product.objects.get(name='Wild Mushrooms')
        self.assertEqual(product.seasonal_status, Product.SeasonalStatus.LIMITED)
        self.assertEqual(product.get_seasonal_status_display(), 'Limited Availability')
    
    def test_seasonal_status_displayed_on_browse_page(self):
        """Test that seasonal status is visible to customers on browse page."""
        from datetime import date, timedelta
        
        today = date.today()
        
        # Create in-season product with dates
        Product.objects.create(
            producer=self.producer,
            category=self.category,
            name='Summer Tomatoes',
            description='Fresh summer tomatoes',
            price=Decimal('3.50'),
            unit=Product.Unit.KG,
            stock_quantity=50,
            is_available=True,
            seasonal_status=Product.SeasonalStatus.IN_SEASON,
            seasonal_start_date=today - timedelta(days=30),
            seasonal_end_date=today + timedelta(days=30),
            allergen_info='No common allergens',
        )
        
        # Customer views browse page
        self.client.login(username='testcustomer', password='CustomerPass123!')
        response = self.client.get(self.browse_url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Summer Tomatoes')
        # Should show checkmark for in-season products
        self.assertContains(response, '✓')
    
    def test_all_year_products_show_correct_indicator(self):
        """Test that year-round products display 'Available All Year' indicator."""
        Product.objects.create(
            producer=self.producer,
            category=self.category,
            name='Carrots',
            description='Stored carrots available year-round',
            price=Decimal('2.00'),
            unit=Product.Unit.KG,
            stock_quantity=80,
            is_available=True,
            seasonal_status=Product.SeasonalStatus.ALL_YEAR,
            allergen_info='No common allergens',
        )
        
        self.client.login(username='testcustomer', password='CustomerPass123!')
        response = self.client.get(self.browse_url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Carrots')
        self.assertContains(response, 'Available All Year')
    
    def test_out_of_season_products_are_marked(self):
        """Test that out-of-season products are clearly marked."""
        from datetime import date, timedelta
        
        today = date.today()
        
        # Create out-of-season product with dates in the past but still available
        Product.objects.create(
            producer=self.producer,
            category=self.category,
            name='Pumpkins',
            description='Autumn pumpkins (out of season)',
            price=Decimal('5.00'),
            unit=Product.Unit.ITEM,
            stock_quantity=5,
            is_available=True,
            seasonal_status=Product.SeasonalStatus.IN_SEASON,
            seasonal_start_date=today - timedelta(days=90),
            seasonal_end_date=today - timedelta(days=30),
            allergen_info='No common allergens',
        )
        
        self.client.login(username='testcustomer', password='CustomerPass123!')
        response = self.client.get(self.browse_url)
        
        self.assertEqual(response.status_code, 200)
        # Out of season products should still be visible but marked
        self.assertContains(response, 'Pumpkins')
        self.assertContains(response, 'Out of Season')
    
    def test_producer_can_update_seasonal_status(self):
        """Test that producers can update seasonal status as seasons change."""
        # Create product initially out of season
        product = Product.objects.create(
            producer=self.producer,
            category=self.category,
            name='Blueberries',
            description='Summer blueberries',
            price=Decimal('5.50'),
            unit=Product.Unit.PACK,
            stock_quantity=0,
            is_available=False,
            seasonal_status=Product.SeasonalStatus.OUT_OF_SEASON,
            allergen_info='No common allergens',
        )
        
        self.assertEqual(product.seasonal_status, Product.SeasonalStatus.OUT_OF_SEASON)
        
        # Producer updates to in season
        self.client.login(username='greenvalleyfarm', password='ProducerPass123!')
        edit_url = reverse('edit_product', args=[product.id])
        
        updated_data = {
            'name': 'Blueberries',
            'category': self.category.id,
            'description': 'Summer blueberries - now in season!',
            'price': Decimal('5.50'),
            'unit': Product.Unit.PACK,
            'stock_quantity': 25,
            'is_available': True,
            'seasonal_status': Product.SeasonalStatus.IN_SEASON,
            'allergen_info': 'No common allergens',
        }
        
        response = self.client.post(edit_url, data=updated_data)
        
        product.refresh_from_db()
        self.assertEqual(product.seasonal_status, Product.SeasonalStatus.IN_SEASON)
        self.assertTrue(product.is_available)
        self.assertEqual(product.stock_quantity, 25)
    
    def test_multiple_products_with_different_seasonal_patterns(self):
        """Test system supports multiple products with different seasonal patterns."""
        # Create products with different seasonal statuses
        Product.objects.create(
            producer=self.producer,
            category=self.category,
            name='Strawberries',
            description='Summer strawberries',
            price=Decimal('4.50'),
            unit=Product.Unit.PACK,
            stock_quantity=30,
            is_available=True,
            seasonal_status=Product.SeasonalStatus.IN_SEASON,
            allergen_info='No common allergens',
        )
        
        Product.objects.create(
            producer=self.producer,
            category=self.category,
            name='Onions',
            description='Stored onions',
            price=Decimal('1.50'),
            unit=Product.Unit.KG,
            stock_quantity=100,
            is_available=True,
            seasonal_status=Product.SeasonalStatus.ALL_YEAR,
            allergen_info='No common allergens',
        )
        
        Product.objects.create(
            producer=self.producer,
            category=self.category,
            name='Rhubarb',
            description='Spring rhubarb',
            price=Decimal('3.00'),
            unit=Product.Unit.BUNCH,
            stock_quantity=0,
            is_available=False,
            seasonal_status=Product.SeasonalStatus.OUT_OF_SEASON,
            allergen_info='No common allergens',
        )
        
        # Verify all products exist with correct seasonal status
        self.assertEqual(Product.objects.count(), 3)
        
        strawberries = Product.objects.get(name='Strawberries')
        onions = Product.objects.get(name='Onions')
        rhubarb = Product.objects.get(name='Rhubarb')
        
        self.assertEqual(strawberries.seasonal_status, Product.SeasonalStatus.IN_SEASON)
        self.assertEqual(onions.seasonal_status, Product.SeasonalStatus.ALL_YEAR)
        self.assertEqual(rhubarb.seasonal_status, Product.SeasonalStatus.OUT_OF_SEASON)
    
    def test_seasonal_form_validation(self):
        """Test that ProductForm correctly validates seasonal status field."""
        form_data = {
            'name': 'Test Product',
            'category': self.category.id,
            'description': 'Test description',
            'price': Decimal('5.00'),
            'unit': Product.Unit.ITEM,
            'stock_quantity': 10,
            'is_available': True,
            'seasonal_status': Product.SeasonalStatus.IN_SEASON,
            'allergen_info': 'No common allergens',
        }
        
        form = ProductForm(data=form_data)
        self.assertTrue(form.is_valid(), f"Form errors: {form.errors}")
    
    def test_seasonal_status_choices_available_in_form(self):
        """Test that all seasonal status choices are available in the form."""
        form = ProductForm()
        
        # Get the seasonal_status field choices
        seasonal_field = form.fields.get('seasonal_status')
        self.assertIsNotNone(seasonal_field)
        
        # Verify all expected choices exist
        choice_values = [choice[0] for choice in Product.SeasonalStatus.choices]
        
        self.assertIn(Product.SeasonalStatus.IN_SEASON, choice_values)
        self.assertIn(Product.SeasonalStatus.OUT_OF_SEASON, choice_values)
        self.assertIn(Product.SeasonalStatus.ALL_YEAR, choice_values)
        self.assertIn(Product.SeasonalStatus.LIMITED, choice_values)
    
    def test_seasonal_information_educates_customers(self):
        """Test that seasonal information is clear and educational for customers."""
        from datetime import date, timedelta
        
        today = date.today()
        
        # Create products representing different seasons with dates
        Product.objects.create(
            producer=self.producer,
            category=self.category,
            name='June Strawberries',
            description='Peak season strawberries - supporting local farms during harvest time',
            price=Decimal('4.50'),
            unit=Product.Unit.PACK,
            stock_quantity=30,
            is_available=True,
            seasonal_status=Product.SeasonalStatus.IN_SEASON,
            seasonal_start_date=today - timedelta(days=15),
            seasonal_end_date=today + timedelta(days=45),
            allergen_info='No common allergens',
        )
        
        self.client.login(username='testcustomer', password='CustomerPass123!')
        response = self.client.get(self.browse_url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'June Strawberries')
        # Check for checkmark indicating in-season
        self.assertContains(response, '✓')
    
    def test_producer_dashboard_shows_seasonal_status(self):
        """Test that producer's product dashboard displays seasonal status."""
        Product.objects.create(
            producer=self.producer,
            category=self.category,
            name='Seasonal Apples',
            description='Autumn apples',
            price=Decimal('3.00'),
            unit=Product.Unit.KG,
            stock_quantity=50,
            is_available=True,
            seasonal_status=Product.SeasonalStatus.IN_SEASON,
            allergen_info='No common allergens',
        )
        
        self.client.login(username='greenvalleyfarm', password='ProducerPass123!')
        response = self.client.get(self.my_products_url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Seasonal Apples')
        self.assertContains(response, 'In Season')
    
    def test_seasonal_status_persists_across_updates(self):
        """Test that seasonal status is maintained when updating other product fields."""
        product = Product.objects.create(
            producer=self.producer,
            category=self.category,
            name='Test Product',
            description='Original description',
            price=Decimal('5.00'),
            unit=Product.Unit.ITEM,
            stock_quantity=10,
            is_available=True,
            seasonal_status=Product.SeasonalStatus.IN_SEASON,
            allergen_info='No common allergens',
        )
        
        # Update price but keep seasonal status
        self.client.login(username='greenvalleyfarm', password='ProducerPass123!')
        edit_url = reverse('edit_product', args=[product.id])
        
        updated_data = {
            'name': 'Test Product',
            'category': self.category.id,
            'description': 'Updated description',
            'price': Decimal('6.00'),  # Changed
            'unit': Product.Unit.ITEM,
            'stock_quantity': 15,  # Changed
            'is_available': True,
            'seasonal_status': Product.SeasonalStatus.IN_SEASON,  # Unchanged
            'allergen_info': 'No common allergens',
        }
        
        response = self.client.post(edit_url, data=updated_data)
        
        product.refresh_from_db()
        self.assertEqual(product.seasonal_status, Product.SeasonalStatus.IN_SEASON)
        self.assertEqual(product.price, Decimal('6.00'))
        self.assertEqual(product.stock_quantity, 15)
    
    def test_default_seasonal_status_is_all_year(self):
        """Test that products default to 'Available All Year' if not specified."""
        product = Product.objects.create(
            producer=self.producer,
            category=self.category,
            name='Default Product',
            description='Product without explicit seasonal status',
            price=Decimal('5.00'),
            unit=Product.Unit.ITEM,
            stock_quantity=10,
            is_available=True,
            allergen_info='No common allergens',
            # seasonal_status not specified - should default to ALL_YEAR
        )
        
        self.assertEqual(product.seasonal_status, Product.SeasonalStatus.ALL_YEAR)
    
    def test_seasonal_dates_can_be_set(self):
        """Test that producers can set specific seasonal date ranges."""
        from datetime import date
        
        self.client.login(username='greenvalleyfarm', password='ProducerPass123!')
        
        product_data = {
            'name': 'Summer Strawberries',
            'category': self.category.id,
            'description': 'Fresh strawberries available June through August',
            'price': Decimal('4.50'),
            'unit': Product.Unit.PACK,
            'stock_quantity': 30,
            'is_available': True,
            'seasonal_status': Product.SeasonalStatus.IN_SEASON,
            'seasonal_start_date': date(2026, 6, 1),
            'seasonal_end_date': date(2026, 8, 31),
            'allergen_info': 'No common allergens',
        }
        
        response = self.client.post(self.add_product_url, data=product_data)
        
        product = Product.objects.get(name='Summer Strawberries')
        self.assertEqual(product.seasonal_start_date, date(2026, 6, 1))
        self.assertEqual(product.seasonal_end_date, date(2026, 8, 31))
    
    def test_seasonal_date_range_display(self):
        """Test that seasonal date ranges are displayed in human-readable format."""
        from datetime import date
        
        product = Product.objects.create(
            producer=self.producer,
            category=self.category,
            name='June Berries',
            description='Seasonal berries',
            price=Decimal('5.00'),
            unit=Product.Unit.PACK,
            stock_quantity=20,
            is_available=True,
            seasonal_status=Product.SeasonalStatus.IN_SEASON,
            seasonal_start_date=date(2026, 6, 1),
            seasonal_end_date=date(2026, 8, 31),
            allergen_info='No common allergens',
        )
        
        # Should display "June - August"
        date_range = product.get_seasonal_date_range_display()
        self.assertIn('June', date_range)
        self.assertIn('August', date_range)
    
    def test_is_currently_in_season_with_dates(self):
        """Test automatic seasonal status calculation based on current date."""
        from datetime import date, timedelta
        
        today = date.today()
        
        # Create product in season (dates include today)
        product_in_season = Product.objects.create(
            producer=self.producer,
            category=self.category,
            name='Current Season Product',
            description='Product currently in season',
            price=Decimal('5.00'),
            unit=Product.Unit.ITEM,
            stock_quantity=20,
            is_available=True,
            seasonal_status=Product.SeasonalStatus.IN_SEASON,
            seasonal_start_date=today - timedelta(days=30),
            seasonal_end_date=today + timedelta(days=30),
            allergen_info='No common allergens',
        )
        
        self.assertTrue(product_in_season.is_currently_in_season())
    
    def test_is_currently_out_of_season_with_dates(self):
        """Test that products outside their date range are marked out of season."""
        from datetime import date, timedelta
        
        today = date.today()
        
        # Create product out of season (dates in the past)
        product_out_of_season = Product.objects.create(
            producer=self.producer,
            category=self.category,
            name='Past Season Product',
            description='Product past its season',
            price=Decimal('5.00'),
            unit=Product.Unit.ITEM,
            stock_quantity=0,
            is_available=False,
            seasonal_status=Product.SeasonalStatus.IN_SEASON,
            seasonal_start_date=today - timedelta(days=90),
            seasonal_end_date=today - timedelta(days=30),
            allergen_info='No common allergens',
        )
        
        self.assertFalse(product_out_of_season.is_currently_in_season())
    
    def test_all_year_products_always_in_season(self):
        """Test that ALL_YEAR products are always considered in season regardless of dates."""
        from datetime import date
        
        product = Product.objects.create(
            producer=self.producer,
            category=self.category,
            name='Year Round Product',
            description='Available all year',
            price=Decimal('3.00'),
            unit=Product.Unit.KG,
            stock_quantity=100,
            is_available=True,
            seasonal_status=Product.SeasonalStatus.ALL_YEAR,
            allergen_info='No common allergens',
        )
        
        self.assertTrue(product.is_currently_in_season())
        self.assertEqual(product.get_seasonal_date_range_display(), 'Available All Year')
    
    def test_seasonal_dates_validation_both_required(self):
        """Test that both start and end dates must be provided together."""
        from datetime import date
        
        self.client.login(username='greenvalleyfarm', password='ProducerPass123!')
        
        # Try to set only start date
        product_data = {
            'name': 'Invalid Product',
            'category': self.category.id,
            'description': 'Product with incomplete dates',
            'price': Decimal('5.00'),
            'unit': Product.Unit.ITEM,
            'stock_quantity': 10,
            'is_available': True,
            'seasonal_status': Product.SeasonalStatus.IN_SEASON,
            'seasonal_start_date': date(2026, 6, 1),
            # seasonal_end_date missing
            'allergen_info': 'No common allergens',
        }
        
        response = self.client.post(self.add_product_url, data=product_data)
        
        # Should fail validation
        self.assertNotEqual(response.status_code, 302)  # Not redirected (form error)
    
    def test_cross_year_seasonal_dates(self):
        """Test that seasonal dates can span across year boundary (e.g., winter crops)."""
        from datetime import date
        
        # Winter product: November to February
        product = Product.objects.create(
            producer=self.producer,
            category=self.category,
            name='Winter Kale',
            description='Winter vegetable',
            price=Decimal('3.50'),
            unit=Product.Unit.BUNCH,
            stock_quantity=40,
            is_available=True,
            seasonal_status=Product.SeasonalStatus.IN_SEASON,
            seasonal_start_date=date(2025, 11, 1),
            seasonal_end_date=date(2026, 2, 28),
            allergen_info='No common allergens',
        )
        
        # The is_currently_in_season method should handle cross-year dates
        # This test just verifies the dates are stored correctly
        self.assertEqual(product.seasonal_start_date.month, 11)
        self.assertEqual(product.seasonal_end_date.month, 2)
