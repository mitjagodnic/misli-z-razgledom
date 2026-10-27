#!/bin/sh
# Pošlje lokalne spremembe na GitHub. Stran zgradi in objavi GitHub sam (.github/workflows/objava.yml),
# isto se zgodi, ko Uroš shrani spremembo v urejevalniku (/urednik/).
# Uporaba: ./objavi.sh "Kratek opis spremembe"
set -e
cd "$(dirname "$0")"
git pull -q --rebase origin main   # najprej prenesi, kar je Uroš medtem spremenil v urejevalniku
python3 build.py                   # preveri, da se stran zgradi
git add -A
if git diff --cached --quiet; then
  echo "Ni sprememb za objavo."
else
  git commit -q -m "${1:-Posodobitev strani}" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
  git push -q origin main
  echo "Poslano. GitHub bo stran objavil v 1–2 minutah."
fi
