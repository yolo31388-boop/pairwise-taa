import pytest

from render.taa import (
    halton,
    jitter_offset,
    clamp_history,
    disocclusion_mask,
    resolve
)


def test_halton_first_base2():
    assert halton(1, 2) == pytest.approx(0.5)

def test_halton_second_base2():
    assert halton(2, 2) == pytest.approx(0.25)

def test_halton_first_base3():
    assert halton(1, 3) == pytest.approx(1.0 / 3.0)

def test_jitter_frame0():
    assert jitter_offset(0, 1920, 1080) == pytest.approx((0.0, -0.000154321))

def test_jitter_frame1():
    assert jitter_offset(1, 1920, 1080) == pytest.approx((-0.000130208, 0.000154321))

def test_jitter_odd_size():
    assert jitter_offset(2, 101, 37) == pytest.approx((0.002475248, -0.010510511))

def test_clamp_inside():
    assert clamp_history((0.5, 0.5, 0.5), (0.0, 0.0, 0.0), (1.0, 1.0, 1.0)) == (0.5, 0.5, 0.5)

def test_clamp_high_low():
    assert clamp_history((2.0, -1.0, 0.5), (0.0, 0.0, 0.0), (1.0, 1.0, 1.0)) == (1.0, 0.0, 0.5)

def test_clamp_upper_range():
    assert clamp_history((1.2, 0.4, 0.9), (0.0, 0.0, 0.0), (2.0, 2.0, 2.0)) == (1.2, 0.4, 0.9)

def test_disocc_stable():
    assert disocclusion_mask([1.0, 2.0], [1.0, 1.005], [(0.0, 0.0, 1.0), (0.0, 0.0, 1.0)], [(0.0, 0.0, 1.0), (0.0, 0.0, 1.0)]) == [False, False]

def test_disocc_depth_change():
    assert disocclusion_mask([1.0, 2.0], [1.0, 1.8], [(0.0, 0.0, 1.0), (0.0, 0.0, 1.0)], [(0.0, 0.0, 1.0), (0.0, 0.0, 1.0)]) == [False, True]

def test_disocc_normal_change():
    assert disocclusion_mask([1.0, 2.0], [1.0, 2.0], [(0.0, 0.0, 1.0), (1.0, 0.0, 0.0)], [(0.0, 0.0, 1.0), (0.0, 0.0, 1.0)]) == [False, True]

def test_resolve_disocc_uses_current():
    assert resolve((1.0, 0.0, 0.0), (0.0, 0.0, 0.0), [True], 0.1) == (1.0, 0.0, 0.0)

def test_resolve_blend():
    assert resolve((1.0, 0.0, 0.0), (0.0, 0.0, 0.0), [False], 0.1) == pytest.approx((0.1, 0.0, 0.0))

def test_resolve_alpha_zero():
    assert resolve((1.0, 0.0, 0.0), (0.0, 0.0, 0.0), [False], 0.0) == (0.0, 0.0, 0.0)
