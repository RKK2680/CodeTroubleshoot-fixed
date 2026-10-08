import io

from fastapi.testclient import TestClient
from PIL import Image

from app.main import app
from app.preprocessing.image_ops import preprocess_image, resize_image
import numpy as np


def png_bytes(width=80, height=40):
    image = Image.new("RGB", (width, height), "white")
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def jpeg_bytes():
    image = Image.new("RGB", (80, 40), "white")
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG")
    return buffer.getvalue()


def test_homepage():
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    assert "Process" in response.text
    assert "Copy text" in response.text
    assert "Download text" in response.text


def test_recognize_png(monkeypatch, tmp_path):
    monkeypatch.setenv("RESULT_DIR", str(tmp_path))
    monkeypatch.setattr(
        "app.recognition.ocr.pytesseract.image_to_string",
        lambda image, lang="eng", config="": "Hello",
    )
    client = TestClient(app)
    response = client.post(
        "/api/recognize",
        files={"file": ("note.png", png_bytes(), "image/png")},
    )
    assert response.status_code == 200
    body = response.json()
    assert isinstance(body["text"], str)
    assert isinstance(body["processing_ms"], (int, float))
    assert body["filename"] == "note.png"


def test_recognize_jpeg(monkeypatch, tmp_path):
    monkeypatch.setenv("RESULT_DIR", str(tmp_path))
    monkeypatch.setattr(
        "app.recognition.ocr.pytesseract.image_to_string",
        lambda image, lang="eng", config="": "Hello",
    )
    client = TestClient(app)
    response = client.post(
        "/api/recognize",
        files={"file": ("scan.jpg", jpeg_bytes(), "image/jpeg")},
    )
    assert response.status_code == 200
    assert isinstance(response.json()["text"], str)


def test_missing_file():
    client = TestClient(app)
    response = client.post("/api/recognize")
    assert response.status_code == 422


def test_rejects_pdf():
    client = TestClient(app)
    response = client.post(
        "/api/recognize",
        files={"file": ("notes.pdf", b"%PDF-1.4", "application/pdf")},
    )
    assert response.status_code == 400


def test_rejects_png_with_wrong_content():
    client = TestClient(app)
    response = client.post(
        "/api/recognize",
        files={"file": ("note.png", b"not-an-image", "image/png")},
    )
    assert response.status_code == 400


def test_rejects_oversized_image():
    client = TestClient(app)
    payload = png_bytes() + b"0" * (5 * 1024 * 1024)
    response = client.post(
        "/api/recognize",
        files={"file": ("large.png", payload, "image/png")},
    )
    assert response.status_code == 400


def test_rejects_path_filename(monkeypatch, tmp_path):
    monkeypatch.setenv("RESULT_DIR", str(tmp_path))
    client = TestClient(app)
    response = client.post(
        "/api/recognize",
        files={"file": ("../../secret.png", png_bytes(), "image/png")},
    )
    assert response.status_code == 400


def test_resize_keeps_aspect_ratio():
    tall = np.full((1200, 480, 3), 255, dtype=np.uint8)
    out = resize_image(tall)
    h, w = out.shape[:2]
    assert h <= 600 and w <= 800
    assert abs(w / h - 480 / 1200) < 0.01


def test_resize_does_not_upscale_small_images():
    small = np.full((40, 80, 3), 255, dtype=np.uint8)
    assert resize_image(small).shape[:2] == (40, 80)


def test_preprocess_gives_dark_text_on_white():
    image = np.full((60, 200, 3), 255, dtype=np.uint8)
    image[20:40, 50:150] = 0
    out = preprocess_image(image)
    assert out[0, 0] == 255 and out[30, 100] == 0


def test_download_returns_text(monkeypatch, tmp_path):
    monkeypatch.setenv("RESULT_DIR", str(tmp_path))
    monkeypatch.setattr(
        "app.recognition.ocr.pytesseract.image_to_string",
        lambda image, lang="eng", config="": "Hello world",
    )
    client = TestClient(app)
    body = client.post(
        "/api/recognize", files={"file": ("note.png", png_bytes(), "image/png")}
    ).json()
    response = client.get(f"/api/results/{body['id']}/download")
    assert response.status_code == 200
    assert response.text == "Hello world"
    again = client.get(f"/api/results/{body['id']}/download")
    assert again.text == "Hello world"
