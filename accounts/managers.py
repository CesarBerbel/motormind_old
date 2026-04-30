from django.contrib.auth.base_user import BaseUserManager


class CustomUserManager(BaseUserManager):
    """
    Custom manager for users that authenticate with email instead of username.
    """

    def create_user(self, email, password=None, **extra_fields):
        """
        Create and save a regular user with email and password.
        """
        if not email:
            raise ValueError("O email é obrigatório.")

        email = self.normalize_email(email)

        user = self.model(email=email, **extra_fields)

        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """
        Create and save a superuser with email and password.
        """
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if not extra_fields.get("is_staff"):
            raise ValueError("O superusuário precisa ter is_staff=True.")

        if not extra_fields.get("is_superuser"):
            raise ValueError("O superusuário precisa ter is_superuser=True.")

        return self.create_user(email=email, password=password, **extra_fields)
