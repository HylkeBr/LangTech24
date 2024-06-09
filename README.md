# LangTech24
Final project Language Technology 2024

## To do:
- Maat achter antwoorden
  - Bv van '4' naar '4 meter'
- Bij meerdere gevonden antwoorden de beste er uit halen
  -  Niet wanneer om meerdere antwoorden gevraagd wordt
  -  Filteren op correcte antwoorden op een of andere manier?
- Meer verschillende soorten vragen matchen
  - Kun je me een lijst geven van alle berensoorten?
  - Hoeveel jongen krijgt een kat?
  - Hoe heet een goudvis in het Duits?
- Output formaat aanpassen naar wat nodig is voor inleveren
  - JSON oid geloof ik
- Wellicht nog meer/andere dingen

## Done:
- Soorten vragen:
  - Wat is [een aspect] van [een dier]?
    - Example: Wat is de belangrijkste voedselbron van een tijger?
  - Is een [een dier] [kleur]?
  - Welke kleur heeft [een dier]?
  - Waar is [een dier] goed voor? (regex)
  - Waar komt [een dier] voor? (regex)
  - Hoeveel weegt [een [bn] dier]? (regex, statement)
    - bn: pasgeboren, volwassene, mannelijke, vrouwelijke
  - Hoe zwaar is [een dier]?
  - Hoe lang is [een dier]?
  - Hoe groot is [een dier]?
  - Hoe hoog is [een dier]?

- Geeft lijst met alle gevonden antwoorden
  - Ook wanneer dit niet de bedoeling is
