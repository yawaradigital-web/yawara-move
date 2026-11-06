'use strict';
/* MOVE Explore: private, offline search among the approved demonstration places only.
   This does not geocode arbitrary addresses or contact a location search provider. */
(function(){
  function norm(value){
    return String(value).normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLocaleLowerCase('pt-BR').trim();
  }
  function mount(){
    if(typeof PLACES==='undefined')return;
    for(const id of ['origin','destination']){
      const select=document.getElementById(id);
      if(!select||select.dataset.searchMounted==='true')continue;
      select.dataset.searchMounted='true';
      const wrapper=document.createElement('div');wrapper.className='move-place-search';
      const input=document.createElement('input');
      input.type='search';input.autocomplete='off';input.spellcheck=false;
      input.className='move-place-input';
      input.id='search-'+id;
      input.placeholder='Buscar entre os locais de teste';
      input.setAttribute('role','combobox');
      input.setAttribute('aria-label',id==='origin'?'Buscar origem em locais demonstrativos':'Buscar destino em locais demonstrativos');
      input.setAttribute('aria-autocomplete','list');
      input.setAttribute('aria-expanded','false');
      const results=document.createElement('div');
      results.id='options-'+id;results.className='move-place-options hidden';
      results.setAttribute('role','listbox');
      results.setAttribute('aria-label','Locais demonstrativos encontrados');
      input.setAttribute('aria-controls',results.id);
      const info=document.createElement('div');info.className='move-place-help';
      info.textContent='Busca local · apenas seis pontos demonstrativos, sem consulta externa';
      wrapper.append(input,results,info);
      select.before(wrapper);
      select.hidden=true;
      select.setAttribute('aria-hidden','true');
      select.tabIndex=-1;
      let active=-1, candidates=[];
      const reset=()=>{input.value=PLACES[Number(select.value)]?.label||'';};
      const close=()=>{results.classList.add('hidden');input.setAttribute('aria-expanded','false');input.removeAttribute('aria-activedescendant');active=-1;};
      function moveActive(next){
        const buttons=Array.from(results.querySelectorAll('button'));
        if(!buttons.length)return;
        active=(next+buttons.length)%buttons.length;
        buttons.forEach((b,i)=>b.setAttribute('aria-selected',String(i===active)));
        input.setAttribute('aria-activedescendant',buttons[active].id);
        buttons[active].scrollIntoView({block:'nearest'});
      }
      function choose(index){
        select.value=String(index);
        select.dispatchEvent(new Event('change',{bubbles:true}));
        reset();close();input.focus();
      }
      function render(){
        const q=norm(input.value);results.replaceChildren();active=-1;
        candidates=PLACES.map((point,index)=>({point,index})).filter(item=>norm(item.point.label).includes(q));
        for(const item of candidates){
          const b=document.createElement('button');b.type='button';b.className='move-place-option';
          b.id='option-'+id+'-'+item.index;b.setAttribute('role','option');b.setAttribute('aria-selected','false');
          b.textContent=item.point.label;
          b.addEventListener('pointerdown',e=>e.preventDefault());
          b.addEventListener('click',()=>choose(item.index));
          results.append(b);
        }
        if(!candidates.length){const empty=document.createElement('p');empty.className='move-place-noresults';empty.textContent='Nenhum local de demonstração encontrado';results.append(empty);}
        results.classList.remove('hidden');
        input.setAttribute('aria-expanded','true');
      }
      input.addEventListener('focus',()=>{input.select();render();});
      input.addEventListener('input',render);
      input.addEventListener('keydown',event=>{
        if(event.key==='Escape'){close();reset();return;}
        if(event.key==='ArrowDown'||event.key==='ArrowUp'){
          event.preventDefault();
          if(results.classList.contains('hidden'))render();
          moveActive(active+(event.key==='ArrowDown'?1:-1));return;
        }
        if(event.key==='Enter'&&!results.classList.contains('hidden')&&candidates.length){
          event.preventDefault();choose(candidates[Math.max(0,active)].index);
        }
      });
      input.addEventListener('blur',()=>{window.setTimeout(()=>{if(!wrapper.contains(document.activeElement)){close();reset();}},120);});
      select.addEventListener('change',()=>{reset();document.getElementById('estimateResult')?.replaceChildren();});
      reset();
    }
  }
  window.initMovePlaceSearch=mount;
  mount();
})();
