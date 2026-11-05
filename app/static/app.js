'use strict';
const PLACES=[
 {label:'Avenida Paulista, São Paulo',lat:-23.5614,lon:-46.6559},
 {label:'Parque Ibirapuera, São Paulo',lat:-23.5874,lon:-46.6576},
 {label:'Estação da Luz, São Paulo',lat:-23.5340,lon:-46.6350},
 {label:'Aeroporto de Congonhas, São Paulo',lat:-23.6261,lon:-46.6564},
 {label:'Praça da Sé, São Paulo',lat:-23.5505,lon:-46.6333},
 {label:'Shopping Metrópole, São Bernardo do Campo',lat:-23.6933,lon:-46.5496}
];
const el=id=>document.getElementById(id);
const format=n=>(n/100).toLocaleString('pt-BR',{style:'currency',currency:'BRL'});
const sessionKey='yawara_move_local_demo';
let session=null;try{session=JSON.parse(sessionStorage.getItem(sessionKey)||'null')}catch(e){session=null}
let lastQuote=null;
function message(t,isError=false){let n=el('alert');n.textContent=t;n.classList.remove('hidden');n.classList.toggle('error',isError);}
function hideMessage(){el('alert').classList.add('hidden')}
function make(tag,text,className){const e=document.createElement(tag);if(text!==undefined)e.textContent=text;if(className)e.className=className;return e}
async function api(path,method='GET',body){const headers={'Content-Type':'application/json'};if(session)headers.Authorization='Bearer '+session.token;let res;try{res=await fetch('/api'+path,{method,headers,body:body?JSON.stringify(body):undefined})}catch(e){throw Error('Não foi possível conectar ao servidor local.')};let data;try{data=await res.json()}catch{throw Error('Resposta inválida do servidor')};if(!res.ok)throw Error(typeof data.detail==='string'?data.detail:'Falha na operação');return data}
async function run(fn){try{hideMessage();await fn()}catch(e){message(e.message||'Falha desconhecida',true)}}
function points(){['origin','destination','driverPoint'].forEach(id=>{let select=el(id);PLACES.forEach((p,i)=>{let o=make('option',p.label);o.value=String(i);select.appendChild(o)})});el('destination').value='1'}
function selected(id){return PLACES[Number(el(id).value)]}
function updateSession(){el('sessionLabel').textContent=session?session.name+' · '+(session.role==='driver'?'motorista':'passageiro'):'Visitante';el('logout').classList.toggle('hidden',!session);el('registration').classList.toggle('hidden',!!session);el('profileInfo').textContent=session?'Conta de teste ativa: '+session.name+'. Perfil '+(session.role==='driver'?'motorista':'passageiro')+'.':'Nenhuma conta de teste ativa.'}
function switchPanel(name){document.querySelectorAll('.nav button').forEach(b=>b.classList.toggle('on',b.dataset.panel===name));['home','rides','driver','about'].forEach(p=>el(p+'Panel').classList.toggle('hidden',p!==name));const texts={home:['Para onde vamos?','A mobilidade do seu jeito, com clareza em cada etapa.'],rides:['Suas viagens','Acompanhe solicitações e viagens demonstrativas.'],driver:['MOVE Driver','Disponibilidade e ofertas de corridas no simulador.'],about:['Sobre o sandbox','Transparência sobre o que é real e o que é simulado.']};el('pageTitle').textContent=texts[name][0];el('pageSubtitle').textContent=texts[name][1];hideMessage();if(name==='rides')run(loadRides);if(name==='driver')run(loadOffers)}
function checkRole(role){if(!session)throw Error('Crie uma conta de teste para continuar.');if(session.role!==role)throw Error('Esta ação exige uma conta de '+(role==='driver'?'motorista':'passageiro')+'.')}
function addAction(box,label,fn){const b=make('button',label);b.addEventListener('click',()=>run(fn));box.appendChild(b)}
function rideCard(r,mode){const d=make('article',undefined,'ride');const head=make('header');head.append(make('span','Corrida #'+r.id.slice(0,7)),make('span',r.status.replace('_',' '),'tag'));d.appendChild(head);d.appendChild(make('div',r.origin+' → '+r.destination,'route'));d.appendChild(make('div',format(r.fare_cents)+' · '+r.km+' km estimados · comissão '+format(r.commission_cents),'minor'));const ac=make('div',undefined,'actions');if(mode==='passenger'){
 if(['requested','accepted'].includes(r.status))addAction(ac,'Cancelar',async()=>{await api('/rides/'+r.id+'/cancel','POST');message('Corrida cancelada.');await loadRides()});
 if(r.status==='completed')addAction(ac,'Simular pagamento',async()=>{const p=await api('/rides/'+r.id+'/simulate-payment','POST');message(p.idempotent?'Pagamento de teste já estava registrado.':'Pagamento de teste registrado — sem cobrança real.');await loadRides()});
}else if(mode==='offers')addAction(ac,'Aceitar corrida',async()=>{await api('/rides/'+r.id+'/accept','POST');message('Oferta aceita com sucesso.');await loadOffers()});else if(mode==='driver'){
 if(r.status==='accepted')addAction(ac,'Iniciar viagem',async()=>{await api('/rides/'+r.id+'/start','POST');await loadRides()});
 if(r.status==='in_progress')addAction(ac,'Concluir viagem',async()=>{await api('/rides/'+r.id+'/complete','POST');await loadRides()});
}d.appendChild(ac);return d}
async function loadRides(){const list=el('rideList');list.replaceChildren();if(!session){list.textContent='Crie uma conta de teste para ver viagens.';el('summary').textContent='Sem sessão.';return};const data=await api('/rides/mine');if(!data.rides.length)list.textContent='Nenhuma viagem encontrada.';for(const r of data.rides)list.appendChild(rideCard(r,session.role));const sum=await api('/summary');el('summary').textContent='Viagens por status: '+(Object.entries(sum.rides_by_status).map(([k,v])=>k+': '+v).join(' · ')||'nenhuma')+' | Valores de teste pagos: '+format(sum.simulated_paid_cents)+' | Comissão de teste: '+format(sum.simulated_commission_cents)}
async function loadOffers(){const list=el('offers');list.replaceChildren();if(!session||session.role!=='driver'){list.textContent='Entre com uma conta de motorista de teste.';return}const data=await api('/rides/available');if(!data.rides.length)list.textContent=data.notice||'Nenhuma oferta próxima no momento.';for(const r of data.rides)list.appendChild(rideCard(r,'offers'))}
function renderQuote(q){const box=el('quoteResult');box.replaceChildren();box.classList.remove('hidden');box.append(make('div','Tarifa estimada ilustrativa','minor'),make('div',format(q.fare_cents),'quote-price'),make('div',q.distance_km_illustrative+' km aproximados · comissão MOVE '+format(q.commission_cents),'quote-meta'));const action=make('button','Solicitar corrida de teste →','primary');action.addEventListener('click',()=>run(async()=>{checkRole('passenger');const r=await api('/rides','POST',{origin:selected('origin'),destination:selected('destination')});message('Solicitação criada (#'+r.ride_id.slice(0,7)+'). Abra Minhas viagens para acompanhar.');}));box.appendChild(action)}
points();updateSession();document.querySelectorAll('.nav button').forEach(b=>b.addEventListener('click',()=>switchPanel(b.dataset.panel)));
el('quote').addEventListener('click',()=>run(async()=>{lastQuote=await api('/quote','POST',{origin:selected('origin'),destination:selected('destination')});renderQuote(lastQuote)}));
el('register').addEventListener('click',()=>run(async()=>{const data=await api('/register','POST',{name:el('personName').value.trim(),role:el('role').value});session=data;sessionStorage.setItem(sessionKey,JSON.stringify(session));updateSession();message('Conta de teste criada. Nenhuma identidade real foi verificada.')}));
el('logout').addEventListener('click',()=>{session=null;sessionStorage.removeItem(sessionKey);updateSession();switchPanel('home');message('Sessão local encerrada.')});
el('refreshRides').addEventListener('click',()=>run(loadRides));
el('refreshOffers').addEventListener('click',()=>run(loadOffers));
el('goOnline').addEventListener('click',()=>run(async()=>{checkRole('driver');const p=selected('driverPoint');await api('/driver/location','POST',{lat:p.lat,lon:p.lon,online:true});message('Motorista disponível em ponto demonstrativo.');await loadOffers()}));
el('goOffline').addEventListener('click',()=>run(async()=>{checkRole('driver');const p=selected('driverPoint');await api('/driver/location','POST',{lat:p.lat,lon:p.lon,online:false});message('Disponibilidade desativada.');await loadOffers()}));

// Modality discovery is informative only: future products are not advertised as available.
document.querySelectorAll('[data-service]').forEach(button=>button.addEventListener('click',()=>{
 if(button.dataset.service==='rides'){document.querySelector('#origin').focus();document.querySelector('#homePanel .columns').scrollIntoView({behavior:window.matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth',block:'start'});return;}
 const names={compare:'MOVE Compare',delivery:'MOVE Entregas',journey:'MOVE Viagens',rental:'MOVE Aluguel',business:'MOVE Business'};
 message((names[button.dataset.service]||'Esta modalidade')+' está em planejamento e ainda não permite solicitar serviços. A simulação de corridas continua disponível.');
 document.querySelector('#alert').scrollIntoView({block:'nearest'});
}));