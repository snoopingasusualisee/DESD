"""Idempotent seed command — populates the demo with categories, producers,
customers, products, recipes, farm stories, delivered orders and reviews so
the marketplace looks lived-in on first boot.

Safe to run repeatedly: every record uses get_or_create on a stable unique
key so re-running won't duplicate anything.
"""
from decimal import Decimal
from datetime import date, timedelta
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone

from marketplace.models import (
    Category,
    Product,
    Recipe,
    RecipeProduct,
    FarmStory,
    FavoriteRecipe,
    ProductReview,
)
from orders.models import Order, OrderItem

User = get_user_model()


class Command(BaseCommand):
    help = "Populate the database with sample categories, users, products, recipes, stories, orders and reviews."

    def handle(self, *args, **options):
        self._seed_categories()
        self._seed_producers()
        self._seed_customers()
        self._seed_products()
        self._seed_recipes()
        self._seed_stories()
        self._seed_orders_and_reviews()
        self._seed_favorites()

        self.stdout.write(self.style.SUCCESS(
            "\nDatabase seeded successfully!"
            "\n\nTest accounts (password: testpass123):"
            "\n  Customer: testcustomer"
            "\n  Customer: emily_jones"
            "\n  Customer: david_smith"
            "\n  Customer: sarah_brown"
            "\n  Producer: bristol_farm"
            "\n  Producer: somerset_dairy"
            "\n  Producer: avon_bakery"
        ))

    # ------------------------------------------------------------------ helpers
    def _row(self, label, created):
        flag = "Created" if created else "Already exists"
        self.stdout.write(f"  {flag}: {label}")

    # ------------------------------------------------------------------ data
    def _seed_categories(self):
        self.stdout.write("\nSeeding categories...")
        data = [
            ("Dairy", "dairy", "Fresh milk, cheese, butter, and yogurt from local farms"),
            ("Vegetables", "vegetables", "Seasonal vegetables grown in the Bristol region"),
            ("Fruit", "fruit", "Fresh fruit from local orchards and farms"),
            ("Meat", "meat", "Ethically raised meat from local farms"),
            ("Bakery", "bakery", "Freshly baked bread, pastries, and cakes"),
            ("Eggs", "eggs", "Free-range eggs from local poultry farms"),
            ("Honey & Preserves", "honey-preserves", "Local honey, jams, and preserves"),
            ("Drinks", "drinks", "Locally produced juices, ciders, and soft drinks"),
        ]
        self._categories = {}
        for name, slug, description in data:
            cat, created = Category.objects.get_or_create(
                slug=slug,
                defaults={"name": name, "description": description},
            )
            self._categories[slug] = cat
            self._row(f"Category '{cat.name}'", created)

    def _seed_producers(self):
        self.stdout.write("\nSeeding producers...")
        data = [
            ("bristol_farm", "farm@bristol.test", "James", "Hartley"),
            ("somerset_dairy", "dairy@somerset.test", "Emma", "Clarke"),
            ("avon_bakery", "bakery@avon.test", "Tom", "Baker"),
        ]
        self._producers = {}
        for username, email, first, last in data:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    "email": email,
                    "first_name": first,
                    "last_name": last,
                    "role": "producer",
                    "delivery_address": "Bristol, UK",
                    "postcode": "BS1 1AA",
                },
            )
            if created:
                user.set_password("testpass123")
                user.save()
            self._producers[username] = user
            self._row(f"Producer '{user.username}'", created)

    def _seed_customers(self):
        self.stdout.write("\nSeeding customers...")
        data = [
            ("testcustomer", "customer@test.com", "Test", "Customer", "10 High Street, Bristol", "BS2 8HH"),
            ("emily_jones", "emily@test.com", "Emily", "Jones", "22 Park Road, Bristol", "BS6 6PR"),
            ("david_smith", "david@test.com", "David", "Smith", "45 King Street, Bath", "BA1 1LT"),
            ("sarah_brown", "sarah@test.com", "Sarah", "Brown", "8 Queen Square, Bristol", "BS1 4LH"),
        ]
        self._customers = {}
        for username, email, first, last, addr, postcode in data:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    "email": email,
                    "first_name": first,
                    "last_name": last,
                    "role": "customer",
                    "delivery_address": addr,
                    "postcode": postcode,
                },
            )
            if created:
                user.set_password("testpass123")
                user.save()
            self._customers[username] = user
            self._row(f"Customer '{user.username}'", created)

    def _seed_products(self):
        self.stdout.write("\nSeeding products...")
        today = date.today()
        data = [
            # Dairy
            {"name": "Whole Milk (1L)", "category": "dairy", "producer": "somerset_dairy", "price": "1.80", "unit": "l", "stock_quantity": 50, "description": "Fresh whole milk from grass-fed cows", "seasonal_status": "all_year", "allergen_info": "Contains milk"},
            {"name": "Semi-Skimmed Milk (1L)", "category": "dairy", "producer": "somerset_dairy", "price": "1.60", "unit": "l", "stock_quantity": 50, "description": "Semi-skimmed milk, perfect for everyday use", "seasonal_status": "all_year", "allergen_info": "Contains milk"},
            {"name": "Farmhouse Cheddar (200g)", "category": "dairy", "producer": "somerset_dairy", "price": "4.50", "unit": "pack", "stock_quantity": 30, "description": "Mature cheddar aged for 12 months", "seasonal_status": "all_year", "allergen_info": "Contains milk"},
            {"name": "Organic Butter (250g)", "category": "dairy", "producer": "somerset_dairy", "price": "3.20", "unit": "pack", "stock_quantity": 40, "description": "Rich creamy organic butter", "seasonal_status": "all_year", "allergen_info": "Contains milk"},
            {"name": "Natural Yogurt (500g)", "category": "dairy", "producer": "somerset_dairy", "price": "2.40", "unit": "pack", "stock_quantity": 25, "description": "Thick and creamy natural yogurt", "seasonal_status": "all_year", "allergen_info": "Contains milk"},
            # Vegetables
            {"name": "Carrots (1kg)", "category": "vegetables", "producer": "bristol_farm", "price": "1.20", "unit": "kg", "stock_quantity": 80, "description": "Crunchy organic carrots", "seasonal_status": "all_year"},
            {"name": "Potatoes (2kg)", "category": "vegetables", "producer": "bristol_farm", "price": "2.50", "unit": "kg", "stock_quantity": 60, "description": "Floury potatoes, great for roasting and mashing", "seasonal_status": "all_year"},
            {"name": "Broccoli", "category": "vegetables", "producer": "bristol_farm", "price": "1.50", "unit": "item", "stock_quantity": 40, "description": "Fresh green broccoli heads", "seasonal_status": "in_season"},
            {"name": "Tomatoes (500g)", "category": "vegetables", "producer": "bristol_farm", "price": "2.00", "unit": "pack", "stock_quantity": 35, "description": "Vine-ripened tomatoes", "seasonal_status": "in_season"},
            {"name": "Onions (1kg)", "category": "vegetables", "producer": "bristol_farm", "price": "1.00", "unit": "kg", "stock_quantity": 70, "description": "Brown onions, a kitchen staple", "seasonal_status": "all_year"},
            {"name": "Courgettes (3 pack)", "category": "vegetables", "producer": "bristol_farm", "price": "1.80", "unit": "pack", "stock_quantity": 30, "description": "Freshly picked courgettes", "seasonal_status": "in_season"},
            # Fruit
            {"name": "Apples - Bramley (6 pack)", "category": "fruit", "producer": "bristol_farm", "price": "2.80", "unit": "pack", "stock_quantity": 45, "description": "Cooking apples from local orchards", "seasonal_status": "in_season"},
            {"name": "Strawberries (400g)", "category": "fruit", "producer": "bristol_farm", "price": "3.50", "unit": "pack", "stock_quantity": 20, "description": "Sweet juicy strawberries", "seasonal_status": "limited"},
            {"name": "Raspberries (200g)", "category": "fruit", "producer": "bristol_farm", "price": "3.00", "unit": "pack", "stock_quantity": 15, "description": "Hand-picked raspberries", "seasonal_status": "limited"},
            # Meat
            {"name": "Chicken Breast (500g)", "category": "meat", "producer": "bristol_farm", "price": "6.50", "unit": "pack", "stock_quantity": 20, "description": "Free-range chicken breast fillets", "seasonal_status": "all_year"},
            {"name": "Pork Sausages (6 pack)", "category": "meat", "producer": "bristol_farm", "price": "4.80", "unit": "pack", "stock_quantity": 25, "description": "Traditional pork sausages made with local herbs", "seasonal_status": "all_year"},
            {"name": "Beef Mince (500g)", "category": "meat", "producer": "bristol_farm", "price": "5.50", "unit": "pack", "stock_quantity": 18, "description": "Lean beef mince from grass-fed cattle", "seasonal_status": "all_year"},
            {"name": "Lamb Chops (4 pack)", "category": "meat", "producer": "bristol_farm", "price": "8.00", "unit": "pack", "stock_quantity": 12, "description": "Tender lamb chops", "seasonal_status": "all_year"},
            # Bakery
            {"name": "Sourdough Loaf", "category": "bakery", "producer": "avon_bakery", "price": "3.80", "unit": "item", "stock_quantity": 20, "description": "Handmade sourdough with a crispy crust", "seasonal_status": "all_year", "allergen_info": "Contains gluten"},
            {"name": "Wholemeal Bread", "category": "bakery", "producer": "avon_bakery", "price": "2.50", "unit": "item", "stock_quantity": 25, "description": "Nutritious wholemeal loaf", "seasonal_status": "all_year", "allergen_info": "Contains gluten"},
            {"name": "Croissants (4 pack)", "category": "bakery", "producer": "avon_bakery", "price": "4.00", "unit": "pack", "stock_quantity": 15, "description": "Flaky butter croissants", "seasonal_status": "all_year", "allergen_info": "Contains gluten, milk, eggs"},
            {"name": "Scones (6 pack)", "category": "bakery", "producer": "avon_bakery", "price": "3.50", "unit": "pack", "stock_quantity": 18, "description": "Classic fruit scones", "seasonal_status": "all_year", "allergen_info": "Contains gluten, milk, eggs"},
            # Eggs
            {"name": "Free-Range Eggs (6 pack)", "category": "eggs", "producer": "bristol_farm", "price": "2.80", "unit": "pack", "stock_quantity": 40, "description": "Large free-range eggs from happy hens", "seasonal_status": "all_year", "allergen_info": "Contains eggs"},
            {"name": "Free-Range Eggs (12 pack)", "category": "eggs", "producer": "bristol_farm", "price": "4.80", "unit": "dozen", "stock_quantity": 30, "description": "Large free-range eggs, dozen box", "seasonal_status": "all_year", "allergen_info": "Contains eggs"},
            # Honey & Preserves
            {"name": "Local Wildflower Honey (340g)", "category": "honey-preserves", "producer": "bristol_farm", "price": "6.50", "unit": "item", "stock_quantity": 20, "description": "Raw wildflower honey from Bristol apiaries", "seasonal_status": "limited"},
            {"name": "Strawberry Jam (300g)", "category": "honey-preserves", "producer": "bristol_farm", "price": "3.80", "unit": "item", "stock_quantity": 25, "description": "Homemade strawberry jam", "seasonal_status": "all_year"},
            # Drinks
            {"name": "Apple Juice (1L)", "category": "drinks", "producer": "bristol_farm", "price": "3.20", "unit": "l", "stock_quantity": 30, "description": "Pressed from local Bramley apples", "seasonal_status": "in_season"},
            {"name": "Elderflower Cordial (500ml)", "category": "drinks", "producer": "bristol_farm", "price": "4.50", "unit": "ml", "stock_quantity": 20, "description": "Handmade elderflower cordial", "seasonal_status": "limited"},
        ]

        self._products = {}
        created_count = 0
        for p in data:
            cat = self._categories.get(p["category"])
            producer = self._producers.get(p["producer"])
            if not cat or not producer:
                continue
            product, created = Product.objects.get_or_create(
                producer=producer,
                name=p["name"],
                defaults={
                    "category": cat,
                    "price": Decimal(p["price"]),
                    "unit": p["unit"],
                    "stock_quantity": p["stock_quantity"],
                    "description": p["description"],
                    "is_available": True,
                    "seasonal_status": p["seasonal_status"],
                    "allergen_info": p.get("allergen_info", ""),
                    "harvest_date": today - timedelta(days=3),
                },
            )
            self._products[p["name"]] = product
            if created:
                created_count += 1
        self.stdout.write(f"  {created_count} new products created (total {Product.objects.count()})")

    def _seed_recipes(self):
        self.stdout.write("\nSeeding recipes...")
        data = [
            {
                "producer": "avon_bakery",
                "title": "Classic Sourdough Toast with Honey",
                "description": "A simple breakfast that lets local ingredients shine.",
                "ingredients": "2 slices Sourdough Loaf\n1 tbsp Local Wildflower Honey\n1 knob Organic Butter",
                "instructions": "1. Toast the sourdough until golden.\n2. Spread with butter while warm.\n3. Drizzle generously with honey and serve.",
                "seasonal_tag": "all_season",
                "products": ["Sourdough Loaf", "Local Wildflower Honey (340g)", "Organic Butter (250g)"],
            },
            {
                "producer": "somerset_dairy",
                "title": "Farmhouse Cheddar Mac & Cheese",
                "description": "Creamy comfort food using mature Somerset cheddar.",
                "ingredients": "300g pasta\n200g Farmhouse Cheddar, grated\n500ml Whole Milk\n40g Organic Butter\n40g flour",
                "instructions": "1. Cook pasta until al dente.\n2. Make a roux with butter and flour, whisk in milk.\n3. Stir in grated cheddar until smooth.\n4. Combine with pasta and bake at 200C for 15 minutes.",
                "seasonal_tag": "autumn_winter",
                "products": ["Farmhouse Cheddar (200g)", "Whole Milk (1L)", "Organic Butter (250g)"],
            },
            {
                "producer": "bristol_farm",
                "title": "Roasted Carrot and Potato Tray Bake",
                "description": "A hearty vegetarian dinner using seasonal roots.",
                "ingredients": "1kg Carrots\n2kg Potatoes\n1kg Onions\nOlive oil, rosemary, sea salt",
                "instructions": "1. Preheat oven to 200C.\n2. Chop vegetables into chunks.\n3. Toss with olive oil and rosemary.\n4. Roast for 45 minutes, turning halfway.",
                "seasonal_tag": "autumn_winter",
                "products": ["Carrots (1kg)", "Potatoes (2kg)", "Onions (1kg)"],
            },
            {
                "producer": "bristol_farm",
                "title": "Summer Berry Pavlova",
                "description": "Light meringue topped with fresh local berries.",
                "ingredients": "4 Free-Range Eggs (whites)\n200g caster sugar\n300ml double cream\n400g Strawberries\n200g Raspberries",
                "instructions": "1. Whisk egg whites to stiff peaks, gradually add sugar.\n2. Spread on baking sheet, bake at 120C for 1 hour.\n3. Top with whipped cream and fresh berries.",
                "seasonal_tag": "summer",
                "products": ["Free-Range Eggs (6 pack)", "Strawberries (400g)", "Raspberries (200g)"],
            },
            {
                "producer": "bristol_farm",
                "title": "Sausage and Bean Casserole",
                "description": "Slow-cooked stew perfect for cold evenings.",
                "ingredients": "1 pack Pork Sausages\n2 tins butter beans\n400g chopped tomatoes\n1 Onion\nFresh herbs",
                "instructions": "1. Brown sausages in a heavy pan.\n2. Add chopped onion, beans and tomatoes.\n3. Simmer for 45 minutes, stirring occasionally.",
                "seasonal_tag": "autumn_winter",
                "products": ["Pork Sausages (6 pack)", "Onions (1kg)", "Tomatoes (500g)"],
            },
            {
                "producer": "avon_bakery",
                "title": "Cream Tea Scones",
                "description": "Traditional West Country cream tea.",
                "ingredients": "6 Scones\n200ml clotted cream\n300g Strawberry Jam",
                "instructions": "1. Warm scones briefly in oven.\n2. Split and serve with jam and clotted cream.\n3. Enjoy with a strong cup of tea.",
                "seasonal_tag": "all_season",
                "products": ["Scones (6 pack)", "Strawberry Jam (300g)"],
            },
            {
                "producer": "somerset_dairy",
                "title": "Yogurt Parfait with Apple Compote",
                "description": "A wholesome breakfast or light dessert.",
                "ingredients": "500g Natural Yogurt\n6 Bramley Apples\n50g granola\n2 tbsp honey",
                "instructions": "1. Stew apples with a splash of water until soft.\n2. Layer yogurt, apple compote and granola in glasses.\n3. Drizzle with honey.",
                "seasonal_tag": "autumn_winter",
                "products": ["Natural Yogurt (500g)", "Apples - Bramley (6 pack)", "Local Wildflower Honey (340g)"],
            },
            {
                "producer": "bristol_farm",
                "title": "Garden Tomato Bruschetta",
                "description": "Fresh, zesty starter celebrating summer tomatoes.",
                "ingredients": "1 Sourdough Loaf\n500g Tomatoes\n1 garlic clove\nFresh basil, olive oil",
                "instructions": "1. Slice sourdough and toast.\n2. Rub with garlic.\n3. Top with diced tomatoes, basil and a drizzle of olive oil.",
                "seasonal_tag": "summer",
                "products": ["Sourdough Loaf", "Tomatoes (500g)"],
            },
        ]
        for r in data:
            recipe, created = Recipe.objects.get_or_create(
                producer=self._producers[r["producer"]],
                title=r["title"],
                defaults={
                    "description": r["description"],
                    "ingredients": r["ingredients"],
                    "instructions": r["instructions"],
                    "seasonal_tag": r["seasonal_tag"],
                    "is_published": True,
                },
            )
            self._row(f"Recipe '{recipe.title}'", created)
            for product_name in r["products"]:
                product = self._products.get(product_name)
                if product:
                    RecipeProduct.objects.get_or_create(recipe=recipe, product=product)

    def _seed_stories(self):
        self.stdout.write("\nSeeding farm stories...")
        data = [
            {
                "producer": "bristol_farm",
                "title": "Welcome to Bristol Farm",
                "content": "We're a family-run farm just outside Bristol, growing seasonal vegetables and raising free-range animals on 80 acres of pasture. Five generations of Hartleys have worked this land, and we're passionate about feeding our community with food that is grown with care, harvested at peak ripeness, and delivered straight to your door.",
            },
            {
                "producer": "bristol_farm",
                "title": "Why We Don't Spray",
                "content": "We choose not to use synthetic pesticides on our crops. Yes, we lose a few cabbages to caterpillars each year, but the trade-off is a thriving population of bees, hoverflies and ladybirds that keep our fields balanced. Healthy soil grows healthy food, and that's a principle we won't compromise on.",
            },
            {
                "producer": "somerset_dairy",
                "title": "From Pasture to Pint",
                "content": "Our herd of 60 dairy cows graze fresh Somerset pasture from April through October. We milk twice a day in our small parlour and bottle the milk on-site within hours of milking. Cows have names, not numbers - and you'll often find Daisy, Hazel and Buttercup waiting at the gate at milking time.",
            },
            {
                "producer": "somerset_dairy",
                "title": "How We Make Our Cheddar",
                "content": "Traditional farmhouse cheddar takes patience. Each truckle is hand-pressed, wrapped in muslin, and aged for at least 12 months in our cellars. The flavour deepens and crystallises as it matures, giving you that satisfying crunch and depth that mass-produced cheese can never match.",
            },
            {
                "producer": "avon_bakery",
                "title": "The Story of Our Sourdough Starter",
                "content": "Our sourdough starter, affectionately named Maeve, is over 30 years old. She came to us from my grandmother and is fed and tended every single day. Sourdough takes 24 hours from mix to bake, but the result is bread with a crisp crust, an open crumb, and a tangy depth no commercial loaf can replicate.",
            },
            {
                "producer": "avon_bakery",
                "title": "Why Local Flour Matters",
                "content": "We mill our own wholemeal flour from grain grown within 30 miles of the bakery. Local grain means fresher flour, better flavour, and a far smaller carbon footprint than imported wheat. It also means we know exactly how our wheat is grown - and that matters when it ends up on your breakfast table.",
            },
        ]
        for s in data:
            story, created = FarmStory.objects.get_or_create(
                producer=self._producers[s["producer"]],
                title=s["title"],
                defaults={"content": s["content"], "is_published": True},
            )
            self._row(f"Story '{story.title}'", created)

    def _seed_orders_and_reviews(self):
        """Create a few delivered orders so customers can review products."""
        self.stdout.write("\nSeeding delivered orders + reviews...")

        # Each tuple: (customer_username, [product_names], days_ago)
        order_specs = [
            ("testcustomer", ["Whole Milk (1L)", "Sourdough Loaf", "Free-Range Eggs (6 pack)"], 14),
            ("testcustomer", ["Farmhouse Cheddar (200g)", "Apples - Bramley (6 pack)"], 21),
            ("emily_jones", ["Strawberries (400g)", "Raspberries (200g)", "Natural Yogurt (500g)"], 7),
            ("emily_jones", ["Sourdough Loaf", "Local Wildflower Honey (340g)"], 30),
            ("david_smith", ["Pork Sausages (6 pack)", "Potatoes (2kg)", "Onions (1kg)"], 10),
            ("david_smith", ["Beef Mince (500g)", "Tomatoes (500g)"], 18),
            ("sarah_brown", ["Croissants (4 pack)", "Apple Juice (1L)"], 5),
            ("sarah_brown", ["Carrots (1kg)", "Broccoli", "Lamb Chops (4 pack)"], 25),
        ]

        # Each tuple: (customer, product_name, rating, title, text, anonymous, response)
        review_specs = [
            ("testcustomer", "Whole Milk (1L)", 5, "Tastes amazing", "Genuinely the best milk I've had in years. Creamy, fresh, and lasts for ages.", False, None),
            ("testcustomer", "Sourdough Loaf", 5, "Perfect crust", "Crispy outside, chewy inside. My new go-to weekend bread.", False, "Thank you! We bake every loaf the slow way."),
            ("testcustomer", "Free-Range Eggs (6 pack)", 4, "Lovely yolks", "Beautiful deep orange yolks. One was cracked on arrival but still 5 stars on flavour.", False, None),
            ("testcustomer", "Farmhouse Cheddar (200g)", 5, "Real cheddar", "Tangy, sharp and just the right amount of crystal crunch. Will reorder.", False, None),
            ("testcustomer", "Apples - Bramley (6 pack)", 4, "Great for crumbles", "Beautiful cooking apples. Made an excellent pie with these.", False, None),
            ("emily_jones", "Strawberries (400g)", 5, "Best of the season", "These taste like the strawberries I remember from my grandparents' garden.", False, None),
            ("emily_jones", "Raspberries (200g)", 5, "Bursting with flavour", "Hand-picked really shows. Sweet and intensely flavoured.", False, None),
            ("emily_jones", "Natural Yogurt (500g)", 4, "Thick and creamy", "Lovely with granola. Slightly less tang than I prefer but still excellent.", False, None),
            ("emily_jones", "Sourdough Loaf", 5, "Worth every penny", "Lasts the whole week and toasts beautifully. Fantastic bakery.", False, None),
            ("emily_jones", "Local Wildflower Honey (340g)", 5, "Floral and fragrant", "You can really taste the meadow flowers. A weekly treat now.", True, None),
            ("david_smith", "Pork Sausages (6 pack)", 5, "Proper bangers", "Meaty, herby, no rubbish fillers. The kids ask for these every week.", False, "Made fresh every Tuesday from our own pigs."),
            ("david_smith", "Potatoes (2kg)", 4, "Floury and good", "Roasted up beautifully. Some had a bit of green so docked one star.", False, None),
            ("david_smith", "Beef Mince (500g)", 5, "Lean and clean", "Made the best chilli I've ever cooked. Will buy again.", False, None),
            ("david_smith", "Tomatoes (500g)", 4, "Tasty", "Proper tomato flavour, none of that supermarket blandness.", False, None),
            ("sarah_brown", "Croissants (4 pack)", 5, "Like Paris", "Layers and layers of buttery flake. Saturday breakfast sorted.", False, None),
            ("sarah_brown", "Apple Juice (1L)", 4, "Refreshing", "Cloudy and full of flavour. A bit tart but I like that.", False, None),
            ("sarah_brown", "Carrots (1kg)", 5, "Sweet and crunchy", "Easily the best carrots we've had. Even raw they're delicious.", False, None),
            ("sarah_brown", "Lamb Chops (4 pack)", 5, "Sunday lunch sorted", "Tender, well-trimmed and cooked beautifully on the grill.", False, "We're so glad you enjoyed them!"),
        ]

        # Create one delivered order per spec so reviews have a verified order_id
        # to point at.
        order_lookup = {}  # (customer, frozenset(products)) -> Order
        for username, product_names, days_ago in order_specs:
            customer = self._customers.get(username)
            if not customer:
                continue
            products = [self._products[n] for n in product_names if n in self._products]
            if not products:
                continue
            key = (username, frozenset(p.id for p in products))
            existing = Order.objects.filter(
                user=customer,
                status=Order.STATUS_DELIVERED,
                items__product__in=products,
            ).distinct()
            # Try to match by exact product set
            order = None
            for cand in existing:
                cand_pids = frozenset(cand.items.values_list("product_id", flat=True))
                if cand_pids == key[1]:
                    order = cand
                    break
            if order is None:
                with transaction.atomic():
                    total = sum((p.price for p in products), Decimal("0.00"))
                    order = Order.objects.create(
                        user=customer,
                        status=Order.STATUS_DELIVERED,
                        total=total,
                        delivery_date=date.today() - timedelta(days=days_ago - 2),
                        commission=(total * Order.COMMISSION_RATE).quantize(Decimal("0.01")),
                        full_name=customer.get_full_name() or customer.username,
                        email=customer.email or f"{customer.username}@test.com",
                        address_line1=customer.delivery_address or "Bristol, UK",
                        city="Bristol",
                        postcode=customer.postcode or "BS1 1AA",
                    )
                    # Backdate created_at
                    Order.objects.filter(pk=order.pk).update(
                        created_at=timezone.now() - timedelta(days=days_ago)
                    )
                    for p in products:
                        OrderItem.objects.create(
                            order=order,
                            product=p,
                            product_name=p.name,
                            unit_price=p.price,
                            quantity=1,
                            line_total=p.price,
                        )
                self._row(f"Delivered order #{order.id} for {username}", True)
            else:
                self._row(f"Delivered order #{order.id} for {username}", False)
            order_lookup[key] = order

        # Now create reviews tied to the right delivered order
        for spec in review_specs:
            username, product_name, rating, title, text, anonymous, response = spec
            customer = self._customers.get(username)
            product = self._products.get(product_name)
            if not customer or not product:
                continue
            # Find a delivered order for this customer that contains this product
            order = (
                Order.objects
                .filter(user=customer, status=Order.STATUS_DELIVERED, items__product=product)
                .order_by("-created_at")
                .first()
            )
            if order is None:
                continue
            review, created = ProductReview.objects.get_or_create(
                product=product,
                customer=customer,
                defaults={
                    "order": order,
                    "rating": rating,
                    "title": title,
                    "review_text": text,
                    "is_anonymous": anonymous,
                    "producer_response": response or "",
                    "producer_response_date": timezone.now() if response else None,
                },
            )
            self._row(f"Review {rating}* '{title}' on {product.name}", created)

    def _seed_favorites(self):
        self.stdout.write("\nSeeding favourite recipes...")
        # Each customer favourites a couple of recipes
        favourite_specs = [
            ("testcustomer", "Classic Sourdough Toast with Honey"),
            ("testcustomer", "Cream Tea Scones"),
            ("emily_jones", "Summer Berry Pavlova"),
            ("emily_jones", "Yogurt Parfait with Apple Compote"),
            ("david_smith", "Sausage and Bean Casserole"),
            ("david_smith", "Roasted Carrot and Potato Tray Bake"),
            ("sarah_brown", "Garden Tomato Bruschetta"),
            ("sarah_brown", "Farmhouse Cheddar Mac & Cheese"),
        ]
        for username, recipe_title in favourite_specs:
            customer = self._customers.get(username)
            if not customer:
                continue
            recipe = Recipe.objects.filter(title=recipe_title).first()
            if not recipe:
                continue
            _, created = FavoriteRecipe.objects.get_or_create(user=customer, recipe=recipe)
            self._row(f"{username} ♥ '{recipe.title}'", created)
