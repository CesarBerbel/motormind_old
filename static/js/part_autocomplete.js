$(document).ready(function () {

    const input = $("#id_name");

    const dropdown = $("<div class='autocomplete-box'></div>").css({
        position: "absolute",
        background: "#fff",
        border: "1px solid #ccc",
        width: input.outerWidth(),
        zIndex: 1000,
        display: "none"
    });

    input.after(dropdown);

    input.on("keyup", function () {
        const query = $(this).val();

        if (query.length < 2) {
            dropdown.hide();
            return;
        }

        $.ajax({
            url: "/estoque/pecas/autocomplete/",
            data: { q: query },
            success: function (data) {

                dropdown.empty();

                if (data.results.length === 0) {
                    dropdown.hide();
                    return;
                }

                data.results.forEach(function (item) {
                    const option = $(`
                        <div class="p-2 border-bottom autocomplete-item">
                            <strong>${item.name}</strong><br>
                            <small>${item.brand} | ${item.category}</small>
                        </div>
                    `);

                    option.on("click", function () {

                        $("#id_name").val(item.name);

                        if ($("#id_brand").length) {
                            $("#id_brand option").filter(function () {
                                return $(this).text() === item.brand;
                            }).prop("selected", true);
                        }

                        if ($("#id_category").length) {
                            $("#id_category option").filter(function () {
                                return $(this).text() === item.category;
                            }).prop("selected", true);
                        }

                        if ($("#id_sale_price").length) {
                            $("#id_sale_price").val(item.sale_price);
                        }

                        if ($("#id_cost_price").length) {
                            $("#id_cost_price").val(item.cost_price);
                        }

                        dropdown.hide();
                    });

                    dropdown.append(option);
                });

                dropdown.show();
            }
        });
    });

    $(document).click(function (e) {
        if (!$(e.target).closest("#id_name").length) {
            dropdown.hide();
        }
    });
});