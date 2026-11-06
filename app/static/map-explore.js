'use strict';
/* Public OSM tiles are requested only after the visitor clicks "Abrir mapa". */
(() => {
  const button = document.getElementById('loadMap');
  const host = document.getElementById('realMap');
  const status = document.getElementById('mapStatus');
  if (!button || !host || !status) return;
  let map = null, originMarker = null, destinationMarker = null, connector = null;
  const bounds = [[-23.73,-46.80],[-23.48,-46.47]];
  let sampleLayer=null;
  function addSamplePoints(){
    if(!map || sampleLayer || typeof PLACES==='undefined')return;
    sampleLayer=L.layerGroup().addTo(map);
    PLACES.forEach((point,index)=>{
      const marker=L.circleMarker([point.lat,point.lon],{
        radius:7,color:'#f4fcfb',weight:2,fillColor:'#35d5cf',fillOpacity:1
      }).addTo(sampleLayer);
      marker.bindTooltip(point.label,{direction:'top'});
      marker.on('click',()=>{
        const destination=document.getElementById('destination');
        if(!destination){
          status.textContent='Abra Corridas ou Comparar para escolher um destino.';
          return;
        }
        destination.value=String(index);
        destination.dispatchEvent(new Event('change',{bubbles:true}));
        status.textContent='Destino demonstrativo selecionado no mapa: '+point.label+'. Agora você pode consultar a rota de teste.';
      });
    });
  }

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
    addSamplePoints();
    button.textContent='Atualizar pontos no mapa';
    status.textContent='Mapa de ruas por OpenStreetMap carregado. Seu navegador pode contatar o servidor público de mapas; não há navegação nem rastreamento.';
    requestAnimationFrame(()=>{map.invalidateSize();sync()});
  });
  const routeButton=document.getElementById('roadDemoRoute');
  const routeResult=document.getElementById('roadDemoResult');
  let routeLine=null;
  let routeNonce=0;
  function clearRoute(){
    routeNonce++;
    if(routeLine && map){map.removeLayer(routeLine);routeLine=null;}
    if(routeResult)routeResult.textContent='Consulta viária opcional. O percurso exibido não representa uma viagem contratada.';
  }
  if(routeButton && routeResult){
    routeButton.addEventListener('click',async()=>{
      const a=document.getElementById('origin'),b=document.getElementById('destination');
      if(!a||!b){routeResult.textContent='Escolha Corridas ou Comparar para consultar a rota.';return;}
      if(a.value===b.value){routeResult.textContent='Escolha dois locais diferentes.';return;}
      const nonce=++routeNonce;
      routeButton.disabled=true;
      routeResult.textContent='Consultando percurso demonstrativo pelas ruas...';
      try{
        const response=await fetch('/api/demo-route?origin='+encodeURIComponent(a.value)+'&destination='+encodeURIComponent(b.value),{headers:{'Accept':'application/json'}});
        const data=await response.json();
        if(nonce!==routeNonce)return;
        if(!response.ok)throw Error(typeof data.detail==='string'?data.detail:'Serviço de rotas indisponível.');
        if(!Array.isArray(data.coordinates)||data.coordinates.length<2||data.coordinates.length>4000||data.routing!=='road_demo_not_guaranteed')throw Error('Dados de rota inválidos.');
        const positions=data.coordinates.map(p=>[p[1],p[0]]);
        if(positions.some(p=>p.length!==2||p.some(v=>typeof v!=='number'||!Number.isFinite(v))))throw Error('Coordenadas de rota inválidas.');
        if(!map)button.click();
        if(!map)throw Error('Mapa indisponível no momento.');
        if(routeLine)map.removeLayer(routeLine);
        routeLine=L.polyline(positions,{color:'#35d5cf',weight:5,opacity:.9}).addTo(map);
        map.fitBounds(routeLine.getBounds().pad(.15),{maxZoom:14,animate:false});
        routeResult.textContent='Percurso viário demonstrativo: '+data.distance_km.toLocaleString('pt-BR')+' km · cerca de '+data.duration_minutes_illustrative+' min em condições de referência. Não considera trânsito ao vivo e NÃO é previsão de chegada. Fonte: '+data.source+'.';
      }catch(err){if(nonce===routeNonce)routeResult.textContent='Não foi possível consultar o percurso: '+(err.message||'erro de conexão')+' A linha ilustrativa permanece disponível.';}
      finally{routeButton.disabled=false;}
    });
  }
  document.addEventListener('change',event=>{
    if(event.target && (event.target.id==='origin'||event.target.id==='destination')){clearRoute();sync();}
  });
  document.querySelectorAll('[data-tab]').forEach(tab=>tab.addEventListener('click',()=>{
    if(map)requestAnimationFrame(()=>{map.invalidateSize();sync()});
  }));
})();
