import tkinter as tk
from tkinter import messagebox
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
        
        self.state = HangmanState(max_wrong=6, difficulty='medium')
        self.stats_store = StatsStore("stats.json")
        self.stats = self.stats_store.load()
        
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
        self.counter_label.pack(pady=(0, 20))

        # Guessed letters display
        self.guessed_label = tk.Label(right_frame, text="Guessed: -",
                          font=('Arial', 12),
                          bg='white', fg='#34495E',
                          wraplength=500, justify='left')
        self.guessed_label.pack(pady=(0, 16))
        
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

        self.restart_button = tk.Button(right_frame, text="Restart",
                                        font=('Arial', 11, 'bold'),
                                        bg='#2C3E50', fg='white',
                                        activebackground='#1F2D3A',
                                        relief='flat', cursor='hand2',
                                        command=self.new_game)
        self.restart_button.pack(pady=(18, 0))
        
        # Bind keyboard input
        self.root.bind('<Key>', self.on_key_press)

    def on_difficulty_change(self, choice):
        level = (choice or "Medium").strip().lower()
        self.state.set_difficulty(level)
        self.new_game()
        self.status_label.config(text=f"Difficulty set to {choice}. Good luck!")

    def update_stats_display(self):
        played = self.stats['games_played']
        wins = self.stats['wins']
        best = self.stats['best_streak']
        self.stats_label.config(text=f"Played: {played}  Wins: {wins}  Best Streak: {best}")

    def record_game_result(self, won):
        self.stats['games_played'] += 1
        if won:
            self.stats['wins'] += 1
            self.stats['current_streak'] += 1
            self.stats['best_streak'] = max(self.stats['best_streak'], self.stats['current_streak'])
        else:
            self.stats['losses'] += 1
            self.stats['current_streak'] = 0
        self.stats_store.save(self.stats)
        self.update_stats_display()
    
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
        self.state.reset()
        
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
        self.update_stats_display()
    
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
    
    def update_word_display(self):
        """Optimized word display update"""
        self.word_label.config(text=self.state.masked_word)
    
    def game_over(self, won):
        self.state.game_active = False
        self.record_game_result(won)
        
        # Disable all buttons at once
        for btn in self.letter_buttons.values():
            btn.config(state='disabled')
        
        if won:
            self.play_sound_async('win')
            self.root.after(450, lambda: self._show_game_over_dialog(True))
        else:
            self.play_sound_async('lose')
            self.root.after(1300, lambda: self._show_game_over_dialog(False))
    
    def _show_game_over_dialog(self, won):
        """Show game over dialog after sound completes"""
        if won:
            result = messagebox.askyesno("🎉 Congratulations!", 
                              f"You won! The word was: {self.state.word}\n\nPlay again?")
        else:
            result = messagebox.askyesno("💀 Game Over", 
                              f"You lost! The word was: {self.state.word}\n\nPlay again?")
        
        if result:
            self.new_game()
        else:
            self.root.quit()

if __name__ == "__main__":
    root = tk.Tk()
    game = HangmanGame(root)
    root.mainloop()