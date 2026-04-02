const WORDS = [
  { word: "RAINBOW", hint: "Colorful light display in sky during rain", category: "Everyday Objects" },
  { word: "PYTHON", hint: "A popular programming language", category: "Tech" },
  { word: "ELEPHANT", hint: "Largest land animal with trunk", category: "Animals" },
  { word: "WATERMELON", hint: "Large green fruit with red flesh", category: "Food" },
  { word: "TELESCOPE", hint: "Instrument for viewing distant objects", category: "Tech" },
  { word: "SUNFLOWER", hint: "Tall yellow flower that follows the sun", category: "Nature" },
];

const MAX_WRONG = 6;
const TURN_SECONDS = 15;

const state = {
  word: "",
  hint: "",
  category: "Everyday Objects",
  guessed: new Set(),
  wrong: 0,
  saved: 0,
  best: 0,
  timerEnabled: false,
  secondsLeft: TURN_SECONDS,
  timerId: null,
  hintsLeft: 2,
};

const els = {
  categoryLabel: document.getElementById("categoryLabel"),
  savedCount: document.getElementById("savedCount"),
  bestCount: document.getElementById("bestCount"),
  wordMask: document.getElementById("wordMask"),
  hintText: document.getElementById("hintText"),
  statusText: document.getElementById("statusText"),
  missesText: document.getElementById("missesText"),
  timerText: document.getElementById("timerText"),
  keyboard: document.getElementById("keyboard"),
  newBtn: document.getElementById("newBtn"),
  hintBtn: document.getElementById("hintBtn"),
  timerToggle: document.getElementById("timerToggle"),
  scene: document.getElementById("scene"),
};

function drawScene() {
  const ctx = els.scene.getContext("2d");
  ctx.clearRect(0, 0, els.scene.width, els.scene.height);

  ctx.fillStyle = "#E3E3E3";
  ctx.beginPath();
  ctx.moveTo(255, 120); ctx.lineTo(285, 390); ctx.lineTo(225, 390);
  ctx.closePath();
  ctx.fill();

  ctx.fillStyle = "#E6E6E6";
  ctx.beginPath();
  ctx.moveTo(318, 138); ctx.lineTo(348, 390); ctx.lineTo(288, 390);
  ctx.closePath();
  ctx.fill();

  ctx.fillStyle = "#121212";
  ctx.beginPath();
  ctx.ellipse(275, 400, 65, 40, 0, 0, Math.PI * 2);
  ctx.fill();

  ctx.fillStyle = "#fff";
  ctx.beginPath(); ctx.ellipse(252, 393, 10, 8, 0, 0, Math.PI * 2); ctx.fill();
  ctx.beginPath(); ctx.ellipse(295, 393, 10, 8, 0, 0, Math.PI * 2); ctx.fill();

  ctx.fillStyle = "#121212";
  ctx.beginPath(); ctx.ellipse(252, 393, 4, 4, 0, 0, Math.PI * 2); ctx.fill();
  ctx.beginPath(); ctx.ellipse(295, 393, 4, 4, 0, 0, Math.PI * 2); ctx.fill();

  ctx.strokeStyle = "#111";
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.arc(301, 195, 15, 0, Math.PI * 2);
  ctx.stroke();

  ctx.beginPath();
  ctx.moveTo(301, 210); ctx.lineTo(301, 256);
  ctx.moveTo(301, 230); ctx.lineTo(285, 245);
  ctx.moveTo(301, 230); ctx.lineTo(317, 245);
  ctx.moveTo(301, 256); ctx.lineTo(289, 276);
  ctx.moveTo(301, 256); ctx.lineTo(313, 276);
  ctx.stroke();

  const balloonColors = ["#BF4658", "#729D45", "#4E8AB8", "#C96A44", "#B84E9A", "#5A8C7A"];
  const anchors = [[270, 148], [292, 136], [318, 142], [338, 156], [282, 168], [322, 170]];
  const balloonsLeft = Math.max(MAX_WRONG - state.wrong, 0);

  anchors.forEach(([bx, by], idx) => {
    if (idx < balloonsLeft) {
      ctx.strokeStyle = "#111";
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(301, 182);
      ctx.lineTo(bx, by + 12);
      ctx.stroke();

      ctx.fillStyle = balloonColors[idx];
      ctx.beginPath();
      ctx.ellipse(bx, by - 2, 14, 16, 0, 0, Math.PI * 2);
      ctx.fill();
    } else {
      ctx.strokeStyle = "#BDBDBD";
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.moveTo(bx - 8, by - 8); ctx.lineTo(bx + 8, by + 8);
      ctx.moveTo(bx + 8, by - 8); ctx.lineTo(bx - 8, by + 8);
      ctx.stroke();
    }
  });
}

function maskWord() {
  return [...state.word].map(ch => (state.guessed.has(ch) ? ch : "_")).join(" ");
}

function isWon() {
  return [...state.word].every(ch => state.guessed.has(ch));
}

function stopTimer() {
  if (state.timerId) {
    clearInterval(state.timerId);
    state.timerId = null;
  }
}

function startTimer() {
  stopTimer();
  if (!state.timerEnabled) {
    els.timerText.textContent = "Timer: Off";
    return;
  }
  state.secondsLeft = TURN_SECONDS;
  els.timerText.textContent = `Timer: ${state.secondsLeft}s`;
  state.timerId = setInterval(() => {
    state.secondsLeft -= 1;
    if (state.secondsLeft <= 0) {
      stopTimer();
      state.wrong += 1;
      els.statusText.textContent = "Time up! You lost one attempt.";
      updateUI();
      if (state.wrong >= MAX_WRONG) {
        endGame(false);
      } else {
        startTimer();
      }
      return;
    }
    els.timerText.textContent = `Timer: ${state.secondsLeft}s`;
  }, 1000);
}

function endGame(won) {
  stopTimer();
  [...els.keyboard.querySelectorAll("button")].forEach(btn => { btn.disabled = true; });
  if (won) {
    state.saved += 1;
    state.best = Math.max(state.best, state.saved);
    els.statusText.textContent = "Great job. You saved the character.";
    setTimeout(() => alert(`You won. Word: ${state.word}`), 50);
  } else {
    state.saved = 0;
    els.statusText.textContent = "Game over. Balloons are gone.";
    setTimeout(() => alert(`You lost. Word: ${state.word}`), 50);
  }
  updateUI();
}

function handleGuess(letter) {
  if (state.guessed.has(letter)) return;
  state.guessed.add(letter);
  if (!state.word.includes(letter)) {
    state.wrong += 1;
    els.statusText.textContent = `Nope, ${letter} is not in the word.`;
  } else {
    els.statusText.textContent = `Nice, ${letter} is in the word.`;
  }
  updateUI();
  if (state.wrong >= MAX_WRONG) return endGame(false);
  if (isWon()) return endGame(true);
  if (state.timerEnabled) startTimer();
}

function useHint() {
  if (state.hintsLeft <= 0) return;
  const options = [...new Set(state.word.split(""))].filter(ch => !state.guessed.has(ch));
  if (!options.length) return;
  const letter = options[Math.floor(Math.random() * options.length)];
  state.guessed.add(letter);
  state.hintsLeft -= 1;
  state.wrong += 1;
  els.statusText.textContent = `Hint revealed ${letter}, but cost 1 miss.`;
  updateUI();
  if (state.wrong >= MAX_WRONG) return endGame(false);
  if (isWon()) return endGame(true);
}

function buildKeyboard() {
  els.keyboard.innerHTML = "";
  "ABCDEFGHIJKLMNOPQRSTUVWXYZ".split("").forEach(letter => {
    const btn = document.createElement("button");
    btn.className = "key";
    btn.textContent = letter;
    btn.addEventListener("click", () => handleGuess(letter));
    els.keyboard.appendChild(btn);
  });
}

function updateUI() {
  els.categoryLabel.textContent = state.category;
  els.savedCount.textContent = String(state.saved);
  els.bestCount.textContent = String(state.best);
  els.wordMask.textContent = maskWord();
  els.hintText.textContent = `Hint: ${state.hint}`;
  els.missesText.textContent = `Misses: ${state.wrong}/${MAX_WRONG}`;
  els.hintBtn.textContent = `Hint (${state.hintsLeft})`;
  if (!state.timerEnabled) {
    els.timerText.textContent = "Timer: Off";
  }

  [...els.keyboard.querySelectorAll("button")].forEach(btn => {
    const letter = btn.textContent;
    btn.disabled = state.guessed.has(letter) || state.wrong >= MAX_WRONG || isWon();
  });

  drawScene();
}

function newGame() {
  stopTimer();
  const pick = WORDS[Math.floor(Math.random() * WORDS.length)];
  state.word = pick.word;
  state.hint = pick.hint;
  state.category = pick.category;
  state.guessed = new Set();
  state.wrong = 0;
  state.hintsLeft = 2;
  els.statusText.textContent = "Pick a letter to start.";
  updateUI();
  startTimer();
}

function init() {
  buildKeyboard();
  els.newBtn.addEventListener("click", newGame);
  els.hintBtn.addEventListener("click", useHint);
  els.timerToggle.addEventListener("change", (e) => {
    state.timerEnabled = e.target.checked;
    startTimer();
  });

  window.addEventListener("keydown", (e) => {
    const key = e.key.toUpperCase();
    if (/^[A-Z]$/.test(key)) {
      handleGuess(key);
    }
  });

  newGame();
}

init();
