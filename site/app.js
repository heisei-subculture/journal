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
  const a = node('article','entry'+(index===0?' featured':'')); a.id=p.id; a.dataset.category=p.category;
  const cover=node('div','cover');cover.setAttribute('aria-hidden','true');
  const words={'音楽':['J-POP','MUSIC'],'アイドル':['アイドル','IDOL'],'映画・マンガ':['映画と','マンガ'],'お笑い':['お笑い','COMEDY'],'雑記':['日々の','メモ']};
  const topics={
    'tsunku-2007':['LOVE\nマシーン','つんく♂ / 2007'],
    'sasaji-2026':['スピッツ\nユニコーン\nプリプリ','笹路正徳 / 2026'],
    'nakagawake-2021':['M-1の\nその後。','中川家 / 2021'],
    'battle-royale-2025':['バトル・\nロワイアル','藤原竜也 / 深作欣二'],
    'ytv-2026':['次の\n漫才師。','ytv漫才新人賞 / 2026']
  };
  const label=topics[p.id]||words[p.category]||[p.category,'JOURNAL'];
  cover.append(node('span','cover-index',String(index+1).padStart(2,'0')),node('strong','cover-word',label[0]),node('span','cover-sub',label[1]));
  a.append(cover);
  const body=node('div','card-body');
  const meta=node('div','meta');meta.append(node('span','tag'+(p.type==='thought'?' thought':''),p.category));
  const archive = p.type==='news' && new Date(p.created_at)-new Date(p.published_at)>7*86400000;
  meta.append(node('span','',p.type==='thought'?'つぶやき':archive?'再発見':'ニュース'));
  meta.append(node('time','',`紹介 ${date(p.created_at)}`));
  if(p.type==='news')meta.append(node('time','',`元記事 ${date(p.published_at)}`));
  body.append(meta);
  const heading=node('h3');
  if(p.type==='news' && safeUrl(p.source_url)){const link=node('a','',p.title);link.href=safeUrl(p.source_url);link.target='_blank';link.rel='noopener noreferrer';heading.append(link);}else heading.textContent=p.title;
  body.append(heading);
  if(p.summary)body.append(node('p','summary',p.summary));
  if(p.comment){const box=node('div','comment');box.append(node('span','comment-label',p.type==='thought'?'ひとりごと / EDITOR’S NOTE':'ひとこと / EDITOR’S COMMENT'),node('p','',p.comment));body.append(box);}

  const actions=node('div','entry-actions');
  if(p.type==='news')actions.append(sourceLink(p));else actions.append(node('span','',date(p.created_at)));
  const b=node('button','save',saved.has(p.id)?'★ 保存済み':'☆ あとで読む');b.type='button';b.setAttribute('aria-pressed',String(saved.has(p.id)));b.setAttribute('aria-label',`${p.title}を${saved.has(p.id)?'保存から外す':'保存する'}`);
  b.onclick=()=>{if(saved.has(p.id))saved.delete(p.id);else saved.add(p.id);try{localStorage.setItem('heisei-saved',JSON.stringify([...saved]));}catch(_){}render();};actions.append(b);body.append(actions);
  if(p.ai_generated)body.append(node('p','reason','AI選定・要約'));
  a.append(body);
  return a;
}
function render(){
  const posts=feed.posts.filter(p=>(category==='すべて'||p.category===category)&&(kind==='all'||(kind==='saved'?saved.has(p.id):p.type===kind))&&[p.title,p.summary,p.comment,p.category].join(' ').toLocaleLowerCase().includes(query.toLocaleLowerCase())).sort((a,b)=>new Date(b.created_at)-new Date(a.created_at));
  $('#feed').replaceChildren(...posts.map(article));$('#count').textContent=`${posts.length}件の投稿`;
  if(!posts.length){const e=node('div','empty');e.append(node('strong','',kind==='saved'?'保存した記事はありません。':kind==='thought'?'つぶやきはまだありません。':'該当する投稿はまだありません。'),node('p','',kind==='saved'?'記事の「☆ あとで読む」で、このブラウザに保存できます。':'別のジャンルや検索語でも探してみてください。'));$('#feed').append(e);}
}
document.querySelectorAll('[data-category]').forEach(b=>b.onclick=()=>{category=b.dataset.category;document.querySelectorAll('[data-category]').forEach(x=>{x.classList.toggle('active',x===b);x.setAttribute('aria-pressed',String(x===b));});render();});
document.querySelectorAll('[data-kind]').forEach(b=>b.onclick=()=>{kind=b.dataset.kind;document.querySelectorAll('[data-kind]').forEach(x=>{x.classList.toggle('active',x===b);x.setAttribute('aria-pressed',String(x===b));});render();});
$('#search').addEventListener('input',e=>{query=e.target.value;render();});
$('#updated').textContent=feed.updated_at?`更新 ${date(feed.updated_at)}`:'最初の配信を準備中';
if(['127.0.0.1','localhost'].includes(location.hostname))$('#editor-link').hidden=false;
render();
