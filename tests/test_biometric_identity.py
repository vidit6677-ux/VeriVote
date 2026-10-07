from services.biometric_service import is_face_match


def test_face_match_requires_the_qr_identity():

    assert is_face_match("shlok", "shlok", 50.0)
    assert not is_face_match("shlok", "vidit", 50.0)


def test_face_match_rejects_a_weak_match_even_for_the_right_identity():

    assert not is_face_match("shlok", "shlok", 100.1)
