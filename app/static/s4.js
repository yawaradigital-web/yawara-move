'use strict';
/* MOVE Connect S4: progressive enhancement over the demo planner. No live location or pricing. */
(() => {
  const origin = document.getElementById('origin');
  const destination = document.getElementById('destination');
  const quoteButton = document.getElementById('quote');
  const quoteBox = document.getElementById('quoteResult');
  if (!origin || !destination || !quoteButton || !quoteBox || typeof PLACES === 'undefined') return;
  const slots = {};
  const normalize = value => String(value).normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase().trim();
  const reset = () => {
    quoteBox.replaceChildren();
    quoteBox.classList.add('hidden');
    if (typeof lastQuote !== 'undefined') lastQuote = null;
  };
  const setPoint = (select, index) => {
    select.value = String(index);
    select.dispatchEvent(new Event('change', { bubbles: true }));
  };
  const updateSearch = (select) => {
    const slot = slots[select.id];
    if (slot) slot.input.value = PLACES[Number(select.value)]?.label || '';
  };
  const buildSearch = (select, labelText) => {
    const wrap = document.createElement('div');
    wrap.className = 'move-search';
    const label = document.createElement('label');
    label.setAttribute('for', 's4-' + select.id);
    label.className = 'move-search-label';
    label.textContent = labelText;
    const input = document.createElement('input');
    input.type = 'search';
    input.id = 's4-' + select.id;
    input.autocomplete = 'off';
    input.spellcheck = false;
    input.placeholder = 'Busque um local de demonstração';
    input.setAttribute('aria-controls', 's4-list-' + select.id);
    input.setAttribute('aria-expanded', 'false');
    input.setAttribute('role', 'combobox');
    input.setAttribute('aria-autocomplete', 'list');
    const list = document.createElement('div');
    list.id = 's4-list-' + select.id;
    list.className = 'move-search-list hidden';
    list.setAttribute('role', 'listbox');
    const note = document.createElement('span');
    note.className = 'move-search-note';
    note.textContent = 'Apenas pontos pré-definidos · sem GPS';
    wrap.append(label, input, list, note);
    select.parentElement?.insertAdjacentElement('afterend', wrap);
    select.classList.add('move-original-select');
    select.setAttribute('aria-label', labelText + ' (seletor alternativo)');
    const close = () => {
      list.classList.add('hidden');
      input.setAttribute('aria-expanded', 'false');
    };
    const render = () => {
      list.replaceChildren();
      const query = normalize(input.value);
      const matches = PLACES.map((p, index) => ({p,index})).filter(({p}) => normalize(p.label).includes(query));
      for (const {p,index} of matches) {
        const b = document.createElement('button');
        b.type = 'button'; b.className = 'move-search-choice';
        b.setAttribute('role', 'option');
        b.textContent = p.label;
        b.addEventListener('pointerdown', e => e.preventDefault());
        b.addEventListener('click', () => { setPoint(select,index); input.value=p.label; close(); input.focus(); });
        list.appendChild(b);
      }
      if (!matches.length) {
        const empty = document.createElement('span');
        empty.className = 'move-search-empty';
        empty.textContent = 'Nenhum ponto demonstrativo encontrado';
        list.appendChild(empty);
      }
      list.classList.remove('hidden');
      input.setAttribute('aria-expanded','true');
    };
    input.addEventListener('input', render);
    input.addEventListener('focus', render);
    input.addEventListener('keydown', e => {
      if (e.key === 'Escape') { close(); updateSearch(select); }
      if (e.key === 'Enter') {
        const first = list.querySelector('button');
        if (first && !list.classList.contains('hidden')) {e.preventDefault(); first.click();}
      }
    });
    input.addEventListener('blur', () => { window.setTimeout(() => { close(); updateSearch(select); }, 120); });
    select.addEventListener('change', () => { updateSearch(select); reset(); });
    slots[select.id] = {input, close};
    updateSearch(select);
  };
  buildSearch(origin, 'Pesquisar origem');
  buildSearch(destination, 'Pesquisar destino');
  const swap = document.createElement('button');
  swap.type = 'button';
  swap.className = 'move-swap';
  swap.textContent = '⇅ Inverter origem e destino';
  swap.setAttribute('aria-label', 'Inverter origem e destino');
  swap.addEventListener('click', () => {
    const a = origin.value, b = destination.value;
    setPoint(origin,b); setPoint(destination,a);
    updateSearch(origin); updateSearch(destination);
  });
  const destinationSearch = slots.destination.input.closest('.move-search');
  destinationSearch.insertAdjacentElement('afterend', swap);
  const caption = document.createElement('p');
  caption.className = 'move-disclaimer';
  caption.textContent = 'Preços e distância são simulados; não representam cotações ou rotas reais.';
  quoteButton.insertAdjacentElement('afterend', caption);
  const previousRender = renderQuote;
  renderQuote = function(q) {
    previousRender(q);
    const summary = document.createElement('div');
    summary.className = 'move-results';
    const heading = document.createElement('div');
    heading.className = 'move-results-heading';
    heading.textContent = 'Resultado da simulação';
    const route = document.createElement('div');
    route.className = 'move-result-route';
    const start = document.createElement('span'); start.textContent = PLACES[Number(origin.value)]?.label || 'Origem';
    const end = document.createElement('span'); end.textContent = PLACES[Number(destination.value)]?.label || 'Destino';
    const connector = document.createElement('span'); connector.textContent = '↓'; connector.setAttribute('aria-hidden','true');
    route.append(start,connector,end);
    const available = document.createElement('div');
    available.className = 'move-provider move-provider-active';
    const title = document.createElement('strong'); title.textContent = 'MOVE Corridas · Simulador';
    const info = document.createElement('span'); info.textContent = 'Única opção demonstrativa disponível';
    available.append(title,info);
    const future = document.createElement('div');
    future.className = 'move-provider move-provider-muted';
    const futureTitle = document.createElement('strong'); futureTitle.textContent = 'Outras plataformas e modalidades';
    const futureText = document.createElement('span'); futureText.textContent = 'Integrações não habilitadas. Sem preços de terceiros.';
    future.append(futureTitle,futureText);
    summary.append(heading,route,available,future);
    quoteBox.insertBefore(summary,quoteBox.firstChild);
  };
  quoteButton.addEventListener('click', () => {
    if (origin.value === destination.value) {
      const msg = document.getElementById('alert');
      if (msg) { msg.textContent='Selecione uma origem diferente do destino.'; msg.classList.remove('hidden'); }
    }
  });
})();