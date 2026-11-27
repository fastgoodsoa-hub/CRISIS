"""Couverture complète KDP (4e + dos + 1re) — collection Synesis.

Usage :
  python3 couverture_kdp.py [livre=reussir|crisis] tome=1 pages=228 papier=blanc version=1 [texte4=...] [guides] [sortie=...]

- Format 6 x 9 po, fond perdu 0,125 po (haut, bas, bords extérieurs).
- Dos = pages x 0,002252 po (blanc) ou x 0,0025 po (crème).
- Le PDF final est aplati en une seule image à 600 ppp (évite les erreurs de traitement KDP
  sur les polices) ; l'option « guides » produit un aperçu avec coupe, zones de sécurité
  et zone code-barres (à ne jamais envoyer à KDP).
"""
import os, sys, subprocess, tempfile
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

ICI = os.path.dirname(os.path.abspath(__file__))
RAC = os.path.dirname(ICI)
args = dict(a.split('=', 1) for a in sys.argv[1:] if '=' in a)
GUIDES = 'guides' in sys.argv[1:]
LIVRE = args.get('livre', 'crisis')
TOME = int(args.get('tome', 1))
PAGES = int(args.get('pages', 228))
PAPIER = args.get('papier', 'blanc')
VERSION = args.get('version', '1')
GRAVURES = {'reussir': 'gravure_x4.png', 'crisis': 'gravure_cri_x4.png'}
GRAVURE = args.get('gravure', os.path.join(ICI, GRAVURES[LIVRE]))
TEXTE4 = args.get('texte4')            # fichier texte de la 4e (paragraphes séparés par une ligne vide)

# --- Charte -----------------------------------------------------------------
CREME = HexColor('#F9F7EA')
COULEURS = {('reussir', 1): '#E8A82D', ('reussir', 2): '#1F3A5F', ('crisis', 1): '#9E3B2C'}
BANDE = HexColor(args.get('couleur', COULEURS[(LIVRE, TOME)]))
NOIR = HexColor('#111111')
# Texte posé sur la bande : noir si la bande est claire, crème si elle est foncée (bleu nuit, etc.)
_lum = 0.2126 * BANDE.red + 0.7152 * BANDE.green + 0.0722 * BANDE.blue
SUR_BANDE = NOIR if _lum > 0.45 else CREME
AUTEUR = 'Paul DOURIS'
# Accroches (coupes de ligne choisies pour la colonne de gauche)
ACCROCHES = {
    1: ['Ce que disent plus de 50', 'sages, philosophes', 'et entrepreneurs,', 'de l\u2019Égypte des pharaons', 'à nos jours'],   # validée le 27 nov. 2026
    2: ['Ce que disent plus de 50', 'sages, philosophes,', 'entrepreneurs', 'et investisseurs,', 'de l\u2019Égypte des pharaons', 'à nos jours'],  # validée le 27 nov. 2026
}
ACCROCHES['crisis'] = ['Ce que nous apprennent', '4 500 ans de guerres,', 'de krachs et d\u2019épidémies,', 'de l\u2019Égypte des pharaons', 'à nos jours']   # proposition du 27 nov. 2026, à valider
ACCROCHE = ACCROCHES['crisis'] if LIVRE == 'crisis' else ACCROCHES[TOME]
# Titre (lignes, même corps), sous-titre, mention du tome, texte du dos, nom de fichier
PROFILS = {
    'reussir': dict(titre=['RÉUSSIR SA VIE', 'ET ÊTRE HEUREUX'], sous='Les leçons de 4 500 ans de sagesse', tome=True,
                    dos='RÉUSSIR SA VIE ET ÊTRE HEUREUX', nom=f'Couverture Tome {TOME} - Réussir sa vie et être heureux'),
    'crisis':  dict(titre=['CRISIS'], sous='Comment survivre à une crise ?', tome=False,
                    dos='CRISIS — COMMENT SURVIVRE À UNE CRISE ?', nom='Couverture - CRISIS, comment survivre à une crise'),
}
PR = PROFILS[LIVRE]
for f in ['RobotoCond-Black', 'RobotoCond-Bold', 'RobotoCond-Medium', 'RobotoSemiCond-Regular', 'RobotoSemiCond-Light', 'Roboto-Regular',
          'Roboto-Bold', 'Roboto-Italic', 'Roboto-BoldItalic']:
    pdfmetrics.registerFont(TTFont(f, os.path.join(ICI, 'fonts', f + '.ttf')))
from reportlab.lib.fonts import addMapping
addMapping('Roboto-Regular', 0, 0, 'Roboto-Regular'); addMapping('Roboto-Regular', 1, 0, 'Roboto-Bold')
addMapping('Roboto-Regular', 0, 1, 'Roboto-Italic'); addMapping('Roboto-Regular', 1, 1, 'Roboto-BoldItalic')

# --- Géométrie (pouces) -----------------------------------------------------
IN = 72.0
BL = 0.125
TW, TH = 6.0, 9.0
DOS = PAGES * (0.002252 if PAPIER == 'blanc' else 0.0025)
W = BL + TW + DOS + TW + BL
H = BL + TH + BL
X4 = BL                    # bord de coupe gauche de la 4e
XD = BL + TW               # début du dos
XF = BL + TW + DOS         # bord gauche (pli) de la 1re
YB = BL                    # bas de coupe
# Repères tirés du visuel Gemini (848 x 1264 px = 6 x 9 po)
def fx(px): return XF + px * TW / 848
def fy(py): return YB + TH - py * TH / 1264       # py compté depuis le haut
Y_BANDE = fy(622)
CAD = (fx(357), fy(1105), fx(782), fy(476))       # x0, y0, x1, y1 (cadre extérieur)
MARGE = 0.5                                        # marge texte depuis la coupe

def p(v): return v * IN

def texte_ajuste(c, txt, police, largeur, x, y, max_pt=200):
    """Écrit txt en ajustant le corps pour occuper « largeur » ; renvoie le corps."""
    pt = largeur * IN / pdfmetrics.stringWidth(txt, police, 1)
    pt = min(pt, max_pt)
    c.setFont(police, pt); c.drawString(p(x), p(y), txt)
    return pt

def espace(c, txt, police, pt, x, y, interlettre):
    c.saveState(); c.setFont(police, pt)
    t = c.beginText(p(x), p(y)); t.setCharSpace(interlettre); t.textLine(txt); c.drawText(t)
    c.restoreState()

def construire(sortie):
    c = canvas.Canvas(sortie, pagesize=(p(W), p(H)))
    c.setTitle(f"{PR['nom']} V{VERSION}")
    # Fonds : crème en haut, bande de couleur en bas, sur toute la couverture (4e, dos, 1re)
    c.setFillColor(CREME); c.rect(0, 0, p(W), p(H), stroke=0, fill=1)
    c.setFillColor(BANDE); c.rect(0, 0, p(W), p(Y_BANDE), stroke=0, fill=1)

    # ---------------- 1re de couverture ----------------
    c.setFillColor(NOIR)
    xg = XF + MARGE
    larg_titre = CAD[2] - xg
    espace(c, 'COLLECTION SYNESIS', 'RobotoCond-Bold', 8.5, xg, YB + TH - 0.55, 1.6)
    # Titre : toutes les lignes au même corps, calé sur la ligne la plus longue
    lignes = PR['titre']
    pt = larg_titre * IN / max(pdfmetrics.stringWidth(l, 'RobotoCond-Black', 1) for l in lignes)
    asc = pt * 0.711 / IN                          # hauteur de capitale Roboto
    y1 = YB + TH - 0.80 - asc
    lead = pt * 1.02 / IN
    c.setFont('RobotoCond-Black', pt)
    for i, l in enumerate(lignes):
        c.drawString(p(xg), p(y1 - i * lead), l)
    ysous = y1 - (len(lignes) - 1) * lead - 0.52
    texte_ajuste(c, PR['sous'], 'RobotoSemiCond-Regular', larg_titre, xg, ysous)
    if PR['tome']:                                 # TOME n, aligné sur le haut du cadre
        c.setFont('RobotoCond-Black', 24)
        c.drawString(p(xg), p(CAD[3] - 24 * 0.711 / IN), f'TOME {TOME}')
    # Accroche dans la colonne gauche de la bande
    c.setFillColor(SUR_BANDE)
    c.setFont('RobotoCond-Medium', 13)
    yac = Y_BANDE - 0.55
    for i, ligne in enumerate(ACCROCHE):
        c.drawString(p(xg), p(yac - i * 0.225), ligne)
    # Nom d'auteur, ligne de base sur le bas du cadre
    c.setFont('RobotoCond-Medium', 23)
    c.drawString(p(xg), p(CAD[1]), AUTEUR)
    c.setFillColor(NOIR)
    # Gravure + cadre
    c.drawImage(GRAVURE, p(CAD[0]), p(CAD[1]), p(CAD[2] - CAD[0]), p(CAD[3] - CAD[1]))
    ep = 6 * TW / 848                              # épaisseur du cadre d'origine (6 px)
    c.setStrokeColor(NOIR); c.setLineWidth(p(ep))
    c.rect(p(CAD[0] + ep / 2), p(CAD[1] + ep / 2), p(CAD[2] - CAD[0] - ep), p(CAD[3] - CAD[1] - ep), stroke=1, fill=0)

    # ---------------- Dos (lecture de bas en haut) ----------------
    # Le texte du dos traverse la limite crème / bande : on le trace deux fois, découpé par zone.
    for couleur, y0, y1 in ((NOIR, Y_BANDE, H), (SUR_BANDE, 0, Y_BANDE)):
        c.saveState()
        zone = c.beginPath(); zone.rect(p(XD), p(y0), p(DOS), p(y1 - y0)); c.clipPath(zone, stroke=0, fill=0)
        c.translate(p(XD + DOS / 2), p(YB))
        c.rotate(90)                               # x = vers le haut, y = vers la 4e
        corps = 12.5
        base = -corps * 0.711 / 2                  # capitales centrées sur l'axe du dos
        c.setFillColor(couleur)
        pos = 0.40
        c.setFont('RobotoCond-Medium', corps); c.drawString(p(pos), base, AUTEUR)
        pos += pdfmetrics.stringWidth(AUTEUR, 'RobotoCond-Medium', corps) / IN + 0.35
        titre = PR['dos']
        c.setFont('RobotoCond-Black', corps); c.drawString(p(pos), base, titre)
        pos += pdfmetrics.stringWidth(titre, 'RobotoCond-Black', corps) / IN + 0.25
        if PR['tome']:
            c.drawString(p(pos), base, f'TOME {TOME}')
        syn = 'SYNESIS'
        c.setFont('RobotoCond-Bold', 9)
        t = c.beginText(p(TH - 0.40) - pdfmetrics.stringWidth(syn, 'RobotoCond-Bold', 9) - 6 * 1.2, -9 * 0.711 / 2)
        t.setCharSpace(1.2); t.textLine(syn); c.drawText(t)
        c.restoreState()

    # ---------------- 4e de couverture ----------------
    c.setFillColor(SUR_BANDE)
    espace(c, 'COLLECTION SYNESIS', 'RobotoCond-Bold', 8.5, X4 + MARGE, YB + 0.5, 1.6)
    if TEXTE4:
        # Texte en deux blocs séparés par une ligne « --- » : le premier sur le crème, le second sur la bande.
        from reportlab.platypus import Paragraph, Frame
        from reportlab.lib.styles import ParagraphStyle
        accroche4 = ParagraphStyle('a', fontName='Roboto-Regular', fontSize=13, leading=17, spaceAfter=10, textColor=NOIR)
        corps4 = ParagraphStyle('t', fontName='Roboto-Regular', fontSize=11, leading=15.3, spaceAfter=7, textColor=NOIR)
        corps4b = ParagraphStyle('tb', parent=corps4, textColor=SUR_BANDE)
        haut, bas = open(TEXTE4, encoding='utf-8').read().split('\n---\n')
        def paras(bloc, premier_style, suite=corps4):
            out = []
            for i, b in enumerate([b for b in bloc.split('\n\n') if b.strip()]):
                out.append(Paragraph(b.strip().replace('\n', ' '), premier_style if i == 0 else suite))
            return out
        x, w = X4 + MARGE, TW - 2 * MARGE
        cadres = [
            (Frame(p(x), p(Y_BANDE + 0.22), p(w), p(YB + TH - 0.6 - (Y_BANDE + 0.22)), leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0), paras(haut, accroche4)),
            (Frame(p(x), p(YB + 1.75), p(w), p(Y_BANDE - 0.35 - (YB + 1.75)), leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0), paras(bas, corps4b, corps4b)),
        ]
        for fr, contenu in cadres:
            fr.addFromList(contenu, c)
            if contenu:
                sys.exit(('Bloc du haut' if fr is cadres[0][0] else 'Bloc du bas') + ' : texte de 4e trop long, ' + str(len(contenu)) + ' paragraphe(s) en trop.')

    if GUIDES:
        c.setLineWidth(0.6)
        c.setStrokeColor(HexColor('#E0007A'))       # coupe
        c.rect(p(BL), p(BL), p(W - 2 * BL), p(TH))
        c.line(p(XD), 0, p(XD), p(H)); c.line(p(XF), 0, p(XF), p(H))
        c.setStrokeColor(HexColor('#00A0E0')); c.setDash(3, 3)   # zones de sécurité 0,125 po
        s = 0.125
        c.rect(p(X4 + s), p(YB + s), p(TW - 2 * s), p(TH - 2 * s))
        c.rect(p(XF + s), p(YB + s), p(TW - 2 * s), p(TH - 2 * s))
        c.rect(p(XD + 0.0625), p(YB + s), p(DOS - 0.125), p(TH - 2 * s))
        c.setDash(); c.setStrokeColor(HexColor('#E0007A')); c.setFillColor(HexColor('#FFFFFF'))
        bx, by = XD - 0.25 - 2.0, YB + 0.25         # zone code-barres KDP 2 x 1,2 po
        c.rect(p(bx), p(by), p(2.0), p(1.2), fill=1)
        c.setFillColor(HexColor('#E0007A')); c.setFont('Roboto-Regular', 8)
        c.drawCentredString(p(bx + 1.0), p(by + 0.55), 'Zone code-barres (KDP)')
    c.showPage(); c.save()

def aplatir(vecto, sortie, dpi=600):
    from PIL import Image
    Image.MAX_IMAGE_PIXELS = None
    with tempfile.TemporaryDirectory() as d:
        subprocess.run(['pdftoppm', '-r', str(dpi), '-png', '-singlefile', vecto, os.path.join(d, 'r')], check=True)
        im = Image.open(os.path.join(d, 'r.png')).convert('RGB')
        c = canvas.Canvas(sortie, pagesize=(p(W), p(H)))
        c.setTitle(f"{PR['nom']} V{VERSION}")
        png = os.path.join(d, 'flat.png'); im.save(png, optimize=True)
        c.drawImage(png, 0, 0, p(W), p(H)); c.showPage(); c.save()
    nettoyer(sortie)
    return im.size

def nettoyer(f):
    """Retire la police Helvetica non incorporée que ReportLab déclare par défaut."""
    import pikepdf
    pdf = pikepdf.open(f, allow_overwriting_input=True)
    noop = b'BT /F1 12 Tf 14.4 TL ET'
    for pg in pdf.pages:
        for s in (pg.Contents if isinstance(pg.Contents, pikepdf.Array) else [pg.Contents]):
            r = s.read_bytes()
            if noop in r: s.write(r.replace(noop, b''))
        fonts = pg.Resources.get('/Font')
        if fonts is not None and '/F1' in fonts: del fonts['/F1']
    pdf.remove_unreferenced_resources(); pdf.save(f)

if __name__ == '__main__':
    nom = args.get('sortie') or os.path.join(ICI, '..', '..', 'pdf',
        f"{PR['nom']} V{VERSION}" + (' - GUIDES' if GUIDES else '') + '.pdf')
    os.makedirs(os.path.dirname(nom), exist_ok=True)
    if os.path.exists(nom):
        sys.exit(f'Refus : {nom} existe déjà (ne jamais écraser un fichier livré).')
    vec = nom.replace('.pdf', ' (vectoriel).pdf')
    construire(vec)
    if GUIDES:
        os.rename(vec, nom)
    else:
        print('pixels', aplatir(vec, nom)); os.remove(vec)
    print(f'{nom}\n{W:.4f} x {H:.4f} po = {W*25.4:.1f} x {H*25.4:.1f} mm ; dos {DOS:.4f} po = {DOS*25.4:.2f} mm')
