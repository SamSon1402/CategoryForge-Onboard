from category_forge.core.normalize import normalize_label


def test_alias_normalization():
    assert normalize_label("T-Shirts") == "t shirt"
    assert normalize_label("Tracksuit bottoms") == "pants"
