# CRISIS — Comment survivre à une crise ? — mode d'emploi du dépôt

Livre de Rudy Martin, publié sous le pseudonyme Paul Douris, dans la collection Synesis (comme « Réussir sa vie et être heureux », dépôt séparé `4500-ans-de-sagesse` : ne pas mélanger les deux livres). Tout le travail se fait en français ; tutoyer Rudy.

## Contenu

- `projet/plan.md` : grille commune des chapitres et plan (Introduction, Parties I à III, 20 chapitres, conclusion, annexes), transmis le 27 nov. 2026.
- `outils/couverture/` : couverture complète KDP (4e + dos + 1re, 6 × 9 po, fond perdu 0,125 po, dos = pages × 0,002252 po en blanc ou × 0,0025 po en crème). `python3 couverture_kdp.py pages=N papier=blanc version=V [texte4=textes/….txt] [guides]` produit `pdf/Couverture - CRISIS, comment survivre à une crise VV.pdf`, aplati à 600 ppp ; refuse d'écraser un fichier existant. Même mise en page que « Réussir sa vie » : haut crème, bande rouge brique (#9E3B2C) avec texte crème, dessin du Cri de Munch (domaine public) encadré à droite, issu d'un visuel Gemini (`gravure.py … cri`), Roboto condensé.
- `outils/couverture/textes/` : textes de 4e (V2 du 27 nov. 2026, durée « 3 200 ans » validée : la crise la plus ancienne du plan est l'effondrement de l'âge du bronze). Accroche de la 1re dans `couverture_kdp.py` (ACCROCHES['crisis'] : « …de l'âge du bronze à nos jours », V3 du 27 nov. 2026).
- `pdf/` : couvertures produites.

## Règles

- Ne jamais écraser un fichier livré : numéro de version dans le nom de chaque fichier.
- Texte de 4e de couverture : le soumettre à Rudy avant de le poser ; pas d'œuvre protégée citée, pas de promesse de résultat.
- Le dos est provisoire (228 pages) tant que le nombre de pages n'est pas connu.

## Après chaque modification

Faire un commit et le pousser sur `main`.
