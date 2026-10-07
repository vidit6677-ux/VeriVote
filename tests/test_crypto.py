from services.crypto_service import (
    generate_ed25519_keypair,
    sha256_hex,
    sign_checkpoint,
    verify_checkpoint,
)


def test_sha256_is_deterministic_and_field_delimited():
    assert sha256_hex("vote", 1) == sha256_hex("vote", 1)
    assert sha256_hex("vote|1") != sha256_hex("vote", 1)


def test_ed25519_checkpoint_signature_round_trip(monkeypatch):
    private_key, public_key = generate_ed25519_keypair()
    monkeypatch.setenv("VERIVOTE_BOOTH_ED25519_PRIVATE_KEY", private_key)
    monkeypatch.setenv("VERIVOTE_BOOTH_ED25519_PUBLIC_KEY", public_key)

    signature = sign_checkpoint("BOOTH", "checkpoint-data", "demo-secret")

    assert signature.startswith("ed25519:")
    assert verify_checkpoint("BOOTH", "checkpoint-data", signature, "demo-secret")
    assert not verify_checkpoint("BOOTH", "changed-data", signature, "demo-secret")
