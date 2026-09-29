from __future__ import annotations

import os
import unittest
from unittest.mock import patch

import langfuse

from app import tracing


class TracingAdapterTests(unittest.TestCase):
    def test_child_observation_adapter_uses_v4_context_manager(self) -> None:
        class FakeObservation:
            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

        class FakeClient:
            def __init__(self):
                self.calls = []

            def start_as_current_observation(self, **kwargs):
                self.calls.append(kwargs)
                return FakeObservation()

        client = FakeClient()
        with tracing.child_observation(client, name="retrieval", as_type="retriever"):
            pass

        self.assertEqual(client.calls, [{"name": "retrieval", "as_type": "retriever"}])

    def test_adapter_uses_the_installed_langfuse_v4_api(self) -> None:
        self.assertEqual(tracing.observe.__module__, langfuse.observe.__module__)
        client = tracing.get_langfuse_client()
        self.assertTrue(callable(client.update_current_span))
        self.assertTrue(callable(client.update_current_generation))
        self.assertTrue(callable(client.start_as_current_observation))

    def test_tracing_is_disabled_without_both_keys(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            self.assertFalse(tracing.tracing_enabled())

        with patch.dict(os.environ, {"LANGFUSE_PUBLIC_KEY": "pk-only"}, clear=True):
            self.assertFalse(tracing.tracing_enabled())


if __name__ == "__main__":
    unittest.main()
