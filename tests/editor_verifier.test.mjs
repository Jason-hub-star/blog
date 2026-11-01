// 실사용 고객 기록이 없는 공개 검증 계약. 실제 브라우저 검증은 별도다.
import assert from 'node:assert/strict';
import {verifyGeumgangEditor} from '../automation/verify_editor.mjs';
import {createNaverOps, fileName} from '../automation/browser_helpers.mjs';

const post = {title:'가상 제목',body_length_min:1500,body_length_max:1800,
  blocks:[{type:'quote',text:'가상 입력의 한 줄 요약입니다.',size:19},{type:'p',text:'가상 본문 '.repeat(230)+'마지막 문장입니다.'}],
  photos:['후사진.jpg'],banners:[{suffix:'15-18-10.png'},{suffix:'15-18-18.png'},{suffix:'15-17-53.png'}],tags:['가상태그'],
  review_captures:[{name:'후기.jpg',after_text:'마지막 문장입니다.'}]};
post.blocks[1].text='가상 본문 '.repeat(265)+'마지막 문장입니다.';
post.media_groups=[['움직이는썸네일.gif'],['후사진.jpg'],['후기.jpg'],['대표사진.png'],...post.banners.map(b=>['KakaoTalk_Photo_2026-11-01-'+b.suffix])];
const observed={title:post.title,body:post.blocks.map((b,i)=>({text:b.text,fonts:[i?'15px':'19px'],align:'center'})),quotes:[{text:post.blocks[0].text,defaultStyle:true,lines:1,italic:true}],firstContentKind:'quote',card:'초슬림 3연동 금강이지스',
  images:post.media_groups.flat().map(n=>({src:'https://example.invalid/'+encodeURIComponent(n),representative:n==='대표사진.png',linked:true,previousText:post.blocks[1].text})),
  mediaGroups:post.media_groups.map(g=>g.map(n=>'https://example.invalid/'+encodeURIComponent(n))),tags:['#가상태그'],noMarkers:true,noTemplateExamples:true};
const verify=o=>verifyGeumgangEditor({playwright:{frameLocator:()=>({getByRole:()=>({evaluate:async()=>o})})}},post);
assert.equal((await verify(structuredClone(observed))).result,'PASS');
for (const [key,mutate] of [
  ['nativeTopHook',o=>o.quotes[0].lines=2],
  ['imageOrderAndCount',o=>o.images.reverse()],
  ['photoGrouping',o=>o.mediaGroups[1].push('가짜.jpg')],
  ['representativePNG',o=>o.images[3].representative=false],
  ['reviewCapturePlacement',o=>o.images[2].previousText='다른 설명'],
  ['linkedReviewCaptures',o=>o.images[2].linked=false],
  ['body15Heading30',o=>o.body[1].fonts=['16px']],
]) {const bad=structuredClone(observed);mutate(bad);assert.equal((await verify(bad)).tests[key],false,key);}
assert.equal(fileName('C:\\한글 폴더\\사진.jpg'),'사진.jpg');
assert.throws(()=>createNaverOps({}, {}, {platform:'unknown'}));
const calls=[];
const ops=createNaverOps({playwright:{frameLocator:()=>({getByRole:()=>({waitFor:async()=>{}})})}},
  {getAXState:async()=>calls.length?'2 button Open':'0 dialog Open\n1 text field File name',click:async i=>calls.push(i),pressKey:async k=>calls.push(k),typeText:async t=>calls.push(t)}, {platform:'windows'});
await ops.fillPicker('C:\\한글 폴더\\사진.jpg');
assert.deepEqual(calls,[1,'ctrl+a','C:\\한글 폴더\\사진.jpg',2]);
console.log('PASS: 공개 가상 DOM 17조건·오류7종·Windows 파일창 모의 계약');
