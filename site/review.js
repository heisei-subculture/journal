'use strict';

const list=document.querySelector('#review-list'), filter=document.querySelector('#review-filter');
const el=(tag,text)=>{const n=document.createElement(tag);if(text)n.textContent=text;return n;};
const url=v=>{try{const u=new URL(v);return u.protocol==='https:'&&!u.username&&!u.password?u.href:null;}catch{return null;}};
const search = document.querySelector('#article-search');
const category = document.querySelector('#article-category');
const order = document.querySelector('#article-order');
const pager = document.querySelector('#article-pager');
const statusNames = {pending:'確認待ち', approved:'採用済み', rejected:'見送り'};
const pageSize = 12;
let candidates = [];
let page = 1;

function searchable(text){
 return text.normalize('NFKC').toLowerCase().replace(/[\s・‐‑–—－-]+/gu,'');
}

async function refreshReview(){
 const response = await fetch('api/review',{cache:'no-store'});
 if(!response.ok)throw Error('記事を読み込めませんでした');
 candidates = (await response.json()).candidates;
 for(const option of filter.options){
  const count = option.value ? candidates.filter(p=>p.review_status===option.value).length : candidates.length;
  option.textContent = (statusNames[option.value] || 'すべて') + '（' + count + '件）';
 }
 renderArticles();
}

function articleRow(post){
 const row = el('article');
 row.className = 'article-result';
 const meta = el('div');
 meta.className = 'article-meta';
 const badge = el('strong',statusNames[post.review_status]);
 badge.dataset.status = post.review_status;
 meta.append(badge, el('span',post.category),
             el('span',post.source_name), el('span','元記事 '+post.published_at.slice(0,10)));
 const details = el('details');
 details.open = post.review_status==='pending';
 const summary = el('summary',post.title);
 details.append(summary);
 const body = el('div');
 body.className = 'article-detail';
 if(url(post.image_url)){
  const img = el('img');
  img.src=url(post.image_url); img.alt=''; img.loading='lazy'; img.referrerPolicy='no-referrer';
  img.onerror=()=>img.remove(); body.append(img);
 }
 body.append(el('p',post.summary));
 if(post.selection_reason)body.append(el('p','選定理由：'+post.selection_reason));
 if(post.comment)body.append(el('p','コメント：'+post.comment));
 details.append(body);
 const actions = el('div');
 actions.className = 'article-actions';
 const link = el('a','元記事 ↗');
 link.href=url(post.source_url); link.target='_blank'; link.rel='noopener noreferrer';
 actions.append(link);
 if(post.review_status==='approved'){
  const edit = el('button','コメントを編集');
  edit.className='secondary'; edit.type='button';
  edit.onclick=()=>{
   const published=posts.find(item=>item.type==='news'&&item.source_url===post.source_url);
   if(!published){status('掲載記事を読み込めませんでした。画面を更新してください。',true);return;}
   select(published); $('#comment').focus();
  };
  actions.append(edit,reviewButton(post,'withdraw','確認待ちに戻す'));
 }else if(post.review_status==='pending'){
  actions.append(reviewButton(post,'approve','採用して掲載'),reviewButton(post,'reject','見送り'));
 }else{
  actions.append(reviewButton(post,'pending','確認待ちに戻す'));
 }
 row.append(meta,details,actions);
 return row;
}

function renderArticles(){
 const terms = search.value.trim().split(/\s+/u).map(searchable).filter(Boolean);
 const items = candidates.filter(post=>{
  if(filter.value && post.review_status!==filter.value)return false;
  if(category.value && post.category!==category.value)return false;
  const fields=[post.title,post.summary,post.source_name,post.source_url,post.category,post.comment,post.selection_reason];
  const text=fields.filter(Boolean).map(searchable).join(' ');
  return terms.every(term=>text.includes(term));
 });
 const direction=order.value==='oldest'?1:-1;
 items.sort((a,b)=>direction*(Date.parse(a.created_at)-Date.parse(b.created_at)));
 const pages=Math.max(1,Math.ceil(items.length/pageSize));
 page=Math.min(page,pages);
 const start=(page-1)*pageSize;
 const visible=items.slice(start,start+pageSize);
 list.replaceChildren(...visible.map(articleRow));
 $('#review-count').textContent=items.length ? items.length+'件中 '+(start+1)+'〜'+(start+visible.length)+'件' : '該当する記事はありません';
 pager.replaceChildren();
 if(pages>1){
  for(const [step,label] of [[-1,'前へ'],[1,'次へ']]){
   const button=el('button',label);
   button.type='button'; button.className='secondary';
   button.disabled=page+step<1 || page+step>pages;
   button.onclick=()=>{page+=step; renderArticles(); $('#review-count').scrollIntoView({block:'start'});};
   pager.append(button);
  }
 }
}

function reviewButton(post,action,label){
 const button=el('button',label);
 button.type='button';
 button.className=action==='approve'?'primary':'secondary';
 button.onclick=async()=>{
  const controls=button.parentElement.querySelectorAll('button');
  controls.forEach(control=>control.disabled=true);
  try{
   const response=await fetch('api/review',{
    method:'POST',
    headers:{'Content-Type':'application/json','X-Heisei-Editor':'1'},
    body:JSON.stringify({id:post.id,action})
   });
   if(!response.ok)throw Error((await response.json()).error);
   if(action==='withdraw'&&current?.id===post.id)select(null);
   await Promise.all([refreshReview(),load()]);
   const messages={
    withdraw:'掲載を取り下げ、確認待ちに戻しました。記事とコメントは保存されています。',
    approve:'採用しました。ローカルの通信に掲載されています。',
    reject:'見送りにしました。',
    pending:'確認待ちに戻しました。'
   };
   status(messages[action]);
  }catch(error){
   status(error.message,true);
  }finally{
   controls.forEach(control=>control.disabled=false);
  }
 };
 return button;
}
for(const option of $('#category').options)category.add(new Option(option.text,option.value));
search.value=new URLSearchParams(location.search).get('q') || '';
function changeFilters(){page=1;renderArticles();}
search.oninput=changeFilters;
filter.onchange=category.onchange=order.onchange=changeFilters;
refreshReview().catch(e=>status(e.message,true));
