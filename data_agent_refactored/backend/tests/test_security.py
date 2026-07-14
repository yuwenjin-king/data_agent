"""Security tests: ModelConfig secrets are encrypted at rest, decrypted on use,
masked in responses; maybe_decrypt tolerates legacy plaintext."""
from app.models.chat import ModelConfig
from app.schemas.chat import ModelConfigCreate
from app.services.chat_service import model_config_crud
from app.utils.crypto import encrypt, maybe_decrypt


def test_maybe_decrypt_tolerant_of_plaintext():
    # Legacy plaintext / test fixtures must pass through unchanged.
    assert maybe_decrypt("not-a-fernet-token") == "not-a-fernet-token"
    assert maybe_decrypt("sk-plain") == "sk-plain"
    assert maybe_decrypt("") == ""
    assert maybe_decrypt(None) is None
    # Real encrypted values round-trip.
    assert maybe_decrypt(encrypt("secret")) == "secret"


def test_model_config_api_key_encrypted_at_rest(db_session):
    config = model_config_crud.create(
        db_session,
        obj_in=ModelConfigCreate(
            provider="openai",
            base_url="https://api.openai.com/v1",
            api_key="sk-secret-1234567890",
            model_name="gpt-4o",
            model_type="CHAT",
        ),
    )
    raw = db_session.get(ModelConfig, config.id)
    # The persisted value must NOT be the plaintext key.
    assert raw.api_key != "sk-secret-1234567890"
    # And it must decrypt back to the plaintext for use.
    assert maybe_decrypt(raw.api_key) == "sk-secret-1234567890"


def test_model_config_proxy_password_encrypted_at_rest(db_session):
    config = model_config_crud.create(
        db_session,
        obj_in=ModelConfigCreate(
            provider="openai",
            base_url="https://api.openai.com/v1",
            api_key="sk-key",
            model_name="gpt-4o",
            model_type="CHAT",
            proxy_enabled=True,
            proxy_host="proxy.local",
            proxy_port=8080,
            proxy_username="user",
            proxy_password="proxy-secret-pw",
        ),
    )
    raw = db_session.get(ModelConfig, config.id)
    assert raw.proxy_password != "proxy-secret-pw"
    assert maybe_decrypt(raw.proxy_password) == "proxy-secret-pw"


def test_model_config_response_masks_api_key(client):
    create_resp = client.post(
        "/api/v1/chat/model-configs",
        json={
            "provider": "openai",
            "base_url": "https://api.openai.com/v1",
            "api_key": "sk-secret-1234567890",
            "model_name": "gpt-4o",
            "model_type": "CHAT",
        },
    )
    assert create_resp.status_code == 200
    create_body = create_resp.json()["data"]
    # The raw key must never appear in any response.
    assert create_body["api_key"] != "sk-secret-1234567890"
    assert create_body["api_key"].startswith("****")
    assert "secret" not in create_body["api_key"]

    list_resp = client.get("/api/v1/chat/model-configs")
    listed = list_resp.json()["data"][0]
    assert listed["api_key"].startswith("****")
    assert listed["api_key"] != "sk-secret-1234567890"


def test_model_config_update_re_encrypts_api_key(db_session):
    config = model_config_crud.create(
        db_session,
        obj_in=ModelConfigCreate(
            provider="openai",
            base_url="https://api.openai.com/v1",
            api_key="sk-original-key-1234",
            model_name="gpt-4o",
            model_type="CHAT",
        ),
    )
    first_cipher = db_session.get(ModelConfig, config.id).api_key

    from app.schemas.chat import ModelConfigUpdate

    model_config_crud.update(
        db_session,
        db_obj=config,
        obj_in=ModelConfigUpdate(api_key="sk-rotated-key-5678"),
    )
    second_cipher = db_session.get(ModelConfig, config.id).api_key
    # Cipher changes on rotation and decrypts to the new key.
    assert second_cipher != first_cipher
    assert maybe_decrypt(second_cipher) == "sk-rotated-key-5678"
