"""
memory_system.py - JSON-based local memory system for JarvisAssistant
Provides persistent conversation memory and knowledge storage
"""

import json
import os
import time
from datetime import datetime
from pathlib import Path
import threading

class JarvisMemory:
    def __init__(self):
        """Initialize the memory system with portable structure"""

        # Get paths relative to portable structure
        self.base_path = Path(__file__).parent.parent
        self.memory_path = self.base_path / "memory"
        self.memory_path.mkdir(exist_ok=True)

        # Memory files
        self.conversation_file = self.memory_path / "conversations.json"
        self.knowledge_file = self.memory_path / "knowledge_base.json"
        self.preferences_file = self.memory_path / "user_preferences.json"

        # In-memory storage
        self.conversations = []
        self.knowledge_base = {}
        self.user_preferences = {}

        # Thread lock for safe file operations
        self.lock = threading.Lock()

        # Load existing data
        self._load_memory()

    def _load_memory(self):
        """Load existing memory from JSON files"""
        try:
            # Load conversations
            if self.conversation_file.exists():
                with open(self.conversation_file, 'r', encoding='utf-8') as f:
                    self.conversations = json.load(f)

            # Load knowledge base
            if self.knowledge_file.exists():
                with open(self.knowledge_file, 'r', encoding='utf-8') as f:
                    self.knowledge_base = json.load(f)

            # Load user preferences
            if self.preferences_file.exists():
                with open(self.preferences_file, 'r', encoding='utf-8') as f:
                    self.user_preferences = json.load(f)

            print(f"[Memory] Loaded {len(self.conversations)} conversations, {len(self.knowledge_base)} knowledge entries")

        except Exception as e:
            print(f"[Memory] Error loading memory: {e}")
            # Initialize with empty data if loading fails
            self.conversations = []
            self.knowledge_base = {}
            self.user_preferences = {}

    def _save_memory(self):
        """Save current memory to JSON files"""
        try:
            with self.lock:
                # Save conversations
                with open(self.conversation_file, 'w', encoding='utf-8') as f:
                    json.dump(self.conversations, f, indent=2, ensure_ascii=False)

                # Save knowledge base
                with open(self.knowledge_file, 'w', encoding='utf-8') as f:
                    json.dump(self.knowledge_base, f, indent=2, ensure_ascii=False)

                # Save user preferences
                with open(self.preferences_file, 'w', encoding='utf-8') as f:
                    json.dump(self.user_preferences, f, indent=2, ensure_ascii=False)

        except Exception as e:
            print(f"[Memory] Error saving memory: {e}")

    def add_conversation_exchange(self, user_input, assistant_response, session_id=None):
        """Add a conversation exchange to memory"""

        if session_id is None:
            session_id = datetime.now().strftime("%Y%m%d_%H%M%S")

        exchange = {
            "timestamp": datetime.now().isoformat(),
            "session_id": session_id,
            "user_input": user_input,
            "assistant_response": assistant_response,
            "type": "conversation"
        }

        self.conversations.append(exchange)

        # Keep only last 1000 conversations to prevent file bloat
        if len(self.conversations) > 1000:
            self.conversations = self.conversations[-1000:]

        # Save to disk
        self._save_memory()

    def add_knowledge(self, key, value, category="general"):
        """Add knowledge to the knowledge base"""

        knowledge_entry = {
            "value": value,
            "category": category,
            "timestamp": datetime.now().isoformat(),
            "access_count": 0
        }

        self.knowledge_base[key] = knowledge_entry
        self._save_memory()

    def get_knowledge(self, key):
        """Retrieve knowledge from the knowledge base"""

        if key in self.knowledge_base:
            # Increment access count
            self.knowledge_base[key]["access_count"] += 1
            self._save_memory()
            return self.knowledge_base[key]["value"]

        return None

    def search_knowledge(self, search_term, limit=5):
        """Search through knowledge base"""

        results = []
        search_term = search_term.lower()

        for key, entry in self.knowledge_base.items():
            if (search_term in key.lower() or
                search_term in str(entry["value"]).lower()):
                results.append({
                    "key": key,
                    "value": entry["value"],
                    "category": entry["category"]
                })

                if len(results) >= limit:
                    break

        return results

    def get_recent_conversations(self, limit=10):
        """Get recent conversation history"""
        return self.conversations[-limit:] if self.conversations else []

    def get_conversation_context(self, limit=5):
        """Get recent conversation context for AI prompts"""

        recent = self.get_recent_conversations(limit * 2)  # Get more to filter
        context_parts = []

        for conv in recent[-limit:]:
            context_parts.append(f"User: {conv['user_input']}")
            context_parts.append(f"Assistant: {conv['assistant_response']}")

        return "\n".join(context_parts)

    def set_user_preference(self, key, value):
        """Set user preference"""
        self.user_preferences[key] = {
            "value": value,
            "timestamp": datetime.now().isoformat()
        }
        self._save_memory()

    def get_user_preference(self, key, default=None):
        """Get user preference"""
        if key in self.user_preferences:
            return self.user_preferences[key]["value"]
        return default

    def clear_conversations(self):
        """Clear conversation history"""
        self.conversations = []
        self._save_memory()
        print("[Memory] Conversation history cleared")

    def clear_knowledge(self):
        """Clear knowledge base"""
        self.knowledge_base = {}
        self._save_memory()
        print("[Memory] Knowledge base cleared")

    def get_memory_stats(self):
        """Get memory system statistics"""
        return {
            "conversations": len(self.conversations),
            "knowledge_entries": len(self.knowledge_base),
            "user_preferences": len(self.user_preferences),
            "memory_path": str(self.memory_path),
            "last_conversation": self.conversations[-1]["timestamp"] if self.conversations else None
        }

    def export_memory(self, export_path):
        """Export all memory to a single JSON file"""
        export_data = {
            "export_timestamp": datetime.now().isoformat(),
            "conversations": self.conversations,
            "knowledge_base": self.knowledge_base,
            "user_preferences": self.user_preferences
        }

        with open(export_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)

        print(f"[Memory] Memory exported to {export_path}")

    def import_memory(self, import_path):
        """Import memory from a JSON file"""
        try:
            with open(import_path, 'r', encoding='utf-8') as f:
                import_data = json.load(f)

            # Merge imported data with existing data
            if "conversations" in import_data:
                self.conversations.extend(import_data["conversations"])

            if "knowledge_base" in import_data:
                self.knowledge_base.update(import_data["knowledge_base"])

            if "user_preferences" in import_data:
                self.user_preferences.update(import_data["user_preferences"])

            self._save_memory()
            print(f"[Memory] Memory imported from {import_path}")

        except Exception as e:
            print(f"[Memory] Error importing memory: {e}")

# Global instance for easy access
_memory_system = None

def get_memory_system():
    """Get global memory system instance"""
    global _memory_system
    if _memory_system is None:
        _memory_system = JarvisMemory()
    return _memory_system

def remember_conversation(user_input, assistant_response, session_id=None):
    """Convenience function for storing conversations"""
    memory = get_memory_system()
    memory.add_conversation_exchange(user_input, assistant_response, session_id)

def remember_knowledge(key, value, category="general"):
    """Convenience function for storing knowledge"""
    memory = get_memory_system()
    memory.add_knowledge(key, value, category)

def recall_knowledge(key):
    """Convenience function for retrieving knowledge"""
    memory = get_memory_system()
    return memory.get_knowledge(key)

def get_conversation_context(limit=5):
    """Convenience function for getting conversation context"""
    memory = get_memory_system()
    return memory.get_conversation_context(limit)

if __name__ == "__main__":
    # Test the memory system
    memory = JarvisMemory()

    # Test conversation storage
    memory.add_conversation_exchange("Hello", "Good day, sir. How may I assist you?")

    # Test knowledge storage
    memory.add_knowledge("user_name", "Tony Stark", "personal")

    # Test retrieval
    print("Knowledge test:", memory.get_knowledge("user_name"))
    print("Recent conversations:", memory.get_recent_conversations(1))
    print("Memory stats:", memory.get_memory_stats())