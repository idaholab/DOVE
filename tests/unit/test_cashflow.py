# Copyright 2024, Battelle Energy Alliance, LLC
# ALL RIGHTS RESERVED
""" """

import pytest

from dove.core import Cost, Revenue


@pytest.mark.unit()
@pytest.mark.parametrize("cf_type, cf_sign", [(Cost, -1), (Revenue, 1)])
def test_defaults(cf_type, cf_sign):
    cf = cf_type(name="cf")
    assert cf.alpha == 1.0
    assert cf.dprime == 1.0
    assert cf.scalex == 1.0
    assert cf.sign == cf_sign


@pytest.mark.unit()
@pytest.mark.parametrize("cf_type, cf_sign", [(Cost, -1), (Revenue, 1)])
def test_evaluate_with_price_profile(cf_type, cf_sign):
    cf = cf_type(name="cf", price_profile=[3.0], alpha=0.5, dprime=11.0, scalex=0.5)
    assert cf.evaluate(0, 44.0) == cf_sign * 3.0  # sign * 3 * 0.5 * (44/11)**0.5 == sign * 3


@pytest.mark.unit()
@pytest.mark.parametrize("cf_type, cf_sign", [(Cost, -1), (Revenue, 1)])
def test_evaluate_without_price_profile(cf_type, cf_sign):
    cf = cf_type(name="cf", alpha=2.0, dprime=11.0, scalex=0.5)
    assert cf.evaluate(0, 44.0) == cf_sign * 4.0  # sign * 2 * (44/11)**0.5 == sign * 4


@pytest.mark.unit()
def test_evaluate_bad_timestep():
    cf = Revenue(name="cf", price_profile=[3.0])
    with pytest.raises(IndexError) as exc:
        cf.evaluate(1, 3.0)
    assert "outside of range for provided price_profile data" in str(exc.value)
