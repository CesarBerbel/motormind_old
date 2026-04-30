// This script applies a Brazilian Real money mask to inputs with class "money-input".

function onlyDigits(value) {
    return value.replace(/\D/g, "");
}

function formatToBRL(value) {
    const digits = onlyDigits(value);

    if (!digits) {
        return "";
    }

    const numericValue = Number(digits) / 100;

    return numericValue.toLocaleString("pt-BR", {
        style: "currency",
        currency: "BRL"
    });
}

function applyMoneyMask(input) {
    input.addEventListener("input", function () {
        input.value = formatToBRL(input.value);
    });

    input.addEventListener("blur", function () {
        input.value = formatToBRL(input.value);
    });
}

document.addEventListener("DOMContentLoaded", function () {
    const moneyInputs = document.querySelectorAll(".money-input");

    moneyInputs.forEach(function (input) {
        if (input.value) {
            input.value = formatToBRL(input.value);
        }

        applyMoneyMask(input);
    });
});