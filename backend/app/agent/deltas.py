"""Pure arithmetic deltas and multi-week trends.

Kept out of the LLM's hands so the math is always correct — the Analyst node
only reasons about what these numbers MEAN, never computes them itself. A real
analyst reads the whole trend line, not just this week vs. last week, so we also
summarize the full snapshot history deterministically.
"""
from typing import Any, Optional


def compute_deltas(current: dict[str, Any], prior: Optional[dict[str, Any]]) -> dict[str, Any]:
    def pct_change(delta: float, base: float) -> Optional[float]:
        if not base:
            return None
        return round(delta / base * 100, 2)

    posts = current.get("posts_published") or 0
    impressions = current.get("impressions") or 0
    reach_per_post = round(impressions / posts, 2) if posts else None

    result: dict[str, Any] = {
        "followers_total": current.get("followers_total"),
        "followers_new_this_period": current.get("followers_new"),
        "impressions": impressions,
        "engagements": current.get("engagements"),
        "engagement_rate": current.get("engagement_rate"),
        "posts_published": posts,
        "reach_per_post": reach_per_post,
        "follower_velocity_per_day": round((current.get("followers_new") or 0) / 7, 2),
        "has_prior_period": prior is not None,
    }

    if prior is None:
        return result

    prior_posts = prior.get("posts_published") or 0
    prior_impressions = prior.get("impressions") or 0
    prior_reach_per_post = round(prior_impressions / prior_posts, 2) if prior_posts else None

    result["followers_delta"] = (current.get("followers_total") or 0) - (prior.get("followers_total") or 0)
    result["impressions_delta"] = impressions - prior_impressions
    result["impressions_pct_change"] = pct_change(impressions - prior_impressions, prior_impressions)
    result["engagement_rate_delta"] = round(
        (current.get("engagement_rate") or 0) - (prior.get("engagement_rate") or 0), 2
    )
    result["posts_published_delta"] = posts - prior_posts
    result["reach_per_post_prior"] = prior_reach_per_post
    result["reach_per_post_delta"] = (
        round(reach_per_post - prior_reach_per_post, 2)
        if reach_per_post is not None and prior_reach_per_post is not None
        else None
    )
    return result


def _reach_per_post(s: dict[str, Any]) -> Optional[float]:
    posts = s.get("posts_published") or 0
    return round((s.get("impressions") or 0) / posts, 2) if posts else None


def _consecutive_decline(series: list[Optional[float]]) -> int:
    """How many periods in a row (ending now) the metric fell. Ignores None gaps."""
    vals = [v for v in series if v is not None]
    streak = 0
    for i in range(len(vals) - 1, 0, -1):
        if vals[i] < vals[i - 1]:
            streak += 1
        else:
            break
    return streak


def summarize_trend(snapshots: list[dict[str, Any]]) -> dict[str, Any]:
    """Compact, deterministic summary of the whole snapshot history (oldest -> newest).

    Gives the Analyst real memory of the trend line: the per-week series plus derived
    signals (consecutive weeks of decline, net follower change across the window) so it
    can distinguish a one-week blip from a sustained slide.
    """
    ordered = sorted(snapshots, key=lambda s: s.get("period_end") or "")
    series = [
        {
            "period_end": s.get("period_end"),
            "followers_total": s.get("followers_total"),
            "followers_new": s.get("followers_new"),
            "impressions": s.get("impressions"),
            "engagements": s.get("engagements"),
            "engagement_rate": s.get("engagement_rate"),
            "posts_published": s.get("posts_published"),
            "reach_per_post": _reach_per_post(s),
        }
        for s in ordered
    ]

    out: dict[str, Any] = {"weeks_of_history": len(series), "series": series}
    if len(series) >= 2:
        first, last = series[0], series[-1]
        out["net_follower_change"] = (last["followers_total"] or 0) - (first["followers_total"] or 0)
        out["engagement_rate_decline_streak"] = _consecutive_decline(
            [s["engagement_rate"] for s in series]
        )
        out["reach_per_post_decline_streak"] = _consecutive_decline(
            [s["reach_per_post"] for s in series]
        )
        out["impressions_decline_streak"] = _consecutive_decline([s["impressions"] for s in series])
    return out
