import routes.workspaces as workspace_routes


class FakeCursor:
    def __init__(self):
        self.results = iter([{"workspace_id": 11}, {"channel_id": 22}])
        self.executed = []
        self.closed = False

    def execute(self, query, params=None):
        self.executed.append((query, params))

    def fetchone(self):
        return next(self.results)

    def close(self):
        self.closed = True


class FakeConnection:
    def __init__(self):
        self.committed = False
        self.rolled_back = False
        self.closed = False

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True

    def close(self):
        self.closed = True


def test_create_workspace_commits_workspace_channel_and_memberships(
    client, monkeypatch
):
    cursor = FakeCursor()
    connection = FakeConnection()
    monkeypatch.setattr(workspace_routes, "get_connection", lambda: connection)
    monkeypatch.setattr(workspace_routes, "dict_cursor", lambda conn: cursor)
    with client.session_transaction() as session:
        session["user_id"] = 7
        session["username"] = "kavish"

    response = client.post(
        "/workspaces/create",
        data={"name": "Study Group", "description": "Coursework"},
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/workspaces/11")
    assert connection.committed is True
    assert connection.rolled_back is False
    assert connection.closed is True
    assert cursor.closed is True
    statements = " ".join(query for query, _ in cursor.executed)
    assert "INSERT INTO Workspace " in statements
    assert "INSERT INTO WorkspaceMembership " in statements
    assert "INSERT INTO WorkspaceAdmin " in statements
    assert "INSERT INTO Channel " in statements
    assert "INSERT INTO ChannelMembership " in statements
