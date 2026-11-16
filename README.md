# Profile Scheduler pro Home Assistant

První funkční kostra univerzálního scheduleru: profily, zařízení nebo skupiny akcí
v řádcích a barevné časové úseky v denní ose 00:00–24:00. Hodnoty mají textové
popisky, takže význam plánu nezávisí na rozlišení barev.

Plány se ukládají jako strukturovaná data. Integrace přímo vykonává standardní
HA akce; negeneruje množství YAML automatizací a scén.

## Požadavky a instalace

- Cílová a testovací verze: **Home Assistant 2026.10.4**, Python **3.14.2+**.
- Jde o rané MVP instalovatelné přes HACS jako vlastní repozitář. Starší verze HA nejsou podporované.
- Používá doménu `profile_scheduler`, aby nekolidovalo s existujícím projektem `scheduler`.

### Instalace přes HACS

1. V HACS otevřete nabídku **⋮ → Vlastní repozitáře / Custom repositories**.
2. Zadejte adresu **`https://github.com/VitisEK/scheduler`**.
3. Zvolte typ **Integrace / Integration** a klikněte na **Přidat**.
4. Vyhledejte **Profile Scheduler**, otevřete jej a zvolte **Stáhnout / Download**.
   Pokud je nabídnuta verze, použijte **main**; repozitář zatím nevydává releases.
5. Restartujte Home Assistant.
6. V **Nastavení → Zařízení a služby → Přidat integraci** vyhledejte **Profile Scheduler**.
7. Otevřete **Scheduler** v postranní nabídce.

HACS stáhne celou integraci včetně `frontend/panel.js`. Není potřeba přidávat kartu,
Lovelace resource ani další frontendový repozitář. Aktualizace instalujte přes HACS
a potom restartujte HA. HACS zajišťuje stažení souborů; první konfiguraci integrace
je potřeba dokončit v **Zařízení a služby**. Pokud už máte ruční instalaci této domény,
neodebírejte kvůli přechodu config entry v HA: její odebrání by smazalo uložené plány.

Postup přidání vychází z [oficiálního návodu HACS pro vlastní repozitáře](https://hacs.dev/docs/faq/custom_repositories/).

### Ruční instalace

1. Stáhněte tento repozitář a zkopírujte celou složku
   `custom_components/profile_scheduler` do `/config/custom_components/profile_scheduler`
   ve vašem HA. Výsledkem musí být například
   `/config/custom_components/profile_scheduler/manifest.json` a `frontend/panel.js`.
2. Restartujte Home Assistant.
3. V **Nastavení → Zařízení a služby → Přidat integraci** vyhledejte **Profile Scheduler**.
4. Otevřete **Scheduler** v postranní nabídce. Editor je dostupný administrátorům.
5. Pokud panel požádá o načtení standardních editorů, otevřete běžný přehled HA,
   vraťte se do Scheduleru a použijte **Znovu načíst editory**. Toto může být nutné
   po novém načtení prohlížeče. Nevyžaduje se přidávání Lovelace resources ani YAML konfigurace.

### První otevření a řešení potíží

Pokud panel požádá o načtení editorů, otevřete běžný přehled HA a vraťte se do Scheduleru.
Pokud integrace po instalaci není v seznamu, ověřte cestu, restart HA a případně
obnovte prohlížeč bez mezipaměti. Chyby načtení integrace hledejte v systémových protokolech HA.

## První plán

1. Vytvořte profil, například **Doma**, a zvolte dny pro automatický výběr.
   Připravené prázdné profily jsou Doma, Pracovní týden, Víkend pryč a Dovolená.
2. Přidejte řádek, pojmenujte jej a přes standardní HA selector vyberte entity,
   například `climate.obyvak`. Prázdný seznam cílů je vhodný pro skupinu různých akcí.
3. Klikněte na **Přidat úsek** nebo do prázdné časové osy. Kliknutí zakládá úsek
   se začátkem zaokrouhleným na 30 minut; přesné časy lze upravit ve formuláři.
4. Nastavte čas, barvu a srozumitelný popisek, například **21 °C**, **Vypnuto** nebo
   **Nabíjení 8 A**. Popisek je informační; skutečné parametry nastavte v editoru akcí.
5. V **Akce Home Assistant** přidejte běžnou HA akci, její cíl a parametry. Používá
   se stejný editor jako v automatizacích. Cíle řádku pouze předvyplní první novou akci;
   při změně cílů řádku se již uložené cíle akcí automaticky nepřepisují.
6. Uložte dialog a potom celý plán tlačítkem **Uložit** nad seznamem profilů.
7. Vyberte profil ručně nebo ponechte automatický výběr a zapněte plán. Zapnutí
   ihned aplikuje právě platné stavové úseky. Výchozí nový plán je vypnutý.

Kliknutím na blok otevřete úpravu i smazání. Řádky a profily lze také upravit nebo
smazat. Rozpracované změny zůstávají v prohlížeči do uložení celého plánu; zavření
stránky na ně upozorní. Současné přepsání z jiného editoru je chráněné revizí.

## Podporované akce

| Použití | Příklady standardních HA akcí | Režim |
| --- | --- | --- |
| Topení | `climate.set_temperature`, `climate.set_hvac_mode` | Stav |
| Světla | `light.turn_on` s jasem/barvou, `light.turn_off` | Stav |
| Přepínače | `switch.turn_on`, `switch.turn_off` | Stav |
| Nabíjení auta | Akce, které poskytuje vaše EV integrace; často switch, number nebo select | Stav pro podporované nastavovací akce, jinak jednorázově |
| Scény | `scene.turn_on` | Jednorázově |
| Skripty | `script.turn_on` nebo konkrétní `script.*` | Jednorázově |
| Další sekvence | Standardní HA akce, podmínky, čekání a další konstrukce editoru | Jednorázově |

**Stav** je pro opakovatelné nastavení absolutních hodnot. Backend přijímá jen
známé nastavovací akce s konkrétními cíli a bez šablon; přepnutí typu toggle,
relativní změny jasu, scény, skripty a obecné sekvence patří do režimu
**Jednorázově**. Editor standardně nabízí i tyto akce; při uložení nevhodného
stavového bloku integrace vysvětlí, že je nutné změnit režim.

Nabíjení auta není nová EV integrace: scheduler používá akce a parametry existující
integrace vozu nebo nabíječky. Zachovává jejich rozsahy a validaci v HA.

## Čas a vykonávání

- Úseky jsou **včetně začátku a bez konce**: 06:00–22:00 platí od 06:00 do 21:59…
  Čas 24:00 je možný jako konec. Noční úsek 22:00–06:00 pokračuje přes půlnoc.
- Na konci úseku se automaticky neposílá opačná akce. Například pro vypnutí světla
  v 22:00 vytvořte další úsek se začátkem 22:00 a akcí `light.turn_off`.
- Úseky jednoho řádku se nesmějí překrývat. Různé řádky jsou nezávislé; nevytvářejte
  v nich protichůdné akce pro stejné zařízení.
- Automatický výběr použije první profil v seznamu odpovídající dnešnímu dni.
  Doma a Dovolená mají ve výchozím nastavení prázdné dny a vybírají se ručně.
  Při ručním výběru pravidla dnů neomezují aktivitu profilu. Zpět přepněte volbou
  **Automaticky podle dnů**. V MVP pořadí profilů určuje pořadí jejich vytvoření.
- O půlnoci se znovu vyhodnotí pravidla dnů. Nový profil má přednost i před nočním
  úsekem předchozího profilu. Pokud profil neodpovídá, nové akce se neprovádějí.
- Po restartu, opětovném zapnutí, uložení plánu, změně profilu nebo časového pásma
  se dopočítají a nastaví pouze právě platné **stavové** úseky.
- **Jednorázové** úseky se při obnově ani ruční změně profilu nepřehrávají. Spouštějí se
  jen na naplánované hranici; výpadek a zpoždění o minutu nebo více se nedohánějí.
  Přesný začátek úseku při automatickém přepnutí profilu o půlnoci je běžná hranice,
  takže se akce provede; starší jednorázové úseky nového profilu se nedohánějí.
- Platí časové pásmo nastavené v HA. Při jarní změně času se neexistující hranice
  posune na první platnou minutu. Úsek celý uvnitř vynechané hodiny se neprovede.
  Při podzimním opakování hodiny se hranice provede pouze při prvním výskytu.
- Akce v bloku běží jako standardní HA sekvence. Různé řádky mohou běžet souběžně.
  Následující hranice nebo změna plánu zruší stále běžící sekvence před zahájením
  nového vyhodnocení. Limit běhu je 60 sekund; chyby se automaticky neopakují.
  Již vykonané účinky ani samostatně spuštěný skript přes `script.turn_on` nelze vrátit.
- Vypnutí nebo odebrání integrace zruší čekající úlohy; zařízení zůstanou v posledním
  nastaveném stavu. Scheduler neposkytuje záruku exactly-once při pádu HA.

## Správa a data

Integrace vytvoří standardní HA entity: přepínač zapnutí, výběr profilu a senzory
aktivního profilu a nejbližšího vyhodnocení. Nejbližší termín může být půlnoc pro
výběr profilu, i když tehdy nebude potřeba odeslat akci. Panel stav obnovuje nejvýše
po 30 sekundách, pokud není rozepsaná změna nebo otevřený dialog.

Plán a jeho revize se ukládají přes `homeassistant.helpers.storage.Store` do HA
`.storage/profile_scheduler.<entry_id>`. Soubory neupravujte ručně; zahrňte je do
zálohy HA. Samotný reload nebo restart data ponechá, odebrání integrace plány smaže.
MVP podporuje jednu instanci integrace.

## Rozsah a známá omezení

Vlastní je denní časová osa, model profilů a jejich vazba na vykonávání. HA poskytuje
konfigurační dialog, formuláře, výběr entit, editor akcí s našeptáváním, motivy,
běh sekvencí, storage, entity a plánování callbacků. Panel má české a anglické texty;
nativní editory přebírají jazyk HA. Frontendové komponenty HA nejsou stabilní externí
API, proto je jejich kompatibilita soustředěná do malé načítací vrstvy a má být
ověřená při aktualizacích HA.

MVP zatím nenabízí přetahování bloků, kalendářní výjimky dovolené podle dat,
historii vykonání ani export/import v UI. Jednorázové akce lze nastavit na začátek
libovolného úseku; šířka bloku neznamená opakování akce během jeho trvání.
Akce plánu nemají reloadovat ani odebírat samotnou integraci; nepřímé řízení jejího
lifecycle skriptem zatím není podporované.

## Vývoj

Viz [architektura a vývoj](docs/DEVELOPMENT.md), [výsledek ověřování](docs/VALIDATION.md)
a [pravidla agentů](AGENTS.md). Zdrojové soubory jsou přímo instalovatelné bez sestavení
frontendu. Testy frontendového průchodu používají zástupné nativní prvky a nenahrazují
kontrolu ve skutečném HA prohlížeči.
