// Misli z razgledom — the few bits that need a script:
// menu, live dateline, contact form, biography pop-up.
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

  // Contact form. With Web3Forms it sends right here on the page; without it, it opens the email program.
  var S = en ? { sending: 'Sending …', sent: 'Thank you, your message has been sent.', slow: 'Please take a moment and try again.',
                 failed: 'The message could not be sent. Please try again or write to ' }
             : { sending: 'Pošiljam …', sent: 'Hvala, sporočilo je poslano.', slow: 'Počakajte trenutek in poskusite znova.',
                 failed: 'Sporočila ni bilo mogoče poslati. Poskusite znova ali pišite na ' };
  var odprto = Date.now();
  document.querySelectorAll('.contact-form').forEach(function (form) {
    var stanje = form.querySelector('[data-stanje]');
    form.addEventListener('submit', function (ev) {
      ev.preventDefault();
      var f = form.elements;
      if (form.hasAttribute('data-kontakt')) {
        var body = f.message.value + '\n\n— ' + f.name.value + ' (' + f.email.value + ')';
        window.location.href = 'mailto:' + form.getAttribute('data-kontakt') +
          '?subject=' + encodeURIComponent(form.getAttribute('data-zadeva')) + '&body=' + encodeURIComponent(body);
        return;
      }
      if (f.botcheck && f.botcheck.checked) return;              // a robot filled the hidden field
      if (Date.now() - odprto < 4000) { stanje.textContent = S.slow; return; }  // sent faster than a person can type
      var gumb = form.querySelector('button[type=submit]');
      gumb.disabled = true;
      stanje.textContent = S.sending;
      fetch(form.action, { method: 'POST', headers: { Accept: 'application/json' }, body: new FormData(form) })
        .then(function (r) { return r.json(); })
        .then(function (d) {
          if (!d.success) throw new Error(d.message);
          form.reset();
          stanje.textContent = S.sent;
        })
        .catch(function () { stanje.textContent = S.failed + form.getAttribute('data-web3forms') + '.'; })
        .then(function () { gumb.disabled = false; });
    });
  });

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
