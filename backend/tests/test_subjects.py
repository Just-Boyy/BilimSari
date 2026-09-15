async def test_list_subjects_returns_ten(client, auth_token):
    resp = await client.get("/api/subjects", headers={"Authorization": f"Bearer {auth_token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 10
    assert all("progress_pct" in item for item in data)


async def test_sections_and_topics_for_first_subject(client, auth_token):
    headers = {"Authorization": f"Bearer {auth_token}"}
    subjects = (await client.get("/api/subjects", headers=headers)).json()
    subject_id = subjects[0]["id"]

    sections = (await client.get(f"/api/subjects/{subject_id}/sections", headers=headers)).json()
    assert len(sections) == 1

    topics = (await client.get(f"/api/sections/{sections[0]['id']}/topics", headers=headers)).json()
    assert len(topics) == 2
    assert topics[0]["status"] == "unlocked"
    assert topics[1]["status"] == "locked"
