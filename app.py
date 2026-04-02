import tkinter as tk
from tkinter import messagebox
import random
import sys
import threading

from game_logic import HangmanState
from stats_store import StatsStore

# Try to import winsound for Windows
try:
    import winsound
    SOUND_AVAILABLE = True
except ImportError:
    SOUND_AVAILABLE = False

class HangmanGame:
    def __init__(self, root):
        self.root = root
        self.root.title("Hangman Game")
        self.root.geometry("1000x700")
        self.root.resizable(False, False)
        
        # Create gradient background effect
        self.root.configure(bg='#6B7FCC')
        
        self.state = HangmanState(max_wrong=6, difficulty='medium', theme='all')
        self.stats_store = StatsStore("stats.json")
        self.stats = self.stats_store.load()
        self.player_name = self.stats.get('player_name', 'Player')

        self.turn_seconds = 15
        self.turn_time_left = self.turn_seconds
        self.timer_after_id = None
        self.hints_per_round = 2
        self.hints_remaining = self.hints_per_round
        self.hint_penalties = 0
        
        # Pre-calculate hangman drawing coordinates
        self.hangman_parts = [
            ('oval', 220, 120, 280, 180),  # Head
            ('line', 250, 180, 250, 280),  # Body
            ('line', 250, 210, 210, 250),  # Left arm
            ('line', 250, 210, 290, 250),  # Right arm
            ('line', 250, 280, 220, 340),  # Left leg
            ('line', 250, 280, 280, 340),  # Right leg
        ]
        
        self.setup_ui()
        self.new_game()

    def _unlock_achievement(self, label):
        if label not in self.stats['achievements']:
            self.stats['achievements'].append(label)
            return True
        return False

    def _round_score(self, won, wrong_guesses):
        if not won:
            return 0
        base = max(self.state.max_wrong - wrong_guesses, 0) * 10
        difficulty_bonus = {'easy': 5, 'medium': 10, 'hard': 20}[self.state.difficulty]
        theme_bonus = 2 if self.state.theme != 'all' else 0
        score = base + difficulty_bonus + theme_bonus - (self.hint_penalties * 5)
        return max(score, 0)

    def _show_toast(self, text, bg='#2C3E50'):
        toast = tk.Toplevel(self.root)
        toast.overrideredirect(True)
        toast.configure(bg=bg)
        toast.attributes('-topmost', True)

        label = tk.Label(toast, text=text, fg='white', bg=bg, font=('Arial', 10, 'bold'))
        label.pack(padx=12, pady=8)

        x = self.root.winfo_x() + 620
        y = self.root.winfo_y() + 40
        toast.geometry(f"+{x}+{y}")
        toast.after(1600, toast.destroy)
    
    def play_sound_async(self, sound_type):
        """Play sound in a separate thread to avoid blocking UI"""
        if SOUND_AVAILABLE and sys.platform == 'win32':
            threading.Thread(target=self._play_sound, args=(sound_type,), daemon=True).start()
        else:
            self.root.bell()
    
    def _play_sound(self, sound_type):
        """Internal method to play sounds"""
        try:
            if sound_type == 'correct':
                winsound.Beep(800, 100)
            elif sound_type == 'wrong':
                winsound.Beep(300, 200)
            elif sound_type == 'click':
                winsound.Beep(600, 50)
            elif sound_type == 'win':
                for freq, dur in [(523, 120), (659, 120), (784, 200)]:
                    winsound.Beep(freq, dur)
            elif sound_type == 'lose':
                for freq, dur in [(494, 150), (440, 150), (392, 150), 
                                 (349, 150), (294, 250), (262, 400)]:
                    winsound.Beep(freq, dur)
        except:
            pass
    
    def setup_ui(self):
        # Main white container
        container = tk.Frame(self.root, bg='white', bd=0)
        container.place(relx=0.5, rely=0.5, anchor='center', width=900, height=550)
        
        container_inner = tk.Frame(container, bg='white')
        container_inner.pack(expand=True, fill='both', padx=30, pady=30)
        
        # Left side - Canvas
        left_frame = tk.Frame(container_inner, bg='white')
        left_frame.pack(side='left', padx=(0, 40))
        
        self.canvas = tk.Canvas(left_frame, width=350, height=400, 
                               bg='white', highlightthickness=0)
        self.canvas.pack()
        
        tk.Label(left_frame, text="HANGMAN GAME", 
                font=('Arial', 18, 'bold'), bg='white', 
                fg='#2C3E50').pack(pady=(20, 0))
        
        # Right side - Game info and letters
        right_frame = tk.Frame(container_inner, bg='white')
        right_frame.pack(side='right', fill='both', expand=True)

        controls_frame = tk.Frame(right_frame, bg='white')
        controls_frame.pack(fill='x', pady=(0, 10))

        tk.Label(controls_frame, text="Name:",
             font=('Arial', 11, 'bold'), bg='white', fg='#2C3E50').pack(side='left')

        self.name_var = tk.StringVar(value=self.player_name)
        self.name_entry = tk.Entry(controls_frame, textvariable=self.name_var, width=12,
                       font=('Arial', 10), relief='solid', bd=1)
        self.name_entry.pack(side='left', padx=(6, 6))

        save_name_btn = tk.Button(controls_frame, text="Save",
                      font=('Arial', 9, 'bold'), bg='#2C3E50', fg='white',
                      relief='flat', cursor='hand2', command=self.on_player_name_save)
        save_name_btn.pack(side='left', padx=(0, 12))

        tk.Label(controls_frame, text="Difficulty:",
                 font=('Arial', 11, 'bold'), bg='white', fg='#2C3E50').pack(side='left')

        self.difficulty_var = tk.StringVar(value='Medium')
        difficulty_menu = tk.OptionMenu(
            controls_frame,
            self.difficulty_var,
            'Easy',
            'Medium',
            'Hard',
            command=self.on_difficulty_change,
        )
        difficulty_menu.config(bg='white', fg='#2C3E50', relief='solid', bd=1, width=8)
        difficulty_menu.pack(side='left', padx=(8, 18))

        tk.Label(controls_frame, text="Theme:",
                 font=('Arial', 11, 'bold'), bg='white', fg='#2C3E50').pack(side='left')

        self.theme_var = tk.StringVar(value='All')
        theme_menu = tk.OptionMenu(
            controls_frame,
            self.theme_var,
            'All',
            'Animals',
            'Tech',
            'Nature',
            'Food',
            command=self.on_theme_change,
        )
        theme_menu.config(bg='white', fg='#2C3E50', relief='solid', bd=1, width=9)
        theme_menu.pack(side='left', padx=(8, 18))

        self.timer_var = tk.BooleanVar(value=bool(self.stats.get('timer_enabled', False)))
        timer_toggle = tk.Checkbutton(controls_frame, text="Timer",
                          variable=self.timer_var,
                          command=self.on_timer_toggle,
                          bg='white', fg='#2C3E50',
                          font=('Arial', 10, 'bold'),
                          activebackground='white')
        timer_toggle.pack(side='left', padx=(0, 12))

        self.stats_label = tk.Label(controls_frame, text="",
                                    font=('Arial', 10), bg='white', fg='#34495E')
        self.stats_label.pack(side='left')
        
        # Word display
        self.word_label = tk.Label(right_frame, text="", 
                                   font=('Arial', 36, 'bold'),
                                   bg='white', fg='#2C3E50',
                                   justify='center')
        self.word_label.pack(pady=(0, 20))

        self.status_label = tk.Label(right_frame, text="Pick a letter to start!",
                         font=('Arial', 11), bg='white', fg='#566573')
        self.status_label.pack(pady=(0, 12))
        
        # Hint display
        self.hint_label = tk.Label(right_frame, text="", 
                                   font=('Arial', 12),
                                   bg='white', fg='#555',
                                   wraplength=500, justify='left')
        self.hint_label.pack(pady=(0, 10))
        
        # Incorrect guesses counter
        self.counter_label = tk.Label(right_frame, text="Incorrect: 0/6", 
                                      font=('Arial', 13, 'bold'),
                                      bg='white', fg='#E74C3C')
        self.counter_label.pack(pady=(0, 6))

        self.timer_label = tk.Label(right_frame, text="Timer: Off",
                        font=('Arial', 11, 'bold'),
                        bg='white', fg='#D35400')
        self.timer_label.pack(pady=(0, 12))

        # Guessed letters display
        self.guessed_label = tk.Label(right_frame, text="Guessed: -",
                          font=('Arial', 12),
                          bg='white', fg='#34495E',
                          wraplength=500, justify='left')
        self.guessed_label.pack(pady=(0, 16))

        self.achievements_label = tk.Label(right_frame, text="Achievements: None yet",
                           font=('Arial', 10), bg='white', fg='#2C3E50',
                           wraplength=500, justify='left')
        self.achievements_label.pack(pady=(0, 8))

        self.leaderboard_label = tk.Label(right_frame, text="Leaderboard: No scores yet",
                          font=('Arial', 10), bg='white', fg='#2C3E50',
                          wraplength=500, justify='left')
        self.leaderboard_label.pack(pady=(0, 12))

        self.history_label = tk.Label(right_frame, text="Recent rounds: None",
                          font=('Arial', 10), bg='white', fg='#2C3E50',
                          wraplength=500, justify='left')
        self.history_label.pack(pady=(0, 12))
        
        # Letter buttons - optimized grid creation
        letters_frame = tk.Frame(right_frame, bg='white')
        letters_frame.pack()
        
        self.letter_buttons = {}
        alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        
        # Create all buttons at once
        for i, letter in enumerate(alphabet):
            btn = tk.Button(letters_frame, text=letter, width=3, height=1,
                          font=('Arial', 13, 'bold'),
                          bg='#6B7FCC', fg='white',
                          activebackground='#5A6EBB',
                          relief='flat',
                          cursor='hand2',
                          command=lambda l=letter: self.guess_letter(l))
            btn.grid(row=i // 9, column=i % 9, padx=3, pady=3)
            self.letter_buttons[letter] = btn

        action_frame = tk.Frame(right_frame, bg='white')
        action_frame.pack(pady=(10, 0))

        self.hint_button = tk.Button(action_frame, text="Hint (2)",
                         font=('Arial', 11, 'bold'),
                         bg='#D68910', fg='white',
                         activebackground='#B9770E',
                         relief='flat', cursor='hand2',
                         command=self.use_hint)
        self.hint_button.pack(side='left', padx=(0, 10))

        self.restart_button = tk.Button(action_frame, text="Restart",
                                        font=('Arial', 11, 'bold'),
                                        bg='#2C3E50', fg='white',
                                        activebackground='#1F2D3A',
                                        relief='flat', cursor='hand2',
                                        command=self.new_game)
        self.restart_button.pack(side='left')
        
        # Bind keyboard input
        self.root.bind('<Key>', self.on_key_press)

    def on_difficulty_change(self, choice):
        level = (choice or "Medium").strip().lower()
        self.state.set_difficulty(level)
        self.new_game()
        self.status_label.config(text=f"Difficulty set to {choice}. Good luck!")

    def on_theme_change(self, choice):
        level = (choice or "All").strip().lower()
        self.state.set_theme(level)
        self.new_game()
        self.status_label.config(text=f"Theme set to {choice}.")

    def on_player_name_save(self):
        entered = self.name_var.get().strip()
        if not entered:
            entered = 'Player'
        self.player_name = entered[:20]
        self.name_var.set(self.player_name)
        self.stats['player_name'] = self.player_name
        self.stats_store.save(self.stats)
        self.status_label.config(text=f"Player set to {self.player_name}.")

    def on_timer_toggle(self):
        self.stats['timer_enabled'] = bool(self.timer_var.get())
        self.stats_store.save(self.stats)
        if self.timer_var.get() and self.state.game_active:
            self._start_turn_timer(reset=True)
        else:
            self._cancel_turn_timer()
            self.timer_label.config(text="Timer: Off")

    def _cancel_turn_timer(self):
        if self.timer_after_id is not None:
            self.root.after_cancel(self.timer_after_id)
            self.timer_after_id = None

    def _start_turn_timer(self, reset=False):
        if not self.timer_var.get() or not self.state.game_active:
            self.timer_label.config(text="Timer: Off")
            return
        self._cancel_turn_timer()
        if reset:
            self.turn_time_left = self.turn_seconds
        self.timer_label.config(text=f"Timer: {self.turn_time_left}s")
        self.timer_after_id = self.root.after(1000, self._tick_timer)

    def _tick_timer(self):
        self.timer_after_id = None
        if not self.timer_var.get() or not self.state.game_active:
            self.timer_label.config(text="Timer: Off")
            return

        self.turn_time_left -= 1
        if self.turn_time_left <= 0:
            self.handle_timeout()
            return

        self.timer_label.config(text=f"Timer: {self.turn_time_left}s")
        self.timer_after_id = self.root.after(1000, self._tick_timer)

    def handle_timeout(self):
        result = self.state.add_wrong_guess()
        if result == 'ignored':
            return

        self.play_sound_async('wrong')
        self.draw_hangman(self.state.wrong_guesses)
        self.counter_label.config(text=f"Incorrect: {self.state.wrong_guesses}/{self.state.max_wrong}")
        self.status_label.config(text="Time up! You lost one attempt.")
        if result == 'lost':
            self.game_over(False)
            return
        self.turn_time_left = self.turn_seconds
        self._start_turn_timer(reset=False)

    def update_history_display(self):
        rows = self.stats.get('round_history', [])[:5]
        if not rows:
            self.history_label.config(text="Recent rounds: None")
            return
        parts = []
        for row in rows:
            parts.append(
                f"{row['word']} {row['result']} {row['score']} pts ({row['difficulty'].title()}/{row['theme'].title()})"
            )
        self.history_label.config(text="Recent rounds: " + ' | '.join(parts))

    def update_stats_display(self):
        played = self.stats['games_played']
        wins = self.stats['wins']
        best = self.stats['best_streak']
        self.stats_label.config(text=f"Played: {played}  Wins: {wins}  Best Streak: {best}")

        recent_badges = self.stats['achievements'][-3:]
        if recent_badges:
            badge_text = ', '.join(recent_badges)
            self.achievements_label.config(text=f"Achievements: {badge_text}")
        else:
            self.achievements_label.config(text="Achievements: None yet")

        board = self.stats['leaderboard'][:3]
        if board:
            rows = [
                f"{idx + 1}. {entry['name']} {entry['score']} pts ({entry['difficulty'].title()}/{entry['theme'].title()})"
                for idx, entry in enumerate(board)
            ]
            self.leaderboard_label.config(text="Leaderboard: " + ' | '.join(rows))
        else:
            self.leaderboard_label.config(text="Leaderboard: No scores yet")
        self.update_history_display()

    def record_game_result(self, won, wrong_guesses):
        self.stats['games_played'] += 1
        unlocked_now = []
        score = 0

        if won:
            self.stats['wins'] += 1
            self.stats['current_streak'] += 1
            self.stats['best_streak'] = max(self.stats['best_streak'], self.stats['current_streak'])

            score = self._round_score(won=True, wrong_guesses=wrong_guesses)
            self.stats['leaderboard'].append(
                {
                    'name': self.player_name,
                    'score': score,
                    'difficulty': self.state.difficulty,
                    'theme': self.state.theme,
                }
            )
            self.stats['leaderboard'].sort(key=lambda item: item['score'], reverse=True)
            self.stats['leaderboard'] = self.stats['leaderboard'][:10]

            if self.stats['wins'] == 1 and self._unlock_achievement('First Win'):
                unlocked_now.append('First Win')
            if self.stats['current_streak'] >= 3 and self._unlock_achievement('Hat Trick'):
                unlocked_now.append('Hat Trick')
            if wrong_guesses == 0 and self._unlock_achievement('Perfect Round'):
                unlocked_now.append('Perfect Round')
            if self.state.difficulty == 'hard' and self._unlock_achievement('Hard Mode Hero'):
                unlocked_now.append('Hard Mode Hero')
            if self.state.theme != 'all' and self._unlock_achievement('Theme Explorer'):
                unlocked_now.append('Theme Explorer')
        else:
            self.stats['losses'] += 1
            self.stats['current_streak'] = 0

        history_row = {
            'word': self.state.word,
            'result': 'Win' if won else 'Loss',
            'score': score,
            'difficulty': self.state.difficulty,
            'theme': self.state.theme,
        }
        self.stats['round_history'].insert(0, history_row)
        self.stats['round_history'] = self.stats['round_history'][:20]

        self.stats_store.save(self.stats)
        self.update_stats_display()
        return unlocked_now, score
    
    def on_key_press(self, event):
        """Handle keyboard input"""
        if not self.state.game_active:
            return
        
        letter = event.char.upper()
        if letter in self.letter_buttons and self.letter_buttons[letter]['state'] == 'normal':
            self.guess_letter(letter)
    
    def draw_hangman(self, stage):
        """Optimized drawing - only update what changed"""
        self.canvas.delete('all')
        
        # Draw gallows - static parts
        self.canvas.create_line(50, 380, 300, 380, width=4, fill='#2C3E50')
        self.canvas.create_line(100, 380, 100, 80, width=4, fill='#2C3E50')
        self.canvas.create_line(100, 80, 250, 80, width=4, fill='#2C3E50')
        self.canvas.create_line(100, 120, 140, 80, width=3, fill='#2C3E50')
        self.canvas.create_line(250, 80, 250, 120, width=3, fill='#2C3E50')
        
        # Draw hangman parts based on stage
        for i in range(min(stage, len(self.hangman_parts))):
            part = self.hangman_parts[i]
            if part[0] == 'oval':
                self.canvas.create_oval(part[1], part[2], part[3], part[4], 
                                       width=3, outline='#2C3E50')
            else:  # line
                self.canvas.create_line(part[1], part[2], part[3], part[4], 
                                       width=3, fill='#2C3E50')
    
    def new_game(self):
        self._cancel_turn_timer()
        self.state.reset()
        self.hints_remaining = self.hints_per_round
        self.hint_penalties = 0
        self.turn_time_left = self.turn_seconds
        
        # Reset canvas
        self.draw_hangman(0)
        
        # Reset letter buttons efficiently
        for btn in self.letter_buttons.values():
            btn.config(state='normal', bg='#6B7FCC')
        
        # Update displays
        self.update_word_display()
        self.hint_label.config(text=f"Hint: {self.state.hint}")
        self.counter_label.config(text=f"Incorrect: {self.state.wrong_guesses}/{self.state.max_wrong}")
        self.guessed_label.config(text="Guessed: -")
        self.status_label.config(text="Pick a letter to start!")
        self.hint_button.config(text=f"Hint ({self.hints_remaining})", state='normal')
        self._start_turn_timer(reset=True)
        self.update_stats_display()

    def use_hint(self):
        if not self.state.game_active:
            return
        if self.hints_remaining <= 0:
            self.status_label.config(text="No hints left this round.")
            return

        candidates = [c for c in set(self.state.word) if c not in self.state.guessed_letters]
        if not candidates:
            self.status_label.config(text="No hidden letters left for a hint.")
            return

        letter = random.choice(candidates)
        reveal_result = self.state.guess(letter)
        self.hints_remaining -= 1
        self.hint_penalties += 1
        self.hint_button.config(text=f"Hint ({self.hints_remaining})")

        if letter in self.letter_buttons:
            self.letter_buttons[letter].config(state='disabled', bg='#95A5D8')

        penalty_result = self.state.add_wrong_guess()
        self.play_sound_async('correct')
        if penalty_result != 'ignored':
            self.play_sound_async('wrong')

        self.draw_hangman(self.state.wrong_guesses)
        self.update_word_display()
        self.counter_label.config(text=f"Incorrect: {self.state.wrong_guesses}/{self.state.max_wrong}")
        guessed_text = ' '.join(sorted(self.state.guessed_letters))
        self.guessed_label.config(text=f"Guessed: {guessed_text}")

        if reveal_result == 'won':
            self.status_label.config(text=f"Hint revealed '{letter}'. You solved it!")
            self.game_over(True)
            return
        if penalty_result == 'lost':
            self.status_label.config(text="Hint cost your final attempt.")
            self.game_over(False)
            return

        if self.hints_remaining <= 0:
            self.hint_button.config(state='disabled')
        self.status_label.config(text=f"Hint revealed '{letter}' but cost 1 attempt.")
        self.turn_time_left = self.turn_seconds
        self._start_turn_timer(reset=False)
    
    def guess_letter(self, letter):
        result = self.state.guess(letter)
        if result == 'ignored':
            return
        
        # Play click sound asynchronously
        self.play_sound_async('click')
        
        self.letter_buttons[letter].config(state='disabled', bg='#95A5D8')

        if result == 'wrong':
            self.play_sound_async('wrong')
            self.draw_hangman(self.state.wrong_guesses)
            self.counter_label.config(text=f"Incorrect: {self.state.wrong_guesses}/{self.state.max_wrong}")
            self.status_label.config(text=f"Nope, '{letter}' is not in the word.")
        elif result == 'correct':
            self.play_sound_async('correct')
            self.status_label.config(text=f"Nice! '{letter}' is in the word.")
        
        self.update_word_display()
        guessed_text = ' '.join(sorted(self.state.guessed_letters))
        self.guessed_label.config(text=f"Guessed: {guessed_text}")

        if result == 'lost':
            self.status_label.config(text="Out of attempts. Better luck next round.")
            self.game_over(False)
            return
        if result == 'won':
            self.status_label.config(text="Great job, you solved it!")
            self.game_over(True)
            return
        self.turn_time_left = self.turn_seconds
        self._start_turn_timer(reset=False)
    
    def update_word_display(self):
        """Optimized word display update"""
        self.word_label.config(text=self.state.masked_word)
    
    def game_over(self, won):
        self._cancel_turn_timer()
        self.state.game_active = False
        unlocked_now, score = self.record_game_result(won, self.state.wrong_guesses)
        
        # Disable all buttons at once
        for btn in self.letter_buttons.values():
            btn.config(state='disabled')
        self.hint_button.config(state='disabled')
        self.timer_label.config(text="Timer: Off")

        for badge in unlocked_now:
            self._show_toast(f"Achievement unlocked: {badge}", bg='#117A65')
        
        if won:
            self.play_sound_async('win')
            self.root.after(450, lambda: self._show_game_over_dialog(True, unlocked_now, score))
        else:
            self.play_sound_async('lose')
            self.root.after(1300, lambda: self._show_game_over_dialog(False, unlocked_now, score))
    
    def _show_game_over_dialog(self, won, unlocked_now, score):
        """Show game over dialog after sound completes"""
        badge_line = ""
        if unlocked_now:
            badge_line = "\nUnlocked: " + ', '.join(unlocked_now)

        score_line = f"\nScore: {score}"

        if won:
            result = messagebox.askyesno("Congratulations", 
                              f"You won! The word was: {self.state.word}{score_line}{badge_line}\n\nPlay again?")
        else:
            result = messagebox.askyesno("Game Over", 
                              f"You lost! The word was: {self.state.word}{score_line}{badge_line}\n\nPlay again?")
        
        if result:
            self.new_game()
        else:
            self.root.quit()

if __name__ == "__main__":
    root = tk.Tk()
    game = HangmanGame(root)
    root.mainloop()