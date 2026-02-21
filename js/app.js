let state = {
  scenarios: [],
  responses: [],
  players: [],
  discard: [],
  currentScenario: null,
  judgeIndex: 0,
  playIndex: 0,
  played: []
};

const $ = id => document.getElementById(id);

async function loadCards(){
  const res = await fetch('data/cards.json');
  const data = await res.json();
  state.scenarios = data.scenarios.slice();
  state.responses = data.responses.slice();
}

function shuffle(arr){
  for(let i=arr.length-1;i>0;i--){
    const j=Math.floor(Math.random()*(i+1));[arr[i],arr[j]]=[arr[j],arr[i]]
  }
}

function startGame(){
  const count = Math.max(3,Math.min(12,parseInt($('playerCount').value||4)));
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
  $('scenarioText').textContent = state.currentScenario;
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
  $('turnLabel').textContent = `Player ${player.id}'s turn to play`;
  const hand = $('hand'); hand.innerHTML='';
  player.hand.forEach((card,i)=>{
    const el=document.createElement('div');el.className='card';el.textContent=card;
    el.onclick=()=>{ playCard(idx,i); };
    hand.appendChild(el);
  });
  $('playerTurn').classList.remove('hidden'); $('playedArea').classList.add('hidden');
  $('nextTurnBtn').classList.remove('hidden'); $('judgePickBtn').classList.add('hidden'); $('nextRoundBtn').classList.add('hidden');
}

function playCard(playerIdx,handIdx){
  const card = state.players[playerIdx].hand.splice(handIdx,1)[0];
  state.played.push({card,player:playerIdx});
  state.playIndex++;
  // auto-advance to next player
  if(state.playIndex >= state.players.length -1) showPlayedForJudge(); else startPlayTurn();
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
