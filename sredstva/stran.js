// Misli z razgledom — the few bits that need a script:
// phone menu, live dateline, next-issue countdown, biography pop-up, shelf filter.
(function () {
  // texts the script writes, per page language (<html lang>)
  var en = document.documentElement.lang === 'en';
  var T = en ? {
    locale: 'en-GB', open: 'Open menu', close: 'Close menu', today: 'Today', tomorrow: 'Tomorrow', soon: 'Soon',
    onItsWay: ', and the next one is on its way',
    days: function (n) { return 'In ' + n + ' days'; }
  } : {
    locale: 'sl-SI', open: 'Odpri meni', close: 'Zapri meni', today: 'Danes', tomorrow: 'Jutri', soon: 'Kmalu',
    onItsWay: ', naslednja je že na poti',
    days: function (n) { return 'Čez ' + n + ' ' + (n % 100 === 1 ? 'dan' : n % 100 === 2 ? 'dneva' : 'dni'); }
  };

  // Phone menu: the hamburger opens the sections over the whole screen
  var tgl = document.querySelector('.menu-toggle');
  if (tgl) {
    var root = document.documentElement;
    var meni = function (odprt) {
      root.classList.toggle('meni-odprt', odprt);
      tgl.setAttribute('aria-expanded', String(odprt));
      tgl.setAttribute('aria-label', odprt ? T.close : T.open);
    };
    tgl.addEventListener('click', function () { meni(!root.classList.contains('meni-odprt')); });
    document.addEventListener('keydown', function (ev) { if (ev.key === 'Escape') meni(false); });
    document.querySelectorAll('.site-nav a').forEach(function (a) { a.addEventListener('click', function () { meni(false); }); });
  }

  // Dateline: day and time in the page language, kept live like a printed clock
  var day = document.querySelector('[data-dan]');
  var time = document.querySelector('[data-ura]');
  if (day || time) {
    var fDay = new Intl.DateTimeFormat(T.locale, { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' });
    var fTime = new Intl.DateTimeFormat(T.locale, { hour: '2-digit', minute: '2-digit' });
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
    if (n > 1) when.textContent = T.days(n);
    else if (n === 1) when.textContent = T.tomorrow;
    else if (n === 0) when.textContent = T.today;
    else {
      when.textContent = T.soon;
      if (then) then.textContent = T.onItsWay;
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
        var on = f === '*' || it.getAttribute('data-skupina') === f;
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
