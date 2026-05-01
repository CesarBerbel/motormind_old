import random
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from faker import Faker

from customers.models import Customer, Vehicle
from financial.models import (
    CashFlowEntry,
    Expense,
    Payment,
    PaymentMethod,
    Receivable,
)
from financial.services import (
    create_receivable_from_service_order,
    register_expense,
    register_payment,
)
from service_orders.models import ServiceOrder, ServiceOrderItem


class Command(BaseCommand):
    """
    Seed database with realistic workshop data.
    """

    help = "Populate, reset, or reset and populate the development database."

    def add_arguments(self, parser):
        """
        Add command arguments.
        """
        parser.add_argument(
            "--only-seed",
            action="store_true",
            help="Only populate data without deleting existing data.",
        )

        parser.add_argument(
            "--reset-and-seed",
            action="store_true",
            help="Delete data, keep admin, create users and populate data.",
        )

        parser.add_argument(
            "--reset-only",
            action="store_true",
            help="Delete data and keep only admin user.",
        )

        parser.add_argument(
            "--orders",
            type=int,
            default=25,
            help="Number of service orders to create.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        """
        Execute selected seed mode.
        """
        self.fake = Faker("pt_BR")
        self.orders_count = options["orders"]

        selected_modes = [
            options["only_seed"],
            options["reset_and_seed"],
            options["reset_only"],
        ]

        if selected_modes.count(True) != 1:
            self.stdout.write(
                self.style.ERROR(
                    "Choose exactly one option: --only-seed, --reset-and-seed or --reset-only."
                )
            )
            return

        # RESET ONLY
        if options["reset_only"]:
            self.reset_database()
            return

        # RESET + SEED
        if options["reset_and_seed"]:
            self.reset_database()
        else:
            # ONLY SEED -> mantém usuários existentes
            self.admin_user = self.get_or_create_admin_user()

        self.create_users_by_existing_groups()

        customers = self.create_customers_and_vehicles()
        service_orders = self.create_service_orders(customers)

        self.create_financial_data(service_orders)
        self.create_expenses()

        self.stdout.write(self.style.SUCCESS("Realistic seed completed successfully."))

    def get_or_create_admin_user(self):
        """
        Return admin user or create it.
        """
        User = get_user_model()

        admin_user = User.objects.filter(email="admin@admin.com").first()

        if admin_user:
            admin_user.is_staff = True
            admin_user.is_superuser = True
            admin_user.is_active = True
            admin_user.set_password("321654")
            admin_user.save()
            return admin_user

        return User.objects.create_superuser(            
            email="admin@admin.com",
            password="321654",
        )

    def reset_database(self):
        """
        Delete all data and recreate admin user.
        """
        self.stdout.write(self.style.WARNING("Resetting database..."))

        User = get_user_model()

        # Delete all financial data
        CashFlowEntry.objects.all().delete()
        Payment.objects.all().delete()
        Receivable.objects.all().delete()
        Expense.objects.all().delete()

        # Delete service orders
        ServiceOrderItem.objects.all().delete()
        ServiceOrder.objects.all().delete()

        # Delete customers and vehicles
        Vehicle.objects.all().delete()
        Customer.objects.all().delete()

        # Delete ALL users
        User.objects.all().delete()

        # Recreate admin
        self.admin_user = User.objects.create_superuser(
            email="admin@admin.com",
            password="321654",
        )

        self.stdout.write(self.style.SUCCESS("Database reset completed with new admin."))

    def create_users_by_existing_groups(self):
        """
        Create 5 users for each existing group.
        """
        User = get_user_model()
        groups = Group.objects.all().order_by("name")

        if not groups.exists():
            self.stdout.write(
                self.style.WARNING(
                    "No groups found. Create groups first if you want role-based users."
                )
            )
            return

        for group in groups:
            group_slug = group.name.lower().replace(" ", "_").replace("-", "_")

            for index in range(1, 6):
                email = f"{group_slug}{index}@motormind.test"

                user, created = User.objects.get_or_create(
                    email=email,
                    defaults={
                        "is_active": True,
                        "is_staff": False,
                    },
                )

                if created:
                    user.set_password("123456")
                    user.save()

                user.groups.clear()
                user.groups.add(group)

        self.stdout.write(self.style.SUCCESS("Users by group created successfully."))

    def has_field(self, model_class, field_name):
        """
        Check if model has field.
        """
        return any(field.name == field_name for field in model_class._meta.fields)

    def get_choice_value(self, model_class, field_name, preferred_values, default):
        """
        Return valid choice value.
        """
        try:
            field = model_class._meta.get_field(field_name)
        except Exception:
            return default

        if not field.choices:
            return default

        choices = [choice[0] for choice in field.choices]

        for preferred_value in preferred_values:
            if preferred_value in choices:
                return preferred_value

        return random.choice(choices)

    def create_customers_and_vehicles(self):
        """
        Create realistic customers and vehicles.
        """
        customers_data = [
            ("João Pereira", "(11) 98845-1200", "joao.pereira@example.com", [("Toyota", "Corolla", 2018, "Prata", "ABC1D23")]),
            ("Maria Oliveira", "(21) 99714-8821", "maria.oliveira@example.com", [("Honda", "Civic", 2020, "Preto", "HJK7L89")]),
            ("Carlos Mendes", "(31) 98420-7744", "carlos.mendes@example.com", [("Volkswagen", "Gol", 2015, "Branco", "MNO2P34")]),
            ("Ana Costa", "(41) 99122-4410", "ana.costa@example.com", [("Chevrolet", "Onix", 2019, "Vermelho", "QRS5T67")]),
            ("Roberto Lima", "(51) 98977-5533", "roberto.lima@example.com", [("Hyundai", "HB20", 2017, "Azul", "UVW8X90")]),
            ("Fernanda Rocha", "(61) 99685-3301", "fernanda.rocha@example.com", [("Jeep", "Renegade", 2021, "Cinza", "YZA3B45")]),
        ]

        customers = []

        for name, phone, email, vehicles in customers_data:
            customer_data = {"name": name}

            if self.has_field(Customer, "phone"):
                customer_data["phone"] = phone

            if self.has_field(Customer, "email"):
                customer_data["email"] = email

            customer = Customer.objects.create(**customer_data)
            customers.append(customer)

            for brand, model, year, color, plate in vehicles:
                vehicle_data = {}

                if self.has_field(Vehicle, "customer"):
                    vehicle_data["customer"] = customer

                if self.has_field(Vehicle, "brand"):
                    vehicle_data["brand"] = brand

                if self.has_field(Vehicle, "model"):
                    vehicle_data["model"] = model

                if self.has_field(Vehicle, "year"):
                    vehicle_data["year"] = year

                if self.has_field(Vehicle, "color"):
                    vehicle_data["color"] = color

                if self.has_field(Vehicle, "plate"):
                    vehicle_data["plate"] = plate

                Vehicle.objects.create(**vehicle_data)

        return customers

    def get_service_templates(self):
        """
        Return controlled service templates.
        """
        return [
            {
                "title": "Troca de óleo e filtros",
                "description": "Revisão preventiva básica com troca de óleo e filtros.",
                "diagnosis": "Óleo vencido e filtros com acúmulo de sujeira.",
                "solution": "Substituição do óleo, filtro de óleo e filtro de ar.",
                "parts": [
                    ("Óleo sintético 5W30", Decimal("4.00"), Decimal("48.00")),
                    ("Filtro de óleo", Decimal("1.00"), Decimal("42.00")),
                    ("Filtro de ar", Decimal("1.00"), Decimal("58.00")),
                ],
                "services": [
                    ("Mão de obra troca de óleo e filtros", Decimal("1.00"), Decimal("95.00")),
                ],
            },
            {
                "title": "Revisão do sistema de freios",
                "description": "Cliente relatou ruído ao frear.",
                "diagnosis": "Pastilhas dianteiras desgastadas e fluido escurecido.",
                "solution": "Troca das pastilhas e substituição do fluido de freio.",
                "parts": [
                    ("Jogo de pastilhas dianteiras", Decimal("1.00"), Decimal("190.00")),
                    ("Fluido de freio DOT 4", Decimal("1.00"), Decimal("52.00")),
                ],
                "services": [
                    ("Mão de obra revisão de freios", Decimal("1.00"), Decimal("170.00")),
                ],
            },
            {
                "title": "Troca de bateria",
                "description": "Veículo com dificuldade na partida.",
                "diagnosis": "Bateria com baixa capacidade de retenção de carga.",
                "solution": "Substituição da bateria e teste do alternador.",
                "parts": [
                    ("Bateria 60Ah", Decimal("1.00"), Decimal("440.00")),
                ],
                "services": [
                    ("Instalação da bateria e teste de carga", Decimal("1.00"), Decimal("75.00")),
                ],
            },
            {
                "title": "Diagnóstico eletrônico",
                "description": "Luz da injeção acesa no painel.",
                "diagnosis": "Scanner apontou falha intermitente em sensor.",
                "solution": "Leitura com scanner, limpeza de conectores e teste de rodagem.",
                "parts": [],
                "services": [
                    ("Diagnóstico com scanner automotivo", Decimal("1.00"), Decimal("150.00")),
                ],
            },
        ]

    def create_service_orders(self, customers):
        """
        Create realistic service orders.
        """
        service_orders = []
        templates = self.get_service_templates()

        for _ in range(self.orders_count):
            customer = random.choice(customers)
            vehicle = customer.vehicles.first()
            template = random.choice(templates)

            service_order_data = {}

            if self.has_field(ServiceOrder, "customer"):
                service_order_data["customer"] = customer

            if self.has_field(ServiceOrder, "vehicle") and vehicle:
                service_order_data["vehicle"] = vehicle

            if self.has_field(ServiceOrder, "assigned_mechanic"):
                service_order_data["assigned_mechanic"] = self.admin_user

            if self.has_field(ServiceOrder, "created_by"):
                service_order_data["created_by"] = self.admin_user

            if self.has_field(ServiceOrder, "title"):
                service_order_data["title"] = template["title"]

            if self.has_field(ServiceOrder, "description"):
                service_order_data["description"] = template["description"]

            if self.has_field(ServiceOrder, "diagnosis"):
                service_order_data["diagnosis"] = template["diagnosis"]

            if self.has_field(ServiceOrder, "solution"):
                service_order_data["solution"] = template["solution"]

            if self.has_field(ServiceOrder, "status"):
                service_order_data["status"] = self.get_choice_value(
                    ServiceOrder,
                    "status",
                    ["open", "in_progress", "finished"],
                    "open",
                )

            if self.has_field(ServiceOrder, "priority"):
                service_order_data["priority"] = self.get_choice_value(
                    ServiceOrder,
                    "priority",
                    ["medium", "high", "low"],
                    "medium",
                )

            if self.has_field(ServiceOrder, "expected_delivery_date"):
                service_order_data["expected_delivery_date"] = self.fake.date_between(
                    start_date="today",
                    end_date="+12d",
                )

            if self.has_field(ServiceOrder, "discount"):
                service_order_data["discount"] = Decimal(
                    random.choice(["0.00", "20.00", "35.00"])
                )

            service_order = ServiceOrder.objects.create(**service_order_data)

            self.create_service_order_items(service_order, template)
            service_orders.append(service_order)

        return service_orders

    def create_service_order_items(self, service_order, template):
        """
        Create parts and service items.
        """
        part_type = self.get_choice_value(
            ServiceOrderItem,
            "item_type",
            ["part", "parts"],
            "part",
        )

        service_type = self.get_choice_value(
            ServiceOrderItem,
            "item_type",
            ["service", "labor"],
            "service",
        )

        for description, quantity, unit_price in template["parts"]:
            self.create_service_order_item(
                service_order=service_order,
                item_type=part_type,
                description=description,
                quantity=quantity,
                unit_price=unit_price,
            )

        for description, quantity, unit_price in template["services"]:
            self.create_service_order_item(
                service_order=service_order,
                item_type=service_type,
                description=description,
                quantity=quantity,
                unit_price=unit_price,
            )

    def create_service_order_item(
        self,
        service_order,
        item_type,
        description,
        quantity,
        unit_price,
    ):
        """
        Create one service order item.
        """
        item_data = {}

        if self.has_field(ServiceOrderItem, "service_order"):
            item_data["service_order"] = service_order

        if self.has_field(ServiceOrderItem, "item_type"):
            item_data["item_type"] = item_type

        if self.has_field(ServiceOrderItem, "description"):
            item_data["description"] = description

        if self.has_field(ServiceOrderItem, "quantity"):
            item_data["quantity"] = quantity

        if self.has_field(ServiceOrderItem, "unit_price"):
            item_data["unit_price"] = unit_price

        ServiceOrderItem.objects.create(**item_data)

    def create_financial_data(self, service_orders):
        """
        Create receivables and payments.
        """
        for service_order in service_orders:
            if service_order.total_amount < Decimal("0.01"):
                continue

            try:
                receivable = create_receivable_from_service_order(
                    service_order=service_order,
                    created_by=self.admin_user,
                )
            except Exception:
                continue

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
                created_by=self.admin_user,
                paid_at=timezone.now(),
                notes=f"Pagamento referente à OS #{service_order.pk}.",
            )

    def create_expenses(self):
        """
        Create realistic expenses.
        """
        expenses = [
            ("Aluguel da oficina", Decimal("2800.00")),
            ("Energia elétrica", Decimal("740.00")),
            ("Conta de água", Decimal("180.00")),
            ("Internet e telefone", Decimal("220.00")),
            ("Compra de ferramentas", Decimal("1350.00")),
            ("Reposição de estoque", Decimal("3200.00")),
            ("Material de limpeza", Decimal("160.00")),
            ("Sistema de gestão", Decimal("149.90")),
        ]

        for description, amount in expenses:
            register_expense(
                description=description,
                amount=amount,
                created_by=self.admin_user,
                due_date=self.fake.date_between(start_date="-10d", end_date="+20d"),
                paid_at=timezone.now() if random.choice([True, False]) else None,
                notes=f"Despesa operacional: {description}.",
            )