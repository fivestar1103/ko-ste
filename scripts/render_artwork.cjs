/* Native SVG artwork. Optional font CSS supplies IBM Plex at render time. */
const fs = require('node:fs');
const path = require('node:path');
const { pathToFileURL } = require('node:url');
const root = path.resolve(__dirname, '..');
const out = path.join(root, 'assets');
const palettes = {
  light: { paper: '#f2f4f7', card: '#ffffff', ink: '#10151c', second: '#55606d', muted: '#8b95a3', line: '#e3e8ee', accent: '#22485c', mark: '#a8741a' },
  dark: { paper: '#0d1116', card: '#161c24', ink: '#e8ecf1', second: '#97a2ae', muted: '#626d7a', line: '#242c36', accent: '#79bdd6', mark: '#d9a441' },
};
const escape = s => s.replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;');
function art(kind, theme, mobile = false) {
  const p = palettes[theme];
  const w = mobile ? 720 : 1600;
  const h = kind === 'cover' ? (mobile ? 930 : 660) : (mobile ? 1080 : 460);
  const elements = [];
  const text = (x,y,s,size=26,color=p.ink,weight=400,mono=false) => elements.push(`<text x="${x}" y="${y}" font-size="${size}" font-weight="${weight}" fill="${color}" font-family="${mono?'IBM Plex Mono':'IBM Plex Sans KR'}, sans-serif">${escape(s)}</text>`);
  const line = (x,y,x2,y2,color=p.line,width=2) => elements.push(`<path d="M${x} ${y}L${x2} ${y2}" stroke="${color}" stroke-width="${width}" fill="none"/>`);
  const rect = (x,y,rw,rh,color) => elements.push(`<rect x="${x}" y="${y}" width="${rw}" height="${rh}" fill="${color}"/>`);
  const label = (x,y,s) => text(x,y,s,18,p.second,400,true);
  if (kind === 'cover') {
    const m = mobile ? 48 : 72;
    label(m,60,'KOREAN / WRITING / AGENT SKILL');
    text(m,mobile?174:202,'ko-ste',mobile?104:136,p.ink,500,true);
    text(m,mobile?267:321,'뜻은 그대로.',mobile?59:68,p.ink,500);
    text(m,mobile?345:409,'읽기는 쉽게.',mobile?59:68,p.ink,500);
    text(m,mobile?415:482,'한국어를 다듬는 Agent Skill.',mobile?26:28,p.second);
    if (!mobile) {
      line(822,104,822,510);
      const x = 895;
      label(x,143,'01 / BEFORE');
      text(x,218,'배포 수행이',42,p.second);
      text(x,272,'필요합니다.',42,p.ink,500);
      line(x,310,1508,310);
      label(x,358,'02 / AFTER');
      text(x,427,'배포가 필요합니다.',42,p.ink,500);
      line(1023,445,1212,445,p.accent,4);
      text(x,488,'필요의 강도를 유지합니다.',24,p.second);
      line(m,552,1528,552);
      label(m,599,'CLAUDE CODE + CODEX');
      label(1057,599,'CONDITIONS / NUMBERS / MODALITY');
    } else {
      line(m,475,672,475);
      label(m,520,'01 / BEFORE');
      text(m,579,'배포 수행이 필요합니다.',34,p.second);
      line(m,622,672,622);
      label(m,670,'02 / AFTER');
      text(m,729,'배포가 필요합니다.',34,p.ink,500);
      line(151,747,337,747,p.accent,4);
      text(m,792,'필요의 강도를 유지합니다.',25,p.second);
      line(m,839,672,839);
      label(m,889,'CLAUDE CODE + CODEX');
    }
  } else {
    const m = mobile ? 48 : 72;
    label(m,56,'HOW KO-STE WORKS');
    const steps = [
      ['01','보존할 뜻을 확인','사실 · 조건 · 수치','확신 · 의무 · 코드'],
      ['02','필요한 부분만 수정','이미 잘 읽히는 문장은','그대로 둡니다.'],
      ['03','원문과 다시 대조','더한 뜻과 빠진 조건이','없는지 확인합니다.'],
    ];
    steps.forEach((s,i) => {
      const x = mobile ? 48 : 72 + i*516;
      const y = mobile ? 108 + i*274 : 116;
      line(x,y,x+(mobile?624:450),y);
      text(x,y+50,s[0],24,p.accent,500,true);
      text(x,y+103,s[1],mobile?39:36,p.ink,500);
      text(x,y+158,s[2],mobile?29:26,p.second);
      text(x,y+201,s[3],mobile?29:26,p.second);
      if (!mobile && i<2) {
        line(x+461,y+127,x+484,y+127,p.muted);
        elements.push(`<path d="M${x+478} ${y+121}l6 6-6 6" stroke="${p.muted}" fill="none" stroke-width="2"/>`);
      }
    });
    const foot = mobile ? 954 : 376;
    rect(m,foot,4,52,p.accent);
    text(m+22,foot+21,'해석이 갈리면 원문을 유지하고',mobile?26:24,p.second);
    text(m+22,foot+53,'확인할 내용을 덧붙입니다.',mobile?26:24,p.second);
  }
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}" viewBox="0 0 ${w} ${h}" role="img"><title>ko-ste — ${kind==='cover'?'뜻은 그대로. 읽기는 쉽게.':'의미 보존, 필요한 수정, 원문 대조'}</title><rect width="${w}" height="${h}" fill="${p.paper}"/>${elements.join('')}</svg>`;
}
async function main() {
  fs.mkdirSync(out,{recursive:true});
  const { chromium } = require(process.env.KO_STE_PLAYWRIGHT_MODULE || 'playwright');
  let css = '';
  if (process.argv[2]) {
    const cssPath = path.resolve(process.argv[2]);
    const fonts = process.argv[3] ? path.resolve(process.argv[3]) : path.join(path.dirname(cssPath),'fonts');
    css = fs.readFileSync(cssPath,'utf8').replaceAll(/url\(\/fonts\/([^)]*)\)/g,(_,name)=>`url("${pathToFileURL(path.join(fonts,name)).href}")`);
  }
  const browser = await chromium.launch({executablePath:process.env.KO_STE_CHROMIUM || chromium.executablePath(),headless:true,args:['--allow-file-access-from-files']});
  try {
    for (const kind of ['cover','workflow']) for (const theme of ['light','dark']) for (const mobile of [false,true]) {
      const name = `${kind}${theme==='dark'?'-dark':''}${mobile?'-mobile':''}`;
      const svg = art(kind,theme,mobile);
      fs.writeFileSync(path.join(out,`${name}.svg`),svg+'\n');
      const page = await browser.newPage({viewport:{width:mobile?720:1600,height:kind==='cover'?(mobile?930:660):(mobile?1080:460)},deviceScaleFactor:1});
      const htmlPath = path.join(root,'.local',`${name}.html`);
      fs.mkdirSync(path.dirname(htmlPath),{recursive:true});
      fs.writeFileSync(htmlPath,`<!doctype html><html><meta charset="utf-8"><style>${css}body{margin:0}svg{display:block}</style>${svg}</html>`);
      await page.goto(pathToFileURL(htmlPath).href);
      await page.evaluate(()=>document.fonts.ready);
      if (css && !(await page.evaluate(()=>document.fonts.check('500 42px "IBM Plex Sans KR"','뜻은 그대로')))) throw new Error('IBM Plex font failed to load');
      await page.screenshot({path:path.join(out,`${name}.png`)});
      await page.close();
      console.log(name);
    }
  } finally { await browser.close(); }
}
main().catch(error=>{console.error(error);process.exit(1)});
