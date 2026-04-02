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

    def test_lowercase_input_is_accepted(self):
        state = self._state(word="CAT")
        state.reset()

        result = state.guess("c")

        self.assertEqual(result, "correct")
        self.assertIn("C", state.guessed_letters)

    def test_non_letter_input_is_ignored(self):
        state = self._state()
        state.reset()

        result = state.guess("1")

        self.assertEqual(result, "ignored")
        self.assertEqual(state.wrong_guesses, 0)

    def test_repeated_letters_show_in_masked_word(self):
        state = self._state(word="LEVEL")
        state.reset()
        state.guess("L")

        self.assertEqual(state.masked_word, "L _ _ _ L")

    def test_difficulty_filters_word_pool(self):
        words = [
            ("CAT", "short"),
            ("KEYBOARD", "medium"),
            ("WATERMELON", "long"),
        ]
        state = HangmanState(word_list=words, chooser=lambda items: items[0], difficulty="hard")

        state.reset()

        self.assertEqual(state.word, "WATERMELON")

    def test_invalid_difficulty_raises(self):
        state = self._state()

        with self.assertRaises(ValueError):
            state.set_difficulty("expert")

    def test_theme_filters_word_pool(self):
        state = HangmanState(chooser=lambda items: items[0], theme="food")

        state.reset()

        self.assertIn(state.word, {"PIZZA", "SANDWICH", "CHOCOLATE", "STRAWBERRY", "PINEAPPLE", "WATERMELON"})

    def test_theme_and_difficulty_can_filter_together(self):
        words = [
            ("CAT", "short animal"),
            ("ELEPHANT", "long animal"),
            ("PIZZA", "food"),
        ]
        state = HangmanState(word_list=words, chooser=lambda items: items[0], theme="animals", difficulty="hard")

        state.reset()

        self.assertEqual(state.word, "ELEPHANT")

    def test_invalid_theme_raises(self):
        state = self._state()

        with self.assertRaises(ValueError):
            state.set_theme("sports")


if __name__ == "__main__":
    unittest.main()
