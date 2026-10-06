# Capturing real screenshots to files (the reliable recipe)

The generator embeds images from a `screenshots/` folder. To fill that folder with **real,
crisp** captures of the running app, drive a browser and use `html2canvas` to POST each screen
to the local `shot_server.py`. Browser screenshot tools show you an image but usually can't
**save bytes to disk** — this receiver does.

## 1. Start the receiver
```bash
python3 scripts/shot_server.py docs/screenshots 8899   # dir + port
```

## 2. In the app page (a browser you control), install a capture helper
Run this once per full page load (it resets on navigation). It loads html2canvas from the local
receiver, which serves a pinned, hash-checked copy — nothing is pulled from a CDN at capture time.
If the page's CSP blocks `127.0.0.1` scripts, fall back to the browser tool's own screenshots.
```js
(async()=>{
  if(!window.html2canvas){await new Promise((ok,err)=>{const s=document.createElement('script');
    s.src='http://127.0.0.1:8899/html2canvas.js';s.onload=ok;s.onerror=err;document.head.appendChild(s);});}
  window.__shot = async (name)=>{
    const c = await html2canvas(document.body,{scale:1,useCORS:true,backgroundColor:'#ffffff',
      x:scrollX,y:scrollY,width:innerWidth,height:innerHeight,
      windowWidth:document.documentElement.scrollWidth,windowHeight:document.documentElement.scrollHeight});
    const b = await new Promise(res=>c.toBlob(res,'image/jpeg',0.72));
    await fetch('http://127.0.0.1:8899/save?name='+encodeURIComponent(name),{method:'POST',body:b});
    return name;
  };
})()
```
Then, on each screen: `await window.__shot('01-login')`, `await window.__shot('02-dashboard')`, …

## Gotchas learned the hard way

- **Full-page vs viewport.** The snippet above captures the viewport. For a whole scrolling page,
  call `html2canvas(document.body,{backgroundColor})` with no x/y/width/height. Viewport shots are
  cleaner for docs; full-page for long forms/reports.

- **Modals/dialogs won't render when you capture `document.body`** if there is heavy content
  behind them — html2canvas paints the dimmed backdrop and drops the dialog. **Fix: capture the
  modal element directly at scale 2:**
  ```js
  const panel = document.querySelector('.your-modal, .swal2-popup, [role=dialog]');
  const c = await html2canvas(panel,{scale:2,backgroundColor:'#ffffff'});
  ```
  The grey border you get is the backdrop; crop it or leave it.

- **SweetAlert2 popups** (`.swal2-popup`) often render blank in html2canvas. Don't screenshot them
  — put that content (e.g. a title/description you typed) into the guide as a **text card / `spec`**
  instead. It reads better anyway.

- **`<input type=date>` can hang html2canvas.** Before capturing, swap them to text and restore
  after: `d.setAttribute('type','text'); …capture…; d.setAttribute('type','date')`. Set values with
  the native setter + dispatch events so a React form keeps them:
  ```js
  const set=Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set;
  set.call(el,'2026-12-31'); el.dispatchEvent(new Event('input',{bubbles:true})); el.dispatchEvent(new Event('change',{bubbles:true}));
  ```

- **`document.hidden === true` breaks capture.** If the browser window/tab is backgrounded, its
  `requestAnimationFrame` is paused and html2canvas hangs (the call may "time out" even though the
  POST later lands). Keep the tab foregrounded; and after any "timeout", **check the file on disk —
  it often saved anyway.**

- **Some cards render as empty boxes.** A few components just won't paint in html2canvas. Capture the
  useful region and crop the empty part (PIL: `Image.open(p).crop((x0,y0,x1,y1)).save(p)`), or grab
  a smaller element. Don't ship broken empty boxes.

- **Charts** (SVG/canvas dashboards) usually *do* render — capture the full page to include them.

- **Name files to match the guide spec** (`01-login`, `02-dashboard`, …). Sort order doesn't matter
  to the generator; the spec's `imgs` list references basenames.

## The ones that cost hours

- **A `<video>` element crashes html2canvas** — it silently renders the whole region blank. Skip it:
  `html2canvas(el,{ignoreElements:e=>e.tagName==='VIDEO'})`, and composite a real frame in
  separately with `ffmpeg -ss 2 -i file.mp4 -frames:v 1 out.jpg`.

- **Canvas/Recharts charts often render blank** even though the metric *cards* around them render
  fine. Prefer the numbers, crop the blank chart, or accept its absence — never ship a big empty box.

- **SweetAlert popups won't paint**, even element-targeted. If you need the popup *as an image*:
  trigger it live, read its exact text and buttons, then build a **faithful HTML replica** (a plain
  styled `<div>` with the same icon, wording and button colours, positioned off-screen) and
  html2canvas *that*. The content is real — verified live — you're only re-rendering it in a
  capturable form. Otherwise a `spec`/text card is fine and often reads better.

- **A UI state that only exists from saved server state? Seed it via the API, don't fight the UI.**
  For example a "resume where you left off?" prompt that needs prior progress: create the progress
  row with the project's own seed/fixture script (or ask the user to), then reload so the component
  mounts and reads it. Far more reliable than clicking through to build the state, and it uses the
  app's real data path.

- **Signed-in screens: let the user sign in.** Never read, mint or copy tokens, cookies or stored
  sessions yourself, and never type real credentials. Ask the user to sign in (in the browser you
  are driving) with a test account from the project's seed data, then capture. If the app bounces
  to `/login` mid-run, pause and ask them to sign in again.

- **Overlay sidebars fly out over content at narrow widths.** Capture dashboards at ≥1024px so the
  menu is a fixed column beside the content rather than covering it.

- **Recompress before building.** These docs embed every image as base64. `sips --resampleWidth 1440
  -s formatOptions 72` (or ImageMagick) keeps a rich guide at ~5–8 MB instead of 16.
