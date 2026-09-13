import { mkdir, writeFile, copyFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { person, papers, projects, elsewhere, reading, journals } from './data.mjs';

export const escape = value => String(value).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
export function link(label, href, extra = '') {
  if (!/^(https?:\/\/|mailto:|[a-z0-9-]+\.html(?:#[a-z0-9-]+)?$|#[a-z0-9-]+$)/i.test(href)) throw new Error(`Invalid link: ${href}`);
  return `<a href="${escape(href)}" ${extra}>${escape(label)}</a>`;
}
const links = items => `<div class="links">${items.map(([label, href]) => link(label, href)).join('')}</div>`;

function diagram(kind, compact = false) {
  const lines = (points, color = 'currentColor') => `<path d="${points}" stroke="${color}" fill="none" stroke-width="1.5"/>`;
  const node = (x, y, r = 5) => `<circle cx="${x}" cy="${y}" r="${r}" fill="var(--paper)" stroke="currentColor" stroke-width="1.5"/>`;
  const text = (x,y,t,cls='') => `<text x="${x}" y="${y}" class="${cls}">${t}</text>`;
  let drawing;
  switch (kind) {
    case 'library':
      drawing = [48,90,132].map(y => lines(`M35 ${y} H115 L155 90 H205 M205 90 L240 ${y} H285`) + node(35,y) + node(285,y)).join('') + '<rect x="130" y="65" width="75" height="50" fill="var(--paper)" stroke="var(--accent)" stroke-width="2"/>' + text(143,96,'NWQ','accent') + text(27,163,'PROBLEMS') + text(226,163,'RESULTS');
      break;
    case 'hybrid':
      drawing = lines('M25 65 C45 15 65 115 85 65 S125 15 145 65 S185 115 205 65 S245 15 285 65','var(--accent)') + lines('M25 120 H285') + '<rect x="76" y="107" width="25" height="26" fill="var(--paper)" stroke="currentColor"/>' + '<rect x="216" y="107" width="25" height="26" fill="var(--paper)" stroke="currentColor"/>' + lines('M156 65 V120') + node(156,65) + node(156,120) + text(25,163,'CONTINUOUS') + text(217,163,'DISCRETE');
      break;
    case 'downfolding':
      drawing = '<rect x="38" y="32" width="115" height="115" fill="none" stroke="currentColor"/>' + [1,2,3,4].map(i=>lines(`M38 ${32+23*i} H153 M${38+23*i} 32 V147`)).join('') + '<rect x="61" y="55" width="46" height="46" fill="var(--accent)" opacity=".2"/>' + lines('M167 90 H210 M204 84 L210 90 L204 96','var(--accent)') + '<rect x="228" y="63" width="55" height="55" fill="none" stroke="var(--accent)" stroke-width="2"/>' + lines('M255.5 63 V118 M228 90.5 H283','var(--accent)') + text(38,173,'FULL SPACE') + text(221,173,'ACTIVE SPACE');
      break;
    case 'subspace':
      drawing = lines('M60 136 L145 34 L278 70 L193 156 Z') + lines('M96 110 L183 60 L231 113 Z','var(--accent)') + node(96,110) + node(183,60) + node(231,113) + text(38,177,'STATES → SUBSPACE');
      break;
    case 'operator':
      drawing = lines('M28 82 Q48 30 67 83 T105 82','var(--accent)') + '<rect x="125" y="57" width="65" height="65" fill="none" stroke="currentColor"/>' + text(148,99,'G','operator-symbol') + lines('M211 105 Q232 42 250 62 T287 83','var(--accent)') + text(28,163,'INPUT') + text(219,163,'SOLUTION');
      break;
    case 'uncertainty':
      drawing = lines('M32 139 H285 M42 145 V36') + lines('M45 136 C100 136 118 52 160 52 S222 136 280 136','var(--accent)') + lines('M130 82 H194 M130 73 V91 M194 73 V91') + node(162,82) + text(43,172,'ESTIMATE & UNCERTAINTY');
      break;
    case 'workflow':
      drawing = [40,135,230].map((x,i) => `<rect x="${x}" y="67" width="50" height="50" fill="none" stroke="${i===1?'var(--accent)':'currentColor'}"/>`+text(x+15,98,String(i+1))).join('') + lines('M90 92 H135 M185 92 H230') + text(33,158,'QUESTION → METHOD → REVIEW');
      break;
    default:
      drawing = lines('M55 119 L103 49 L168 91 L242 38 M168 91 L251 141 M55 119 L133 152 L168 91') + [[55,119],[103,49],[168,91],[242,38],[251,141],[133,152]].map(([x,y])=>node(x,y,x===168?9:4)).join('') + text(29,180,'PLAN YOUR NEXT STEP');
  }
  return `<div class="diagram ${compact?'compact':''}"><svg viewBox="0 0 320 200" aria-hidden="true">${drawing}</svg>${compact?'':'<span class="diagram-caption">Conceptual illustration</span>'}</div>`;
}

function publication(id) {
  const p = papers[id];
  if (!p) throw new Error(`Unknown publication: ${id}`);
  return `<li class="publication"><div class="pub-meta">${escape(p.venue)} · ${p.year} <span>${escape(p.status)}</span></div><h4>${link(p.title, p.links[0][1])}</h4>${links(p.links)}${p.authors?`<details class="citation"><summary>Authors & citation</summary><p>${escape(p.authors)}.</p><p>${escape(p.title)}. ${escape(p.venue)} (${p.year}).${p.doi?` DOI: ${escape(p.doi)}.`:''}</p></details>`:''}</li>`;
}

function project(p, index) {
  return `<article class="project" id="${p.id}"><div class="project-visual"><span class="index">${String(index+1).padStart(2,'0')} / ${escape(p.type)}</span>${diagram(p.visual)}</div><div class="project-content"><div class="eyebrow status">${escape(p.status)}</div><h2>${escape(p.title)}</h2><p class="project-description">${escape(p.description)}</p>${links(p.links)}${p.note?`<p class="release-note">${escape(p.note)}</p>`:''}${p.detail||p.contribution?`<details class="project-detail"><summary>About this work${p.contribution?' & my contribution':''}</summary>${p.detail?`<p>${escape(p.detail)}</p>`:''}${p.contribution?`<p><strong>My contribution.</strong> ${escape(p.contribution)}</p>`:''}</details>`:''}${p.papers.length?`<h3 class="small-heading">Related publications</h3><ul class="publications">${[...p.papers].sort((a,b)=>(papers[b].date||String(papers[b].year)).localeCompare(papers[a].date||String(papers[a].year))).map(publication).join('')}</ul>`:''}</div></article>`;
}

function about() {
  return `<section class="hero"><div class="eyebrow">Quantum algorithms · Scientific computing</div><h1>Muqing Zheng<span class="name-period">.</span></h1><div class="role">Computer Scientist<span>Pacific Northwest National Laboratory</span></div><div class="bio"><p id="bio">${escape(person.bio)}</p><div class="bio-actions"><button class="copy-button" type="button" data-copy="bio">Copy bio <span aria-hidden="true">↗</span></button>${link('Get in touch ↗',`mailto:${person.email}`)}</div><span id="copy-status" class="sr-only" role="status"></span></div>${links(person.links)}</section><section class="current"><div class="section-heading"><h2>Currently working on</h2>${link('All projects ↗','projects.html')}</div><div class="current-grid">${projects.filter(p=>p.group==='current').map((p,i)=>`<a class="work-card" href="projects.html#${p.id}"><span class="index">0${i+1} / ${escape(p.type)}</span>${diagram(p.visual,true)}<h3>${escape(p.title)} <span aria-hidden="true">↗</span></h3><p>${escape(p.subtitle)}</p></a>`).join('')}</div></section><section class="elsewhere"><h2 class="eyebrow">Elsewhere</h2><ul class="elsewhere-list">${elsewhere.map(p=>`<li>${link(p.title+' ↗',p.url)}<p>${escape(p.description)}</p></li>`).join('')}</ul></section><aside class="reading" aria-label="Reading"><p><span class="reading-label">On my bookshelf</span>${reading.map(b=>`<span class="book"><cite>${escape(b.title)}</cite> — ${escape(b.author)}</span>`).join('; ')}.</p></aside>`;
}

function experience() {
  return `<section class="page-intro"><span class="eyebrow">Academic & professional background</span><h1>Experience.</h1></section><section class="cv-section"><h2>Appointments</h2><div class="timeline"><article><span class="timeline-date">May 2026–now</span><div><h3>Pacific Northwest National Laboratory</h3><p>Computer Scientist</p></div></article><article><span class="timeline-date">2024–2026</span><div><h3>Pacific Northwest National Laboratory</h3><p>Postdoctoral Research Associate</p></div></article><article><span class="timeline-date">2022–2024</span><div><h3>Pacific Northwest National Laboratory</h3><p>Ph.D. intern</p></div></article><article><span class="timeline-date">2020–2024</span><div><h3>Lehigh University</h3><p>Research Assistant</p></div></article></div></section><section class="cv-section"><h2>Education</h2><div class="timeline"><article><span class="timeline-date">2024</span><div><h3>Ph.D. in Industrial Engineering</h3><p>Lehigh University · Advisor: Xiu Yang</p><p class="secondary">Quantum Algorithm Implementations and a Classical Look on Quantum Error Mitigation</p></div></article><article><span class="timeline-date">2019</span><div><h3>B.S. in Mathematics</h3><p>Rose-Hulman Institute of Technology</p><p class="secondary">Mathematics and Computational Science double major</p></div></article></div></section><section class="cv-section"><h2>Teaching</h2><div class="timeline"><article><span class="timeline-date">Fall 2021</span><div><h3>Stochastic Models and Applications</h3><p>Teaching Assistant · ISE 429 · Lehigh University</p></div></article><article><span class="timeline-date">Spring 2021</span><div><h3>Optimization Algorithms and Software</h3><p>Teaching Assistant · ISE 355/455 · Lehigh University</p></div></article></div></section><section class="cv-section"><h2>Selected talks</h2><div class="timeline"><article><span class="timeline-date">Aug 2025</span><div><h3>Unleashed from constrained optimization: Quantum computing for quantum chemistry</h3><p>ACS Fall 2025</p></div></article><article><span class="timeline-date">Jul 2025</span><div><h3>Bypassing Optimization: Generator-Coordinate-Inspired Methods for Quantum Chemistry</h3><p>Quantum Computing User Forum</p></div></article><article><span class="timeline-date">Jun 2025</span><div><h3>An Early Investigation of the Quantum Linear Solver for Scientific Applications</h3><p>Software Frameworks for Integrating Quantum and HPC Ecosystems · ACM ICS</p></div></article><article><span class="timeline-date">Apr 2025</span><div><h3>Computational co-design of quantum computing applications to quantum chemistry</h3><p>Workshop on Quantum Computing Applications in Quantum Chemistry</p></div></article></div></section><section class="cv-section"><h2>Journal reviewing</h2><ul class="service-list">${journals.map(j=>`<li>${escape(j)}</li>`).join('')}</ul></section><section class="research-end">${link('View projects & publications ↗','projects.html')}</section>`;
}

function projectPage() {
  const groups = [['current','In progress'],['research','Research contributions']];
  return `<section class="page-intro"><span class="eyebrow">Projects & publications</span><h1>Work, in context.</h1><p>Quantum algorithms, scientific software, and related publications.</p><nav class="jump-links" aria-label="Project sections">${groups.map(([id,title])=>link(title,`#${id}`)).join('')}</nav></section>${groups.map(([id,title])=>`<section class="project-group" id="${id}"><div class="group-heading"><h2>${title}</h2><span>${String(projects.filter(p=>p.group===id).length).padStart(2,'0')}</span></div>${projects.filter(p=>p.group===id).map(p=>project(p,projects.indexOf(p))).join('')}</section>`).join('')}`;
}

function layout(page, content) {
  const names = {about:'About',experience:'Experience',projects:'Projects'};
  return `<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta name="description" content="Muqing Zheng, Computer Scientist at Pacific Northwest National Laboratory. Quantum algorithms, scientific computing, and research software."><meta name="theme-color" content="#f6f5f1"><meta property="og:title" content="Muqing Zheng | ${names[page]}"><meta property="og:description" content="Quantum algorithms, scientific computing, and research software."><meta property="og:type" content="website"><title>${names[page]} · Muqing Zheng</title><link rel="icon" href="favicon.svg" type="image/svg+xml"><link rel="stylesheet" href="style.css"><script src="site.js" defer></script></head><body><a class="skip-link" href="#main">Skip to content</a><div class="shell"><header class="site-header"><a class="wordmark" href="index.html" aria-label="Muqing Zheng, home">MZ<span class="wordmark-dot">.</span></a><nav aria-label="Main navigation">${Object.entries(names).map(([key,name])=>link(name,key==='about'?'index.html':`${key}.html`,page===key?'aria-current="page"':'')).join('')}</nav></header><main id="main">${content}</main><footer><div><span>Muqing Zheng</span><span class="secondary">Quantum algorithms & scientific computing</span></div></footer></div></body></html>`;
}

export async function build() {
  await mkdir(new URL('./dist/', import.meta.url), {recursive:true});
  for (const [page,content] of [['about',about()],['experience',experience()],['projects',projectPage()]]) {
    await writeFile(new URL(`./dist/${page==='about'?'index':page}.html`,import.meta.url),layout(page,content));
  }
  for (const name of ['style.css','site.js','favicon.svg']) await copyFile(new URL(`./${name}`,import.meta.url),new URL(`./dist/${name}`,import.meta.url));
  await writeFile(new URL('./dist/.nojekyll',import.meta.url),'');
}
if (process.argv[1] && fileURLToPath(import.meta.url) === process.argv[1]) {
  await build();
  console.log('Built dist/: About, Experience, Projects.');
}
