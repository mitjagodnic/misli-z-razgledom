#!/usr/bin/env python3
"""Build the Café Goričan site, in Slovenian (site root) and English (/en/).

Reads vsebina/ (texts and pictures) and the design system tokens,
writes the finished static site into stran/.  Run:  python3 build.py

Everything Uroš publishes is a post of Walking the Myth (vsebina/walking-the-myth/*.md):
an essay, a note, or a recommendation (café, film, book …). The home page shows the newest
essay/note and the three newest recommendations from that list.

English texts live in vsebina/en/. Its JSON files hold only the translated fields, keyed by
item id, and are laid over the Slovenian ones. Its .md files mirror the Slovenian file names and
override their fields (pictures, links and dates stay shared); `slug:` gives the English address.
"""
import datetime
import hashlib
import html
import json
import math
import os
import re
import shutil
from pathlib import Path

KOREN = Path(__file__).resolve().parent
VSEBINA = KOREN / 'vsebina'
DS = KOREN / 'design-system'
IZHOD = KOREN / 'stran'
# Set when building the public demo (objavi.sh): the site's address path, e.g. /misli-z-razgledom/.
# The 404 page needs it, and the demo asks search engines not to index it.
OSNOVA = os.environ.get('OSNOVA', '')

JEZIKI = ('sl', 'en')
TOKENI = ['fonts', 'colors', 'typography', 'spacing', 'effects', 'base']
# section key → folder per language
SEKCIJE = {
    'knjige': {'sl': 'knjige/', 'en': 'books/'},
    'kontakt': {'sl': 'kontakt/', 'en': 'contact/'},
    'o-avtorju': {'sl': 'o-avtorju/', 'en': 'about/'},
}
NAV = ['knjige', 'kontakt', 'o-avtorju']
# The only labels (kickers) the site may show. Content always uses the Slovenian word;
# the English pages show its translation.
OZNAKE = ['Esej', 'Zapis', 'Priporočilo', 'Knjiga', 'Film', 'Glasba', 'Razstava', 'Teater', 'Kavarna',
          'Mesto', 'Arhitektura']
OZNAKE_EN = {'Esej': 'Essay', 'Zapis': 'Note', 'Priporočilo': 'Recommendation', 'Knjiga': 'Book',
             'Film': 'Film', 'Glasba': 'Music', 'Razstava': 'Exhibition', 'Teater': 'Theatre', 'Kavarna': 'Café',
             'Mesto': 'City', 'Arhitektura': 'Architecture'}
VRSTE = {'esej': 'Esej', 'zapis': 'Zapis', 'priporocilo': 'Priporočilo'}
KOLEDAR = {
    'sl': {'dnevi': ['ponedeljek', 'torek', 'sreda', 'četrtek', 'petek', 'sobota', 'nedelja'],
           'meseci': ['januar', 'februar', 'marec', 'april', 'maj', 'junij', 'julij', 'avgust',
                      'september', 'oktober', 'november', 'december']},
    'en': {'dnevi': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'],
           'meseci': ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August',
                      'September', 'October', 'November', 'December']},
}

# every fixed text on the pages, per language
UI = {
    'sl': {
        'nav': {'knjige': 'Knjige', 'kontakt': 'Kontakt', 'o-avtorju': 'O avtorju'},
        'na_vsebino': 'Na vsebino', 'rubrike': 'Rubrike', 'odpri_meni': 'Odpri meni',
        'jezik': 'English version', 'foto': 'Fotografija',
        'o_avtorju': 'O avtorju', 'vec_o_meni': 'Več o meni', 'zivljenjepis': 'Življenjepis', 'zapri': 'Zapri',
        'vec_o_knjigi': 'Več o knjigi', 'kupi': 'Kupi knjigo', 'nadaljuj': 'Nadaljuj branje',
        'vstopi': 'Vstopi v projekt', 'priporocilo': 'Priporočilo', 'preberi': 'Preberi', 'kmalu': 'Kmalu',
        'izide_kmalu': 'Izide kmalu.', 'nazaj_na': 'Nazaj na ',
        'na_polici': 'Na polici', 'na_polici_pod': 'Kar priporočam za branje, gledanje in posedanje.',
        'knjige_naslov': 'Knjige',
        'kontakt': 'Kontakt', 'kontakt_pod': 'Pišite mi.', 'ime': 'Ime', 'eposta': 'E-pošta',
        'sporocilo': 'Sporočilo', 'poslji': 'Pošlji',
        'zadeva': 'Sporočilo s spletne strani Café Goričan',
        'kontakt_opomba': 'Sporočilo se odpre v vašem e-poštnem programu in gre na {email}.',
        'branje': lambda m: '%d %s branja' % (m, 'minuta' if m == 1 else 'minute' if m in (2, 3, 4) else 'minut'),
    },
    'en': {
        'nav': {'knjige': 'Books', 'kontakt': 'Contact', 'o-avtorju': 'About'},
        'na_vsebino': 'Skip to content', 'rubrike': 'Sections', 'odpri_meni': 'Open menu',
        'jezik': 'Slovenska različica', 'foto': 'Photo',
        'o_avtorju': 'About the author', 'vec_o_meni': 'More about me', 'zivljenjepis': 'Biography',
        'zapri': 'Close', 'vec_o_knjigi': 'More about the book', 'kupi': 'Buy the book',
        'nadaljuj': 'Continue reading', 'vstopi': 'Enter the project', 'priporocilo': 'Find out more',
        'preberi': 'Read', 'kmalu': 'Soon', 'izide_kmalu': 'Coming soon.', 'nazaj_na': 'Back to ',
        'na_polici': 'On the shelf', 'na_polici_pod': 'What I recommend for reading, watching and lingering.',
        'knjige_naslov': 'Books',
        'kontakt': 'Contact', 'kontakt_pod': 'Write to me.', 'ime': 'Name', 'eposta': 'Email',
        'sporocilo': 'Message', 'poslji': 'Send',
        'zadeva': 'Message from the Café Goričan website',
        'kontakt_opomba': 'The message opens in your email program and goes to {email}.',
        'branje': lambda m: '%d min read' % m,
    },
}
IKONA = ("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16'%3E"
         "%3Ccircle cx='8' cy='8' r='6' fill='%238B2635'/%3E%3C/svg%3E")

JEZIK = 'sl'   # the language being built right now
V = {}         # all content, per language (filled in zgradi)

e = html.escape


def t(kljuc):
    return UI[JEZIK][kljuc]


def drugi_jezik():
    return 'en' if JEZIK == 'sl' else 'sl'


def pot(kljuc, jezik=None, slug=''):
    """A page's folder from the site root: '' for the Slovenian home, 'en/books/<slug>/' …
    kljuc is 'domov', a section key, or a project id (its page sits at <id>/)."""
    jezik = jezik or JEZIK
    predpona = '' if jezik == 'sl' else 'en/'
    if kljuc == 'domov':
        return predpona
    mapa = SEKCIJE[kljuc][jezik] if kljuc in SEKCIJE else kljuc + '/'
    return predpona + mapa + (slug + '/' if slug else '')


def oba(kljuc, slug_sl='', slug_en=''):
    """A page's folder in both languages, for the SL/EN switch."""
    return {'sl': pot(kljuc, 'sl', slug_sl), 'en': pot(kljuc, 'en', slug_en)}


# ---------- content ----------
# Every item is a JSON file, one per language: vsebina/<collection>/sl/<id>.json and …/en/<id>.json
# (posts, books), or vsebina/sl/<name>.json and vsebina/en/<name>.json (site texts, project, biography).
# The editor at /urednik/ writes exactly these files. English values replace Slovenian ones where filled in;
# pictures, links and dates are kept in the Slovenian file only.

def beri(pot_):
    return json.loads(pot_.read_text(encoding='utf-8')) if pot_.exists() else {}


def prekrij(osnova, prevod):
    """Lay the filled-in English values over the Slovenian ones (dicts by key)."""
    out = dict(osnova)
    for k, v in prevod.items():
        if isinstance(v, dict) and isinstance(osnova.get(k), dict):
            out[k] = prekrij(osnova[k], v)
        elif v not in (None, '', []):
            out[k] = v
    return out


def slika(vrednost):
    """The editor stores pictures as /slike/<file>; the site uses the file name."""
    return Path(vrednost).name if vrednost else ''


def slugify(besedilo):
    import unicodedata
    t_ = unicodedata.normalize('NFKD', besedilo).encode('ascii', 'ignore').decode().lower()
    return re.sub(r'[^a-z0-9]+', '-', t_).strip('-')


def vrstica(besedilo):
    """Escape a line of text and allow *italic*, **bold** and [links](https://…)."""
    t_ = e(besedilo)
    t_ = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', t_)
    t_ = re.sub(r'\*(.+?)\*', r'<em>\1</em>', t_)
    t_ = re.sub(r'(?<!\w)_(.+?)_(?!\w)', r'<em>\1</em>', t_)
    t_ = re.sub(r'\[([^\]]+)\]\((https?://[^)\s]+)\)', r'<a href="\2">\1</a>', t_)
    return t_


def datum(niz):
    return datetime.date.fromisoformat(niz[:10])


def kol(kljuc):
    return KOLEDAR[JEZIK][kljuc]


def dne(d):
    """'19. oktober 2026' / '19 October 2026'"""
    return ('%d. %s %d' if JEZIK == 'sl' else '%d %s %d') % (d.day, kol('meseci')[d.month - 1], d.year)


def telo_html(telo):
    """Paragraphs from the editor's text: '> ' is a pull quote, '## ' a subhead."""
    bloki = []
    for kos in re.split(r'\n\s*\n', (telo or '').strip()):
        kos = ' '.join(kos.split())
        if kos.startswith('> '):
            bloki.append('<figure class="pull-quote"><blockquote>“%s”</blockquote></figure>' % vrstica(kos[2:]))
        elif kos.startswith('## '):
            bloki.append('<h2>%s</h2>' % vrstica(kos[3:]))
        elif kos:
            bloki.append('<p>%s</p>' % vrstica(kos))
    return '\n'.join(bloki)


def element(pot_sl, pot_en, jezik):
    """One item in a language. None in English when it has no English file or title yet."""
    d = beri(pot_sl)
    if jezik == 'en':
        en = beri(pot_en)
        if not en.get('naslov'):
            return None
        d = prekrij(d, en)
    return d


def zbirka(mapa, jezik):
    """A collection (posts, books), oldest first by date."""
    out = []
    for f in sorted((VSEBINA / mapa / 'sl').glob('*.json')):
        d = element(f, VSEBINA / mapa / 'en' / f.name, jezik)
        if d is None or d.get('osnutek'):
            continue
        besedilo = d.get('besedilo', '')
        d.update(id=f.stem, telo=telo_html(besedilo),
                 minute=max(1, math.ceil(len(re.findall(r'\w+', besedilo)) / 200)))
        d['slug'] = f.stem if jezik == 'sl' else (d.get('slug') if 'slug' in beri(VSEBINA / mapa / 'en' / f.name)
                                                  else slugify(d['naslov']))
        for k in ('slika', 'platnica'):
            if d.get(k):
                d[k] = slika(d[k])
        out.append(d)
    return sorted(out, key=lambda o: o.get('datum', ''))


def nalozi(jezik):
    def datoteka(ime):
        sl = beri(VSEBINA / 'sl' / ime)
        return prekrij(sl, beri(VSEBINA / 'en' / ime)) if jezik == 'en' else sl
    s = datoteka('stran.json')
    s['avtor']['portret'] = slika(s['avtor']['portret'])
    s['avtor']['podpis'] = slika(s['avtor']['podpis'])
    s['leto'] = datetime.date.today().year
    bio = datoteka('zivljenjepis.json')
    s['zivljenjepis'] = dict(bio, telo=telo_html(bio.get('besedilo', ''))) if bio else None
    p = datoteka('projekt.json')
    p.setdefault('id', 'walking-the-myth')
    p['slika'] = slika(p.get('slika'))
    p['objave'] = zbirka('objave', jezik)
    return {'stran': s, 'knjige': zbirka('knjige', jezik), 'projekti': [p]}


def najdi(jezik, zbirka_, id_):
    return next((x for x in V[jezik][zbirka_] if x['id'] == id_), None)


def je_besedilo(o):
    return o.get('vrsta') in ('esej', 'zapis')


# ---------- components (named after the design system) ----------

def oznaka(beseda):
    if beseda not in OZNAKE:
        raise SystemExit('Oznaka "%s" ni dovoljena. Izberi eno od: %s' % (beseda, ', '.join(OZNAKE)))
    return beseda if JEZIK == 'sl' else OZNAKE_EN[beseda]


def kicker(*besede):
    """Labels from the allowed list, joined with ' · '."""
    return '<div class="kicker">%s</div>' % ' · '.join(e(oznaka(b)) for b in besede)


def kicker_objave(o):
    """Essay / Note, or Recommendation · Café …"""
    vrsta = VRSTE.get(o.get('vrsta'))
    if not vrsta:
        raise SystemExit('Objava "%s" mora imeti vrsto: %s' % (o['id'], ', '.join(VRSTE)))
    return kicker(vrsta, o['kategorija']) if o.get('kategorija') else kicker(vrsta)


def gumb(besedilo, href, zunanja=False):
    ext = ' target="_blank" rel="noopener"' if zunanja else ''
    return '<a class="btn" href="%s"%s>%s</a>' % (e(href), ext, e(besedilo))


def section_label(naslov, podnaslov=None):
    p = '<p>%s</p>' % e(podnaslov) if podnaslov else ''
    return '<div class="section-label"><h2>%s</h2>%s</div>' % (e(naslov), p)


def dateline(s):
    danes = datetime.date.today()
    dan = ('%s, %s' if JEZIK == 'sl' else '%s %s') % (kol('dnevi')[danes.weekday()], dne(danes))
    return ('<div class="dateline"><span data-dan="{kraj}">{kraj}, {dan}</span>'
            '<span class="time" data-ura></span></div>').format(kraj=e(s['kraj']), dan=e(dan))


def site_header(s, R, aktivno, z_imenom, par):
    ime = '<a class="name-compact" href="%s%s">%s</a>' % (R, pot('domov'), e(s['naslov'])) if z_imenom else ''
    nav = ''.join(
        '<a href="%s%s"%s>%s</a>' % (R, pot(k), ' aria-current="page"' if k == aktivno else '', e(t('nav')[k]))
        for k in NAV)
    drugi = drugi_jezik()
    jezik = '<a class="lang-switch" href="%s%s" hreflang="%s" lang="%s" aria-label="%s">%s</a>' % (
        R, par[drugi], drugi, drugi, e(t('jezik')), drugi.upper())
    # the menu hides behind this button (stran.js opens it over the whole screen)
    gumb_meni = ('<button type="button" class="menu-toggle" aria-expanded="false" aria-controls="glavni-meni" '
                 'aria-label="%s"><span></span><span></span><span></span></button>') % e(t('odpri_meni'))
    return ('<header class="site-header wrap">%s<div class="header-row"><div>%s</div>'
            '<nav class="site-nav" id="glavni-meni" aria-label="%s">%s</nav><div class="header-end">%s%s</div>'
            '</div></header>') % (dateline(s), ime, e(t('rubrike')), nav, jezik, gumb_meni)


def author_block(s, R, cta=True, z_oznako=True):
    a = s['avtor']
    # opens the biography pop-up; without a script it is a plain link to the about page
    gumb_html = ('<a class="btn" href="%s%s" data-odpri="zivljenjepis">%s</a>' % (
        R, pot('o-avtorju'), e(t('vec_o_meni')))) if cta else ''
    return ('<section class="author"><img class="author-portrait" src="{R}slike/{p}" alt="{ime}">'
            '<div>{label}<p class="author-quote">“{c}”</p><div class="copy">{o}</div>{g}</div>'
            '<img class="author-signature" src="{R}slike/{pod}" alt=""></section>').format(
        R=R, p=e(a['portret']), ime=e(s['ime']), c=e(a['citat']),
        label=section_label(t('o_avtorju')) if z_oznako else '', o=e(a['o_meni']), g=gumb_html,
        pod=e(a['podpis']))


def contact_form(s):
    """For now the form opens the visitor's email program, addressed to Uroš (stran.js builds the message)."""
    email = e(s['email'])
    return ('<form class="contact-form" action="mailto:{m}" method="post" enctype="text/plain" '
            'data-kontakt="{m}" data-zadeva="{z}">'
            '<label><span>{ime}</span><input name="ime" autocomplete="name" required></label>'
            '<label><span>{ep}</span><input name="eposta" type="email" autocomplete="email" required></label>'
            '<label class="cf-wide"><span>{sp}</span><textarea name="sporocilo" rows="5" required></textarea></label>'
            '<div class="cf-wide cf-end"><button type="submit" class="btn">{poslji}</button>'
            '<p class="cf-note">{opomba}</p></div></form>').format(
        m=email, z=e(t('zadeva')), ime=t('ime'), ep=t('eposta'), sp=t('sporocilo'), poslji=t('poslji'),
        opomba=t('kontakt_opomba').format(email='<a href="mailto:%s">%s</a>' % (email, email)))


def contact_section(s):
    return '<section class="contact wrap" id="kontakt">%s%s</section>' % (
        section_label(t('kontakt'), t('kontakt_pod')), contact_form(s))


def bio_dialog(s):
    """'Več o meni' pop-up with the biography from zivljenjepis.md."""
    z = s.get('zivljenjepis')
    if not z:
        return ''
    return ('<dialog class="bio-dialog" id="zivljenjepis" aria-labelledby="zivljenjepis-naslov">'
            '<div class="bio-top"><span class="bio-label">{l}</span>'
            '<button type="button" class="btn bio-close" data-zapri>{x}</button></div>'
            '<div class="bio-body"><h2 class="bio-title" id="zivljenjepis-naslov">{n}</h2>'
            '<div class="bio-text">{t}</div></div></dialog>').format(
        l=t('zivljenjepis'), x=t('zapri'), n=e(z.get('naslov', s['ime'])), t=z['telo'])


def site_footer(s, R, z_avtorjem, s_kontaktom):
    avtor = ('<div class="author-band"><div class="wrap">%s</div></div>%s' % (author_block(s, R), bio_dialog(s))
             if z_avtorjem else '')
    plain = '' if (z_avtorjem or s_kontaktom) else ' site-footer--plain'
    return ('<div class="footer-band">{a}{k}<footer class="site-footer wrap{p}">'
            '<p class="footer-wordmark">{w}</p><div class="footer-row"><span>© {ime}, {leto}</span>'
            '<span>{kraj}</span></div></footer></div>').format(
        a=avtor, k=contact_section(s) if s_kontaktom else '', p=plain, w=e(s['naslov']), ime=e(s['ime']),
        leto=s['leto'], kraj=e(s['kraj']))


def book_cover(k, R):
    """The flat cover shown as a standing book: turned a little, spine on the left, shadow below."""
    hrbet = ' style="--spine:%s"' % e(k['hrbet']) if k.get('hrbet') else ''
    return ('<span class="book-cover"%s><img src="%sslike/%s" alt="%s">'
            '<span class="book-spine" aria-hidden="true"></span></span>') % (
        hrbet, R, e(k['platnica']), e(k['naslov']))


def blank_cover(naslov, avtor):
    """A plain typeset cover for a book that has no cover yet, on the same book mockup."""
    return ('<span class="book-cover book-cover--blank"><span class="blank-cover">'
            '<span class="blank-author">%s</span><span class="blank-title">%s</span></span>'
            '<span class="book-spine" aria-hidden="true"></span></span>') % (e(avtor), e(naslov))


def book_feature(k, R, h='h2'):
    """A book: cover, short text, 'Več o knjigi' to its own page and 'Kupi knjigo' to the shop."""
    href = R + pot('knjige', slug=k['id'])
    gumbi = gumb(t('vec_o_knjigi'), href) + (gumb(t('kupi'), k['kupi'], zunanja=True) if k.get('kupi') else '')
    return ('<article class="book-feature"><a href="{h}" tabindex="-1">{m}</a><div class="text">{k}'
            '<{hx} class="h-feature"><a href="{h}">{n}</a></{hx}><div class="copy">{t}</div>'
            '<div class="btn-row">{g}</div></div></article>').format(
        h=e(href), m=book_cover(k, R), n=e(k['naslov']), k=kicker('Knjiga'), hx=h, t=e(k['kratko']), g=gumbi)


def story_teaser(o, p, R):
    """The newest essay or note of a project, labelled with its kind (Esej / Zapis)."""
    href = R + pot(p['id'], slug=o['slug'])
    return ('<article class="story-teaser">{k}<h2 class="h-story"><a href="{h}">{n}</a></h2>'
            '<div class="copy">{t}</div>{g}</article>').format(
        k=kicker_objave(o), h=e(href), n=e(o['naslov']), t=e(o.get('povzetek', '')), g=gumb(t('nadaljuj'), href))


def project_teaser(p, R):
    return ('<article class="project" id="{id}"><img src="{R}slike/{s}" alt="" loading="lazy">'
            '<div><h3 class="h-feature">{n}</h3><div class="copy">{t}</div>{g}</div></article>').format(
        id=e(p['id']), R=R, s=e(p['slika']), n=e(p['naslov']), t=e(p['opis']), g=gumb(t('vstopi'), R + pot(p['id'])))


def shelf_item(x, R):
    """One recommendation. A book cover or film poster stands centred on the plate;
    other pictures (a café) fill it. Title and 'Priporočilo' lead to the outside page."""
    oblika = {'knjiga': ' shelf-plate--object', 'plakat': ' shelf-plate--object',
              'fotografija': ' shelf-plate--print'}.get(x.get('oblika'), '')
    zasluge = ''
    if x.get('slika_avtor'):
        # a licensed photo: author and licence under it, as the licence asks
        avtor = ('<a href="%s" target="_blank" rel="noopener">%s</a>' % (e(x['slika_vir']), e(x['slika_avtor']))
                 if x.get('slika_vir') else e(x['slika_avtor']))
        lic = ('<a href="%s" target="_blank" rel="noopener">%s</a>' % (e(x['slika_licenca_url']),
                                                                       e(x['slika_licenca']))
               if x.get('slika_licenca_url') else e(x.get('slika_licenca', '')))
        zasluge = '<p class="shelf-credit">%s: %s%s</p>' % (t('foto'), avtor, ', ' + lic if lic else '')
    plosca = ('<div class="shelf-plate%s"><img src="%sslike/%s" alt="%s" loading="lazy">%s</div>' % (
        oblika, R, e(x['slika']), e(x['naslov']), zasluge)) if x.get('slika') else ''
    pod = '<span>%s</span>' % e(x['podnaslov']) if x.get('podnaslov') else ''
    href = x.get('povezava')
    ext = ' target="_blank" rel="noopener"'
    naslov = '<a href="%s"%s>%s</a>' % (e(href), ext, e(x['naslov'])) if href else e(x['naslov'])
    g = gumb(t('priporocilo'), href, zunanja=True) if href else ''
    return ('<article class="shelf-item" id="{id}">{pl}{k}<h3>{n}{pod}</h3>'
            '<div class="copy">{t}</div>{g}</article>').format(
        id=e(x['id']), pl=plosca, k=kicker(x['kategorija']), n=naslov, pod=pod, t=e(x.get('povzetek', '')), g=g)


def page_head(naslov, R, uvod=None, dodatek=''):
    u = '<p class="page-standfirst">%s</p>' % e(uvod) if uvod else ''
    return '<div class="page-head"><h1 class="page-title">%s</h1>%s%s</div>' % (e(naslov), u, dodatek)


# ---------- page shell ----------

def stran(pot_, naslov, glava_html, telo_html_, s, R, par, aktivno=None, opis=None, z_imenom=True,
          z_avtorjem=True, s_kontaktom=True, domov=False):
    """Write one page. par holds the page's folder in both languages, for the SL/EN switch."""
    title = naslov if domov else '%s — %s' % (naslov, s['naslov'])
    opis = opis or s['podnaslov']
    dok = '''<!doctype html>
<html lang="{jezik}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">{noindex}
<script>document.documentElement.className += ' js'</script>
<title>{title}</title>
<meta name="description" content="{opis}">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{opis}">
<meta name="theme-color" content="#EFECE1">
<link rel="icon" href="{ikona}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
{pisave}
<link rel="stylesheet" href="{R}sredstva/ds.css?v={v}">
<link rel="stylesheet" href="{R}sredstva/stran.css?v={v}">
</head>
<body>
<a class="skip" href="#vsebina">{skip}</a>
{glava}{hero}
<main id="vsebina"{main_cls}>{telo}</main>
{noga}
<script src="{R}sredstva/stran.js?v={v}" defer></script>
</body>
</html>
'''.format(jezik=JEZIK, title=e(title), opis=e(opis), ikona=IKONA, pisave=PISAVE, R=R, v=VERZIJA,
           noindex='\n<meta name="robots" content="noindex">' if OSNOVA else '', skip=t('na_vsebino'),
           glava=site_header(s, R, aktivno, z_imenom, par), hero=glava_html,
           main_cls='' if domov else ' class="page-main"', telo=telo_html_,
           noga=site_footer(s, R, z_avtorjem, s_kontaktom))
    cilj = IZHOD / pot_
    cilj.parent.mkdir(parents=True, exist_ok=True)
    cilj.write_text(dok, encoding='utf-8')


def R_za(pot_):
    globina = pot_.count('/')
    return '../' * globina if globina else './'


# ---------- pages ----------

def naslovnica(v):
    s = v['stran']
    pot_ = pot('domov') + 'index.html'
    R = R_za(pot_)
    hero = ('<div class="hero wrap"><h1 class="masthead">{w}</h1><div class="masthead-meta">'
            '<p class="standfirst">{u}</p></div></div>').format(w=e(s['naslov']), u=e(s['podnaslov']))
    deli = []
    projekt = v['projekti'][0] if v['projekti'] else None
    objave = projekt['objave'] if projekt else []
    besedila = [o for o in objave if je_besedilo(o)]
    priporocila = [o for o in objave if o.get('vrsta') == 'priporocilo']
    prvi = []
    if v['knjige']:
        prvi.append(book_feature(v['knjige'][0], R))
    if besedila:
        prvi.append(story_teaser(besedila[-1], projekt, R))  # the newest essay or note
    if prvi:
        deli.append('<section class="section wrap"><div class="today">%s</div></section>' % ''.join(prvi))
    if projekt:
        deli.append('<div class="project-band"><section class="section wrap">%s</section></div>' % (
            project_teaser(projekt, R)))
    if priporocila:
        predmeti = ''.join(shelf_item(x, R) for x in reversed(priporocila[-3:]))  # the three newest
        deli.append('<section class="section wrap">%s<div class="shelf">%s</div></section>' % (
            section_label(t('na_polici'), t('na_polici_pod')), predmeti))
    stran(pot_, '%s — %s' % (s['naslov'], s['ime']), hero, ''.join(deli), s, R, oba('domov'),
          z_imenom=False, domov=True)


def knjige(v):
    """Books: the list, and a page for each published book."""
    s = v['stran']
    pot_ = pot('knjige') + 'index.html'
    R = R_za(pot_)
    glava = '<div class="wrap">%s</div>' % page_head(t('knjige_naslov'), R)
    seznam = [book_feature(k, R) for k in v['knjige']]
    for p in v['projekti']:
        # a book that is still being written: plain cover, 'Izide kmalu', into the project
        seznam.append(('<article class="book-feature"><a href="{h}" tabindex="-1">{m}</a><div class="text">{k}'
                       '<h2 class="h-feature"><a href="{h}">{n}</a></h2><div class="copy">{t}</div>'
                       '<div class="btn-row">{g}</div></div></article>').format(
            h=e(R + pot(p['id'])), m=blank_cover(p['naslov'], s['ime']), k=kicker('Knjiga'), n=e(p['naslov']),
            t=e(p.get('knjiga', t('izide_kmalu'))), g=gumb(t('vstopi'), R + pot(p['id']))))
    telo = '<div class="wrap page-body"><div class="book-list">%s</div></div>' % ''.join(seznam)
    stran(pot_, t('nav')['knjige'], glava, telo, s, R, oba('knjige'), aktivno='knjige')

    for k in v['knjige']:
        pot_ = pot('knjige', slug=k['id']) + 'index.html'
        R = R_za(pot_)
        glava = '<div class="wrap"><div class="page-head">%s<h1 class="page-title">%s</h1></div></div>' % (
            kicker('Knjiga'), e(k['naslov']))
        odstavki = telo_html(k.get('opis') or k['kratko'])
        kupi = '<div class="btn-row" style="margin-top:28px">%s</div>' % gumb(
            t('kupi'), k['kupi'], zunanja=True) if k.get('kupi') else ''
        podatki = '<p class="book-facts">%s</p>' % '<br>'.join(e(x) for x in k['podatki']) if k.get('podatki') else ''
        telo = ('<div class="wrap page-body"><article class="book-page">'
                '{m}<div><div class="copy">{o}</div>{kupi}{pod}'
                '</div></article></div>').format(m=book_cover(k, R), o=odstavki, kupi=kupi, pod=podatki)
        stran(pot_, k['naslov'], glava, telo, s, R, oba('knjige', k['id'], k['id']), aktivno='knjige',
              opis=k['kratko'])


def timeline(p, s, R):
    """Posts from oldest to newest with their date in the left column, and the book at the end."""
    vrstice = []
    for o in p['objave']:
        kdaj = '<span class="tl-day">%s</span>' % e(dne(datum(o['datum']))) if o.get('datum') else ''
        if je_besedilo(o):
            href, ext, g = R + pot(p['id'], slug=o['slug']), '', t('preberi')
        else:
            href, ext, g = o.get('povezava'), ' target="_blank" rel="noopener"', t('priporocilo')
        pod = '<span class="tl-sub">%s</span>' % e(o['podnaslov']) if o.get('podnaslov') else ''
        naslov = '<a href="%s"%s>%s</a>%s' % (e(href), ext, e(o['naslov']), pod) if href else e(o['naslov']) + pod
        vrstice.append(
            '<li class="tl-item"><div class="tl-when">{k}</div><article class="tl-post">{o}'
            '<h3 class="tl-title">{n}</h3><p class="copy">{t}</p>{g}</article></li>'.format(
                k=kdaj, o=kicker_objave(o), n=naslov, t=e(o.get('povzetek', '')),
                g=gumb(g, href, zunanja=bool(ext)) if href else ''))
    vrstice.append(
        '<li class="tl-item tl-book"><div class="tl-when"><span class="tl-soon">{km}</span></div>'
        '<article class="tl-post book-soon">{c}<div>{k}<h3 class="tl-title">{n}</h3><p class="copy">{t}</p></div>'
        '</article></li>'.format(km=t('kmalu'), c=blank_cover(p['naslov'], s['ime']), k=kicker('Knjiga'),
                                 n=e(p['naslov']), t=e(p.get('knjiga', t('izide_kmalu')))))
    return '<ol class="timeline">%s</ol>' % ''.join(vrstice)


def projekti(v):
    s = v['stran']
    for p in v['projekti']:
        pot_ = pot(p['id']) + 'index.html'
        R = R_za(pot_)
        glava = ('<div class="wrap project-head"><div class="project-intro"><h1 class="page-title">{n}</h1>'
                 '<p class="page-standfirst">{u}</p></div><figure class="project-photo"><img src="{R}slike/{sl}" '
                 'alt="Berlin">{zasl}</figure></div>').format(
            n=e(p['naslov']), u=e(p.get('uvod', p['opis'])), R=R, sl=e(p['slika']),
            zasl='<figcaption>%s: %s</figcaption>' % (t('foto'), e(p['slika_avtor'])) if p.get('slika_avtor') else '')
        telo = '<div class="wrap page-body">%s</div>' % timeline(p, s, R)
        stran(pot_, p['naslov'], glava, telo, s, R, oba(p['id']), opis=p.get('uvod', p['opis']))

        # essays and notes have their own page under the project
        drugi_p = najdi(drugi_jezik(), 'projekti', p['id']) or {}
        for o in p['objave']:
            if not je_besedilo(o):
                continue
            pot_ = pot(p['id'], slug=o['slug']) + 'index.html'
            R = R_za(pot_)
            meta = '%s<br>%s<br>%s' % (e(s['ime']), e(dne(datum(o['datum']))) if o.get('datum') else '',
                                       t('branje')(o['minute']))
            glava = ('<div class="wrap essay-head"><div class="kicker">{pr} · {vr}</div>'
                     '<h1 class="page-title essay-title">{n}</h1>'
                     '<div class="essay-meta-row"><p class="page-standfirst">{u}</p><div class="essay-meta">{m}</div>'
                     '</div></div>').format(pr=e(p['naslov']), vr=e(oznaka(VRSTE[o['vrsta']])), n=e(o['naslov']),
                                            u=e(o.get('povzetek', '')), m=meta)
            telo = ('<div class="wrap"><article class="essay-body">%s<div class="essay-nav">%s</div>'
                    '</article></div>') % (o['telo'], gumb(t('nazaj_na') + p['naslov'], R + pot(p['id'])))
            drugi = next((x for x in drugi_p.get('objave', []) if x['id'] == o['id']), None)
            par = {JEZIK: pot(p['id'], slug=o['slug']),
                   drugi_jezik(): pot(p['id'], drugi_jezik(), drugi['slug'] if drugi else '')}
            stran(pot_, o['naslov'], glava, telo, s, R, par, opis=o.get('povzetek'))


def kontakt(v):
    s = v['stran']
    pot_ = pot('kontakt') + 'index.html'
    R = R_za(pot_)
    glava = '<div class="wrap">%s</div>' % page_head(t('kontakt'), R, uvod=t('kontakt_pod'))
    telo = '<div class="wrap page-body contact-page">%s</div>' % contact_form(s)
    stran(pot_, t('nav')['kontakt'], glava, telo, s, R, oba('kontakt'), aktivno='kontakt', s_kontaktom=False)


def o_avtorju(v):
    s = v['stran']
    pot_ = pot('o-avtorju') + 'index.html'
    R = R_za(pot_)
    glava = '<div class="wrap">%s</div>' % page_head(s['ime'], R)
    z = s.get('zivljenjepis')
    bio = '<div class="about-bio bio-text">%s</div>' % z['telo'] if z else ''
    telo = '<div class="wrap page-body about">%s%s</div>' % (author_block(s, R, cta=False, z_oznako=False), bio)
    stran(pot_, t('nav')['o-avtorju'], glava, telo, s, R, oba('o-avtorju'), aktivno='o-avtorju',
          opis=s['avtor']['o_meni'], z_avtorjem=False)


def napaka_404(v):
    """One 404 page for the whole site (GitHub Pages serves only one), in both languages."""
    s = v['stran']
    # 404 is served from any depth, so it links from the site root
    R = OSNOVA or '/'
    glava = '<div class="wrap">%s</div>' % page_head(
        'Te strani ni', R, uvod='Morda je zapis zamenjal mizo. This page does not exist.')
    telo = '<div class="wrap page-body"><div class="btn-row">%s%s</div></div>' % (
        gumb('Nazaj na naslovnico', R), gumb('Back to the front page', R + 'en/'))
    stran('404.html', 'Strani ni', glava, telo, s, R, oba('domov'), s_kontaktom=False)


# ---------- assets ----------

def ds_css():
    """Join the DS tokens into one file; Google Fonts go into <head> as a link."""
    pisave, deli = [], []
    for ime in TOKENI:
        css = (DS / 'tokens' / (ime + '.css')).read_text(encoding='utf-8')
        for url in re.findall(r"@import url\('([^']+)'\);", css):
            pisave.append('<link rel="stylesheet" href="%s">' % e(url))
        deli.append('/* tokens/%s.css */\n%s' % (ime, re.sub(r"@import url\('[^']+'\);\n?", '', css).strip()))
    return '\n'.join(pisave), '\n\n'.join(deli) + '\n'


def zgradi():
    global PISAVE, VERZIJA, JEZIK
    for j in JEZIKI:
        V[j] = nalozi(j)
    if IZHOD.exists():
        shutil.rmtree(IZHOD)
    (IZHOD / 'sredstva').mkdir(parents=True)
    PISAVE, css = ds_css()
    (IZHOD / 'sredstva' / 'ds.css').write_text(css, encoding='utf-8')
    for f in (KOREN / 'sredstva').iterdir():
        if f.is_file():
            shutil.copy2(f, IZHOD / 'sredstva' / f.name)
    # a short fingerprint of the styles and script, so browsers fetch them again after each update
    VERZIJA = hashlib.md5(b''.join(f.read_bytes() for f in sorted((IZHOD / 'sredstva').iterdir()))).hexdigest()[:8]
    shutil.copytree(VSEBINA / 'slike', IZHOD / 'slike')
    shutil.copytree(KOREN / 'urednik', IZHOD / 'urednik')  # the editor (Sveltia CMS)

    for j in JEZIKI:
        JEZIK = j
        v = V[j]
        naslovnica(v)
        knjige(v)
        projekti(v)
        kontakt(v)
        o_avtorju(v)
    JEZIK = 'sl'
    napaka_404(V['sl'])

    strani = sorted(str(p.relative_to(IZHOD)) for p in IZHOD.rglob('*.html'))
    print('Zgrajeno %d strani v %s (%d angleških)' % (
        len(strani), IZHOD, sum(1 for p in strani if p.startswith('en/'))))


def main():
    zgradi()


PISAVE = ''
VERZIJA = ''

if __name__ == '__main__':
    main()
