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
