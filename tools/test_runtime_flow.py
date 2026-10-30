"""Regression tests for offline inference and voice-response progress."""

import logging
import importlib.util
import os
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import reasoning
import runtime_log


class RuntimeFlowTests(unittest.TestCase):
    @staticmethod
    def engine_without_assets():
        engine = object.__new__(reasoning.LlamaReasoning)
        engine.llama_exe = Path("unused-llama-completion.exe")
        engine.model_path = Path("unused-model.gguf")
        engine.context_size = 512
        engine.conversation_history = []
        return engine

    def test_batch_inference_never_inherits_console_input(self):
        engine = self.engine_without_assets()
        output = subprocess.CompletedProcess([], 0, "4\n[ Prompt: 10 t/s ]", "")
        with patch("reasoning.subprocess.run", return_value=output) as run:
            with patch("reasoning.get_runtime_logger") as logger:
                self.assertEqual(engine.generate_response("What is 2+2?", max_tokens=8), "4")

        self.assertEqual(run.call_args.kwargs["stdin"], subprocess.DEVNULL)
        self.assertEqual(run.call_args.kwargs["timeout"], 120)
        self.assertEqual(logger.return_value.info.call_count, 2)
        self.assertIn(
            "inference started", logger.return_value.info.call_args_list[0].args[0]
        )
        self.assertIn("reply inference ok", logger.return_value.info.call_args.args[0])
        self.assertNotIn("What is 2+2?", str(logger.return_value.info.call_args_list))
        self.assertEqual(len(engine.conversation_history), 2)

    def test_inference_timeout_is_reported(self):
        engine = self.engine_without_assets()
        with patch(
            "reasoning.subprocess.run",
            side_effect=subprocess.TimeoutExpired(["llama-completion"], 120),
        ):
            with patch("reasoning.get_runtime_logger") as logger:
                response = engine.generate_response("Hello")
        self.assertIn("taking longer", response)
        self.assertIn("reply inference timeout", logger.return_value.info.call_args.args[0])

    def test_structured_interpretation_has_no_prompt_echo_or_history_side_effect(self):
        engine = self.engine_without_assets()
        schema = {"type": "object", "properties": {"kind": {"type": "string"}}}
        answer = '{"kind":"self_purpose","goal":"My purpose","draft":""}'
        with patch(
            "reasoning.subprocess.run",
            return_value=subprocess.CompletedProcess([], 0, answer, ""),
        ) as run:
            with patch("reasoning.get_runtime_logger") as logger:
                self.assertEqual(
                    engine.generate_structured_response("What is your intent?", schema),
                    answer,
                )
        command = run.call_args.args[0]
        self.assertIn("--json-schema", command)
        self.assertIn("--no-display-prompt", command)
        self.assertIn("--offline", command)
        self.assertEqual(run.call_args.kwargs["stdin"], subprocess.DEVNULL)
        self.assertNotIn("What is your intent?", str(logger.return_value.info.call_args_list))
        self.assertEqual(engine.conversation_history, [])

    def test_structured_inference_fails_closed_on_process_errors(self):
        engine = self.engine_without_assets()
        with patch(
            "reasoning.subprocess.run",
            return_value=subprocess.CompletedProcess([], 1, "", "failed"),
        ):
            with patch("reasoning.get_runtime_logger"):
                with self.assertRaises(RuntimeError):
                    engine.generate_structured_response("Hello", {"type": "object"})

    def test_runtime_log_is_local_and_persistent(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.dict(os.environ, {"JARVIS_BASE_PATH": directory}):
                with patch.object(
                    runtime_log.logging, "getLogger",
                    return_value=logging.Logger("jarvis.runtime.test"),
                ):
                    logger = runtime_log.get_runtime_logger()
                    try:
                        logger.info("intent inference ok after 1.0s")
                        for handler in logger.handlers:
                            handler.flush()
                        log_file = Path(directory) / "logs" / "runtime.log"
                        self.assertIn(
                            "intent inference ok after 1.0s",
                            log_file.read_text(encoding="utf-8"),
                        )
                    finally:
                        for handler in logger.handlers[:]:
                            logger.removeHandler(handler)
                            handler.close()

    def test_voice_path_exposes_both_stages_then_clears_status(self):
        import jarvis_app

        app = object.__new__(jarvis_app.JarvisApp)
        app.page = SimpleNamespace(update=Mock())
        app.activity_text = SimpleNamespace(value="")
        app.add_chat_message = Mock()
        app.create_jarvis_persona_prompt = Mock(return_value="persona")
        observed = []
        engine = Mock()

        def classify(_):
            observed.append(app.activity_text.value)
            return "CONTINUE_LOOP"

        def reply(*_, **__):
            observed.append(app.activity_text.value)
            return (
                '{"kind":"dialogue","goal":"","draft":"Doing well, thank you."}'
            )

        engine.generate_structured_response.side_effect = reply
        with patch.object(jarvis_app, "process_command", side_effect=classify):
            with patch.object(jarvis_app, "get_reasoning_engine", return_value=engine):
                with patch.object(
                    jarvis_app, "get_conversation_context", return_value=""
                ) as get_context:
                    with patch.object(jarvis_app, "remember_conversation") as remember:
                        with patch.object(jarvis_app, "speak"):
                            app.process_user_command("Checking in")
        self.assertEqual(
            observed,
            ["Checking your request locally...", "Understanding your request locally..."],
        )
        self.assertEqual(app.activity_text.value, "")
        get_context.assert_called_once_with(3, query=None)
        remember.assert_called_once_with("Checking in", "Doing well, thank you.")
        engine.generate_response.assert_not_called()
        engine.generate_structured_response.assert_called_once()

    def test_deactivated_voice_session_discards_late_inference_reply(self):
        import jarvis_app

        app = object.__new__(jarvis_app.JarvisApp)
        app.page = SimpleNamespace(update=Mock())
        app.activity_text = SimpleNamespace(value="")
        app.add_chat_message = Mock()
        app.create_jarvis_persona_prompt = Mock(return_value="persona")
        app.is_listening = True
        app._voice_generation = 1
        engine = Mock()

        def reply(*_, **__):
            app.is_listening = False
            app._voice_generation += 1
            return '{"kind":"dialogue","goal":"","draft":"A late reply."}'

        engine.generate_structured_response.side_effect = reply
        with patch.object(jarvis_app, "process_command", return_value="CONTINUE_LOOP"):
            with patch.object(jarvis_app, "get_conversation_context", return_value=""):
                with patch.object(jarvis_app, "get_reasoning_engine", return_value=engine):
                    with patch.object(jarvis_app, "remember_conversation") as remember:
                        with patch.object(jarvis_app, "speak") as speak:
                            app.process_user_command("Checking in", voice_generation=1)
        engine.generate_structured_response.assert_called_once()
        remember.assert_not_called()
        speak.assert_not_called()
        app.add_chat_message.assert_not_called()
        self.assertEqual(app.activity_text.value, "")

    def test_live_data_request_stays_offline_without_inference(self):
        import jarvis_app

        app = object.__new__(jarvis_app.JarvisApp)
        app.page = SimpleNamespace(update=Mock())
        app.activity_text = SimpleNamespace(value="")
        app.add_chat_message = Mock()
        with patch.object(jarvis_app, "process_command", return_value="CONTINUE_LOOP"):
            with patch.object(jarvis_app, "get_reasoning_engine") as engine:
                with patch.object(jarvis_app, "get_conversation_context") as context:
                    with patch.object(jarvis_app, "remember_conversation") as remember:
                        with patch.object(jarvis_app, "get_runtime_logger") as logger:
                            with patch.object(jarvis_app, "speak") as speak:
                                app.process_user_command("Has my flight gate changed?")
        engine.assert_not_called()
        context.assert_not_called()
        remember.assert_not_called()
        self.assertIn("offline", speak.call_args.args[0].lower())
        self.assertNotIn(
            "Has my flight gate changed?", str(logger.return_value.info.call_args_list)
        )
        self.assertEqual(app.activity_text.value, "")

    def test_local_metrics_do_not_require_a_model(self):
        import jarvis_app

        app = object.__new__(jarvis_app.JarvisApp)
        app.page = SimpleNamespace(update=Mock())
        app.activity_text = SimpleNamespace(value="")
        app.add_chat_message = Mock()
        with patch.object(jarvis_app, "process_command", return_value="CONTINUE_LOOP"):
            with patch.object(jarvis_app, "get_reasoning_engine") as engine:
                with patch.object(jarvis_app, "get_conversation_context") as context:
                    with patch.object(jarvis_app, "remember_conversation") as remember:
                        with patch.object(jarvis_app.psutil, "cpu_percent", return_value=12.5):
                            with patch.object(
                                jarvis_app.psutil, "virtual_memory",
                                return_value=SimpleNamespace(percent=34.5),
                            ):
                                with patch.object(jarvis_app, "speak") as speak:
                                    app.process_user_command("What is my CPU usage?")
        engine.assert_not_called()
        context.assert_not_called()
        remember.assert_not_called()
        self.assertIn("12.5%", speak.call_args.args[0])
        self.assertIn("34.5%", speak.call_args.args[0])
        self.assertEqual(app.activity_text.value, "")

    def test_failed_local_metrics_do_not_fall_back_to_model(self):
        import jarvis_app

        app = object.__new__(jarvis_app.JarvisApp)
        app.page = SimpleNamespace(update=Mock())
        app.activity_text = SimpleNamespace(value="")
        app.add_chat_message = Mock()
        with patch.object(jarvis_app, "process_command", return_value="CONTINUE_LOOP"):
            with patch.object(jarvis_app, "get_reasoning_engine") as engine:
                with patch.object(jarvis_app, "get_conversation_context") as context:
                    with patch.object(jarvis_app, "remember_conversation") as remember:
                        with patch.object(
                            jarvis_app.psutil, "cpu_percent", side_effect=RuntimeError("metrics unavailable")
                        ):
                            with patch.object(jarvis_app, "speak") as speak:
                                app.process_user_command("What is my CPU usage?")
        engine.assert_not_called()
        context.assert_not_called()
        remember.assert_not_called()
        self.assertIn("cannot read local", speak.call_args.args[0].lower())

    def test_approved_memory_reaches_one_inference_with_source(self):
        import decision_controller
        import jarvis_app

        app = object.__new__(jarvis_app.JarvisApp)
        app.page = SimpleNamespace(update=Mock())
        app.activity_text = SimpleNamespace(value="")
        app.add_chat_message = Mock()
        app.create_jarvis_persona_prompt = Mock(return_value="persona")
        engine = Mock()
        engine.generate_response.return_value = "Your reviewed note says Pixel is your cat."
        source = "User-reviewed vault notes:\nSource: Jarvis/Knowledge/pixel.md\nPixel is a cat."
        with patch.object(jarvis_app, "process_command", return_value="CONTINUE_LOOP"):
            with patch.object(
                decision_controller.OfflineDecisionController, "_search",
                return_value=[(3, "pixel.md", "Pixel is a cat.")],
            ):
                with patch.object(jarvis_app, "get_conversation_context", return_value=source) as context:
                    with patch.object(jarvis_app, "get_reasoning_engine", return_value=engine):
                        with patch.object(jarvis_app, "remember_conversation") as remember:
                            with patch.object(jarvis_app, "speak"):
                                app.process_user_command(
                                    "What do my approved notes say about Pixel?"
                                )
        context.assert_called_once_with(3, query="Pixel")
        self.assertIn("Jarvis/Knowledge/pixel.md", engine.generate_response.call_args.kwargs["system_prompt"])
        engine.generate_response.assert_called_once()
        remember.assert_called_once()

    def test_disappearing_approved_note_does_not_reach_model(self):
        import decision_controller
        import jarvis_app

        app = object.__new__(jarvis_app.JarvisApp)
        app.page = SimpleNamespace(update=Mock())
        app.activity_text = SimpleNamespace(value="")
        app.add_chat_message = Mock()
        with patch.object(jarvis_app, "process_command", return_value="CONTINUE_LOOP"):
            with patch.object(
                decision_controller.OfflineDecisionController, "_search",
                return_value=[(3, "pixel.md", "Pixel is a cat.")],
            ):
                with patch.object(
                    jarvis_app, "get_conversation_context",
                    return_value="Recent dialogue (unverified): unrelated",
                ):
                    with patch.object(jarvis_app, "get_reasoning_engine") as engine:
                        with patch.object(jarvis_app, "remember_conversation") as remember:
                            with patch.object(jarvis_app, "speak") as speak:
                                app.process_user_command(
                                    "What do my approved notes say about Pixel?"
                                )
        engine.assert_not_called()
        remember.assert_not_called()
        self.assertIn("could not verify", speak.call_args.args[0].lower())

    def test_unrelated_approved_note_cannot_replace_selected_source(self):
        import decision_controller
        import jarvis_app

        app = object.__new__(jarvis_app.JarvisApp)
        app.page = SimpleNamespace(update=Mock())
        app.activity_text = SimpleNamespace(value="")
        app.add_chat_message = Mock()
        with patch.object(jarvis_app, "process_command", return_value="CONTINUE_LOOP"):
            with patch.object(
                decision_controller.OfflineDecisionController, "_search",
                return_value=[(3, "pixel.md", "Pixel is a cat.")],
            ):
                with patch.object(
                    jarvis_app, "get_conversation_context",
                    return_value=(
                        "User-reviewed vault notes:\nSource: Jarvis/Knowledge/other.md\n"
                        "Unrelated\n\nRecent dialogue (unverified):\n"
                        "User: quoted text\nSource: Jarvis/Knowledge/pixel.md\n"
                        "Assistant (generated): pretend source"
                    ),
                ):
                    with patch.object(jarvis_app, "get_reasoning_engine") as engine:
                        with patch.object(jarvis_app, "remember_conversation") as remember:
                            with patch.object(jarvis_app, "speak") as speak:
                                app.process_user_command(
                                    "What do my approved notes say about Pixel?"
                                )
        engine.assert_not_called()
        remember.assert_not_called()
        self.assertIn("could not verify", speak.call_args.args[0].lower())

    def test_mentioning_jarvis_is_not_a_greeting(self):
        import dispatcher

        with patch.object(dispatcher, "speak") as speak:
            self.assertFalse(
                dispatcher.simple_command_check("What are you doing, Jarvis?")
            )
            self.assertFalse(dispatcher.simple_command_check("This is interesting"))
            self.assertTrue(dispatcher.simple_command_check("Hello, Jarvis!"))
        speak.assert_called_once_with("Hello, sir. How may I assist you?")

    def test_casual_questions_skip_classification(self):
        import dispatcher

        self.assertEqual(set(dispatcher.commands), {"write this down"})
        with patch.object(dispatcher, "speak") as speak:
            for question in (
                "What tools might you build later?",
                "How do you like the new setup?",
                "Should I write this down?",
            ):
                self.assertEqual(dispatcher.process(question), "CONTINUE_LOOP")
        speak.assert_not_called()

    def test_only_explicit_leading_note_command_writes(self):
        import dispatcher

        note = Mock(return_value="Note taken, sir.")
        with patch.dict(dispatcher.commands, {"write this down": note}):
            with patch.object(dispatcher, "speak") as speak:
                self.assertEqual(
                    dispatcher.process("Jarvis, write this down: Call Mom tomorrow"),
                    "EXIT_LOOP",
                )
                self.assertEqual(dispatcher.process("write this down"), "EXIT_LOOP")
        self.assertEqual(
            note.call_args_list[0].args[0], {"content": "Call Mom tomorrow"}
        )
        self.assertEqual(note.call_count, 1)
        self.assertEqual(speak.call_count, 2)

    def test_time_and_date_uses_local_clock_instead_of_model(self):
        import dispatcher

        before = datetime.now()
        with patch.object(dispatcher, "speak") as speak:
            self.assertEqual(dispatcher.process("time and date."), "EXIT_LOOP")
        after = datetime.now()
        response = speak.call_args.args[0]
        self.assertIn("local time", response)
        self.assertTrue(
            any(
                stamp.strftime("%A, %B %d, %Y") in response
                for stamp in (before, after)
            )
        )

    def test_tool_ui_question_acknowledges_available_and_unavailable_tools(self):
        import dispatcher

        with patch.object(dispatcher, "speak") as speak:
            self.assertEqual(
                dispatcher.process("Can you see any of your tools or your UI?"),
                "EXIT_LOOP",
            )
        response = speak.call_args.args[0]
        self.assertIn("save a note", response)
        self.assertIn("cannot view my screen", response)

    def test_live_voice_capability_questions_are_grounded_locally(self):
        import dispatcher

        with patch.object(dispatcher, "speak") as speak:
            self.assertEqual(dispatcher.process("Do you see your obsidian?"), "EXIT_LOOP")
            self.assertIn("approved", speak.call_args.args[0].lower())
            self.assertIn("cannot edit arbitrary", speak.call_args.args[0].lower())
            self.assertEqual(
                dispatcher.process(
                    "Well, Jarvis, do you recognize any of your tools or the obsidian?"
                ),
                "EXIT_LOOP",
            )
            self.assertIn("declared local capabilities", speak.call_args.args[0])
            self.assertIn("cannot visually see Obsidian", speak.call_args.args[0])
            self.assertIn("cannot edit arbitrary", speak.call_args.args[0].lower())
            for question in (
                "Can you manage your Obsidian vault?",
                "Can you update my Obsidian notes?",
                "Are you able to read my vault?",
            ):
                with self.subTest(question=question):
                    self.assertEqual(dispatcher.process(question), "EXIT_LOOP")
                    self.assertIn("cannot edit arbitrary", speak.call_args.args[0].lower())
            self.assertEqual(
                dispatcher.process("How you doing Jarvis can you see all your new"),
                "EXIT_LOOP",
            )
            self.assertIn("cannot view my screen", speak.call_args.args[0])

    def test_live_voice_capability_question_does_not_start_inference(self):
        import dispatcher
        import jarvis_app

        app = object.__new__(jarvis_app.JarvisApp)
        app.page = SimpleNamespace(update=Mock())
        app.activity_text = SimpleNamespace(value="")
        app.add_chat_message = Mock()
        with patch.object(dispatcher, "speak") as speak:
            with patch.object(jarvis_app, "get_reasoning_engine") as engine:
                with patch.object(jarvis_app, "get_conversation_context") as context:
                    with patch.object(jarvis_app, "remember_conversation") as remember:
                        with patch.object(jarvis_app, "speak"):
                            app.process_user_command(
                                "Well, Jarvis, do you recognize any of your tools or the obsidian?"
                            )
        engine.assert_not_called()
        context.assert_not_called()
        remember.assert_not_called()
        self.assertIn("approved Knowledge", speak.call_args.args[0])
        self.assertEqual(app.activity_text.value, "")

    def test_semantic_capability_and_purpose_are_grounded_without_second_call(self):
        import jarvis_app
        from obsidian_memory import PurposeRecord

        app = object.__new__(jarvis_app.JarvisApp)
        app.page = SimpleNamespace(update=Mock())
        app.activity_text = SimpleNamespace(value="")
        app.add_chat_message = Mock()
        engine = Mock()
        brain = Mock()
        brain.read_purpose.return_value = PurposeRecord(
            "Support the user as an offline companion.",
            "Jarvis/Core/Purpose.md", "approved",
        )
        with patch.object(jarvis_app, "process_command", return_value="CONTINUE_LOOP"):
            with patch.object(jarvis_app, "get_conversation_context", return_value=""):
                with patch.object(jarvis_app, "get_reasoning_engine", return_value=engine):
                    with patch.object(jarvis_app, "get_brain", return_value=brain):
                        with patch.object(jarvis_app, "remember_conversation") as remember:
                            with patch.object(jarvis_app, "speak") as speak:
                                engine.generate_structured_response.return_value = (
                                    '{"kind":"capability_inventory","goal":"","draft":'
                                    '"I can edit every note."}'
                                )
                                app.process_user_command("What tools do you have available?")
                                self.assertIn(
                                    "cannot edit arbitrary Obsidian notes",
                                    speak.call_args.args[0],
                                )
                                engine.generate_structured_response.return_value = (
                                    '{"kind":"self_purpose","goal":"","draft":'
                                    '"I own the vault."}'
                                )
                                app.process_user_command("What is your intent?")
        self.assertIn("Support the user", speak.call_args.args[0])
        self.assertNotIn("I own the vault", speak.call_args.args[0])
        self.assertEqual(engine.generate_structured_response.call_count, 2)
        engine.generate_response.assert_not_called()
        remember.assert_not_called()
        self.assertEqual(app.activity_text.value, "")

    def test_purpose_file_question_reports_status_without_capability_list(self):
        import jarvis_app

        app = object.__new__(jarvis_app.JarvisApp)
        app.page = SimpleNamespace(update=Mock())
        app.activity_text = SimpleNamespace(value="")
        app.add_chat_message = Mock()
        engine = Mock()
        engine.generate_structured_response.return_value = (
            '{"kind":"purpose_status","goal":"","draft":""}'
        )
        brain = Mock()
        brain.read_purpose.return_value = None
        brain.purpose_status.return_value = "pending"
        with patch.object(jarvis_app, "process_command", return_value="CONTINUE_LOOP"):
            with patch.object(jarvis_app, "get_conversation_context", return_value=""):
                with patch.object(jarvis_app, "get_reasoning_engine", return_value=engine):
                    with patch.object(jarvis_app, "get_brain", return_value=brain):
                        with patch.object(jarvis_app, "remember_conversation") as remember:
                            with patch.object(jarvis_app, "speak") as speak:
                                app.process_user_command("Did you find purpose.md?")
        response = speak.call_args.args[0]
        self.assertIn("pending", response)
        self.assertIn("Purpose.md", response)
        self.assertNotIn("save a note", response)
        self.assertNotIn("tool", response.lower())
        brain.read_purpose.assert_not_called()
        brain.purpose_status.assert_called_once()
        remember.assert_not_called()
        self.assertEqual(app.activity_text.value, "")

    def test_semantic_voice_reply_is_discarded_after_deactivation(self):
        import jarvis_app

        app = object.__new__(jarvis_app.JarvisApp)
        app.page = SimpleNamespace(update=Mock())
        app.activity_text = SimpleNamespace(value="")
        app.add_chat_message = Mock()
        app.is_listening = True
        app._voice_generation = 1
        engine = Mock()

        def late_reply(*_, **__):
            app.is_listening = False
            app._voice_generation += 1
            return '{"kind":"dialogue","goal":"","draft":"Late answer."}'

        engine.generate_structured_response.side_effect = late_reply
        with patch.object(jarvis_app, "process_command", return_value="CONTINUE_LOOP"):
            with patch.object(jarvis_app, "get_conversation_context", return_value=""):
                with patch.object(jarvis_app, "get_reasoning_engine", return_value=engine):
                    with patch.object(jarvis_app, "remember_conversation") as remember:
                        with patch.object(jarvis_app, "speak") as speak:
                            app.process_user_command("How are you?", voice_generation=1)
        remember.assert_not_called()
        speak.assert_not_called()
        app.add_chat_message.assert_not_called()

    def test_invalid_semantic_output_does_not_fall_back_to_ungrounded_reply(self):
        import jarvis_app

        app = object.__new__(jarvis_app.JarvisApp)
        app.page = SimpleNamespace(update=Mock())
        app.activity_text = SimpleNamespace(value="")
        app.add_chat_message = Mock()
        engine = Mock()
        engine.generate_structured_response.return_value = (
            '{"kind":"run_command","goal":"Start a tool","draft":"Done"}'
        )
        with patch.object(jarvis_app, "process_command", return_value="CONTINUE_LOOP"):
            with patch.object(jarvis_app, "get_conversation_context", return_value=""):
                with patch.object(jarvis_app, "get_reasoning_engine", return_value=engine):
                    with patch.object(jarvis_app, "remember_conversation") as remember:
                        with patch.object(jarvis_app, "speak") as speak:
                            app.process_user_command("What tools do you have?")
        engine.generate_response.assert_not_called()
        remember.assert_not_called()
        self.assertIn("could not determine your intent", speak.call_args.args[0])
        self.assertNotIn("Done", speak.call_args.args[0])
        self.assertEqual(app.activity_text.value, "")

    def test_mentioning_recognition_without_asking_ability_stays_conversational(self):
        import dispatcher

        with patch.object(dispatcher, "speak") as speak:
            self.assertEqual(
                dispatcher.process("I recognize tools in Obsidian."), "CONTINUE_LOOP"
            )
        speak.assert_not_called()

    def test_self_purpose_and_health_questions_are_not_canned_replies(self):
        import dispatcher

        with patch.object(dispatcher, "speak") as speak:
            for question in (
                "What is your purpose as my assistant?",
                "Who are you?",
                "How are your reasoning systems working?",
                "Can you help me organize my notes?",
            ):
                with self.subTest(question=question):
                    self.assertEqual(dispatcher.process(question), "CONTINUE_LOOP")
        speak.assert_not_called()

    def test_conversation_word_does_not_bypass_semantic_interpretation(self):
        import jarvis_app

        app = object.__new__(jarvis_app.JarvisApp)
        app.page = SimpleNamespace(update=Mock())
        app.activity_text = SimpleNamespace(value="")
        app.add_chat_message = Mock()
        engine = Mock()
        engine.generate_structured_response.return_value = (
            '{"kind":"dialogue","goal":"","draft":"Conversation memory is unverified."}'
        )
        with patch.object(jarvis_app, "process_command", return_value="CONTINUE_LOOP"):
            with patch.object(jarvis_app, "get_conversation_context", return_value=""):
                with patch.object(jarvis_app, "get_reasoning_engine", return_value=engine):
                    with patch.object(jarvis_app, "remember_conversation"):
                        with patch.object(jarvis_app, "speak") as speak:
                            app.process_user_command("How does conversation memory work?")
        engine.generate_structured_response.assert_called_once()
        self.assertIn("unverified", speak.call_args.args[0])

    def test_gratitude_with_punctuation_needs_no_model(self):
        import dispatcher

        with patch.object(dispatcher, "speak") as speak:
            self.assertEqual(dispatcher.process("Thank you."), "EXIT_LOOP")
        speak.assert_called_once_with("You're welcome, sir.")

    def test_persona_does_not_claim_unavailable_tools(self):
        import jarvis_app

        prompt = jarvis_app.JarvisApp.create_jarvis_persona_prompt(None)
        self.assertIn("You are JARVIS (Just a Rather Very Intelligent System)", prompt)
        self.assertNotIn("Tony Stark", prompt)
        self.assertIn("available capabilities", prompt)
        self.assertIn("saves an unverified", prompt)
        self.assertIn("cannot inspect arbitrary tools", prompt)
        self.assertIn("entirely offline", prompt)

    def test_startup_displays_and_speaks_the_same_canonical_name(self):
        import jarvis_app

        app = object.__new__(jarvis_app.JarvisApp)
        app.page = SimpleNamespace()
        app.add_chat_message = Mock()
        with patch.object(jarvis_app, "speak") as speak:
            with patch.object(jarvis_app.threading, "Thread") as thread:
                app.setup_page()
                app.startup_sequence()

        greeting = jarvis_app.STARTUP_GREETING
        self.assertEqual(app.page.title, "JARVIS - Just a Rather Very Intelligent System")
        self.assertIn("I am JARVIS, Just a Rather Very Intelligent System", greeting)
        self.assertNotIn("J.A.R.V.I.S.", greeting)
        app.add_chat_message.assert_called_once_with("Jarvis", greeting, True)
        speak.assert_called_once_with(greeting)
        thread.return_value.start.assert_called_once()

    def test_idle_message_requires_microphone_button(self):
        source = (ROOT / "scripts" / "jarvis_app.py").read_text(encoding="utf-8")
        self.assertIn("Use the microphone button to resume.", source)
        self.assertNotIn("Say 'Jarvis' to wake me", source)

    def test_missing_memory_module_prevents_ui_start(self):
        module_path = ROOT / "scripts" / "jarvis_app.py"
        spec = importlib.util.spec_from_file_location("jarvis_app_missing_test", module_path)
        module = importlib.util.module_from_spec(spec)
        original_import = __import__

        def missing_memory(name, *args, **kwargs):
            if name == "obsidian_memory":
                raise ImportError("missing required memory module")
            return original_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=missing_memory):
            with self.assertRaisesRegex(ImportError, "required memory module"):
                spec.loader.exec_module(module)
