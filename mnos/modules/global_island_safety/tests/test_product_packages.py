import pytest
from mnos.modules.global_island_safety.product_packages import PRODUCT_PACKAGES

def test_product_packages_load():
    assert len(PRODUCT_PACKAGES) == 9
    assert "Resort Safety Node" in PRODUCT_PACKAGES

def test_package_pricing_ranges():
    for name, pkg in PRODUCT_PACKAGES.items():
        assert "-" in pkg.setup_price_range_usd
        assert "-" in pkg.monthly_saas_range_usd

def test_no_facial_recognition_by_default():
    for name, pkg in PRODUCT_PACKAGES.items():
        for sys in pkg.included_systems:
            assert "Facial Recognition" not in sys
