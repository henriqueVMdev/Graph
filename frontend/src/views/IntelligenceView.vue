<template><div class="h-[calc(100vh-3.5rem)] overflow-y-auto p-4 space-y-4">
 <div class="flex items-center gap-3"><div><h1 class="text-base font-semibold text-gray-100">Central de Inteligência</h1><p class="text-[10px] text-gray-600">sinais · validação · divergências · saúde dos dados</p></div><div class="flex-1"/><form @submit.prevent="load" class="flex gap-2"><input v-model="symbol" class="form-input !py-1.5 text-xs w-32 uppercase"/><button class="btn-secondary !py-1.5 text-xs">Analisar</button></form></div>
 <div v-if="error" class="card p-3 text-red-400 text-xs">{{error}}</div>
 <div class="card p-4 overflow-x-auto"><div class="flex items-center gap-3 mb-2"><div class="title !mb-0">Ranking do universo — onde estão os melhores setups</div>
  <span v-if="rank?.building" class="text-[10px] text-accent-yellow font-mono">calculando {{rank.done}}/{{rank.total}}…</span>
  <span v-else-if="rank?.ts" class="text-[10px] text-gray-600 font-mono">atualizado {{new Date(rank.ts).toLocaleTimeString('pt-BR')}}</span></div>
  <table class="w-full text-xs font-mono whitespace-nowrap"><thead><tr class="text-gray-600 text-left"><th class="py-1">Ativo</th><th>Classe</th><th>Sinal</th><th class="text-right">Score</th><th class="text-right">Conf.</th><th class="text-right">Cobertura</th><th class="text-right">Fatores</th><th class="text-left pl-3">Divergências</th></tr></thead>
   <tbody><tr v-for="r in rank?.rows||[]" :key="r.symbol" @click="r.score!=null&&(symbol=r.symbol,load())"
     class="border-t border-surface-600 cursor-pointer hover:bg-surface-600/30" :class="{'opacity-40':r.score==null}">
    <td class="py-1.5 text-gray-200">{{r.symbol}}</td><td class="text-gray-500">{{r.class}}</td>
    <td :class="r.label==='COMPRA'?'text-green-400':r.label==='VENDA'?'text-red-400':r.label==='ERRO'?'text-red-600':'text-gray-400'" class="font-semibold">{{r.label}}</td>
    <td class="text-right" :class="(r.score||0)>0?'text-green-400':(r.score||0)<0?'text-red-400':'text-gray-400'">{{r.score!=null?(r.score>0?'+':'')+r.score.toFixed(1):'—'}}</td>
    <td class="text-right text-gray-300">{{r.confidence!=null?r.confidence.toFixed(0)+'%':'—'}}</td>
    <td class="text-right text-gray-500">{{r.coverage_pct!=null?r.coverage_pct.toFixed(0)+'%':'—'}}</td>
    <td class="text-right text-gray-500">{{r.n_factors??'—'}}</td>
    <td class="pl-3 text-[10px] text-amber-400/80 max-w-[24rem] truncate">{{r.error||(r.divergences||[]).join(' · ')||'—'}}</td>
   </tr></tbody></table>
  <p v-if="!(rank?.rows||[]).length" class="text-xs text-gray-600 py-4 text-center">construindo ranking pela primeira vez…</p>
  <p class="text-[10px] text-gray-600 mt-2">score = soma dos votos dos fatores · clique numa linha para a análise completa · universo: cripto, commodities CFTC, índices, FX e ações-tema</p>
 </div>
 <div class="card p-4 overflow-x-auto" v-if="track"><div class="title">Auto-auditoria forward — o que os sinais gravados renderam de verdade</div>
  <table class="w-full text-xs font-mono"><thead><tr class="text-gray-600 text-left"><th class="py-1">Sinal</th><th class="text-right">Gravados</th><th class="text-right">Maduros 7d</th><th class="text-right">Ret. médio 7d</th><th class="text-right">Acerto 7d</th><th class="text-right">Maduros 30d</th><th class="text-right">Ret. médio 30d</th><th class="text-right">Acerto 30d</th></tr></thead>
   <tbody><tr v-for="(v,k) in track.summary" :key="k" class="border-t border-surface-600">
    <td class="py-1.5 font-semibold" :class="k==='COMPRA'?'text-green-400':k==='VENDA'?'text-red-400':'text-gray-400'">{{k}}</td>
    <td class="text-right text-gray-300">{{v.signals}}</td>
    <td class="text-right text-gray-500">{{v.matured_7d}}</td>
    <td class="text-right" :class="pctClass(v.avg_fwd_7d_pct)">{{pct(v.avg_fwd_7d_pct)}}</td>
    <td class="text-right text-gray-300">{{v.favorable_7d_pct!=null?v.favorable_7d_pct+'%':'—'}}</td>
    <td class="text-right text-gray-500">{{v.matured_30d}}</td>
    <td class="text-right" :class="pctClass(v.avg_fwd_30d_pct)">{{pct(v.avg_fwd_30d_pct)}}</td>
    <td class="text-right text-gray-300">{{v.favorable_30d_pct!=null?v.favorable_30d_pct+'%':'—'}}</td>
   </tr></tbody></table>
  <p v-if="track.note" class="text-xs text-gray-500 py-2">{{track.note}}</p>
  <details v-if="(track.signals||[]).length" class="mt-2"><summary class="text-[10px] text-gray-500 cursor-pointer uppercase">últimos sinais gravados ({{track.signals.length}})</summary>
   <table class="w-full text-[11px] font-mono mt-2"><thead><tr class="text-gray-600 text-left"><th>Data</th><th>Ativo</th><th>Sinal</th><th class="text-right">Score</th><th class="text-right">Preço no sinal</th><th class="text-right">7d depois</th><th class="text-right">30d depois</th></tr></thead>
    <tbody><tr v-for="s in track.signals" :key="s.symbol+s.date" class="border-t border-surface-600/40">
     <td class="py-1 text-gray-500">{{s.date}}</td><td class="text-gray-200">{{s.symbol}}</td>
     <td :class="s.label==='COMPRA'?'text-green-400':s.label==='VENDA'?'text-red-400':'text-gray-500'">{{s.label}}</td>
     <td class="text-right text-gray-400">{{s.score!=null?(s.score>0?'+':'')+s.score.toFixed(1):'—'}}</td>
     <td class="text-right text-gray-400">{{s.price?.toLocaleString('pt-BR',{maximumFractionDigits:2})}}</td>
     <td class="text-right" :class="pctClass(s.fwd_7d_pct)">{{pct(s.fwd_7d_pct)}}</td>
     <td class="text-right" :class="pctClass(s.fwd_30d_pct)">{{pct(s.fwd_30d_pct)}}</td>
    </tr></tbody></table></details>
  <p class="text-[10px] text-gray-600 mt-2">{{track.method}}</p>
 </div>
 <template v-if="d&&!loading"><div class="grid grid-cols-2 md:grid-cols-5 gap-2">
  <div class="metric-card"><span class="metric-label">Sinal</span><span class="metric-value" :class="signalClass">{{d.signal.label}}</span></div>
  <div class="metric-card"><span class="metric-label">Score</span><span class="metric-value text-gray-100">{{d.signal.score.toFixed(2)}}</span></div>
  <div class="metric-card"><span class="metric-label">Confiança histórica</span><span class="metric-value text-accent-yellow">{{d.signal.confidence}}%</span><small class="text-[8px] text-gray-600">cobertura {{d.signal.coverage_pct??'—'}}%</small></div>
  <div class="metric-card"><span class="metric-label">Preço</span><span class="metric-value text-gray-100">{{money(d.signal.price)}}</span></div>
  <div class="metric-card"><span class="metric-label">Distância Pi Top</span><span class="metric-value text-gray-300">{{pct(d.liquidity?.pi_top_distance_pct)}}</span></div>
 </div>
 <div class="grid grid-cols-1 lg:grid-cols-2 gap-4"><div class="card p-4"><div class="title">Explicação do sinal</div><div v-for="r in d.signal.reasons" :key="r" class="text-xs text-gray-300 py-1 border-b border-surface-600">{{r}}</div></div>
 <div class="card p-4"><div class="title">Divergências</div><div v-for="x in d.divergences" :key="x.title" class="rounded bg-surface-600/30 p-2 mb-2"><div :class="x.severity==='warning'?'text-red-400':'text-green-400'" class="text-xs font-semibold">{{x.title}}</div><div class="text-[10px] text-gray-500">{{x.detail}}</div></div><p v-if="!d.divergences.length" class="text-xs text-gray-600">nenhuma divergência forte detectada</p></div></div>
 <div class="card p-4 overflow-x-auto"><div class="title">Validação histórica dos sinais</div><table class="w-full text-xs font-mono"><thead><tr class="text-gray-600"><th class="text-left">Sinal</th><th>Dias</th><th>Ret. 30d</th><th>Acerto 30d</th><th>Ret. 90d</th></tr></thead><tbody><tr v-for="(v,k) in d.validation" :key="k" class="border-t border-surface-600"><td class="py-2">{{k}}</td><td class="text-center">{{v.samples}}</td><td class="text-center">{{pct(v.return_30d_pct)}}</td><td class="text-center">{{pct(v.win_rate_30d_pct)}}</td><td class="text-center">{{pct(v.return_90d_pct)}}</td></tr></tbody></table></div>
 <div class="card p-4"><div class="title">Saúde das fontes</div><div v-for="h in d.health" :key="h.source" class="flex justify-between py-1 border-t border-surface-600 text-xs"><span class="text-gray-300">{{h.source}}</span><span :class="h.status==='ok'?'text-green-400':'text-amber-400'">{{h.status}} <small>{{h.detail}}</small></span></div></div>
 <div class="card p-4" v-if="liq"><div class="title">Liquidez e risco sistêmico · FRED</div><div class="grid grid-cols-2 md:grid-cols-3 gap-2"><div v-for="s in liq.series" :key="s.id" class="rounded bg-surface-600/30 p-2"><div class="text-[9px] text-gray-500 uppercase">{{s.label}}</div><div class="text-sm font-mono text-gray-200">{{s.value?.toLocaleString('pt-BR')??'—'}}</div><div class="text-[9px]" :class="(s.change_30??0)>=0?'text-green-500':'text-red-400'">Δ30 obs {{s.change_30?.toFixed(2)??s.status}}</div></div></div></div>
 </template></div></template>
<script setup>import{ref,computed,onMounted,onUnmounted}from'vue';import{getIntelligence,getIntelligenceRanking,getIntelligenceTracking,getLiquidity}from'@/api/client.js';const symbol=ref('BTC'),d=ref(null),liq=ref(null),rank=ref(null),track=ref(null),loading=ref(false),error=ref(null);let pollTimer=null;const signalClass=computed(()=>d.value?.signal.label==='COMPRA'?'text-green-400':d.value?.signal.label==='VENDA'?'text-red-400':'text-gray-300');const pct=v=>v==null?'—':`${v>=0?'+':''}${Number(v).toFixed(2)}%`,money=v=>v==null?'—':`$${Number(v).toLocaleString('pt-BR',{maximumFractionDigits:2})}`,pctClass=v=>v==null?'text-gray-500':v>0?'text-green-400':v<0?'text-red-400':'text-gray-400';async function load(){loading.value=true;error.value=null;try{[d.value,liq.value]=await Promise.all([getIntelligence(symbol.value).then(r=>r.data),getLiquidity().then(r=>r.data)])}catch(e){error.value=e.response?.data?.error||e.message}finally{loading.value=false}}
async function pollRank(){try{rank.value=(await getIntelligenceRanking()).data;if(rank.value?.building){pollTimer=setTimeout(pollRank,4000)}}catch{pollTimer=setTimeout(pollRank,8000)}}
async function loadTrack(){try{track.value=(await getIntelligenceTracking()).data}catch{/* fica oculto */}}
onMounted(()=>{load();pollRank();loadTrack()});onUnmounted(()=>clearTimeout(pollTimer))</script>
<style scoped>.title{@apply text-[10px] text-gray-500 uppercase font-semibold mb-2}</style>
