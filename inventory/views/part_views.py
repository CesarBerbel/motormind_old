from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from core.permissions import (
    can_access_inventory,
    can_manage_inventory,
    can_move_inventory_stock,
    user_passes_permission,
)
from inventory.forms import PartBrandForm, PartCategoryForm, PartForm, StockMovementForm
from inventory.models import Part, PartBrand, PartCategory
from inventory.selectors import get_critical_parts_with_priority
from inventory.services import (
    adjust_stock,
    create_stock_entry,
    create_stock_loss,
    create_stock_output,
    release_reserved_stock,
    reserve_stock,
    return_stock,
)


@login_required
@user_passes_permission(can_access_inventory)
def part_list_view(request):
    """
    List inventory parts.
    """

    # 🔥 CORREÇÃO AQUI
    search = request.GET.get("q") or request.GET.get("search", "")
    search = search.strip()

    low_stock = request.GET.get("low_stock", "").strip()
    status = request.GET.get("status", "").strip()

    parts = Part.objects.select_related("brand", "category").all().order_by("name")

    if search:
        parts = parts.filter(
            Q(name__icontains=search)
            | Q(internal_code__icontains=search)
            | Q(barcode__icontains=search)
            | Q(brand__name__icontains=search)
            | Q(category__name__icontains=search)
        )

    if status == "active":
        parts = parts.filter(is_active=True)

    if status == "inactive":
        parts = parts.filter(is_active=False)

    if low_stock == "1":
        parts = [part for part in parts if part.is_low_stock]

    return render(
        request,
        "inventory/part_list.html",
        {
            "parts": parts,
            "search": search,
            "low_stock": low_stock,
            "status": status,
        },
    )


@login_required
@user_passes_permission(can_access_inventory)
def critical_parts_view(request):
    """
    Show critical parts with restock priority.
    """
    critical_parts = get_critical_parts_with_priority()

    return render(
        request,
        "inventory/critical_parts.html",
        {
            "critical_parts": critical_parts,
            "critical_parts_count": len(critical_parts),
        },
    )


@login_required
@user_passes_permission(can_access_inventory)
def part_detail_view(request, pk):
    """
    Show inventory part detail and stock movement history.
    """
    part = get_object_or_404(
        Part,
        pk=pk,
    )

    movements = part.stock_movements.select_related(
        "created_by",
        "service_order",
    ).all()

    return render(
        request,
        "inventory/part_detail.html",
        {
            "part": part,
            "movements": movements,
        },
    )


@login_required
@user_passes_permission(can_manage_inventory)
def part_create_view(request):
    """
    Create inventory part.
    """
    if request.method == "POST":
        form = PartForm(request.POST)

        if form.is_valid():
            part = form.save()

            messages.success(
                request,
                "Peça cadastrada com sucesso.",
            )

            return redirect(
                "inventory:part_detail",
                pk=part.pk,
            )

        messages.error(
            request,
            "Não foi possível cadastrar a peça. Verifique os dados informados.",
        )

    else:
        form = PartForm()

    return render(
        request,
        "inventory/part_form.html",
        {
            "form": form,
            "page_title": "Cadastrar peça",
            "button_text": "Salvar peça",
        },
    )


@login_required
@user_passes_permission(can_manage_inventory)
def part_update_view(request, pk):
    """
    Update inventory part.
    """
    part = get_object_or_404(
        Part,
        pk=pk,
    )

    if request.method == "POST":
        form = PartForm(
            request.POST,
            instance=part,
        )

        if form.is_valid():
            updated_part = form.save()

            messages.success(
                request,
                "Peça atualizada com sucesso.",
            )

            return redirect(
                "inventory:part_detail",
                pk=updated_part.pk,
            )

        messages.error(
            request,
            "Não foi possível atualizar a peça. Verifique os dados informados.",
        )

    else:
        form = PartForm(instance=part)

    return render(
        request,
        "inventory/part_form.html",
        {
            "form": form,
            "part": part,
            "page_title": "Editar peça",
            "button_text": "Salvar alterações",
        },
    )


@login_required
@user_passes_permission(can_move_inventory_stock)
def stock_movement_create_view(request, pk):
    """
    Create stock movement for a part.
    """
    part = get_object_or_404(
        Part,
        pk=pk,
    )

    if request.method == "POST":
        form = StockMovementForm(request.POST)

        if form.is_valid():
            movement_type = form.cleaned_data["movement_type"]
            quantity = form.cleaned_data["quantity"]
            reason = form.cleaned_data["reason"]

            try:
                if movement_type == "in":
                    create_stock_entry(
                        part=part,
                        quantity=quantity,
                        created_by=request.user,
                        reason=reason,
                    )

                elif movement_type == "out":
                    create_stock_output(
                        part=part,
                        quantity=quantity,
                        created_by=request.user,
                        reason=reason,
                    )

                elif movement_type == "loss":
                    create_stock_loss(
                        part=part,
                        quantity=quantity,
                        created_by=request.user,
                        reason=reason,
                    )

                elif movement_type == "reserve":
                    reserve_stock(
                        part=part,
                        quantity=quantity,
                        created_by=request.user,
                        reason=reason,
                    )

                elif movement_type == "release":
                    release_reserved_stock(
                        part=part,
                        quantity=quantity,
                        created_by=request.user,
                        reason=reason,
                    )

                elif movement_type == "return":
                    return_stock(
                        part=part,
                        quantity=quantity,
                        created_by=request.user,
                        reason=reason,
                    )

                elif movement_type == "adjust":
                    adjust_stock(
                        part=part,
                        new_quantity=quantity,
                        created_by=request.user,
                        reason=reason,
                    )

                messages.success(
                    request,
                    "Movimentação registrada com sucesso.",
                )

                return redirect(
                    "inventory:part_detail",
                    pk=part.pk,
                )

            except ValidationError as error:
                form.add_error(
                    None,
                    error,
                )

                messages.error(
                    request,
                    "Não foi possível registrar a movimentação.",
                )

        else:
            messages.error(
                request,
                "Não foi possível registrar a movimentação. Verifique os dados informados.",
            )

    else:
        form = StockMovementForm()

    return render(
        request,
        "inventory/stock_movement_form.html",
        {
            "form": form,
            "part": part,
        },
    )


@login_required
@user_passes_permission(can_access_inventory)
def brand_list_view(request):
    """
    List part brands.
    """
    search = request.GET.get("search", "").strip()
    status = request.GET.get("status", "").strip()

    brands = PartBrand.objects.all().order_by("name")

    if search:
        brands = brands.filter(name__icontains=search)

    if status == "active":
        brands = brands.filter(is_active=True)

    if status == "inactive":
        brands = brands.filter(is_active=False)

    return render(
        request,
        "inventory/brands/list.html",
        {
            "brands": brands,
            "search": search,
            "status": status,
        },
    )


@login_required
@user_passes_permission(can_manage_inventory)
def brand_create_view(request):
    """
    Create part brand.
    """
    if request.method == "POST":
        form = PartBrandForm(request.POST)

        if form.is_valid():
            form.save()
            messages.success(request, "Marca cadastrada com sucesso.")
            return redirect("inventory:brand_list")

        messages.error(
            request,
            "Não foi possível cadastrar a marca. Verifique os dados informados.",
        )

    else:
        form = PartBrandForm(initial={"is_active": True})

    return render(
        request,
        "inventory/brands/form.html",
        {
            "form": form,
            "page_title": "Cadastrar marca",
            "button_text": "Salvar marca",
            "back_url_name": "inventory:brand_list",
        },
    )


@login_required
@user_passes_permission(can_manage_inventory)
def brand_update_view(request, pk):
    """
    Update part brand.
    """
    brand = get_object_or_404(PartBrand, pk=pk)

    if request.method == "POST":
        form = PartBrandForm(request.POST, instance=brand)

        if form.is_valid():
            form.save()
            messages.success(request, "Marca atualizada com sucesso.")
            return redirect("inventory:brand_list")

        messages.error(
            request,
            "Não foi possível atualizar a marca. Verifique os dados informados.",
        )

    else:
        form = PartBrandForm(instance=brand)

    return render(
        request,
        "inventory/brands/form.html",
        {
            "form": form,
            "brand": brand,
            "page_title": "Editar marca",
            "button_text": "Salvar alterações",
            "back_url_name": "inventory:brand_list",
        },
    )


@login_required
@user_passes_permission(can_access_inventory)
def category_list_view(request):
    """
    List part categories.
    """
    search = request.GET.get("search", "").strip()
    status = request.GET.get("status", "").strip()

    categories = PartCategory.objects.all().order_by("name")

    if search:
        categories = categories.filter(
            Q(name__icontains=search) | Q(description__icontains=search)
        )

    if status == "active":
        categories = categories.filter(is_active=True)

    if status == "inactive":
        categories = categories.filter(is_active=False)

    return render(
        request,
        "inventory/categories/list.html",
        {
            "categories": categories,
            "search": search,
            "status": status,
        },
    )


@login_required
@user_passes_permission(can_manage_inventory)
def category_create_view(request):
    """
    Create part category.
    """
    if request.method == "POST":
        form = PartCategoryForm(request.POST)

        if form.is_valid():
            form.save()
            messages.success(request, "Categoria cadastrada com sucesso.")
            return redirect("inventory:category_list")

        messages.error(
            request,
            "Não foi possível cadastrar a categoria. Verifique os dados informados.",
        )

    else:
        form = PartCategoryForm(initial={"is_active": True})

    return render(
        request,
        "inventory/categories/form.html",
        {
            "form": form,
            "page_title": "Cadastrar categoria",
            "button_text": "Salvar categoria",
            "back_url_name": "inventory:category_list",
        },
    )


@login_required
@user_passes_permission(can_manage_inventory)
def category_update_view(request, pk):
    """
    Update part category.
    """
    category = get_object_or_404(PartCategory, pk=pk)

    if request.method == "POST":
        form = PartCategoryForm(request.POST, instance=category)

        if form.is_valid():
            form.save()
            messages.success(request, "Categoria atualizada com sucesso.")
            return redirect("inventory:category_list")

        messages.error(
            request,
            "Não foi possível atualizar a categoria. Verifique os dados informados.",
        )

    else:
        form = PartCategoryForm(instance=category)

    return render(
        request,
        "inventory/categories/form.html",
        {
            "form": form,
            "category": category,
            "page_title": "Editar categoria",
            "button_text": "Salvar alterações",
            "back_url_name": "inventory:category_list",
        },
    )


def part_autocomplete(request):
    query = request.GET.get("q", "").strip()

    results = []

    if query:
        parts = (
            Part.objects.select_related("brand", "category")
            .filter(
                Q(name__icontains=query)
                | Q(internal_code__icontains=query)
                | Q(barcode__icontains=query)
            )
            .order_by("name")[:10]
        )

        for part in parts:
            results.append(
                {
                    "id": part.id,
                    "name": part.name,
                    "internal_code": part.internal_code,
                    "brand_id": part.brand_id,
                    "brand_name": part.brand.name if part.brand else "",
                    "category_id": part.category_id,
                    "category_name": part.category.name if part.category else "",
                    "sale_price": str(part.sale_price),
                    "cost_price": str(part.cost_price),
                    "unit": part.unit,
                    "location": part.location,
                }
            )

    return JsonResponse({"results": results})
