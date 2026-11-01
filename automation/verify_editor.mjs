// cua_repl의 문서화된 DOM 읽기만 사용한다. 내부 SmartEditor 모델은 읽지 않는다.
export async function verifyGeumgangEditor(ed, post) {
  const observed = await ed.playwright.frameLocator('#mainFrame').getByRole('article').evaluate(e => {
    const comps = Array.from(e.querySelectorAll('.se-component'));
    const media = comps.filter(c => c.classList.contains('se-image') || c.classList.contains('se-imageStrip'));
    const images = media.flatMap(c=>Array.from(c.querySelectorAll('.se-module-image')).map(unit=>({
      id:unit.id,componentId:c.id,src:unit.querySelector('img')?.src || '',
      previousText:comps.slice(0,comps.indexOf(c)).filter(p=>p.innerText.replace(/[\u200b\ufeff\s]/g,'')).at(-1)?.innerText || '',
      representative:!!unit.querySelector('.se-set-rep-image-button.se-is-selected'),
      linked:!!unit.querySelector('.se-image-link-icon') || (c.classList.contains('se-image') && !!c.querySelector('.se-image-link-icon'))
    })));
    const body = [];
    const content = comps.filter(c => c.classList.contains('se-text') || c.classList.contains('se-quotation'));
    outer: for (const c of content) {
      const kind = c.classList.contains('se-quotation') ? 'quote' : 'text';
      for (const p of c.querySelectorAll(kind==='quote'?'.se-quote p':'p')) {
        const text = p.innerText.replace(/[\u200b\ufeff]/g, '').trim();
        if (text === '금강이지스 공식 스토어') break outer;
        if (!text) continue;
        const spans = Array.from(p.querySelectorAll('span.__se-node')).filter(s => s.innerText.trim());
        const fonts = spans.map(s => getComputedStyle(s).fontSize);
        for (const line of text.split('\n').filter(Boolean)) body.push({text:line.trim(),fonts,align:getComputedStyle(p).textAlign,kind});
      }
    }
    const tail = comps.slice(comps.indexOf(media.at(-1))+1);
    return {
      title: e.querySelector('.se-documentTitle').innerText,
      body,
      quotes: comps.filter(c=>c.classList.contains('se-quotation')).map(c=>({
        text:Array.from(c.querySelectorAll('.se-quote span.__se-node')).map(s=>s.innerText).join(''),
        defaultStyle:c.classList.contains('se-l-default'),
        lines:Array.from(c.querySelectorAll('.se-quote p')).filter(p=>Array.from(p.querySelectorAll('span.__se-node')).some(s=>s.innerText.trim())).length,
        italic:Array.from(c.querySelectorAll('.se-quote span.__se-node')).filter(s=>s.innerText.trim()).every(s=>getComputedStyle(s).fontStyle==='italic'||!!s.querySelector('i'))
      })),
      firstContentKind:content.find(c=>c.innerText.replace(/[\u200b\ufeff\s]/g,'').length)?.classList.contains('se-quotation')?'quote':'text',
      card: e.querySelector('.se-oglink')?.innerText || '',
      images,
      mediaGroups: media.map(c=>Array.from(c.querySelectorAll('.se-module-image img')).map(i=>i.src)),
      tags: tail.map(c => c.innerText).join(' ').match(/#[^\s#]+/gu) || [],
      noMarkers: !e.innerText.includes('〔'),
      noTemplateExamples: !['제목 한번 더 반복','금정구 금강로 225','2~3페이지 진입'].some(t=>e.innerText.includes(t))
    };
  });
  const norm = s => s.replace(/\s/g,' ');
  const expected = post.blocks.filter(b => b.text).flatMap(b => b.text.split('\n').filter(Boolean).map(text => ({text,size:b.type==='quote'?b.size:b.type==='h'?30:15})));
  const captures = post.review_captures || [];
  const groups = post.media_groups || [['움직이는썸네일.gif'],...(post.photo_groups || post.photos.map(p=>[p])),['대표사진.png'],...captures.map(c=>[c.name]),...post.banners.map(b=>['KakaoTalk_Photo_2026-11-01-'+b.suffix])];
  const names = groups.flat();
  const imageFor = name => observed.images.find(im=>decodeURIComponent(im.src).includes(name));
  const bodyText = observed.body.map(b=>b.text).join('');
  const expectedLength = expected.map(b=>b.text).join('').length;
  const tests = {
    title: norm(observed.title) === norm(post.title),
    exactBody: JSON.stringify(observed.body.map(b=>norm(b.text))) === JSON.stringify(expected.map(b=>norm(b.text))),
    nativeTopHook:post.blocks[0].type==='quote' && !post.blocks[0].text.includes('\n') && observed.firstContentKind==='quote' && observed.quotes.length===1 && observed.quotes[0].lines===1 && norm(observed.quotes[0].text)===norm(post.blocks[0].text) && observed.quotes[0].defaultStyle && observed.quotes[0].italic,
    bodyLength: bodyText.length===expectedLength && bodyText.length>=post.body_length_min && bodyText.length<=post.body_length_max,
    removedPhrasesAbsent: (post.removed_body_phrases || []).every(p=>!bodyText.includes(p)),
    body15Heading30: observed.body.length===expected.length && observed.body.every((b,i)=>b.fonts.length>0 && b.fonts.every(f=>f===expected[i].size+'px')),
    centered: observed.body.every(b=>b.align==='center'),
    imageOrderAndCount: observed.images.length===names.length && observed.images.every((im,i)=>decodeURIComponent(im.src).includes(names[i])),
    photoGrouping:observed.mediaGroups.length===groups.length && observed.mediaGroups.every((g,i)=>g.length===groups[i].length && g.every((src,j)=>decodeURIComponent(src).includes(groups[i][j]))),
    representativePNG: observed.images.filter(im=>im.representative).length===1 && imageFor('대표사진.png')?.representative,
    linkedReviewCaptures: captures.every(c=>imageFor(c.name)?.linked),
    reviewCapturePlacement:captures.every(c=>!c.after_text || norm(imageFor(c.name)?.previousText || '').trim().endsWith(norm(c.after_text))),
    linkedBanners: observed.images.slice(-3).every(im=>im.linked),
    productCard: observed.card.includes(post.card_label || '초슬림 3연동') && observed.card.includes('금강이지스'),
    tagsBelowBanners: JSON.stringify(observed.tags)===JSON.stringify(post.tags.map(t=>'#'+t)),
    noMarkers: observed.noMarkers,
    noTemplateExamples: observed.noTemplateExamples
  };
  return {result:Object.values(tests).every(Boolean)?'PASS':'FAIL',bodyLength:bodyText.length,tests,observed};
}
