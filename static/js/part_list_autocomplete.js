document.addEventListener("DOMContentLoaded", function () {
    const input = document.getElementById("part-search-input");

    if (!input) {
        return;
    }

    const form = input.closest("form");

    const dropdown = document.createElement("div");
    dropdown.className = "autocomplete-box";
    dropdown.style.position = "absolute";
    dropdown.style.background = "#fff";
    dropdown.style.border = "1px solid #d0d7de";
    dropdown.style.borderRadius = "8px";
    dropdown.style.width = input.offsetWidth + "px";
    dropdown.style.zIndex = "3000";
    dropdown.style.display = "none";
    dropdown.style.boxShadow = "0 8px 24px rgba(0,0,0,0.12)";
    dropdown.style.overflow = "hidden";

    input.parentNode.style.position = "relative";
    input.insertAdjacentElement("afterend", dropdown);

    input.addEventListener("input", function () {
        const query = input.value.trim();

        if (query.length < 2) {
            dropdown.style.display = "none";
            return;
        }

        fetch("/estoque/pecas/autocomplete/?q=" + encodeURIComponent(query))
            .then(function (response) {
                return response.json();
            })
            .then(function (data) {
                dropdown.innerHTML = "";

                if (!data.results || data.results.length === 0) {
                    dropdown.style.display = "none";
                    return;
                }

                data.results.forEach(function (item) {
                    const button = document.createElement("button");
                    button.type = "button";
                    button.className = "w-100 text-start p-2 border-0 bg-white";
                    button.innerHTML = `
                        <strong>${item.name}</strong><br>
                        <small>
                            ${item.internal_code || "Sem código"} |
                            ${item.brand_name || "Sem marca"} |
                            ${item.category_name || "Sem categoria"}
                        </small>
                    `;

                    button.addEventListener("mouseenter", function () {
                        button.style.background = "#f1f5f9";
                    });

                    button.addEventListener("mouseleave", function () {
                        button.style.background = "#fff";
                    });

                    button.addEventListener("click", function () {
                        input.value = item.name;
                        dropdown.style.display = "none";

                        const url = new URL(window.location.href);
                        url.searchParams.set("q", item.name);
                        url.searchParams.delete("page");

                        window.location.href = url.toString();
                    });

                    dropdown.appendChild(button);
                });

                dropdown.style.display = "block";
            });
    });

    window.addEventListener("resize", function () {
        dropdown.style.width = input.offsetWidth + "px";
    });

    document.addEventListener("click", function (event) {
        if (!input.contains(event.target) && !dropdown.contains(event.target)) {
            dropdown.style.display = "none";
        }
    });
});