import random


DIFFICULTY_RULES = {
    "easy": (0, 7),
    "medium": (8, 9),
    "hard": (10, 99),
}

DEFAULT_WORD_LIST = [
    ("RAINBOW", "Colorful light display in sky during rain"),
    ("PYTHON", "A popular programming language"),
    ("COMPUTER", "Electronic device for processing data"),
    ("KEYBOARD", "Input device with keys"),
    ("ELEPHANT", "Largest land animal with trunk"),
    ("MOUNTAIN", "Large natural elevation of earth"),
    ("OCEAN", "Vast body of salt water"),
    ("BUTTERFLY", "Insect with colorful wings"),
    ("GUITAR", "String musical instrument"),
    ("CAMERA", "Device for taking photographs"),
    ("LIBRARY", "Place with many books"),
    ("PIZZA", "Italian dish with cheese and toppings"),
    ("CASTLE", "Large fortified building"),
    ("ROCKET", "Vehicle for space travel"),
    ("DIAMOND", "Precious gemstone"),
    ("SANDWICH", "Food made between two slices of bread"),
    ("TELEPHONE", "Device used for voice communication"),
    ("BICYCLE", "Two-wheeled vehicle powered by pedaling"),
    ("CHOCOLATE", "Sweet treat made from cocoa beans"),
    ("UMBRELLA", "Portable shelter from rain or sun"),
    ("AIRPLANE", "Flying vehicle with wings and engines"),
    ("VOLCANO", "Mountain that can erupt with lava"),
    ("PENGUIN", "Black and white bird that cannot fly"),
    ("TREASURE", "Valuable collection of precious items"),
    ("TORNADO", "Spinning column of air and debris"),
    ("DINOSAUR", "Extinct prehistoric reptile"),
    ("SPACESHIP", "Vehicle designed for space travel"),
    ("WATERFALL", "Water flowing over a cliff or rocks"),
    ("LIGHTHOUSE", "Tower with bright light to guide ships"),
    ("SNOWFLAKE", "Unique ice crystal that falls from sky"),
    ("JELLYFISH", "Transparent sea creature with tentacles"),
    ("KANGAROO", "Hopping marsupial from Australia"),
    ("FIREWORKS", "Explosive displays of colored lights"),
    ("TELESCOPE", "Instrument for viewing distant objects"),
    ("CROCODILE", "Large reptile with powerful jaws"),
    ("HURRICANE", "Powerful rotating storm system"),
    ("MUSHROOM", "Fungus that grows from the ground"),
    ("PEACOCK", "Colorful bird with magnificent tail feathers"),
    ("SUBMARINE", "Underwater vessel for ocean exploration"),
    ("DRAGONFLY", "Insect with four transparent wings"),
    ("SUNFLOWER", "Tall yellow flower that follows the sun"),
    ("BASKETBALL", "Sport played with orange ball and hoops"),
    ("STRAWBERRY", "Red berry with seeds on the outside"),
    ("HELICOPTER", "Aircraft with rotating blades overhead"),
    ("PINEAPPLE", "Tropical fruit with spiky exterior"),
    ("WATERMELON", "Large green fruit with red flesh inside"),
    ("SAXOPHONE", "Brass wind instrument with curved shape"),
    ("CHAMELEON", "Lizard that changes color for camouflage"),
    ("BLIZZARD", "Severe snowstorm with strong winds"),
]


class HangmanState:
    def __init__(self, word_list=None, max_wrong=6, chooser=None, difficulty="medium"):
        self.word_list = list(word_list or DEFAULT_WORD_LIST)
        self.max_wrong = max_wrong
        self.chooser = chooser or random.choice
        self.difficulty = "medium"
        self.word = ""
        self.hint = ""
        self.guessed_letters = set()
        self.wrong_guesses = 0
        self.game_active = False
        self.set_difficulty(difficulty)

    @property
    def available_difficulties(self):
        return tuple(DIFFICULTY_RULES.keys())

    @property
    def masked_word(self):
        return " ".join(letter if letter in self.guessed_letters else "_" for letter in self.word)

    @property
    def is_won(self):
        return bool(self.word) and all(letter in self.guessed_letters for letter in self.word)

    @property
    def is_lost(self):
        return self.wrong_guesses >= self.max_wrong

    def set_difficulty(self, difficulty):
        level = (difficulty or "").strip().lower()
        if level not in DIFFICULTY_RULES:
            raise ValueError(f"Unsupported difficulty: {difficulty}")
        self.difficulty = level

    def _filtered_words(self):
        min_len, max_len = DIFFICULTY_RULES[self.difficulty]
        filtered = [item for item in self.word_list if min_len <= len(item[0]) <= max_len]
        if filtered:
            return filtered
        return self.word_list

    def reset(self):
        pool = self._filtered_words()
        self.word, self.hint = self.chooser(pool)
        self.guessed_letters.clear()
        self.wrong_guesses = 0
        self.game_active = True

    def guess(self, letter):
        candidate = (letter or "").strip().upper()
        if not self.game_active or len(candidate) != 1 or not candidate.isalpha():
            return "ignored"
        if candidate in self.guessed_letters:
            return "ignored"

        self.guessed_letters.add(candidate)
        if candidate not in self.word:
            self.wrong_guesses += 1
            if self.is_lost:
                self.game_active = False
                return "lost"
            return "wrong"

        if self.is_won:
            self.game_active = False
            return "won"
        return "correct"
