"""Lightweight unit tests for the core logic.

No network or API key required. Run from the backend folder:

    python -m unittest discover -s tests
"""

import os
import sys
import unittest
from pathlib import Path
from unittest import mock

# Make the backend package importable when run via `unittest discover`.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import services.mistral_client as mc
from models import TranscriptionResult, TranscriptionSegment
from services.transcription_engines import get_engine, WhisperEngine, VoxtralEngine
from services.refine import (
    RefinementMode,
    get_refinement_service,
    reset_refinement_service,
)


class EngineSelectionTests(unittest.TestCase):
    def test_default_and_unknown_select_whisper(self):
        self.assertIsInstance(get_engine("whisper", "base"), WhisperEngine)
        self.assertIsInstance(get_engine("", "base"), WhisperEngine)

    def test_voxtral_selected(self):
        engine = get_engine("voxtral", "base")
        self.assertIsInstance(engine, VoxtralEngine)
        self.assertEqual(engine.model_name, "voxtral-mini-latest")

    def test_whisper_model_passthrough(self):
        self.assertEqual(get_engine("whisper", "small").model_name, "small")


class _NoKeyMixin:
    """Isolate key state: no env key, no keychain, no session key."""

    def setUp(self):
        self._saved_env = os.environ.pop("MISTRAL_API_KEY", None)
        self._keyring_patch = mock.patch.object(mc, "_get_remembered_key", return_value=None)
        self._keyring_patch.start()
        mc._session_key = None
        mc.reset_mistral_client()

    def tearDown(self):
        self._keyring_patch.stop()
        mc._session_key = None
        mc.reset_mistral_client()
        if self._saved_env is not None:
            os.environ["MISTRAL_API_KEY"] = self._saved_env


class KeyHandlingTests(_NoKeyMixin, unittest.TestCase):
    def test_no_key_status(self):
        status = mc.key_status()
        self.assertFalse(status["configured"])
        self.assertIsNone(status["source"])
        self.assertIsNone(status["hint"])

    def test_session_key_exposes_only_hint(self):
        mc.set_key("sk-secret-ABCD1234", remember=False)
        status = mc.key_status()
        self.assertTrue(status["configured"])
        self.assertEqual(status["source"], "session")
        self.assertEqual(status["hint"], "1234")
        # The raw key must never appear in the status payload.
        self.assertNotIn("sk-secret", str(status))

    def test_environment_takes_precedence(self):
        mc.set_key("session-0000", remember=False)
        os.environ["MISTRAL_API_KEY"] = "env-key-WXYZ"
        try:
            status = mc.key_status()
            self.assertEqual(status["source"], "environment")
            self.assertEqual(status["hint"], "WXYZ")
        finally:
            os.environ.pop("MISTRAL_API_KEY", None)


class RefinementTests(_NoKeyMixin, unittest.TestCase):
    def setUp(self):
        super().setUp()
        reset_refinement_service()

    def test_exactly_five_modes(self):
        modes = get_refinement_service().get_available_modes()
        self.assertEqual(set(modes), {m.value for m in RefinementMode})
        self.assertEqual(len(modes), 5)

    def test_prompt_template_builds(self):
        cfg = get_refinement_service().get_mode_config("clean_transcript")
        self.assertIn("{transcript}", cfg.user_prompt_template)
        self.assertIn("hello world", cfg.user_prompt_template.format(transcript="hello world"))

    def test_action_items_is_low_temperature_json(self):
        cfg = get_refinement_service().get_mode_config("action_items")
        self.assertEqual(cfg.output_format, "json")
        self.assertLessEqual(cfg.temperature, 0.2)

    def test_refine_without_key_fails_gracefully(self):
        result = get_refinement_service().refine("some transcript", "clean_transcript")
        self.assertFalse(result.success)
        self.assertIn("not configured", (result.error or "").lower())


class TranscriptEditTests(unittest.TestCase):
    def setUp(self):
        os.environ.pop("MISTRAL_API_KEY", None)
        import main  # noqa: WPS433 (import here to build the app once tests run)
        from fastapi.testclient import TestClient
        import services.file_service as file_service

        self.file_service = file_service
        self.client = TestClient(main.app)
        self.file_id = "unittest_edit01"
        file_service.save_transcription(
            self.file_id,
            TranscriptionResult(
                file_id=self.file_id,
                text="original text",
                segments=[TranscriptionSegment(start=0.0, end=1.0, text="original text")],
                model="base",
                language="en",
            ),
        )

    def tearDown(self):
        self.file_service.delete_file(self.file_id)

    def test_edit_persists_and_sets_flag(self):
        resp = self.client.put(f"/api/transcribe/{self.file_id}/result", json={"text": "edited text"})
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertEqual(body["text"], "edited text")
        self.assertTrue(body["edited"])

        # Edit survives a fresh read (would survive a refresh).
        reread = self.client.get(f"/api/transcribe/{self.file_id}/result").json()
        self.assertEqual(reread["text"], "edited text")
        self.assertTrue(reread["edited"])


if __name__ == "__main__":
    unittest.main()
