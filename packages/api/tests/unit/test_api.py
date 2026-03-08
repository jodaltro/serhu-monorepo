"""Unit tests for the SerHu REST API."""

from __future__ import annotations

import pytest


class TestHealthEndpoint:

    def test_health_check(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["service"] == "serhu-api"


class TestCreateBeing:

    def test_create_being_returns_201(self, client):
        resp = client.post("/beings", json={"name": "Luna", "language": "pt"})
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Luna"
        assert data["language"] == "pt"
        assert data["stage"] == "sensorimotor"
        assert data["cognitive_age"] == 0.0
        assert "being_id" in data

    def test_create_being_default_language(self, client):
        resp = client.post("/beings", json={"name": "DefaultBeing"})
        assert resp.status_code == 201
        assert resp.json()["language"] == "en"

    def test_create_being_french(self, client):
        resp = client.post("/beings", json={"name": "Soleil", "language": "fr"})
        assert resp.status_code == 201
        assert resp.json()["language"] == "fr"


class TestGetBeing:

    def test_get_being_after_creation(self, client):
        create_resp = client.post("/beings", json={"name": "Luna"})
        being_id = create_resp.json()["being_id"]

        resp = client.get(f"/beings/{being_id}")
        assert resp.status_code == 200
        assert resp.json()["being_id"] == being_id
        assert resp.json()["name"] == "Luna"

    def test_get_nonexistent_being_404(self, client):
        resp = client.get("/beings/nonexistent-id")
        assert resp.status_code == 404


class TestGetPersonality:

    def test_personality_has_all_dimensions(self, client):
        create_resp = client.post("/beings", json={"name": "Luna"})
        being_id = create_resp.json()["being_id"]

        resp = client.get(f"/beings/{being_id}/personality")
        assert resp.status_code == 200
        data = resp.json()

        # Must have all 4 personality models
        assert "hexaco" in data
        assert "tci_temperament" in data
        assert "tci_character" in data
        assert "schwartz" in data

        # HEXACO tabula rasa: all facets at 0.5
        assert data["hexaco"]["sincerity"] == 0.5
        assert data["hexaco"]["creativity"] == 0.5

        # TCI Character tabula rasa: all at 0.0
        assert data["tci_character"]["empathy"] == 0.0

        # Schwartz tabula rasa: all at 0.0
        assert data["schwartz"]["hedonism"] == 0.0

        # Beliefs start empty
        assert data["core_beliefs"] == []
        assert data["surface_beliefs"] == []


class TestProcessMessage:

    def test_process_message(self, client):
        create_resp = client.post("/beings", json={"name": "Luna"})
        being_id = create_resp.json()["being_id"]

        resp = client.post(
            f"/beings/{being_id}/process",
            json={"role": "user", "content": "Hello!"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["working_memory_count"] >= 1

    def test_process_with_trait_deltas(self, client):
        create_resp = client.post("/beings", json={"name": "Luna"})
        being_id = create_resp.json()["being_id"]

        resp = client.post(
            f"/beings/{being_id}/process",
            json={
                "role": "user",
                "content": "You are very kind",
                "trait_deltas": {"hexaco": {"gentleness": 0.05}},
            },
        )
        assert resp.status_code == 200

        # Verify the trait was updated
        p_resp = client.get(f"/beings/{being_id}/personality")
        assert p_resp.json()["hexaco"]["gentleness"] == 0.55


class TestConsolidate:

    def test_consolidate(self, client):
        create_resp = client.post("/beings", json={"name": "Luna"})
        being_id = create_resp.json()["being_id"]

        # Add some messages
        client.post(f"/beings/{being_id}/process", json={"role": "user", "content": "Hello!"})
        client.post(f"/beings/{being_id}/process", json={"role": "user", "content": "How are you?"})

        resp = client.post(f"/beings/{being_id}/consolidate")
        assert resp.status_code == 200
        assert "archived" in resp.json()


class TestSleep:

    def test_sleep_cycle(self, client):
        create_resp = client.post("/beings", json={"name": "Luna"})
        being_id = create_resp.json()["being_id"]

        # Add some episodes for sleep to process
        for i in range(5):
            client.post(
                f"/beings/{being_id}/process",
                json={"role": "user", "content": f"Message {i}"},
            )

        # Use sleep-once for backward-compatible single-shot sleep
        resp = client.post(
            f"/beings/{being_id}/sleep-once",
            json={"num_rollouts": 50, "svd_rank": 4, "seed": 42},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "facts_extracted" in data
        assert "beliefs_added" in data
        assert "hypotheses_generated" in data

    def test_sleep_and_wake(self, client):
        create_resp = client.post("/beings", json={"name": "Luna"})
        being_id = create_resp.json()["being_id"]

        # Add some episodes
        for i in range(5):
            client.post(
                f"/beings/{being_id}/process",
                json={"role": "user", "content": f"Message {i}"},
            )

        # Start continuous sleep
        resp = client.post(
            f"/beings/{being_id}/sleep",
            json={"num_rollouts": 50, "svd_rank": 4, "seed": 42},
        )
        assert resp.status_code == 200
        assert resp.json()["is_sleeping"] is True

        # Check the being is sleeping
        being = client.get(f"/beings/{being_id}").json()
        assert being["is_sleeping"] is True

        # Wake the being
        resp = client.post(f"/beings/{being_id}/wake", json={"timeout": 10.0})
        assert resp.status_code == 200
        data = resp.json()
        assert "cycles_completed" in data
        assert data["cycles_completed"] >= 1

    def test_sleep_while_already_sleeping_returns_409(self, client):
        create_resp = client.post("/beings", json={"name": "Luna"})
        being_id = create_resp.json()["being_id"]

        # Start continuous sleep
        client.post(
            f"/beings/{being_id}/sleep",
            json={"num_rollouts": 50, "svd_rank": 4, "seed": 42},
        )

        # Second sleep attempt should fail
        resp = client.post(
            f"/beings/{being_id}/sleep",
            json={"num_rollouts": 50, "svd_rank": 4, "seed": 42},
        )
        assert resp.status_code == 409

        # Cleanup: wake up the being
        client.post(f"/beings/{being_id}/wake", json={"timeout": 10.0})


class TestRecall:

    def test_recall_after_messages(self, client):
        create_resp = client.post("/beings", json={"name": "Luna"})
        being_id = create_resp.json()["being_id"]

        # Add messages and consolidate to archival
        for i in range(3):
            client.post(
                f"/beings/{being_id}/process",
                json={"role": "user", "content": f"Message about topic {i}"},
            )
        client.post(f"/beings/{being_id}/consolidate")

        resp = client.post(
            f"/beings/{being_id}/recall",
            json={"query": "topic", "top_k": 5},
        )
        assert resp.status_code == 200
        assert "memories" in resp.json()


class TestLearnFact:

    def test_learn_fact(self, client):
        create_resp = client.post("/beings", json={"name": "Luna"})
        being_id = create_resp.json()["being_id"]

        resp = client.post(
            f"/beings/{being_id}/learn",
            json={"fact": "The sky is blue"},
        )
        assert resp.status_code == 200
        assert resp.json()["stored"] is True


class TestVisualState:

    def test_visual_state_tabula_rasa(self, client):
        create_resp = client.post("/beings", json={"name": "Luna"})
        being_id = create_resp.json()["being_id"]

        resp = client.get(f"/beings/{being_id}/visual")
        assert resp.status_code == 200
        data = resp.json()

        # Should have all visual fields
        assert data["being_id"] == being_id
        assert data["cognitive_stage"] == "sensorimotor"
        assert data["cognitive_age"] == 0.0

        # Color
        assert 0.0 <= data["hue"] <= 360.0
        assert 0.0 <= data["saturation"] <= 1.0
        assert 0.0 <= data["lightness"] <= 1.0
        assert 0.0 <= data["alpha"] <= 1.0

        # Geometry
        assert 0.0 <= data["roundness"] <= 1.0
        assert 0.0 <= data["complexity"] <= 1.0
        assert 0.0 <= data["scale"] <= 1.0

        # Animation
        assert data["pulse_rate"] > 0
        assert 0.0 <= data["movement_speed"] <= 1.0

    def test_visual_state_changes_with_traits(self, client):
        create_resp = client.post("/beings", json={"name": "Luna"})
        being_id = create_resp.json()["being_id"]

        # Get initial visual state
        v1 = client.get(f"/beings/{being_id}/visual").json()

        # Update traits to be very agreeable
        client.post(
            f"/beings/{being_id}/process",
            json={
                "role": "user",
                "content": "You are kind",
                "trait_deltas": {
                    "hexaco": {
                        "forgiveness": 0.05,
                        "gentleness": 0.05,
                        "flexibility": 0.05,
                        "patience": 0.05,
                    }
                },
            },
        )

        # Get updated visual state
        v2 = client.get(f"/beings/{being_id}/visual").json()

        # Roundness should increase with agreeableness
        assert v2["roundness"] > v1["roundness"]


class TestChatWithSelfLearning:

    def test_chat_without_llm_returns_200(self, client):
        """Chat now works without external LLM (self-learning)."""
        create_resp = client.post("/beings", json={"name": "Luna"})
        being_id = create_resp.json()["being_id"]

        resp = client.post(
            f"/beings/{being_id}/chat",
            json={"message": "Hello!"},
        )
        # Without an LLM client, chat now uses self-learning (NeuralEngine)
        assert resp.status_code == 200
        data = resp.json()
        assert "response" in data
        assert isinstance(data["response"], str)


class TestSeedWorld:

    def test_seed_world_default_stage(self, client):
        """Seed uses the Being's current stage when none is specified."""
        create_resp = client.post("/beings", json={"name": "Luna"})
        being_id = create_resp.json()["being_id"]

        resp = client.post(f"/beings/{being_id}/seed")
        assert resp.status_code == 200
        data = resp.json()
        assert data["stage"] == "sensorimotor"
        assert data["facts_injected"] > 0
        assert data["episodes_injected"] > 0

    def test_seed_world_specific_stage(self, client):
        """Seed accepts an explicit stage parameter."""
        create_resp = client.post("/beings", json={"name": "Luna"})
        being_id = create_resp.json()["being_id"]

        resp = client.post(
            f"/beings/{being_id}/seed",
            json={"stage": "preoperational"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["stage"] == "preoperational"
        assert data["facts_injected"] > 0

    def test_seed_world_without_episodes(self, client):
        """Seed can inject facts only (no episodes)."""
        create_resp = client.post("/beings", json={"name": "Luna"})
        being_id = create_resp.json()["being_id"]

        resp = client.post(
            f"/beings/{being_id}/seed",
            json={"include_episodes": False},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["facts_injected"] > 0
        assert data["episodes_injected"] == 0

    def test_seed_world_nonexistent_being_404(self, client):
        resp = client.post("/beings/nonexistent-id/seed")
        assert resp.status_code == 404
