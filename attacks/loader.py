
"""Load and filter attack cases from a YAML file."""

from pathlib import Path
import yaml


class Attack(dict):
    """Allow attack fields to be accessed by key or attribute."""

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            if name == "is_multiturn":
                return bool(self.get("turns"))
            raise AttributeError(name) from None

    def get_all_texts(self):
        """Return all attack prompts in execution order."""
        if self.get("turns"):
            return [
                turn["text"] if isinstance(turn, dict) else turn
                for turn in self["turns"]
            ]

        return [self["text"]]


class AttackLibrary(list):
    """Load, store, and filter attack cases."""

    @classmethod
    def from_yaml(cls, path):
        with Path(path).open("r", encoding="utf-8") as file:
            data = yaml.safe_load(file) or {}

        attacks = data.get("attacks", [])
        return cls(Attack(item) for item in attacks)

    @property
    def categories(self):
        return sorted({attack["category"] for attack in self})

    def filter(self, categories=None, severities=None):
        """Return attacks matching the optional category and severity filters."""
        selected = self

        if categories:
            selected = [
                attack for attack in selected
                if attack.get("category") in categories
            ]

        if severities:
            selected = [
                attack for attack in selected
                if attack.get("severity") in severities
            ]

        return AttackLibrary(selected)
