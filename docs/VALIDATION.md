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

Ověřeno 16. 11. 2026 na Linuxu, Pythonu 3.14.10 a HA 2026.10.4:

- **44 Python testů prošlo**: 18 testů čistého jádra a 26 HA integračních scénářů.
- **3 frontendové testy prošly**.
- **Ruff, kontrola formátování, mypy a hassfest prošly**; mypy zkontrolovalo 11 zdrojových souborů.

Úspěšný běh: [Checks 43961725276](https://github.com/VitisEK/scheduler/actions/runs/43961725276),
implementační commit `f79a417f99ff656b603791a9cbe938957fb9f8ab`.
Následná změna této dokumentace nemění ověřený kód.

HA testy používají skutečné config entries, Store, Script, časové callbacky a nativní
entity. Ověřují obnovu po uložení/restartu/zapnutí, ruční i automatické profily,
půlnoc, jednorázové akce bez přehrání při obnově, revize a oprávnění, staré callbacky
a vypnutí scheduleru jeho vlastní akcí. Scénáře světla, přepínače, nabíjecího proudu
a režimu, scény a obou způsobů volání skriptu ověřují také předání cíle a parametrů.
Vedlejší účinky služeb jsou nahrazené syntetickými koncovými body.

Testy používají syntetické služby a řízený čas. Nebyla ovládaná skutečná domácnost.
Frontendový test používá jsdom a zástupné nativní prvky; nezaručuje kompatibilitu
vnitřního vykreslování komponent ve skutečném prohlížeči HA.
Ruční instalace a proklikání celé aplikace ve skutečném HA prohlížeči nebyly provedené.
Frontendová rozhraní byla navíc porovnána se zdroji frontendové verze `20260930.5`,
kterou používá cílový HA; návod popisuje možné první načtení editorů přes přehled.
