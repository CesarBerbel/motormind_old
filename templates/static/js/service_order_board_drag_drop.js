// Drag and drop for the service order board.
// This version avoids visual flickering by using dragenter/dragleave counters
// and by ignoring dragleave events fired when the pointer moves over children.

(function () {
    "use strict";

    let draggedCard = null;
    let isUpdating = false;

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

    function updateColumnCounters() {
        const columns = document.querySelectorAll(".service-order-dropzone");

        columns.forEach(function (column) {
            const status = column.dataset.status;
            const counter = document.querySelector(
                `.service-order-column-counter[data-status="${status}"]`
            );

            if (!counter) {
                return;
            }

            counter.textContent = column.querySelectorAll(".service-order-card").length;
        });
    }

    function updateEmptyColumnMessages() {
        const columns = document.querySelectorAll(".service-order-dropzone");

        columns.forEach(function (column) {
            const cards = column.querySelectorAll(".service-order-card");
            const emptyMessage = column.querySelector(".service-order-empty-message");

            if (!emptyMessage) {
                return;
            }

            if (cards.length === 0) {
                emptyMessage.classList.remove("d-none");
            } else {
                emptyMessage.classList.add("d-none");
            }
        });
    }

    function clearDropzoneState() {
        document.querySelectorAll(".service-order-dropzone").forEach(function (column) {
            column.classList.remove("is-drag-over");
            column.dataset.dragDepth = "0";
        });
    }

    function updateCardVisualStatus(card, status, statusLabel) {
        const statusBadge = card.querySelector(".service-order-status-badge");
        const statusSelect = card.querySelector('select[name="status"]');

        card.dataset.status = status;
        card.classList.add("was-updated");

        if (statusBadge) {
            statusBadge.textContent = statusLabel;
            statusBadge.className = "badge text-bg-secondary service-order-status-badge";
        }

        if (statusSelect) {
            statusSelect.value = status;
        }

        window.setTimeout(function () {
            card.classList.remove("was-updated");
        }, 800);
    }

    function updateServiceOrderStatus(status, updateUrl) {
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
            return response.json().then(function (data) {
                if (!response.ok) {
                    throw new Error(data.message || "Não foi possível atualizar o status.");
                }

                return data;
            });
        });
    }

    function setupCards() {
        document.querySelectorAll(".service-order-card").forEach(function (card) {
            card.addEventListener("dragstart", function (event) {
                if (isUpdating) {
                    event.preventDefault();
                    return;
                }

                draggedCard = card;

                event.dataTransfer.effectAllowed = "move";
                event.dataTransfer.setData("text/plain", card.dataset.orderId);

                document.body.classList.add("service-order-is-dragging");

                window.setTimeout(function () {
                    card.classList.add("is-dragging");
                }, 0);
            });

            card.addEventListener("dragend", function () {
                draggedCard = null;
                document.body.classList.remove("service-order-is-dragging");
                card.classList.remove("is-dragging");
                clearDropzoneState();
            });
        });
    }

    function setupColumns() {
        document.querySelectorAll(".service-order-dropzone").forEach(function (column) {
            column.dataset.dragDepth = "0";

            column.addEventListener("dragenter", function (event) {
                event.preventDefault();

                if (!draggedCard || isUpdating) {
                    return;
                }

                const currentDepth = Number(column.dataset.dragDepth || "0");
                column.dataset.dragDepth = String(currentDepth + 1);
                column.classList.add("is-drag-over");
            });

            column.addEventListener("dragover", function (event) {
                event.preventDefault();

                if (!draggedCard || isUpdating) {
                    event.dataTransfer.dropEffect = "none";
                    return;
                }

                event.dataTransfer.dropEffect = "move";
                column.classList.add("is-drag-over");
            });

            column.addEventListener("dragleave", function (event) {
                if (column.contains(event.relatedTarget)) {
                    return;
                }

                const currentDepth = Math.max(Number(column.dataset.dragDepth || "1") - 1, 0);
                column.dataset.dragDepth = String(currentDepth);

                if (currentDepth === 0) {
                    column.classList.remove("is-drag-over");
                }
            });

            column.addEventListener("drop", function (event) {
                event.preventDefault();
                event.stopPropagation();

                if (!draggedCard || isUpdating) {
                    clearDropzoneState();
                    return;
                }

                const card = draggedCard;
                const newStatus = column.dataset.status;
                const currentStatus = card.dataset.status;
                const updateUrl = card.dataset.updateUrl;

                clearDropzoneState();

                if (!newStatus || !updateUrl) {
                    showDragMessage("Configuração do quadro incompleta. Verifique data-status e data-update-url.", "danger");
                    return;
                }

                if (newStatus === currentStatus) {
                    return;
                }

                isUpdating = true;
                card.classList.add("is-updating");

                updateServiceOrderStatus(newStatus, updateUrl)
                    .then(function (data) {
                        const emptyMessage = column.querySelector(".service-order-empty-message");

                        if (emptyMessage) {
                            column.insertBefore(card, emptyMessage);
                        } else {
                            column.appendChild(card);
                        }

                        updateCardVisualStatus(card, data.status, data.status_label);
                        updateColumnCounters();
                        updateEmptyColumnMessages();
                        showDragMessage(data.message || "Status atualizado com sucesso.", "success");
                    })
                    .catch(function (error) {
                        updateColumnCounters();
                        updateEmptyColumnMessages();
                        showDragMessage(error.message, "danger");
                    })
                    .finally(function () {
                        isUpdating = false;
                        card.classList.remove("is-updating");
                    });
            });
        });
    }

    document.addEventListener("dragover", function (event) {
        if (draggedCard) {
            event.preventDefault();
        }
    });

    document.addEventListener("drop", function (event) {
        if (draggedCard) {
            event.preventDefault();
            clearDropzoneState();
        }
    });

    document.addEventListener("DOMContentLoaded", function () {
        setupCards();
        setupColumns();
        updateColumnCounters();
        updateEmptyColumnMessages();
    });
}());
