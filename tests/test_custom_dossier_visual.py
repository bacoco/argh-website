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


if __name__ == "__main__":
    unittest.main()
