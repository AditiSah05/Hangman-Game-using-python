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

const DEFAULT_DOC = {
  active_profile: "Player",
  profiles: {
    Player: {
      saved: 0,
      best: 0,
      timerEnabled: false,
      customWords: [],
    },
  },
};

let statsDoc = structuredClone(DEFAULT_DOC);

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
  profileSelect: document.getElementById("profileSelect"),
  addProfileBtn: document.getElementById("addProfileBtn"),
  importPackBtn: document.getElementById("importPackBtn"),
  exportPackBtn: document.getElementById("exportPackBtn"),
  importPackInput: document.getElementById("importPackInput"),
  activeProfileBadge: document.getElementById("activeProfileBadge"),
  progressFill: document.getElementById("progressFill"),
  toastStack: document.getElementById("toastStack"),
  scene: document.getElementById("scene"),
};

function showToast(text) {
  const toast = document.createElement("div");
  toast.className = "toast";
  toast.textContent = text;
  els.toastStack.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateY(-4px)";
    setTimeout(() => toast.remove(), 200);
  }, 1600);
}

function pulseKey(letter, className) {
  const btn = [...els.keyboard.querySelectorAll("button")].find((b) => b.textContent === letter);
  if (!btn) return;
  btn.classList.remove("pop-correct", "pop-wrong");
  btn.classList.add(className);
  setTimeout(() => btn.classList.remove(className), 260);
}

function sanitizeCustomWords(list) {
  if (!Array.isArray(list)) return [];
  const out = [];
  list.forEach((item) => {
    if (!item || typeof item !== "object") return;
    const word = String(item.word || "").trim().toUpperCase();
    const hint = String(item.hint || "").trim();
    if (word.length < 2 || !/^[A-Z]+$/.test(word) || !hint) return;
    out.push({ word, hint: hint.slice(0, 120) });
  });
  return out.slice(0, 200);
}

function normalizeDoc(raw) {
  const doc = structuredClone(DEFAULT_DOC);
  if (!raw || typeof raw !== "object") return doc;

  let active = String(raw.active_profile || raw.player_name || doc.active_profile).trim();
  if (!active) active = doc.active_profile;

  const profiles = {};
  const rawProfiles = raw.profiles;
  if (rawProfiles && typeof rawProfiles === "object") {
    Object.entries(rawProfiles).forEach(([name, profile]) => {
      if (!name || typeof profile !== "object") return;
      const safeName = String(name).trim().slice(0, 20);
      if (!safeName) return;
      profiles[safeName] = {
        saved: Math.max(Number(profile.saved) || 0, 0),
        best: Math.max(Number(profile.best) || 0, 0),
        timerEnabled: Boolean(profile.timerEnabled),
        customWords: sanitizeCustomWords(profile.customWords),
      };
    });
  }

  if (!Object.keys(profiles).length) {
    profiles[active] = {
      saved: Math.max(Number(raw.games_played) || 0, 0),
      best: Math.max(Number(raw.best_streak) || 0, 0),
      timerEnabled: Boolean(raw.timer_enabled),
      customWords: sanitizeCustomWords(raw.custom_words || []),
    };
  }

  if (!profiles[active]) {
    const first = Object.keys(profiles)[0];
    active = first || doc.active_profile;
    if (!profiles[active]) {
      profiles[active] = structuredClone(doc.profiles.Player);
    }
  }

  return {
    ...raw,
    active_profile: active,
    profiles,
  };
}

function activeProfileName() {
  return statsDoc.active_profile;
}

function activeProfile() {
  return statsDoc.profiles[activeProfileName()];
}

async function loadStats() {
  try {
    const res = await fetch("/api/stats");
    if (res.ok) {
      const raw = await res.json();
      statsDoc = normalizeDoc(raw);
      return;
    }
  } catch (_) {
    // Fallback below.
  }

  const local = localStorage.getItem("hangman_frontend_stats");
  if (local) {
    try {
      statsDoc = normalizeDoc(JSON.parse(local));
      return;
    } catch (_) {
      statsDoc = structuredClone(DEFAULT_DOC);
      return;
    }
  }
  statsDoc = structuredClone(DEFAULT_DOC);
}

async function saveStats() {
  const profile = activeProfile();
  const mergedDoc = {
    ...statsDoc,
    player_name: activeProfileName(),
    timer_enabled: profile.timerEnabled,
    custom_words: profile.customWords.map((row) => ({ word: row.word, hint: row.hint })),
    games_played: profile.saved,
    best_streak: profile.best,
  };

  localStorage.setItem("hangman_frontend_stats", JSON.stringify(mergedDoc));
  try {
    await fetch("/api/stats", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(mergedDoc),
    });
  } catch (_) {
    // Local storage already saved; ignore network errors.
  }
}

function rebuildProfileSelect() {
  const names = Object.keys(statsDoc.profiles).sort((a, b) => a.localeCompare(b));
  els.profileSelect.innerHTML = "";
  names.forEach((name) => {
    const opt = document.createElement("option");
    opt.value = name;
    opt.textContent = name;
    if (name === activeProfileName()) opt.selected = true;
    els.profileSelect.appendChild(opt);
  });
  els.activeProfileBadge.textContent = `Active: ${activeProfileName()}`;
}

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

function getWordPool() {
  const profile = activeProfile();
  const custom = profile.customWords.map((row) => ({ word: row.word, hint: row.hint, category: "Custom" }));
  return WORDS.concat(custom);
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
  const profile = activeProfile();
  if (won) {
    state.saved += 1;
    state.best = Math.max(state.best, state.saved);
    profile.saved = state.saved;
    profile.best = state.best;
    els.statusText.textContent = "Great job. You saved the character.";
    showToast("Round won. Nice save.");
    setTimeout(() => alert(`You won. Word: ${state.word}`), 50);
  } else {
    state.saved = 0;
    profile.saved = 0;
    els.statusText.textContent = "Game over. Balloons are gone.";
    showToast("Round lost. Try another word.");
    setTimeout(() => alert(`You lost. Word: ${state.word}`), 50);
  }
  saveStats();
  updateUI();
}

function handleGuess(letter) {
  if (state.guessed.has(letter)) return;
  state.guessed.add(letter);
  if (!state.word.includes(letter)) {
    state.wrong += 1;
    els.statusText.textContent = `Nope, ${letter} is not in the word.`;
    pulseKey(letter, "pop-wrong");
  } else {
    els.statusText.textContent = `Nice, ${letter} is in the word.`;
    pulseKey(letter, "pop-correct");
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
  pulseKey(letter, "pop-correct");
  showToast(`Hint used. Revealed ${letter}.`);
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
  const progress = Math.max(0, ((MAX_WRONG - state.wrong) / MAX_WRONG) * 100);
  els.progressFill.style.width = `${progress}%`;
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
  const pool = getWordPool();
  const pick = pool[Math.floor(Math.random() * pool.length)];
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

function switchProfile(name) {
  const safe = String(name || "").trim();
  if (!safe || !statsDoc.profiles[safe]) return;
  statsDoc.active_profile = safe;
  const profile = activeProfile();
  state.saved = profile.saved;
  state.best = profile.best;
  state.timerEnabled = profile.timerEnabled;
  els.timerToggle.checked = profile.timerEnabled;
  rebuildProfileSelect();
  saveStats();
  showToast(`Switched to ${safe}.`);
  newGame();
}

function addProfile() {
  const input = prompt("Profile name:", "Player2");
  if (!input) return;
  const name = input.trim().slice(0, 20);
  if (!name) return;
  if (!statsDoc.profiles[name]) {
    statsDoc.profiles[name] = { saved: 0, best: 0, timerEnabled: false, customWords: [] };
  }
  showToast(`Profile ${name} ready.`);
  switchProfile(name);
}

function exportPack() {
  const profile = activeProfile();
  const payload = { profile: activeProfileName(), customWords: profile.customWords };
  const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `${activeProfileName().replace(/\s+/g, "_")}_custom_pack.json`;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

function importPackFile(file) {
  if (!file) return;
  const reader = new FileReader();
  reader.onload = async () => {
    try {
      const parsed = JSON.parse(String(reader.result));
      const imported = sanitizeCustomWords(parsed.customWords || parsed);
      const profile = activeProfile();
      profile.customWords = imported;
      await saveStats();
      els.statusText.textContent = `Imported ${imported.length} custom words.`;
      showToast(`Imported ${imported.length} words.`);
      newGame();
    } catch (_) {
      alert("Invalid JSON file for custom pack.");
    }
  };
  reader.readAsText(file);
}

async function init() {
  await loadStats();
  rebuildProfileSelect();
  const profile = activeProfile();
  state.saved = profile.saved;
  state.best = profile.best;
  state.timerEnabled = profile.timerEnabled;
  els.timerToggle.checked = profile.timerEnabled;

  buildKeyboard();
  els.newBtn.addEventListener("click", newGame);
  els.hintBtn.addEventListener("click", useHint);
  els.timerToggle.addEventListener("change", (e) => {
    state.timerEnabled = e.target.checked;
    activeProfile().timerEnabled = state.timerEnabled;
    saveStats();
    startTimer();
  });

  els.profileSelect.addEventListener("change", (e) => {
    switchProfile(e.target.value);
  });

  els.addProfileBtn.addEventListener("click", addProfile);
  els.exportPackBtn.addEventListener("click", exportPack);
  els.importPackBtn.addEventListener("click", () => els.importPackInput.click());
  els.importPackInput.addEventListener("change", (e) => {
    importPackFile(e.target.files[0]);
    e.target.value = "";
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
