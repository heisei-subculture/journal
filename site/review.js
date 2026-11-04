'use strict';
(()=>{
const list=document.querySelector('#review-list'), filter=document.querySelector('#review-filter');
const el=(tag,text)=>{const n=document.createElement(tag);if(text)n.textContent=text;return n;};
const url=v=>{try{const u=new URL(v);return u.protocol==='https:'&&!u.username&&!u.password?u.href:null;}catch{return null;}};
async function refresh(){
 const r=await fetch('api/review',{cache:'no-store'});if(!r.ok)throw Error('候補を読み込めませんでした');const q=await r.json();
 document.querySelector('#review-count').textContent=`（確認待ち ${q.candidates.filter(p=>p.review_status==='pending').length}件）`;
 list.replaceChildren();const items=q.candidates.filter(p=>p.review_status===filter.value);
 if(!items.length)list.append(el('p','この状態の記事はありません。'));
 for(const p of items){
  const card=el('article');card.style.cssText='border-top:2px solid;padding:20px 0;clear:both;display:flow-root';
  if(url(p.image_url)){const img=el('img');img.src=url(p.image_url);img.alt='';img.loading='lazy';img.referrerPolicy='no-referrer';img.style.cssText='float:right;width:130px;max-height:130px;object-fit:contain;margin:0 0 12px 14px';img.onerror=()=>img.remove();card.append(img);}
  card.append(el('h3',p.title),el('small',`${p.category} ／ ${p.source_name} ／ 元記事 ${p.published_at.slice(0,10)}`),el('p',p.summary),el('p','選定理由：'+p.selection_reason));
  const link=el('a','元記事を読む ↗');if(url(p.source_url))link.href=url(p.source_url);link.target='_blank';link.rel='noopener noreferrer';card.append(link);
  if(p.review_status!=='approved'){
   const actions=el('div');actions.style.cssText='display:flex;gap:12px;margin-top:15px';
   for(const [action,label] of p.review_status==='pending'?[['approve','採用して掲載'],['reject','見送り']]:[['pending','確認待ちに戻す']]){
    const b=el('button',label);b.className=action==='approve'?'primary':'secondary';b.onclick=async()=>{actions.querySelectorAll('button').forEach(x=>x.disabled=true);try{const r=await fetch('api/review',{method:'POST',headers:{'Content-Type':'application/json','X-Heisei-Editor':'1'},body:JSON.stringify({id:p.id,action})});const d=await r.json();if(!r.ok)throw Error(d.error);await refresh();await load();status(action==='approve'?'採用しました。ローカルの通信に掲載されています。':action==='reject'?'見送りにしました。':'確認待ちに戻しました。');}catch(e){status(e.message,true);actions.querySelectorAll('button').forEach(x=>x.disabled=false);}};actions.append(b);
   }card.append(actions);
  }list.append(card);
 }
}
filter.onchange=()=>refresh().catch(e=>status(e.message,true));refresh().catch(e=>status(e.message,true));
})();
