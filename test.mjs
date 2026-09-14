import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile, access } from 'node:fs/promises';
import { build, escape, link } from './build.mjs';
import { projects, papers } from './data.mjs';

test('pages build with valid structure and links', async () => {
  await build();
  const plannerUrl = new URL('dist/sf_skills/index.html', import.meta.url);
  const planner = await readFile(plannerUrl, 'utf8');
  assert.match(planner, /Starfield Skill Command Generator/);
  for (const [,asset] of planner.matchAll(/(?:src|href)="(\.\/[^\"]+)"/g)) {
    await access(new URL(asset, plannerUrl));
  }
  await access(new URL('LICENSE', plannerUrl));
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
});

test('text is escaped and unsafe link protocols rejected', () => {
  assert.equal(escape('<script a="x">&\''),'&lt;script a=&quot;x&quot;&gt;&amp;&#39;');
  assert.throws(()=>link('bad','javascript:alert(1)'));
  assert.throws(()=>link('bad','file:///etc/passwd'));
  assert.match(link('Email','mailto:a@example.com'),/mailto:a@example.com/);
});
