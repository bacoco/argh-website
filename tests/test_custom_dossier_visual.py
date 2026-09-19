import tempfile
import unittest
from pathlib import Path
from unittest import mock

import build


class CustomDossierVisualTests(unittest.TestCase):
    def test_dossier_specific_teaching_card_wins_over_taxonomy_image(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            assets = root / "assets" / "illustrations"
            assets.mkdir(parents=True)
            (assets / "dossier-human-gate-timeout-640.jpg").write_bytes(b"image")
            entity = {"type": "dossier", "slug": "human-gate-timeout"}
            store = {
                "assignments": {"human-gate-timeout": "validation-preuves"},
                "place_by_id": {
                    "validation-preuves": {
                        "id": "validation-preuves",
                        "image": "/assets/illustrations/category-validation-evidence-320.jpg",
                        "label": {"fr": {"cuisine": "Contrôle", "expert": "Contrôle"},
                                  "en": {"kitchen": "Check", "expert": "Check"}},
                    }
                },
            }
            with mock.patch.object(build, "ROOT", root):
                image, _, _ = build.entity_visual(entity, store)
            self.assertEqual(
                image,
                "/assets/illustrations/dossier-human-gate-timeout-640.jpg",
            )


    def test_teaching_card_renders_full_width_and_accessible(self):
        entity = {
            "type": "dossier",
            "slug": "human-gate-timeout",
            "slots": [
                {"id": "hero", "heading": {"fr": {"cuisine": "Le chrono décide"}, "en": {}}, "body": []},
                {"id": "response", "heading": {}, "body": [{"fr": {"cuisine": "Le plat attend le chef."}, "en": {}}]},
                {"id": "lesson", "heading": {}, "body": [{"fr": {"cuisine": "Le silence ne vaut pas oui."}, "en": {}}]},
            ],
        }
        image = "/assets/illustrations/dossier-human-gate-timeout-640.webp"
        self.assertTrue(build.is_teaching_card_image(image))
        alt = build.teaching_alt(entity)
        self.assertIn("Le chrono décide", alt)
        self.assertIn("Le plat attend le chef.", alt)
        rendered = build.teaching_visual(image, alt)
        self.assertIn('class="argh-teaching-card"', rendered)
        self.assertIn('alt="Le chrono décide Le plat attend le chef. Le silence ne vaut pas oui."', rendered)


if __name__ == "__main__":
    unittest.main()
