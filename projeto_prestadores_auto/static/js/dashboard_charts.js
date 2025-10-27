document.addEventListener('DOMContentLoaded', function(){
  const cv = document.getElementById('graficoComparacao');
  if(!cv) return;
  const data = JSON.parse(cv.dataset.comparacao || "[]");
  const mesA = cv.dataset.mesanterior || "";
  const mesB = cv.dataset.mesatual || "";
  if(data.length === 0) return;
  const labels = data.map(x => x.nome);
  const anteriores = data.map(x => x.anterior);
  const atuais = data.map(x => x.atual);
  const diffs = data.map(x => x.diff);
  const colors = diffs.map(d => d>0 ? 'rgba(54,162,235,0.6)' : d<0 ? 'rgba(255,99,132,0.6)' : 'rgba(201,203,207,0.6)');
  new Chart(cv.getContext('2d'), {
    type:'bar',
    data:{ labels, datasets:[
      {label: mesA, data: anteriores, backgroundColor:'rgba(255,159,64,0.5)'},
      {label: mesB, data: atuais, backgroundColor: colors}
    ]},
    options:{ responsive:true, plugins:{ legend:{position:'bottom'}}, scales:{ y:{beginAtZero:true} } }
  });
});
