<template>
  <div class="h-[calc(100vh-3.5rem)] overflow-y-auto p-4 space-y-4">
    <div class="flex flex-wrap items-center gap-3">
      <div><h1 class="text-base font-semibold text-gray-100">Tendência Sazonal</h1><p class="text-[10px] text-gray-600">20 · 15 · 10 · 5 · 2 anos · mensal e intramês</p></div>
      <div class="flex-1"/><form @submit.prevent="load" class="flex gap-2"><input v-model="symbol" placeholder="NZDUSD=X, BTC-USD, GC=F" class="form-input !py-1.5 text-xs w-48 uppercase"/><button class="btn-secondary !py-1.5 text-xs" :disabled="loading">{{loading?'Calculando…':'Analisar'}}</button></form>
    </div>
    <div class="flex flex-wrap gap-1.5"><button v-for="s in presets" :key="s" @click="symbol=s;load()" class="px-2 py-1 text-[10px] font-mono rounded border border-surface-500 text-gray-500 hover:text-accent-yellow">{{s}}</button></div>
    <div v-if="error" class="card p-3 text-xs text-red-400">{{error}}</div>
    <template v-if="d&&!loading">
      <div class="grid grid-cols-2 md:grid-cols-5 gap-2">
        <div class="metric-card"><span class="metric-label">Ativo</span><span class="metric-value text-gray-100 !text-sm">{{d.name}}</span></div>
        <div class="metric-card"><span class="metric-label">Histórico</span><span class="metric-value text-gray-200">{{d.history.years}} anos</span></div>
        <div class="metric-card"><span class="metric-label">Melhor mês</span><span class="metric-value text-green-400">{{monthName(d.best_months[0]?.month)}} {{pct(d.best_months[0]?.avg_pct)}}</span></div>
        <div class="metric-card"><span class="metric-label">Pior mês</span><span class="metric-value text-red-400">{{monthName(d.worst_months[0]?.month)}} {{pct(d.worst_months[0]?.avg_pct)}}</span></div>
        <div class="metric-card"><span class="metric-label">Observações</span><span class="metric-value text-gray-200">{{d.history.observations.toLocaleString('pt-BR')}}</span></div>
      </div>
      <div class="card p-4"><div class="title">Curvas sazonais normalizadas</div><div ref="yearChart" class="h-80"/></div>
      <div class="grid grid-cols-1 xl:grid-cols-2 gap-4">
        <div class="card p-4"><div class="title">Retorno médio e taxa de acerto mensal</div><div ref="monthChart" class="h-72"/></div>
        <div class="card p-4"><div class="title">Tendência intramês · {{monthName(d.intra_month.month)}}</div><div ref="intraChart" class="h-72"/></div>
      </div>
      <div class="card p-4 overflow-x-auto"><div class="title">Heatmap de performance mensal (%)</div>
        <table class="w-full text-[10px] font-mono"><thead><tr><th class="text-left">Ano</th><th v-for="m in 12" :key="m">{{monthName(m).slice(0,3)}}</th></tr></thead>
          <tbody><tr v-for="row in [...d.heatmap].reverse()" :key="row.year"><td class="py-1 text-gray-400">{{row.year}}</td><td v-for="(v,i) in row.months" :key="i" class="text-center py-1 rounded" :style="heat(v)">{{v==null?'—':v.toFixed(1)}}</td></tr></tbody></table>
      </div>
      <div class="text-[10px] text-gray-600">{{d.methodology}} · {{d.source}}. Sazonalidade histórica não garante repetição futura.</div>
    </template>
  </div>
</template>
<script setup>
import {ref,nextTick,onMounted} from 'vue';import {getSeasonality} from '@/api/client.js'
const symbol=ref('NZDUSD=X'),d=ref(null),loading=ref(false),error=ref(null),yearChart=ref(null),monthChart=ref(null),intraChart=ref(null)
const presets=['NZDUSD=X','EURUSD=X','^GSPC','BTC-USD','GC=F','CL=F','AAPL','PETR4.SA'];const months=['','Janeiro','Fevereiro','Março','Abril','Maio','Junho','Julho','Agosto','Setembro','Outubro','Novembro','Dezembro']
const monthName=m=>months[m]||'—',pct=v=>v==null?'—':`${v>=0?'+':''}${v.toFixed(2)}%`,cfg={responsive:true,displaylogo:false,displayModeBar:false}
const layout=h=>({template:'plotly_dark',paper_bgcolor:'#000',plot_bgcolor:'#080808',font:{color:'#aaa',size:10},height:h,margin:{t:10,r:45,b:35,l:45},xaxis:{gridcolor:'#1e1e1e'},yaxis:{gridcolor:'#1e1e1e',ticksuffix:'%'},legend:{orientation:'h',y:1.12}})
function heat(v){if(v==null)return{};const a=Math.min(.55,Math.abs(v)/12+.08);return{background:v>=0?`rgba(34,197,94,${a})`:`rgba(239,68,68,${a})`,color:'#eee'}}
async function draw(){const P=(await import('plotly.js-dist-min')).default;await nextTick();const c={'20':'#f5c518','15':'#4dabf7','10':'#69db7c','5':'#f59f00','2':'#f74870'}
 P.newPlot(yearChart.value,Object.entries(d.value.paths).map(([k,y])=>({type:'scatter',mode:'lines',x:d.value.day_of_year,y,name:`${k} anos`,line:{color:c[k],width:k==='20'?2:1.2}})),layout(320),cfg)
 const m=d.value.monthly_stats,x=m.map(a=>monthName(a.month).slice(0,3));P.newPlot(monthChart.value,[{type:'bar',x,y:m.map(a=>a.avg_pct),name:'retorno médio',marker:{color:m.map(a=>a.avg_pct>=0?'#22c55e':'#ef4444')}},{type:'scatter',mode:'lines+markers',x,y:m.map(a=>a.win_rate_pct),name:'acerto %',yaxis:'y2',line:{color:'#f5c518'}}],{...layout(288),yaxis2:{overlaying:'y',side:'right',range:[0,100],ticksuffix:'%'}},cfg)
 const p=d.value.intra_month.points,dx=p.map(a=>a.trading_day);P.newPlot(intraChart.value,[{type:'scatter',mode:'lines',x:dx,y:p.map(a=>a.high_pct),line:{width:0},showlegend:false},{type:'scatter',mode:'lines',x:dx,y:p.map(a=>a.low_pct),fill:'tonexty',fillcolor:'rgba(77,171,247,.12)',line:{width:0},name:'25–75%'},{type:'scatter',mode:'lines',x:dx,y:p.map(a=>a.avg_pct),name:'média',line:{color:'#f5c518',width:2}}],layout(288),cfg)}
async function load(){loading.value=true;error.value=null;try{d.value=(await getSeasonality(symbol.value.trim().toUpperCase())).data;loading.value=false;await draw()}catch(e){error.value=e.response?.data?.error||e.message;d.value=null}finally{loading.value=false}}onMounted(load)
</script>
<style scoped>.title{@apply text-[10px] text-gray-500 uppercase mb-2}</style>
