import random
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone
from faker import Faker

from customers.models import Customer, Vehicle
from financial.models import PaymentMethod
from financial.services import (
    create_receivable_from_service_order,
    register_expense,
    register_payment,
)
from service_orders.models import ServiceOrder, ServiceOrderItem


class Command(BaseCommand):
    """
    Seed database with fake development data.
    """

    help = "Populate database with fake data for development"

    def add_arguments(self, parser):
        """
        Add command options.
        """
        parser.add_argument(
            "--customers",
            type=int,
            default=10,
            help="Number of customers to create.",
        )
        parser.add_argument(
            "--orders",
            type=int,
            default=20,
            help="Number of service orders to create.",
        )
        parser.add_argument(
            "--expenses",
            type=int,
            default=15,
            help="Number of expenses to create.",
        )

    def handle(self, *args, **options):
        """
        Run seed command.
        """
        self.fake = Faker("pt_BR")
        self.user = self.get_or_create_user()

        customers = self.create_customers(options["customers"])
        vehicles = self.create_vehicles(customers)
        service_orders = self.create_service_orders(
            customers=customers,
            vehicles=vehicles,
            quantity=options["orders"],
        )

        self.create_financial_data(service_orders)
        self.create_expenses(options["expenses"])

        self.stdout.write(self.style.SUCCESS("Fake data created successfully."))

    def get_or_create_user(self):
        """
        Return first user or create a default admin user.
        """
        User = get_user_model()

        user = User.objects.first()

        if user:
            return user

        return User.objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="admin123",
        )

    def has_field(self, model_class, field_name):
        """
        Check if model has a field.
        """
        return any(field.name == field_name for field in model_class._meta.fields)

    def get_choice_value(self, model_class, field_name, default):
        """
        Return a random valid choice value for a model field.
        """
        try:
            field = model_class._meta.get_field(field_name)
        except Exception:
            return default

        if not field.choices:
            return default

        return random.choice([choice[0] for choice in field.choices])

    def create_customers(self, quantity):
        """
        Create fake customers.
        """
        customers = []

        for _ in range(quantity):
            data = {}

            if self.has_field(Customer, "name"):
                data["name"] = self.fake.name()

            if self.has_field(Customer, "phone"):
                data["phone"] = self.fake.phone_number()

            if self.has_field(Customer, "email"):
                data["email"] = self.fake.unique.email()

            if self.has_field(Customer, "document"):
                data["document"] = self.fake.cpf()

            if self.has_field(Customer, "address"):
                data["address"] = self.fake.address()

            customer = Customer.objects.create(**data)
            customers.append(customer)

        return customers

    def create_vehicles(self, customers):
        """
        Create fake vehicles using the existing customers.Vehicle model.
        """
        vehicles = []

        for customer in customers:
            data = {}

            if self.has_field(Vehicle, "customer"):
                data["customer"] = customer

            if self.has_field(Vehicle, "brand"):
                data["brand"] = self.fake.company().split()[0]

            if self.has_field(Vehicle, "model"):
                data["model"] = self.fake.word().title()

            if self.has_field(Vehicle, "year"):
                data["year"] = random.randint(2010, 2025)

            if self.has_field(Vehicle, "plate"):
                data["plate"] = self.fake.unique.license_plate().upper()

            if self.has_field(Vehicle, "color"):
                data["color"] = self.fake.color_name()

            vehicle = Vehicle.objects.create(**data)
            vehicles.append(vehicle)

        return vehicles

    def create_service_orders(self, customers, vehicles, quantity):
        """
        Create fake service orders and fake items.
        """
        service_orders = []

        for _ in range(quantity):
            customer = random.choice(customers)
            vehicle = random.choice(vehicles)

            data = {}

            if self.has_field(ServiceOrder, "customer"):
                data["customer"] = customer

            if self.has_field(ServiceOrder, "vehicle"):
                data["vehicle"] = vehicle

            if self.has_field(ServiceOrder, "assigned_mechanic"):
                data["assigned_mechanic"] = self.user

            if self.has_field(ServiceOrder, "created_by"):
                data["created_by"] = self.user

            if self.has_field(ServiceOrder, "title"):
                data["title"] = self.fake.sentence(nb_words=4)

            if self.has_field(ServiceOrder, "description"):
                data["description"] = self.fake.paragraph(nb_sentences=2)

            if self.has_field(ServiceOrder, "diagnosis"):
                data["diagnosis"] = self.fake.paragraph(nb_sentences=2)

            if self.has_field(ServiceOrder, "solution"):
                data["solution"] = self.fake.paragraph(nb_sentences=2)

            if self.has_field(ServiceOrder, "status"):
                data["status"] = self.get_choice_value(
                    ServiceOrder,
                    "status",
                    "open",
                )

            if self.has_field(ServiceOrder, "priority"):
                data["priority"] = self.get_choice_value(
                    ServiceOrder,
                    "priority",
                    "medium",
                )

            if self.has_field(ServiceOrder, "expected_delivery_date"):
                data["expected_delivery_date"] = self.fake.date_between(
                    start_date="today",
                    end_date="+15d",
                )

            if self.has_field(ServiceOrder, "discount"):
                data["discount"] = Decimal(random.choice(["0.00", "10.00", "25.00"]))

            service_order = ServiceOrder.objects.create(**data)

            self.create_service_order_items(service_order)

            service_orders.append(service_order)

        return service_orders

    def create_service_order_items(self, service_order):
        """
        Create fake items for a service order.
        """
        for _ in range(random.randint(1, 4)):
            data = {}

            if self.has_field(ServiceOrderItem, "service_order"):
                data["service_order"] = service_order

            if self.has_field(ServiceOrderItem, "item_type"):
                data["item_type"] = self.get_choice_value(
                    ServiceOrderItem,
                    "item_type",
                    "service",
                )

            if self.has_field(ServiceOrderItem, "description"):
                data["description"] = self.fake.sentence(nb_words=5)

            if self.has_field(ServiceOrderItem, "quantity"):
                data["quantity"] = Decimal(random.randint(1, 3))

            if self.has_field(ServiceOrderItem, "unit_price"):
                data["unit_price"] = Decimal(random.randint(50, 800))

            ServiceOrderItem.objects.create(**data)

    def create_financial_data(self, service_orders):
        """
        Create receivables and payments.
        """
        for service_order in service_orders:
            if service_order.total_amount < Decimal("0.01"):
                continue

            receivable = create_receivable_from_service_order(
                service_order=service_order,
                created_by=self.user,
            )

            scenario = random.choice(["unpaid", "partial", "paid"])

            if scenario == "unpaid":
                continue

            if scenario == "partial":
                amount = (receivable.final_amount / Decimal("2.00")).quantize(
                    Decimal("0.01")
                )
            else:
                amount = receivable.final_amount

            if amount < Decimal("0.01"):
                continue

            register_payment(
                receivable=receivable,
                amount=amount,
                method=random.choice(PaymentMethod.values),
                created_by=self.user,
                paid_at=timezone.now(),
                notes=self.fake.sentence(nb_words=8),
            )

    def create_expenses(self, quantity):
        """
        Create fake expenses.
        """
        for _ in range(quantity):
            paid = random.choice([True, False])

            register_expense(
                description=self.fake.sentence(nb_words=5),
                amount=Decimal(random.randint(20, 2500)),
                created_by=self.user,
                due_date=self.fake.date_between(start_date="-10d", end_date="+20d"),
                paid_at=timezone.now() if paid else None,
                notes=self.fake.paragraph(nb_sentences=1),
            )