import random


DIFFICULTY_RULES = {
    "easy": (0, 7),
    "medium": (8, 9),
    "hard": (10, 99),
}

CUSTOM_THEME = "custom"

WORD_PACKS = {
    "all": [
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
    ],
    "animals": [
        ("ELEPHANT", "Largest land animal with trunk"),
        ("BUTTERFLY", "Insect with colorful wings"),
        ("PENGUIN", "Black and white bird that cannot fly"),
        ("DINOSAUR", "Extinct prehistoric reptile"),
        ("JELLYFISH", "Transparent sea creature with tentacles"),
        ("KANGAROO", "Hopping marsupial from Australia"),
        ("CROCODILE", "Large reptile with powerful jaws"),
        ("PEACOCK", "Colorful bird with magnificent tail feathers"),
        ("DRAGONFLY", "Insect with four transparent wings"),
        ("CHAMELEON", "Lizard that changes color for camouflage"),
    ],
    "tech": [
        ("PYTHON", "A popular programming language"),
        ("COMPUTER", "Electronic device for processing data"),
        ("KEYBOARD", "Input device with keys"),
        ("CAMERA", "Device for taking photographs"),
        ("ROCKET", "Vehicle for space travel"),
        ("TELEPHONE", "Device used for voice communication"),
        ("AIRPLANE", "Flying vehicle with wings and engines"),
        ("SPACESHIP", "Vehicle designed for space travel"),
        ("LIGHTHOUSE", "Tower with bright light to guide ships"),
        ("TELESCOPE", "Instrument for viewing distant objects"),
        ("SUBMARINE", "Underwater vessel for ocean exploration"),
        ("HELICOPTER", "Aircraft with rotating blades overhead"),
        ("SAXOPHONE", "Brass wind instrument with curved shape"),
    ],
    "nature": [
        ("RAINBOW", "Colorful light display in sky during rain"),
        ("MOUNTAIN", "Large natural elevation of earth"),
        ("OCEAN", "Vast body of salt water"),
        ("DIAMOND", "Precious gemstone"),
        ("UMBRELLA", "Portable shelter from rain or sun"),
        ("VOLCANO", "Mountain that can erupt with lava"),
        ("TORNADO", "Spinning column of air and debris"),
        ("WATERFALL", "Water flowing over a cliff or rocks"),
        ("SNOWFLAKE", "Unique ice crystal that falls from sky"),
        ("HURRICANE", "Powerful rotating storm system"),
        ("MUSHROOM", "Fungus that grows from the ground"),
        ("SUNFLOWER", "Tall yellow flower that follows the sun"),
        ("BLIZZARD", "Severe snowstorm with strong winds"),
    ],
    "food": [
        ("PIZZA", "Italian dish with cheese and toppings"),
        ("SANDWICH", "Food made between two slices of bread"),
        ("CHOCOLATE", "Sweet treat made from cocoa beans"),
        ("STRAWBERRY", "Red berry with seeds on the outside"),
        ("PINEAPPLE", "Tropical fruit with spiky exterior"),
        ("WATERMELON", "Large green fruit with red flesh inside"),
    ],
}

DEFAULT_WORD_LIST = WORD_PACKS["all"]


class HangmanState:
    def __init__(self, word_list=None, max_wrong=6, chooser=None, difficulty="medium", theme="all", custom_words=None):
        self.word_list = list(word_list or DEFAULT_WORD_LIST)
        self.custom_words = list(custom_words or [])
        self.max_wrong = max_wrong
        self.chooser = chooser or random.choice
        self.difficulty = "medium"
        self.theme = "all"
        self.word = ""
        self.hint = ""
        self.guessed_letters = set()
        self.wrong_guesses = 0
        self.game_active = False
        self.set_difficulty(difficulty)
        self.set_theme(theme)

    @property
    def available_difficulties(self):
        return tuple(DIFFICULTY_RULES.keys())

    @property
    def available_themes(self):
        return tuple(list(WORD_PACKS.keys()) + [CUSTOM_THEME])

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

    def set_theme(self, theme):
        group = (theme or "").strip().lower()
        if group not in self.available_themes:
            raise ValueError(f"Unsupported theme: {theme}")
        self.theme = group

    def set_custom_words(self, custom_words):
        cleaned = []
        for item in custom_words or []:
            if not isinstance(item, (tuple, list)) or len(item) != 2:
                continue
            word = str(item[0]).strip().upper()
            hint = str(item[1]).strip()
            if len(word) < 2 or not word.isalpha() or not hint:
                continue
            cleaned.append((word, hint))
        self.custom_words = cleaned

    def _themed_words(self):
        if self.theme == CUSTOM_THEME:
            if self.custom_words:
                return list(self.custom_words)
            return list(self.word_list)
        if self.theme == "all":
            return list(self.word_list)
        allowed_words = {word for word, _ in WORD_PACKS[self.theme]}
        themed = [item for item in self.word_list if item[0] in allowed_words]
        if themed:
            return themed
        return list(self.word_list)

    def _filtered_words(self):
        min_len, max_len = DIFFICULTY_RULES[self.difficulty]
        themed = self._themed_words()
        filtered = [item for item in themed if min_len <= len(item[0]) <= max_len]
        if filtered:
            return filtered
        return themed

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

    def add_wrong_guess(self):
        if not self.game_active:
            return "ignored"

        self.wrong_guesses += 1
        if self.is_lost:
            self.game_active = False
            return "lost"
        return "wrong"
