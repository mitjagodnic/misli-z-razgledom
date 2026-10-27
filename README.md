# Café Goričan

Spletna stran Uroša Goričana: https://mitjagodnic.github.io/misli-z-razgledom/

- **Urednik:** https://mitjagodnic.github.io/misli-z-razgledom/urednik/ (Sveltia CMS, prijava z GitHub žetonom).
  Vsaka shranjena sprememba se zapiše sem, stran pa se v 1–2 minutah zgradi in objavi sama.
- **Vsebina:** `vsebina/` (JSON, en na objavo in jezik), slike v `vsebina/slike/`.
- **Gradnja:** `python3 build.py` → `stran/` (GitHub Actions: `.github/workflows/objava.yml`).
