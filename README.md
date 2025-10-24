# Hangman Game

A classic word-guessing game implemented in Python using Tkinter for the graphical user interface. Test your vocabulary skills by guessing letters to reveal a hidden word before the hangman drawing is complete!

## Features

- **Interactive GUI**: Clean, modern interface with a centered white container on a gradient background.
- **Word Hints**: Each word comes with a helpful hint to guide your guesses.
- **Sound Effects**: Comprehensive audio feedback including:
  - Click sound for button presses and keyboard input
  - Success tone for correct letter guesses
  - Error tone for incorrect guesses
  - Victory melody when winning the game
  - Defeat sequence when losing (Windows only; falls back to system bell on other platforms)
- **Keyboard Support**: Full keyboard input support - press any letter key (A-Z) to make guesses.
- **Optimized Performance**: Efficient rendering and state management for smooth gameplay.
- **Word Database**: 50+ curated words with hints covering various categories including animals, objects, places, and more.

## Requirements

- Python 3.6 or higher
- Tkinter (usually included with Python installations)
- Windows OS for sound effects (optional; falls back to system bell on other platforms)

## Installation

1. Ensure Python 3.6+ is installed on your system.
2. Download or clone the repository containing `app.py`.
3. No additional dependencies are required beyond standard Python libraries.

## How to Run

1. Open a terminal or command prompt.
2. Navigate to the directory containing `app.py`.
3. Run the following command:

   ```bash
   python app.py
   ```

4. The game window will open. Start playing by clicking letter buttons or using keyboard input.

## Controls

- **Mouse**: Click on letter buttons to make guesses.
- **Keyboard**: Press any letter key (A-Z) to guess that letter.
- **Game Over**: Choose to play again or exit when the game ends.

## Gameplay

- Guess letters to reveal the hidden word.
- You have 6 incorrect guesses before the game ends.
- Use the hint to help identify the word.
- Win by guessing all letters correctly before running out of attempts.


## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests for improvements.

---

Enjoy the game and happy guessing!
