"""Pure arithmetic deltas between this week's snapshot and the prior one.

Kept out of the LLM's hands so the math is always correct — the Analyst node
only reasons about what these numbers MEAN, never computes them itself.
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
