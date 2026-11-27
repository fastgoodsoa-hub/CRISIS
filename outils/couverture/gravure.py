"""Extrait la gravure du visuel Gemini, l'agrandit x4 et la passe en noir pur sur crème.
Usage : python3 gravure.py base.jpg sortie.png [pythagore|cri]"""
import sys
import numpy as np, cv2
from PIL import Image

src, dst = sys.argv[1], sys.argv[2]
SUJET = sys.argv[3] if len(sys.argv) > 3 else 'pythagore'
g = np.asarray(Image.open(src).convert('L')).astype(np.float32)
# intérieur du cadre (cadre redessiné en vectoriel) ; même gabarit Gemini 848 x 1264 pour les deux visuels
x0, x1, y0, y1 = (364, 776, 483, 1100) if SUJET == 'pythagore' else (364, 776, 487, 1100)
g = g[y0:y1, x0:x1]
S = 4
big = cv2.resize(g, None, fx=S, fy=S, interpolation=cv2.INTER_LANCZOS4)
big = cv2.GaussianBlur(big, (0, 0), 1.6)
ink = big < 128                                 # trait noir
# Artefact Gemini : pictogramme de main (curseur) dessiné sur la page du livre.
# Coordonnées dans le visuel d'origine, converties dans l'agrandissement.
def orig(x, y): return (int((x - x0) * S), int((y - y0) * S))
poly = np.array([orig(*p) for p in [(626, 642), (640, 633), (651, 636), (661, 652), (659, 668), (646, 675), (632, 672), (624, 660)]], np.int32)
mask = np.zeros(ink.shape, np.uint8); cv2.fillPoly(mask, [poly], 1)
if SUJET == 'pythagore':
    ink[mask.astype(bool)] = False
# petits points isolés (bruit JPEG)
n, lab, st, _ = cv2.connectedComponentsWithStats(ink.astype(np.uint8), 8)
small = st[:, cv2.CC_STAT_AREA] < 6; small[0] = False
ink[small[lab]] = False
creme = np.array([249, 247, 234], np.uint8)
out = np.where(ink[..., None], np.uint8(0), creme)
Image.fromarray(out.astype(np.uint8)).save(dst)
print(dst, out.shape)
