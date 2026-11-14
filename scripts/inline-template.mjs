#!/usr/bin/env node
// 壳文件 -> 自包含 HTML。
//
// 背景：assets/templates-html/ 下的模板外框（style / 顶部工具栏 / script）已抽成共享
// assets/frame/ 公共部件，模板文件为纯设计稿壳文件（内容 + frame/base.css 链接）。本脚本把壳文件
// 确定性组装为包含共享功能的 HTML，交付用户前必须经过它。内联逻辑在 scripts/lib/frame-inline.mjs，
// 与 build-html.mjs 共用。
//
// 用法：
//   node scripts/inline-template.mjs <壳文件> [输出文件]    # 无输出文件时打印到 stdout
//   node scripts/inline-template.mjs --all <输出目录>        # 内联 assets/templates-html/ 下全部壳文件
//   node scripts/inline-template.mjs --check <基准目录>      # 内联全部壳文件并与基准目录同名文件逐字节比对
//
// 零依赖；内联是确定性的——交付统一走本脚本即得一致产物，不维护逐字节基准。
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import process from 'node:process';
import { fileURLToPath } from 'node:url';
import { inlineShell } from './lib/frame-inline.mjs';

const HERE = fileURLToPath(import.meta.url);
const TEMPLATES_DIR = path.resolve(path.dirname(HERE), '..', 'assets', 'templates-html');
const FRAME_DIR = path.resolve(TEMPLATES_DIR, '..', 'frame');

function inlineOne(shellPath) {
  const html = fs.readFileSync(shellPath, 'utf8');
  try {
    return inlineShell(html, { frameDir: FRAME_DIR });
  } catch (err) {
    throw new Error(`${err.message}：${shellPath}`);
  }
}

function inlineAll(outDir) {
  fs.mkdirSync(outDir, { recursive: true });
  const files = fs.readdirSync(TEMPLATES_DIR).filter((f) => f.endsWith('.html')).sort();
  for (const f of files) {
    const out = inlineOne(path.join(TEMPLATES_DIR, f));
    fs.writeFileSync(path.join(outDir, f), out);
  }
  return files;
}

function checkAll(baselineDir) {
  const outDir = fs.mkdtempSync(path.join(os.tmpdir(), 'inline-template-'));
  const files = inlineAll(outDir);
  let ok = true;
  try {
    for (const f of files) {
      const baselinePath = path.join(baselineDir, f);
      if (!fs.existsSync(baselinePath)) {
        console.error(`缺少基准文件：${f}`);
        ok = false;
        continue;
      }
      const outBytes = fs.readFileSync(path.join(outDir, f));
      const baselineBytes = fs.readFileSync(baselinePath);
      if (Buffer.compare(outBytes, baselineBytes) !== 0) {
        console.error(`逐字节不一致：${f}`);
        ok = false;
      } else {
        console.log(`逐字节一致：${f}`);
      }
    }
  } finally {
    fs.rmSync(outDir, { recursive: true, force: true });
  }
  return ok;
}

const [arg1, arg2] = process.argv.slice(2);

if (arg1 === '--all') {
  if (!arg2) {
    console.error('用法：node scripts/inline-template.mjs --all <输出目录>');
    process.exit(2);
  }
  inlineAll(arg2);
  console.log(`已内联 ${TEMPLATES_DIR} 下全部壳文件到 ${arg2}`);
} else if (arg1 === '--check') {
  if (!arg2) {
    console.error('用法：node scripts/inline-template.mjs --check <基准目录>');
    process.exit(2);
  }
  process.exit(checkAll(arg2) ? 0 : 1);
} else if (arg1) {
  const out = inlineOne(arg1);
  if (arg2) fs.writeFileSync(arg2, out);
  else process.stdout.write(out);
} else {
  console.error(`用法见文件头部注释。TEMPLATES_DIR=${TEMPLATES_DIR}`);
  process.exit(2);
}
