# Inverse General Game Playing
## Abstract
In dit onderzoek werken we verder op het werk van Cropper et al. over Inverse General Game Playing (IGGP) (https://link.springer.com/article/10.1007/s10994-019-05843-w).
Hierbij is het doel om uit observaties van een spel de spelregels ervan af te leiden.
We introduceren enkele metrieken voor het valideren van de gevonden spelregels.
Verder vergelijken we de prestaties van Clausal Discovery engine Claudien op het IGGP probleem met die van Inductive Logic Programming (ILP) systeem ILASP.
Als laatste onderzoeken we de impact van de grootte en diversiteit van de invoerdata.
We concluderen dat de prestaties van Claudien in de buurt komen van die van ILASP indien de invoerdata beperkt blijft, maar dat over het algemeen ILASP nog altijd de beste prestaties neerzet.
Verder tonen we aan dat de prestaties afhankelijk zijn van de invoerdata en van de complexiteit van de spelregels.
Over het algemeen concluderen we dat Inverse General Game Playing een moeilijk probleem blijft voor de bestaande ILP systemen.
## Repository
* background: bevat een script dat de clauses die behoren tot de achtergrondkennis van een spel, apart opslaat.
* claudien: bevat alle scripts om het clausal discovery systeem claudien te gebruiken om te trainen en output ervan op te slaan.
* data: bevat de Cropper dataset en scripts om de maximale en minimale dataset te generegen. Eens je die hebt, kan je met data_generator.py datasets genereren voor het iteratief data experiment. Hier zijn ook de volledige input files voor ILASP en Claudien te vinden. 
* experiments: scripts om basis experiment, iteratief data experiment en incrementeel gerichte voorbeelden experiment. Bevat ook een paar scripts om uit de csv's grafieken te maken.
* game_tree: bevat scripts om minimale/maximale spelboom op te stellen en om geleerde hypotheses te valideren
* games: bevat de spelregels (GDL spelregels van de dataset van Cropper et al. geconverteerd naar prolog notatie)  
* learned_rules: bevat een script dat de hypotheses voor de target-predicaten samenvoegt en ook de background toevoegt en dit wegschrijft zodat we terug een bestand krijgen dat de volledige (geleerde) spelregels vormt voor een spel.
* software: bevat bestanden die nodig zijn voor ILASP te kunnen uitvoeren.
* types: bevat type instanties voor de predicaten per spel  
    
	
## Installatie ILASP
Clingo: 
Wij hebben clingo5 (v5.3) via conda gevonden. Deze, samen met de libraries, zitten ook in de repo onder de folder software. 
Kopieer clingo5 naar usr/bin/clingo5. 

De libraries: libclingo.so, libclingo.so.2 and libclingo.so.2.0 moeten naar /usr/lib gekopieerd worden.
(dit moeten deze versies zijn, nieuwere werken niet met de executable 'GGP_ILASP' van Cropper et al.)

ILASP:  
Wij hebben ILASP gedownload van http://ilasp.com/download en github en gebruikten 'ILASP version 3.4.0' (alles boven 3.x zou moeten werken).
Ook deze zit in de repo onder de folder software.
Kopieer deze naar usr/bin/ILASP.
Beide bestanden moeten wel executable zijn! (aan te passen via chmod 755 $file$)  


   
## Alle gebruikte software
1. SWIPL (zie https://www.swi-prolog.org/build/unix.html)
1. problog (te installeren via pip2)
1. Claudien (python implementatie van Anton Dries: https://bitbucket.org/antondries/claudien/src/master/ )
1. numpy (te installeren via pip3)
1. pyswip (te installeren via pip3)
1. python 2.7 (voor Claudien)
1. python 3
