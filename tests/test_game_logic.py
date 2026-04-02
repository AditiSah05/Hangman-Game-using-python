import unittest

from game_logic import HangmanState


class HangmanStateTests(unittest.TestCase):
    def _state(self, word="PYTHON", hint="A language", max_wrong=6):
        return HangmanState(
            word_list=[(word, hint)],
            max_wrong=max_wrong,
            chooser=lambda items: items[0],
        )

    def test_reset_initializes_expected_values(self):
        state = self._state()
        state.reset()

        self.assertEqual(state.word, "PYTHON")
        self.assertEqual(state.hint, "A language")
        self.assertEqual(state.wrong_guesses, 0)
        self.assertTrue(state.game_active)
        self.assertEqual(state.masked_word, "_ _ _ _ _ _")

    def test_correct_guess_returns_correct(self):
        state = self._state()
        state.reset()

        result = state.guess("P")

        self.assertEqual(result, "correct")
        self.assertIn("P", state.guessed_letters)
        self.assertEqual(state.wrong_guesses, 0)

    def test_wrong_guess_increments_counter(self):
        state = self._state()
        state.reset()

        result = state.guess("Z")

        self.assertEqual(result, "wrong")
        self.assertEqual(state.wrong_guesses, 1)

    def test_duplicate_guess_is_ignored(self):
        state = self._state()
        state.reset()
        state.guess("P")

        result = state.guess("P")

        self.assertEqual(result, "ignored")
        self.assertEqual(state.wrong_guesses, 0)

    def test_winning_guess_returns_won_and_stops_game(self):
        state = self._state(word="AB")
        state.reset()
        state.guess("A")

        result = state.guess("B")

        self.assertEqual(result, "won")
        self.assertFalse(state.game_active)

    def test_losing_guess_returns_lost_and_stops_game(self):
        state = self._state(max_wrong=1)
        state.reset()

        result = state.guess("Z")

        self.assertEqual(result, "lost")
        self.assertFalse(state.game_active)


if __name__ == "__main__":
    unittest.main()
