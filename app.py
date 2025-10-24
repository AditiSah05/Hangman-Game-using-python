import tkinter as tk
from tkinter import messagebox
import random
import sys
import threading

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
        
        # Optimized word list - removed duplicate
        self.word_list = [
            ('RAINBOW', 'Colorful light display in sky during rain'),
            ('PYTHON', 'A popular programming language'),
            ('COMPUTER', 'Electronic device for processing data'),
            ('KEYBOARD', 'Input device with keys'),
            ('ELEPHANT', 'Largest land animal with trunk'),
            ('MOUNTAIN', 'Large natural elevation of earth'),
            ('OCEAN', 'Vast body of salt water'),
            ('BUTTERFLY', 'Insect with colorful wings'),
            ('GUITAR', 'String musical instrument'),
            ('CAMERA', 'Device for taking photographs'),
            ('LIBRARY', 'Place with many books'),
            ('PIZZA', 'Italian dish with cheese and toppings'),
            ('CASTLE', 'Large fortified building'),
            ('ROCKET', 'Vehicle for space travel'),
            ('DIAMOND', 'Precious gemstone'),
            ('SANDWICH', 'Food made between two slices of bread'),
            ('TELEPHONE', 'Device used for voice communication'),
            ('BICYCLE', 'Two-wheeled vehicle powered by pedaling'),
            ('CHOCOLATE', 'Sweet treat made from cocoa beans'),
            ('UMBRELLA', 'Portable shelter from rain or sun'),
            ('AIRPLANE', 'Flying vehicle with wings and engines'),
            ('VOLCANO', 'Mountain that can erupt with lava'),
            ('PENGUIN', 'Black and white bird that cannot fly'),
            ('TREASURE', 'Valuable collection of precious items'),
            ('TORNADO', 'Spinning column of air and debris'),
            ('DINOSAUR', 'Extinct prehistoric reptile'),
            ('SPACESHIP', 'Vehicle designed for space travel'),
            ('WATERFALL', 'Water flowing over a cliff or rocks'),
            ('LIGHTHOUSE', 'Tower with bright light to guide ships'),
            ('SNOWFLAKE', 'Unique ice crystal that falls from sky'),
            ('JELLYFISH', 'Transparent sea creature with tentacles'),
            ('KANGAROO', 'Hopping marsupial from Australia'),
            ('FIREWORKS', 'Explosive displays of colored lights'),
            ('TELESCOPE', 'Instrument for viewing distant objects'),
            ('CROCODILE', 'Large reptile with powerful jaws'),
            ('HURRICANE', 'Powerful rotating storm system'),
            ('MUSHROOM', 'Fungus that grows from the ground'),
            ('PEACOCK', 'Colorful bird with magnificent tail feathers'),
            ('SUBMARINE', 'Underwater vessel for ocean exploration'),
            ('DRAGONFLY', 'Insect with four transparent wings'),
            ('SUNFLOWER', 'Tall yellow flower that follows the sun'),
            ('BASKETBALL', 'Sport played with orange ball and hoops'),
            ('STRAWBERRY', 'Red berry with seeds on the outside'),
            ('HELICOPTER', 'Aircraft with rotating blades overhead'),
            ('PINEAPPLE', 'Tropical fruit with spiky exterior'),
            ('WATERMELON', 'Large green fruit with red flesh inside'),
            ('SAXOPHONE', 'Brass wind instrument with curved shape'),
            ('CHAMELEON', 'Lizard that changes color for camouflage'),
            ('BLIZZARD', 'Severe snowstorm with strong winds')
        ]
        
        self.word = ''
        self.hint = ''
        self.guessed_letters = set()
        self.wrong_guesses = 0
        self.max_wrong = 6
        self.game_active = True
        
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
        
        # Word display
        self.word_label = tk.Label(right_frame, text="", 
                                   font=('Arial', 36, 'bold'),
                                   bg='white', fg='#2C3E50',
                                   justify='center')
        self.word_label.pack(pady=(0, 20))
        
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
        
        # Bind keyboard input
        self.root.bind('<Key>', self.on_key_press)
    
    def on_key_press(self, event):
        """Handle keyboard input"""
        if not self.game_active:
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
        word_data = random.choice(self.word_list)
        self.word = word_data[0]
        self.hint = word_data[1]
        self.guessed_letters.clear()
        self.wrong_guesses = 0
        self.game_active = True
        
        # Reset canvas
        self.draw_hangman(0)
        
        # Reset letter buttons efficiently
        for btn in self.letter_buttons.values():
            btn.config(state='normal', bg='#6B7FCC')
        
        # Update displays
        self.update_word_display()
        self.hint_label.config(text=f"Hint: {self.hint}")
        self.counter_label.config(text=f"Incorrect: 0/{self.max_wrong}")
    
    def guess_letter(self, letter):
        if not self.game_active or letter in self.guessed_letters:
            return
        
        # Play click sound asynchronously
        self.play_sound_async('click')
        
        self.guessed_letters.add(letter)
        self.letter_buttons[letter].config(state='disabled', bg='#95A5D8')
        
        if letter not in self.word:
            self.play_sound_async('wrong')
            self.wrong_guesses += 1
            self.draw_hangman(self.wrong_guesses)
            self.counter_label.config(text=f"Incorrect: {self.wrong_guesses}/{self.max_wrong}")
            
            if self.wrong_guesses >= self.max_wrong:
                self.game_over(False)
                return
        else:
            self.play_sound_async('correct')
        
        self.update_word_display()
        
        # Check if won - optimized check
        if all(c in self.guessed_letters for c in self.word):
            self.game_over(True)
    
    def update_word_display(self):
        """Optimized word display update"""
        display = ' '.join(letter if letter in self.guessed_letters else '_' 
                          for letter in self.word)
        self.word_label.config(text=display)
    
    def game_over(self, won):
        self.game_active = False
        
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
                              f"You won! The word was: {self.word}\n\nPlay again?")
        else:
            result = messagebox.askyesno("💀 Game Over", 
                              f"You lost! The word was: {self.word}\n\nPlay again?")
        
        if result:
            self.new_game()
        else:
            self.root.quit()

if __name__ == "__main__":
    root = tk.Tk()
    game = HangmanGame(root)
    root.mainloop()