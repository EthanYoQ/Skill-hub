#!/usr/bin/env python3
"""
Generate images using Easyclaw Seedream 5.0 Lite via OpenAI-compatible API.

Usage:
    python generate_image.py --prompt "your image description" --filename "output.jpg" [--resolution 1K|2K|4K]

Multi-image editing (up to 14 images):
    python generate_image.py --prompt "combine these images" --filename "output.jpg" -i img1.png -i img2.png -i img3.png
"""

from __future__ import annotations

import argparse
import base64
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

from openai import OpenAI
from PIL import Image as PILImage

MODEL_NAME = "bytepluses.seedream-5.0-lite"
PLACEHOLDER_API_KEY = "easyclaw-placeholder"
MAX_INPUT_IMAGES = 14
MAX_INPUT_PIXELS = 2_560_000
SUPPORTED_OUTPUT_RESOLUTIONS = ["2K", "3K"]
SUPPORTED_ASPECT_RATIOS = [
    "1:1",
    "2:3",
    "3:2",
    "3:4",
    "4:3",
    "9:16",
    "16:9",
    "21:9",
]


class ConfigError(RuntimeError):
    """Raised when required Easyclaw configuration is missing or invalid."""


def resolve_state_dir(home_dir: Path | None = None) -> Path:
    return (home_dir or Path.home()) / ".easyclaw"


def load_json_file(path: Path) -> object:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise ConfigError(f"Missing required file: {path}") from error
    except json.JSONDecodeError as error:
        raise ConfigError(f"Invalid JSON in file: {path}") from error


def normalize_non_empty_string(value: object) -> str:
    if not isinstance(value, str):
        return ""
    return value.strip()


def normalize_base_url(value: str) -> str:
    trimmed = value.strip().rstrip("/")
    if not trimmed:
        raise ConfigError("easyclaw baseUrl must be a non-empty string")
    return trimmed


def extract_base_url_from_config(config_data: object) -> str:
    if not isinstance(config_data, dict):
        raise ConfigError("easyclaw config must be a JSON object")

    models = config_data.get("models")
    if not isinstance(models, dict):
        raise ConfigError("easyclaw config missing models.providers.easyclaw.baseUrl")

    providers = models.get("providers")
    if not isinstance(providers, dict):
        raise ConfigError("easyclaw config missing models.providers.easyclaw.baseUrl")

    easyclaw = providers.get("easyclaw")
    if not isinstance(easyclaw, dict):
        raise ConfigError("easyclaw config missing models.providers.easyclaw.baseUrl")

    base_url = normalize_non_empty_string(easyclaw.get("baseUrl"))
    if not base_url:
        raise ConfigError("easyclaw config missing models.providers.easyclaw.baseUrl")

    return normalize_base_url(base_url)


def extract_auth_from_userinfo(userinfo_data: object) -> tuple[str, str]:
    if not isinstance(userinfo_data, dict):
        raise ConfigError("easyclaw userinfo must be a JSON object")

    uid = normalize_non_empty_string(userinfo_data.get("uid"))
    token = normalize_non_empty_string(userinfo_data.get("token"))
    if not uid or not token:
        raise ConfigError("easyclaw userinfo invalid: uid/token must be non-empty strings")
    return uid, token


def load_easyclaw_runtime_config(state_dir: Path) -> tuple[str, str, str]:
    config_path = state_dir / "easyclaw.json"
    userinfo_path = state_dir / "identity" / "easyclaw-userinfo.json"
    base_url = extract_base_url_from_config(load_json_file(config_path))
    uid, token = extract_auth_from_userinfo(load_json_file(userinfo_path))
    return base_url, uid, token


def build_openai_client(base_url: str, uid: str, token: str) -> OpenAI:
    return OpenAI(
        api_key=PLACEHOLDER_API_KEY,
        base_url=normalize_base_url(base_url),
        default_headers={
            "X-Auth-Uid": uid,
            "X-Auth-Token": token,
        },
    )


def auto_detect_resolution(max_input_dim: int) -> str:
    """Return the default output resolution for Seedream 5.0 Lite."""
    return "2K"


def choose_output_resolution(
    requested_resolution: str | None,
    max_input_dim: int,
    has_input_images: bool,
) -> tuple[str, bool]:
    """Choose final resolution for Seedream 5.0 Lite."""
    if requested_resolution is not None:
        return requested_resolution, False

    return auto_detect_resolution(max_input_dim), False


def resize_image_if_needed(image: PILImage.Image) -> tuple[PILImage.Image, bool]:
    width, height = image.size
    if width * height <= MAX_INPUT_PIXELS:
        return image, False

    scale = (MAX_INPUT_PIXELS / float(width * height)) ** 0.5
    resized_width = max(1, int(width * scale))
    resized_height = max(1, int(height * scale))

    resized = image.resize((resized_width, resized_height), PILImage.Resampling.LANCZOS)
    return resized, True


def encode_image_path(image_path: str) -> tuple[str, int]:
    try:
        with PILImage.open(image_path) as image:
            copied = image.copy()
            image_format = (copied.format or "PNG").lower()
    except Exception as error:
        raise ConfigError(f"Error loading input image '{image_path}': {error}") from error

    processed_image, resized = resize_image_if_needed(copied)
    width, height = processed_image.size

    if resized:
        print(
            f"Resized input image: {image_path} -> {width}x{height} "
            f"({width * height} pixels)"
        )

    mime_type = "image/png" if image_format == "png" else f"image/{image_format}"
    from io import BytesIO

    buffer = BytesIO()
    save_format = "PNG" if image_format == "png" else (processed_image.format or image_format).upper()
    processed_image.save(buffer, format=save_format)
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:{mime_type};base64,{encoded}", max(width, height)


def build_image_request_args(args: argparse.Namespace, output_resolution: str) -> dict:
    request_args: dict[str, object] = {
        "model": MODEL_NAME,
        "prompt": args.prompt,
        "size": output_resolution,
        "output_format": "jpeg",
        "response_format": "b64_json",
    }

    extra_body: dict[str, object] = {
        "watermark": False,
        "sequential_image_generation": "disabled",
        "stream": False,
    }
    if args.aspect_ratio:
        extra_body["aspect_ratio"] = args.aspect_ratio

    if args.input_images:
        images: list[str] = []
        for image_path in args.input_images:
            encoded, _ = encode_image_path(image_path)
            images.append(encoded)
        extra_body["image"] = images[0] if len(images) == 1 else images
    request_args["extra_body"] = extra_body
    return request_args


def save_image_from_response(response: object, output_path: Path) -> bool:
    data = getattr(response, "data", None)
    if not isinstance(data, list) or not data:
        return False

    for item in data:
        image_b64 = getattr(item, "b64_json", None)
        image_url = getattr(item, "url", None)
        if isinstance(image_b64, str) and image_b64.strip():
            output_path.write_bytes(base64.b64decode(image_b64))
            return True
        if isinstance(image_url, str) and image_url.strip():
            download_file(image_url, output_path)
            return True
    return False


def download_file(url: str, output_path: Path) -> None:
    request = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=300) as response:
            output_path.write_bytes(response.read())
    except urllib.error.HTTPError as error:
        payload = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Download failed ({error.code}): {payload}") from error


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate images using Easyclaw Seedream 5.0 Lite"
    )
    parser.add_argument(
        "--prompt",
        "-p",
        required=True,
        help="Image description/prompt",
    )
    parser.add_argument(
        "--filename",
        "-f",
        required=True,
        help="Output filename (e.g., sunset-mountains.jpg)",
    )
    parser.add_argument(
        "--input-image",
        "-i",
        action="append",
        dest="input_images",
        metavar="IMAGE",
        help="Input image path(s) for editing/composition. Can be specified multiple times (up to 14 images).",
    )
    parser.add_argument(
        "--resolution",
        "-r",
        choices=SUPPORTED_OUTPUT_RESOLUTIONS,
        default=None,
        help="Output resolution: 2K or 3K. If omitted, defaults to 2K.",
    )
    parser.add_argument(
        "--aspect-ratio",
        "-a",
        choices=SUPPORTED_ASPECT_RATIOS,
        default=None,
        help=f"Output aspect ratio (default: model decides). Options: {', '.join(SUPPORTED_ASPECT_RATIOS)}",
    )

    args = parser.parse_args()

    output_path = Path(args.filename)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        state_dir = resolve_state_dir()
        base_url, uid, token = load_easyclaw_runtime_config(state_dir)
        client = build_openai_client(base_url, uid, token)

        max_input_dim = 0
        if args.input_images:
            if len(args.input_images) > MAX_INPUT_IMAGES:
                print(
                    f"Error: Too many input images ({len(args.input_images)}). Maximum is {MAX_INPUT_IMAGES}.",
                    file=sys.stderr,
                )
                return 1
            for image_path in args.input_images:
                _, current_dim = encode_image_path(image_path)
                max_input_dim = max(max_input_dim, current_dim)
                print(f"Loaded input image: {image_path}")

        output_resolution, auto_detected = choose_output_resolution(
            requested_resolution=args.resolution,
            max_input_dim=max_input_dim,
            has_input_images=bool(args.input_images),
        )
        if auto_detected:
            print(f"Auto-detected resolution: {output_resolution}")

        if args.input_images:
            img_count = len(args.input_images)
            print(
                f"Processing {img_count} image{'s' if img_count > 1 else ''} with resolution {output_resolution}..."
            )
        else:
            print(f"Generating image with resolution {output_resolution}...")

        request_args = build_image_request_args(args, output_resolution)
        response = client.images.generate(**request_args)

        if save_image_from_response(response, output_path):
            full_path = output_path.resolve()
            print(f"\nImage saved: {full_path}")
            print(f"MEDIA:{full_path}")
            return 0

        print("Error: No image was generated in the response.", file=sys.stderr)
        return 1
    except ConfigError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    except Exception as error:
        print(f"Error generating image: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
