// ponytail: 실제 저장 DOM을 이용한 회귀 검사. 네이버 UI 저장복원은 별도로 수행한다.
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
import {verifyGeumgangEditor} from './verify_editor.mjs';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const jobs = ['명지_오픈형3연동','원슬라이딩_구매후기','양개도어_구매후기'];
let checks = 0;
for (const job of jobs) {
  const dir = path.join(root, '현장작업', '2026-11-01_'+job);
  const post = JSON.parse(await readFile(path.join(dir,'post.json'),'utf8'));
  const proof = post.review_reference_year ? '후기별캡처_저장복원_검증.json' : '한줄요약_콜라주_저장복원_검증.json';
  const saved = JSON.parse(await readFile(path.join(dir,proof),'utf8'));
  const verify = observed => verifyGeumgangEditor({playwright:{frameLocator:()=>({getByRole:()=>({evaluate:async()=>observed})})}},post);
  assert.equal((await verify(structuredClone(saved.observed))).result,'PASS'); checks++;
  for (const [name,mutate,failedTest] of [
    ['위치',o=>o.firstContentKind='text','nativeTopHook'],
    ['내용',o=>o.quotes[0].text+='없는 발언','nativeTopHook'],
    ['스타일',o=>o.quotes[0].defaultStyle=false,'nativeTopHook'],
    ['중복',o=>o.quotes.push(o.quotes[0]),'nativeTopHook'],
    ['여러 줄',o=>o.quotes[0].lines=2,'nativeTopHook'],
    ['크기',o=>o.body[0].fonts=['15px'],'body15Heading30'],
    ['분량 누락',o=>o.body.shift(),'bodyLength']
  ]) {
    const observed = structuredClone(saved.observed); mutate(observed);
    const result = await verify(observed);
    assert.equal(result.result,'FAIL',job+': '+name);
    assert.equal(result.tests[failedTest],false,job+': '+name); checks++;
  }
  if (post.photo_groups) {
    for (const [name,mutate] of [
      ['콜라주 해제',o=>o.mediaGroups.splice(1,1,...o.mediaGroups[1].map(s=>[s]))],
      ['좌우 반전',o=>o.mediaGroups[1].reverse()]
    ]) {
      const observed=structuredClone(saved.observed); mutate(observed);
      const result=await verify(observed);
      assert.equal(result.tests.photoGrouping,false,name); checks++;
    }
  }
  if (post.review_reference_year) {
    const name=post.review_captures[0].name;
    const observed=structuredClone(saved.observed);
    const image=observed.images.find(i=>decodeURIComponent(i.src).includes(name));
    image.previousText+='다른 문단';
    assert.equal((await verify(observed)).tests.reviewCapturePlacement,false,'후기 문단/카드 불일치'); checks++;
    const unlinked=structuredClone(saved.observed);
    unlinked.images.find(i=>decodeURIComponent(i.src).includes(name)).linked=false;
    assert.equal((await verify(unlinked)).tests.linkedReviewCaptures,false,'후기 원문 링크 소실'); checks++;
  }
}
console.log(`PASS: 실제 저장 DOM 3편 정상/오류 변형 ${checks}검사`);
