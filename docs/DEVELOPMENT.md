# Vývoj integrace Scheduler

## Stav projektu

Repozitář obsahuje první MVP integrace v `custom_components/profile_scheduler`:
deterministické jádro, HA backend, nativní entity, JSON websocket API a frontendový panel.
Testy jsou v `tests`, CI v `.github/workflows/checks.yml`. Výsledky skutečně provedených
kontrol a jejich omezení jsou v [VALIDATION.md](VALIDATION.md).

## Rozdělení práce

Hlavní agent řídí zadání, rozhraní, společné soubory a výslednou kontrolu.
Role jsou projektové TOML soubory v `.codex/agents/`:

| Role | Odpovědnost | Zápis |
| --- | --- | --- |
| `ha_architect` | Architektura, kompatibilita, časové a provozní chování | Bez úprav souborů |
| `scheduler_engine` | Výpočet termínů a opakování | Přidělené soubory jádra |
| `ha_integration` | Config flow, lifecycle, entity, storage, akce HA | Přidělené soubory integrace |
| `ha_tests` | Deterministické testy a regrese | Přidělené testy a fixtures |
| `ha_reviewer` | Nezávislá kontrola správnosti a rizik | Bez úprav souborů |

Model a úroveň uvažování se dědí z hlavní relace. Limit je tři současní subagenti;
konkrétní klient nebo spravované nastavení může limit snížit. Omezení zápisu u rolí
jsou instrukce, nikoli samostatný bezpečnostní sandbox.

U větší funkce nejprve sjednoťte rozhraní a akceptační kritéria. Potom lze oddělit
jádro, HA adaptér a testy do různých souborů. Testy vycházejí ze stejného kontraktu.
Reviewer dostane hotový společný diff. Hlavní agent vyřeší nálezy a ověří výsledek.
Malé změny řeší jeden agent.

## Použití v Codexu

Otevřete tuto složku jako projekt a spusťte novou relaci Codexu, aby načetla nové
projektové nastavení a role. Projektová konfigurace vyžaduje důvěryhodný projekt;
spravované zásady klienta mají přednost. Dostupnost vlastních rolí ověřte v nové relaci.
Pokud je daný klient nepodporuje, `AGENTS.md` stále popisuje pracovní postup a hlavní
agent může zadat stejnou roli běžnému subagentovi. Nevytvářejte globální výjimky oprávnění.

Příklady zadání:

```text
Použij ha_architect pro návrh MVP scheduleru. Sepiš otevřená rozhodnutí,
navrhni rozhraní a akceptační kritéria. Implementaci zatím nevytvářej.
```

```text
Implementuj domluvenou funkci. Rozděl samostatné soubory mezi scheduler_engine,
ha_integration a ha_tests. Po integraci změn použij ha_reviewer,
vyřeš nálezy a spusť dostupné kontroly.
```

## Architektura MVP a přijatá rozhodnutí

1. **Jádro `engine.py`:** čisté výpočty nad předaným časem, bez HA a bez I/O.
2. **HA adaptér:** config flow, `ConfigEntry.runtime_data`, Store v1, callback na nejbližší
   hranici, standardní Script pro vykonání akcí; žádná vygenerovaná YAML automatizace.
3. **Panel `frontend/panel.js`:** vlastní osa a struktura profilů/řádků, nativní `ha-form`,
   `ha-selector` pro entity a akce, `ha-dialog`, HA motivy. Není potřeba npm build při instalaci.
4. **API:** administrátorské websocket příkazy `profile_scheduler/get`, `/save`,
   `/set_profile`, `/set_enabled`; optimistická revize brání přepsání z jiného editoru.
5. **Správa:** jedna config entry, nativní switch, select a senzory; soukromé plány
   může měnit administrátor nebo systémová automatizace. Publikace ani HACS nebyly součástí MVP.

`scheduler` je obsazen projektem nielsfaber/scheduler-component a `universal_scheduler`
projektem schblondie/universal_scheduler. Pro `profile_scheduler` nebyla nalezena
kolize v HA Core ani veřejném vyhledávání; použita je tato doména.

Časové a provozní chování je podrobně popsané v [README](../README.md): polootevřené
intervaly včetně nočních, přednost aktuálního profilu při půlnoci, první odpovídající
profil, ruční override, HA časové pásmo a jeho změny, posun neexistující hranice na
první platnou minutu a pouze první výskyt opakované hodiny. Stavové akce se při obnově
znovu nastavují, jednorázové se nedohánějí. Úplně vynechaný jarní interval se přeskočí.
Po skončení bloku není implicitní opačná akce. Nové vyhodnocení ruší předchozí sekvence;
akce mají limit 60 sekund a žádné automatické retry.

Nativní frontendové komponenty se nekopírují. `window.loadCardHelpers()` a button editor
načtou `ha-form`/`ha-selector`; action selector načítá skutečný automatizační editor.
Při studeném přímém otevření panelu může být nutná návštěva přehledu HA. Toto omezení
je viditelné v UI i návodu; nepoužívají se privátní metody routeru ani hashované importy.

Store má explicitní verzi 1. Pro budoucí změnu schématu je nutná migrace a odpovídající
testy; samotné zvýšení čísla verze bez migrace není přijatelné.

Významná přijatá rozhodnutí zapisujte stručně s důvodem sem nebo do samostatného ADR
v `docs/decisions/`. Otevřená produktová rozhodnutí nepřevádějte potichu na implementační výchozí hodnoty.

## Prostředí a kontroly

Nainstalovaný Python na tomto počítači není automaticky kompatibilní s vybraným HA.
Při první implementaci ověřte požadavky HA a testovacího pluginu, vytvořte izolované
prostředí a zapište reprodukovatelné verze závislostí. Pro HA testy a CI preferujte Linux
(například WSL, kontejner nebo Linux CI runner), pokud nativní Windows požadavky nesplní.

Závislosti jsou připnuté v `requirements-dev.txt`: HA 2026.10.4 a testovací plugin
0.13.375 vyžadují Python 3.14.2+. Na Linuxu použijte:

```sh
python3.14 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements-dev.txt
python -m ruff check .
python -m ruff format --check .
python -m mypy
python -m pytest -q
npm ci
npm test
```

Na Windows je připravené místní prostředí `.venv-ha` s Pythonem 3.14; stav jeho
kontrol uvádí VALIDATION.md. Čisté jádro lze testovat odděleně příkazem
`python -m unittest discover -s tests -p test_engine.py -v`; Windows potřebuje `tzdata`.
Frontendové testy přes jsdom ověřují průchod vlastním panelem a vazby na nativní
selektory, jejich vnitřní vykreslování nahrazují testovacími prvky. Nejde o browser E2E
test se skutečným HA frontendem.

CI obsahuje Ruff, mypy, pytest, frontendové testy a hassfest. CI samotné nebylo
ověřené pouhým vytvořením workflow; skutečný výsledek zaznamenejte po spuštění.

## Zdroje

Konfigurace rolí ověřena 16. 11. 2026 proti oficiální dokumentaci; místní CLI hlásí
`0.169.0-alpha.11.1`. Před změnou formátu ověřte podporu používaného klienta.

- [Codex: Subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents)
- [Codex: AGENTS.md](https://learn.chatgpt.com/docs/agent-configuration/agents-md)
- [Home Assistant: Integration Quality Scale](https://contributors.home-assistant.io/core/quality-scale/)
- [Home Assistant: Writing tests](https://contributors.home-assistant.io/core/development/tests/)
- [Home Assistant: Blocking operations](https://contributors.home-assistant.io/core/internals/blocking-operations/)
- [Home Assistant: Events](https://contributors.home-assistant.io/core/integrations/events/)
