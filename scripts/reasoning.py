"""
reasoning.py - LLaMA 3 reasoning engine using llama.cpp
Replaces Ollama dependency with direct llama.cpp Windows binary calls
"""

import os
import subprocess
import json
import threading
import time
from pathlib import Path

class LlamaReasoning:
    def __init__(self, model_path=None, context_size=4096):
        """Initialize LLaMA reasoning engine with llama.cpp"""

        # Get paths relative to portable structure
        self.base_path = Path(__file__).parent.parent
        self.bin_path = self.base_path / "bin"
        self.models_path = self.base_path / "models"

        # Default model path
        if model_path is None:
            model_path = self.models_path / "llama3-8b-q4.gguf"

        self.model_path = Path(model_path)
        self.context_size = context_size
        self.llama_exe = self.bin_path / "llama-cli.exe"

        # Conversation memory
        self.conversation_history = []

        self._validate_setup()

    def _validate_setup(self):
        """Validate that llama.cpp binary and model exist"""
        if not self.llama_exe.exists():
            raise FileNotFoundError(f"llama.cpp binary not found at {self.llama_exe}")

        if not self.model_path.exists():
            raise FileNotFoundError(f"Model not found at {self.model_path}")

    def generate_response(self, prompt, system_prompt=None, max_tokens=512, temperature=0.7):
        """
        Generate response using llama.cpp

        Args:
            prompt: User input text
            system_prompt: Optional system instruction
            max_tokens: Maximum response length
            temperature: Creativity level (0.0-1.0)

        Returns:
            Generated response text
        """

        # Build full prompt with conversation history
        full_prompt = self._build_prompt(prompt, system_prompt)

        # Construct llama.cpp command - simplified for stability testing
        cmd = [
            str(self.llama_exe),
            "-m", str(self.model_path),
            "-p", full_prompt,
            "-n", str(max_tokens),
            "--temp", str(temperature),
            "-c", "1024",  # Smaller context for testing
            "-ngl", "33",  # All layers to GPU (test if this works)
            "--threads", "4",  # Conservative threading
            "--batch-size", "256",  # Smaller batch for testing
            "--no-warmup",  # Skip warmup
            "-v",  # Verbose output to see what's happening
        ]

        try:
            # Run llama.cpp and capture output
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                timeout=30  # Reduced timeout to prevent hanging
            )

            if result.returncode == 0:
                response = result.stdout.strip()

                # Parse response to extract only the assistant's part
                # Look for "Assistant:" and take everything after it
                if "Assistant:" in response:
                    response = response.split("Assistant:")[-1].strip()

                # Remove various output artifacts
                response = response.replace("> EOF by user", "").strip()
                response = response.replace("assistant", "", 1).strip()

                # Remove any remaining prompt echoing or system text
                lines = response.split('\n')
                clean_lines = []
                for line in lines:
                    line = line.strip()
                    if line and not line.startswith('System:') and not line.startswith('User:') and not line.startswith('Assistant:'):
                        clean_lines.append(line)

                response = ' '.join(clean_lines).strip()

                # Add to conversation history
                self.conversation_history.append({
                    "role": "user",
                    "content": prompt
                })
                self.conversation_history.append({
                    "role": "assistant",
                    "content": response
                })

                # Keep history manageable (last 10 exchanges)
                if len(self.conversation_history) > 20:
                    self.conversation_history = self.conversation_history[-20:]

                return response
            else:
                error_msg = result.stderr or "Unknown llama.cpp error"
                print(f"[LlamaReasoning] Error: {error_msg}")
                # Return JSON-compatible response for dispatcher compatibility
                if system_prompt and "JSON" in system_prompt:
                    return '{"intent": "unrecognized", "entities": {}}'
                return "I'm having trouble thinking right now. Please try again."

        except subprocess.TimeoutExpired:
            print("[LlamaReasoning] Response generation timed out")
            # Return a JSON-compatible response for dispatcher compatibility
            if system_prompt and "JSON" in system_prompt:
                return '{"intent": "unrecognized", "entities": {}}'
            return "I apologize, but my response is taking longer than expected. Please try rephrasing your request."
        except Exception as e:
            print(f"[LlamaReasoning] Unexpected error: {e}")
            # Return JSON-compatible response for dispatcher compatibility
            if system_prompt and "JSON" in system_prompt:
                return '{"intent": "unrecognized", "entities": {}}'
            return "I encountered an unexpected issue. Please try again."

    def _build_prompt(self, user_input, system_prompt=None):
        """Build complete prompt with system instruction and conversation history"""

        if system_prompt is None:
            system_prompt = """You are JARVIS, an intelligent AI assistant. You are helpful, precise, and have a subtle wit.
Address the user respectfully and provide clear, accurate responses. Keep responses concise but informative."""

        # Start with system prompt
        prompt_parts = [f"System: {system_prompt}\n"]

        # Add recent conversation history
        for msg in self.conversation_history[-6:]:  # Last 3 exchanges
            role = msg["role"].title()
            content = msg["content"]
            prompt_parts.append(f"{role}: {content}\n")

        # Add current user input
        prompt_parts.append(f"User: {user_input}\n")
        prompt_parts.append("Assistant:")

        return "".join(prompt_parts)

    def clear_conversation(self):
        """Clear conversation history"""
        self.conversation_history = []
        print("[LlamaReasoning] Conversation history cleared")

    def get_conversation_summary(self):
        """Get summary of current conversation"""
        if not self.conversation_history:
            return "No conversation history"

        return f"Conversation has {len(self.conversation_history)} messages"

# Global instance for easy access
_reasoning_engine = None

def get_reasoning_engine():
    """Get global reasoning engine instance"""
    global _reasoning_engine
    if _reasoning_engine is None:
        _reasoning_engine = LlamaReasoning()
    return _reasoning_engine

def generate_response(prompt, system_prompt=None, **kwargs):
    """Convenience function for generating responses"""
    engine = get_reasoning_engine()
    return engine.generate_response(prompt, system_prompt, **kwargs)

if __name__ == "__main__":
    # Test the reasoning engine
    engine = LlamaReasoning()
    response = engine.generate_response("Hello, what's your name?")
    print(f"Response: {response}")