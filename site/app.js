'use strict';
const feed = window.HEISEI_FEED || {posts:[],updated_at:null};
let category = 'すべて', kind = 'all', query = '';
let saved = new Set();
try { saved = new Set(JSON.parse(localStorage.getItem('heisei-saved') || '[]')); } catch (_) {}
const $ = s => document.querySelector(s);
const node = (tag, cls, text) => {const e = document.createElement(tag); if(cls)e.className=cls; if(text!==undefined)e.textContent=text; return e;};
const date = value => new Intl.DateTimeFormat('ja-JP',{year:'numeric',month:'2-digit',day:'2-digit',timeZone:'Asia/Tokyo'}).format(new Date(value));
const safeUrl = value => {try {const u = new URL(value); return u.protocol === 'https:' && !u.username && !u.password ? u.href : null;}catch(_){return null;}};
function sourceLink(p) {const a = node('a','source',`${p.source_name}で読む ↗`);const url=safeUrl(p.source_url);if(url){a.href=url;a.target='_blank';a.rel='noopener noreferrer';}return a;}
function article(p, index) {
  const a = node('article','entry'+(index===0?' featured':'')); a.id=p.id;
  const meta=node('div','meta');meta.append(node('span','tag'+(p.type==='thought'?' thought':''),p.category));
  const archive = p.type==='news' && new Date(p.created_at)-new Date(p.published_at)>7*86400000;
  meta.append(node('span','',p.type==='thought'?'つぶやき':archive?'再発見':'ニュース'));
  meta.append(node('time','',`紹介 ${date(p.created_at)}`));
  if(p.type==='news')meta.append(node('time','',`元記事 ${date(p.published_at)}`));
  a.append(meta);
  const heading=node('h3');
  if(p.type==='news' && safeUrl(p.source_url)){const link=node('a','',p.title);link.href=safeUrl(p.source_url);link.target='_blank';link.rel='noopener noreferrer';heading.append(link);}else heading.textContent=p.title;
  a.append(heading);
  if(p.summary)a.append(node('p','summary',p.summary));
  if(p.comment){const box=node('div','comment');box.append(node('span','comment-label',p.type==='thought'?'ひとりごと / EDITOR’S NOTE':'ひとこと / EDITOR’S COMMENT'),node('p','',p.comment));a.append(box);}
  if(p.selection_reason)a.append(node('p','reason',`AIが拾った理由：${p.selection_reason}`));
  const actions=node('div','entry-actions');
  if(p.type==='news')actions.append(sourceLink(p));else actions.append(node('span','',date(p.created_at)));
  const b=node('button','save',saved.has(p.id)?'★ 保存済み':'☆ あとで読む');b.type='button';b.setAttribute('aria-pressed',String(saved.has(p.id)));b.setAttribute('aria-label',`${p.title}を${saved.has(p.id)?'保存から外す':'保存する'}`);
  b.onclick=()=>{if(saved.has(p.id))saved.delete(p.id);else saved.add(p.id);try{localStorage.setItem('heisei-saved',JSON.stringify([...saved]));}catch(_){}render();};actions.append(b);a.append(actions);
  if(p.ai_generated)a.append(node('p','reason','AI選定・要約｜コメントは書き手本人が追記します'));
  return a;
}
function render(){
  const posts=feed.posts.filter(p=>(category==='すべて'||p.category===category)&&(kind==='all'||(kind==='saved'?saved.has(p.id):p.type===kind))&&[p.title,p.summary,p.comment,p.category].join(' ').toLocaleLowerCase().includes(query.toLocaleLowerCase())).sort((a,b)=>new Date(b.created_at)-new Date(a.created_at));
  $('#feed').replaceChildren(...posts.map(article));$('#count').textContent=`${posts.length}件の投稿`;
  if(!posts.length){const e=node('div','empty');e.append(node('strong','',kind==='saved'?'あとで読みたい記事を、ここに。':kind==='thought'?'最初のつぶやきは、これから。':'該当する投稿はまだありません。'),node('p','',kind==='saved'?'記事の「☆ あとで読む」で、このブラウザに保存できます。':'別のジャンルや検索語でも探してみてください。'));$('#feed').append(e);}
}
document.querySelectorAll('[data-category]').forEach(b=>b.onclick=()=>{category=b.dataset.category;document.querySelectorAll('[data-category]').forEach(x=>{x.classList.toggle('active',x===b);x.setAttribute('aria-pressed',String(x===b));});render();});
document.querySelectorAll('[data-kind]').forEach(b=>b.onclick=()=>{kind=b.dataset.kind;document.querySelectorAll('[data-kind]').forEach(x=>{x.classList.toggle('active',x===b);x.setAttribute('aria-pressed',String(x===b));});render();});
$('#search').addEventListener('input',e=>{query=e.target.value;render();});
$('#updated').textContent=feed.updated_at?`更新 ${date(feed.updated_at)}`:'最初の配信を準備中';
const notes=feed.posts.filter(p=>p.type==='thought').sort((a,b)=>new Date(b.created_at)-new Date(a.created_at)).slice(0,3);
if(notes.length)for(const p of notes){const e=node('article');e.append(node('time','',date(p.created_at)),node('p','',p.comment.slice(0,100)+(p.comment.length>100?'…':'')));const a=node('a','','続きを読む →');a.href='#'+p.id;a.onclick=()=>{category='すべて';kind='all';query='';$('#search').value='';document.querySelector('[data-category="すべて"]').click();document.querySelector('[data-kind="all"]').click();};e.append(a);$('#notes').append(e);}else $('#notes').append(node('p','','聴いた曲のこと。観た番組のこと。書き手のつぶやきが、ここに並びます。'));
if(['127.0.0.1','localhost'].includes(location.hostname))$('#editor-link').hidden=false;
render();
