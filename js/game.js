// BilimSari Game State — XP, Streak, Hearts, Gems, Progress
const BS_KEY = 'bilimsari_game_v1';

const DEFAULT_STATE = {
  xp: 0,
  gems: 50,
  hearts: 5,
  maxHearts: 5,
  streak: 0,
  lastActiveDate: null,
  dailyGoal: 20,
  dailyXp: 0,
  dailyGoalDate: null,
  completedLessons: {}, // courseId -> [lessonIds]
  lessonStats: {}, // lessonId -> { attempts, correct, wrong }
  wrongQueue: [], // for review
  achievements: [],
  displayName: null,
};

function todayStr() {
  return new Date().toISOString().slice(0, 10);
}

function loadGame() {
  try {
    const raw = localStorage.getItem(BS_KEY);
    if (!raw) return { ...DEFAULT_STATE };
    return { ...DEFAULT_STATE, ...JSON.parse(raw) };
  } catch {
    return { ...DEFAULT_STATE };
  }
}

function saveGame(state) {
  localStorage.setItem(BS_KEY, JSON.stringify(state));
}

function getGame() {
  const s = loadGame();
  // Yurak/shans o'chirilgan
  s.hearts = s.maxHearts || 5;
  // Daily reset for dailyXp
  const today = todayStr();
  if (s.dailyGoalDate !== today) {
    s.dailyXp = 0;
    s.dailyGoalDate = today;
    saveGame(s);
  }
  // Hearts regenerate slowly: +1 every 4h offline concept simplified — full hearts after new day if 0? 
  // Keep simple: practice restores hearts
  return s;
}

function updateGame(mutator) {
  const s = getGame();
  mutator(s);
  saveGame(s);
  return s;
}

function addXp(amount) {
  return updateGame(s => {
    s.xp += amount;
    s.dailyXp += amount;
  });
}

function addGems(amount) {
  return updateGame(s => { s.gems += amount; });
}

function loseHeart() {
  // Yurak tizimi o'chirilgan — hech narsa kamaymaydi
  return getGame();
}

function restoreHeart(n = 1) {
  return getGame();
}

function refillHearts() {
  return getGame();
}

function markLessonComplete(courseId, lessonId, accuracy) {
  return updateGame(s => {
    if (!s.completedLessons[courseId]) s.completedLessons[courseId] = [];
    if (!s.completedLessons[courseId].includes(lessonId)) {
      s.completedLessons[courseId].push(lessonId);
    }
    // Streak
    const today = todayStr();
    if (s.lastActiveDate !== today) {
      const yesterday = new Date();
      yesterday.setDate(yesterday.getDate() - 1);
      const yStr = yesterday.toISOString().slice(0, 10);
      if (s.lastActiveDate === yStr) s.streak += 1;
      else if (s.lastActiveDate !== today) s.streak = 1;
      s.lastActiveDate = today;
    }
    // Achievements
    unlockAchievements(s);
  });
}

function isLessonDone(courseId, lessonId) {
  const s = getGame();
  return (s.completedLessons[courseId] || []).includes(lessonId);
}

function courseProgress(courseId, totalLessons) {
  const done = (getGame().completedLessons[courseId] || []).length;
  return { done, total: totalLessons, pct: totalLessons ? Math.round(done / totalLessons * 100) : 0 };
}

function unlockAchievements(s) {
  const checks = [
    { id: 'streak_7', cond: s.streak >= 7 },
    { id: 'streak_30', cond: s.streak >= 30 },
    { id: 'xp_1000', cond: s.xp >= 1000 },
    { id: 'xp_5000', cond: s.xp >= 5000 },
    { id: 'lessons_10', cond: Object.values(s.completedLessons).flat().length >= 10 },
    { id: 'lessons_50', cond: Object.values(s.completedLessons).flat().length >= 50 },
  ];
  checks.forEach(a => {
    if (a.cond && !s.achievements.includes(a.id)) s.achievements.push(a.id);
  });
}

function pushWrong(item) {
  updateGame(s => {
    s.wrongQueue = s.wrongQueue.filter(w => w.id !== item.id);
    s.wrongQueue.unshift(item);
    s.wrongQueue = s.wrongQueue.slice(0, 100);
  });
}

function levelFromXp(xp) {
  return Math.floor(xp / 100) + 1;
}

// Floating XP animation helper
function showFloatingXp(amount, el) {
  const node = document.createElement('div');
  node.textContent = `+${amount} XP`;
  node.style.cssText = `
    position:fixed; z-index:9999; pointer-events:none;
    font-weight:800; font-size:18px; color:#58A700;
    animation: bsFloatXp .9s ease forwards;
  `;
  const r = el ? el.getBoundingClientRect() : { left: window.innerWidth/2, top: window.innerHeight/2 };
  node.style.left = (r.left + (r.width||0)/2) + 'px';
  node.style.top = (r.top || window.innerHeight/3) + 'px';
  document.body.appendChild(node);
  setTimeout(() => node.remove(), 900);
}

// Inject keyframes once
(function() {
  if (document.getElementById('bs-game-style')) return;
  const s = document.createElement('style');
  s.id = 'bs-game-style';
  s.textContent = `
    @keyframes bsFloatXp {
      0% { opacity:1; transform: translate(-50%,0); }
      100% { opacity:0; transform: translate(-50%,-40px); }
    }
    @keyframes bsShake {
      0%,100% { transform: translateX(0); }
      20% { transform: translateX(-6px); }
      40% { transform: translateX(6px); }
      60% { transform: translateX(-4px); }
      80% { transform: translateX(4px); }
    }
    .bs-shake { animation: bsShake .4s ease; }
  `;
  document.head.appendChild(s);
})();
