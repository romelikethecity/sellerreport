"""Tests for the homepage partials in templates.py."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
from templates import signup_form_hero


def test_signup_form_hero_has_form_id():
    html = signup_form_hero(form_id="hero-form", msg_id="hero-msg")
    assert 'id="hero-form"' in html
    assert 'id="hero-msg"' in html


def test_signup_form_hero_posts_to_central_worker():
    html = signup_form_hero(form_id="hero-form", msg_id="hero-msg")
    assert "newsletter-subscribe.rome-workers.workers.dev/subscribe" in html
    assert "list: 'seller-report'" in html or 'list:"seller-report"' in html


def test_signup_form_hero_has_email_input_and_submit_button():
    html = signup_form_hero(form_id="hero-form", msg_id="hero-msg")
    assert 'type="email"' in html
    assert 'type="submit"' in html or "<button" in html


def test_signup_form_hero_distinct_class_from_inline_partial():
    """Hero variant uses .hero-signup so CSS can size it bigger than .nl-signup."""
    html = signup_form_hero(form_id="hero-form", msg_id="hero-msg")
    assert "hero-signup" in html


from templates import career_map_ladder


SAMPLE_COMP = {
    "by_tier": {
        "SDR/BDR": {"n": 778, "median_base": 55000, "median_total": 75000,
                    "limited_sample": False},
        "AE - SMB": {"n": 35, "median_base": 47540, "median_total": 129400,
                     "limited_sample": False},
        "AE - Mid-Market": {"n": 1831, "median_base": 85000, "median_total": 129500,
                            "limited_sample": False},
        "AE - Enterprise": {"n": 250, "median_base": 128500, "median_total": 180000,
                            "limited_sample": False},
        "Director / Sales Manager": {"n": 2224, "median_base": 95000,
                                     "median_total": 137305, "limited_sample": False},
        "RVP": {"n": 35, "median_base": 199000, "median_total": 268125,
                "limited_sample": False},
        "VP Sales": {"n": 168, "median_base": 175300, "median_total": 247400,
                     "limited_sample": False},
        "CRO": {"n": 20, "median_base": 130700, "median_total": 151059,
                "limited_sample": False},
    },
    "career_map_years": {
        "SDR/BDR": {"median_years": 2, "n": 251},
        "AE - SMB": {"median_years": 4, "n": 13},
        "AE - Mid-Market": {"median_years": 4, "n": 601},
        "AE - Enterprise": {"median_years": 6, "n": 46},
        "Director / Sales Manager": {"median_years": 5, "n": 814},
        "RVP": {"median_years": 7, "n": 7},
        "VP Sales": {"median_years": 10, "n": 61},
        "CRO": {"median_years": 11, "n": 6},
    },
}


def test_career_ladder_has_all_8_tiers():
    html = career_map_ladder(SAMPLE_COMP)
    for tier in ["SDR/BDR", "AE - SMB", "AE - Mid-Market", "AE - Enterprise",
                 "Director / Sales Manager", "RVP", "VP Sales", "CRO"]:
        assert tier in html, f"missing tier {tier!r}"


def test_career_ladder_orders_cro_at_top():
    """Ladder reads top-down: CRO first, SDR/BDR last."""
    html = career_map_ladder(SAMPLE_COMP)
    cro_pos = html.index("CRO")
    sdr_pos = html.index("SDR/BDR")
    assert cro_pos < sdr_pos, "CRO should appear before SDR/BDR in the rendered HTML"


def test_career_ladder_renders_money_and_years():
    html = career_map_ladder(SAMPLE_COMP)
    # CRO row: $130K base, $151K total, 11 yrs
    assert "$130K" in html
    assert "$151K" in html
    assert "11 yrs" in html or "11 years" in html
    # SDR/BDR row: $55K base, 2 yrs
    assert "$55K" in html
    assert "2 yrs" in html or "2 years" in html


def test_career_ladder_renders_n_counts():
    html = career_map_ladder(SAMPLE_COMP)
    assert "n=2,224" in html or "n=2224" in html  # Director/Sales Manager comp count


def test_career_ladder_marks_limited_sample():
    """Tiers with limited_sample=True get an asterisk + footnote."""
    data = {"by_tier": {"CRO": {"n": 5, "median_base": 200000, "median_total": 300000,
                                "limited_sample": True}},
            "career_map_years": {"CRO": {"median_years": 11, "n": 3}}}
    html = career_map_ladder(data)
    assert "*" in html
    assert "Limited sample" in html or "limited sample" in html


def test_career_ladder_handles_missing_tier_gracefully():
    """If a tier has no comp data, the ladder skips that rung silently."""
    data = {"by_tier": {"CRO": {"n": 20, "median_base": 130000, "median_total": 150000,
                                "limited_sample": False}},
            "career_map_years": {"CRO": {"median_years": 11, "n": 6}}}
    html = career_map_ladder(data)
    assert "CRO" in html
    # SDR/BDR isn't in by_tier — should not appear
    assert "SDR/BDR" not in html
