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

        def reply(**_):
            observed.append(app.activity_text.value)
            return "Doing well, thank you."

        engine.generate_response.side_effect = reply
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
            ["Checking your request locally...", "Generating a reply locally..."],
        )
        self.assertEqual(app.activity_text.value, "")
        get_context.assert_called_once_with(3, query="Checking in")
        remember.assert_called_once_with("Checking in", "Doing well, thank you.")

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

    def test_persona_does_not_claim_unavailable_tools(self):
        import jarvis_app

        prompt = jarvis_app.JarvisApp.create_jarvis_persona_prompt(None)
        self.assertIn("available capabilities", prompt)
        self.assertIn("saves a local note", prompt)
        self.assertIn("cannot inspect arbitrary tools", prompt)
        self.assertIn("entirely offline", prompt)

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
