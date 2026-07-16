from app.agent.deltas import compute_deltas


def test_cold_start_has_no_deltas():
    current = {
        "followers_total": 1162, "followers_new": 12, "impressions": 0,
        "engagements": 0, "engagement_rate": 0.0, "posts_published": 0,
    }
    result = compute_deltas(current, None)
    assert result["has_prior_period"] is False
    assert "followers_delta" not in result
    assert result["reach_per_post"] is None


def test_detects_growth_between_periods():
    current = {
        "followers_total": 1300, "followers_new": 138, "impressions": 5000,
        "engagements": 250, "engagement_rate": 5.0, "posts_published": 4,
    }
    prior = {
        "followers_total": 1162, "followers_new": 12, "impressions": 2000,
        "engagements": 60, "engagement_rate": 3.0, "posts_published": 3,
    }
    result = compute_deltas(current, prior)
    assert result["has_prior_period"] is True
    assert result["followers_delta"] == 138
    assert result["impressions_delta"] == 3000
    assert result["engagement_rate_delta"] == 2.0
    assert result["posts_published_delta"] == 1


def test_detects_audience_fatigue_signal_reach_per_post_falling_while_volume_rises():
    current = {
        "followers_total": 1400, "followers_new": 20, "impressions": 3000,
        "engagements": 90, "engagement_rate": 3.0, "posts_published": 6,
    }
    prior = {
        "followers_total": 1380, "followers_new": 30, "impressions": 4000,
        "engagements": 200, "engagement_rate": 5.0, "posts_published": 3,
    }
    result = compute_deltas(current, prior)
    # posts went up (3 -> 6) but reach per post collapsed (1333 -> 500) — classic fatigue signal
    assert result["posts_published_delta"] > 0
    assert result["reach_per_post_delta"] < 0


def test_zero_posts_gives_null_reach_per_post_not_a_crash():
    current = {
        "followers_total": 1162, "followers_new": 12, "impressions": 0,
        "engagements": 0, "engagement_rate": 0.0, "posts_published": 0,
    }
    prior = {
        "followers_total": 1150, "followers_new": 5, "impressions": 100,
        "engagements": 5, "engagement_rate": 5.0, "posts_published": 1,
    }
    result = compute_deltas(current, prior)
    assert result["reach_per_post"] is None
    assert result["reach_per_post_prior"] == 100.0
