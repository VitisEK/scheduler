# Témata a profily: požadované chování

- Téma vlastní seznam entit a seznam profilů. Profily téhož tématu nastavují
  stavy jeho entit. Různá témata mohou mít současně různé aktivní profily.
- Aktivní profil se volí pro každé téma samostatně ručně nebo automatizací
  Home Assistantu. Den v týdnu sám o sobě aktivní profil nepřepíná.
- Profil může používat stejný denní časový plán každý den, nebo jednotlivé
  plány podle dne v týdnu. Různé profily mohou mít plán pro tentýž den.
- Přepnutí aktivního profilu má obnovit právě platné stavové úseky; jednorázové
  akce z minulosti se nesmějí zpětně spouštět. Časové pásmo a chování při DST
  se nadále řídí pravidly popsanými v README.

## Dopad na existující data

Stávající schéma má globální profil a v automatickém režimu vybírá profil podle
aktuálního dne v týdnu. Nový model takový režim neobsahuje. Migrace proto musí
zachovat původní profily, entity, úseky a akce, ale samotný způsob volby profilu
nelze beze změny chování převést. Při převodu vzniká jedno téma se zachovanými profily a řádky. Ručně vybraný
profil zůstává aktivní; původní automatický výběr přejde do neaktivního stavu
a HA zobrazí oznámení. Uživatel vybere profil ručně nebo automatizací.


