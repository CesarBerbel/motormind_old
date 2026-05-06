// Preenche automaticamente o preço unitário do item do combo
// com o preço padrão do serviço selecionado.

function comboDecimalToBRL(decimalText) {
    if (!decimalText) {
        return "";
    }

    const normalized = String(decimalText).replace(".", ",");
    const numericValue = Number(String(decimalText).replace(",", "."));

    if (Number.isNaN(numericValue)) {
        return "";
    }

    return numericValue.toLocaleString("pt-BR", {
        style: "currency",
        currency: "BRL"
    });
}

function findComboRow(element) {
    return element.closest("tr.formset-row") || element.closest("tr");
}

function fillComboServicePrice(selectElement, force) {
    const selectedOption = selectElement.options[selectElement.selectedIndex];

    if (!selectedOption) {
        return;
    }

    const defaultPrice = selectedOption.dataset.defaultPrice;

    if (!defaultPrice) {
        return;
    }

    const row = findComboRow(selectElement);

    if (!row) {
        return;
    }

    const priceInput = row.querySelector('input[name$="-unit_price"]');

    if (!priceInput) {
        return;
    }

    if (!force && priceInput.value) {
        return;
    }

    priceInput.value = comboDecimalToBRL(defaultPrice);
    priceInput.dataset.autofilledFromService = "1";
}

document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll("select.combo-service-select").forEach(function (selectElement) {
        fillComboServicePrice(selectElement, false);
    });
});

document.addEventListener("change", function (event) {
    const target = event.target;

    if (target && target.matches("select.combo-service-select")) {
        fillComboServicePrice(target, true);
    }
});

document.addEventListener("input", function (event) {
    const target = event.target;

    if (target && target.matches('input[name$="-unit_price"]')) {
        target.dataset.autofilledFromService = "0";
    }
});
