/* Yawara Live event and ranking engine v1 — pure functions, no TikTok dependency. */
(function(root){
'use strict';
const FAN_POINTS=Object.freeze({like:1,share:1,follow:5,heart_me:5,super_fan:10});
const ONCE=new Set(['follow','heart_me','super_fan']);
const BOARD_ROLES=['Presidente','Vice-presidente','Diretor de Futebol','Técnico','Capitão','Atacante','Goleiro'];
const FAN_ROLES=['Líder da Torcida','Vice-líder','Organizador','Puxador de Canto','Camisa 12','Animador','Torcedor Destaque'];
function fresh(){return {participants:{},processed:{},events:[],sequence:0};}
function clone(x){return JSON.parse(JSON.stringify(x));}
function join(state,id,club,name){
 if(!id||!club)throw Error('Identificador e clube obrigatórios');
 if(state.participants[id])throw Error('Participante já inscrito');
 const next=clone(state);next.participants[id]={id,club,name:name||id,giftPoints:0,fanPoints:0,joined:next.sequence++,giftReached:0,fanReached:0,once:{}};return next;
}
function event(state,e,giftRules){
 if(!e||!e.id||!e.userId||!e.type)throw Error('Evento incompleto');
 if(state.processed[e.id])return {state,duplicate:true,awarded:0};
 const u=state.participants[e.userId];if(!u)throw Error('Participante inexistente');
 const units=e.units===undefined?1:e.units;
 if(!Number.isSafeInteger(units)||units<1||units>100000)throw Error('Quantidade inválida');
 if(ONCE.has(e.type)&&units!==1)throw Error('Evento único não aceita quantidade');
 if(ONCE.has(e.type)&&u.once[e.type])return {state,duplicate:true,awarded:0};
 let points,category;
 if(e.type==='gift'){
   const perUnit=giftRules&&giftRules[e.giftId];
   if(!Number.isSafeInteger(perUnit)||perUnit<1)throw Error('Presente não configurado');
   points=perUnit*units;category='gift';
 }else if(Object.prototype.hasOwnProperty.call(FAN_POINTS,e.type)){
   points=FAN_POINTS[e.type]*units;category='fan';
 }else throw Error('Tipo de evento desconhecido');
 if(!Number.isSafeInteger(points)||points<=0)throw Error('Pontos inválidos');
 const next=clone(state),p=next.participants[e.userId];if(category==='gift'){p.giftPoints+=points;p.giftReached=next.sequence++;}else{p.fanPoints+=points;p.fanReached=next.sequence++;}
 if(ONCE.has(e.type))p.once[e.type]=true;
 next.processed[e.id]=true;next.events.push({id:e.id,userId:e.userId,type:e.type,units,points,category});
 return {state:next,duplicate:false,awarded:points};
}
function ranking(state,club,kind){
 const key=kind==='gift'?'giftPoints':kind==='fan'?'fanPoints':null;
 if(!key)throw Error('Ranking inválido');
 const reached=kind==='gift'?'giftReached':'fanReached',roles=kind==='gift'?BOARD_ROLES:FAN_ROLES;
 return Object.values(state.participants).filter(p=>p.club===club&&p[key]>0).sort((a,b)=>b[key]-a[key]||a[reached]-b[reached]||a.joined-b.joined).map((p,i)=>({id:p.id,name:p.name,points:p[key],position:i+1,role:roles[i]||'Participante'}));
}
function score(state,club){return Object.values(state.participants).filter(p=>p.club===club).reduce((s,p)=>({gift:s.gift+p.giftPoints,fan:s.fan+p.fanPoints,total:s.total+p.giftPoints+p.fanPoints}),{gift:0,fan:0,total:0});}
const api={fresh,join,event,ranking,score,FAN_POINTS,BOARD_ROLES,FAN_ROLES};
if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.YawaraEngine=api;
})(typeof globalThis!=='undefined'?globalThis:this);
