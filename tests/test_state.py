from unittest import TestCase

from narrator import GameNarrator
from state import GameState


class TestIntro(TestCase):
    narrator = GameNarrator()
    INTRO = narrator.intro()

    def test_intro(self):
        game_state = GameState(TestIntro.INTRO)
        history = game_state.history_so_far()
        self.assertGreater(len(history), 100)

    def test_update(self):
        game_state = GameState(TestIntro.INTRO)
        game_state.update(["She is now in outer space floating above the Earth"],
                          "Low-Earth Orbit", "Wants to land on the Moon!")
        history = game_state.history_so_far()

        self.assertIn("outer space", history)
        self.assertNotIn("Moon", history)
        self.assertNotIn("Low-Earth Orbit", history)
