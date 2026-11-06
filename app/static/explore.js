'use strict';
const PLACES=[
 {label:'Avenida Paulista, São Paulo',lat:-23.5614,lon:-46.6559},
 {label:'Parque Ibirapuera, São Paulo',lat:-23.5874,lon:-46.6576},
 {label:'Estação da Luz, São Paulo',lat:-23.5340,lon:-46.6350},
 {label:'Aeroporto de Congonhas, São Paulo',lat:-23.6261,lon:-46.6564},
 {label:'Praça da Sé, São Paulo',lat:-23.5505,lon:-46.6333},
 {label:'Shopping Metrópole, São Bernardo do Campo',lat:-23.6933,lon:-46.5496}
];
const content=document.getElementById('experience');
const esc=value=>String(value).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;');
const options=()=>PLACES.map((p,i)=>'<option value="'+i+'">'+esc(p.label)+'</option>').join('');
const descriptions={
 entregas:['MOVE Entregas','Planeje entregas de documentos, pacotes e cargas com veículos adequados, acompanhamento e confirmação de recebimento.','Protótipo informativo. Nenhuma coleta, despacho ou entrega disponível.'],
 viagens:['MOVE Viagens','Compare conceitos de caronas, viagens rodoviárias, trechos e horários em uma experiência unificada.','Protótipo informativo. Nenhum bilhete, reserva ou parceria comercial disponível.'],
 aluguel:['MOVE Aluguel','Explore um conceito de aluguel digital de veículos, categorias, horários e regras transparentes.','Protótipo informativo. Nenhum carro disponível para reserva.'],
 business:['MOVE Business','Central futura para empresas administrarem mobilidade, entregas, centros de custo e relatórios.','Protótipo informativo. Não há contrato, faturamento ou contas corporativas ativas.']
};
function selectedPoint(id){return PLACES[Number(document.getElementById(id).value)];}
function routeMarkup(){return '<h2>Para onde vamos?</h2><p>Selecione pontos de referência para testar uma estimativa fictícia.</p><div class="field"><label for="origin">Origem</label><select id="origin">'+options()+'</select></div><div class="field"><label for="destination">Destino</label><select id="destination">'+options()+'</select></div><button class="primary" id="estimate" type="button">Ver estimativa de teste</button><div id="estimateResult" role="status" aria-live="polite"></div>';}
function showInfo(key){const d=descriptions[key];content.innerHTML='<h2>'+d[0]+'</h2><p>'+d[1]+'</p><div class="result"><strong>Em desenvolvimento</strong><p class="fine">'+d[2]+'</p></div><button class="primary" id="backRoute" type="button">Testar uma corrida fictícia</button>';document.getElementById('backRoute').addEventListener('click',()=>activate('corridas'));}
function activate(key){
 document.querySelectorAll('[data-tab]').forEach(b=>b.setAttribute('aria-selected',String(b.dataset.tab===key)));
 if(descriptions[key]){showInfo(key);return;}
 content.innerHTML=routeMarkup();
 document.getElementById('destination').value='1';
 document.querySelector('#estimate').addEventListener('click',quote);
 if(key==='comparar')content.insertAdjacentHTML('afterbegin','<div class="notice">Comparação demonstrativa: somente MOVE possui um valor ilustrativo. Sem dados de terceiros.</div>');
}
async function quote(){
 const a=selectedPoint('origin'),b=selectedPoint('destination'),out=document.getElementById('estimateResult');
 if(!a||!b||a===b){out.textContent='Escolha locais diferentes.';return;}
 out.textContent='Calculando simulação...';
 try{
  const response=await fetch('/api/quote',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({origin:a,destination:b})});
  const q=await response.json();
  if(!response.ok)throw Error(typeof q.detail==='string'?q.detail:'Não foi possível calcular.');
  const money=value=>(value/100).toLocaleString('pt-BR',{style:'currency',currency:'BRL'});
  out.replaceChildren();
  const card=document.createElement('div');card.className='result';
  const title=document.createElement('strong');title.textContent='MOVE Corridas · valor fictício';
  const fare=document.createElement('h2');fare.textContent=money(q.fare_cents);
  const desc=document.createElement('p');desc.className='fine';desc.textContent=q.distance_km_illustrative+' km estimados por fator educativo · comissão simulada de '+money(q.commission_cents)+'.';
  const info=document.createElement('p');info.className='fine';info.textContent='Sem preço, tempo de chegada ou disponibilidade de terceiros. Nenhuma corrida foi solicitada.';
  card.append(title,fare,desc,info);out.append(card);
 }catch(e){out.textContent='Falha na consulta de simulação. '+(e.message||'');}
}
document.querySelectorAll('[data-tab]').forEach(b=>b.addEventListener('click',()=>activate(b.dataset.tab)));
activate('corridas');
