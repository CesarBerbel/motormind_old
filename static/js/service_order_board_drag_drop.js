// This script enables drag and drop status updates on the service order board.

function getCookie(name) {
    let cookieValue = null;

    if (document.cookie && document.cookie !== "") {
        const cookies = document.cookie.split(";");

        for (let index = 0; index < cookies.length; index += 1) {
            const cookie = cookies[index].trim();

            if (cookie.substring(0, name.length + 1) === `${name}=`) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }

    return cookieValue;
}

function showDragMessage(message, type) {
    const messageContainer = document.getElementById("dragDropMessage");

    if (!messageContainer) {
        return;
    }

    messageContainer.innerHTML = `
        <div class="alert alert-${type} alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Fechar"></button>
        </div>
    `;
}

function updateServiceOrderStatus(orderId, status, updateUrl) {
    const csrfToken = getCookie("csrftoken");

    const formData = new FormData();
    formData.append("status", status);

    return fetch(updateUrl, {
        method: "POST",
        headers: {
            "X-CSRFToken": csrfToken,
            "X-Requested-With": "XMLHttpRequest"
        },
        body: formData
    }).then(function (response) {
        if (!response.ok) {
            throw new Error("Não foi possível atualizar o status.");
        }

        return response.json();
    });
}

document.addEventListener("DOMContentLoaded", function () {
    const cards = document.querySelectorAll(".service-order-card");
    const columns = document.querySelectorAll(".service-order-dropzone");

    cards.forEach(function (card) {
        card.addEventListener("dragstart", function (event) {
            event.dataTransfer.setData("text/plain", card.dataset.orderId);
            card.classList.add("opacity-50");
        });

        card.addEventListener("dragend", function () {
            card.classList.remove("opacity-50");
        });
    });

    columns.forEach(function (column) {
        column.addEventListener("dragover", function (event) {
            event.preventDefault();
            column.classList.add("border", "border-primary");
        });

        column.addEventListener("dragleave", function () {
            column.classList.remove("border", "border-primary");
        });

        column.addEventListener("drop", function (event) {
            event.preventDefault();

            column.classList.remove("border", "border-primary");

            const orderId = event.dataTransfer.getData("text/plain");
            const card = document.querySelector(`[data-order-id="${orderId}"]`);

            if (!card) {
                return;
            }

            const newStatus = column.dataset.status;
            const currentStatus = card.dataset.status;
            const updateUrl = card.dataset.updateUrl;

            if (newStatus === currentStatus) {
                return;
            }

            updateServiceOrderStatus(orderId, newStatus, updateUrl)
                .then(function (data) {
                    card.dataset.status = data.status;
                    column.appendChild(card);

                    const statusBadge = card.querySelector(".service-order-status-badge");

                    if (statusBadge) {
                        statusBadge.textContent = data.status_label;
                        statusBadge.className = "badge text-bg-secondary service-order-status-badge";
                    }

                    showDragMessage("Status atualizado com sucesso.", "success");
                })
                .catch(function () {
                    showDragMessage("Não foi possível atualizar o status da ordem.", "danger");
                });
        });
    });
});