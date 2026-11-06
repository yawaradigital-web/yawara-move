'use strict';
/* Real-address lookup is an optional information-only preview. It never changes ride coordinates. */
(() => {
  const form=document.getElementById('addressPreviewForm');
  const input=document.getElementById('addressPreviewInput');
  const button=document.getElementById('addressPreviewButton');
  const status=document.getElementById('addressPreviewStatus');
  const results=document.getElementById('addressPreviewResults');
  if(!form||!input||!button||!status||!results)return;
  let available=false;
  let pending=false;
  button.disabled=true;
  async function checkProvider(){
    try{
      const response=await fetch('/api/address-preview/status',{headers:{Accept:'application/json'},cache:'no-store'});
      if(!response.ok)throw Error('status unavailable');
      const data=await response.json();
      available=data.enabled===true&&data.mode==='preview_only';
      button.disabled=!available;
      status.textContent=available
        ?'Busca de endereços disponível somente para prévia informativa. Nenhuma corrida será criada.'
        :'Busca externa ainda não configurada. A pesquisa local de seis pontos acima continua disponível.';
    }catch(err){
      available=false;button.disabled=true;
      status.textContent='Não foi possível verificar o serviço externo. Use os pontos demonstrativos acima.';
    }
  }
  form.addEventListener('submit',async event=>{
    event.preventDefault();
    if(!available||pending)return;
    const text=input.value.trim().replace(/\s+/g,' ');
    if(text.length<4||text.length>100){
      status.textContent='Digite de 4 a 100 caracteres para consultar.';
      return;
    }
    results.replaceChildren();
    pending=true;button.disabled=true;status.textContent='Buscando endereços…';
    try{
      const response=await fetch('/api/address-preview',{
        method:'POST',headers:{'Content-Type':'application/json',Accept:'application/json'},
        cache:'no-store',body:JSON.stringify({text})
      });
      const data=await response.json();
      if(!response.ok)throw Error(typeof data.detail==='string'?data.detail:'Não foi possível buscar endereços.');
      if(data.mode!=='preview_only'||!Array.isArray(data.results))throw Error('Resposta inválida.');
      for(const place of data.results){
        if(typeof place.label!=='string'||typeof place.lat!=='number'||typeof place.lon!=='number')continue;
        const item=document.createElement('div');item.className='address-preview-item';
        const title=document.createElement('strong');title.textContent=place.label;
        const hint=document.createElement('small');hint.textContent='Endereço informativo · não utilizável para reservar ou simular corrida';
        item.append(title,hint);results.append(item);
      }
      status.textContent=results.childElementCount
        ?results.childElementCount+' endereço(s) encontrado(s). Somente visualização, sem ação de viagem.'
        :'Nenhum endereço encontrado. Tente um termo mais específico.';
    }catch(err){status.textContent=err.message||'Erro na consulta. Os pontos demonstrativos continuam disponíveis.';}
    finally{pending=false;button.disabled=!available;}
  });
  checkProvider();
})();