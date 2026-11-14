#!/usr/bin/env node
// resume-data.json -> 自包含 HTML 简历。
//
// 用法：
//   node scripts/build-html.mjs <resume-data.json> <输出.html> [--variant <变体名>] [--shell <壳文件>]
//
// 行为：
//   1. 按 resume-data.schema.json 的事实结构读取数据（字段见 assets/resume-data-template.json）
//   2. 选一个壳文件：--shell 显式指定 > --variant 匹配 > data.meta.target_variant > variant-black
//   3. 复用壳的 <head> 与 <body> 类，替换 <main> 与 <title>
//   4. 调用 scripts/lib/frame-inline.mjs 内联 CSS/工具栏/编辑器，输出自包含 HTML
//
// 零 npm 依赖（Node 18+）。

import fs from 'node:fs';
import path from 'node:path';
import process from 'node:process';
import { fileURLToPath } from 'node:url';
import { inlineShell } from './lib/frame-inline.mjs';

const HERE = fileURLToPath(import.meta.url);
const ROOT = path.resolve(path.dirname(HERE), '..');
const TEMPLATES_DIR = path.join(ROOT, 'assets', 'templates-html');
const FRAME_DIR = path.join(ROOT, 'assets', 'frame');

const esc = (s) =>
  String(s == null ? '' : s)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');

function bulletItems(bullets) {
  if (!Array.isArray(bullets) || !bullets.length) return '';
  const items = bullets
    .map((b) => (typeof b === 'string' ? esc(b) : `${esc(b.label || '')}${esc(b.text || '')}`))
    .filter(Boolean)
    .map((t) => `<li>${t}</li>`)
    .join('');
  return items ? `<ul class="bullet-list">${items}</ul>` : '';
}

function section(title, en, inner) {
  if (!inner) return '';
  const enHtml = en ? `<span class="section-en">${esc(en)}</span>` : '';
  return `<section class="resume-section"><h2 class="section-title"><span>${esc(title)}</span>${enHtml}</h2>${inner}</section>`;
}

function entries(list, { title, en, orgKey, roleKey, nameKey }) {
  if (!Array.isArray(list) || !list.length) return '';
  const body = list
    .map((item) => {
      const org = item[orgKey] || item[nameKey] || '';
      const role = item[roleKey] || '';
      const head = `<div class="entry-head"><span class="date">${esc(item.dates || '')}</span><strong class="org">${esc(org)}</strong><strong class="role">${esc(role)}</strong></div>`;
      const copy = item.text ? `<p class="entry-copy">${esc(item.text)}</p>` : '';
      return `<article class="entry">${head}${copy}${bulletItems(item.bullets)}</article>`;
    })
    .join('');
  return section(title, en, body);
}

function standalone(title, en, list) {
  if (!Array.isArray(list) || !list.length) return '';
  const items = list
    .map((x) => (typeof x === 'string' ? esc(x) : `${esc(x.label || '')}${esc(x.text || '')}`))
    .map((t) => `<li>${t}</li>`)
    .join('');
  return section(title, en, `<ul class="bullet-list standalone">${items}</ul>`);
}

function buildMain(data, photoRef) {
  const p = data.profile || {};
  const contacts = [p.city, p.phone, p.email, p.wechat_or_portfolio, p.language_cert, p.birth_place]
    .filter(Boolean)
    .map((x) => `<span>${esc(x)}</span>`)
    .join('');
  const photo = photoRef
    ? `<figure class="photo-frame has-photo"><img src="${esc(photoRef)}" alt="${esc(p.name || '')}"></figure>`
    : '';

  const header = `<header class="resume-header"><div class="identity"><h1>${esc(p.name)}</h1><p class="headline">${esc(p.target_role)}</p><div class="contact-grid">${contacts}</div></div>${photo}</header>`;

  const parts = [
    header,
    data.summary ? section('个人简介', 'Profile', `<p class="section-copy">${esc(data.summary)}</p>`) : '',
    entries(data.education, { title: '教育背景', en: 'Education', orgKey: 'school', roleKey: 'major_degree' }),
    entries(data.experience, { title: '实习与工作经历', en: 'Experience', orgKey: 'organization', roleKey: 'role' }),
    entries(data.projects, { title: '项目经历', en: 'Projects', nameKey: 'name', roleKey: 'role' }),
    standalone('技能证书', 'Skills', data.skills),
    standalone('荣誉与奖项', 'Honors', data.awards),
    (data.extra_sections || [])
      .map((s) => standalone(s.title, s.en || '', s.bullets))
      .join(''),
  ];
  return `<main class="resume-page" contenteditable="false">${parts.join('')}</main>`;
}

function pickShell(variant, explicitShell) {
  if (explicitShell) return path.resolve(explicitShell);
  const files = fs.readdirSync(TEMPLATES_DIR).filter((f) => f.endsWith('.html'));
  // 允许传入 "black" 或 "variant-black"
  const v = variant ? variant.replace(/^variant-/, '') : '';
  if (v) {
    const hit = files.find((f) => f.startsWith(`variant-${v}-`) || f === `variant-${v}.html`);
    if (hit) return path.join(TEMPLATES_DIR, hit);
  }
  const fallback = files.find((f) => f.startsWith('variant-black-')) || files[0];
  if (!fallback) throw new Error('assets/templates-html 下没有可用壳文件');
  if (variant) console.warn(`未找到变体 ${variant} 的壳文件，改用 ${fallback}`);
  return path.join(TEMPLATES_DIR, fallback);
}

function main() {
  const args = process.argv.slice(2);
  const flags = {};
  const positional = [];
  for (let i = 0; i < args.length; i += 1) {
    if (args[i] === '--variant' || args[i] === '--shell') {
      flags[args[i].slice(2)] = args[i + 1];
      i += 1;
    } else {
      positional.push(args[i]);
    }
  }
  const [dataPath, outPath] = positional;
  if (!dataPath || !outPath) {
    console.error('用法：node scripts/build-html.mjs <resume-data.json> <输出.html> [--variant <变体>] [--shell <壳文件>]');
    process.exit(2);
  }

  const dataFile = path.resolve(dataPath);
  const data = JSON.parse(fs.readFileSync(dataFile, 'utf8'));
  if (!data.profile || !data.profile.name) throw new Error('resume-data 缺少 profile.name');
  if (!data.profile.target_role) throw new Error('resume-data 缺少 profile.target_role');

  const shellPath = pickShell(flags.variant || (data.meta && data.meta.target_variant), flags.shell);
  let shell = fs.readFileSync(shellPath, 'utf8');

  // 照片：用户提供真实文件时复制到输出目录并引用相对路径；无则整块删除
  let photoRef = '';
  if (data.profile.photo) {
    const absPhoto = path.resolve(path.dirname(dataFile), data.profile.photo);
    if (fs.existsSync(absPhoto)) {
      const outDir = path.dirname(path.resolve(outPath));
      fs.mkdirSync(outDir, { recursive: true });
      const dest = path.join(outDir, path.basename(absPhoto));
      fs.copyFileSync(absPhoto, dest);
      photoRef = `./${path.basename(absPhoto)}`;
    } else {
      console.warn(`照片文件不存在，已跳过：${data.profile.photo}`);
    }
  }

  shell = shell.replace(/<title>[^<]*<\/title>/, `<title>${esc(data.profile.name)}｜${esc(data.profile.target_role)}</title>`);
  const mainHtml = buildMain(data, photoRef);
  if (!/<main class="resume-page"[^>]*>[\s\S]*<\/main>/.test(shell)) {
    throw new Error(`壳文件结构不符合预期（缺少 main.resume-page）：${shellPath}`);
  }
  shell = shell.replace(/<main class="resume-page"[^>]*>[\s\S]*<\/main>/, mainHtml);
  // 无照片时同时移除壳里残留的演示照片容器（新壳已无条件渲染，这里仅兜底）
  if (!photoRef) shell = shell.replace(/<figure class="photo-frame[\s\S]*?<\/figure>/, '');

  const out = inlineShell(shell, { frameDir: FRAME_DIR });
  const target = path.resolve(outPath);
  fs.mkdirSync(path.dirname(target), { recursive: true });
  fs.writeFileSync(target, out);
  console.log(`已生成 ${target}（壳：${path.basename(shellPath)}，${(out.length / 1024).toFixed(1)} KB）`);
}

main();
