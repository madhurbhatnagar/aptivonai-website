const posts = [
  {
    handle: "@laserlemons",
    type: "Dance",
    caption: "Trying the hallway shuffle in rain boots.",
    goal: "This is chaotic but weirdly lovable. A like boosts the vibe.",
    bestAction: "like",
  },
  {
    handle: "@pantryoracle",
    type: "Cooking",
    caption: "A 12-part saga about toast seasoning and destiny.",
    goal: "The comments will carry this one. Start the conversation.",
    bestAction: "comment",
  },
  {
    handle: "@crypticcorgi",
    type: "Advice",
    caption: "Explaining taxes using smoke bombs and a unicycle.",
    goal: "The algorithm senses confusion. Skip before the cringe spreads.",
    bestAction: "skip",
  },
  {
    handle: "@glittergarage",
    type: "DIY",
    caption: "I turned a traffic cone into a lamp and I regret nothing.",
    goal: "Bold and bizarre wins hearts. Reward it with a like.",
    bestAction: "like",
  },
  {
    handle: "@bookedandbusy",
    type: "Storytime",
    caption: "My barista accidentally exposed an entire local love triangle.",
    goal: "Messy stories deserve comment chaos. Dive in.",
    bestAction: "comment",
  },
  {
    handle: "@mildlyferal",
    type: "Prank",
    caption: "Pretending to interview pigeons for a startup accelerator.",
    goal: "Fun, quick, and shareable. A like keeps momentum up.",
    bestAction: "like",
  },
  {
    handle: "@snackprophet",
    type: "Review",
    caption: "Ranking office vending machine chips by emotional damage.",
    goal: "People will absolutely argue in the replies. Comment bait.",
    bestAction: "comment",
  },
  {
    handle: "@oopsallgreenscreen",
    type: "Hot Take",
    caption: "Claiming every movie should be 14 minutes long.",
    goal: "Low-value rage bait. Skip it before it tanks retention.",
    bestAction: "skip",
  },
];

const scoreEl = document.querySelector("#score");
const comboEl = document.querySelector("#combo");
const timeEl = document.querySelector("#time");
const creatorHandleEl = document.querySelector("#creatorHandle");
const trendTypeEl = document.querySelector("#trendType");
const captionEl = document.querySelector("#caption");
const goalEl = document.querySelector("#goal");
const cardEl = document.querySelector("#card");
const feedbackEl = document.querySelector("#feedback");
const startPanelEl = document.querySelector("#startPanel");
const endPanelEl = document.querySelector("#endPanel");
const startBtnEl = document.querySelector("#startBtn");
const restartBtnEl = document.querySelector("#restartBtn");
const finalTitleEl = document.querySelector("#finalTitle");
const finalScoreTextEl = document.querySelector("#finalScoreText");
const likeBtnEl = document.querySelector("#likeBtn");
const skipBtnEl = document.querySelector("#skipBtn");
const commentBtnEl = document.querySelector("#commentBtn");

const roundLengthSeconds = 45;
let score = 0;
let combo = 1;
let bestCombo = 1;
let secondsLeft = roundLengthSeconds;
let currentPost = null;
let playing = false;
let timerId = null;
let pointerStart = null;

function shuffle(list) {
  const clone = [...list];
  for (let i = clone.length - 1; i > 0; i -= 1) {
    const j = Math.floor(Math.random() * (i + 1));
    [clone[i], clone[j]] = [clone[j], clone[i]];
  }
  return clone;
}

let queue = shuffle(posts);

function getNextPost() {
  if (queue.length === 0) {
    queue = shuffle(posts);
  }
  return queue.pop();
}

function renderPost(post) {
  creatorHandleEl.textContent = post.handle;
  trendTypeEl.textContent = post.type;
  captionEl.textContent = post.caption;
  goalEl.textContent = post.goal;
}

function updateHud() {
  scoreEl.textContent = score;
  comboEl.textContent = `x${combo}`;
  timeEl.textContent = secondsLeft;
}

function setFeedback(message, goodMove) {
  feedbackEl.textContent = message;
  cardEl.classList.remove("flash-good", "flash-bad");
  void cardEl.offsetWidth;
  cardEl.classList.add(goodMove ? "flash-good" : "flash-bad");
}

function nextRound() {
  currentPost = getNextPost();
  renderPost(currentPost);
  resetCardPosition();
}

function handleAction(action) {
  if (!playing || !currentPost) {
    return;
  }

  const success = action === currentPost.bestAction;

  if (success) {
    score += 100 * combo;
    combo += 1;
    bestCombo = Math.max(bestCombo, combo);
    setFeedback(`Perfect read. ${action} was the move.`, true);
  } else {
    combo = 1;
    score = Math.max(0, score - 60);
    setFeedback(`Algorithm wobble. ${currentPost.bestAction} was stronger here.`, false);
  }

  updateHud();
  animateCardOut(action, nextRound);
}

function animateCardOut(action, onDone) {
  const transforms = {
    like: "translateX(-130%) rotate(-16deg)",
    comment: "translateX(130%) rotate(16deg)",
    skip: "translateY(-130%) rotate(8deg)",
  };

  cardEl.style.transform = transforms[action];
  cardEl.style.opacity = "0";

  window.setTimeout(() => {
    cardEl.style.transition = "none";
    cardEl.style.transform = "translateX(0) translateY(40px) scale(0.95)";
    cardEl.style.opacity = "0";

    requestAnimationFrame(() => {
      cardEl.style.transition = "transform 180ms ease, opacity 180ms ease, box-shadow 180ms ease";
      cardEl.style.transform = "translateX(0) translateY(0) scale(1)";
      cardEl.style.opacity = "1";
      onDone();
    });
  }, 160);
}

function resetCardPosition() {
  cardEl.style.transform = "translateX(0) translateY(0) rotate(0)";
  cardEl.style.opacity = "1";
}

function finishGame() {
  playing = false;
  window.clearInterval(timerId);
  timerId = null;
  endPanelEl.classList.remove("hidden");

  if (score >= 2200) {
    finalTitleEl.textContent = "You broke the For You page.";
  } else if (score >= 1200) {
    finalTitleEl.textContent = "Solid creator instincts.";
  } else {
    finalTitleEl.textContent = "The feed got a little cursed.";
  }

  finalScoreTextEl.textContent = `Final score: ${score}. Highest combo: x${bestCombo}.`;
}

function startGame() {
  score = 0;
  combo = 1;
  bestCombo = 1;
  secondsLeft = roundLengthSeconds;
  playing = true;
  queue = shuffle(posts);

  startPanelEl.classList.add("hidden");
  endPanelEl.classList.add("hidden");
  feedbackEl.textContent = "Swipe the right move to keep the algorithm happy.";

  updateHud();
  nextRound();

  window.clearInterval(timerId);
  timerId = window.setInterval(() => {
    secondsLeft -= 1;
    updateHud();

    if (secondsLeft <= 0) {
      finishGame();
    }
  }, 1000);
}

function actionFromKey(key) {
  if (key === "ArrowLeft") {
    return "like";
  }

  if (key === "ArrowRight") {
    return "comment";
  }

  if (key === "ArrowUp" || key === " ") {
    return "skip";
  }

  return null;
}

function actionFromSwipe(deltaX, deltaY) {
  if (Math.abs(deltaY) > Math.abs(deltaX) && deltaY < -50) {
    return "skip";
  }

  if (deltaX < -50) {
    return "like";
  }

  if (deltaX > 50) {
    return "comment";
  }

  return null;
}

cardEl.addEventListener("pointerdown", (event) => {
  if (!playing) {
    return;
  }

  pointerStart = { x: event.clientX, y: event.clientY };
  cardEl.classList.add("dragging");
});

cardEl.addEventListener("pointermove", (event) => {
  if (!pointerStart || !playing) {
    return;
  }

  const deltaX = event.clientX - pointerStart.x;
  const deltaY = event.clientY - pointerStart.y;
  const rotation = deltaX / 18;
  cardEl.style.transform = `translateX(${deltaX}px) translateY(${deltaY}px) rotate(${rotation}deg)`;
});

cardEl.addEventListener("pointerup", (event) => {
  if (!pointerStart || !playing) {
    return;
  }

  const deltaX = event.clientX - pointerStart.x;
  const deltaY = event.clientY - pointerStart.y;
  const action = actionFromSwipe(deltaX, deltaY);

  pointerStart = null;
  cardEl.classList.remove("dragging");

  if (action) {
    handleAction(action);
  } else {
    resetCardPosition();
  }
});

cardEl.addEventListener("pointercancel", () => {
  pointerStart = null;
  cardEl.classList.remove("dragging");
  resetCardPosition();
});

cardEl.addEventListener("pointerleave", () => {
  if (!pointerStart) {
    return;
  }

  pointerStart = null;
  cardEl.classList.remove("dragging");
  resetCardPosition();
});

document.addEventListener("keydown", (event) => {
  const action = actionFromKey(event.key);

  if (!action) {
    return;
  }

  event.preventDefault();
  handleAction(action);
});

likeBtnEl.addEventListener("click", () => handleAction("like"));
skipBtnEl.addEventListener("click", () => handleAction("skip"));
commentBtnEl.addEventListener("click", () => handleAction("comment"));
startBtnEl.addEventListener("click", startGame);
restartBtnEl.addEventListener("click", startGame);

updateHud();
renderPost(posts[0]);
