from __future__ import annotations

import base64
import json
import math
import shutil
import subprocess
import wave
from pathlib import Path

import httpx
from openai import OpenAI
from PIL import Image, ImageDraw, ImageFont

from .config import Settings


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


class MediaBuilder:
    def __init__(self, settings: Settings):
        self.settings = settings

    def generate_images(self, prompts: list[str], output_dir: Path, title: str) -> list[Path]:
        ensure_dir(output_dir)
        if self.settings.openai_api_key and not self.settings.dry_run:
            paths = self._generate_openai_images(prompts, output_dir)
            if paths:
                return paths
        return [self._placeholder_image(prompt, output_dir / f"image_{idx + 1:02d}.png", title) for idx, prompt in enumerate(prompts)]

    def _generate_openai_images(self, prompts: list[str], output_dir: Path) -> list[Path]:
        client = OpenAI(api_key=self.settings.openai_api_key)
        paths: list[Path] = []
        for idx, prompt in enumerate(prompts, start=1):
            try:
                response = client.images.generate(model=self.settings.openai_image_model, prompt=prompt, size="1024x1536")
                item = response.data[0]
                path = output_dir / f"image_{idx:02d}.png"
                if getattr(item, "b64_json", None):
                    path.write_bytes(base64.b64decode(item.b64_json))
                elif getattr(item, "url", None):
                    path.write_bytes(httpx.get(item.url, timeout=60).content)
                else:
                    continue
                paths.append(path)
            except Exception:
                continue
        return paths

    def _placeholder_image(self, prompt: str, path: Path, title: str) -> Path:
        width, height = 1080, 1920
        image = Image.new("RGB", (width, height), color=(18, 22, 33))
        draw = ImageDraw.Draw(image)
        try:
            font_title = ImageFont.truetype("DejaVuSans.ttf", 58)
            font_body = ImageFont.truetype("DejaVuSans.ttf", 34)
        except OSError:
            font_title = ImageFont.load_default()
            font_body = ImageFont.load_default()
        draw.rounded_rectangle((70, 120, width - 70, height - 120), radius=48, fill=(31, 39, 61), outline=(94, 234, 212), width=4)
        draw.text((110, 190), "AUTO CONTENT PIPELINE", font=font_body, fill=(94, 234, 212))
        for line_idx, line in enumerate(_wrap(title, 18)[:6]):
            draw.text((110, 300 + line_idx * 74), line, font=font_title, fill=(250, 250, 255))
        draw.text((110, 850), "Prompt", font=font_body, fill=(255, 210, 120))
        for line_idx, line in enumerate(_wrap(prompt, 34)[:12]):
            draw.text((110, 930 + line_idx * 50), line, font=font_body, fill=(220, 226, 240))
        draw.text((110, height - 240), "Dry-run placeholder. Set OPENAI_API_KEY for GPT Image 2.", font=font_body, fill=(170, 180, 210))
        image.save(path)
        return path

    def generate_audio(self, script: str, output_path: Path) -> Path:
        ensure_dir(output_path.parent)
        if self.settings.openai_api_key and not self.settings.dry_run:
            try:
                client = OpenAI(api_key=self.settings.openai_api_key)
                speech = client.audio.speech.create(model=self.settings.openai_tts_model, voice=self.settings.openai_tts_voice, input=script[:6000])
                speech.stream_to_file(output_path)
                return output_path
            except Exception:
                pass
        return self._fallback_wav(output_path)

    def _fallback_wav(self, output_path: Path, seconds: int = 4) -> Path:
        sample_rate = 44_100
        with wave.open(str(output_path), "w") as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(sample_rate)
            for i in range(sample_rate * seconds):
                value = int(12_000 * math.sin(2 * math.pi * 220 * i / sample_rate))
                wav.writeframesraw(value.to_bytes(2, byteorder="little", signed=True))
        return output_path

    def compose_video(self, images: list[Path], audio_path: Path, output_path: Path) -> Path:
        ensure_dir(output_path.parent)
        if not images:
            raise ValueError("At least one image is required to render video.")
        ffmpeg = shutil.which("ffmpeg")
        if not ffmpeg:
            manifest = output_path.with_suffix(".video-manifest.json")
            manifest.write_text(json.dumps({"status": "ffmpeg_missing", "images": [str(p) for p in images], "audio": str(audio_path)}, ensure_ascii=False, indent=2), encoding="utf-8")
            return manifest
        duration = max(_audio_duration_seconds(audio_path), len(images) * 3)
        per_image = max(3, duration / len(images))
        cmd: list[str] = [ffmpeg, "-y"]
        for image in images:
            cmd.extend(["-loop", "1", "-t", str(per_image), "-i", str(image)])
        cmd.extend(["-i", str(audio_path)])
        filters = []
        labels = []
        for idx in range(len(images)):
            label = f"v{idx}"
            labels.append(f"[{label}]")
            filters.append(f"[{idx}:v]scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2,setsar=1,format=yuv420p[{label}]")
        filters.append(f"{''.join(labels)}concat=n={len(images)}:v=1:a=0[v]")
        cmd.extend(["-filter_complex", ";".join(filters), "-map", "[v]", "-map", f"{len(images)}:a", "-shortest", "-r", "30", "-c:v", "libx264", "-c:a", "aac", "-movflags", "+faststart", str(output_path)])
        subprocess.run(cmd, check=True, capture_output=True)
        return output_path


def _wrap(text: str, width: int) -> list[str]:
    words = text.replace("\n", " ").split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if len(candidate) > width and current:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)
    return lines or [""]


def _audio_duration_seconds(audio_path: Path) -> float:
    if audio_path.suffix.lower() == ".wav":
        with wave.open(str(audio_path), "rb") as wav:
            return wav.getnframes() / float(wav.getframerate())
    return 30.0
