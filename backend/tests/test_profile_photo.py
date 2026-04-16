"""Tests for profile photo upload, replace, and delete."""

import io
import os

import pytest


class TestProfilePhoto:
    """Profile photo upload lifecycle tests."""

    def _register_and_token(self, client, email="photo@example.com") -> str:
        resp = client.post("/auth/register", json={
            "email": email,
            "password": "Secure@pass1",
            "display_name": "Photo User",
        })
        return resp.json()["access_token"]

    def _auth_header(self, token: str) -> dict:
        return {"Authorization": f"Bearer {token}"}

    def _make_png(self, size: int = 100) -> io.BytesIO:
        """Create a minimal valid PNG file."""
        # Minimal 1x1 PNG
        import struct
        import zlib

        def _chunk(chunk_type: bytes, data: bytes) -> bytes:
            c = chunk_type + data
            return struct.pack(">I", len(data)) + c + struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)

        sig = b"\x89PNG\r\n\x1a\n"
        ihdr = _chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0))
        raw = zlib.compress(b"\x00\x00\x00\x00")
        idat = _chunk(b"IDAT", raw)
        iend = _chunk(b"IEND", b"")
        return io.BytesIO(sig + ihdr + idat + iend)

    def test_upload_photo_success(self, client, tmp_path, monkeypatch):
        monkeypatch.setattr("app.config.settings.upload_dir", str(tmp_path / "uploads"))
        token = self._register_and_token(client)

        png = self._make_png()
        resp = client.post(
            "/auth/profile-photo",
            headers=self._auth_header(token),
            files={"file": ("avatar.png", png, "image/png")},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["profile_photo_url"] is not None
        assert body["profile_photo_url"].endswith(".png")
        assert "profile_photos" in body["profile_photo_url"]

    def test_upload_photo_returns_in_me(self, client, tmp_path, monkeypatch):
        monkeypatch.setattr("app.config.settings.upload_dir", str(tmp_path / "uploads"))
        token = self._register_and_token(client)

        png = self._make_png()
        client.post(
            "/auth/profile-photo",
            headers=self._auth_header(token),
            files={"file": ("avatar.png", png, "image/png")},
        )

        resp = client.get("/auth/me", headers=self._auth_header(token))
        assert resp.status_code == 200
        assert resp.json()["profile_photo_url"] is not None

    def test_me_returns_null_photo_by_default(self, client):
        token = self._register_and_token(client)
        resp = client.get("/auth/me", headers=self._auth_header(token))
        assert resp.status_code == 200
        assert resp.json()["profile_photo_url"] is None

    def test_upload_replaces_old_photo(self, client, tmp_path, monkeypatch):
        monkeypatch.setattr("app.config.settings.upload_dir", str(tmp_path / "uploads"))
        token = self._register_and_token(client)

        # Upload first photo
        png1 = self._make_png()
        resp1 = client.post(
            "/auth/profile-photo",
            headers=self._auth_header(token),
            files={"file": ("first.png", png1, "image/png")},
        )
        url1 = resp1.json()["profile_photo_url"]

        # Upload second photo
        png2 = self._make_png()
        resp2 = client.post(
            "/auth/profile-photo",
            headers=self._auth_header(token),
            files={"file": ("second.png", png2, "image/png")},
        )
        url2 = resp2.json()["profile_photo_url"]

        assert url1 != url2
        # Old file removed from disk
        old_path = url1.lstrip("/")
        assert not os.path.isfile(old_path)

    def test_delete_photo(self, client, tmp_path, monkeypatch):
        monkeypatch.setattr("app.config.settings.upload_dir", str(tmp_path / "uploads"))
        token = self._register_and_token(client)

        png = self._make_png()
        upload_resp = client.post(
            "/auth/profile-photo",
            headers=self._auth_header(token),
            files={"file": ("del.png", png, "image/png")},
        )
        assert upload_resp.json()["profile_photo_url"] is not None

        del_resp = client.delete("/auth/profile-photo", headers=self._auth_header(token))
        assert del_resp.status_code == 204

        me_resp = client.get("/auth/me", headers=self._auth_header(token))
        assert me_resp.json()["profile_photo_url"] is None

    def test_delete_photo_noop_when_none(self, client):
        token = self._register_and_token(client)
        resp = client.delete("/auth/profile-photo", headers=self._auth_header(token))
        assert resp.status_code == 204

    def test_upload_rejects_invalid_type(self, client):
        token = self._register_and_token(client)
        txt = io.BytesIO(b"not an image")
        resp = client.post(
            "/auth/profile-photo",
            headers=self._auth_header(token),
            files={"file": ("bad.txt", txt, "text/plain")},
        )
        assert resp.status_code == 400
        assert "not allowed" in resp.json()["detail"]

    def test_upload_rejects_oversized_file(self, client, monkeypatch):
        monkeypatch.setattr("app.config.settings.max_photo_size", 10)
        token = self._register_and_token(client)
        big = io.BytesIO(b"x" * 100)
        resp = client.post(
            "/auth/profile-photo",
            headers=self._auth_header(token),
            files={"file": ("big.png", big, "image/png")},
        )
        assert resp.status_code == 400
        assert "too large" in resp.json()["detail"]

    def test_upload_requires_auth(self, client):
        png = io.BytesIO(b"fake")
        resp = client.post(
            "/auth/profile-photo",
            files={"file": ("a.png", png, "image/png")},
        )
        assert resp.status_code in (401, 403)

    def test_upload_jpeg(self, client, tmp_path, monkeypatch):
        monkeypatch.setattr("app.config.settings.upload_dir", str(tmp_path / "uploads"))
        token = self._register_and_token(client)
        # Minimal JPEG-like bytes (content type is what matters for validation)
        jpg = io.BytesIO(b"\xff\xd8\xff\xe0" + b"\x00" * 50)
        resp = client.post(
            "/auth/profile-photo",
            headers=self._auth_header(token),
            files={"file": ("photo.jpg", jpg, "image/jpeg")},
        )
        assert resp.status_code == 200
        assert resp.json()["profile_photo_url"].endswith(".jpg")
