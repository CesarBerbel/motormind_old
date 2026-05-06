from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Q
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, UpdateView

from core.permissions import can_access_inventory, can_manage_inventory
from inventory.forms import PartBrandForm, PartCategoryForm
from inventory.models import PartBrand, PartCategory


class InventoryAccessMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Allows users that can view inventory.
    """

    def test_func(self):
        return can_access_inventory(self.request.user)


class InventoryManageMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Allows users that can manage inventory.
    """

    def test_func(self):
        return can_manage_inventory(self.request.user)


class BrandListView(InventoryAccessMixin, ListView):
    model = PartBrand
    template_name = "inventory/brands/list.html"
    context_object_name = "brands"

    def get_queryset(self):
        search = self.request.GET.get("search", "").strip()
        status = self.request.GET.get("status", "").strip()

        queryset = PartBrand.objects.all().order_by("name")

        if search:
            queryset = queryset.filter(name__icontains=search)

        if status == "active":
            queryset = queryset.filter(is_active=True)

        if status == "inactive":
            queryset = queryset.filter(is_active=False)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["search"] = self.request.GET.get("search", "").strip()
        context["status"] = self.request.GET.get("status", "").strip()
        return context


class BrandCreateView(InventoryManageMixin, CreateView):
    model = PartBrand
    form_class = PartBrandForm
    template_name = "inventory/brands/form.html"
    success_url = reverse_lazy("inventory:brand_list")

    def get_initial(self):
        initial = super().get_initial()
        initial["is_active"] = True
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Cadastrar marca"
        context["button_text"] = "Salvar marca"
        context["back_url_name"] = "inventory:brand_list"
        return context


class BrandUpdateView(InventoryManageMixin, UpdateView):
    model = PartBrand
    form_class = PartBrandForm
    template_name = "inventory/brands/form.html"
    success_url = reverse_lazy("inventory:brand_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Editar marca"
        context["button_text"] = "Salvar alterações"
        context["back_url_name"] = "inventory:brand_list"
        return context


class CategoryListView(InventoryAccessMixin, ListView):
    model = PartCategory
    template_name = "inventory/categories/list.html"
    context_object_name = "categories"

    def get_queryset(self):
        search = self.request.GET.get("search", "").strip()
        status = self.request.GET.get("status", "").strip()

        queryset = PartCategory.objects.all().order_by("name")

        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | Q(description__icontains=search)
            )

        if status == "active":
            queryset = queryset.filter(is_active=True)

        if status == "inactive":
            queryset = queryset.filter(is_active=False)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["search"] = self.request.GET.get("search", "").strip()
        context["status"] = self.request.GET.get("status", "").strip()
        return context


class CategoryCreateView(InventoryManageMixin, CreateView):
    model = PartCategory
    form_class = PartCategoryForm
    template_name = "inventory/categories/form.html"
    success_url = reverse_lazy("inventory:category_list")

    def get_initial(self):
        initial = super().get_initial()
        initial["is_active"] = True
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Cadastrar categoria"
        context["button_text"] = "Salvar categoria"
        context["back_url_name"] = "inventory:category_list"
        return context


class CategoryUpdateView(InventoryManageMixin, UpdateView):
    model = PartCategory
    form_class = PartCategoryForm
    template_name = "inventory/categories/form.html"
    success_url = reverse_lazy("inventory:category_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Editar categoria"
        context["button_text"] = "Salvar alterações"
        context["back_url_name"] = "inventory:category_list"
        return context
