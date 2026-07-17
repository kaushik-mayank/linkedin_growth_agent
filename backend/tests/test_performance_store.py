"""Tests the learning-loop write path (sync_post_performance) with a fake Supabase client."""
from app import performance_store


class _Resp:
    def __init__(self, data):
        self.data = data


class _Query:
    """Minimal fake of the supabase-py fluent query for the calls sync_post_performance makes."""

    def __init__(self, table):
        self.table = table
        self._op = None
        self._payload = None

    def select(self, *_a, **_k):
        self._op = "select"
        return self

    def insert(self, payload):
        self._op = "insert"
        self._payload = payload
        return self

    def update(self, payload):
        self._op = "update"
        self._payload = payload
        return self

    def eq(self, *_a, **_k):
        return self

    def execute(self):
        if self._op == "select":
            return _Resp(list(self.table.rows))
        if self._op == "insert":
            row = {"id": f"id-{len(self.table.rows)}", **self._payload}
            self.table.rows.append(row)
            self.table.inserts.append(self._payload)
            return _Resp([row])
        if self._op == "update":
            self.table.updates.append(self._payload)
            return _Resp([{"id": "updated", **self._payload}])
        return _Resp([])


class _Table:
    def __init__(self):
        self.rows = []
        self.inserts = []
        self.updates = []


class _Client:
    def __init__(self, table):
        self._table = table

    def table(self, _name):
        return _Query(self._table)


def _install(monkeypatch, table):
    monkeypatch.setattr(performance_store, "get_supabase", lambda: _Client(table))


def test_sync_inserts_new_posts_and_skips_rows_without_url(monkeypatch):
    table = _Table()
    _install(monkeypatch, table)
    top_posts = [
        {"url": "https://a", "published": "2026-07-11", "impressions": 120, "engagements": 15},
        {"published": "2026-07-12", "engagements": 8},  # no url -> skipped
    ]
    saved = performance_store.sync_post_performance("proj-1", top_posts)
    assert len(saved) == 1
    assert len(table.inserts) == 1
    assert table.inserts[0]["post_url"] == "https://a"
    assert table.inserts[0]["impressions"] == 120


def test_sync_updates_existing_url_instead_of_duplicating(monkeypatch):
    table = _Table()
    table.rows.append({"id": "existing-1", "post_url": "https://a"})
    _install(monkeypatch, table)
    performance_store.sync_post_performance(
        "proj-1", [{"url": "https://a", "published": "2026-07-11", "impressions": 200, "engagements": 30}]
    )
    assert len(table.inserts) == 0
    assert len(table.updates) == 1
    assert table.updates[0]["impressions"] == 200


def test_sync_coerces_missing_metrics_to_zero(monkeypatch):
    table = _Table()
    _install(monkeypatch, table)
    performance_store.sync_post_performance("proj-1", [{"url": "https://b", "engagements": 8}])
    assert table.inserts[0]["impressions"] == 0
    assert table.inserts[0]["engagements"] == 8
