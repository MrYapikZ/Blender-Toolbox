import json
from pathlib import Path


class JSONManager:
    """A utility class for loading and saving JSON files."""

    @staticmethod
    def load_json(filepath):
        """Load JSON data from the specified filepath."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data
        except Exception as e:
            print(f"Error loading JSON from {filepath}: {e}")
            return None

    @staticmethod
    def save_json(data, filepath):
        """Save data as JSON to the specified filepath."""
        try:
            Path(filepath).parent.mkdir(parents=True, exist_ok=True)
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            print(f"Data successfully saved to {filepath}")
        except Exception as e:
            print(f"Error saving JSON to {filepath}: {e}")
