(async function(){
  async function jget(url){ const r=await fetch(url); return r.json(); }

  // Engagement
  try{
    const days = 14;
    const eng = await jget(`/api/analytics/engagement?days=${days}`);
    const xs = eng.data.series.map(p=>p.day);
    const active = eng.data.series.map(p=>p.active);
    const posts  = eng.data.series.map(p=>p.posts);
    Plotly.newPlot('chart-engagement', [
      {x: xs, y: active, mode:'lines+markers', name:'Active Users'},
      {x: xs, y: posts,  mode:'lines+markers', name:'Posts'}
    ], {margin:{t:10}, legend:{orientation:'h'}}, {displayModeBar:false});
  }catch(e){}

  // Sentiment (if AI endpoint exists)
  try{
    const s = await jget('/api/ai/sentiment/trend');
    const xs = s.data.map(p=>p.day);
    const val = s.data.map(p=>p.score);
    Plotly.newPlot('chart-sentiment', [
      {x: xs, y: val, mode:'lines+markers', name:'Sentiment (−1..+1)'}
    ], {yaxis:{range:[-1,1]}, margin:{t:10}, legend:{orientation:'h'}}, {displayModeBar:false});
  }catch(e){}
})();
