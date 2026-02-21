let state = {
  scenarios: [],
  responses: [],
  players: [],
  discard: [],
  currentScenario: null,
  judgeIndex: 0,
  playIndex: 0,
  played: [],
  category: 'basic',
  playerCount: 4
};

const $ = id => document.getElementById(id);

// Simple on-page debug logger so we can see errors in the browser without devtools
function debugLog(msg){
  try{
    let d = document.getElementById('debugLog');
    if(!d){
      d = document.createElement('div'); d.id = 'debugLog';
      d.style.cssText = 'position:fixed;right:12px;bottom:12px;max-width:320px;max-height:200px;overflow:auto;background:rgba(0,0,0,0.7);color:#fff;padding:8px;border-radius:6px;font-size:12px;z-index:9999';
      document.body.appendChild(d);
    }
    const p = document.createElement('div'); p.textContent = (new Date()).toLocaleTimeString() + ' — ' + msg; d.appendChild(p); d.scrollTop = d.scrollHeight;
  }catch(e){ /* ignore */ }
}

// surface runtime errors to the page for easier debugging
window.addEventListener('error', (ev)=>{
  debugLog('Error: ' + (ev && ev.message) + ' at ' + (ev && ev.filename) + ':' + (ev && ev.lineno));
});
window.addEventListener('unhandledrejection', (ev)=>{
  debugLog('UnhandledRejection: ' + (ev && ev.reason && ev.reason.toString()));
});

// Avatar colors for players
const avatarColors = ['#6366f1', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#06b6d4', '#14b8a6', '#f97316', '#6b7280', '#a16207', '#7c3aed'];

// Simple beep sounds (using Web Audio API)
function playSound(type = 'select'){
  try {
    const audioContext = new (window.AudioContext || window.webkitAudioContext)();
    const oscillator = audioContext.createOscillator();
    const gainNode = audioContext.createGain();
    
    oscillator.connect(gainNode);
    gainNode.connect(audioContext.destination);
    
    if(type === 'select'){
      oscillator.frequency.value = 800;
      gainNode.gain.setValueAtTime(0.1, audioContext.currentTime);
      gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.1);
      oscillator.start(audioContext.currentTime);
      oscillator.stop(audioContext.currentTime + 0.1);
    } else if(type === 'reveal'){
      oscillator.frequency.value = 600;
      gainNode.gain.setValueAtTime(0.1, audioContext.currentTime);
      gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.3);
      oscillator.start(audioContext.currentTime);
      oscillator.stop(audioContext.currentTime + 0.3);
    } else if(type === 'ding'){
      oscillator.frequency.value = 1000;
      gainNode.gain.setValueAtTime(0.1, audioContext.currentTime);
      gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.2);
      oscillator.start(audioContext.currentTime);
      oscillator.stop(audioContext.currentTime + 0.2);
    }
  } catch(e){
    // audio not supported
  }
}

async function loadCards(){
  try{
    const res = await fetch('data/cards.json');
    if(!res.ok) throw new Error('HTTP '+res.status+' fetching cards.json');
    const data = await res.json();
    state.categoryData = data;
    debugLog('Loaded cards.json — categories: ' + Object.keys(data).join(','));
  }catch(err){
    debugLog('loadCards error: ' + err.message);
    throw err;
  }
}

function loadCategory(cat){
  state.category = cat;
  const catData = state.categoryData[cat];
  state.scenarios = catData.scenarios.slice();
  state.responses = catData.responses.slice();
}

function shuffle(arr){
  for(let i=arr.length-1;i>0;i--){
    const j=Math.floor(Math.random()*(i+1));[arr[i],arr[j]]=[arr[j],arr[i]]
  }
}

function fillBlanks(scenario){
  // if scenario has blanks (_____ pattern), return as-is for display
  return scenario;
}

function countBlanks(scenario){
  // count occurrences of _____
  const matches = scenario.match(/_____/g);
  const count = matches ? matches.length : 0;
  // always require at least 1 card response
  return Math.max(1, count);
}

function showPlayerSetup(){
  state.playerCount = Math.max(3,Math.min(12,parseInt($('playerCount').value||4)));
  if(!$('customNames').checked){
    // skip directly to game with default names
    initializeGame(null);
    return;
  }
  // show name input screen
  const inputs = $('playerInputs');
  inputs.innerHTML = '';
  for(let i=0; i<state.playerCount; i++){
    const div = document.createElement('div');
    div.className = 'playerInput';
    const avatar = document.createElement('div');
    avatar.className = 'playerAvatar';
    avatar.style.backgroundColor = avatarColors[i];
    avatar.textContent = i+1;
    const input = document.createElement('input');
    input.type = 'text';
    input.placeholder = `Player ${i+1} name`;
    input.maxLength = 20;
    div.appendChild(avatar);
    div.appendChild(input);
    inputs.appendChild(div);
  }
  $('setup').classList.add('hidden');
  $('playerSetup').classList.remove('hidden');
}

function initializeGame(names){
  const cat = $('categorySelect').value;
  loadCategory(cat);
  
  if(names && names.length > 0){
    state.players = names.map((name, i) => ({
      id: i+1,
      name: name || `Player ${i+1}`,
      score: 0,
      hand: [],
      color: avatarColors[i]
    }));
  } else {
    state.players = Array.from({length: state.playerCount}, (_,i) => ({
      id: i+1,
      name: `Player ${i+1}`,
      score: 0,
      hand: [],
      color: avatarColors[i]
    }));
  }
  
  shuffle(state.responses);
  // deal 7 each
  for(let p of state.players){
    for(let i=0;i<7;i++) p.hand.push(drawResponse());
  }
  state.judgeIndex = 0; state.playIndex = 0; state.played = [];
  $('setup').classList.add('hidden');
  $('playerSetup').classList.add('hidden');
  $('game').classList.remove('hidden');
  nextRound();
}

function drawResponse(){
  if(state.responses.length===0){
    state.responses = state.discard.slice(); state.discard = []; shuffle(state.responses);
  }
  return state.responses.pop();
}

function nextRound(){
  state.played = [];
  state.currentScenario = state.scenarios.length?state.scenarios.shift(): 'No more scenarios.';
  state.playIndex = 0;
  renderRound();
}

function renderRound(){
  $('scenarioText').textContent = fillBlanks(state.currentScenario);
  const judge = state.players[state.judgeIndex];
  $('roundInfo').textContent = `Judge: ${judge.name}`;
  renderScoreboard();
  startPlayTurn();
}

function renderScoreboard(){
  const sb = $('scoreboard'); sb.innerHTML='';
  state.players.forEach(p=>{
    const d=document.createElement('div');d.className='score';
    d.innerHTML = `<span style="display:inline-block;width:16px;height:16px;background:${p.color};border-radius:50%;margin-right:8px;vertical-align:middle;"></span>${p.name}: ${p.score}`;
    sb.appendChild(d);
  });
}

function startPlayTurn(){
  // find next player who is not judge
  if(state.playIndex >= state.players.length -1){
    // all played
    showPlayedForJudge(); return;
  }
  // determine which player to show (skip judge)
  let idx = (state.judgeIndex + 1 + state.playIndex) % state.players.length;
  const player = state.players[idx];
  const blanksNeeded = countBlanks(state.currentScenario);
  $('turnLabel').textContent = `${player.name}'s turn to play (select ${blanksNeeded} card${blanksNeeded>1?'s':''})`;
  const hand = $('hand'); 
  hand.innerHTML='';
  
  let selectedCards = [];
  const cardEls = [];
  
  player.hand.forEach((card,i)=>{
    const el=document.createElement('div');el.className='card';el.textContent=card;
    cardEls[i] = el;
    el.onclick=()=>{ 
      playSound('select');
      if(selectedCards.includes(i)){
        selectedCards = selectedCards.filter(x => x !== i);
        el.classList.remove('selected');
      } else if(selectedCards.length < blanksNeeded){
        selectedCards.push(i);
        el.classList.add('selected');
      }
      // for single blank, auto-play when card selected
      if(blanksNeeded === 1 && selectedCards.length === 1){
        playCard(idx, selectedCards[0]);
        return;
      }
    };
    hand.appendChild(el);
  });
  
  // only show play button for multi-card scenarios
  if(blanksNeeded > 1){
    const br = document.createElement('div');br.style.width = '100%';br.style.height = '0';
    hand.appendChild(br);
    const submitBtn = document.createElement('button');
    submitBtn.textContent = `Play ${blanksNeeded} cards`;
    submitBtn.style.marginTop = '12px';
    submitBtn.onclick = () => {
      if(selectedCards.length === blanksNeeded){
        playCard(idx, selectedCards.slice());
      }
    };
    hand.appendChild(submitBtn);
  }
  
  $('playerTurn').classList.remove('hidden'); $('playedArea').classList.add('hidden');
  $('nextTurnBtn').classList.add('hidden'); $('judgePickBtn').classList.add('hidden'); $('nextRoundBtn').classList.add('hidden');
}

function playCard(playerIdx, indicesOrIndex){
  const player = state.players[playerIdx];
  let cards = [];
  
  if(Array.isArray(indicesOrIndex)){
    // multiple card indices selected - remove in reverse order to avoid index shifting
    const sortedIndices = indicesOrIndex.sort((a,b) => b-a);
    cards = sortedIndices.map(i => player.hand[i]);
    sortedIndices.forEach(i => player.hand.splice(i,1));
  } else {
    // single card index
    cards = [player.hand[indicesOrIndex]];
    player.hand.splice(indicesOrIndex, 1);
  }
  
  // combine card responses with a /
  const combinedCard = cards.join(' / ');
  state.played.push({card: combinedCard, player: playerIdx});
  state.playIndex++;
  
  // show "pass to next" screen instead of auto-advancing
  showPassToNext();
}

function showPassToNext(){
  // determine next player (skip judge)
  let nextIdx = (state.judgeIndex + 1 + state.playIndex) % state.players.length;
  
  if(state.playIndex >= state.players.length -1){
    // all players have played, show for judge
    showPlayedForJudge();
  } else {
    const nextPlayer = state.players[nextIdx];
    $('playerTurn').classList.add('hidden');
    $('playedArea').classList.add('hidden');
    $('roundInfo').textContent = `${nextPlayer.name}, it's your turn! Tap "Ready" when you have the device.`;
    $('nextTurnBtn').textContent = 'Ready';
    $('nextTurnBtn').classList.remove('hidden');
    $('nextTurnBtn').onclick = () => startPlayTurn();
    $('judgePickBtn').classList.add('hidden');
    $('nextRoundBtn').classList.add('hidden');
  }
}

function showPlayedForJudge(){
  playSound('reveal');
  $('playerTurn').classList.add('hidden');
  $('playedArea').classList.remove('hidden');
  const pc = $('playedCards'); pc.innerHTML='';
  // shuffle anonymous presentation
  const shuffled = state.played.slice(); shuffle(shuffled);
  shuffled.forEach((p,i)=>{
    const el=document.createElement('div');el.className='card';el.textContent=p.card;
    el.onclick=()=>judgePick(p);
    pc.appendChild(el);
  });
  $('nextTurnBtn').classList.add('hidden'); $('judgePickBtn').classList.remove('hidden');
}

function judgePick(play){
  playSound('ding');
  // award point
  state.players[play.player].score++;
  // move played to discard
  state.played.forEach(p=>state.discard.push(p.card));
  // refill hands to 7
  state.players.forEach(p=>{while(p.hand.length<7) p.hand.push(drawResponse())});
  // advance judge
  state.judgeIndex = (state.judgeIndex+1) % state.players.length;
  renderScoreboard();
  $('judgePickBtn').classList.add('hidden'); $('nextRoundBtn').classList.remove('hidden');
}

document.addEventListener('DOMContentLoaded',async()=>{
  await loadCards();
  // Attach Start click handler and log for debugging
  try{
    const start = $('startBtn');
    if(start){ start.onclick = showPlayerSetup; debugLog('startBtn handler attached'); }
    else debugLog('startBtn not found');
  }catch(e){ debugLog('attach startBtn error: '+e.message); }
  $('startGameBtn').onclick=()=>{
    const names = Array.from($('playerInputs').querySelectorAll('input')).map(inp => inp.value.trim());
    initializeGame(names);
  };
  $('skipNamesBtn').onclick=()=>{ initializeGame(null); };
  $('nextTurnBtn').onclick=()=>{ startPlayTurn(); };
  $('judgePickBtn').onclick=()=>{ /* revealed already clickable */ };
  $('nextRoundBtn').onclick=()=>{ nextRound(); $('nextRoundBtn').classList.add('hidden'); };
});
