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
  - Hoeveel weegt [een [amod] dier]? (regex, statement)
    - amod: pasgeboren, volwassene, mannelijke, vrouwelijke
  - Hoeveel jongen krijgt [een dier]? (regex)
  - Hoe zwaar is [een dier]?
  - Hoe lang is [een dier]?
  - Hoe groot is [een dier]?
  - Hoe hoog is [een dier]?
  - Hoe heet [een dier] in [een taal]?
    - all available languages supported

- Geeft lijst met alle gevonden antwoorden
  - Ook wanneer dit niet de bedoeling is
