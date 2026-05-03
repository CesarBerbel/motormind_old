from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from core.permissions import (
    can_access_inventory,
    can_manage_inventory,
    can_move_inventory_stock,
    user_passes_permission,
)
from inventory.forms import PartForm, StockMovementForm
from inventory.models import Part
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
    search = request.GET.get("search", "").strip()
    low_stock = request.GET.get("low_stock", "").strip()
    status = request.GET.get("status", "").strip()

    parts = Part.objects.all().order_by("name")

    if search:
        parts = parts.filter(
            Q(name__icontains=search)
            | Q(internal_code__icontains=search)
            | Q(barcode__icontains=search)
            | Q(brand__icontains=search)
            | Q(category__icontains=search)
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
