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
        self.root.geometry("1100x620")
        self.root.minsize(1000, 560)
        self.root.resizable(True, True)
        
        self.root.configure(bg='#ECECEC')
        
        self.stats_store = StatsStore("stats.json")
        self.stats = self.stats_store.load()
        self.player_name = self.stats.get('player_name', 'Player')

        custom_words = [(item['word'], item['hint']) for item in self.stats.get('custom_words', [])]
        difficulty = self.stats.get('default_difficulty', 'medium')
        theme = self.stats.get('default_theme', 'all')
        try:
            self.state = HangmanState(max_wrong=6, difficulty=difficulty, theme=theme, custom_words=custom_words)
        except ValueError:
            self.state = HangmanState(max_wrong=6, difficulty='medium', theme='all', custom_words=custom_words)

        self.turn_seconds = self.stats.get('turn_seconds', 15)
        self.turn_time_left = self.turn_seconds
        self.timer_after_id = None
        self.hints_per_round = self.stats.get('hints_per_round', 2)
        self.hints_remaining = self.hints_per_round
        self.hint_penalties = 0
        self.is_paused = False
        
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
        if not self.stats.get('sound_enabled', True):
            return
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
        top_bar = tk.Frame(self.root, bg='#16233A', height=16)
        top_bar.pack(fill='x', side='top')

        container = tk.Frame(self.root, bg='#ECECEC')
        container.pack(expand=True, fill='both', padx=18, pady=12)

        top_info = tk.Frame(container, bg='#ECECEC')
        top_info.pack(fill='x', pady=(0, 6))

        self.category_label = tk.Label(top_info, text="Everyday Objects",
                                       font=('Comic Sans MS', 18, 'bold'),
                                       bg='#ECECEC', fg='#262626')
        self.category_label.pack(side='top')

        self.stats_label = tk.Label(top_info, text="Saved: 0\nBest: 0",
                                    font=('Comic Sans MS', 12, 'bold'),
                                    justify='right', bg='#ECECEC', fg='#262626')
        self.stats_label.place(relx=1.0, x=-4, y=0, anchor='ne')

        main_frame = tk.Frame(container, bg='#ECECEC')
        main_frame.pack(fill='both', expand=True)

        left_panel = tk.Frame(main_frame, bg='#ECECEC')
        left_panel.pack(side='left', fill='both', expand=True, padx=(0, 18))

        self.word_label = tk.Label(left_panel, text="", font=('Comic Sans MS', 38, 'bold'),
                                   bg='#ECECEC', fg='#111111', justify='center')
        self.word_label.pack(pady=(4, 10))

        self.hint_label = tk.Label(left_panel, text="", font=('Comic Sans MS', 11),
                                   bg='#ECECEC', fg='#555555', wraplength=560, justify='left')
        self.hint_label.pack(anchor='w', pady=(0, 6))

        utility_row = tk.Frame(left_panel, bg='#ECECEC')
        utility_row.pack(anchor='w', pady=(0, 8))

        self.counter_label = tk.Label(utility_row, text="Misses: 0/6", font=('Comic Sans MS', 11, 'bold'), bg='#ECECEC', fg='#A94442')
        self.counter_label.pack(side='left')

        self.timer_label = tk.Label(utility_row, text="Timer: Off", font=('Comic Sans MS', 11, 'bold'), bg='#ECECEC', fg='#7D3C98')
        self.timer_label.pack(side='left', padx=(14, 0))

        self.status_label = tk.Label(left_panel, text="Pick a letter to start!",
                                     font=('Comic Sans MS', 10), bg='#ECECEC', fg='#555555')
        self.status_label.pack(anchor='w', pady=(0, 8))

        letters_frame = tk.Frame(left_panel, bg='#ECECEC')
        letters_frame.pack(anchor='w')

        self.letter_buttons = {}
        alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        for i, letter in enumerate(alphabet):
            btn = tk.Button(
                letters_frame,
                text=letter,
                width=3,
                height=1,
                font=('Comic Sans MS', 20, 'bold'),
                bg='#F6F6F6',
                fg='#111111',
                activebackground='#E5E5E5',
                activeforeground='#111111',
                relief='solid',
                bd=2,
                cursor='hand2',
                command=lambda l=letter: self.guess_letter(l),
            )
            btn.grid(row=i // 6, column=i % 6, padx=4, pady=4)
            self.letter_buttons[letter] = btn

        bottom_row = tk.Frame(left_panel, bg='#ECECEC')
        bottom_row.pack(anchor='w', pady=(10, 0))

        self.hint_button = tk.Button(bottom_row, text="Hint (2)", font=('Comic Sans MS', 10, 'bold'),
                                     bg='#B04A5A', fg='white', activebackground='#9E3E4E',
                                     relief='flat', cursor='hand2', command=self.use_hint)
        self.hint_button.pack(side='left', padx=(0, 8))

        self.restart_button = tk.Button(bottom_row, text="Restart", font=('Comic Sans MS', 10, 'bold'),
                                        bg='#2C3E50', fg='white', activebackground='#1F2D3A',
                                        relief='flat', cursor='hand2', command=self.new_game)
        self.restart_button.pack(side='left', padx=(0, 8))

        self.pause_button = tk.Button(bottom_row, text="Pause", font=('Comic Sans MS', 10, 'bold'),
                                      bg='#7D6608', fg='white', activebackground='#6E2C00',
                                      relief='flat', cursor='hand2', command=self.toggle_pause)
        self.pause_button.pack(side='left', padx=(0, 8))

        settings_button = tk.Button(bottom_row, text="Settings", font=('Comic Sans MS', 10, 'bold'),
                                    bg='#515A5A', fg='white', activebackground='#3F4747',
                                    relief='flat', cursor='hand2', command=self.open_settings_window)
        settings_button.pack(side='left', padx=(0, 8))

        custom_pack_btn = tk.Button(bottom_row, text="Custom Pack", font=('Comic Sans MS', 10, 'bold'),
                                    bg='#1B4F72', fg='white', activebackground='#154360',
                                    relief='flat', cursor='hand2', command=self.open_custom_pack_window)
        custom_pack_btn.pack(side='left', padx=(0, 8))

        self.guessed_label = tk.Label(left_panel, text="Guessed: -", font=('Comic Sans MS', 10),
                                      bg='#ECECEC', fg='#4A4A4A', wraplength=560, justify='left')
        self.guessed_label.pack(anchor='w', pady=(8, 0))

        self.achievements_label = tk.Label(left_panel, text="", font=('Comic Sans MS', 9), bg='#ECECEC', fg='#5A5A5A')
        self.achievements_label.pack(anchor='w')
        self.leaderboard_label = tk.Label(left_panel, text="", font=('Comic Sans MS', 9), bg='#ECECEC', fg='#5A5A5A')
        self.leaderboard_label.pack(anchor='w')
        self.history_label = tk.Label(left_panel, text="", font=('Comic Sans MS', 9), bg='#ECECEC', fg='#5A5A5A')
        self.history_label.pack(anchor='w')

        right_panel = tk.Frame(main_frame, bg='#ECECEC')
        right_panel.pack(side='right', fill='both', padx=(0, 6))

        self.canvas = tk.Canvas(right_panel, width=360, height=450, bg='#ECECEC', highlightthickness=0)
        self.canvas.pack()

        self.name_var = tk.StringVar(value=self.player_name)
        self.name_entry = tk.Entry(container, textvariable=self.name_var, width=1)
        self.difficulty_var = tk.StringVar(value=self.state.difficulty.title())
        self.theme_var = tk.StringVar(value=self.state.theme.title())
        self.timer_var = tk.BooleanVar(value=bool(self.stats.get('timer_enabled', False)))

        self.root.bind('<Key>', self.on_key_press)

    def on_difficulty_change(self, choice):
        level = (choice or "Medium").strip().lower()
        self.state.set_difficulty(level)
        self.stats['default_difficulty'] = level
        self.stats_store.save(self.stats)
        self.new_game()
        self.status_label.config(text=f"Difficulty set to {choice}. Good luck!")

    def on_theme_change(self, choice):
        level = (choice or "All").strip().lower()
        if level == 'custom' and not self.stats.get('custom_words', []):
            self.status_label.config(text="Custom pack is empty. Add words first.")
            self.theme_var.set(self.state.theme.title())
            return
        self.state.set_theme(level)
        self.stats['default_theme'] = level
        self.stats_store.save(self.stats)
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
        if self.timer_var.get() and self.state.game_active and not self.is_paused:
            self._start_turn_timer(reset=True)
        else:
            self._cancel_turn_timer()
            self.timer_label.config(text="Timer: Off")

    def toggle_pause(self):
        if not self.state.game_active:
            return
        self.is_paused = not self.is_paused
        if self.is_paused:
            self._cancel_turn_timer()
            self.pause_button.config(text='Resume')
            self.status_label.config(text='Game paused.')
        else:
            self.pause_button.config(text='Pause')
            self.status_label.config(text='Game resumed.')
            self._start_turn_timer(reset=False)

    def open_settings_window(self):
        window = tk.Toplevel(self.root)
        window.title('Settings')
        window.resizable(False, False)
        window.configure(bg='white')

        frame = tk.Frame(window, bg='white', padx=16, pady=16)
        frame.pack(fill='both', expand=True)

        timer_seconds_var = tk.IntVar(value=self.turn_seconds)
        hints_var = tk.IntVar(value=self.hints_per_round)
        sound_var = tk.BooleanVar(value=bool(self.stats.get('sound_enabled', True)))
        default_difficulty_var = tk.StringVar(value=self.state.difficulty.title())
        default_theme_var = tk.StringVar(value=self.state.theme.title())

        tk.Label(frame, text='Timer seconds (5-60):', bg='white', fg='#2C3E50', font=('Arial', 10, 'bold')).grid(row=0, column=0, sticky='w', pady=(0, 8))
        tk.Spinbox(frame, from_=5, to=60, textvariable=timer_seconds_var, width=8).grid(row=0, column=1, sticky='w', pady=(0, 8))

        tk.Label(frame, text='Hints per round (0-5):', bg='white', fg='#2C3E50', font=('Arial', 10, 'bold')).grid(row=1, column=0, sticky='w', pady=(0, 8))
        tk.Spinbox(frame, from_=0, to=5, textvariable=hints_var, width=8).grid(row=1, column=1, sticky='w', pady=(0, 8))

        tk.Checkbutton(frame, text='Enable sound', variable=sound_var, bg='white', activebackground='white').grid(row=2, column=0, sticky='w', pady=(0, 8))

        tk.Label(frame, text='Default difficulty:', bg='white', fg='#2C3E50', font=('Arial', 10, 'bold')).grid(row=3, column=0, sticky='w', pady=(0, 8))
        tk.OptionMenu(frame, default_difficulty_var, 'Easy', 'Medium', 'Hard').grid(row=3, column=1, sticky='w', pady=(0, 8))

        tk.Label(frame, text='Default theme:', bg='white', fg='#2C3E50', font=('Arial', 10, 'bold')).grid(row=4, column=0, sticky='w', pady=(0, 8))
        tk.OptionMenu(frame, default_theme_var, 'All', 'Animals', 'Tech', 'Nature', 'Food', 'Custom').grid(row=4, column=1, sticky='w', pady=(0, 8))

        def save_settings():
            self.turn_seconds = max(5, min(60, int(timer_seconds_var.get())))
            self.hints_per_round = max(0, min(5, int(hints_var.get())))
            self.stats['turn_seconds'] = self.turn_seconds
            self.stats['hints_per_round'] = self.hints_per_round
            self.stats['sound_enabled'] = bool(sound_var.get())
            self.stats['default_difficulty'] = default_difficulty_var.get().lower()
            selected_theme = default_theme_var.get().lower()
            if selected_theme == 'custom' and not self.stats.get('custom_words', []):
                selected_theme = 'all'
            self.stats['default_theme'] = selected_theme

            self.state.set_difficulty(self.stats['default_difficulty'])
            self.state.set_theme(self.stats['default_theme'])
            self.difficulty_var.set(self.state.difficulty.title())
            self.theme_var.set(self.state.theme.title())
            self.turn_time_left = self.turn_seconds
            self.stats_store.save(self.stats)
            self.new_game()
            self.status_label.config(text='Settings saved.')
            window.destroy()

        tk.Button(frame, text='Save', command=save_settings, bg='#2C3E50', fg='white', relief='flat').grid(row=5, column=0, pady=(8, 0), sticky='w')
        tk.Button(frame, text='Cancel', command=window.destroy, bg='#7F8C8D', fg='white', relief='flat').grid(row=5, column=1, pady=(8, 0), sticky='e')

    def open_custom_pack_window(self):
        window = tk.Toplevel(self.root)
        window.title('Custom Word Pack')
        window.resizable(False, False)
        window.configure(bg='white')

        frame = tk.Frame(window, bg='white', padx=16, pady=16)
        frame.pack(fill='both', expand=True)

        tk.Label(frame, text='Word:', bg='white', fg='#2C3E50', font=('Arial', 10, 'bold')).grid(row=0, column=0, sticky='w')
        word_var = tk.StringVar()
        tk.Entry(frame, textvariable=word_var, width=18).grid(row=0, column=1, padx=(8, 0), sticky='w')

        tk.Label(frame, text='Hint:', bg='white', fg='#2C3E50', font=('Arial', 10, 'bold')).grid(row=1, column=0, sticky='w', pady=(8, 0))
        hint_var = tk.StringVar()
        tk.Entry(frame, textvariable=hint_var, width=28).grid(row=1, column=1, padx=(8, 0), pady=(8, 0), sticky='w')

        listbox = tk.Listbox(frame, width=45, height=8)
        listbox.grid(row=2, column=0, columnspan=2, pady=(10, 8))

        custom_rows = [dict(item) for item in self.stats.get('custom_words', [])]

        def refresh_listbox():
            listbox.delete(0, tk.END)
            for item in custom_rows:
                listbox.insert(tk.END, f"{item['word']} - {item['hint']}")

        def add_word():
            word = word_var.get().strip().upper()
            hint = hint_var.get().strip()
            if len(word) < 2 or not word.isalpha() or not hint:
                self.status_label.config(text='Custom words need letters-only word and non-empty hint.')
                return
            custom_rows.append({'word': word, 'hint': hint[:120]})
            word_var.set('')
            hint_var.set('')
            refresh_listbox()

        def remove_selected():
            selected = listbox.curselection()
            if not selected:
                return
            del custom_rows[selected[0]]
            refresh_listbox()

        def save_custom_pack():
            self.stats['custom_words'] = custom_rows[:200]
            self.state.set_custom_words([(item['word'], item['hint']) for item in self.stats['custom_words']])
            self.stats_store.save(self.stats)
            if self.state.theme == 'custom' and not self.stats['custom_words']:
                self.state.set_theme('all')
                self.theme_var.set('All')
            self.new_game()
            self.status_label.config(text='Custom pack saved.')
            window.destroy()

        tk.Button(frame, text='Add', command=add_word, bg='#1B4F72', fg='white', relief='flat').grid(row=3, column=0, sticky='w')
        tk.Button(frame, text='Remove Selected', command=remove_selected, bg='#7D6608', fg='white', relief='flat').grid(row=3, column=1, sticky='e')
        tk.Button(frame, text='Save Pack', command=save_custom_pack, bg='#2C3E50', fg='white', relief='flat').grid(row=4, column=0, pady=(10, 0), sticky='w')
        tk.Button(frame, text='Close', command=window.destroy, bg='#7F8C8D', fg='white', relief='flat').grid(row=4, column=1, pady=(10, 0), sticky='e')

        refresh_listbox()

    def _cancel_turn_timer(self):
        if self.timer_after_id is not None:
            self.root.after_cancel(self.timer_after_id)
            self.timer_after_id = None

    def _start_turn_timer(self, reset=False):
        if not self.timer_var.get() or not self.state.game_active or self.is_paused:
            self.timer_label.config(text="Timer: Off")
            return
        self._cancel_turn_timer()
        if reset:
            self.turn_time_left = self.turn_seconds
        self.timer_label.config(text=f"Timer: {self.turn_time_left}s")
        self.timer_after_id = self.root.after(1000, self._tick_timer)

    def _tick_timer(self):
        self.timer_after_id = None
        if not self.timer_var.get() or not self.state.game_active or self.is_paused:
            self.timer_label.config(text="Timer: Off")
            return

        self.turn_time_left -= 1
        if self.turn_time_left <= 0:
            self.handle_timeout()
            return

        self.timer_label.config(text=f"Timer: {self.turn_time_left}s")
        self.timer_after_id = self.root.after(1000, self._tick_timer)

    def handle_timeout(self):
        if self.is_paused:
            return
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
            self.history_label.config(text="")
            return
        self.history_label.config(text="")

    def update_stats_display(self):
        played = self.stats['games_played']
        best = self.stats['best_streak']
        self.stats_label.config(text=f"Saved: {played}\nBest: {best}")
        self.category_label.config(text=self.state.theme.title() if self.state.theme != 'all' else 'Everyday Objects')

        recent_badges = self.stats['achievements'][-3:]
        if recent_badges:
            badge_text = ', '.join(recent_badges)
            self.achievements_label.config(text=f"Badges: {badge_text}")
        else:
            self.achievements_label.config(text="")

        board = self.stats['leaderboard'][:3]
        if board:
            rows = [
                f"{idx + 1}. {entry['name']} {entry['score']} pts ({entry['difficulty'].title()}/{entry['theme'].title()})"
                for idx, entry in enumerate(board)
            ]
            self.leaderboard_label.config(text="")
        else:
            self.leaderboard_label.config(text="")
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
        if not self.state.game_active or self.is_paused:
            return
        
        letter = event.char.upper()
        if letter in self.letter_buttons and self.letter_buttons[letter]['state'] == 'normal':
            self.guess_letter(letter)
    
    def draw_hangman(self, stage):
        """Draw a balloon-rescue scene inspired by the reference style."""
        self.canvas.delete('all')

        self.canvas.create_polygon(255, 120, 285, 390, 225, 390, fill='#E3E3E3', outline='')
        self.canvas.create_polygon(318, 138, 348, 390, 288, 390, fill='#E6E6E6', outline='')

        self.canvas.create_oval(210, 360, 340, 440, fill='#121212', outline='#121212')
        self.canvas.create_oval(242, 385, 263, 401, fill='white', outline='')
        self.canvas.create_oval(285, 385, 306, 401, fill='white', outline='')
        self.canvas.create_oval(247, 389, 255, 397, fill='#121212', outline='')
        self.canvas.create_oval(290, 389, 298, 397, fill='#121212', outline='')

        self.canvas.create_oval(286, 180, 316, 210, fill='#FFFFFF', outline='#111111', width=2)
        self.canvas.create_line(301, 210, 301, 256, fill='#111111', width=2)
        self.canvas.create_line(301, 230, 285, 245, fill='#111111', width=2)
        self.canvas.create_line(301, 230, 317, 245, fill='#111111', width=2)
        self.canvas.create_line(301, 256, 289, 276, fill='#111111', width=2)
        self.canvas.create_line(301, 256, 313, 276, fill='#111111', width=2)

        balloon_colors = ['#BF4658', '#729D45', '#4E8AB8', '#C96A44', '#B84E9A', '#5A8C7A']
        balloons_left = max(self.state.max_wrong - stage, 0)
        anchor_points = [(270, 148), (292, 136), (318, 142), (338, 156), (282, 168), (322, 170)]

        for idx, (bx, by) in enumerate(anchor_points):
            if idx < balloons_left:
                self.canvas.create_line(301, 182, bx, by + 12, fill='#111111', width=1)
                self.canvas.create_oval(bx - 14, by - 18, bx + 14, by + 14,
                                        fill=balloon_colors[idx], outline='')
            else:
                self.canvas.create_line(bx - 8, by - 8, bx + 8, by + 8, fill='#BDBDBD', width=2)
                self.canvas.create_line(bx + 8, by - 8, bx - 8, by + 8, fill='#BDBDBD', width=2)
    
    def new_game(self):
        self._cancel_turn_timer()
        self.is_paused = False
        self.pause_button.config(text='Pause')
        self.state.reset()
        self.hints_remaining = self.hints_per_round
        self.hint_penalties = 0
        self.turn_time_left = self.turn_seconds
        
        # Reset canvas
        self.draw_hangman(0)
        
        # Reset letter buttons efficiently
        for btn in self.letter_buttons.values():
            btn.config(state='normal', bg='#F6F6F6', fg='#111111', relief='solid', bd=2)
        
        # Update displays
        self.update_word_display()
        self.hint_label.config(text=f"Hint: {self.state.hint}")
        self.counter_label.config(text=f"Misses: {self.state.wrong_guesses}/{self.state.max_wrong}")
        self.guessed_label.config(text="Guessed: -")
        self.status_label.config(text="Pick a letter to start!")
        self.hint_button.config(text=f"Hint ({self.hints_remaining})", state='normal')
        self._start_turn_timer(reset=True)
        self.update_stats_display()

    def use_hint(self):
        if not self.state.game_active or self.is_paused:
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
            self.letter_buttons[letter].config(state='disabled', bg='#ECECEC', fg='#B8B8B8')

        penalty_result = self.state.add_wrong_guess()
        self.play_sound_async('correct')
        if penalty_result != 'ignored':
            self.play_sound_async('wrong')

        self.draw_hangman(self.state.wrong_guesses)
        self.update_word_display()
        self.counter_label.config(text=f"Misses: {self.state.wrong_guesses}/{self.state.max_wrong}")
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
        if self.is_paused:
            return
        result = self.state.guess(letter)
        if result == 'ignored':
            return
        
        # Play click sound asynchronously
        self.play_sound_async('click')
        
        self.letter_buttons[letter].config(state='disabled', bg='#ECECEC', fg='#B8B8B8')

        if result == 'wrong':
            self.play_sound_async('wrong')
            self.draw_hangman(self.state.wrong_guesses)
            self.counter_label.config(text=f"Misses: {self.state.wrong_guesses}/{self.state.max_wrong}")
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