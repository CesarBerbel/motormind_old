from django.apps import AppConfig


class InventoryConfig(AppConfig):
    """
    App configuration for inventory.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "inventory"
    verbose_name = "Estoque"
