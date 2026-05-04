import pytest
from django.urls import resolve, reverse

from mensagens import views


@pytest.mark.parametrize(
    ("route_name", "view_func"),
    [
        ("dashboard", views.dashboard),
        ("template_list", views.template_list),
        ("template_create", views.template_create),
        ("variable_help", views.variable_help),
        ("manual_message_create", views.manual_message_create),
        ("queue_list", views.queue_list),
        ("log_list", views.log_list),
    ],
)
def test_static_urls_resolve_to_expected_views(route_name, view_func):
    match = resolve(reverse(f"mensagens:{route_name}"))

    assert match.func == view_func


def test_template_update_url_resolves_to_expected_view():
    match = resolve(reverse("mensagens:template_update", kwargs={"pk": 123}))

    assert match.func == views.template_update
    assert match.kwargs["pk"] == 123


def test_queue_process_url_resolves_to_expected_view():
    match = resolve(reverse("mensagens:queue_process", kwargs={"pk": 456}))

    assert match.func == views.queue_process
    assert match.kwargs["pk"] == 456
