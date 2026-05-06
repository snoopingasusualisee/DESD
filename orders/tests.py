"""
Tests for the order email notification feature.

We use Django's `locmem` email backend (django.core.mail.backends.locmem.EmailBackend),
which captures every email that would be "sent" into `django.core.mail.outbox`.
This lets us assert on subject, recipients, and body without ever touching real SMTP
or needing Gmail credentials in CI.
"""
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase, override_settings

from marketplace.models import Category, Product
from orders.models import Order, OrderItem
from orders.notifications import (
    sanitize_email_content,
    send_order_confirmation_email,
    send_status_update_email,
)


User = get_user_model()


@override_settings(
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
    DEFAULT_FROM_EMAIL='noreply@brfn.test',
)
class OrderConfirmationEmailTests(TestCase):
    """Tests for send_order_confirmation_email."""

    def setUp(self):
        mail.outbox = []

        self.customer = User.objects.create_user(
            username='alice',
            email='alice@example.com',
            password='testpass123',
            role='customer',
        )
        self.producer = User.objects.create_user(
            username='bob_farm',
            email='bob@farm.example',
            password='testpass123',
            role='producer',
        )
        self.category = Category.objects.create(name='Vegetables', slug='vegetables')
        self.product = Product.objects.create(
            category=self.category,
            producer=self.producer,
            name='Organic Carrots',
            price=Decimal('2.50'),
            stock_quantity=100,
        )

        self.order = Order.objects.create(
            user=self.customer,
            full_name='Alice Customer',
            email='alice@example.com',
            address_line1='123 Test Street',
            city='Bristol',
            postcode='BS1 4DJ',
            total=Decimal('5.00'),
            commission=Decimal('0.25'),
            delivery_date=date.today() + timedelta(days=3),
            status=Order.STATUS_CONFIRMED,
        )
        OrderItem.objects.create(
            order=self.order,
            product=self.product,
            product_name='Organic Carrots',
            unit_price=Decimal('2.50'),
            quantity=2,
            line_total=Decimal('5.00'),
        )

    def test_email_is_sent_when_order_confirmation_called(self):
        """One email should land in the outbox per call."""
        send_order_confirmation_email(self.order)
        self.assertEqual(len(mail.outbox), 1)

    def test_email_goes_to_the_orders_email_address(self):
        """Recipient must be the order.email, not the user.email (they can differ)."""
        send_order_confirmation_email(self.order)
        sent = mail.outbox[0]
        self.assertEqual(sent.to, ['alice@example.com'])

    def test_email_subject_contains_order_id(self):
        send_order_confirmation_email(self.order)
        self.assertIn(f"Order #{self.order.id}", mail.outbox[0].subject)
        self.assertIn("BRFN", mail.outbox[0].subject)

    def test_email_from_address_uses_default_from_email(self):
        send_order_confirmation_email(self.order)
        self.assertEqual(mail.outbox[0].from_email, 'noreply@brfn.test')

    def test_email_body_contains_receipt_details(self):
        """The body should contain the customer's name, items, totals, and delivery info."""
        send_order_confirmation_email(self.order)
        body = mail.outbox[0].body

        self.assertIn('Alice Customer', body)
        self.assertIn('Organic Carrots', body)
        self.assertIn('x2', body)
        self.assertIn('£5.00', body)
        self.assertIn('123 Test Street', body)
        self.assertIn('Bristol', body)
        self.assertIn('BS1 4DJ', body)

    def test_email_body_contains_commission_breakdown(self):
        send_order_confirmation_email(self.order)
        body = mail.outbox[0].body

        self.assertIn('Commission', body)
        self.assertIn('£0.25', body)
        self.assertIn('£5.25', body)

    def test_smtp_failure_is_caught_and_does_not_raise(self):
        """
        If the underlying send_mail throws (e.g. Gmail rejects credentials in prod),
        the view that called us must NOT 500 — the order is already paid for and
        committed. We log and move on.
        """
        with patch('orders.notifications.send_mail', side_effect=Exception('SMTP down')):
            send_order_confirmation_email(self.order)

        self.assertEqual(len(mail.outbox), 0)

    def test_header_injection_attempt_is_sanitised(self):
        """
        Sneaking newlines into name/email fields is a classic email-header-injection
        attack. We strip CR/LF before they ever reach the mail layer.
        """
        self.order.full_name = "Evil\r\nBcc: attacker@evil.com"
        self.order.save()

        send_order_confirmation_email(self.order)
        body = mail.outbox[0].body

        self.assertNotIn('\r\nBcc:', body)
        self.assertNotIn('\nBcc:', body)


@override_settings(
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
    DEFAULT_FROM_EMAIL='noreply@brfn.test',
)
class OrderStatusUpdateEmailTests(TestCase):
    """Tests for send_status_update_email."""

    def setUp(self):
        mail.outbox = []

        self.customer = User.objects.create_user(
            username='charlie',
            email='charlie@example.com',
            password='testpass123',
            role='customer',
        )
        self.order = Order.objects.create(
            user=self.customer,
            full_name='Charlie Buyer',
            email='charlie@example.com',
            address_line1='1 Some Lane',
            city='Bristol',
            postcode='BS2 0AA',
            total=Decimal('10.00'),
            delivery_date=date.today() + timedelta(days=2),
            status=Order.STATUS_READY,
        )

    def test_status_email_is_sent_to_order_email(self):
        send_status_update_email(
            self.order, Order.STATUS_CONFIRMED, Order.STATUS_READY,
        )
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ['charlie@example.com'])

    def test_status_email_includes_human_readable_status(self):
        send_status_update_email(
            self.order, Order.STATUS_CONFIRMED, Order.STATUS_READY,
        )
        body = mail.outbox[0].body
        self.assertIn('Ready', body)

    def test_producer_note_is_included_when_provided(self):
        send_status_update_email(
            self.order, Order.STATUS_CONFIRMED, Order.STATUS_READY,
            note='Pickup window is 9am-noon',
        )
        body = mail.outbox[0].body
        self.assertIn('Pickup window is 9am-noon', body)

    def test_producer_note_section_omitted_when_empty(self):
        send_status_update_email(
            self.order, Order.STATUS_CONFIRMED, Order.STATUS_READY, note='',
        )
        body = mail.outbox[0].body
        self.assertNotIn('Note from producer:', body)


class SanitiseEmailContentTests(TestCase):
    """Direct unit tests for the header-injection guard."""

    def test_strips_carriage_returns_and_newlines(self):
        result = sanitize_email_content("hello\r\nBcc: evil@x.com")
        self.assertNotIn('\r', result)
        self.assertNotIn('\n', result)

    def test_handles_none(self):
        self.assertEqual(sanitize_email_content(None), "")

    def test_handles_empty_string(self):
        self.assertEqual(sanitize_email_content(""), "")

    def test_preserves_normal_text(self):
        self.assertEqual(sanitize_email_content("Alice Smith"), "Alice Smith")
