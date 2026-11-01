import assert from 'node:assert/strict';
import { createNaverOps, fileName } from '../automation/browser_helpers.mjs';

assert.equal(fileName('C:\\사진 폴더\\대표사진.png'), '대표사진.png');
assert.equal(fileName('/photos/대표사진.png'), '대표사진.png');
assert.throws(() => createNaverOps({}, {}), /platform/);

function editor(selected = '처음 마지막') {
  const calls = [];
  const paragraphs = {
    filter() { return this; }, first() { return this; }, last() { return this; },
    async click(options) { calls.push(['select', options]); }
  };
  const frame = {
    getByRole(role, options) {
      if (role === 'article') return { evaluate: async () => ({ groups: [{ id: 'text', text: '처음 마지막' }], images: ['image'] }) };
      return { waitFor: async () => calls.push(['loaded', options.name]) };
    },
    locator(selector) {
      if (selector === '#text p') return paragraphs;
      if (selector === '.se-component.se-image') return { evaluateAll: async () => ['image'] };
      throw Error('Unexpected selector: ' + selector);
    }
  };
  return {
    calls, playwright: { frameLocator: () => frame },
    pressKey: async (_, key) => calls.push(['key', key]),
    getAXState: async () => 'observed',
    clipboard: { readText: async () => selected },
    paste: async (_, value) => calls.push(['paste', value])
  };
}

for (const platform of ['mac', 'windows']) {
  const ed = editor();
  await createNaverOps(ed, {}, { platform }).replaceTextGroup(0, '<p>새 본문</p>');
  assert(ed.calls.some(c => c[0] === 'key' && c[1] === (platform === 'mac' ? 'super+c' : 'ctrl+c')));
  assert(ed.calls.some(c => c[0] === 'paste'));
}
const wrong = editor('마지막만');
await assert.rejects(createNaverOps(wrong, {}, { platform: 'windows' }).replaceTextGroup(0, '<p>x</p>'), /전체 선택/);
assert(!wrong.calls.some(c => c[0] === 'paste'));

const ed = editor();
const appCalls = [];
let observation = 0;
const app = {
  async getAXState() {
    observation++;
    return observation === 1 ? '1 window 열기\n2 edit 파일 이름:\n3 button 열기(O)' : '1 window 열기\n2 edit 파일 이름:\n8 button 링크 입력 열기\n9 button 열기(O)';
  },
  async click(i) { appCalls.push(['click', i]); },
  async pressKey(k) { appCalls.push(['key', k]); },
  async typeText(s) { appCalls.push(['type', s]); }
};
await createNaverOps(ed, app, { platform: 'windows' }).fillPicker('C:\\사진 폴더\\대표사진.png');
assert.deepEqual(appCalls.map(c => c[1]), [2, 'ctrl+a', 'C:\\사진 폴더\\대표사진.png', 9]);
assert(ed.calls.some(c => c[0] === 'loaded' && c[1] === '대표사진.png'));
const unknown = { getAXState: async () => '1 window Chrome' };
await assert.rejects(createNaverOps(editor(), unknown, { platform: 'windows' }).fillPicker('C:\\x.png'), /미확인/);
let chosen;
await createNaverOps(editor(), {}, { platform: 'windows', chooseFile: async value => { chosen = value.name; } }).fillPicker('C:\\사진\\대표사진.png');
assert.equal(chosen, '대표사진.png');
console.log('PASS: OS copy keys, path separators, whole-text guard, fresh Windows dialog indices, unknown-dialog stop, picker override');
