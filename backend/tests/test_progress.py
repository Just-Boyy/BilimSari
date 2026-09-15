async def test_complete_lesson_unlocks_completed_status(client, auth_token):
    headers = {"Authorization": f"Bearer {auth_token}"}
    subjects = (await client.get("/api/subjects", headers=headers)).json()
    subject_id = subjects[0]["id"]
    sections = (await client.get(f"/api/subjects/{subject_id}/sections", headers=headers)).json()
    topics = (await client.get(f"/api/sections/{sections[0]['id']}/topics", headers=headers)).json()
    topic_id = topics[0]["id"]

    lesson = (await client.get(f"/api/topics/{topic_id}/lesson", headers=headers)).json()
    assert "correct_answer" not in lesson
    assert "content_html" in lesson

    complete_resp = await client.post(
        "/api/progress/complete", json={"topic_id": topic_id, "stage": "lesson"}, headers=headers
    )
    assert complete_resp.status_code == 200
    assert complete_resp.json()["is_completed"] is True

    topics_after = (await client.get(f"/api/sections/{sections[0]['id']}/topics", headers=headers)).json()
    assert topics_after[0]["status"] == "completed"
    assert topics_after[1]["status"] == "locked"
