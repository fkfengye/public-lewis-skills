#!/usr/bin/env node
import fs from 'node:fs/promises';
import path from 'node:path';
import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);
const args = process.argv.slice(2);
if (!args.length || args.includes('--help')) {
  process.stdout.write('用法：node render_svg.mjs input.svg --output output.png [--report qa.json] [--scale 2] [--strict] [--playwright-module 模块绝对路径]\nPlaywright 从正常模块解析、DIAGRAM_PLAYWRIGHT_MODULE 或 --playwright-module 获取；本脚本不安装依赖。\n');
  process.exit(args.length ? 0 : 2);
}
const input = path.resolve(args.shift());
const options = {scale: 2};
for (let i = 0; i < args.length; i++) {
  const flag = args[i];
  if (flag === '--strict') options.strict = true;
  else if (['--output', '--report', '--scale', '--playwright-module'].includes(flag)) {
    if (!args[i + 1]) throw new Error(`缺少参数值：${flag}`);
    options[flag.slice(2)] = args[++i];
  } else throw new Error(`未知参数：${flag}`);
}
if (!options.output) throw new Error('必须显式提供 --output');
options.scale = Number(options.scale);
if (!Number.isFinite(options.scale) || options.scale <= 0 || options.scale > 4) throw new Error('scale 必须在 0 到 4 之间');
const output = path.resolve(options.output), reportPath = path.resolve(options.report || output + '.qa.json');
const svgSource = await fs.readFile(input, 'utf8');
const { chromium } = require(options['playwright-module'] || process.env.DIAGRAM_PLAYWRIGHT_MODULE || 'playwright');
let browser;
try {
  browser = await chromium.launch({headless: true});
  const context = await browser.newContext({javaScriptEnabled: false, deviceScaleFactor: options.scale});
  const page = await context.newPage();
  const blocked = [];
  await page.route('**/*', route => { blocked.push(route.request().url()); return route.abort(); });
  await page.setContent('<!doctype html><html><head><meta charset="utf-8"><meta http-equiv="Content-Security-Policy" content="default-src \'none\'; script-src \'none\'; style-src \'unsafe-inline\'; img-src data:; font-src data:"><style>html,body{margin:0;background:white}svg{display:block}</style></head><body>' + svgSource + '</body></html>');
  const size = await page.locator('svg').first().evaluate(svg => ({width: svg.viewBox.baseVal.width, height: svg.viewBox.baseVal.height}));
  if (!(size.width > 0 && size.height > 0)) throw new Error('SVG 必须具有有效 viewBox');
  if (Math.max(size.width, size.height) * options.scale > 16000 || size.width * size.height * options.scale ** 2 > 80000000) {
    throw new Error('位图超过本脚本限幅，请降低 --scale 或拆分长图；源SVG保持不变');
  }
  await page.setViewportSize({width: Math.ceil(size.width), height: Math.ceil(size.height)});
  await page.locator('svg').first().evaluate(svg => {svg.setAttribute('width', svg.viewBox.baseVal.width); svg.setAttribute('height', svg.viewBox.baseVal.height);});
  await page.evaluate(() => document.fonts.ready);
  const geometry = await page.locator('svg').first().evaluate(svg => {
    const canvas = svg.getBoundingClientRect();
    const visible = element => {const s=getComputedStyle(element);return s.display!=='none'&&s.visibility!=='hidden'&&Number(s.opacity)!==0;};
    const text = [...svg.querySelectorAll('text')].filter(visible).map(e => ({element:e, label:e.textContent, rect:e.getBoundingClientRect()}));
    const outOfBounds = text.filter(t=>t.rect.left<canvas.left-.5||t.rect.right>canvas.right+.5||t.rect.top<canvas.top-.5||t.rect.bottom>canvas.bottom+.5).map(t=>t.label);
    const overlaps = [];
    text.forEach((a,i)=>text.slice(i+1).forEach(b=>{
      if(a.element.hasAttribute('data-qa-allow-overlap')||b.element.hasAttribute('data-qa-allow-overlap'))return;
      if(Math.min(a.rect.right,b.rect.right)-Math.max(a.rect.left,b.rect.left)>2&&Math.min(a.rect.bottom,b.rect.bottom)-Math.max(a.rect.top,b.rect.top)>2)overlaps.push([a.label,b.label]);
    }));
    const connectors=[...svg.querySelectorAll('path[data-diagram-role="connector"]')];
    const lineLabelIntersections=[];
    for(const connector of connectors){
      const length=connector.getTotalLength(),matrix=connector.getScreenCTM();
      if(!matrix)continue;
      const hits=new Set();
      for(let step=0;step<=Math.min(4000,Math.ceil(length/5));step++){
        const p=connector.getPointAtLength(length*step/Math.max(1,Math.min(4000,Math.ceil(length/5))));
        const pixel=new DOMPoint(p.x,p.y).matrixTransform(matrix);
        for(const t of text){if(t.element.hasAttribute('data-qa-allow-overlap'))continue;const r=t.rect;if(pixel.x>r.left+2&&pixel.x<r.right-2&&pixel.y>r.top+2&&pixel.y<r.bottom-2)hits.add(t.label);}
      }
      if(hits.size)lineLabelIntersections.push({id:connector.id||null,labels:[...hits]});
    }
    const references=[...svg.querySelectorAll('[href],[xlink\\:href]')].map(e=>e.getAttribute('href')||e.getAttribute('xlink:href')).filter(v=>v&&!v.startsWith('#')&&!v.startsWith('data:'));
    return {outOfBounds,textOverlaps:overlaps,connectorChecks:connectors.length,lineLabelIntersections,externalReferences:references,foreignObjects:svg.querySelectorAll('foreignObject').length};
  });
  await page.locator('svg').first().screenshot({path: output});
  const violations = geometry.outOfBounds.length + geometry.textOverlaps.length + geometry.lineLabelIntersections.length + geometry.externalReferences.length;
  const report={input,output,size,scale:options.scale,geometry,blockedRequests:blocked,staticGeometryPassed:violations===0,semanticReview:'required',visualReview:'required'};
  await fs.writeFile(reportPath, JSON.stringify(report,null,2)+'\n');
  process.stdout.write(JSON.stringify(report)+'\n');
  if(options.strict&&violations)process.exitCode=1;
} catch (error) {
  process.stderr.write(String(error.stack||error)+'\n');process.exitCode=2;
} finally {await browser?.close();}
