// Adds rows to Django inline formsets rendered with an empty_form template.
// Expected markup:
// - button[data-add-formset-row="tbody-id"]
// - tbody#tbody-id[data-prefix="formset-prefix"]
// - template#tbody-id-empty

function replaceFormsetIndex(html, prefix, index) {
    const marker = new RegExp(prefix + "-__prefix__", "g");
    return html.replace(marker, prefix + "-" + index);
}

function initializeDynamicRow(row) {
    if (typeof applyMoneyMask === "function") {
        row.querySelectorAll(".money-input").forEach(function (input) {
            applyMoneyMask(input);
        });
    }
}

function addFormsetRow(targetId) {
    const container = document.getElementById(targetId);

    if (!container) {
        return;
    }

    const prefix = container.dataset.prefix;
    const totalFormsInput = document.getElementById("id_" + prefix + "-TOTAL_FORMS");
    const emptyTemplate = document.getElementById(targetId + "-empty");

    if (!prefix || !totalFormsInput || !emptyTemplate) {
        return;
    }

    const nextIndex = Number(totalFormsInput.value);
    const html = replaceFormsetIndex(emptyTemplate.innerHTML, prefix, nextIndex);

    const wrapper = document.createElement("tbody");
    wrapper.innerHTML = html.trim();

    while (wrapper.firstElementChild) {
        const row = wrapper.firstElementChild;
        container.appendChild(row);
        initializeDynamicRow(row);
    }

    totalFormsInput.value = nextIndex + 1;
}

document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll("[data-add-formset-row]").forEach(function (button) {
        button.addEventListener("click", function () {
            addFormsetRow(button.dataset.addFormsetRow);
        });
    });
});
