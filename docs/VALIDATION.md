# Ověření MVP

## Místní kontroly

- Čisté plánovací jádro: **18 testů prošlo** (půlnoc, noční úseky, profily, DST,
  výlučný konec intervalu, přepočet časového pásma a výkon při 2 000 blocích).
- Frontend: **3 testy prošly** (vytvoření profilu → entity/akce → úsek → uložení
  a aktivace, zachování otevřeného editoru, vysvětlení studeného načtení HA prvků).
- Ruff check a Ruff format check: prošly. Python 3.14 kompilace zdrojů: prošla.
- Plné HA testy nelze spustit na nativním Windows: HA runner vyžaduje `fcntl`.
  Připravené prostředí používá Python 3.14.10, HA 2026.10.4 a testovací plugin 0.13.375.

## Linux CI

Workflow `.github/workflows/checks.yml` spouští pytest, Ruff, mypy, frontendové testy
a hassfest na GitHub Actions. Výsledek prvního běhu bude doplněn po jeho dokončení.

Testy používají syntetické služby a řízený čas. Nebyla ovládaná skutečná domácnost.
Frontendový test používá jsdom a zástupné nativní prvky; nezaručuje kompatibilitu
vnitřního vykreslování komponent ve skutečném prohlížeči HA.
