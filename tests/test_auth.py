from werkzeug.security import generate_password_hash

import routes.auth as auth_routes


class FakeCursor:
    def __init__(self, rows):
        self._rows = iter(rows)
        self.closed = False
        self.executed = []

    def execute(self, query, params=None):
        self.executed.append((query, params))

    def fetchone(self):
        return next(self._rows, None)

    def close(self):
        self.closed = True


class FakeConnection:
    def __init__(self):
        self.closed = False

    def close(self):
        self.closed = True


def test_login_requires_both_credentials(client):
    response = client.post("/login", data={"username": "", "password": ""})

    assert response.status_code == 200
    assert b"Username and password are required." in response.data


def test_registration_validation_does_not_query_database(client, monkeypatch):
    def fail_if_called():
        raise AssertionError("invalid form should not open a database connection")

    monkeypatch.setattr(auth_routes, "get_connection", fail_if_called)

    response = client.post(
        "/register",
        data={
            "email": "invalid",
            "username": "ab",
            "password": "short",
            "confirm_password": "different",
        },
    )

    assert response.status_code == 200
    assert b"A valid email address is required." in response.data
    assert b"Username must be at least 3 characters." in response.data
    assert b"Password must be at least 6 characters." in response.data
    assert b"Passwords do not match." in response.data


def test_successful_login_sets_session_and_closes_resources(client, monkeypatch):
    cursor = FakeCursor(
        [
            {
                "user_id": 7,
                "username": "kavish",
                "email": "kavish@example.com",
                "nickname": "Kavish",
                "password": generate_password_hash("correct-password"),
            }
        ]
    )
    connection = FakeConnection()
    monkeypatch.setattr(auth_routes, "get_connection", lambda: connection)
    monkeypatch.setattr(auth_routes, "dict_cursor", lambda conn: cursor)

    response = client.post(
        "/login",
        data={"username": "kavish", "password": "correct-password"},
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/dashboard")
    with client.session_transaction() as session:
        assert session["user_id"] == 7
        assert session["username"] == "kavish"
    assert cursor.closed is True
    assert connection.closed is True


def test_login_rejects_external_next_url(client, monkeypatch):
    cursor = FakeCursor(
        [
            {
                "user_id": 7,
                "username": "kavish",
                "email": "kavish@example.com",
                "nickname": None,
                "password": generate_password_hash("correct-password"),
            }
        ]
    )
    monkeypatch.setattr(auth_routes, "get_connection", FakeConnection)
    monkeypatch.setattr(auth_routes, "dict_cursor", lambda conn: cursor)

    response = client.post(
        "/login?next=https://example.com/phishing",
        data={"username": "kavish", "password": "correct-password"},
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/dashboard")
