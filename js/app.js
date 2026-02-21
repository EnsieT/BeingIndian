let state = {
  scenarios: [],
  responses: [],
  players: [],
  discard: [],
  currentScenario: null,
  judgeIndex: 0,
  playIndex: 0,
  played: [],
  category: 'basic'
};

const $ = id => document.getElementById(id);

async function loadCards(){
  const res = await fetch('data/cards.json');
  const data = await res.json();
  state.categoryData = data.categories;
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
  return matches ? matches.length : 0;
}

function startGame(){
  const cat = $('categorySelect').value;
  const count = Math.max(3,Math.min(12,parseInt($('playerCount').value||4)));
  loadCategory(cat);
  state.players = Array.from({length:count},(_,i)=>({id:i+1,score:0,hand:[]}));
  shuffle(state.responses);
  // deal 7 each
  for(let p of state.players){
    for(let i=0;i<7;i++) p.hand.push(drawResponse());
  }
  state.judgeIndex = 0; state.playIndex = 0; state.played = [];
  $('setup').classList.add('hidden'); $('game').classList.remove('hidden');
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
  $('roundInfo').textContent = `Judge: Player ${state.judgeIndex+1}`;
  renderScoreboard();
  startPlayTurn();
}

function renderScoreboard(){
  const sb = $('scoreboard'); sb.innerHTML='';
  state.players.forEach(p=>{const d=document.createElement('div');d.className='score';d.textContent=`P${p.id}: ${p.score}`;sb.appendChild(d)});
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
  $('turnLabel').textContent = `Player ${player.id}'s turn to play (select ${blanksNeeded} card${blanksNeeded>1?'s':''})`;
  const hand = $('hand'); 
  hand.innerHTML='';
  
  let selectedCards = [];
  const cardEls = [];
  
  player.hand.forEach((card,i)=>{
    const el=document.createElement('div');el.className='card';el.textContent=card;
    cardEls[i] = el;
    el.onclick=()=>{ 
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
    $('roundInfo').textContent = `Player ${nextPlayer.id}, it's your turn! Tap "Ready" when you have the device.`;
    $('nextTurnBtn').textContent = 'Ready';
    $('nextTurnBtn').classList.remove('hidden');
    $('nextTurnBtn').onclick = () => startPlayTurn();
    $('judgePickBtn').classList.add('hidden');
    $('nextRoundBtn').classList.add('hidden');
  }
}

function showPlayedForJudge(){
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
  $('startBtn').onclick=startGame;
  $('nextTurnBtn').onclick=()=>{ startPlayTurn(); };
  $('judgePickBtn').onclick=()=>{ /* revealed already clickable */ };
  $('nextRoundBtn').onclick=()=>{ nextRound(); $('nextRoundBtn').classList.add('hidden'); };
});
