// cua_repl 전용. 먼저 현재 Umji 탭과 Chrome 앱을 연결하고 문서화된 API 핸들을 전달한다.
// 인증정보/쿠키/SmartEditor 내부 모델을 읽거나 바꾸지 않는다.
export function fileName(path) {
  return path.split(/[\\/]/).pop();
}

export function createNaverOps(ed, chromeApp, { platform, chooseFile } = {}) {
  if (!['mac', 'windows'].includes(platform)) throw Error('platform을 mac 또는 windows로 지정하세요');
  const frame = () => ed.playwright.frameLocator('#mainFrame');
  return {
    async replaceTextGroup(index, html) {
      const before = await frame().getByRole('article').evaluate(e => ({
        groups: Array.from(e.querySelectorAll('.se-component.se-text')).filter(c => c.innerText.trim()).map(c => ({
          id: c.id, text: Array.from(c.querySelectorAll('p')).map(p => p.innerText).join('')
        })),
        images: Array.from(e.querySelectorAll('.se-component.se-image')).map(c => c.id)
      }));
      const group = before.groups[index];
      if (!group) throw Error('교체할 본문 구간 없음');
      const paragraphs = frame().locator('#' + group.id + ' p').filter({ hasText: /\S/ });
      await paragraphs.first().click();
      await ed.pressKey(null, 'Home');
      await paragraphs.last().click({ modifiers: ['Shift'] });
      await ed.pressKey(null, 'shift+End');
      await ed.getAXState({ emit: false });
      await ed.pressKey(null, platform === 'windows' ? 'ctrl+c' : 'super+c');
      const selected = await ed.clipboard.readText();
      if (selected.replace(/\s/g, '') !== group.text.replace(/\s/g, '')) {
        throw Error('본문 구간 전체 선택 미확인');
      }
      await ed.paste(null, html, { format: 'html' });
      await ed.getAXState({ emit: false });
      const afterImages = await frame().locator('.se-component.se-image').evaluateAll(es => es.map(e => e.id));
      if (JSON.stringify(before.images) !== JSON.stringify(afterImages)) throw Error('본문 교체 중 사진 배치 변경 감지');
    },
    async replaceImage(index, path) {
      await frame().locator('.se-component.se-image').nth(index).locator('img').click();
      await frame().getByRole('button', { name: '사진 교체', exact: true }).click();
      await this.fillPicker(path);
    },
    async uploadAtMarker(marker, path) {
      await frame().getByText(marker, { exact: true }).click();
      await ed.pressKey(null, 'Home');
      await ed.pressKey(null, 'shift+End');
      const selected = await ed.getAXState({ emit: false });
      if (!selected.includes(marker + ' 선택됨')) throw Error('사진 자리 선택 미확인');
      await frame().getByRole('button', { name: '사진 추가', exact: true }).click();
      await this.fillPicker(path);
    },
    async fillPicker(path) {
      const name = fileName(path);
      if (chooseFile) {
        await chooseFile({ path, name, platform, ed, app: chromeApp });
        await frame().getByRole('img', { name, exact: true }).waitFor({ state: 'visible', timeoutMs: 15000 });
        return;
      }
      if (platform === 'windows') {
        // ponytail: 한국어/영어 파일창의 명시적 관찰만 지원. 다른 AX 형식은 chooseFile로 확장한다.
        let state = await chromeApp.getAXState({ disableDiffing: true, emit: false });
        const dialog = /(?:dialog|window|대화\s?상자|창).*?(?:Open|열기)/i.test(state);
        const field = state.split('\n').find(line => /(?:edit|text field|textbox|텍스트 필드)/i.test(line) && /(?:File name|파일 이름)/i.test(line));
        if (!dialog || !field) throw Error('Windows 열기 창/파일 이름 칸 미확인. 최신 UI로 확인하거나 chooseFile을 제공하세요');
        const index = field.trim().match(/^\d+/);
        if (!index) throw Error('Windows 파일 이름 칸의 접근성 번호 없음');
        await chromeApp.click(Number(index[0]));
        await chromeApp.pressKey('ctrl+a');
        await chromeApp.typeText(path);
        state = await chromeApp.getAXState({ disableDiffing: true, emit: false });
        const button = state.split('\n').find(line => /(?:\bbutton\b|버튼)\s+["']?(?:Open|열기)(?:["'\s,(]|$)/i.test(line));
        const openIndex = button?.trim().match(/^\d+/);
        if (!openIndex) throw Error('Windows 열기 버튼 미확인');
        await chromeApp.click(Number(openIndex[0]));
        await frame().getByRole('img', { name, exact: true }).waitFor({ state: 'visible', timeoutMs: 15000 });
        return;
      }
      let state = await chromeApp.getAXState({ disableDiffing: true, emit: false });
      if (!state.includes('open-panel')) {
        // ponytail: 고정 sleep 대신 창 전환 중 한 번 더 관찰. 계속 없으면 중단한다.
        await chromeApp.getScreenshot({ emit: false });
        state = await chromeApp.getAXState({ disableDiffing: true, emit: false });
      }
      if (!state.includes('open-panel')) throw Error('파일 선택창 준비 실패');
      const item = state.split('\n').find(line => line.includes('이미지 ') && line.includes('ID: ' + name));
      if (item) {
        await chromeApp.click(Number(item.trim().match(/^\d+/)[0]));
      } else {
        await chromeApp.pressKey('slash');
        state = await chromeApp.getAXState({ disableDiffing: true, emit: false });
        const field = state.match(/(\d+) 텍스트 필드 \(settable\).*ID: PathTextField/);
        if (!field) throw Error('경로 입력칸 없음');
        await chromeApp.setValue(Number(field[1]), path);
        await chromeApp.pressKey('Return');
      }
      state = await chromeApp.getAXState({ disableDiffing: true, emit: false });
      const open = state.match(/(\d+) 버튼 열기, ID: OKButton/);
      if (!open) throw Error('열기 버튼 비활성 또는 없음');
      await chromeApp.click(Number(open[1]));
      await frame().getByRole('img', { name, exact: true }).waitFor({ state: 'visible', timeoutMs: 15000 });
    }
  };
}

export async function verifyEditor(ed, config) {
  const observed = await ed.playwright.frameLocator('#mainFrame').getByRole('article').evaluate(e => {
    const components = Array.from(e.querySelectorAll('.se-component'));
    const images = Array.from(e.querySelectorAll('.se-component.se-image'));
    const bannerIndex = components.indexOf(images.at(-1));
    const textComponents = components.slice(0, bannerIndex).filter(c => c.classList.contains('se-text'));
    const paragraphs = textComponents.flatMap(c => Array.from(c.querySelectorAll('p')));
    const spans = textComponents.flatMap(c => Array.from(c.querySelectorAll('span.__se-node'))).filter(s => s.innerText.trim());
    const tail = components.slice(bannerIndex+1).filter(c => c.classList.contains('se-text'));
    const tailSpans = tail.flatMap(c => Array.from(c.querySelectorAll('span.__se-node'))).filter(s => s.innerText.trim());
    const lastParagraphs = textComponents.at(-1) ? Array.from(textComponents.at(-1).querySelectorAll('p')) : [];
    const greeting = paragraphs.find(p => p.innerText.trim() === '안녕하세요.');
    const trailingBlankCount = lastParagraphs.length - 1 - lastParagraphs.map(p => !!p.innerText.trim()).lastIndexOf(true);
    return {
      title: e.querySelector('.se-documentTitle').innerText,
      lines: paragraphs.map(p => p.innerText.trim()).filter(Boolean),
      headingLines: textComponents.flatMap(c => Array.from(c.querySelectorAll('.se-fs30 b'))).map(b => b.innerText).filter(s => s.trim()),
      bodyBold: textComponents.flatMap(c => Array.from(c.querySelectorAll('.se-fs16 b'))).map(b => b.innerText).filter(s => s.trim()),
      fontClasses: Array.from(new Set(spans.map(s => Array.from(s.classList).find(c => /^se-fs/.test(c))))),
      paragraphFonts: paragraphs.filter(p => p.innerText.trim()).map(p => Array.from(p.querySelectorAll('span.__se-node')).filter(s => s.innerText.trim()).map(s => Array.from(s.classList).find(c => /^se-fs/.test(c)))),
      sentenceGaps: paragraphs.filter(p => /[.!?]$/.test(p.innerText.trim())).map(p => ({
        text: p.innerText.trim(), blankAfter: !!p.nextElementSibling && !p.nextElementSibling.innerText.trim(),
        nextText: p.nextElementSibling?.innerText.trim() || ''
      })),
      tags: (tail.map(c => c.innerText).join(' ').match(/#[^\s#]+/gu) || []),
      tagsFont16: tailSpans.every(s => s.classList.contains('se-fs16') && !s.querySelector('b')),
      greetingNextText: greeting?.nextElementSibling?.innerText.trim() || '',
      trailingBlankCount,
      noBlankBeforeThumbnail: !components.slice(1, components.indexOf(images[0])).some(c => c.classList.contains('se-text')),
      titleThumbnailGap: images[0]?.getBoundingClientRect().top - e.querySelector('.se-documentTitle').getBoundingClientRect().bottom,
      images: images.map(c => ({ id: c.id, src: c.querySelector('img')?.src || '',
        representative: !!c.querySelector('.se-set-rep-image-button.se-is-selected'),
        linkIcon: !!c.querySelector('.se-image-link-icon') })),
      noPlaceholders: !e.innerText.includes('〔')
    };
  });
  const normalize = value => value.replace(/\s/g, ' ');
  const expected = config.blocks.filter(b => b.type !== 'image').flatMap(b => b.text.replaceAll('**', '').split('\n'));
  const expectedFonts = config.blocks.filter(b => b.type !== 'image').flatMap(b => b.text.split('\n').map(() => b.type === 'heading' ? 'se-fs30' : 'se-fs16'));
  const headings = config.blocks.filter(b => b.type === 'heading').flatMap(b => b.text.split('\n'));
  const bold = config.blocks.filter(b => b.type === 'text').flatMap(b => Array.from(b.text.matchAll(/\*\*(.*?)\*\*/gs)).flatMap(m => m[1].split('\n')));
  const compactTransitions = new Map(config.blocks.flatMap((b, i) => b.gap_after === false && config.blocks[i+1]?.text ? [[b.text.replaceAll('**', '').split('\n').at(-1), config.blocks[i+1].text.replaceAll('**', '').split('\n')[0]]] : []));
  const expectedTags = (config.tags || []).map(t => '#' + t);
  const tests = {
    title: normalize(observed.title) === normalize(config.title),
    exactTextOrder: JSON.stringify(observed.lines) === JSON.stringify(expected),
    exactBodyCharacterCount: observed.lines.join('').length === config.body_target_chars,
    headings30Bold: JSON.stringify(observed.headingLines) === JSON.stringify(headings),
    onlyChosenBodyWordsBold: JSON.stringify(observed.bodyBold) === JSON.stringify(bold),
    body16: observed.paragraphFonts.length === expectedFonts.length && observed.paragraphFonts.every((fonts, i) => fonts.length > 0 && fonts.every(c => c === expectedFonts[i])),
    sentenceBlankLines: observed.sentenceGaps.length > 0 && observed.sentenceGaps.every(p => p.blankAfter || compactTransitions.get(p.text) === p.nextText),
    imageCount: observed.images.length === config.blocks.filter(b => b.type === 'image').length + 1,
    representativePNG: observed.images.filter(i => i.representative).length === 1 && observed.images[0].representative && decodeURIComponent(observed.images[0].src).includes('대표사진.png'),
    gifPresent: observed.images.some(i => /\.gif/i.test(i.src)),
    lastBannerLinked: observed.images.at(-1).linkIcon,
    noPlaceholders: observed.noPlaceholders,
    tagsBelowBanner: JSON.stringify(observed.tags) === JSON.stringify(expectedTags) && (!expectedTags.length || expectedTags.length === 15) && observed.tagsFont16,
    compactGreeting: !compactTransitions.has('안녕하세요.') || observed.greetingNextText === compactTransitions.get('안녕하세요.'),
    compactBanner: observed.trailingBlankCount <= 1,
    compactThumbnail: observed.noBlankBeforeThumbnail
  };
  const failed = Object.entries(tests).filter(([, passed]) => !passed).map(([name]) => name);
  if (failed.length) throw Error('편집기 검사 실패: ' + failed.join(', '));
  return { result: 'PASS', tests, observed };
}
