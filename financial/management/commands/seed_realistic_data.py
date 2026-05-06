import random
import unicodedata
from decimal import Decimal

from django.apps import apps
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models.deletion import ProtectedError
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
            help="Delete data, recreate admin and populate data.",
        )
        parser.add_argument(
            "--reset-only",
            action="store_true",
            help="Delete data and recreate only admin user.",
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

        if options["reset_only"]:
            self.reset_database()
            return

        if options["reset_and_seed"]:
            self.reset_database()
        else:
            self.admin_user = self.get_or_create_admin_user()

        self.ensure_default_groups()
        self.create_users_by_existing_groups()

        employees = self.create_employees()
        parts = self.create_parts()

        customers = self.create_customers_and_vehicles()
        service_orders = self.create_service_orders(
            customers=customers,
            employees=employees,
            parts=parts,
        )

        self.create_financial_data(service_orders)
        self.create_expenses()

        self.stdout.write(self.style.SUCCESS("Realistic seed completed successfully."))

    # =========================
    # RESET
    # =========================

    def reset_database(self):
        """
        Delete development data in dependency-safe order and recreate admin user.
        """
        self.stdout.write(self.style.WARNING("Resetting database..."))

        delete_order = [
            # Financial children.
            ("financial", "CashFlowEntry"),
            ("financial", "Payment"),
            ("financial", "Receivable"),
            ("financial", "Expense"),
            # Inventory/order integration.
            ("inventory", "StockMovement"),
            ("inventory", "PartStockMovement"),
            ("inventory", "ServiceOrderPart"),
            # Service order children.
            ("service_orders", "ServiceOrderItem"),
            ("service_orders", "ServiceOrderHistory"),
            ("service_orders", "ServiceOrderNote"),
            ("service_orders", "ServiceOrderTimeEntry"),
            # Service orders.
            ("service_orders", "ServiceOrder"),
            # Extra inventory movement aliases.
            ("inventory", "InventoryMovement"),
            ("inventory", "Movement"),
            ("inventory", "PartMovement"),
            # Parts before lookup tables protected by FK.
            ("inventory", "Part"),
            ("service_orders", "Part"),
            # Lookup tables after parts.
            ("inventory", "PartBrand"),
            ("inventory", "PartCategory"),
            ("inventory", "Brand"),
            ("inventory", "Category"),
            # Optional legacy service models.
            ("service_orders", "Employee"),
            # Vehicles before customers.
            ("customers", "Vehicle"),
            ("vehicles", "Vehicle"),
            ("customers", "Customer"),
        ]

        for app_label, model_name in delete_order:
            self.delete_model_objects_if_exists(app_label, model_name)

        User = get_user_model()

        self.delete_objects_referencing_model(User)
        self.delete_model_objects_if_exists(
            User._meta.app_label, User._meta.object_name
        )

        self.admin_user = self.create_admin_user()
        self.ensure_default_groups()

        self.stdout.write(self.style.SUCCESS("Database reset completed."))

    def delete_model_objects_if_exists(self, app_label, model_name):
        """
        Delete all objects for an optional model when it exists.
        """
        try:
            model_class = apps.get_model(app_label, model_name)
        except LookupError:
            return

        queryset = model_class.objects.all()

        if not queryset.exists():
            return

        try:
            result = queryset.delete()
        except ProtectedError as error:
            protected_models = sorted(
                {
                    protected_object.__class__._meta.label
                    for protected_object in error.protected_objects
                }
            )

            raise CommandError(
                f"Cannot delete {model_class._meta.label}. "
                f"Protected by: {', '.join(protected_models)}"
            ) from error

        deleted_count = result[0] if isinstance(result, tuple) else result

        self.stdout.write(
            self.style.SUCCESS(
                f"Deleted {deleted_count} object(s) from {model_class._meta.label}."
            )
        )

    def delete_objects_referencing_model(self, target_model):
        """
        Delete objects from installed business models that directly reference target_model.

        Only concrete FK/OneToOne fields are considered. Reverse relations and
        many-to-many relations are ignored to avoid deleting auth groups.
        """
        ignored_models = {
            "auth.Group",
            "auth.Permission",
            "contenttypes.ContentType",
            target_model._meta.label,
        }

        for model_class in apps.get_models():
            if model_class._meta.label in ignored_models:
                continue

            references_target = False

            for field in model_class._meta.fields:
                if not getattr(field, "is_relation", False):
                    continue

                if not getattr(field, "remote_field", None):
                    continue

                if field.remote_field.model == target_model:
                    references_target = True
                    break

            if not references_target:
                continue

            queryset = model_class.objects.all()

            if not queryset.exists():
                continue

            try:
                result = queryset.delete()
            except ProtectedError as error:
                protected_models = sorted(
                    {
                        protected_object.__class__._meta.label
                        for protected_object in error.protected_objects
                    }
                )

                raise CommandError(
                    f"Cannot delete objects from {model_class._meta.label} "
                    f"before deleting {target_model._meta.label}. "
                    f"Protected by: {', '.join(protected_models)}"
                ) from error

            deleted_count = result[0] if isinstance(result, tuple) else result

            self.stdout.write(
                self.style.SUCCESS(
                    f"Deleted {deleted_count} object(s) from {model_class._meta.label} "
                    f"because it references {target_model._meta.label}."
                )
            )

    # =========================
    # USERS / GROUPS
    # =========================

    def ensure_default_groups(self):
        """
        Ensure default role groups exist before creating group users.
        """
        group_names = [
            "Administrador",
            "Atendente",
            "Mecanico",
            "Financeiro",
        ]

        for group_name in group_names:
            Group.objects.get_or_create(name=group_name)

    def create_admin_user(self):
        """
        Create admin user with the expected default password.
        """
        User = get_user_model()

        return User.objects.create_superuser(
            email="admin@admin.com",
            password="321654",
        )

    def get_or_create_admin_user(self):
        """
        Return admin user or create it with a valid password.
        """
        User = get_user_model()

        admin_user = User.objects.filter(email="admin@admin.com").first()

        if admin_user:
            if not admin_user.has_usable_password():
                admin_user.set_password("321654")
                admin_user.save(update_fields=["password"])

            return admin_user

        return self.create_admin_user()

    def normalize_group_slug_for_email(self, group_name):
        """
        Convert a group name into a deterministic ASCII slug safe for email local-part.
        """
        normalized = unicodedata.normalize("NFKD", group_name)
        ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
        ascii_text = ascii_text.lower().strip()

        allowed_chars = []
        previous_was_separator = False

        for char in ascii_text:
            if char.isalnum():
                allowed_chars.append(char)
                previous_was_separator = False
            elif char in {" ", "-", "_"} and not previous_was_separator:
                allowed_chars.append("_")
                previous_was_separator = True

        slug = "".join(allowed_chars).strip("_")

        if not slug:
            return "grupo"

        return slug

    def create_users_by_existing_groups(self):
        """
        Create 5 users for each existing group with first name and last name.
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

        people_names = [
            ("Lucas", "Ferreira"),
            ("Mariana", "Almeida"),
            ("Pedro", "Castro"),
            ("Bianca", "Ribeiro"),
            ("Gustavo", "Mendes"),
        ]

        for group in groups:
            group_slug = self.normalize_group_slug_for_email(group.name)

            for index, (first_name, last_name) in enumerate(people_names, start=1):
                email = f"{group_slug}{index}@motormind.test"

                user = User.objects.filter(email=email).first()

                if not user:
                    user = User.objects.create_user(
                        email=email,
                        password="123456",
                    )

                user.first_name = first_name
                user.last_name = last_name
                user.is_active = True
                user.is_staff = False
                user.set_password("123456")
                user.save()
                user.groups.clear()
                user.groups.add(group)

        self.stdout.write(self.style.SUCCESS("Users by group created successfully."))

    # =========================
    # HELPERS
    # =========================

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

    def get_first_existing_field(self, model_class, field_names):
        """
        Return the first field name that exists in the model.
        """
        for field_name in field_names:
            if self.has_field(model_class, field_name):
                return field_name

        return None

    def get_employee_model(self):
        """
        Return Employee model if it exists.
        """
        try:
            return apps.get_model("service_orders", "Employee")
        except LookupError:
            return None

    def get_part_model(self):
        """
        Return Part model if it exists.
        """
        try:
            return apps.get_model("inventory", "Part")
        except LookupError:
            try:
                return apps.get_model("service_orders", "Part")
            except LookupError:
                return None

    def get_service_order_part_model(self):
        """
        Return inventory ServiceOrderPart model if it exists.
        """
        try:
            return apps.get_model("inventory", "ServiceOrderPart")
        except LookupError:
            return None

    def get_part_stock_movement_model(self):
        """
        Return PartStockMovement model if it exists.
        """
        try:
            return apps.get_model("inventory", "PartStockMovement")
        except LookupError:
            return None

    def get_stock_movement_model(self):
        """
        Return StockMovement model if it exists.
        """
        try:
            return apps.get_model("inventory", "StockMovement")
        except LookupError:
            return None

    def get_or_create_random_part_brand(self, preferred_name=None):
        """
        Return a random or preferred PartBrand instance.
        """
        PartBrand = apps.get_model("inventory", "PartBrand")

        brand_names = [
            "Bosch",
            "Mobil",
            "Mann",
            "Tecfil",
            "Fras-le",
            "Moura",
            "Gates",
            "SKF",
            "Urba",
            "Nakata",
            "Schaeffler",
            "Mahle",
            "NGK",
            "Denso",
            "Monroe",
            "TRW",
            "Cobreq",
            "Varga",
            "Magneti Marelli",
            "Continental",
        ]

        brand_name = preferred_name or random.choice(brand_names)

        brand, _created = PartBrand.objects.get_or_create(
            name=brand_name,
            defaults={"is_active": True},
        )

        return brand

    def get_or_create_random_part_category(self, preferred_name=None):
        """
        Return a random or preferred PartCategory instance.
        """
        PartCategory = apps.get_model("inventory", "PartCategory")

        category_names = [
            "Freio",
            "Motor",
            "Suspensão",
            "Filtros",
            "Lubrificantes",
            "Elétrica",
            "Arrefecimento",
            "Correias",
            "Bateria",
            "Direção",
        ]

        category_name = preferred_name or random.choice(category_names)

        category, _created = PartCategory.objects.get_or_create(
            name=category_name,
            defaults={"is_active": True},
        )

        return category

    # =========================
    # CPF
    # =========================

    def generate_valid_cpf(self):
        """
        Generate a valid Brazilian CPF without mask.
        """
        base_digits = [random.randint(0, 9) for _ in range(9)]

        first_digit = self.calculate_cpf_digit(base_digits, 10)
        second_digit = self.calculate_cpf_digit(base_digits + [first_digit], 11)

        cpf_digits = base_digits + [first_digit, second_digit]

        return "".join(str(digit) for digit in cpf_digits)

    def calculate_cpf_digit(self, digits, weight_start):
        """
        Calculate CPF verification digit.
        """
        total = sum(
            digit * (weight_start - index) for index, digit in enumerate(digits)
        )
        remainder = (total * 10) % 11

        if remainder == 10:
            return 0

        return remainder

    def generate_unique_customer_cpf(self):
        """
        Generate valid unique customer CPF.
        """
        while True:
            cpf = self.generate_valid_cpf()

            if not Customer.objects.filter(document=cpf).exists():
                return cpf

    def generate_unique_employee_cpf(self, Employee):
        """
        Generate valid unique employee CPF.
        """
        while True:
            cpf = self.generate_valid_cpf()

            if not Employee.objects.filter(document=cpf).exists():
                return cpf

    # =========================
    # EMPLOYEES
    # =========================

    def create_employees(self):
        """
        Create realistic employees with first name and last name.
        """
        Employee = self.get_employee_model()

        if not Employee:
            return []

        employee_data = [
            ("Carlos", "Almeida", "mechanic"),
            ("Rafael", "Moura", "electrician"),
            ("João", "Batista", "bodywork"),
            ("Ana", "Souza", "attendant"),
            ("Fernanda", "Lima", "financial"),
            ("Marcos", "Pereira", "manager"),
        ]

        employees = []

        for first_name, last_name, preferred_role in employee_data:
            data = {}

            if self.has_field(Employee, "first_name"):
                data["first_name"] = first_name

            if self.has_field(Employee, "last_name"):
                data["last_name"] = last_name

            if self.has_field(Employee, "name"):
                data["name"] = f"{first_name} {last_name}"

            if self.has_field(Employee, "cpf"):
                data["cpf"] = self.generate_unique_employee_cpf(Employee)

            if self.has_field(Employee, "document"):
                data["document"] = self.generate_unique_employee_cpf(Employee)

            if self.has_field(Employee, "role"):
                data["role"] = self.get_choice_value(
                    Employee,
                    "role",
                    [preferred_role],
                    preferred_role,
                )

            if self.has_field(Employee, "phone"):
                data["phone"] = self.fake.phone_number()

            if self.has_field(Employee, "is_active"):
                data["is_active"] = True

            employee = Employee.objects.create(**data)
            employees.append(employee)

        return employees

    # =========================
    # PARTS
    # =========================

    def create_parts(self):
        """
        Create controlled parts catalog with current and minimum stock scenarios.
        """
        Part = self.get_part_model()

        if not Part:
            self.stdout.write(
                self.style.WARNING(
                    "Part model not found. Parts catalog will not be created."
                )
            )
            return []

        parts_data = [
            (
                "Óleo sintético 5W30",
                "OIL-5W30",
                "Mobil",
                "Lubrificantes",
                Decimal("32.00"),
                Decimal("48.00"),
                Decimal("60.00"),
                Decimal("15.00"),
            ),
            (
                "Filtro de óleo",
                "FILTER-OIL-001",
                "Mann",
                "Filtros",
                Decimal("25.00"),
                Decimal("42.00"),
                Decimal("40.00"),
                Decimal("10.00"),
            ),
            (
                "Filtro de ar",
                "FILTER-AIR-001",
                "Tecfil",
                "Filtros",
                Decimal("34.00"),
                Decimal("58.00"),
                Decimal("35.00"),
                Decimal("10.00"),
            ),
            (
                "Jogo de pastilhas dianteiras",
                "BRAKE-PAD-FRONT",
                "Fras-le",
                "Freio",
                Decimal("120.00"),
                Decimal("190.00"),
                Decimal("3.00"),
                Decimal("8.00"),
            ),
            (
                "Fluido de freio DOT 4",
                "BRAKE-FLUID-DOT4",
                "Bosch",
                "Freio",
                Decimal("31.00"),
                Decimal("52.00"),
                Decimal("4.00"),
                Decimal("12.00"),
            ),
            (
                "Bateria 60Ah",
                "BATTERY-60AH",
                "Moura",
                "Bateria",
                Decimal("320.00"),
                Decimal("440.00"),
                Decimal("5.00"),
                Decimal("5.00"),
            ),
            (
                "Kit correia dentada",
                "TIMING-BELT-KIT",
                "Gates",
                "Correias",
                Decimal("290.00"),
                Decimal("430.00"),
                Decimal("10.00"),
                Decimal("4.00"),
            ),
            (
                "Tensor da correia",
                "BELT-TENSIONER",
                "SKF",
                "Correias",
                Decimal("105.00"),
                Decimal("165.00"),
                Decimal("15.00"),
                Decimal("6.00"),
            ),
            (
                "Bomba d'água",
                "WATER-PUMP",
                "Urba",
                "Arrefecimento",
                Decimal("170.00"),
                Decimal("250.00"),
                Decimal("10.00"),
                Decimal("4.00"),
            ),
            (
                "Par de bieletas",
                "STABILIZER-LINK-PAIR",
                "Nakata",
                "Suspensão",
                Decimal("95.00"),
                Decimal("155.00"),
                Decimal("18.00"),
                Decimal("6.00"),
            ),
        ]

        current_stock_field = self.get_first_existing_field(
            Part,
            [
                "current_stock",
                "stock_quantity",
                "quantity",
                "stock",
                "available_quantity",
            ],
        )

        minimum_stock_field = self.get_first_existing_field(
            Part,
            ["minimum_stock", "min_stock", "minimum_quantity", "min_quantity"],
        )

        parts = []

        for (
            name,
            code,
            brand_name,
            category_name,
            cost_price,
            sale_price,
            current_stock,
            minimum_stock,
        ) in parts_data:
            defaults = {}

            if self.has_field(Part, "name"):
                defaults["name"] = name

            if self.has_field(Part, "description"):
                defaults["description"] = name

            if self.has_field(Part, "brand"):
                brand_field = Part._meta.get_field("brand")

                if brand_field.is_relation:
                    defaults["brand"] = self.get_or_create_random_part_brand(
                        preferred_name=brand_name
                    )
                else:
                    defaults["brand"] = brand_name

            if self.has_field(Part, "category"):
                category_field = Part._meta.get_field("category")

                if category_field.is_relation:
                    defaults["category"] = self.get_or_create_random_part_category(
                        preferred_name=category_name
                    )
                else:
                    defaults["category"] = category_name

            if self.has_field(Part, "cost_price"):
                defaults["cost_price"] = cost_price

            if self.has_field(Part, "purchase_price"):
                defaults["purchase_price"] = cost_price

            if self.has_field(Part, "sale_price"):
                defaults["sale_price"] = sale_price

            if self.has_field(Part, "price"):
                defaults["price"] = sale_price

            if current_stock_field:
                defaults[current_stock_field] = current_stock

            if minimum_stock_field:
                defaults[minimum_stock_field] = minimum_stock

            if self.has_field(Part, "unit"):
                defaults["unit"] = "un"

            if self.has_field(Part, "location"):
                defaults["location"] = f"Prateleira {random.choice(['A1', 'B2', 'C3'])}"

            if self.has_field(Part, "is_active"):
                defaults["is_active"] = True

            lookup = {}

            if self.has_field(Part, "internal_code"):
                lookup["internal_code"] = code
            elif self.has_field(Part, "sku"):
                lookup["sku"] = code
            elif self.has_field(Part, "code"):
                lookup["code"] = code
            else:
                lookup["name"] = name

            part, _created = Part.objects.update_or_create(
                **lookup,
                defaults=defaults,
            )

            parts.append(part)

        return parts

    def find_part_by_sku(self, parts, sku):
        """
        Find part by internal code, sku or code.
        """
        for part in parts:
            if hasattr(part, "internal_code") and part.internal_code == sku:
                return part

            if hasattr(part, "sku") and part.sku == sku:
                return part

            if hasattr(part, "code") and part.code == sku:
                return part

        return None

    # =========================
    # SERVICE ORDER PARTS
    # =========================

    def create_inventory_service_order_part_if_possible(
        self,
        service_order,
        part,
        quantity,
    ):
        """
        Create inventory ServiceOrderPart record correctly.
        """
        ServiceOrderPartModel = self.get_service_order_part_model()

        if not ServiceOrderPartModel:
            return None

        unit_price = getattr(
            part,
            "sale_price",
            Decimal("0.00"),
        )

        if not unit_price or unit_price <= Decimal("0.00"):
            unit_price = Decimal("10.00")

        quantity = quantity or Decimal("1.00")

        data = {}

        if self.has_field(ServiceOrderPartModel, "service_order"):
            data["service_order"] = service_order

        if self.has_field(ServiceOrderPartModel, "part"):
            data["part"] = part

        if self.has_field(ServiceOrderPartModel, "quantity"):
            data["quantity"] = quantity

        if self.has_field(ServiceOrderPartModel, "unit_price"):
            data["unit_price"] = unit_price

        if self.has_field(ServiceOrderPartModel, "created_by"):
            data["created_by"] = self.admin_user

        if self.has_field(ServiceOrderPartModel, "status"):
            data["status"] = self.get_choice_value(
                ServiceOrderPartModel,
                "status",
                ["used", "reserved"],
                "used",
            )

        if self.has_field(ServiceOrderPartModel, "discount"):
            data["discount"] = Decimal("0.00")

        return ServiceOrderPartModel.objects.create(**data)

    # =========================
    # CUSTOMERS AND VEHICLES
    # =========================

    def create_customers_and_vehicles(self):
        """
        Create realistic customers and vehicles.
        """
        customers_data = [
            (
                "João Pereira",
                "(11) 98845-1200",
                "joao.pereira@example.com",
                [("Toyota", "Corolla", 2018, "Prata", "ABC1D23")],
            ),
            (
                "Maria Oliveira",
                "(21) 99714-8821",
                "maria.oliveira@example.com",
                [("Honda", "Civic", 2020, "Preto", "HJK7L89")],
            ),
            (
                "Carlos Mendes",
                "(31) 98420-7744",
                "carlos.mendes@example.com",
                [("Volkswagen", "Gol", 2015, "Branco", "MNO2P34")],
            ),
            (
                "Ana Costa",
                "(41) 99122-4410",
                "ana.costa@example.com",
                [("Chevrolet", "Onix", 2019, "Vermelho", "QRS5T67")],
            ),
            (
                "Roberto Lima",
                "(51) 98977-5533",
                "roberto.lima@example.com",
                [("Hyundai", "HB20", 2017, "Azul", "UVW8X90")],
            ),
            (
                "Fernanda Rocha",
                "(61) 99685-3301",
                "fernanda.rocha@example.com",
                [("Jeep", "Renegade", 2021, "Cinza", "YZA3B45")],
            ),
        ]

        customers = []

        for name, phone, email, vehicles in customers_data:
            customer_data = {"name": name}

            if self.has_field(Customer, "document"):
                customer_data["document"] = self.generate_unique_customer_cpf()

            if self.has_field(Customer, "phone"):
                customer_data["phone"] = phone

            if self.has_field(Customer, "email"):
                customer_data["email"] = email

            if self.has_field(Customer, "is_active"):
                customer_data["is_active"] = True

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

                if self.has_field(Vehicle, "is_active"):
                    vehicle_data["is_active"] = True

                Vehicle.objects.create(**vehicle_data)

        return customers

    # =========================
    # SERVICE TEMPLATES
    # =========================

    def get_service_templates(self):
        """
        Return controlled service templates with real part SKUs.
        """
        return [
            {
                "title": "Troca de óleo e filtros",
                "description": "Revisão preventiva básica com troca de óleo e filtros.",
                "diagnosis": "Óleo vencido e filtros com acúmulo de sujeira.",
                "solution": "Substituição do óleo, filtro de óleo e filtro de ar.",
                "parts": [
                    ("OIL-5W30", Decimal("4.00")),
                    ("FILTER-OIL-001", Decimal("1.00")),
                    ("FILTER-AIR-001", Decimal("1.00")),
                ],
                "services": [
                    (
                        "Mão de obra troca de óleo e filtros",
                        Decimal("1.00"),
                        Decimal("95.00"),
                    ),
                ],
            },
            {
                "title": "Revisão do sistema de freios",
                "description": "Cliente relatou ruído ao frear.",
                "diagnosis": "Pastilhas dianteiras desgastadas e fluido escurecido.",
                "solution": "Troca das pastilhas e substituição do fluido de freio.",
                "parts": [
                    ("BRAKE-PAD-FRONT", Decimal("1.00")),
                    ("BRAKE-FLUID-DOT4", Decimal("1.00")),
                ],
                "services": [
                    (
                        "Mão de obra revisão de freios",
                        Decimal("1.00"),
                        Decimal("170.00"),
                    ),
                ],
            },
            {
                "title": "Troca de bateria",
                "description": "Veículo com dificuldade na partida.",
                "diagnosis": "Bateria com baixa capacidade de retenção de carga.",
                "solution": "Substituição da bateria e teste do alternador.",
                "parts": [
                    ("BATTERY-60AH", Decimal("1.00")),
                ],
                "services": [
                    (
                        "Instalação da bateria e teste de carga",
                        Decimal("1.00"),
                        Decimal("75.00"),
                    ),
                ],
            },
            {
                "title": "Troca de correia dentada",
                "description": "Manutenção preventiva por quilometragem.",
                "diagnosis": "Correia dentada próxima do prazo de troca.",
                "solution": "Substituição do kit de correia, tensor e bomba d'água.",
                "parts": [
                    ("TIMING-BELT-KIT", Decimal("1.00")),
                    ("BELT-TENSIONER", Decimal("1.00")),
                    ("WATER-PUMP", Decimal("1.00")),
                ],
                "services": [
                    (
                        "Mão de obra troca de correia dentada",
                        Decimal("1.00"),
                        Decimal("390.00"),
                    ),
                ],
            },
        ]

    # =========================
    # SERVICE ORDERS
    # =========================

    def create_service_orders(self, customers, employees, parts):
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

            self.create_service_order_items(service_order, template, parts)
            service_orders.append(service_order)

        return service_orders

    def create_service_order_items(self, service_order, template, parts):
        """
        Create part and service items for a service order.
        """
        for sku, quantity in template["parts"]:
            part = self.find_part_by_sku(parts, sku)

            if part:
                self.create_part_item_from_catalog(
                    service_order=service_order,
                    part=part,
                    quantity=quantity,
                )

        service_type = self.get_choice_value(
            ServiceOrderItem,
            "item_type",
            ["service", "labor"],
            "service",
        )

        for description, quantity, unit_price in template["services"]:
            self.create_service_order_item(
                service_order=service_order,
                item_type=service_type,
                description=description,
                quantity=quantity,
                unit_price=unit_price,
                part=None,
            )

    def create_part_item_from_catalog(self, service_order, part, quantity):
        """
        Create service order item and inventory service order part from catalog.
        """
        part_type = self.get_choice_value(
            ServiceOrderItem,
            "item_type",
            ["part", "parts"],
            "part",
        )

        unit_price = getattr(
            part,
            "sale_price",
            getattr(part, "price", Decimal("0.00")),
        )

        description = getattr(part, "name", "Peça cadastrada")

        item = self.create_service_order_item(
            service_order=service_order,
            item_type=part_type,
            description=description,
            quantity=quantity,
            unit_price=unit_price,
            part=part,
        )

        self.create_inventory_service_order_part_if_possible(
            service_order=service_order,
            part=part,
            quantity=quantity,
        )

        self.create_stock_movement_if_possible(
            service_order=service_order,
            service_order_item=item,
            part=part,
            quantity=quantity,
        )

        self.decrease_part_stock_if_possible(part, quantity)

        return item

    def create_service_order_item(
        self,
        service_order,
        item_type,
        description,
        quantity,
        unit_price,
        part=None,
    ):
        """
        Create one service order item.
        """
        item_data = {}

        if self.has_field(ServiceOrderItem, "service_order"):
            item_data["service_order"] = service_order

        if self.has_field(ServiceOrderItem, "item_type"):
            item_data["item_type"] = item_type

        if self.has_field(ServiceOrderItem, "part") and part:
            item_data["part"] = part

        if self.has_field(ServiceOrderItem, "description"):
            item_data["description"] = description

        if self.has_field(ServiceOrderItem, "quantity"):
            item_data["quantity"] = quantity

        if self.has_field(ServiceOrderItem, "unit_price"):
            item_data["unit_price"] = unit_price

        return ServiceOrderItem.objects.create(**item_data)

    def create_stock_movement_if_possible(
        self,
        service_order,
        service_order_item,
        part,
        quantity,
    ):
        """
        Create stock movement record if StockMovement or PartStockMovement exists.
        """
        StockMovementModel = (
            self.get_stock_movement_model() or self.get_part_stock_movement_model()
        )

        if not StockMovementModel:
            return

        movement_data = {}

        if self.has_field(StockMovementModel, "part"):
            movement_data["part"] = part

        if self.has_field(StockMovementModel, "service_order"):
            movement_data["service_order"] = service_order

        if self.has_field(StockMovementModel, "service_order_item"):
            movement_data["service_order_item"] = service_order_item

        if self.has_field(StockMovementModel, "movement_type"):
            movement_data["movement_type"] = self.get_choice_value(
                StockMovementModel,
                "movement_type",
                ["out"],
                "out",
            )

        if self.has_field(StockMovementModel, "quantity"):
            movement_data["quantity"] = quantity

        if self.has_field(StockMovementModel, "created_by"):
            movement_data["created_by"] = self.admin_user

        if self.has_field(StockMovementModel, "reason"):
            movement_data["reason"] = "Baixa por ordem de serviço seed."

        StockMovementModel.objects.create(**movement_data)

    def decrease_part_stock_if_possible(self, part, quantity):
        """
        Decrease part stock using existing stock field.
        """
        Part = part.__class__

        stock_field = self.get_first_existing_field(
            Part,
            [
                "current_stock",
                "stock_quantity",
                "quantity",
                "stock",
                "available_quantity",
            ],
        )

        if not stock_field:
            return

        current_value = getattr(part, stock_field) or Decimal("0.00")
        new_value = current_value - quantity

        if new_value < Decimal("0.00"):
            new_value = Decimal("0.00")

        setattr(part, stock_field, new_value)

        update_fields = [stock_field]

        if self.has_field(Part, "updated_at"):
            update_fields.append("updated_at")

        part.save(update_fields=update_fields)

    # =========================
    # FINANCIAL
    # =========================

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
