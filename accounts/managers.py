from django.contrib.auth.base_user import BaseUserManager


class CustomUserManager(BaseUserManager):
    """
    Custom manager for users that authenticate with email instead of username.

    The default queryset hides users removed with soft delete. Use
    CustomUser.all_objects when an administrative recovery flow needs to see
    logically deleted users.
    """

    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True)

    # Creation policy:
    # - create_superuser creates only a pure superuser and must be used by the
    #   Django management command createsuperuser;
    # - create_user creates an internal employee by default;
    # - create_customer_user creates a customer portal user.

    def _create_user(self, email, password=None, **extra_fields):
        """
        Create and save a user with normalized email and encrypted password.
        """
        if not email:
            raise ValueError("O email é obrigatório.")

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_user(self, email, password=None, **extra_fields):
        """
        Create and save a regular internal employee user.
        """
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("is_customer", False)
        extra_fields.setdefault("is_employee", True)

        if extra_fields.get("is_superuser"):
            raise ValueError(
                "Superuser deve ser criado apenas com create_superuser/createsuperuser."
            )

        if extra_fields.get("is_customer"):
            raise ValueError("Use create_customer_user para criar usuário de cliente.")

        if not extra_fields.get("is_employee"):
            raise ValueError(
                "Usuário comum criado por create_user deve ser funcionário."
            )

        return self._create_user(email=email, password=password, **extra_fields)

    def create_customer_user(self, email, password=None, **extra_fields):
        """
        Create and save a customer portal user.
        """
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("is_customer", True)
        extra_fields.setdefault("is_employee", False)

        if extra_fields.get("is_superuser"):
            raise ValueError("Cliente não pode ser superuser.")

        if extra_fields.get("is_staff"):
            raise ValueError("Cliente não deve ter acesso ao Django Admin.")

        if not extra_fields.get("is_customer") or extra_fields.get("is_employee"):
            raise ValueError("Usuário de cliente deve ser cliente e não funcionário.")

        return self._create_user(email=email, password=password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        """
        Create and save a pure superuser.
        """
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("is_customer", False)
        extra_fields.setdefault("is_employee", False)

        if not extra_fields.get("is_staff"):
            raise ValueError("O superusuário precisa ter is_staff=True.")

        if not extra_fields.get("is_superuser"):
            raise ValueError("O superusuário precisa ter is_superuser=True.")

        if extra_fields.get("is_customer") or extra_fields.get("is_employee"):
            raise ValueError("O superusuário não pode ser cliente nem funcionário.")

        return self._create_user(email=email, password=password, **extra_fields)
