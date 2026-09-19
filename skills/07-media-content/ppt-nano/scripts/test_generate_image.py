import importlib.util
from pathlib import Path

import pytest

MODULE_PATH = Path(__file__).with_name("generate_image.py")
SPEC = importlib.util.spec_from_file_location("generate_image", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


@pytest.mark.parametrize(
    ("max_input_dim", "expected"),
    [
        (0, "2K"),
        (1499, "2K"),
        (1500, "2K"),
        (2999, "2K"),
        (3000, "2K"),
    ],
)
def test_auto_detect_resolution_defaults_to_2k(max_input_dim, expected):
    assert MODULE.auto_detect_resolution(max_input_dim) == expected


@pytest.mark.parametrize(
    ("requested_resolution", "max_input_dim", "has_input_images", "expected"),
    [
        (None, 2200, True, ("2K", False)),
        (None, 0, False, ("2K", False)),
        ("2K", 3500, True, ("2K", False)),
        ("3K", 3500, True, ("3K", False)),
    ],
)
def test_choose_output_resolution_table(
    requested_resolution,
    max_input_dim,
    has_input_images,
    expected,
):
    assert (
        MODULE.choose_output_resolution(
            requested_resolution,
            max_input_dim,
            has_input_images,
        )
        == expected
    )


@pytest.mark.parametrize(
    ("home", "expected"),
    [
        (Path("C:/Users/alice"), Path("C:/Users/alice/.easyclaw")),
        (Path("/Users/alice"), Path("/Users/alice/.easyclaw")),
        (Path("/home/alice"), Path("/home/alice/.easyclaw")),
    ],
)
def test_resolve_state_dir_uses_easyclaw_hidden_folder(home, expected):
    assert MODULE.resolve_state_dir(home_dir=home) == expected


@pytest.mark.parametrize(
    ("raw_base_url", "expected"),
    [
        ("https://aibot-srv.easyclaw.com", "https://aibot-srv.easyclaw.com"),
        ("https://aibot-srv.easyclaw.cn/v1", "https://aibot-srv.easyclaw.cn/v1"),
        (" https://aibot-srv.easyclaw.com/ ", "https://aibot-srv.easyclaw.com"),
    ],
)
def test_normalize_base_url_trims_without_forcing_v1(raw_base_url, expected):
    assert MODULE.normalize_base_url(raw_base_url) == expected


@pytest.mark.parametrize(
    ("config_data", "expected"),
    [
        (
            {"models": {"providers": {"easyclaw": {"baseUrl": "https://aibot-srv.easyclaw.com"}}}},
            "https://aibot-srv.easyclaw.com",
        ),
    ],
)
def test_extract_base_url_from_config_table(config_data, expected):
    assert MODULE.extract_base_url_from_config(config_data) == expected


@pytest.mark.parametrize(
    "config_data",
    [
        {},
        {"models": {}},
        {"models": {"providers": {}}},
        {"models": {"providers": {"easyclaw": {}}}},
        {"models": {"providers": {"easyclaw": {"baseUrl": "   "}}}},
    ],
)
def test_extract_base_url_from_config_rejects_missing_or_blank(config_data):
    with pytest.raises(MODULE.ConfigError):
        MODULE.extract_base_url_from_config(config_data)


@pytest.mark.parametrize(
    ("userinfo_data", "expected"),
    [
        ({"uid": "uid-123", "token": "token-456"}, ("uid-123", "token-456")),
        ({"uid": " uid-123 ", "token": " token-456 "}, ("uid-123", "token-456")),
    ],
)
def test_extract_auth_from_userinfo_table(userinfo_data, expected):
    assert MODULE.extract_auth_from_userinfo(userinfo_data) == expected


@pytest.mark.parametrize(
    "userinfo_data",
    [
        {},
        {"uid": "uid-only"},
        {"token": "token-only"},
        {"uid": "", "token": "token"},
        {"uid": "uid", "token": "   "},
    ],
)
def test_extract_auth_from_userinfo_rejects_invalid_payload(userinfo_data):
    with pytest.raises(MODULE.ConfigError):
        MODULE.extract_auth_from_userinfo(userinfo_data)


@pytest.mark.parametrize(
    ("width", "height", "expect_resized", "expected_size"),
    [
        (1600, 1599, False, (1600, 1599)),
        (1600, 1600, False, (1600, 1600)),
        (4000, 2000, True, (2262, 1131)),
        (2000, 4000, True, (1131, 2262)),
    ],
)
def test_resize_image_if_needed_table(width, height, expect_resized, expected_size):
    image = MODULE.PILImage.new("RGB", (width, height), (255, 0, 0))

    resized, did_resize = MODULE.resize_image_if_needed(image)

    assert did_resize is expect_resized
    assert resized.size == expected_size
    assert resized.size[0] * resized.size[1] <= MODULE.MAX_INPUT_PIXELS


def test_build_openai_client_uses_placeholder_key_and_easyclaw_headers(monkeypatch):
    captured = {}

    class FakeOpenAI:
        def __init__(self, **kwargs):
            captured.update(kwargs)

    monkeypatch.setattr(MODULE, "OpenAI", FakeOpenAI)

    MODULE.build_openai_client(
        base_url="https://aibot-srv.easyclaw.com",
        uid="uid-abc",
        token="token-def",
    )

    assert captured["api_key"] == MODULE.PLACEHOLDER_API_KEY
    assert captured["base_url"] == "https://aibot-srv.easyclaw.com"
    assert captured["default_headers"] == {
        "X-Auth-Uid": "uid-abc",
        "X-Auth-Token": "token-def",
    }
