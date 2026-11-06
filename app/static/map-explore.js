'use strict';
/* Public OSM tiles are requested only after the visitor clicks "Abrir mapa". */
(() => {
  const button = document.getElementById('loadMap');
  const host = document.getElementById('realMap');
  const status = document.getElementById('mapStatus');
  if (!button || !host || !status) return;
  let map = null, originMarker = null, destinationMarker = null, connector = null;
  const bounds = [[-23.73,-46.80],[-23.48,-46.47]];
  function sync(){
    if (!map || typeof PLACES === 'undefined') return;
    const origin = document.getElementById('origin');
    const destination = document.getElementById('destination');
    if (!origin || !destination) return;
    const a = PLACES[Number(origin.value)], b = PLACES[Number(destination.value)];
    if (!a || !b) return;
    const aLatLng = [a.lat, a.lon], bLatLng = [b.lat, b.lon];
    if(originMarker)map.removeLayer(originMarker);
    if(destinationMarker)map.removeLayer(destinationMarker);
    if(connector)map.removeLayer(connector);
    originMarker = L.marker(aLatLng).addTo(map).bindPopup('Origem demonstrativa: '+a.label);
    destinationMarker = L.marker(bLatLng).addTo(map).bindPopup('Destino demonstrativo: '+b.label);
    connector = L.polyline([aLatLng,bLatLng],{color:'#168c86',weight:3,dashArray:'7,9'}).addTo(map);
    const fit = L.latLngBounds(aLatLng,bLatLng);
    map.fitBounds(fit.pad(0.35),{maxZoom:13,animate:false});
    status.textContent='Marcadores de origem e destino atualizados. Linha pontilhada é apenas uma ligação geométrica, não uma rota.';
  }
  button.addEventListener('click',()=>{
    if (map) {map.invalidateSize();sync();return;}
    if (typeof L === 'undefined'){
      status.textContent='Não foi possível carregar o mapa. A simulação por pontos continua disponível.';
      return;
    }
    host.classList.remove('hidden');
    map = L.map(host,{zoomControl:true,scrollWheelZoom:false,attributionControl:true,maxZoom:17});
    L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png',{
      maxZoom:17,
      attribution:'&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener noreferrer">OpenStreetMap contributors</a>',
      crossOrigin:true
    }).addTo(map);
    map.fitBounds(bounds);
    button.textContent='Atualizar pontos no mapa';
    status.textContent='Mapa de ruas por OpenStreetMap carregado. Seu navegador pode contatar o servidor público de mapas; não há navegação nem rastreamento.';
    requestAnimationFrame(()=>{map.invalidateSize();sync()});
  });
  document.addEventListener('change',event=>{
    if(event.target && (event.target.id==='origin'||event.target.id==='destination'))sync();
  });
  document.querySelectorAll('[data-tab]').forEach(tab=>tab.addEventListener('click',()=>{
    if(map)requestAnimationFrame(()=>{map.invalidateSize();sync()});
  }));
})();
