def test_full_vertical_slice(client, auth_headers):
    # Create an intention
    response = client.post(
        "/intentions",
        json={"title": "Start a company", "description": "Not sure where to begin"},
        headers=auth_headers,
    )
    assert response.status_code == 201
    intention = response.json()
    assert intention["status"] == "clarifying"
    intention_id = intention["id"]

    # Clarification conversation: keep sending messages until ready_to_summarize
    ready = False
    summary = None
    for turn_text in ["I want to build a software company", "Success looks like $10k MRR within a year"]:
        response = client.post(
            f"/intentions/{intention_id}/messages",
            json={"content": turn_text},
            headers=auth_headers,
        )
        assert response.status_code == 200
        body = response.json()
        assert body["assistant_message"]
        if body["ready_to_summarize"]:
            ready = True
            summary = body["summary"]

    assert ready is True
    assert summary

    history = client.get(f"/intentions/{intention_id}/messages", headers=auth_headers)
    assert history.status_code == 200
    assert len(history.json()) == 4  # 2 user + 2 assistant

    # Generate the plan
    response = client.post(f"/intentions/{intention_id}/generate-plan", headers=auth_headers)
    assert response.status_code == 200
    plan = response.json()
    assert plan["status"] == "active"
    assert plan["desired_outcome"]
    assert len(plan["milestones"]) == 2
    assert len(plan["milestones"][0]["actions"]) == 2

    # Dashboard fetch
    response = client.get(f"/intentions/{intention_id}", headers=auth_headers)
    assert response.status_code == 200
    dashboard = response.json()
    assert dashboard["desired_outcome"] == plan["desired_outcome"]

    # Next action is the highest-priority pending action
    response = client.get(f"/intentions/{intention_id}/next-action", headers=auth_headers)
    assert response.status_code == 200
    next_action = response.json()
    assert next_action["title"] == "First action"

    # Completing it advances the next action
    response = client.post(f"/actions/{next_action['id']}/complete", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["status"] == "completed"

    # Priority is global across the intention (lower = higher priority), so
    # "Third action" (priority 1, in milestone 2) outranks "Second action"
    # (priority 2, in milestone 1) once "First action" is done.
    response = client.get(f"/intentions/{intention_id}/next-action", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["title"] == "Third action"

    # Uncompleting the first action makes it the next action again, since it
    # has the same priority (1) as "Third action" but was created earlier.
    response = client.post(
        f"/actions/{next_action['id']}/uncomplete", headers=auth_headers
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "pending"
    assert body["completed_at"] is None

    response = client.get(f"/intentions/{intention_id}/next-action", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["title"] == "First action"


def test_signup_requires_unique_email(client):
    payload = {"email": "dup@example.com", "password": "supersecret123"}
    first = client.post("/auth/signup", json=payload)
    assert first.status_code == 201

    second = client.post("/auth/signup", json=payload)
    assert second.status_code == 409


def test_login_with_wrong_password_is_rejected(client):
    client.post("/auth/signup", json={"email": "user@example.com", "password": "supersecret123"})
    response = client.post("/auth/login", json={"email": "user@example.com", "password": "wrongpass"})
    assert response.status_code == 401


def test_generate_plan_before_conversation_fails(client, auth_headers):
    response = client.post(
        "/intentions",
        json={"title": "Buy a business"},
        headers=auth_headers,
    )
    intention_id = response.json()["id"]

    response = client.post(f"/intentions/{intention_id}/generate-plan", headers=auth_headers)
    assert response.status_code == 400


def test_cannot_access_another_users_intention(client, auth_headers):
    response = client.post("/intentions", json={"title": "My secret plan"}, headers=auth_headers)
    intention_id = response.json()["id"]

    other_signup = client.post(
        "/auth/signup", json={"email": "other@example.com", "password": "supersecret123"}
    )
    other_headers = {"Authorization": f"Bearer {other_signup.json()['access_token']}"}

    response = client.get(f"/intentions/{intention_id}", headers=other_headers)
    assert response.status_code == 404
