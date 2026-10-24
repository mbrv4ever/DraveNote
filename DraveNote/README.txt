DraveNote - lokale markdown-notities
=====================================

DraveNote bewaart je notities als gewone Markdown-bestanden (.md) in een map
naast de app (standaard 'notities'). Je kunt die bestanden dus altijd ook
buiten DraveNote openen of meenemen. Alles werkt lokaal en offline.

STARTEN
- Dubbelklik run.bat. De eerste keer installeert hij eenmalig de benodigde
  onderdelen (PyQt6) in een .venv-map. Daarna start de app meteen.
- Werkt er iets niet bij het starten? Draai start-debug.bat (toont fouten in een
  venster) of herstel.bat (zet de .venv opnieuw op).

GEBRUIK
- 'Nieuw' vraagt om een naam en maakt de notitie. Typ links; rechts zie je het voorbeeld.
- Kies bovenaan Bewerken / Gesplitst / Voorbeeld.
- De titel in de lijst komt uit de eerste regel (een kop met #).
- 'Hernoemen' en 'Verwijderen' voor beheer. Verwijderd gaat naar de map 'prullenbak';
  legen kan via Instellingen (Prullenbak > Legen).
- 'Map openen' opent de notitiemap in de verkenner.
- Zoekbalk filtert op titel en inhoud.

OPMAAK (Markdown) - of gebruik de knoppen
- # Kop 1, ## Kop 2, ### Kop 3
- **vet**, *cursief*, `code`
- - lijst   of   1. genummerd
- - [ ] taak (afvinken met - [x])
- > citaat
- [tekst](https://adres) voor een link
- --- voor een scheidingslijn

OPSLAAN
- DraveNote slaat automatisch op terwijl je typt.

TOEGANKELIJKHEID
- Stel de lettergrootte in via Instellingen (editor en voorbeeld).
- Taal volgt je systeem (NL/EN), of kies handmatig in Instellingen.

EIGEN .EXE MAKEN (optioneel)
- Draai eerst run.bat (voor de .venv), daarna bouw-exe.bat.
- Resultaat: dist\DraveNote.exe (een enkel bestand).

Vragen of een tip? service@dravenlock.nl
Steun de ontwikkeling: https://paypal.me/roger076
