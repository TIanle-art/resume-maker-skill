#!/usr/bin/env node
// 共享部件内联（frame -> 自包含 HTML）。
// 由 inline-template.mjs 与 build-html.mjs 共用，保证两条构建路径产出同一套 CSS/工具栏/编辑器。

import fs from 'node:fs';
import path from 'node:path';

export const FRAME_LINK = '<link rel="stylesheet" href="../frame/base.css">';
const FRAME_LINK_GENERIC = /<link\s+rel="stylesheet"\s+href="[^"]*frame\/base\.css"\s*>/;
const SHELL_ONLY_RE = /\r?\n\/\* @@SHELL-ONLY-START@@[\s\S]*?@@SHELL-ONLY-END@@ \*\/\r?\n/;

/**
 * 把壳 HTML 组装为自包含 HTML。
 * @param {string} html 壳文件内容
 * @param {{frameDir:string}} opts frame 目录绝对路径
 * @returns {string}
 */
export function inlineShell(html, { frameDir }) {
  if (!FRAME_LINK_GENERIC.test(html)) {
    throw new Error(`不是壳文件（缺少 frame/base.css 链接）`);
  }
  if (!html.includes(' design-preview')) {
    throw new Error(`不是壳文件（缺少 design-preview 类）`);
  }

  const eol = html.includes('\r\n') ? '\r\n' : '\n';

  // 1) 移除 design-preview（壳文件无 toolbar 的观感处理，交付产物不带）
  let out = html.replace(' design-preview', '');

  // 2) 内联共享工具栏与版式 CSS，剥离壳文件预览专用规则
  const css = fs
    .readFileSync(path.join(frameDir, 'base.css'), 'utf8')
    .replace('@import url("toolbar.css");', fs.readFileSync(path.join(frameDir, 'toolbar.css'), 'utf8'))
    .replace(SHELL_ONLY_RE, '');
  out = out.replace(FRAME_LINK_GENERIC, `<style>${eol}${css}</style>`);

  // 3) 注入顶部工具栏
  const toolbar = fs.readFileSync(path.join(frameDir, 'toolbar.html'), 'utf8');
  out = out.replace(/<body[^>]*>\r?\n/, (m) => m + toolbar);

  // 4) 注入编辑脚本
  const editor = fs.readFileSync(path.join(frameDir, 'editor.js'), 'utf8');
  out = out.replace('</body>', `<script>${eol}${editor}</script></body>`);

  return out;
}

export function defaultFrameDir(fileUrl) {
  return path.resolve(path.dirname(fileUrl), '..', '..', 'assets', 'frame');
}

export function templatesDir(fileUrl) {
  return path.resolve(path.dirname(fileUrl), '..', '..', 'assets', 'templates-html');
}
