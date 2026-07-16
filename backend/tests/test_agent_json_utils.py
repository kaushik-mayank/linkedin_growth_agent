import pytest

from app.agent.json_utils import JSONParseError, parse_json_with_repair, try_parse


def test_try_parse_handles_plain_json():
    assert try_parse('{"a": 1}') == {"a": 1}


def test_try_parse_strips_markdown_fences():
    raw = '```json\n{"a": 1, "b": [1, 2]}\n```'
    assert try_parse(raw) == {"a": 1, "b": [1, 2]}


def test_try_parse_extracts_outer_json_from_surrounding_commentary():
    raw = 'Sure, here is the JSON:\n{"a": 1}\nHope that helps!'
    assert try_parse(raw) == {"a": 1}


def test_try_parse_returns_none_for_garbage():
    assert try_parse("not json at all") is None


@pytest.mark.asyncio
async def test_parse_json_with_repair_returns_immediately_on_valid_json():
    async def generate_should_not_be_called(prompt, system=None):
        raise AssertionError("repair should not be called when the first parse succeeds")

    result = await parse_json_with_repair(
        '{"ok": true}', generate_should_not_be_called, expected_shape="{}"
    )
    assert result == {"ok": True}


@pytest.mark.asyncio
async def test_parse_json_with_repair_retries_once_and_succeeds():
    async def fake_generate(prompt, system=None):
        return '{"fixed": true}'

    result = await parse_json_with_repair("this is broken {not json", fake_generate, expected_shape="{}")
    assert result == {"fixed": True}


@pytest.mark.asyncio
async def test_parse_json_with_repair_raises_after_failed_repair():
    async def fake_generate(prompt, system=None):
        return "still not valid json"

    with pytest.raises(JSONParseError):
        await parse_json_with_repair("broken {", fake_generate, expected_shape="{}")
