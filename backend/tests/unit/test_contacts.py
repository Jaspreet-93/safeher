import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_contacts_crud_and_verification_flow(client: AsyncClient) -> None:
    # 1. Register user
    reg_res = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "contact.user@example.com",
            "password": "StrongPassword123!",
            "full_name": "Contact User",
            "terms_consent": True,
        },
    )
    token = reg_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Add an emergency contact
    contact_payload = {
        "name": "Mom",
        "phone_number": "+919876543211",
        "relationship": "parent",
        "priority": 1,
        "location_permission": "sos_only",
    }
    create_res = await client.post("/api/v1/contacts", headers=headers, json=contact_payload)
    assert create_res.status_code == 201
    contact_data = create_res.json()
    assert contact_data["name"] == "Mom"
    assert contact_data["priority"] == 1
    assert contact_data["is_verified"] is False
    assert contact_data["verification_token"] is not None

    contact_id = contact_data["id"]
    verification_token = contact_data["verification_token"]

    # 3. List contacts
    list_res = await client.get("/api/v1/contacts", headers=headers)
    assert list_res.status_code == 200
    assert len(list_res.json()) == 1

    # 4. Verify contact consent via public token link
    verify_res = await client.post(
        f"/api/v1/contacts/verify/{verification_token}", json={"accept": True}
    )
    assert verify_res.status_code == 200
    assert verify_res.json()["is_verified"] is True

    # 5. Prevent duplicate active contact with same phone
    dup_res = await client.post("/api/v1/contacts", headers=headers, json=contact_payload)
    assert dup_res.status_code == 422
    assert "already exists" in dup_res.json()["message"]

    # 6. Delete contact
    del_res = await client.delete(f"/api/v1/contacts/{contact_id}", headers=headers)
    assert del_res.status_code == 200
    assert del_res.json()["status"] == "removed"

    # Contact list should now be empty
    list_after_res = await client.get("/api/v1/contacts", headers=headers)
    assert len(list_after_res.json()) == 0
