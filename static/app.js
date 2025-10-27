// static/app.js
(function () {
  const config = window.APP_CONFIG || { intervalMs: 3000, initialCount: 0 };

  let INTERVAL_MS = Number(config.intervalMs) || 3000;
  let count = Number(config.initialCount) || 0;

  // Shuffled order and position within it
  let order = [];
  let pos = 0;
  let timer = null;

  const img = document.getElementById('viewer');
  const idxEl = document.getElementById('idx');
  const countEl = document.getElementById('count');
  const statusEl = document.getElementById('status');
  const dateEl = document.getElementById('date');
  const filenameEl = document.getElementById('filename');
  const prevBtn = document.getElementById('prev');
  const nextBtn = document.getElementById('next');
  const pauseBtn = document.getElementById('pause');
  const playBtn = document.getElementById('play');
  const speedBtn = document.getElementById('speed');

  function setStatus(t) { statusEl.textContent = t; }
  function setCount(n) { countEl.textContent = n; }
  function setDateText(text) { dateEl.textContent = text || '—'; }
    function setFilenameText(text) { filenameEl.textContent = text || '—'; }

  function range(n) { return Array.from({ length: n }, (_, i) => i); }
  function shuffle(a) {
    for (let i = a.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [a[i], a[j]] = [a[j], a[i]];
    }
    return a;
  }

  function buildOrder(keepIndex /* number | null */) {
    const newOrder = shuffle(range(count));
    if (keepIndex == null) {
      order = newOrder;
      pos = 0;
      return;
    }
    order = newOrder;
    const found = order.indexOf(keepIndex);
    pos = found >= 0 ? found : 0;
  }

  async function refreshCount() {
    try {
      const r = await fetch('/count', { cache: 'no-store' });
      if (!r.ok) throw new Error('HTTP ' + r.status);
      const j = await r.json();
      if (typeof j.count === 'number' && j.count !== count) {
        const currentIndex = order.length ? order[pos] : null;
        count = j.count;
        setCount(count);
        buildOrder(currentIndex);
        showByPos(pos); // re-render current in new order
      }
    } catch (e) {
      console.error(e);
    }
  }

  function srcFor(index) {
    return `/file/${index}?t=${Date.now()}`;
  }

  async function fetchMeta(index) {
    try {
      const r = await fetch(`/meta/${index}`, { cache: 'no-store' });
      if (!r.ok) throw new Error('HTTP ' + r.status);
      return await r.json();
    } catch (e) {
      console.error(e);
      return null;
    }
  }

  function formatDate(iso) {
    // iso like "2024-05-01T14:02:33Z" -> localized string
    try {
      const d = new Date(iso);
      if (isNaN(d.getTime())) return null;
      return d.toLocaleString(undefined, {
        year: 'numeric', month: 'short', day: '2-digit'
        //,hour: '2-digit', minute: '2-digit', second: '2-digit'
      });
    } catch {
      return null;
    }
  }

  async function showByPos(p) {
    if (count === 0 || order.length === 0) { setStatus('no files'); return; }
    pos = ((p % order.length) + order.length) % order.length; // safe modulo
    const index = order[pos];

    // Update image and index immediately
    img.src = srcFor(index);
    idxEl.textContent = String(index);

    // Optimistically clear date and filename while waiting for image to load
    //setDateText('…');
    //setFilenameText('…')

    // Wait for the image to load before fetching meta data
    img.onload = async function() {
      // Fetch & display EXIF date
      const meta = await fetchMeta(index);
      if (meta && meta.date_taken) {
        const pretty = formatDate(meta.date_taken) || meta.date_taken;
        setDateText(pretty);
      } else {
        setDateText('—');
      }

      if (meta && meta.filename) {
        setFilenameText(meta.filename);
      } else {
        setFilenameText('—');
      }
    };

  }

  function next() { showByPos(pos + 1); }
  function prev() { showByPos(pos - 1); }

  function start() {
    stop();
    timer = setInterval(next, INTERVAL_MS);
    setStatus('playing');
    playBtn.style.display = 'none';
    pauseBtn.style.display = '';
  }

  function stop() {
    if (timer) { clearInterval(timer); timer = null; }
    setStatus('paused');
    playBtn.style.display = '';
    pauseBtn.style.display = 'none';
  }

  prevBtn.addEventListener('click', prev);
  nextBtn.addEventListener('click', next);
  pauseBtn.addEventListener('click', stop);
  playBtn.addEventListener('click', start);

  // Keyboard shortcuts
  document.addEventListener('keydown', (e) => {
    if (e.key === 'ArrowLeft') prev();
    else if (e.key === 'ArrowRight') next();
    else if (e.key === ' ') { e.preventDefault(); timer ? stop() : start(); }
  });

  // Initial boot: shuffle ONCE per page load, then show first and start
  setCount(count);
  setDateText('—');
  if (count > 0) buildOrder(null);
  refreshCount();
  showByPos(0);
  start();
  // Add event listeners for dropdown options
  document.querySelectorAll('.dropdown-content a').forEach(item => {
    item.addEventListener('click', event => {
      event.preventDefault();
      const newInterval = Number(event.target.getAttribute('data-interval'));
      if (newInterval) {
        INTERVAL_MS = newInterval;
        speedBtn.innerText = event.target.innerText
        if (timer) {
          start(); // Restart the timer with the new interval
        }
      }
    });
  });
})();
