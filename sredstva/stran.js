// Misli z razgledom — the few bits that need a script:
// live dateline, next-issue countdown, biography pop-up, shelf filter.
(function () {
  // Dateline: day and time in Slovenian, kept live like a printed clock
  var day = document.querySelector('[data-dan]');
  var time = document.querySelector('[data-ura]');
  if (day || time) {
    var fDay = new Intl.DateTimeFormat('sl-SI', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' });
    var fTime = new Intl.DateTimeFormat('sl-SI', { hour: '2-digit', minute: '2-digit' });
    var tick = function () {
      var now = new Date();
      if (day) day.textContent = day.getAttribute('data-dan') + ', ' + fDay.format(now);
      if (time) time.textContent = fTime.format(now);
    };
    tick();
    setInterval(tick, 15000);
  }

  // Next issue: the site changes about once a month, so the footer counts the days
  var next = document.querySelector('[data-naslednja]');
  if (next) {
    var d = next.getAttribute('data-naslednja').split('-');
    var now = new Date();
    var today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    var n = Math.round((new Date(+d[0], +d[1] - 1, +d[2]) - today) / 86400000);
    var when = next.querySelector('[data-kdaj]');
    var then = next.querySelector('[data-potem]');
    if (n > 1) when.textContent = 'Čez ' + n + ' ' + (n % 100 === 1 ? 'dan' : n % 100 === 2 ? 'dneva' : 'dni');
    else if (n === 1) when.textContent = 'Jutri';
    else if (n === 0) when.textContent = 'Danes';
    else {
      when.textContent = 'Kmalu';
      if (then) then.textContent = ', naslednja je že na poti';
    }
  }

  // "Več o meni" opens the biography as a pop-up (Esc, Zapri or a click outside closes it)
  document.querySelectorAll('[data-odpri]').forEach(function (link) {
    var dlg = document.getElementById(link.getAttribute('data-odpri'));
    if (!dlg || typeof dlg.showModal !== 'function') return;
    link.addEventListener('click', function (ev) { ev.preventDefault(); dlg.showModal(); });
    dlg.querySelector('[data-zapri]').addEventListener('click', function () { dlg.close(); });
    dlg.addEventListener('click', function (ev) { if (ev.target === dlg) dlg.close(); });
  });

  // Polica: category filter (without a script every item simply shows)
  var tags = document.querySelectorAll('[data-filter]');
  if (tags.length) {
    var items = document.querySelectorAll('[data-skupina]');
    var empty = document.querySelector('[data-prazno]');
    var pick = function (f) {
      var shown = 0;
      tags.forEach(function (t) { t.setAttribute('aria-pressed', String(t.getAttribute('data-filter') === f)); });
      items.forEach(function (it) {
        var on = f === 'Vse' || it.getAttribute('data-skupina') === f;
        it.hidden = !on;
        if (on) shown++;
      });
      if (empty) empty.hidden = shown > 0;
    };
    tags.forEach(function (t) {
      t.addEventListener('click', function () { pick(t.getAttribute('data-filter')); });
    });
    var bar = document.querySelector('[data-filtri]');
    if (bar) bar.hidden = false;
  }
})();
