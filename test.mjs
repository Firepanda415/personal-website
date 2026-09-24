import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile, access, stat } from 'node:fs/promises';
import { build, escape, link } from './build.mjs';
import { projects, papers } from './data.mjs';

test('pages build with valid structure and links', async () => {
  await build();
  const plannerUrl = new URL('dist/sfskills/index.html', import.meta.url);
  const planner = await readFile(plannerUrl, 'utf8');
  assert.match(planner, /Starfield Skill Command Generator/);
  for (const [,asset] of planner.matchAll(/(?:src|href)="(\.\/[^\"]+)"/g)) {
    await access(new URL(asset, plannerUrl));
  }
  await access(new URL('LICENSE', plannerUrl));
  const wdUrl = new URL('dist/wdtool/index.html', import.meta.url);
  const wd = await readFile(wdUrl, 'utf8');
  assert.match(wd, /WARDOGS/);
  for (const [,asset] of wd.matchAll(/(?:src|href)="(\.\/[^\"]+)"/g)) await access(new URL(asset, wdUrl));
  const wdAppUrl = new URL('app.js', wdUrl);
  const wdApp = await readFile(wdAppUrl, 'utf8');
  for (const [,module] of wdApp.matchAll(/\bfrom\s*['"](\.\/[^'"]+)['"]/g)) await access(new URL(module, wdAppUrl));
  await access(new URL('THIRD_PARTY_NOTICES.md', wdUrl));
  await assert.rejects(access(new URL('assets/maps/', wdUrl)), {code:'ENOENT'});
  const tileManifest = JSON.parse(await readFile(new URL('assets/maps-display/manifest.json', wdUrl), 'utf8'));
  assert.ok(Object.keys(tileManifest.files).length > 0);
  for (const [path, {bytes}] of Object.entries(tileManifest.files)) {
    assert.equal((await stat(new URL(`assets/maps-display/${path}`, wdUrl))).size, bytes, `Missing or truncated map tile: ${path}`);
  }
  assert.equal(new Set(projects.map(p=>p.id)).size,projects.length);
  const referenced = projects.flatMap(p=>p.papers);
  assert.deepEqual([...new Set(referenced)].sort(),Object.keys(papers).sort());
  assert.equal(referenced.length,new Set(referenced).size,'Do not duplicate papers between groups');
  for (const name of ['index.html','experience.html','projects.html']) {
    const html = await readFile(new URL(`dist/${name}`,import.meta.url),'utf8');
    assert.match(html,/<html lang="en">/);
    assert.equal((html.match(/<h1[ >]/g)||[]).length,1);
    assert.equal((html.match(/aria-current="page"/g)||[]).length,1);
    for (const [,href] of html.matchAll(/href="([^"#:]*(?:#[^"]*)?)"/g)) {
      if (!href || href.startsWith('http')) continue;
      const [file,fragment] = href.split('#');
      const path = new URL(`dist/${file||name}`,import.meta.url);
      await access(path);
      if (fragment) assert.ok((await readFile(path,'utf8')).includes(`id="${fragment}"`),`${name}: broken anchor ${href}`);
    }
  }
  const html = await readFile(new URL('dist/projects.html',import.meta.url),'utf8');
  assert.ok(html.indexOf('id="nwqlib"') < html.indexOf('id="quantum-optimization"'));
  assert.match(html,/Public release in preparation/);
  const explained = Object.values(papers).filter(p=>p.explainer);
  if (explained.length) assert.equal((html.match(/<dialog class="explainer-dialog"/g)||[]).length,1);
  for (const {explainer} of explained) {
    for (const key of ['video','poster']) {
      assert.ok((await stat(new URL(`dist/${explainer[key]}`,import.meta.url))).size > 0,`Missing explainer ${key}: ${explainer[key]}`);
    }
    assert.ok(html.includes(`data-explainer="${explainer.video}"`));
    assert.match(explainer.duration,/^\d+:\d\d$/);
  }
});

test('text is escaped and unsafe link protocols rejected', () => {
  assert.equal(escape('<script a="x">&\''),'&lt;script a=&quot;x&quot;&gt;&amp;&#39;');
  assert.throws(()=>link('bad','javascript:alert(1)'));
  assert.throws(()=>link('bad','file:///etc/passwd'));
  assert.match(link('Email','mailto:a@example.com'),/mailto:a@example.com/);
});
