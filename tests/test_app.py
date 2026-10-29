import pytest


def test_factory_applies_test_config(app):
    assert app.testing is True
    assert app.config["SECRET_KEY"] == "test-secret"


def test_index_redirects_anonymous_user_to_login(client):
    response = client.get("/")

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/login")


@pytest.mark.parametrize(
    "path",
    [
        "/dashboard",
        "/workspaces/create",
        "/channels/1",
        "/invitations",
        "/search",
        "/profile",
    ],
)
def test_protected_pages_redirect_anonymous_users(client, path):
    response = client.get(path)

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/login")


def test_avatar_color_filter_is_deterministic(app):
    avatar_color = app.jinja_env.filters["avatar_color"]

    assert avatar_color("Alice") == avatar_color("alice")
    assert avatar_color("") == "#e74c3c"
