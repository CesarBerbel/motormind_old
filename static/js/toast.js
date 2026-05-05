document.addEventListener("DOMContentLoaded", function () {
    const toasts = document.querySelectorAll(".toast-message");

    toasts.forEach((toast, index) => {
        setTimeout(() => {
            toast.classList.add("fade-out");

            setTimeout(() => {
                toast.remove();
            }, 400);

        }, 3000 + (index * 300)); // leve delay entre múltiplos
    });
});