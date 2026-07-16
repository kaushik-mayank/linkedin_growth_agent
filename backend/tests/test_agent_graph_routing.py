from app.agent.graph import _route_after_critic, _route_after_strategist


def test_recovery_week_routes_straight_to_librarian_skipping_copywriter():
    assert _route_after_strategist({"is_recovery_week": True}) == "librarian"


def test_normal_week_routes_to_copywriter():
    assert _route_after_strategist({"is_recovery_week": False}) == "copywriter"


def test_low_score_routes_back_to_copywriter_for_revision():
    state = {"critic_reviews": [{"post_code": "W01-01", "needs_revision": True}]}
    assert _route_after_critic(state) == "copywriter"


def test_all_scores_ok_routes_to_librarian():
    state = {
        "critic_reviews": [
            {"post_code": "W01-01", "needs_revision": False},
            {"post_code": "W01-02", "needs_revision": False},
        ]
    }
    assert _route_after_critic(state) == "librarian"
