# -*- coding: utf-8 -*-
#
# Pool, due giocatori sullo stesso PC. Per ora si gioca a 8-ball.
# Richiede solo pygame:  pip install pygame
#
#   ESC         dal tavolo apre la pausa, dal menu esce
#   F11         tutto schermo
#   mira        muovi il mouse
#   tira        tieni premuto il sinistro e trascina indietro: piu'
#               vai indietro piu' carichi, torni avanti e scarichi.
#               Rilasci e parte.
#   effetto     W / S  sopra-sotto,  A / D  laterale,  E  azzera
#   palla in mano  dopo un fallo: muovi il mouse e clicca per posare
#   ESC         esci
#
# Cartelle accanto a questo file:
#   biliardo_gfx    le PNG delle palle e della stecca
#   biliardo_audio  le tracce (.ogg .mp3 .wav .flac): a ogni partita ne
#                   parte una a caso e va in loop fino a fine partita
#   biliardo_fx     gli effetti, presi dall'inizio del nome del file:
#                   cue... la stecca, ball... palla contro palla,
#                   rail... la sponda, pocket... la palla in buca.
#                   Piu' file dello stesso tipo: il numero nel nome li
#                   mette in fila dal piano al forte (ball_1_leggero,
#                   ball_2_medio...) e si sceglie in base alla botta
#
import copy
import json
import math
import os
import random
import shutil
import sys

import pygame
from pygame import gfxdraw
from pygame.math import Vector2

try:
    import numpy as np
    HA_NUMPY = True
except ImportError:                 # senza numpy si ripiega sul disegno piatto
    HA_NUMPY = False

# ----------------------------------------------------------------- misure
#
# Il tavolo e' un disegno tuo, biliardo_gfx/tavolo.png. Le misure del
# gioco non le decido io: le leggo dalla figura. Le sei buche nere della
# PNG sono state misurate una volta sola e i numeri stanno qui sotto,
# in pixel della figura originale.

TAV_FILE = "table_new.png"
# La linea di partenza: nel disegno del tavolo c'e' gia', a 434 pixel e
# mezzo sull'immagine. Qui e' la stessa, in frazione del campo, cosi' la
# D dello snooker ci va sopra invece di farne una seconda.
BAULK = 0.2493
RAGGIO_D = 0.1710               # il semicerchio, in frazione dell'altezza
# Il disegno del tavolo, uno per disciplina: i birilli giocano su quello
# senza buche, tutti gli altri su quello con le buche.
TAV_FILE_DI = ("table_new.png", "table_new.png", "table_new.png",
               "table_new_5pins.png", "table_new.png", "table_new.png",
               "table_new.png", "table_new_5pins.png", "table_new.png")
TAV_W, TAV_H = 1521.0, 895.0            # quanto misura la PNG
# centri delle sei buche nere, misurati sulla figura
TAV_BUCHE = ((142.5, 136.5), (758.0, 116.5), (1373.5, 136.5),
             (142.5, 759.5), (758.0, 779.0), (1373.5, 759.5))
TAV_R_ANG = 27.0                        # raggio del nero, buca d'angolo
TAV_R_MID = 21.5                        # raggio del nero, buca centrale

# Il campo di gioco e' dove batte la biglia, cioe' il filo della sponda,
# misurato sulla figura: viene 1410 x 704, rapporto 2,003. I centri delle
# buche stanno una ventina di pixel piu' in fuori, dentro la sponda.
TAV_PLAY = (150.5, 144.5, 1365.5, 751.5)
TAV_GOMMA = 24.5                        # la fascia di gomma, sulla figura

# ------------------------------------------------------------ la misura
#
# Il gioco e' disegnato su 1280 per 820: quello e' il disegno di
# partenza, la misura uno. Scegliendo una risoluzione piu' grande il
# disegno non si stira, si rifa' piu' grande: ogni numero passa per K e
# le scritte vengono disegnate grandi invece che ingrandite dopo. E'
# l'unica cura vera per la sgranatura sugli schermi fitti, dove il
# sistema moltiplica per conto suo quello che gli diamo.
#
# Queste misure si calcolano una volta sola, all'avvio, quindi la
# risoluzione bisogna saperla prima di tutto il resto: il file delle
# impostazioni si legge qui, prima delle costanti.
BASE_W, BASE_H = 1280, 820
RISOLUZIONI = ((1280, 820), (1600, 1000), (1920, 1200), (2304, 1296),
               (2560, 1440), (3200, 1800), (3840, 2160))


def cartella_dati():
    """Dove stanno le cose del giocatore (impostazioni, portafoglio,
    stecche comprate, torneo in corso): fuori dalla cartella del gioco,
    nella cartella dati dell'utente. Windows: AppData, Mac: Application
    Support, Linux: ~/.local/share. La prima volta ci sposta i file che
    stavano ancora accanto al gioco."""
    if sys.platform.startswith("win"):
        base = os.environ.get("APPDATA") or os.path.expanduser("~")
    elif sys.platform == "darwin":
        base = os.path.expanduser("~/Library/Application Support")
    else:
        base = os.environ.get("XDG_DATA_HOME") or \
            os.path.expanduser("~/.local/share")
    dove = os.path.join(base, "ClassicPool")
    try:
        os.makedirs(dove, exist_ok=True)
    except OSError:
        return os.path.dirname(os.path.abspath(__file__))
    vecchia = os.path.dirname(os.path.abspath(__file__))
    for nome in ("biliardo_config.json", "biliardo_torneo.json"):
        prima, dopo = os.path.join(vecchia, nome), os.path.join(dove, nome)
        if os.path.exists(prima) and not os.path.exists(dopo):
            try:
                shutil.move(prima, dopo)
            except OSError:
                pass
    return dove


DATI = cartella_dati()


def _misura_salvata():
    try:
        f = os.path.join(DATI, "biliardo_config.json")
        with open(f, "r") as q:
            d = json.load(q)
        v = d.get("risoluzione")
        if isinstance(v, (list, tuple)) and len(v) == 2:
            w, h = int(v[0]), int(v[1])
            if w >= BASE_W and h >= BASE_H:
                return w, h
    except (IOError, ValueError, TypeError, KeyError):
        pass
    return BASE_W, BASE_H


WIN_W, WIN_H = _misura_salvata()
# Il disegno non si deforma mai: si prende il fattore piu' piccolo fra i
# due, cosi' ci sta tutto e semmai avanza dello spazio ai lati, che e'
# fondo e non nero.
K = min(WIN_W / float(BASE_W), WIN_H / float(BASE_H))


def s(v):
    """Un numero del disegno di partenza, portato alla misura scelta."""
    return int(round(v * K))


# La finestra non dipende dal tavolo: e' fissa. Se cambia la misura del
# tavolo, il tavolo si sposta al centro dello spazio libero e la fascia
# dei comandi resta dov'e'. Prima erano legate, e rimpicciolendo il
# tavolo si schiacciavano potenza ed effetto.
ALTO = s(44)                    # in cima resta solo la riga del messaggio
FASCIA = s(120)                 # sotto: le due strisce e la riga dei comandi
BASSO = WIN_H - FASCIA          # dove finisce il tavolo e comincia l'HUD

# Le due strisce in fondo allo schermo, una sull'altra e della stessa
# altezza: sopra il punteggio, sotto le palle gia' imbucate. Sono larghe
# quanto la finestra, non quanto il tavolo, come quelle della tele.
BANDA_H = s(38)
BANDA_STACCO = max(1, s(4))     # il filo scuro fra una e l'altra
PIEDE = s(28)                   # la riga dei comandi, in fondo e in mezzo
BANDA_PALLE = pygame.Rect(0, WIN_H - PIEDE - BANDA_H, WIN_W, BANDA_H)
BANDA_PUNTI = pygame.Rect(0, BANDA_PALLE.top - BANDA_STACCO - BANDA_H,
                          WIN_W, BANDA_H)

# Quanto largo viene il campo di gioco sullo schermo. E' l'unica manopola
# per cambiare il rapporto fra tavolo e bilie: la bilia resta quella che
# e', quindi rimpicciolire il campo vuol dire palle piu' grandi rispetto
# al tavolo. Alla misura vera (1080) il tavolo e' lungo 39 bilie.
CAMPO_W = 950.0 * K
SCALA = CAMPO_W / (TAV_PLAY[2] - TAV_PLAY[0])  # quanto rimpicciolire la PNG
# Quanto del disegno si vede davvero: la PNG ha del vuoto attorno, e
# centrando la figura intera il tavolo finiva addosso alla fascia dei
# nomi. Si centra quello che si vede.
TAV_VISTA = (63.0, 56.0, 1391.0, 784.0)         # x, y, largo, alto
TAV_POS = (int((WIN_W - TAV_VISTA[2] * SCALA) / 2.0 - TAV_VISTA[0] * SCALA),
           int(ALTO + (BASSO - ALTO - TAV_VISTA[3] * SCALA) / 2.0
               - TAV_VISTA[1] * SCALA))

PLAY = pygame.Rect(0, 0, 1, 1)
PLAY.left = int(TAV_POS[0] + TAV_PLAY[0] * SCALA)
PLAY.top = int(TAV_POS[1] + TAV_PLAY[1] * SCALA)
PLAY.width = int((TAV_PLAY[2] - TAV_PLAY[0]) * SCALA)
PLAY.height = int((TAV_PLAY[3] - TAV_PLAY[1]) * SCALA)

RAIL = int((TAV_PLAY[0] - 5.0) * SCALA)        # legno dal filo al bordo

# La bilia non segue piu' il campo: resta di questa misura, cosi'
# rimpicciolendo il tavolo le palle diventano piu' grandi in proporzione.
# Il raggio della palla, in pixel di gioco. Una palla da pool e'
# larga 5,72 cm e il campo 224: su novecentocinquanta pixel di
# campo fanno 12,1 di raggio. Tutto il resto - triangolo, rombo,
# snooker, fisica - e' calcolato da qui.
BALL_R = 5.715 / 2.0 * (TAV_PLAY[2] - TAV_PLAY[0]) / 254.0 * SCALA
BALL_R_BASE = BALL_R
PALLE_PIRAMIDE = 1.10   # alla piramide russa le palle sono un po' piu' grosse
CM = PLAY.w / 254.0             # serve solo alle misure scritte
GOMMA = TAV_GOMMA * SCALA       # la fascia di gomma, in pixel gioco
# quanto viene grande un quadretto di texture. Il panno si piastrella
# sulla PNG a misura vera, non sullo schermo: il quadretto e' in pixel
# dell'immagine, gli stessi che si contano aprendola col programma di
# disegno.
LATO_PANNO = 125
LATO_LEGNO = 220

# Dove si stende il panno sulla figura: fin dove arriva la gomma della
# sponda e non un pixel piu' in la'. Nella PNG la gomma e' la fascia
# grigia a meta' trasparenza, larga diciotto pixel: sopra da 65 a 82,
# sotto da 789 a 806, a sinistra da 66 a 83, a destra da 1496 a 1513.
# Il legno resta di fuori, nella cornice dei diamanti.
PANNO_SU = pygame.Rect(126, 120, 1264, 656)

# La sagoma del tavolo dentro la figura: non e' un quadrato, i quattro
# angoli sono tagliati a quarantacinque gradi. Il disegno arriva da 5 a
# 1574 in larghezza e da 4 a 867 in altezza, e il taglio e' lungo 44
# pixel per lato. Il legno si ferma qui, se no sborda negli angoli.
# Il legno era largo 64 pixel della figura: se ne toglie meta' dal
# filo esterno, la gomma e il panno restano dove sono.
LEGNO_STRINGI = 32
LEGNO_SU = pygame.Rect(*[int(v) for v in TAV_VISTA]).inflate(
    -2 * LEGNO_STRINGI, -2 * LEGNO_STRINGI)
LEGNO_RAGGIO = 26               # gli angoli del tavolo sono tondi

# Le due strisce del punteggio, sotto, larghe quanto il tavolo e non
# quanto la finestra: stanno in colonna col legno.
for _banda in (BANDA_PUNTI, BANDA_PALLE):
    _banda.left = int(TAV_POS[0] + LEGNO_SU.x * SCALA)
    _banda.width = int(LEGNO_SU.w * SCALA)

# Le buche del gioco: quelle della figura, portate in scala.
BUCHE = [Vector2(TAV_POS[0] + bx * SCALA, TAV_POS[1] + by * SCALA)
         for bx, by in TAV_BUCHE]
R_ANG = TAV_R_ANG * SCALA               # il nero disegnato, in pixel gioco
R_MID = TAV_R_MID * SCALA
# La palla e' presa quando il centro entra nel nero per due terzi buoni:
# cosi' quello che vedi e quello che succede sono la stessa cosa.
# Le buche del disegno sono strette rispetto alla palla, percio' presa
# e varco non si prendono dal disegno ma dalla palla: se no una palla
# che arriva in bocca rimbalza sulle punte invece di cadere dentro.
PRESA_ANG = max(R_ANG * 0.72, BALL_R * 1.02)
PRESA_MID = max(R_MID * 0.72, BALL_R * 1.02)
PRESA = [PRESA_ANG, PRESA_MID, PRESA_ANG,
         PRESA_ANG, PRESA_MID, PRESA_ANG]
PRESA_R = PRESA_ANG                     # il valore d'angolo, per le regole
# La rete di sicurezza lavora con una presa piu' larga: una palla che ha
# gia' passato il filo della sponda dentro la bocca e' entrata, anche se
# non e' ancora arrivata al centro del nero. Se no sulle centrali, che
# stanno piu' in fuori, le palle lente rimbalzavano indietro.
PRESA_FUORI = [max(pr * 1.4, r + BALL_R) for pr, r in
               zip(PRESA, (R_ANG, R_MID, R_ANG, R_ANG, R_MID, R_ANG))]

# Dove la sponda e' interrotta, misurato lungo il filo. I due primi
# numeri sono sulla figura, prima di ridurla: servono anche all'ombra,
# che si disegna sulla PNG a misura piena.
VARCO_FIG = 33.5                   # dove la sponda si interrompe, d'angolo
VARCO_MID_FIG = 27.5               # e alla buca centrale
VARCO = VARCO_FIG * SCALA
VARCO_MID = VARCO_MID_FIG * SCALA
VARCO_X = (PLAY.left, PLAY.centerx, PLAY.right)
VARCO_Y = (PLAY.top, PLAY.bottom)

LINEA_X = PLAY.left + PLAY.w * 0.25
PALLINO = Vector2(PLAY.left + PLAY.w * 0.75, PLAY.centery)

# fisica
# Il panno frena con una decelerazione costante, non con uno smorzamento
# percentuale: una palla che rotola perde tot velocita' al secondo, sempre
# la stessa. Con lo smorzamento percentuale la coda finale si trascinava
# all'infinito e i tiri forti morivano troppo presto.
# Il tavolo e' largo 1080 px per circa 2 metri veri, quindi 545 px = 1 m.
# Il panno vero frena una palla che rotola di circa 0.3 m/s^2: qui fanno
# 175 px/s^2. Prima erano 340, cioe' il doppio del vero, ed era per quello
# che dopo una spaccata le palle si piantavano quasi subito.
# Il panno frena in due modi, e sono misure vere. Una palla che rotola
# perde pochissimo: il coefficiente di rotolamento sul panno e' 0,01,
# cioe' 9,8 cm al secondo quadrato. Una palla che striscia, appena
# colpita, perde venti volte tanto: 196 cm/s^2. Qui sono in pixel, con
# 950 px ogni 254 cm.
# Sono in pixel al secondo: se il disegno cresce crescono con lui,
# cosi' la partita e' identica a qualunque risoluzione.
DECEL = 36.7 * K               # rotolamento: 9,8 cm/s^2
DECEL_SCIVOLO = 733.0 * K      # strisciamento: 196 cm/s^2
FERMA = 2.646 * K              # sotto questa velocita' la palla si ferma
REST_PALLA = 0.97              # elasticita' palla contro palla
REST_SPONDA = 0.78             # elasticita' palla contro sponda, di fronte
REST_LATO = 0.90               # e quanto le resta della velocita' di lato
TIRO_MAX = 2292.9 * K          # velocita' massima della stecca
TRASCINO = 229.3 * K           # px da tirare indietro, potenza massima
# La mira col mouse, e non ci sono scalini fra i due modi. Fin sotto
# SALTO_PIANO pixel di spostamento conta solo il movimento di traverso,
# e ogni pixel gira la mira come se il mouse stesse in punta a un
# braccio lungo BRACCIO_MIRA: e' la mira fine. Sopra SALTO_MIRA la mira
# va dove punti. Fra i due valori si mescolano, cosi' la stecca gira
# sempre continua e non salta da una palla all'altra.
SALTO_PIANO = 3.0 * K          # sotto questo, la mira e' solo fine
SALTO_MIRA = 26.0 * K          # sopra questo, la mira va dove punti
BRACCIO_MIRA = 1150.0 * K


def spinta(potenza):
    """Dalla barra alla velocita' vera. Non e' una riga dritta: elevando
    a uno e mezzo la meta' bassa della barra si allarga, cosi' i colpi
    di tocco si dosano invece di partire tutti forti. In cima la barra
    piena resta la botta piena."""
    return max(0.0, min(1.0, potenza)) ** 1.5


# ----------------------------------------------------------------- colori

# I panni e i legni sono file veri, dentro biliardo_gfx/panni e
# biliardo_gfx/bordi. L'elenco si costruisce da solo leggendo la cartella:
# aggiungi un file e compare fra le scelte, senza toccare il codice.
# Il nome che si legge nelle impostazioni viene dal nome del file.

def _bel_nome(f):
    n = os.path.splitext(f)[0].lower()
    for via in ("panno-biliardo-", "panno-", "-go-7", "-go"):
        n = n.replace(via, "")
    pezzi = [x for x in n.split("-") if x and not (len(x) <= 2 and
             (x.isdigit() or x.isalpha()))]
    return " ".join(pezzi).strip().capitalize() or n


# I nomi dei materiali nelle cinque lingue, nell'ordine di LINGUE:
# inglese, italiano, francese, spagnolo, giapponese. La chiave e' un
# pezzo del nome del file, quello piu' lungo che ci sta dentro: cosi' i
# file restano come sono e a schermo si legge nella lingua giusta.
NOMI_TEX = {
    # i panni
    "verde": ("Green", "Verde", "Vert", "Verde",
              "\u30b0\u30ea\u30fc\u30f3"),
    "verde-erba": ("Grass green", "Verde erba", "Vert gazon",
                   "Verde hierba", "\u30b0\u30e9\u30b9\u30b0\u30ea\u30fc\u30f3"),
    "verde-2": ("Emerald", "Smeraldo", "\u00c9meraude", "Esmeralda",
                "\u30a8\u30e1\u30e9\u30eb\u30c9"),
    "verde-3": ("Teal", "Verde petrolio", "Bleu canard", "Verde azulado",
                "\u30c6\u30a3\u30fc\u30eb"),
    "verde-impero": ("Empire green", "Verde impero", "Vert empire",
                     "Verde imperio",
                     "\u30a8\u30f3\u30d1\u30a4\u30a2\u30b0\u30ea\u30fc\u30f3"),
    "verde-muschio": ("Moss green", "Verde muschio", "Vert mousse",
                      "Verde musgo",
                      "\u30e2\u30b9\u30b0\u30ea\u30fc\u30f3"),
    "verde-oliva": ("Olive", "Verde oliva", "Vert olive", "Verde oliva",
                    "\u30aa\u30ea\u30fc\u30d6"),
    "blu": ("Blue", "Blu", "Bleu", "Azul", "\u30d6\u30eb\u30fc"),
    "azzurro": ("Azure", "Azzurro", "Azur", "Azul celeste",
                "\u30a2\u30b8\u30e5\u30fc\u30eb"),
    "celeste": ("Sky blue", "Celeste", "Bleu ciel", "Celeste",
                "\u30b9\u30ab\u30a4\u30d6\u30eb\u30fc"),
    "carta-da-zucchero": ("Powder blue", "Carta da zucchero",
                          "Bleu poudre", "Azul empolvado",
                          "\u30d1\u30a6\u30c0\u30fc\u30d6\u30eb\u30fc"),
    "viola": ("Purple", "Viola", "Violet", "Morado",
              "\u30d1\u30fc\u30d7\u30eb"),
    "lilla": ("Lilac", "Lilla", "Lilas", "Lila",
              "\u30e9\u30a4\u30e9\u30c3\u30af"),
    "rosso-ferrari": ("Racing red", "Rosso Ferrari", "Rouge course",
                      "Rojo carreras",
                      "\u30ec\u30fc\u30b7\u30f3\u30b0\u30ec\u30c3\u30c9"),
    "rosso-antico": ("Antique red", "Rosso antico", "Rouge antique",
                     "Rojo antiguo",
                     "\u30a2\u30f3\u30c6\u30a3\u30fc\u30af\u30ec\u30c3\u30c9"),
    "vinaccia": ("Wine", "Vinaccia", "Lie de vin", "Vino",
                 "\u30ef\u30a4\u30f3\u30ec\u30c3\u30c9"),
    "ruggine": ("Rust", "Ruggine", "Rouille", "\u00d3xido",
                "\u30e9\u30b9\u30c8"),
    "arancione": ("Orange", "Arancione", "Orange", "Naranja",
                  "\u30aa\u30ec\u30f3\u30b8"),
    "senape": ("Mustard", "Senape", "Moutarde", "Mostaza",
               "\u30de\u30b9\u30bf\u30fc\u30c9"),
    "camel-13": ("Tan", "Cuoio", "Fauve", "Cuero",
                 "\u30bf\u30f3"),
    "camel": ("Camel", "Cammello", "Camel", "Camello",
              "\u30ad\u30e3\u30e1\u30eb"),
    "sabbia": ("Sand", "Sabbia", "Sable", "Arena",
               "\u30b5\u30f3\u30c9"),
    "marrone": ("Brown", "Marrone", "Marron", "Marr\u00f3n",
                "\u30d6\u30e9\u30a6\u30f3"),
    "grigio-chiaro": ("Light grey", "Grigio chiaro", "Gris clair",
                      "Gris claro",
                      "\u30e9\u30a4\u30c8\u30b0\u30ec\u30fc"),
    "nero": ("Black", "Nero", "Noir", "Negro",
             "\u30d6\u30e9\u30c3\u30af"),
    # i legni
    "bamboo": ("Bamboo", "Bamb\u00f9", "Bambou", "Bamb\u00fa",
               "\u7af9"),
    "castagno": ("Chestnut", "Castagno", "Ch\u00e2taignier", "Casta\u00f1o",
                 "\u6817"),
    "ciliegio": ("Cherry", "Ciliegio", "Merisier", "Cerezo",
                 "\u30c1\u30a7\u30ea\u30fc"),
    "ebano": ("Ebony", "Ebano", "\u00c9b\u00e8ne", "\u00c9bano",
              "\u9ed2\u6a80"),
    "faggio": ("Beech", "Faggio", "H\u00eatre", "Haya", "\u30d6\u30ca"),
    "frassino": ("Ash", "Frassino", "Fr\u00eane", "Fresno",
                 "\u30a2\u30c3\u30b7\u30e5"),
    "mogano": ("Mahogany", "Mogano", "Acajou", "Caoba",
               "\u30de\u30db\u30ac\u30cb\u30fc"),
    "noce-americano": ("American walnut", "Noce americano",
                       "Noyer am\u00e9ricain", "Nogal americano",
                       "\u30a6\u30a9\u30eb\u30ca\u30c3\u30c8"),
    "noce-italiano": ("Italian walnut", "Noce italiano", "Noyer italien",
                      "Nogal italiano",
                      "\u30a4\u30bf\u30ea\u30a2\u30f3\u30a6\u30a9\u30eb\u30ca\u30c3\u30c8"),
    "olmo": ("Elm", "Olmo", "Orme", "Olmo", "\u30cb\u30ec"),
    "palissandro": ("Rosewood", "Palissandro", "Palissandre", "Palisandro",
                    "\u30ed\u30fc\u30ba\u30a6\u30c3\u30c9"),
    "quercia": ("Oak", "Quercia", "Ch\u00eane", "Roble",
                "\u30aa\u30fc\u30af"),
    "rovere": ("Durmast", "Rovere", "Rouvre", "Roble albar",
               "\u30ca\u30e9"),
    "ulivo": ("Olive wood", "Ulivo", "Olivier", "Olivo",
              "\u30aa\u30ea\u30fc\u30d6\u6750"),
    "wenge": ("Wenge", "Weng\u00e8", "Weng\u00e9", "Wengu\u00e9",
              "\u30a6\u30a7\u30f3\u30b8"),
    "zebrano": ("Zebrawood", "Zebrano", "Z\u00e9brano", "Cebrano",
                "\u30bc\u30d6\u30e9\u30a6\u30c3\u30c9"),
    # le laccature e i materiali moderni
    "9001": ("Cream white", "Bianco crema", "Blanc cr\u00e8me",
             "Blanco crema",
             "\u30af\u30ea\u30fc\u30e0\u30db\u30ef\u30a4\u30c8"),
    "ral-9010": ("Pure white", "Bianco puro", "Blanc pur", "Blanco puro",
                 "\u30d4\u30e5\u30a2\u30db\u30ef\u30a4\u30c8"),
    "bianco-perlato": ("Pearl white", "Bianco perlato", "Blanc nacr\u00e9",
                       "Blanco perlado",
                       "\u30d1\u30fc\u30eb\u30db\u30ef\u30a4\u30c8"),
    "grigio": ("Grey", "Grigio", "Gris", "Gris", "\u30b0\u30ec\u30fc"),
    "nero-sfumato": ("Shaded black", "Nero sfumato", "Noir d\u00e9grad\u00e9",
                     "Negro degradado",
                     "\u30b7\u30a7\u30fc\u30c9\u30d6\u30e9\u30c3\u30af"),
    "invecchiato": ("Distressed", "Invecchiato", "Vieilli", "Envejecido",
                    "\u30a2\u30f3\u30c6\u30a3\u30fc\u30af\u4ed5\u4e0a\u3052"),
    "pennellato": ("Brushed finish", "Pennellato", "Bross\u00e9",
                   "Pincelado",
                   "\u30d6\u30e9\u30c3\u30b7\u30e5\u5857\u88c5"),
    "tinto-noce": ("Walnut stain", "Tinto noce", "Teint\u00e9 noyer",
                   "Tinte nogal",
                   "\u30a6\u30a9\u30eb\u30ca\u30c3\u30c8\u67d3\u8272"),
    "marmo": ("Marble", "Marmo", "Marbre", "M\u00e1rmol",
              "\u5927\u7406\u77f3"),
    "cocco": ("Crocodile", "Coccodrillo", "Crocodile", "Cocodrilo",
              "\u30af\u30ed\u30b3\u30c0\u30a4\u30eb"),
    "fibra-di-carbonio": ("Carbon fibre", "Fibra di carbonio",
                          "Fibre de carbone", "Fibra de carbono",
                          "\u30ab\u30fc\u30dc\u30f3"),
    "vetro-di-murano": ("Murano glass", "Vetro di Murano",
                        "Verre de Murano", "Cristal de Murano",
                        "\u30e0\u30e9\u30fc\u30ce\u30ac\u30e9\u30b9"),
    "acciaio-lucido": ("Polished steel", "Acciaio lucido", "Acier poli",
                       "Acero pulido",
                       "\u93e1\u9762\u30b9\u30c6\u30f3\u30ec\u30b9"),
    "acciaio-spazzolato": ("Brushed steel", "Acciaio spazzolato",
                           "Acier bross\u00e9", "Acero cepillado",
                           "\u30d8\u30a2\u30e9\u30a4\u30f3\u4ed5\u4e0a\u3052"),
    "effetto-argento": ("Silver effect", "Effetto argento", "Effet argent",
                        "Efecto plata",
                        "\u30b7\u30eb\u30d0\u30fc\u8abf"),
    "effetto-platino": ("Platinum effect", "Effetto platino",
                        "Effet platine", "Efecto platino",
                        "\u30d7\u30e9\u30c1\u30ca\u8abf"),
    "effetto-lunare": ("Moon effect", "Effetto lunare", "Effet lunaire",
                       "Efecto lunar", "\u30e0\u30fc\u30f3\u8abf"),
    "foglia-argento": ("Silver leaf", "Foglia argento", "Feuille d'argent",
                       "Pan de plata", "\u9280\u7b94"),
    "foglia-bronzo": ("Bronze leaf", "Foglia bronzo", "Feuille de bronze",
                      "Pan de bronce",
                      "\u30d6\u30ed\u30f3\u30ba\u7b94"),
    "foglia-oro": ("Gold leaf", "Foglia oro", "Feuille d'or",
                   "Pan de oro", "\u91d1\u7b94"),
    "oro-perlato": ("Pearl gold", "Oro perlato", "Or nacr\u00e9",
                    "Oro perlado",
                    "\u30d1\u30fc\u30eb\u30b4\u30fc\u30eb\u30c9"),
    "argento": ("Silver", "Argento", "Argent", "Plata",
                "\u30b7\u30eb\u30d0\u30fc"),
    "ottone": ("Brass", "Ottone", "Laiton", "Lat\u00f3n", "\u771f\u936e"),
    "rame": ("Copper", "Rame", "Cuivre", "Cobre", "\u9285"),
    "oro": ("Gold", "Oro", "Or", "Oro", "\u30b4\u30fc\u30eb\u30c9"),
    "pelle-martellata": ("Hammered leather", "Pelle martellata",
                         "Cuir martel\u00e9", "Piel martillada",
                         "\u30cf\u30f3\u30de\u30fc\u30ec\u30b6\u30fc"),
    "pelle-traforata": ("Perforated leather", "Pelle traforata",
                        "Cuir perfor\u00e9", "Piel perforada",
                        "\u30d1\u30f3\u30c1\u30f3\u30b0\u30ec\u30b6\u30fc"),
    "pelle-liscia": ("Smooth leather", "Pelle liscia", "Cuir lisse",
                     "Piel lisa",
                     "\u30b9\u30e0\u30fc\u30b9\u30ec\u30b6\u30fc"),
    "scamosciato": ("Suede", "Scamosciato", "Daim", "Ante",
                    "\u30b9\u30a8\u30fc\u30c9"),
}


def titolo_tex(percorso):
    """Come si chiama quel panno o quel legno nella lingua di adesso. Se
    non e' in elenco si ripiega sul nome del file, cosi' una texture
    aggiunta domani si vede lo stesso."""
    f = os.path.basename(percorso).lower()
    for chiave in sorted(NOMI_TEX, key=len, reverse=True):
        if chiave in f:
            nomi = NOMI_TEX[chiave]
            k = [c for c, _ in LINGUE].index(CFG.get("lingua", "en")) \
                if CFG.get("lingua", "en") in [c for c, _ in LINGUE] else 0
            return nomi[k] if k < len(nomi) else nomi[0]
    return _bel_nome(os.path.basename(percorso))


def _coda_nome(f):
    """Il pezzetto che il nome bello butta via: il numero o la lettera in
    fondo al file. Serve solo quando due panni si chiamerebbero uguale."""
    n = os.path.splitext(f)[0].lower()
    for via in ("panno-biliardo-", "panno-", "-go-7", "-go"):
        n = n.replace(via, "")
    tolti = [x for x in n.split("-")
             if x and len(x) <= 2 and (x.isdigit() or x.isalpha())]
    return " ".join(tolti)


def elenco_texture(sotto):
    """Tutti i file di quella cartella, uno per uno: sono colori diversi
    anche quando il nome si somiglia, quindi non se ne butta via
    nessuno. Se due finiscono sullo stesso nome si distinguono per come
    sono: il piu' chiaro prende "chiaro", l'altro "scuro"; se sono piu'
    di due si numerano."""
    cartella = os.path.join(GFX, sotto)
    if not os.path.isdir(cartella):
        return []
    gruppi = {}
    for f in sorted(os.listdir(cartella)):
        if not f.lower().endswith((".png", ".jpg", ".jpeg", ".bmp")):
            continue
        gruppi.setdefault(_bel_nome(f), []).append(
            os.path.join(cartella, f))

    fuori = []
    for nome, file_uguali in gruppi.items():
        if len(file_uguali) == 1:
            fuori.append((nome, file_uguali[0]))
            continue
        # stesso nome per piu' file: ognuno si riprende il pezzo che il
        # nome bello gli aveva tolto, che nei file e' proprio quello che
        # li distingue (verde 2, verde 3)
        for p in sorted(file_uguali):
            coda = _coda_nome(os.path.basename(p))
            fuori.append(("%s %s" % (nome, coda) if coda else nome, p))
    return sorted(fuori)


PANNI = []              # si riempiono all'avvio, con prepara_texture()
BORDI = []
TEX = {}                # le texture gia' caricate e portate a misura


BANDIERE = {}           # codice del paese -> file
BAND_TAGLIA = {}        # le bandiere gia' portate a misura


def prepara_bandiere():
    """Le bandiere che stanno in biliardo_gfx/bandiere: il nome del file
    e' il codice del paese, due lettere come "it", o quelle britanniche
    che hanno il codice lungo tipo "gb-sct"."""
    d = os.path.join(GFX, "bandiere")
    if not os.path.isdir(d):
        return
    for nome_f in sorted(os.listdir(d)):
        if nome_f.lower().endswith(".png"):
            BANDIERE[os.path.splitext(nome_f)[0].lower()] = \
                os.path.join(d, nome_f)


def bandiera(codice, alta):
    """La bandiera di quel paese, alta quanto serve. Sono quattro a tre,
    come i disegni da cui vengono."""
    if not codice:
        return None
    chiave = (codice, alta)
    if chiave not in BAND_TAGLIA:
        percorso = BANDIERE.get(codice)
        q = None
        if percorso is not None:
            try:
                img = pygame.image.load(percorso).convert_alpha()
                q = pygame.transform.smoothscale(
                    img, (int(round(alta * 4 / 3.0)), alta))
            except (pygame.error, IOError):
                q = None
        BAND_TAGLIA[chiave] = q
    return BAND_TAGLIA[chiave]


def elenco_bandiere():
    """I codici in ordine, per girarli con le freccette."""
    return sorted(BANDIERE.keys())


def prepara_texture():
    del PANNI[:]
    del BORDI[:]
    PANNI.extend(elenco_texture("panni"))
    BORDI.extend(elenco_texture("bordi"))


MEDIE = {}


def colore_medio(percorso):
    """Il colore medio di una texture: serve per tingere la gomma della
    sponda della stessa tinta del panno, un po' piu' scura."""
    if percorso not in MEDIE:
        try:
            img = pygame.image.load(percorso).convert()
        except (pygame.error, IOError):
            return (40, 90, 60)
        p = pygame.transform.smoothscale(img, (1, 1))
        MEDIE[percorso] = p.get_at((0, 0))[:3]
    return MEDIE[percorso]


def piastrella(sc, rett, percorso, lato):
    """Riempie un rettangolo ripetendo la texture a quadretti piccoli. Le
    foto dei panni sono mille per mille e stirate su tutto il tavolo la
    trama verrebbe enorme: a quadretti resta della misura giusta."""
    q = texture(percorso, (lato, lato))
    if q is None:
        return
    vecchio = sc.get_clip()
    sc.set_clip(rett)
    for x in range(rett.left, rett.right, lato):
        for y in range(rett.top, rett.bottom, lato):
            sc.blit(q, (x, y))
    sc.set_clip(vecchio)


def texture(percorso, misura):
    """La texture portata alla misura che serve, tenuta da parte: caricare
    e ridimensionare mille per mille a ogni fotogramma sarebbe uno spreco."""
    chiave = (percorso, misura)
    if chiave not in TEX:
        try:
            img = pygame.image.load(percorso).convert()
        except (pygame.error, IOError):
            return None
        TEX[chiave] = pygame.transform.smoothscale(img, misura)
    return TEX[chiave]


BUCA = (12, 12, 14)

# Il fondo della finestra, dietro al tavolo e sotto al menu: un verde
# scuro che schiarisce verso il centro, come la luce che cade sul tavolo.
# Il nero pieno faceva sembrare la finestra vuota.
SFONDO = (8, 50, 42)           # al centro
SFONDO_BORDO = (2, 22, 18)     # agli angoli
FONDO = None
# Lo stesso fondo in altri colori: il negozio bordeaux, la borsa blu, cosi'
# si capisce subito dove si e'.
FONDI_TINTE = {"negozio": ((54, 12, 22), (22, 4, 9)),
               "borsa": ((12, 30, 64), (4, 10, 26))}
FONDI = {}
TINTA_ORA = [None]      # il fondo dell'ultima schermata, per le bande


def scurisci(c, k):
    return (int(c[0] * k), int(c[1] * k), int(c[2] * k))


def fondo(tinta=None):
    """Si disegna una volta sola e si ricopia. La grana finissima serve
    a non far vedere le fasce del degrade sugli schermi grandi."""
    global FONDO
    TINTA_ORA[0] = tinta if tinta in FONDI_TINTE else None
    if tinta in FONDI_TINTE:
        if tinta not in FONDI:
            FONDI[tinta] = _fai_fondo(*FONDI_TINTE[tinta])
        return FONDI[tinta]
    if FONDO is not None:
        return FONDO
    FONDO = _fai_fondo(SFONDO, SFONDO_BORDO)
    return FONDO


def _fai_fondo(SFONDO, SFONDO_BORDO):
    s = pygame.Surface((WIN_W, WIN_H)).convert()
    if HA_NUMPY:
        gx = (np.arange(WIN_W, dtype=np.float32) - WIN_W / 2.0) / (WIN_W / 2.0)
        gy = (np.arange(WIN_H, dtype=np.float32) - WIN_H / 2.0) / (WIN_H / 2.0)
        r = np.sqrt(gx[:, None] ** 2 * 0.75 + gy[None, :] ** 2)
        t = np.clip(1.0 - r / 1.25, 0.0, 1.0) ** 1.4
        a = np.stack([SFONDO_BORDO[i] + (SFONDO[i] - SFONDO_BORDO[i]) * t
                      for i in range(3)], axis=2)
        a += np.random.uniform(-1.6, 1.6, a.shape).astype(np.float32)
        px = pygame.surfarray.pixels3d(s)
        px[:] = np.clip(a, 0, 255).astype(np.uint8)
        del px
    else:
        s.fill(SFONDO)
    return s


TESTO = (232, 232, 236)
TESTO_OPACO = (194, 198, 206)

# Un colore per giocatore: il messaggio in mezzo prende il colore di chi
# riguarda, cosi' si capisce a chi tocca senza stare a leggere.
COL_GIOC = ((255, 196, 72), (104, 198, 255))

# colore di ogni numero, come nel biliardo vero
COLORI = {
    1: (238, 186, 30), 2: (24, 70, 172), 3: (206, 36, 40), 4: (96, 42, 140),
    5: (232, 116, 32), 6: (22, 130, 70), 7: (128, 48, 42), 8: (18, 18, 20),
    9: (238, 186, 30), 10: (24, 70, 172), 11: (206, 36, 40), 12: (96, 42, 140),
    13: (232, 116, 32), 14: (22, 130, 70), 15: (128, 48, 42),
}


# I set di palle: stessi colori per numero, come vuole il regolamento,
# ma in tinte diverse. Per ogni set: il nome, i colori dall'1 all'8 (le
# mezze dal 9 al 15 riprendono quelli dall'1 al 7), i puntini della
# bianca, il tondino del numero e il colore della cifra.
_BASE8 = [COLORI[k] for k in range(1, 9)]
# i colori accesi dei set speciali: sempre vivi, mai spenti
_VIVI8 = [(255, 214, 0), (0, 96, 230), (236, 28, 44), (136, 44, 210),
          (255, 120, 0), (0, 176, 80), (200, 30, 110), (16, 16, 20)]
# I caratteri dei numeri: il primo che c'e' sul computer. Classico con
# le grazie per il vintage, tondo per il pastello, moderno per il neon.
CAR_CLASSICO = "arial,liberationsans,helvetica,dejavusans"
CAR_GRAZIE = ("georgia,baskerville,timesnewroman,times,dejavuserif,"
              "liberationserif")
CAR_TONDO = ("arialroundedmtbold,varelaround,nunito,verdana,dejavusans")
CAR_MODERNO = ("futura,avenirnext,avenir,helveticaneue,segoeui,"
               "montserrat,dejavusans")
# nome, colori 1-8, puntini della bianca, tondino, cifra, carattere, stile
SET_PALLE = (
    ("set_classico", _BASE8, (204, 46, 46), (250, 250, 246), (26, 26, 30),
     CAR_CLASSICO, "classico"),
    ("set_retro", [(206, 156, 18), (16, 40, 122), (148, 14, 30),
                   (70, 18, 112), (190, 78, 18), (8, 90, 50),
                   (92, 28, 24), (12, 12, 14)],
     (160, 70, 50), (244, 234, 206), (40, 30, 16), CAR_GRAZIE, "classico"),
    ("set_marmo", [(236, 170, 30), (40, 70, 190), (200, 30, 40),
                   (110, 50, 170), (236, 100, 30), (20, 130, 70),
                   (140, 30, 50), (230, 228, 222)],
     (190, 170, 130), (244, 240, 230), (22, 22, 26), CAR_CLASSICO, "marmo"),
    ("set_continental", _BASE8, (200, 40, 40), (244, 236, 214),
     (246, 240, 226), CAR_CLASSICO, "continental"),
    ("set_pastello", [(248, 186, 40), (120, 196, 236), (226, 44, 50),
                      (168, 120, 204), (200, 110, 40), (30, 168, 150),
                      (246, 120, 136), (16, 16, 20)],
     (20, 20, 22), (250, 250, 246), (22, 22, 26), CAR_CLASSICO, "pastello"),
    ("set_marmo_chiaro", [(244, 190, 50), (70, 110, 220), (226, 60, 64),
                          (146, 90, 210), (246, 132, 56), (46, 166, 100),
                          (176, 60, 80), (30, 30, 34)],
     (190, 170, 130), (250, 248, 242), (22, 22, 26), CAR_CLASSICO,
     "marmo_chiaro"),
    ("set_nere", [(255, 196, 0), (0, 96, 226), (236, 20, 36),
                  (140, 60, 200), (255, 120, 0), (0, 176, 120),
                  (190, 30, 60), (18, 18, 22)],
     (30, 30, 34), (240, 234, 214), (30, 30, 34), CAR_CLASSICO, "nere"),
    ("set_doppia", _VIVI8, (0, 96, 230), (255, 255, 255), (20, 20, 24),
     CAR_MODERNO, "doppia"),
    ("set_zigzag", _BASE8, (30, 30, 34), (250, 250, 246), (26, 26, 30),
     CAR_CLASSICO, "zigzag"),
    ("set_bersaglio", _VIVI8, (236, 28, 44), (255, 255, 255), (20, 20, 24),
     CAR_MODERNO, "bersaglio"),
    ("set_scacchi", _VIVI8, (20, 20, 24), (255, 255, 255), (20, 20, 24),
     CAR_MODERNO, "scacchi"),
)
FONT_PALLE = {}


def font_palle():
    """Il carattere dei numeri per il set scelto, fatto una volta."""
    nomi = set_palle()[5]
    if nomi == CAR_CLASSICO:
        return None         # il classico resta col carattere di sempre
    if nomi not in FONT_PALLE:
        try:
            FONT_PALLE[nomi] = pygame.font.SysFont(nomi, 96, bold=True)
        except Exception:
            FONT_PALLE[nomi] = None
    return FONT_PALLE[nomi]


def stella(s, colore, cx, cy, r, punte=5):
    pt = []
    for k in range(punte * 2):
        a = math.pi / punte * k - math.pi / 2.0
        rr = r if k % 2 == 0 else r * 0.45
        pt.append((cx + math.cos(a) * rr, cy + math.sin(a) * rr))
    pygame.draw.polygon(s, colore, pt)


def marmo(num, base, W, H, chiaro_set=False):
    """Una texture di marmo, sempre la stessa per quel numero: onde
    storte da un rumore morbido che si richiude attorno alla palla."""
    rnd = random.Random(1000 + num)
    x = np.arange(W, dtype=np.float32)[:, None] / W * 2.0 * math.pi
    y = np.arange(H, dtype=np.float32)[None, :] / H * math.pi
    turb = np.zeros((W, H), np.float32)
    for k in range(6):
        fx = rnd.randint(1, 4 + k)
        fy = rnd.uniform(0.5, 3.0 + k)
        turb += (np.sin(fx * x + fy * y + rnd.uniform(0, 6.28))
                 / (1.0 + k * 0.7))
    onda = np.sin(rnd.randint(2, 4) * x + 2.2 * y + 2.6 * turb)
    chiaro = num == 8 and not chiaro_set
    b = np.array(base, np.float32)
    if chiaro_set:
        # la versione chiara: il colore schiarito, venature bianche larghe
        # e poche venature scure, fatte col colore stesso e non col nero
        luce = np.array((252, 250, 246), np.float32)
        t = (onda[..., None] + 1.0) / 2.0
        col = b * (0.85 + 0.25 * t)
        if num == 8:
            col = b + 12.0 * t
        vena_c = np.clip(1.0 - np.abs(onda - 0.45) * 3.0, 0, 1)[..., None]
        vena_s = np.clip(1.0 - np.abs(onda + 0.6) * 7.0, 0, 1)[..., None]
        col = col * (1 - vena_c * 0.75) + luce * vena_c * 0.75
        col = col * (1 - vena_s * 0.5) + (b * 0.45) * vena_s * 0.5
        return np.clip(col, 0, 255).astype(np.uint8)
    scuro = np.array((12, 12, 14), np.float32) if not chiaro \
        else np.array((20, 20, 22), np.float32)
    luce = np.minimum(255.0, b * 0.35 + 190.0) if not chiaro \
        else np.array((250, 248, 244), np.float32)
    t = (onda[..., None] + 1.0) / 2.0
    col = b * (0.55 + 0.45 * t) if not chiaro else \
        b * (0.75 + 0.25 * t)
    # le venature scure, larghe, e quelle chiare, sottili
    vena_s = np.clip(1.0 - np.abs(onda + 0.30) * 2.3, 0, 1)[..., None]
    vena_c = np.clip(1.0 - np.abs(onda - 0.55) * 9.0, 0, 1)[..., None]
    col = col * (1 - vena_s * 0.9) + scuro * vena_s * 0.9
    col = col * (1 - vena_c * 0.7) + luce * vena_c * 0.7
    return np.clip(col, 0, 255).astype(np.uint8)


def dipingi_stile(s, num, base, stile):
    """Il disegno della palla, prima dei tondini coi numeri. Le piene e
    le mezze hanno ognuna il suo, cosi' si riconoscono al volo."""
    bianco = (246, 246, 242)
    mezza = 9 <= num <= 15
    W, H = TEX_W, TEX_H
    if stile == "doppia":
        if mezza:           # bianca con due righe sottili in mezzo
            s.fill(bianco)
            for y in (84, 146):
                pygame.draw.rect(s, base, pygame.Rect(0, y, W, 26))
        else:               # piena con una riga bianca sull'equatore
            s.fill(base)
            pygame.draw.rect(s, bianco, pygame.Rect(0, 122, W, 12))
        return
    if stile == "zigzag":
        # lo stile d'epoca: le piene con una fascetta bianca a zig-zag in
        # alto, le mezze con due calotte bianche dal bordo a denti
        s.fill(base)
        if mezza:
            passo, dente = W / 12.0, 20
            for polo, y0 in ((0, 76), (H, H - 76)):
                verso = 1 if polo == 0 else -1
                pt = [(0, polo)]
                k = 0
                while k * passo / 2.0 <= W:
                    x = k * passo / 2.0
                    y = y0 + (dente if k % 2 == 0 else -dente) * verso * 0.5
                    pt.append((x, y))
                    k += 1
                pt += [(W, polo)]
                pygame.draw.polygon(s, bianco, pt)
        else:
            passo, dente, spess = W / 20.0, 9, 11
            su, giu = [], []
            k = 0
            while k * passo / 2.0 <= W:
                x = k * passo / 2.0
                d = dente if k % 2 == 0 else -dente
                su.append((x, 64 + d - spess / 2.0))
                giu.append((x, 64 + d + spess / 2.0))
                k += 1
            pygame.draw.polygon(s, bianco, su + giu[::-1])
        return
    if stile == "bersaglio":
        if mezza:           # fascia sottile e due anelli
            s.fill(bianco)
            pygame.draw.rect(s, base, pygame.Rect(0, 96, W, 64))
            for u in (W // 4, W * 3 // 4):
                pygame.draw.circle(s, base, (u, 128), 70)
        else:               # piena con l'anello bianco attorno al numero
            s.fill(base)
            for u in (W // 4, W * 3 // 4):
                pygame.draw.circle(s, bianco, (u, 128), 64, 7)
        return
    if stile == "scacchi":
        if mezza:           # fascia a scacchi, colore e bianco
            s.fill(bianco)
            q = 16
            for y in range(64, H - 64, q):
                for x in range(0, W, q):
                    if ((x // q) + (y // q)) % 2 == 0:
                        pygame.draw.rect(s, base, pygame.Rect(x, y, q, q))
        else:               # piena con una riga a scacchi in mezzo
            s.fill(base)
            q = 12
            for x in range(0, W, q):
                for k, y in enumerate((116, 128)):
                    if ((x // q) + k) % 2 == 0:
                        pygame.draw.rect(s, bianco, pygame.Rect(x, y, q, q))
        return
    if stile in ("continental", "pastello"):
        # come il classico, ma le calotte color avorio
        if mezza:
            s.fill((240, 232, 210))
            pygame.draw.rect(s, base, pygame.Rect(0, 64, W, H - 128))
        else:
            s.fill(base)
        return
    if stile == "marmo_chiaro":
        # marmo chiaro: calotte bianche larghe e la fascia di marmo stretta
        px = pygame.surfarray.pixels3d(s)
        px[:] = marmo(num, base, W, H, True)
        del px
        if mezza:
            pygame.draw.rect(s, bianco, pygame.Rect(0, 0, W, 84))
            pygame.draw.rect(s, bianco, pygame.Rect(0, H - 84, W, 84))
        return
    if stile == "marmo":
        # marmo scuro: il colore venato di nero e di chiaro; le mezze con
        # le calotte nere, la 8 marmo chiaro venato di nero
        px = pygame.surfarray.pixels3d(s)
        px[:] = marmo(num, base, W, H)
        del px
        if mezza:
            pygame.draw.rect(s, (14, 14, 16), pygame.Rect(0, 0, W, 84))
            pygame.draw.rect(s, (14, 14, 16), pygame.Rect(0, H - 84, W, 84))
        return
    if stile == "nere":
        # le mezze con le calotte nere invece che bianche
        if mezza:
            s.fill((16, 16, 18))
            pygame.draw.rect(s, base, pygame.Rect(0, 64, W, H - 128))
        else:
            s.fill(base)
        return
    # classico
    if mezza:
        s.fill(bianco)
        pygame.draw.rect(s, base, pygame.Rect(0, 64, W, H - 128))
    else:
        s.fill(base)


# Ogni gioco ha le sue palle: pool (8 e 9), snooker e birilli. Ognuno
# ha i suoi set e la scelta si tiene separata.
PALLE_VISTA = [None]    # nelle impostazioni del menu: che palle si guardano
DENTRO_PARTITA = [False]
PALLE_ERA = {}          # le scelte com'erano aprendo le impostazioni
TIPI_PALLE = ("pool", "blackball", "piramide", "snooker", "birilli")
NOME_TIPO = {"pool": "Pool", "snooker": "Snooker", "birilli": "5-Pins",
             "blackball": "Blackball", "piramide": "Pyramid"}


def tipo_palle(gioco=None):
    if gioco is None and PALLE_VISTA[0] and not DENTRO_PARTITA[0]:
        return PALLE_VISTA[0]
    if gioco is None:
        gioco = GIOCO[0] if "GIOCO" in globals() else 0
    return {2: "snooker", 3: "birilli", 4: "blackball", 6: "snooker",
            7: "birilli", 8: "piramide"}.get(gioco, "pool")


def scelta_palle(tipo):
    d = CFG.get("palle", {}) if "CFG" in globals() else {}
    if not isinstance(d, dict):         # il vecchio salvataggio: solo pool
        d = {"pool": int(d) if isinstance(d, int) else 0}
        CFG["palle"] = d
    elenco = elenco_set(tipo)
    fisso = PALLE_TORNEO[0] if "PALLE_TORNEO" in globals() else None
    if isinstance(fisso, dict):
        fisso = fisso.get(tipo)
    if fisso and DENTRO_PARTITA[0]:
        for i, x in enumerate(elenco):
            if x[0] == fisso:
                return i
    k = d.get(tipo, 0)
    return k if isinstance(k, int) and 0 <= k < len(elenco) else 0


def elenco_set(tipo):
    return {"pool": SET_PALLE, "snooker": SET_SNOOKER,
            "birilli": SET_BIRILLI, "blackball": SET_BLACKBALL,
            "piramide": SET_PIRAMIDE}[tipo]


def set_palle():
    return SET_PALLE[scelta_palle("pool")]


def set_snooker():
    return SET_SNOOKER[scelta_palle("snooker")]


def set_piramide():
    return SET_PIRAMIDE[scelta_palle("piramide")]


def set_blackball():
    return SET_BLACKBALL[scelta_palle("blackball")]


def set_birilli():
    return SET_BIRILLI[scelta_palle("birilli")]


def colore_palla(num):
    """Il colore della palla numero num nel set scelto."""
    if num <= 0 or num > 15:
        return COLORI.get(num, (240, 240, 236))
    return set_palle()[1][(num - 1) % 8 if num <= 8 else num - 9]
# --------------------------------------------------- palle come sfere

# Una palla che rotola non e' un disegno che gira su se' stesso: la sua
# superficie le scorre sopra, il numero attraversa la faccia e sparisce
# oltre il bordo. Per farlo si tiene l'orientamento della palla come
# matrice 3x3 e per ogni pixel del cerchio si guarda quale punto della
# superficie stai vedendo.

# La "buccia" della palla, stesa: in orizzontale il giro completo, in
# verticale da polo a polo. Nella PNG il numero e' alto 106 px; a
# 256x128 lo si schiacciava a 38 e si perdeva tutto prima ancora di
# arrivare sullo schermo. A 512x256 ci arriva intero.
TEX_W, TEX_H = 512, 256
TESSITURE = {}
LUCE = None
LUCE_2 = None
OMBRA = None


def _rot(asse, ang):
    """Matrice di rotazione attorno a un asse (formula di Rodrigues)."""
    x, y, z = asse
    c = math.cos(ang)
    s = math.sin(ang)
    t = 1.0 - c
    return np.array([
        [t * x * x + c,     t * x * y - s * z, t * x * z + s * y],
        [t * x * y + s * z, t * y * y + c,     t * y * z - s * x],
        [t * x * z - s * y, t * y * z + s * x, t * z * z + c]],
        dtype=np.float32)


def _rot_casuale():
    m = _rot((0.0, 0.0, 1.0), random.uniform(0, math.tau))
    m = _rot((1.0, 0.0, 0.0), random.uniform(0, math.tau)) @ m
    return _rot((0.0, 1.0, 0.0), random.uniform(0, math.tau)) @ m


CARTELLA = os.path.dirname(os.path.abspath(__file__))
GFX = os.path.join(CARTELLA, "biliardo_gfx")
AUDIO = os.path.join(CARTELLA, "biliardo_audio")
FX = os.path.join(CARTELLA, "biliardo_fx")
STECCA_IMG = None


def _leggi_asset(num):
    """Dalla PNG dell'asset ricava solo il colore della vernice. La figura
    intera non si usa perche' li' dentro luce e ombra sono gia' dipinte: su
    una sfera che gira, il riflesso girerebbe con lei. La luce la mettiamo
    noi, e il numero lo riscriviamo col carattere."""
    f = os.path.join(GFX, "cue_ball_plain.png" if num == 0
                     else "pool_ball_plain_%d.png" % num)
    if not os.path.exists(f):
        return None
    try:
        im = pygame.image.load(f).convert_alpha()
    except pygame.error:
        return None

    W, H = im.get_size()
    rgb = pygame.surfarray.array3d(im).astype(np.float32)
    alf = pygame.surfarray.array_alpha(im)
    lum = rgb.mean(axis=2)
    pieno = alf > 200

    gx = np.arange(W)[:, None] - W / 2.0
    gy = np.arange(H)[None, :] - H / 2.0
    rr = np.sqrt(gx * gx + gy * gy)

    # il colore: il piu' presente fra quelli ne' bianchi ne' neri
    sel = pieno & (lum > 40) & (lum < 215) & (rr > W * 0.30)
    if sel.sum() < 200:
        sel = pieno & (lum > 40) & (lum < 215)
    campione = rgb[sel].astype(np.int32)
    if len(campione) == 0:
        return None
    chiave = (campione[:, 0] << 16) + (campione[:, 1] << 8) + campione[:, 2]
    valori, quante = np.unique(chiave, return_counts=True)
    k = int(valori[quante.argmax()])
    return ((k >> 16) & 255, (k >> 8) & 255, k & 255)


def scrivi(s, num, font, u, colore=(26, 26, 30), stretto=False):
    """Il numero sul tondino bianco. Non si usa quello disegnato dentro la
    PNG: li' e' un carattere pesante, che a questa misura si chiude e
    diventa una macchia. Meglio scriverlo noi con un carattere magro e
    ridimensionarlo a mano, cosi' una cifra e due cifre riempiono il
    tondino allo stesso modo."""
    t = font.render(str(num), True, colore)
    tw, th = t.get_size()
    # i numeri a due cifre restano dentro il tondino; con l'anello attorno
    # (stretto) dentro l'anello
    k = min(64.0 / th, 64.0 / tw) if stretto else min(82.0 / th, 78.0 / tw)
    t = pygame.transform.smoothscale(
        t, (max(1, int(tw * k)), max(1, int(th * k))))
    s.blit(t, t.get_rect(center=(u, TEX_H // 2)))


# Lo snooker ha palle lisce, senza numero: quindici rosse e sei colori.
# Per non pestare i numeri del pool si contano da cento in su.
SN_ROSSI = tuple(range(101, 116))
SN_GIALLO, SN_VERDE, SN_MARRONE = 121, 122, 123
SN_BLU, SN_ROSA, SN_NERO = 124, 125, 126
SN_COLORI = (SN_GIALLO, SN_VERDE, SN_MARRONE, SN_BLU, SN_ROSA, SN_NERO)

# quanto vale ognuna, e di che tinta e'
SN_VALORE = {SN_GIALLO: 2, SN_VERDE: 3, SN_MARRONE: 4,
             SN_BLU: 5, SN_ROSA: 6, SN_NERO: 7}
SN_TINTA = {SN_GIALLO: (228, 190, 30), SN_VERDE: (16, 106, 52),
            SN_MARRONE: (118, 72, 32), SN_BLU: (24, 72, 168),
            SN_ROSA: (234, 130, 156), SN_NERO: (22, 22, 24)}
SN_ROSSO = (142, 20, 32)        # bordeaux, come le rosse vere


def sn_valore(num):
    """Quanto vale quella palla: uno se e' rossa, il suo se e' un colore."""
    if num in SN_ROSSI:
        return 1
    return SN_VALORE.get(num, 0)


# ------------------------------------------------------- cinque birilli
#
# Il biliardo all'italiana: niente buche, tre bilie e il castello di
# cinque birilli in mezzo al tavolo. I punti sono quelli del regolamento
# FIBiS: birillo laterale 2, rosso abbattuto con altri 4, rosso da solo
# 10, pallino toccato dalla bilia avversaria 3, dalla propria 4, fallo 2
# punti all'avversario. Si tira a turno, sempre, anche facendo punto.
BI_GIALLA = 141                 # la bilia del secondo giocatore
BI_PALLINO = 142                # la rossa, il pallino
BI_TINTA = {BI_GIALLA: (236, 198, 42), BI_PALLINO: (188, 40, 34)}
BI_ARRIVO = 60                  # i punti che vincono la partita
PIRAMIDE_ARRIVO = 8             # alla piramide vince chi ne imbuca otto
BI_LATERALE = 2
BI_ROSSO_CON = 4
BI_ROSSO_SOLO = 10
BI_PALL_AVV = 3
BI_PALL_MIA = 4
BI_FALLO = 2
# Il birillo e' alto 25 mm e largo 10, la bilia 61,5: in proporzione alla
# palla del gioco viene cosi'. Fra un birillo e l'altro ci passa una
# bilia e non di piu', come vuole il regolamento.
BIRILLO_R = max(2.0, BALL_R * 0.163)
BIRILLO_PASSO = BALL_R * 2.0 + BIRILLO_R * 2.0 + 1.0
BIRILLI = []                    # il castello com'e' adesso


class Birillo:
    def __init__(self, pos, rosso=False):
        self.pos = Vector2(pos)
        self.rosso = rosso
        self.in_piedi = True


def arrivo_birilli(gioco):
    """I punti che vincono: alla goriziana i birilli sono nove, si va
    piu' in la'."""
    return BI_ARRIVO * 2 if gioco == 7 else BI_ARRIVO


def posti_birilli():
    """Il castello: quattro birilli in croce attorno a quello rosso, in
    mezzo al tavolo. Alla goriziana sono nove, a rombo: il rosso in mezzo
    e otto bianchi attorno."""
    c = Vector2(PLAY.centerx, PLAY.centery)
    p = BIRILLO_PASSO
    if GIOCO[0] == 7:
        q = p / math.sqrt(2.0)
        fuori = []
        for a in (-1, 0, 1):
            for b in (-1, 0, 1):
                fuori.append((c + Vector2((a + b) * q, (a - b) * q),
                              a == 0 and b == 0))
        return fuori
    return [(c, True),
            (c + Vector2(0.0, -p), False), (c + Vector2(0.0, p), False),
            (c + Vector2(-p, 0.0), False), (c + Vector2(p, 0.0), False)]


def rifai_castello(palle):
    """I birilli si rimettono in piedi dopo ogni tiro. Quello con una
    bilia sopra resta giu' finche' il posto non e' libero."""
    del BIRILLI[:]
    for dove, rosso in posti_birilli():
        b = Birillo(dove, rosso)
        for q in palle:
            if not q.dentro and (q.pos - dove).length() < BALL_R + BIRILLO_R:
                b.in_piedi = False
                break
        BIRILLI.append(b)


def tavolo_a_birilli():
    """Le tre bilie: il pallino sul suo bollino, le due dei giocatori
    sulla linea di partenza."""
    palle = [Palla(0, (LINEA_X, PLAY.centery - PLAY.h * 0.18)),
             Palla(BI_GIALLA, (LINEA_X, PLAY.centery + PLAY.h * 0.18)),
             Palla(BI_PALLINO, PALLINO)]
    rifai_castello(palle)
    return palle


# I set dello snooker: le rosse, i sei colori dal giallo al nero, e i
# puntini della bianca (niente puntini: None). Tinte piene, come le vere.
SET_SNOOKER = (
    ("set_classico", SN_ROSSO,
     dict(SN_TINTA), (204, 46, 46)),
    # il classico in marmo, chiaro e scuro; la bianca in marmo bianco
    ("set_marmo_chiaro", SN_ROSSO, dict(SN_TINTA), (204, 46, 46), "chiaro"),
    ("set_marmo", SN_ROSSO, dict(SN_TINTA), (204, 46, 46), "scuro"),
)
# I set del blackball: le rosse, le gialle, la nera, i puntini della
# bianca. Palle lisce, senza numeri, come quelle dei pub inglesi.
SET_BLACKBALL = (
    ("set_classico", (200, 26, 34), (246, 202, 20), (16, 16, 18),
     (204, 46, 46)),
    # il Pro dei tornei: rosse bordeaux con le calotte color crema, gialle
    # piene, tutte col numero nero su un tondino bianco
    ("set_pro", (122, 18, 30), (253, 130, 0), (12, 12, 14), (196, 30, 40),
     "numeri"),
    # Club: come il Pro, ma blu al posto delle rosse
    ("set_club", (26, 70, 190), (253, 130, 0), (12, 12, 14),
     (26, 70, 190), "numeri"),
    # Club 2: blu e corallo, il numero dentro un anello del colore
    # dell'altra squadra, senza tondino; la bianca crema col trifoglio nero
    ("set_club2", (28, 64, 196), (246, 110, 84), (14, 14, 16),
     (20, 20, 22), "anello"),
    # The Legend: blu e nere lisce col piccolo marchio bianco, la 8
    # d'argento col tondino nero, la bianca crema liscia
    ("set_legend", (24, 70, 190), (14, 14, 18), (176, 178, 184), None,
     "legend"),
)
# I set della piramide russa: le quindici chiare, la rossa, la cifra.
SET_PIRAMIDE = (
    ("set_classico", (240, 230, 206), (176, 22, 30), (24, 22, 20)),
    # le alternative: nere col numero bianco, e il marmo bianco e nero
    ("set_black", (22, 22, 26), (176, 22, 30), (244, 242, 236)),
    ("set_marmo_bianco", (242, 238, 228), (176, 22, 30), (24, 22, 20),
     "chiaro"),
    ("set_marmo_nero", (22, 22, 26), (176, 22, 30), (244, 242, 236),
     "scuro"),
)
# I set dei birilli: la bianca, la gialla, il pallino rosso, i puntini
SET_BIRILLI = (
    ("set_classico", (246, 246, 242), BI_TINTA[BI_GIALLA],
     BI_TINTA[BI_PALLINO], (204, 46, 46)),
    ("set_perla", (244, 238, 222), (214, 178, 80), (128, 24, 40),
     (160, 120, 60)),
    # come il classico, ma il pallino e il birillo in mezzo blu, o verdi
    ("set_blu", (246, 246, 242), BI_TINTA[BI_GIALLA], (30, 76, 196),
     (30, 76, 196), (30, 76, 196)),
    ("set_verde", (246, 246, 242), BI_TINTA[BI_GIALLA], (22, 138, 68),
     (22, 138, 68), (22, 138, 68)),
    # le versioni black: i birilli bianchi diventano neri
    ("set_classico_nero", (22, 22, 26), BI_TINTA[BI_GIALLA],
     BI_TINTA[BI_PALLINO], (204, 46, 46), (188, 40, 34), (22, 22, 26)),
    ("set_blu_nero", (22, 22, 26), BI_TINTA[BI_GIALLA], (30, 76, 196),
     (30, 76, 196), (30, 76, 196), (22, 22, 26)),
    ("set_verde_nero", (22, 22, 26), BI_TINTA[BI_GIALLA], (22, 138, 68),
     (22, 138, 68), (22, 138, 68), (22, 22, 26)),
    # il classico in marmo: bianco coi birilli bianchi, nero coi neri
    ("set_bi_marmo", (246, 246, 242), BI_TINTA[BI_GIALLA],
     BI_TINTA[BI_PALLINO], (204, 46, 46), (188, 40, 34), (238, 234, 222),
     "chiaro"),
    ("set_bi_marmo_nero", (22, 22, 26), BI_TINTA[BI_GIALLA],
     BI_TINTA[BI_PALLINO], (204, 46, 46), (188, 40, 34), (22, 22, 26),
     "scuro"),
)


def bi_marmo(s, num, base):
    """Nei set di marmo dei birilli la palla prende le venature."""
    if tipo_palle() == "birilli":
        vene = set_birilli()[7] if len(set_birilli()) > 7 else None
    elif tipo_palle() == "snooker":
        vene = set_snooker()[4] if len(set_snooker()) > 4 else None
        if num == 0 and vene:
            vene = "chiaro"     # la bianca resta bianca
    else:
        vene = None
    if not vene:
        return
    pygame.surfarray.pixels3d(s)[:] = marmo(num, base, s.get_width(),
                                            s.get_height(), vene == "chiaro")


def sn_tinta(num):
    if num == BI_GIALLA:
        return set_birilli()[2]
    if num == BI_PALLINO:
        return set_birilli()[3]
    st = set_snooker()
    return st[1] if num in SN_ROSSI else st[2].get(num, (200, 200, 200))


def _tessitura(num, font, asset=None):
    """La superficie della palla stesa: in orizzontale il giro completo,
    in verticale dal polo nord al polo sud."""
    s = pygame.Surface((TEX_W, TEX_H))

    if asset is not None and scelta_palle("pool") == 0 \
            and tipo_palle() == "pool":
        colore = asset
        if num == 0:
            s.fill(colore if sum(colore) > 600 else (246, 246, 242))
            for u, v in ((80, 84), (304, 172), (412, 72), (184, 208), (496, 140)):
                pygame.draw.circle(s, (204, 46, 46), (u, v), 10)
            return pygame.surfarray.array3d(s).astype(np.float32)

        if 9 <= num <= 15:
            s.fill((243, 243, 240))
            pygame.draw.rect(s, colore, pygame.Rect(0, 64, TEX_W, TEX_H - 128))
        else:
            s.fill(colore)
        for u in (TEX_W // 4, TEX_W * 3 // 4):
            pygame.draw.circle(s, (250, 250, 246), (u, TEX_H // 2), 62)
            scrivi(s, num, font, u)
        return pygame.surfarray.array3d(s).astype(np.float32)

    if num >= 100:
        # snooker: tinta piena e basta, niente numero
        s.fill(sn_tinta(num))
        bi_marmo(s, num, sn_tinta(num))
        return pygame.surfarray.array3d(s).astype(np.float32)

    _, _, puntini, tondo, cifra, _, stile = set_palle()
    font = font_palle() or font
    bianca = (246, 246, 242)
    # la bianca e' di tutti i giochi: prende i puntini del gioco in corso
    if tipo_palle() == "snooker":
        puntini = set_snooker()[3]
    elif tipo_palle() == "blackball":
        puntini = set_blackball()[4]
        if 1 <= num <= 15:
            # rosse dall'1 al 7, gialle dal 9 al 15, la nera senza numero
            st = set_blackball()
            base = st[1] if num <= 7 else st[3] if num == 8 else st[2]
            s.fill(base)
            if len(st) > 5 and st[5] == "legend":
                if num == 8:
                    # l'argento: un grigio con la brillantina
                    rnd = random.Random(88)
                    for _ in range(900):
                        x, y = rnd.randrange(TEX_W), rnd.randrange(TEX_H)
                        c = rnd.choice(((210, 212, 218), (140, 142, 148),
                                        (236, 238, 242)))
                        s.set_at((x, y), c)
                    for u in (TEX_W // 4, TEX_W * 3 // 4):
                        pygame.draw.circle(s, (14, 14, 16), (u, TEX_H // 2),
                                           40)
                        scrivi(s, 8, font, u, (240, 240, 240), stretto=True)
                else:
                    # il marchio: una rosetta bianca e un anellino sotto
                    for u in (TEX_W // 4, TEX_W * 3 // 4):
                        cy = TEX_H // 2 - 8
                        for a in range(0, 360, 60):
                            ra = math.radians(a)
                            pygame.draw.circle(
                                s, (240, 240, 244),
                                (int(u + 7 * math.cos(ra)),
                                 int(cy + 7 * math.sin(ra))), 5)
                        pygame.draw.circle(s, (240, 240, 244), (u, cy + 26),
                                           7, 2)
            if len(st) > 5 and st[5] == "anello":
                altro = st[2] if num <= 7 else st[1]
                if num == 8:
                    altro = (240, 238, 232)
                for u in (TEX_W // 4, TEX_W * 3 // 4):
                    pygame.draw.circle(s, altro, (u, TEX_H // 2), 40, 6)
                    for d in (-2, -1, 0, 1, 2):     # la cifra piu' piena
                        scrivi(s, num, font, u + d, altro, stretto=True)
            if len(st) > 5 and st[5] == "numeri":
                if num <= 7:        # le rosse: calotte crema
                    s.fill((238, 228, 206))
                    pygame.draw.rect(s, base, pygame.Rect(0, 64, TEX_W,
                                                          TEX_H - 128))
                for u in (TEX_W // 4, TEX_W * 3 // 4):
                    fondo_n = (246, 244, 238)     # tondino bianco
                    cifra_n = (20, 20, 22)        # numero nero
                    pygame.draw.circle(s, fondo_n, (u, TEX_H // 2), 34)
                    scrivi(s, num, font, u, cifra_n, stretto=True)
            return pygame.surfarray.array3d(s).astype(np.float32)
    elif tipo_palle() == "piramide":
        st_p = set_piramide()
        avorio, rossa, nero = st_p[1:4]
        vene = st_p[4] if len(st_p) > 4 else None
        if num == 0:
            s.fill(rossa)       # la rossa, liscia
            if vene:
                pygame.surfarray.pixels3d(s)[:] = marmo(
                    0, rossa, TEX_W, TEX_H, vene == "chiaro")
            return pygame.surfarray.array3d(s).astype(np.float32)
        if 1 <= num <= 15:
            # bianche col numero stampato, senza tondino
            s.fill(avorio)
            if vene:
                pygame.surfarray.pixels3d(s)[:] = marmo(
                    num, avorio, TEX_W, TEX_H, vene == "chiaro")
            for u in (TEX_W // 4, TEX_W * 3 // 4):
                scrivi(s, num, font, u, nero)
            return pygame.surfarray.array3d(s).astype(np.float32)
    elif tipo_palle() == "birilli":
        bianca, puntini = set_birilli()[1], set_birilli()[4]
    if num == 0:
        stile_bb = (set_blackball()[5] if tipo_palle() == "blackball"
                    and len(set_blackball()) > 5 else None)
        trifoglio = stile_bb == "anello" or (stile == "pastello" and
                                             tipo_palle() == "pool")
        s.fill((236, 226, 198) if (stile in ("marmo", "marmo_chiaro",
                                             "continental", "pastello")
                                   and tipo_palle() == "pool")
               or stile_bb in ("anello", "legend") else bianca)
        if tipo_palle() in ("birilli", "snooker"):
            bi_marmo(s, 0, bianca)
        if trifoglio:
            # il segno a tre pallini, da due parti
            for u, v in ((128, 110), (384, 146)):
                for a in (90, 210, 330):
                    ra = math.radians(a)
                    pygame.draw.circle(s, puntini,
                                       (int(u + 9 * math.cos(ra)),
                                        int(v - 9 * math.sin(ra))), 7)
            return pygame.surfarray.array3d(s).astype(np.float32)
        if puntini is None:
            return pygame.surfarray.array3d(s).astype(np.float32)
        # i puntini della bianca: senza, una palla bianca che gira non si
        # vede girare
        for u, v in ((80, 84), (304, 172), (412, 72), (184, 208), (496, 140)):
            if stile == "zigzag" and tipo_palle() == "pool":
                stella(s, puntini, u, v, 14)    # le stelline d'epoca
            else:
                pygame.draw.circle(s, puntini, (u, v), 10)
    else:
        base = colore_palla(num)
        dipingi_stile(s, num, base, stile)
        for u in (TEX_W // 4, TEX_W * 3 // 4):
            if stile == "continental":
                # niente tondino: il numero bianco dentro un anellino
                # bianco, dritto sul colore
                pygame.draw.circle(s, cifra, (u, TEX_H // 2), 40, 4)
                for d in (-1, 0, 1):
                    scrivi(s, num, font, u + d, cifra, stretto=True)
                continue
            pygame.draw.circle(s, tondo, (u, TEX_H // 2), 46)
            if stile in ("nere", "marmo", "marmo_chiaro"):  # l'anello
                pygame.draw.circle(s, cifra, (u, TEX_H // 2), 43, 3)
            scrivi(s, num, font, u, cifra,
                   stretto=(stile in ("nere", "marmo", "marmo_chiaro")))
    return pygame.surfarray.array3d(s).astype(np.float32)


def _fai_ombra():
    """Macchia morbida sotto la palla: un cerchio netto sembrava una
    mezzaluna disegnata a mano."""
    D = int(BALL_R * 2.6)
    g = np.arange(D, dtype=np.float32) - (D - 1) / 2.0
    r = np.sqrt(g[:, None] ** 2 + g[None, :] ** 2) / (BALL_R * 1.25)
    a = np.clip(1.0 - r, 0.0, 1.0) ** 1.7 * 105.0
    s = pygame.Surface((D, D), pygame.SRCALPHA)
    c = pygame.surfarray.pixels3d(s)
    c[:] = (6, 40, 62)
    del c
    al = pygame.surfarray.pixels_alpha(s)
    al[:] = a.astype(np.uint8)
    del al
    return s


# Come va girata una palla perche' il numero guardi in faccia chi guarda:
# serve per le palline piccole della fascia in basso.
M_FACCIA = None
ICONE = {}
ICONA_R = 24.0


ICONE_SPENTE = {}


ICONA_PICCOLA = s(30)   # quanto sono grandi le palline del conto in basso
ICONE_MINI = {}


def icona_ridotta(num, accesa):
    """La pallina del conto, piccola. Si ridimensiona una volta sola e
    poi si ricopia."""
    chiave = (num, accesa)
    if chiave not in ICONE_MINI:
        grande = ICONE[num] if accesa else icona_spenta(num)
        ICONE_MINI[chiave] = pygame.transform.smoothscale(
            grande, (ICONA_PICCOLA, ICONA_PICCOLA))
    return ICONE_MINI[chiave]


def icona_spenta(num):
    """La stessa pallina ma smorzata: quelle di chi non sta tirando devono
    farsi notare meno, se no le due file sembrano uguali."""
    if num not in ICONE_SPENTE:
        # non si usa set_alpha su una copia: su Mac quella strada perde
        # il modo di fusione e attorno alla pallina resta il quadrato
        # nero. Si moltiplica il canale alfa.
        ICONE_SPENTE[num] = smorzata(ICONE[num], 96)
    return ICONE_SPENTE[num]


def prepara_icone():
    """Le palline piccole delle imbucate: si disegnano una volta sola e poi
    si ricopiano, sono sempre uguali."""
    global M_FACCIA
    M_FACCIA = np.array([[1.0, 0.0, 0.0],
                         [0.0, 0.0, -1.0],
                         [0.0, 1.0, 0.0]], dtype=np.float32)
    ICONE_SPENTE.clear()
    ICONE_MINI.clear()
    for k in range(1, 16):
        # la sfera riempie il suo quadretto fino al bordo: senza un po'
        # di aria attorno la pallina risulta tagliata in cima
        sfera = rendi_sfera(k, M_FACCIA, ICONA_R, 1.5, 1.5)
        aria = 2
        q = pygame.Surface((sfera.get_width() + aria * 2,
                            sfera.get_height() + aria * 2), pygame.SRCALPHA)
        q.blit(sfera, (aria, aria))
        ICONE[k] = q


def _prepara_stecca(img):
    """La stecca pronta per il gioco: si toglie il vuoto attorno, si
    gira se serve e si porta a misura. Il disegno va tenuto col calcio a
    destra, perche' e' da quel capo che si appoggia dietro la bianca;
    se la foto ha la punta a destra la si volta, cosi' va bene
    qualunque immagine si metta nella cartella."""
    r = img.get_bounding_rect()
    if r.w > 4 and r.h > 0:
        img = img.subsurface(r).copy()
    if HA_NUMPY:
        a = pygame.surfarray.array_alpha(img)       # [x][y]
        meta = max(1, a.shape[0] // 2)
        # la punta e' il capo sottile: se e' a destra, si gira
        if (a[meta:] > 20).sum() < (a[:meta] > 20).sum():
            img = pygame.transform.flip(img, True, False)
    # lunga come una stecca vera: un metro e quarantacinque su un campo
    # da due e ventiquattro, in proporzione al tavolo che si vede
    lunga = max(120, int(PLAY.w * 145.0 / 224.0))
    k = lunga / float(img.get_width())
    return pygame.transform.smoothscale(
        img, (lunga, max(3, int(img.get_height() * k))))


FONT_TEX = [None]


def misura_palle(gioco):
    """Alla piramide le palle sono un po' piu' grosse; negli altri giochi
    tornano come sono. Le buche restano le stesse."""
    global BALL_R, OMBRA
    nuovo = BALL_R_BASE * (PALLE_PIRAMIDE if gioco == 8 else 1.0)
    if abs(nuovo - BALL_R) > 1e-6:
        BALL_R = nuovo
        if HA_NUMPY and OMBRA is not None:
            OMBRA = _fai_ombra()


def applica_palle():
    """Cambiato il set, o cambiato gioco: si ridipingono le palle e le
    palline delle imbucate, ognuna col set del suo gioco."""
    if not HA_NUMPY or FONT_TEX[0] is None:
        return
    for k in range(16):
        TESSITURE[k] = _tessitura(k, FONT_TEX[0], _leggi_asset(k))
    for k in SN_ROSSI + SN_COLORI + (BI_GIALLA, BI_PALLINO):
        TESSITURE[k] = _tessitura(k, FONT_TEX[0])
    ICONE_SPENTE.clear()
    ICONE_MINI.clear()
    prepara_icone()


def prepara_sfere(font):
    global LUCE, STECCA_IMG, OMBRA
    FONT_TEX[0] = font
    # la stecca dell'asset, se c'e': quella e' un bastone, ruotarla piatta
    # e' giusto e basta
    f = os.path.join(GFX, "pool_cue.png")
    if os.path.exists(f):
        try:
            STECCA_IMG = _prepara_stecca(
                pygame.image.load(f).convert_alpha())
        except pygame.error:
            STECCA_IMG = None
    if not HA_NUMPY:
        return
    for k in range(16):
        TESSITURE[k] = _tessitura(k, font, _leggi_asset(k))
    for k in SN_ROSSI + SN_COLORI:
        TESSITURE[k] = _tessitura(k, font)
    for k in (BI_GIALLA, BI_PALLINO):
        TESSITURE[k] = _tessitura(k, font)
    L = np.array([-0.40, -0.52, -0.76], dtype=np.float32)
    LUCE = L / float(np.linalg.norm(L))
    # la seconda lampada, dall'altra parte e piu' debole: sul tavolo vero
    # ce n'e' sempre piu' di una, e sulla palla si vedono due puntini
    L2 = np.array([0.58, -0.26, -0.77], dtype=np.float32)
    globals()["LUCE_2"] = L2 / float(np.linalg.norm(L2))
    OMBRA = _fai_ombra()
    prepara_icone()


def ruota_palle(palle, dt):
    """Rotolamento senza strisciare: l'asse e' perpendicolare alla corsa."""
    if not HA_NUMPY:
        return
    for b in palle:
        if b.dentro:
            continue
        v = b.vel.length()
        if v < 0.01:
            continue
        ang = v * dt / BALL_R
        b.M = _rot((b.vel.y / v, -b.vel.x / v, 0.0), ang) @ b.M


def rendi_sfera(num, M, R, fx, fy):
    """Disegna la palla numero num, girata come dice M, dentro un quadretto.
    fx e fy sono i decimali della posizione: servono a far scivolare la
    palla sotto al pixel invece di farla saltellare."""
    D0 = int(math.ceil(R * 2)) + 3

    # si disegna al doppio della misura e si rimpicciolisce: e' il modo
    # piu' semplice per togliere la scalettatura dal contorno e dai numeri
    S = 2
    D = D0 * S
    g = (np.arange(D, dtype=np.float32) + 0.5) / S
    ux = (g - fx - R) / R
    uy = (g - fy - R) / R
    NX = np.repeat(ux[:, None], D, axis=1)
    NY = np.repeat(uy[None, :], D, axis=0)
    d2 = NX * NX + NY * NY
    dentro = d2 <= 1.0
    if not dentro.any():
        return None

    w = np.sqrt(np.clip(1.0 - d2, 0.0, 1.0))
    # la normale guarda verso di noi: z entra nello schermo, quindi -w
    nor = np.stack((NX[dentro], NY[dentro], -w[dentro]), axis=1)

    # dal punto che vedo al punto della sua superficie
    t = nor @ M
    lon = np.arctan2(t[:, 1], t[:, 0])
    lat = np.arccos(np.clip(t[:, 2], -1.0, 1.0))
    tx = ((lon / (2.0 * math.pi) + 0.5) * (TEX_W - 1)).astype(np.int32)
    ty = (lat / math.pi * (TEX_H - 1)).astype(np.int32)
    col = TESSITURE[num][tx, ty]

    # Come e' illuminata la palla. Sopra al tavolo c'e' la lampada
    # principale da sinistra e una seconda piu' debole dall'altra parte,
    # come nelle sale vere. Poi tre cose che fanno la sfera:
    #   il bordo si scurisce, perche' li' la superficie scappa via e la
    #   luce la prende di striscio - e' quell'alone che si vede sempre
    #   sulle palle da biliardo, e da solo stacca la palla dal panno;
    #   sotto, dove il panno riflette, torna su un filo di luce;
    #   e i due puntini lucidi, tenuti piccoli.
    diff = np.clip(nor @ LUCE, 0.0, 1.0)
    diff2 = np.clip(nor @ LUCE_2, 0.0, 1.0)
    z = w[dentro]                       # uno al centro, zero sul bordo
    bordo = 0.34 + 0.66 * z ** 0.42
    rimbalzo = np.clip(NY[dentro], 0.0, 1.0) ** 5 * (1.0 - z) ** 2.0

    col = col * ((0.42 + 0.58 * diff + 0.12 * diff2) * bordo)[:, None]
    col += (56.0 * diff ** 16)[:, None]
    col += (18.0 * diff2 ** 26)[:, None]
    col += (26.0 * rimbalzo)[:, None]
    np.clip(col, 0.0, 255.0, out=col)

    rgb = np.zeros((D, D, 3), dtype=np.uint8)
    rgb[dentro] = col.astype(np.uint8)
    # bordo sfumato su mezzo pixel, se no il contorno e' seghettato
    alfa = np.clip((1.0 - np.sqrt(d2)) * R * S * 1.6 + 0.5, 0.0, 1.0) * 255.0

    grande = pygame.Surface((D, D), pygame.SRCALPHA)
    a = pygame.surfarray.pixels3d(grande)
    a[:] = rgb
    del a
    a = pygame.surfarray.pixels_alpha(grande)
    a[:] = alfa.astype(np.uint8)
    del a

    return pygame.transform.smoothscale(grande, (D0, D0))


def disegna_sfera(sc, b):
    R = BALL_R
    # posizione con la virgola: il resto sotto al pixel entra nel calcolo,
    # cosi' a velocita' bassa la palla scivola invece di saltellare
    x0 = b.pos.x - R - 1.0
    y0 = b.pos.y - R - 1.0
    ix = int(math.floor(x0))
    iy = int(math.floor(y0))
    surf = rendi_sfera(b.num, b.M, R, x0 - ix, y0 - iy)
    if surf is not None:
        sc.blit(surf, (ix, iy))


# ---------------------------------------------------------------- la palla


class Palla:
    def __init__(self, num, pos):
        self.num = num                      # 0 = bianca
        self.pos = Vector2(pos)
        self.vel = Vector2(0, 0)
        self.dentro = False
        self.di_sponda = False          # ha preso sponda in questo colpo
        # Come e' girata la palla: una matrice 3x3 che porta la sua
        # superficie nel mondo. Parte storta a caso, cosi' non sono
        # tutte allineate in partenza.
        if HA_NUMPY:
            self.M = _rot_casuale()
        else:
            self.M = None

    @property
    def piena(self):
        return 1 <= self.num <= 7

    @property
    def mezza(self):
        return 9 <= self.num <= 15

    def gruppo(self):
        if self.piena:
            return "solids"
        if self.mezza:
            return "stripes"
        return None

    def ferma(self):
        return self.vel.length_squared() < 0.001


# ------------------------------------------------------------ il triangolo


def nuova_partita(gioco=0):
    """Le palle come stanno all'inizio: il triangolo da quindici per la
    palla 8, il rombo da nove per la palla 9."""
    if gioco == 1:
        return rombo_da_nove()
    if gioco == 5:
        return triangolo_da_dieci()
    if gioco == 2:
        return tavolo_da_snooker()
    if gioco == 6:
        return tavolo_da_snooker(6)
    if gioco in (3, 7):
        return tavolo_a_birilli()
    if gioco == 8:
        return piramide()
    palle = []
    cue = Palla(0, (LINEA_X - PLAY.w * 0.07, PLAY.centery))
    palle.append(cue)

    # ordine del triangolo: 8 al centro, agli angoli una piena e una mezza
    ordine = [1, 11, 5, 8, 10, 3, 14, 7, 2, 13, 4, 15, 6, 12, 9]
    random.shuffle(ordine)
    if 8 in ordine:
        ordine.remove(8)
    # posto fisso: l'8 sta nella terza fila, in mezzo
    fila_di = [1, 2, 3, 4, 5]
    idx = 0
    apice = Vector2(PALLINO)
    passo = BALL_R * 2 + 0.6

    for f, quanti in enumerate(fila_di):
        for k in range(quanti):
            x = apice.x + f * passo * 0.866
            y = apice.y + (k - (quanti - 1) / 2.0) * passo
            if f == 2 and k == 1:
                num = 8
            else:
                num = ordine[idx]
                idx += 1
            palle.append(Palla(num, (x, y)))

    return palle


def sn_posti():
    """I punti del tavolo da snooker, presi in proporzione dal tavolo
    vero: la linea di partenza a un quinto, i tre colori bassi su
    quella, il blu in mezzo, il rosa a tre quarti e il nero in fondo."""
    w, h = float(PLAY.w), float(PLAY.h)
    baulk = PLAY.left + w * BAULK
    raggio_d = h * RAGGIO_D
    return {
        SN_GIALLO: Vector2(baulk, PLAY.centery + raggio_d),
        SN_VERDE: Vector2(baulk, PLAY.centery - raggio_d),
        SN_MARRONE: Vector2(baulk, PLAY.centery),
        SN_BLU: Vector2(PLAY.centerx, PLAY.centery),
        # rosa e nero: i due puntini segnati nel disegno del tavolo
        SN_ROSA: Vector2(PLAY.left + w * 0.7511, PLAY.centery),
        SN_NERO: Vector2(PLAY.left + w * 0.9092, PLAY.centery),
    }


def tavolo_da_snooker(rossi=15):
    """Quindici rossi a triangolo dietro il rosa, e i sei colori al loro
    posto. La bianca parte dentro la D, com'e' giusto."""
    posti = sn_posti()
    palle = [Palla(0, (PLAY.left + PLAY.w * BAULK - BALL_R * 2,
                       PLAY.centery + PLAY.h * 0.06))]
    for num, dove in posti.items():
        palle.append(Palla(num, dove))
    passo = BALL_R * 2 + 0.5
    # l'apice del triangolo sta dietro il rosa, ma senza toccarlo
    apice = Vector2(posti[SN_ROSA].x + passo * 1.12, PLAY.centery)
    k = 0
    file_rossi = (1, 2, 3, 4, 5) if rossi >= 15 else (1, 2, 3)
    for fi, quanti in enumerate(file_rossi):
        for j in range(quanti):
            x = apice.x + fi * passo * 0.866
            y = apice.y + (j - (quanti - 1) / 2.0) * passo
            palle.append(Palla(SN_ROSSI[k], (x, y)))
            k += 1
    return palle


def rombo_da_nove():
    """Il rombo della palla 9: la uno in punta, la nove nel mezzo, le
    altre a caso. Le file sono una, due, tre, due, una."""
    palle = [Palla(0, (LINEA_X - PLAY.w * 0.07, PLAY.centery))]
    altre = [2, 3, 4, 5, 6, 7, 8]
    random.shuffle(altre)
    apice = Vector2(PALLINO)
    passo = BALL_R * 2 + 0.6
    fila_di = [1, 2, 3, 2, 1]
    idx = 0
    for fi, quanti in enumerate(fila_di):
        for k in range(quanti):
            x = apice.x + fi * passo * 0.866
            y = apice.y + (k - (quanti - 1) / 2.0) * passo
            if fi == 0:
                num = 1                     # la uno sempre in punta
            elif fi == 2 and k == 1:
                num = 9                     # la nove sempre in mezzo
            else:
                num = altre[idx]
                idx += 1
            palle.append(Palla(num, (x, y)))
    return palle


def piramide():
    """La piramide russa: quindici bianche numerate a triangolo sul
    punto, e la rossa dietro la linea. Si tira con la rossa solo alla
    spaccata: poi con qualunque palla."""
    palle = [Palla(0, (LINEA_X - PLAY.w * 0.07, PLAY.centery))]
    numeri = list(range(1, 16))
    random.shuffle(numeri)
    apice = Vector2(PALLINO)
    passo = BALL_R * 2 + 0.6
    idx = 0
    for fi, quanti in enumerate((1, 2, 3, 4, 5)):
        for k in range(quanti):
            x = apice.x + fi * passo * 0.866
            y = apice.y + (k - (quanti - 1) / 2.0) * passo
            palle.append(Palla(numeri[idx], (x, y)))
            idx += 1
    return palle


def triangolo_da_dieci():
    """Il triangolo del 10-ball: quattro file, la uno in punta, la dieci
    in mezzo alla terza fila, le altre a caso."""
    palle = [Palla(0, (LINEA_X - PLAY.w * 0.07, PLAY.centery))]
    altre = [2, 3, 4, 5, 6, 7, 8, 9]
    random.shuffle(altre)
    apice = Vector2(PALLINO)
    passo = BALL_R * 2 + 0.6
    idx = 0
    for fi, quanti in enumerate((1, 2, 3, 4)):
        for k in range(quanti):
            x = apice.x + fi * passo * 0.866
            y = apice.y + (k - (quanti - 1) / 2.0) * passo
            if fi == 0:
                num = 1
            elif fi == 2 and k == 1:
                num = 10
            else:
                num = altre[idx]
                idx += 1
            palle.append(Palla(num, (x, y)))
    return palle


# ---------------------------------------------------------------- fisica


def passo_fisica(palle, dt, stato):
    """Un sottopasso di simulazione. Ritorna gli eventi del colpo."""
    senza_buche = bool(BIRILLI)         # il tavolo dei birilli non ne ha
    for b in palle:
        if b.dentro:
            continue
        b.pos += b.vel * dt

    # sponde
    for b in palle:
        if b.dentro:
            continue

        # ogni sponda e' aperta solo davanti alle proprie buche; al
        # biliardo all'italiana le buche non ci sono e la sponda gira
        # tutt'intorno senza interruzioni
        if senza_buche:
            apX = apY = False
        else:
            apX = any(abs(b.pos.y - g) < VARCO for g in VARCO_Y)
            apY = any(abs(b.pos.x - g) < (VARCO_MID if g == PLAY.centerx
                                          else VARCO)
                      for g in VARCO_X)

        # La sponda non restituisce solo di meno di quanto arriva: si
        # mangia anche una parte della velocita' di striscio, quella
        # parallela alla sponda, perche' la gomma frena di lato. E la
        # palla riparte strisciando, non rotolando, quindi perde ancora
        # nel primo pezzo. Senza queste due cose una palla di striscio
        # faceva quattro sponde senza rallentare mai.
        toccata = False
        # quanto forte entra nella gomma: solo la parte che le va
        # contro, non quella di striscio. E' quella che fa il rumore:
        # una palla veloce che la sfiora quasi non si sente.
        botta = 0.0
        if not apX:
            if b.pos.x - BALL_R < PLAY.left:
                b.pos.x = PLAY.left + BALL_R
                botta = max(botta, abs(b.vel.x))
                b.vel.x = -b.vel.x * REST_SPONDA
                b.vel.y *= REST_LATO
                toccata = True
            elif b.pos.x + BALL_R > PLAY.right:
                b.pos.x = PLAY.right - BALL_R
                botta = max(botta, abs(b.vel.x))
                b.vel.x = -b.vel.x * REST_SPONDA
                b.vel.y *= REST_LATO
                toccata = True
        if not apY:
            if b.pos.y - BALL_R < PLAY.top:
                b.pos.y = PLAY.top + BALL_R
                botta = max(botta, abs(b.vel.y))
                b.vel.y = -b.vel.y * REST_SPONDA
                b.vel.x *= REST_LATO
                toccata = True
            elif b.pos.y + BALL_R > PLAY.bottom:
                b.pos.y = PLAY.bottom - BALL_R
                botta = max(botta, abs(b.vel.y))
                b.vel.y = -b.vel.y * REST_SPONDA
                b.vel.x *= REST_LATO
                toccata = True

        if toccata:
            # riparte strisciando: l'effetto che aveva la spinge contro
            # il verso nuovo e se ne va un altro pezzo
            b.v_rotola = b.vel.length() * 5.0 / 7.0
            b.v_era = b.vel.length()
            stato["sponda"] = True
            b.di_sponda = True
            segna(stato, "rail", botta)
            # l'effetto laterale si scarica sulla sponda
            if b.num == stato.get("bilia", 0) \
                    and abs(stato["spin_x"]) > 0.01:
                perp = Vector2(-b.vel.y, b.vel.x)
                if perp.length_squared() > 0.001:
                    b.vel += perp.normalize() * stato["spin_x"] * 52.9 * K
                stato["spin_x"] *= 0.4

    # palla contro palla
    n = len(palle)
    for i in range(n):
        a = palle[i]
        if a.dentro:
            continue
        for j in range(i + 1, n):
            b = palle[j]
            if b.dentro:
                continue

            d = b.pos - a.pos
            dist2 = d.length_squared()
            lim = BALL_R * 2
            if dist2 >= lim * lim or dist2 < 1e-9:
                continue

            dist = math.sqrt(dist2)
            nrm = d / dist

            # separa le due palle sovrapposte
            sovra = lim - dist
            a.pos -= nrm * (sovra / 2)
            b.pos += nrm * (sovra / 2)

            # urto elastico fra masse uguali: si scambiano le componenti
            # lungo la normale, quelle tangenti restano
            va = a.vel.dot(nrm)
            vb = b.vel.dot(nrm)
            if va - vb <= 0:
                continue

            scambio = (va - vb) * REST_PALLA
            segna(stato, "ball", va - vb)
            if senza_buche:
                stato.setdefault("cronaca", []).append(
                    ("urto", a.num, b.num))
            a.vel -= nrm * scambio
            b.vel += nrm * scambio

            # prima palla toccata dalla bianca in questo colpo
            if stato["prima"] is None:
                chi = stato.get("bilia", 0)     # alla piramide non e' la 0
                if a.num == chi:
                    stato["prima"] = b.num
                elif b.num == chi:
                    stato["prima"] = a.num

            # effetto sopra/sotto: la bianca prosegue o torna indietro
            if stato["spin_y"] != 0.0:
                chi = stato.get("bilia", 0)
                cue = a if a.num == chi else (b if b.num == chi else None)
                if cue is not None:
                    cue.vel += nrm * (stato["spin_y"] * 202.8 * K) * (1 if cue is a else -1)
                    stato["spin_y"] *= 0.35

    # i birilli: cadono appena una bilia li tocca
    for bir in BIRILLI:
        if not bir.in_piedi:
            continue
        for b in palle:
            if b.dentro or b.vel.length_squared() < 1e-6:
                continue
            if (b.pos - bir.pos).length() < BALL_R + BIRILLO_R:
                bir.in_piedi = False
                stato.setdefault("cronaca", []).append(
                    ("birillo", bir.rosso, b.num))
                segna(stato, "ball", b.vel.length() * 0.6)
                b.vel *= 0.94
                break

    # buche
    for b in palle:
        if b.dentro:
            continue
        for p, presa in (() if senza_buche else zip(BUCHE, PRESA)):
            if (b.pos - p).length() < presa:
                b.dentro = True
                segna(stato, "pocket", b.vel.length())
                b.vel.update(0, 0)
                stato["imbucate"].append(b.num)
                if getattr(b, "di_sponda", False):
                    stato["di_sponda"] = True
                break

    # Rete di sicurezza. Vicino alle buche la sponda non c'e', quindi una
    # palla lanciata forte di striscio puo' scappare dal tavolo. Se e'
    # finita fuori vicino a una buca vuol dire che e' entrata; altrimenti
    # la si rimette dentro e basta: fuori non ci va mai nessuna.
    for b in palle:
        if b.dentro:
            continue
        if (PLAY.left - 2.0 <= b.pos.x <= PLAY.right + 2.0 and
                PLAY.top - 2.0 <= b.pos.y <= PLAY.bottom + 2.0):
            continue

        if senza_buche:
            b.pos.x = max(PLAY.left + BALL_R,
                          min(PLAY.right - BALL_R, b.pos.x))
            b.pos.y = max(PLAY.top + BALL_R,
                          min(PLAY.bottom - BALL_R, b.pos.y))
            b.vel *= 0.5
            continue

        k = min(range(len(BUCHE)), key=lambda i: (b.pos - BUCHE[i]).length())
        if (b.pos - BUCHE[k]).length() < PRESA_FUORI[k]:
            b.dentro = True
            segna(stato, "pocket", b.vel.length())
            b.vel.update(0, 0)
            stato["imbucate"].append(b.num)
            if getattr(b, "di_sponda", False):
                stato["di_sponda"] = True
        else:
            b.pos.x = max(PLAY.left + BALL_R, min(PLAY.right - BALL_R, b.pos.x))
            b.pos.y = max(PLAY.top + BALL_R, min(PLAY.bottom - BALL_R, b.pos.y))
            b.vel *= 0.5
            stato["sponda"] = True

    # L'attrito, in due tempi come sul tavolo vero. Appena la palla
    # prende una botta non rotola: striscia sul panno, e li' il freno e'
    # venti volte piu' forte. Finito di strisciare comincia a rotolare e
    # da quel momento scivola via quasi senza perdere niente. Per questo
    # un tiro calibrato deve correre: sta rotolando quasi subito.
    scivolo = DECEL_SCIVOLO * dt
    rotola = DECEL * dt
    for b in palle:
        if b.dentro:
            continue
        v = b.vel.length()
        if v > getattr(b, "v_era", 0.0) + 0.5:
            # ha preso una botta: striscia finche' non scende a cinque
            # settimi, che e' dove il rotolamento diventa puro
            b.v_rotola = v * 5.0 / 7.0
        giu = scivolo if v > getattr(b, "v_rotola", 0.0) else rotola
        if v <= FERMA + giu:
            b.vel.update(0, 0)
            b.v_era = 0.0
        else:
            b.vel *= (v - giu) / v
            b.v_era = v - giu


def tutto_fermo(palle):
    return all(b.dentro or b.ferma() for b in palle)


# ----------------------------------------------------------------- regole


# ------------------------------------------------ i messaggi della partita
#
# Il messaggio non si scrive una volta per tutte: si tiene la chiave e
# gli argomenti, e si traduce ogni volta che si disegna. Cosi' se si
# cambia lingua a meta' partita, anche la scritta sul tavolo cambia.
class _DaTradurre:
    """Un pezzo del messaggio che va tradotto al momento: una parola del
    dizionario, o il nome di un giocatore (che puo' essere "Player 1")."""
    def __init__(self, tipo, valore):
        self.tipo, self.valore = tipo, valore

    def testo(self):
        if self.tipo == "n":
            return nome(self.valore)
        return T(self.valore)


def _mt(chiave):
    return _DaTradurre("t", chiave)


def _mn(chi):
    return _DaTradurre("n", chi)


def testo_msg(chiave, args):
    if not args:
        return T(chiave)
    pezzi = tuple(a.testo() if isinstance(a, _DaTradurre) else a
                  for a in args)
    try:
        return T(chiave) % pezzi
    except (TypeError, ValueError):
        return T(chiave)


def imposta_msg(obj, chiave, args=None):
    if args is None:
        args = ()
    elif not isinstance(args, tuple):
        args = (args,)
    obj.msg_t, obj.msg_a = chiave, args
    obj.messaggio = testo_msg(chiave, args)


def messaggio_ora(partita):
    """Il messaggio nella lingua di adesso."""
    if getattr(partita, "msg_t", None):
        return testo_msg(partita.msg_t, partita.msg_a)
    return partita.messaggio



class Partita:
    def __init__(self, gioco=0):
        self.gioco = gioco              # 0 palla 8, 1 palla 9
        self.reset()

    def reset(self):
        if self.gioco not in (3, 7):
            del BIRILLI[:]          # il castello e' solo del cinque birilli
        self.palle = nuova_partita(self.gioco)
        self.vincitore = None
        self.festa = None
        self.ultimo_fallo = False
        self.ultima_delusione = None
        self.serie = 0                  # buche di fila, per il tifo
        self.turno = 0                      # 0 o 1
        self.gruppo = [None, None]          # "solids" / "stripes"
        self.aperto = True
        self.spaccata = True
        self.ball_in_hand = False
        self.finita = False
        self.msg_key = "breaks"
        imposta_msg(self, "breaks", _mn(0))
        self.msg_chi = 0
        self.mie = [[], []]             # le palle imbucate da ognuno
        # lo snooker: punti, break in corso e che palla si deve giocare
        self.punti = [0, 0]
        self.serie_punti = 0
        self.on_rosso = True
        self.on_quale = None
        self.conto_break = {}       # di che palle e' fatta la serie
        self.free_ball = False      # dopo un fallo che lascia imbrigliati
        self.missati = 0            # falli di fila senza toccare niente
        self.visite = 0             # blackball: visite in piu' dopo un fallo
        self.bilia_tiro = 0         # piramide: la palla con cui si tira
        self.scatto = None
        self.spin = Vector2(0, 0)

    def cue(self):
        """La bilia con cui si tira. Ai birilli ognuno ha la sua, quindi
        cambia col turno."""
        cerco = 0
        if self.gioco in (3, 7) and self.turno == 1:
            cerco = BI_GIALLA
        if self.gioco == 8:
            # alla piramide si tira con la palla scelta; se e' in buca,
            # con la rossa, e se manca anche quella con la prima che c'e'
            vive = [b for b in self.palle if not b.dentro]
            for want in (getattr(self, "bilia_tiro", 0), 0):
                for b in vive:
                    if b.num == want:
                        return b
            return vive[0] if vive else None
        for b in self.palle:
            if b.num == cerco:
                return b
        return None

    def cambia_bilia(self, verso=1):
        """Piramide: passa alla palla dopo come palla da tiro."""
        vive = sorted(b.num for b in self.palle if not b.dentro)
        if not vive:
            return
        ora = self.cue().num if self.cue() else vive[0]
        i = vive.index(ora) if ora in vive else 0
        self.bilia_tiro = vive[(i + verso) % len(vive)]

    def bi_avv(self):
        """Ai birilli: il numero della bilia dell'avversario, quella che
        si deve colpire per prima."""
        return BI_GIALLA if self.turno == 0 else 0

    def restanti(self, gruppo):
        return [b for b in self.palle
                if not b.dentro and b.gruppo() == gruppo]

    def prese(self, gruppo, gi=None):
        """Le palle in buca da mostrare sotto al nome. Alla palla 8 sono
        quelle del gruppo, che tanto e' di uno solo; alla palla 9 non ci
        sono gruppi, quindi si tiene il conto di chi le ha imbucate."""
        if self.gioco in (3, 7):
            return []               # ai birilli non si imbuca niente
        if self.gioco in (1, 5, 8):
            return sorted(self.mie[gi]) if gi is not None else []
        if gruppo is None:
            return []
        return sorted(b.num for b in self.palle
                      if b.dentro and b.gruppo() == gruppo)

    def palla_vince(self):
        """Quella che chiude la partita: la 9, o la 10 al 10-ball."""
        return 10 if self.gioco == 5 else 9

    def bassa(self, anche=()):
        """La palla piu' bassa ancora sul tavolo. Con anche=... si
        contano dentro anche quelle appena imbucate, per sapere com'era
        il tavolo prima del colpo."""
        n = [b.num for b in self.palle if not b.dentro and b.num != 0]
        n += [k for k in anche if k != 0]
        return min(n) if n else None

    def sn_bersagli(self, anche=()):
        """Quali palle si possono colpire adesso. Con anche=... si
        contano dentro quelle appena imbucate, per sapere com'era il
        tavolo prima del colpo."""
        if self.on_quale is not None:
            return [self.on_quale]
        quali = SN_ROSSI if self.on_rosso else SN_COLORI
        fuori = [b.num for b in self.palle
                 if not b.dentro and b.num in quali]
        return fuori + [n for n in anche if n in quali]

    def sn_rossi_rimasti(self, anche=()):
        return len([b for b in self.palle
                    if not b.dentro and b.num in SN_ROSSI]) + \
            len([n for n in anche if n in SN_ROSSI])

    def sn_prossimo_colore(self):
        """Nella fase finale i colori si giocano in ordine: il piu' basso
        ancora sul tavolo."""
        vivi = [b.num for b in self.palle
                if not b.dentro and b.num in SN_COLORI]
        if not vivi:
            return None
        return min(vivi, key=lambda n: SN_VALORE[n])

    def prima_legale(self, num):
        """Se la prima palla che tocchi e' delle tue. A tavolo aperto vale
        tutto tranne l'8; l'8 solo quando hai finito il tuo gruppo. E' lo
        stesso criterio con cui poi viene dato il fallo."""
        if num is None:
            return True
        if self.gioco in (3, 7):
            return num == self.bi_avv()
        if self.gioco in (1, 5):
            # alla palla 9 si tocca sempre per prima la piu' bassa
            return num == self.bassa()
        if self.gioco in (2, 6):
            if getattr(self, "free_ball", False):
                return True         # free ball: per questo colpo vale tutto
            return num in self.sn_bersagli()
        g = self.gruppo[self.turno]
        if num == 8:
            return self.puo_tirare_8(self.turno)
        if g is None:
            return True
        return (1 <= num <= 7) == (g == "solids")

    def puo_tirare_8(self, gi):
        g = self.gruppo[gi]
        if g is None:
            return False
        return len(self.restanti(g)) == 0

    # ------------------------------------------------- fine del colpo

    def valuta(self, stato):
        if self.gioco == 8:
            return self.valuta_pir(stato)
        if self.gioco in (1, 5):
            return self.valuta_9(stato)
        if self.gioco in (2, 6):
            return self.valuta_sn(stato)
        if self.gioco in (3, 7):
            return self.valuta_5p(stato)
        imbucate = stato["imbucate"]
        self.festa = None                   # il pubblico: applausi o fischi
        self.ultimo_fallo = False
        # Com'era il tavolo PRIMA di questo colpo: le palle appena
        # imbucate qui contano ancora come se fossero fuori, se no
        # l'otto libero risulta gia' libero e non si annuncia mai.
        def poteva_8(gi):
            g = self.gruppo[gi]
            if g is None:
                return False
            mancano = len(self.restanti(g))
            mancano += sum(1 for n in imbucate if n not in (0, 8) and
                           (1 <= n <= 7) == (g == "solids"))
            return mancano == 0

        otto_prima = (poteva_8(0), poteva_8(1))
        cue_dentro = 0 in imbucate
        otto_dentro = 8 in imbucate
        io = self.turno
        avv = 1 - io

        fallo = False
        motivo = ""

        if otto_dentro:
            if self.puo_tirare_8(io) and not cue_dentro:
                self.finita = True
                dice("game")
                self.festa = "vittoria"
                self.vincitore = io
                self.msg_key = "wins"
                imposta_msg(self, "wins", _mn(io))
                self.msg_chi = io
            else:
                self.finita = True
                dice("foul", "game")
                self.festa = "vittoria"
                self.vincitore = avv
                self.msg_key = "wins_early"
                imposta_msg(self, "wins_early", _mn(avv))
                self.msg_chi = avv
            return

        if stato["prima"] is None:
            fallo, motivo = True, "f_nohit"
        elif cue_dentro:
            fallo, motivo = True, "f_cue"
        elif not imbucate and not stato["sponda"]:
            fallo, motivo = True, "f_norail"
        else:
            # prima palla toccata: deve essere del proprio gruppo
            g = self.gruppo[io]
            if g is not None:
                prima = stato["prima"]
                giusto = (1 <= prima <= 7) if g == "solids" else (9 <= prima <= 15)
                if prima == 8 and not self.puo_tirare_8(io):
                    fallo, motivo = True, "f_eight"
                elif prima != 8 and not giusto:
                    fallo, motivo = True, "f_group"

        # assegnazione dei gruppi alla prima buca utile
        mie = 0
        if self.aperto and not fallo:
            buone = [n for n in imbucate if n not in (0, 8)]
            if buone:
                g = "solids" if 1 <= buone[0] <= 7 else "stripes"
                self.gruppo[io] = g
                self.gruppo[avv] = "stripes" if g == "solids" else "solids"
                self.aperto = False
                if self.gioco != 4:         # al blackball sono rosse e gialle
                    dice(g)                 # "solids" oppure "stripes"
                mie = sum(1 for n in buone
                          if (1 <= n <= 7) == (g == "solids"))
        elif not self.aperto:
            g = self.gruppo[io]
            for n in imbucate:
                if n in (0, 8):
                    continue
                if (1 <= n <= 7) == (g == "solids"):
                    mie += 1

        self.spaccata = False

        if cue_dentro:
            self.rimetti_bianca()

        if fallo:
            self.ultimo_fallo = True
            dice("foul", "ball_in_hand")
            self.turno = avv
            self.ball_in_hand = True
            self.msg_key = "foul"
            imposta_msg(self, "foul", (_mt(motivo), _mn(avv)))
            self.msg_chi = avv
            # al blackball dopo un fallo l'avversario ha due visite: se
            # sbaglia la prima, tira ancora
            self.visite = 1 if self.gioco == 4 else 0
            return

        # Quanto applaudono, da uno a tre: C e' il piu' corto e tiepido,
        # B sta in mezzo, A e' quello che incita. Si sale con la serie di
        # buche di fila e con quante ne entrano in un colpo solo.
        if mie >= 1:
            self.serie += 1
        else:
            self.serie = 0
        lode = 0
        if self.serie >= 4:
            lode = 3
        elif self.serie == 3:
            lode = 2
        elif self.serie == 2:
            lode = 1
        if mie >= 3:
            lode = 3
        elif mie == 2:
            lode = max(lode, 2)
        if mie >= 1 and stato.get("di_sponda"):
            lode = max(lode, 2)              # entrata di sponda, vale doppio
        if mie >= 1 and self.puo_tirare_8(io):
            lode = max(lode, 2)              # gruppo chiuso, si apre l'otto
        if lode:
            self.festa = ("applauso_c", "applauso_b", "applauso_a")[lode - 1]

        for gi in (io, avv):
            if self.puo_tirare_8(gi) and not otto_prima[gi]:
                dice("eight_ball")

        if mie > 0:
            self.msg_key = "continues"
            imposta_msg(self, "continues", _mn(io))
            self.msg_chi = io
        elif self.gioco == 4 and getattr(self, "visite", 0) > 0:
            # la seconda visita dopo il fallo dell'altro
            self.visite -= 1
            self.msg_key = "bb_visit"
            imposta_msg(self, "bb_visit", _mn(io))
            self.msg_chi = io
        else:
            self.visite = 0
            self.turno = avv
            self.msg_key = "to_play"
            imposta_msg(self, "to_play", _mn(avv))
            self.msg_chi = avv

    def palla_in_bocca(self):
        """Una palla ferma proprio sul bordo della buca: quella in sala
        la vedono tutti e si sente."""
        if self.gioco in (3, 7):
            return False            # senza buche non c'e' bocca
        for b in self.palle:
            if b.dentro or b.num == 0:
                continue
            for q in BUCHE:
                if (b.pos - q).length() < PRESA_R + BALL_R * 0.9:
                    return True
        return False

    def delusione(self, stato):
        """Dopo un colpo andato male ogni tanto il pubblico se ne
        accorge: forte se c'e' stato fallo o se la palla e' rimasta sul
        bordo della buca, piano se semplicemente non e' entrato niente.
        Non tutte le volte, e mai due volte di fila la stessa, se no
        diventa una lagna."""
        if self.festa or self.finita:
            return
        mie = [n for n in stato["imbucate"] if n not in (0, 8)]
        if self.ultimo_fallo or self.palla_in_bocca():
            scelta, quanto = "delusione_forte", 0.55
        elif not mie:
            scelta, quanto = "delusione", 0.30
        else:
            return
        if scelta == self.ultima_delusione:
            quanto *= 0.35
        if random.random() > quanto:
            return
        self.ultima_delusione = scelta
        self.festa = scelta

    def valuta_5p(self, stato):
        """Il cinque birilli. Si colpisce per prima la bilia
        dell'avversario: se no e' fallo. Poi fanno punto i birilli
        buttati giu' dall'avversaria o dal pallino, mentre quelli presi
        dalla propria bilia li segna l'altro. Si tira a turno comunque,
        anche avendo fatto punto, e il castello si rimette in piedi a
        ogni tiro."""
        io = self.turno
        altro = 1 - io
        mia = 0 if io == 0 else BI_GIALLA
        avv = self.bi_avv()
        self.festa = None
        self.ultimo_fallo = False
        self.serie = 0

        legale = False
        fallo = False
        caduti = {io: [], altro: []}
        pall_avv = False
        pall_mia = False

        for ev in stato.get("cronaca", []):
            if ev[0] == "urto":
                a, b = ev[1], ev[2]
                if mia in (a, b):
                    q = b if a == mia else a
                    if not legale:
                        if q == avv:
                            legale = True
                        else:
                            fallo = True        # il pallino per primo
                    elif q == BI_PALLINO:
                        pall_mia = True
                elif legale and avv in (a, b) and BI_PALLINO in (a, b):
                    pall_avv = True
            else:
                rosso, chi = ev[1], ev[2]
                if not legale:
                    fallo = True                # birilli prima del contatto
                    caduti[altro].append(rosso)
                elif chi == mia:
                    caduti[altro].append(rosso)
                else:
                    caduti[io].append(rosso)

        if not legale:
            fallo = True                        # non l'ha proprio toccata

        def valore(giu):
            lat = len([r for r in giu if not r])
            if True in giu:
                if lat == 0:
                    return BI_ROSSO_SOLO
                return BI_ROSSO_CON + lat * BI_LATERALE
            return lat * BI_LATERALE

        p_io = valore(caduti[io])
        p_altro = valore(caduti[altro])
        if fallo:
            p_altro += BI_FALLO + p_io
            p_io = 0
        else:
            if pall_avv:
                p_io += BI_PALL_AVV
            if pall_mia:
                p_io += BI_PALL_MIA

        self.punti[io] += p_io
        self.punti[altro] += p_altro

        if fallo:
            self.ultimo_fallo = True
            self.msg_key = "bi_foul"
            imposta_msg(self, "bi_foul", (p_altro, _mn(altro)))
            self.msg_chi = altro
            dice("foul")
        elif p_io:
            self.msg_key = "bi_punti"
            imposta_msg(self, "bi_punti", (_mn(io), p_io))
            self.msg_chi = io
            self.festa = ("applauso_a" if p_io >= 12 else
                          "applauso_b" if p_io >= 8 else
                          "applauso_c" if p_io >= 4 else None)
        else:
            self.msg_key = "bi_zero"
            imposta_msg(self, "bi_zero")
            self.msg_chi = io

        for chi in (io, altro):
            if self.punti[chi] >= arrivo_birilli(self.gioco):
                self.finita = True
                self.vincitore = chi
                self.festa = "vittoria"
                self.msg_key = "wins"
                imposta_msg(self, "wins", _mn(chi))
                self.msg_chi = chi
                break

        if not self.finita:
            self.turno = altro
        self.spaccata = False
        rifai_castello(self.palle)

    def valuta_pir(self, stato):
        """La piramide libera: si tira con qualunque palla e vale ogni
        palla che entra, anche quella con cui si e' tirato se prima ha
        toccato un'altra. Chi ne fa otto vince. Fallo se non si tocca
        niente, o se non entra niente e nessuna palla va in sponda: le
        palle entrate tornano sul punto, chi ha sbagliato ne restituisce
        una delle sue, e l'altro tira con la palla in mano da dietro la
        linea."""
        imbucate = [n for n in stato["imbucate"]]
        io = self.turno
        avv = 1 - io
        self.festa = None
        self.ultimo_fallo = False
        fallo, motivo = False, ""
        if stato["prima"] is None:
            fallo, motivo = True, "f_nohit"
        elif not imbucate and not stato["sponda"]:
            fallo, motivo = True, "f_norail"
        self.spaccata = False
        if fallo:
            for n in imbucate:
                self.rimetti_palla(n)
            if self.mie[io]:
                n = self.mie[io].pop()
                self.punti[io] = max(0, self.punti[io] - 1)
                self.rimetti_palla(n)
            self.ultimo_fallo = True
            self.serie = 0
            dice("foul", "ball_in_hand")
            self.turno = avv
            self.ball_in_hand = True
            self.bilia_tiro = 0
            self.msg_key = "foul"
            imposta_msg(self, "foul", (_mt(motivo), _mn(avv)))
            self.msg_chi = avv
            return
        self.mie[io] += imbucate
        self.punti[io] += len(imbucate)
        if self.punti[io] >= PIRAMIDE_ARRIVO:
            self.finita = True
            dice("game")
            self.festa = "vittoria"
            self.vincitore = io
            self.msg_key = "wins"
            imposta_msg(self, "wins", _mn(io))
            self.msg_chi = io
            return
        if imbucate:
            self.serie += 1
            if len(imbucate) >= 2 or self.serie >= 3:
                self.festa = "applauso_b"
            self.msg_key = "continues"
            imposta_msg(self, "continues", _mn(io))
            self.msg_chi = io
        else:
            self.serie = 0
            self.turno = avv
            self.msg_key = "to_play"
            imposta_msg(self, "to_play", _mn(avv))
            self.msg_chi = avv

    def valuta_9(self, stato):
        """Le regole della palla 9: si tocca sempre per prima la piu'
        bassa, chiunque imbuchi qualcosa continua, e chi manda dentro la
        nove ha vinto. Sul fallo la nove torna sul tavolo."""
        imbucate = stato["imbucate"]
        cue_dentro = 0 in imbucate
        io, avv = self.turno, 1 - self.turno
        self.festa = None
        self.ultimo_fallo = False
        # com'era il tavolo prima del colpo
        prima_bassa = self.bassa(anche=[n for n in imbucate if n != 0])

        fallo, motivo = False, ""
        if stato["prima"] is None:
            fallo, motivo = True, "f_nohit"
        elif prima_bassa is not None and stato["prima"] != prima_bassa:
            fallo, motivo = True, "f_low"
        elif cue_dentro:
            fallo, motivo = True, "f_cue"
        elif not [n for n in imbucate if n != 0] and not stato["sponda"]:
            fallo, motivo = True, "f_norail"

        buone = [n for n in imbucate if n != 0]
        if not fallo:
            self.mie[io].extend(buone)

        if self.palla_vince() in imbucate:
            if not fallo:
                self.finita = True
                dice("game")
                self.festa = "vittoria"
                self.vincitore = io
                self.msg_key = "wins"
                imposta_msg(self, "wins", _mn(io))
                self.msg_chi = io
                return
            self.rimetti_palla(self.palla_vince())       # entrata su fallo: torna in gioco

        self.spaccata = False
        if cue_dentro:
            self.rimetti_bianca()

        if fallo:
            self.ultimo_fallo = True
            self.serie = 0
            dice("foul", "ball_in_hand")
            self.turno = avv
            self.ball_in_hand = True
            self.msg_key = "foul"
            imposta_msg(self, "foul", (_mt(motivo), _mn(avv)))
            self.msg_chi = avv
            return

        quante = len([n for n in buone if n != self.palla_vince()])
        if quante >= 1:
            self.serie += 1
        else:
            self.serie = 0
        lode = 0
        if self.serie >= 4:
            lode = 3
        elif self.serie == 3:
            lode = 2
        elif self.serie == 2:
            lode = 1
        if quante >= 2:
            lode = max(lode, 2)
        if quante >= 1 and stato.get("di_sponda"):
            lode = max(lode, 2)
        if lode:
            self.festa = ("applauso_c", "applauso_b", "applauso_a")[lode - 1]

        if quante > 0:
            self.msg_key = "continues"
            imposta_msg(self, "continues", _mn(io))
            self.msg_chi = io
        else:
            self.turno = avv
            self.msg_key = "to_play"
            imposta_msg(self, "to_play", _mn(avv))
            self.msg_chi = avv

    def valuta_sn(self, stato):
        """Le regole dello snooker: un rosso e poi un colore, finche' ci
        sono rossi; i colori tornano al loro posto ogni volta. Finiti i
        rossi si gioca l'ultimo colore e poi tutti in ordine, e quelli
        restano in buca. Chi sbaglia regala almeno quattro punti."""
        imbucate = stato["imbucate"]
        buone = [n for n in imbucate if n != 0]
        cue_dentro = 0 in imbucate
        io, avv = self.turno, 1 - self.turno
        self.festa = None
        self.ultimo_fallo = False
        veri = self.sn_bersagli(anche=buone)
        era_free = getattr(self, "free_ball", False)
        self.free_ball = False
        # col free ball vale qualunque palla, ma conta come quella giusta
        legali = [b.num for b in self.palle if b.num != 0] if era_free else veri
        vale_come = max([sn_valore(n) for n in veri] or [1]) if era_free else None
        prima = stato["prima"]

        fallo, pena = False, 0
        sbaglio_di_mira = False
        if prima is None:
            fallo, pena = True, 4
            sbaglio_di_mira = True
        elif prima not in legali:
            fallo = True
            pena = max(4, sn_valore(prima),
                       max([sn_valore(n) for n in veri] or [0]))
            sbaglio_di_mira = True
        sbagliate = [n for n in buone if n not in legali]
        if sbagliate:
            fallo = True
            pena = max(pena, 4, max(sn_valore(n) for n in sbagliate))
        if cue_dentro:
            fallo = True
            pena = max(pena, 4)
        if not fallo and not buone and not stato["sponda"]:
            fallo, pena = True, 4

        # i colori imbucati tornano al loro posto; i rossi restano in
        # buca, anche quelli entrati per sbaglio
        rimetti = [n for n in buone if n in SN_COLORI]
        if not fallo and self.sn_rossi_rimasti(anche=buone) == 0 and \
                self.on_quale is not None:
            rimetti = []                # nella fase finale restano dentro

        self.spaccata = False

        if fallo:
            self.ultimo_fallo = True
            self.punti[avv] += pena
            self.serie_punti = 0
            self.serie = 0
            self.conto_break = {}

            # il miss: hai tirato senza prendere la palla giusta pur
            # vedendola. L'altro ti rimette tutto com'era e ti fa
            # ritirare; alla terza volta il frame e' suo.
            miss = (sbaglio_di_mira and not era_free and
                    not getattr(self, "era_snookerato", False))
            if miss:
                self.missati += 1
                self.rimetti_foto()
                if self.missati >= 3:
                    self.finita = True
                    dice("foul_and_a_miss", "frame")
                    self.vincitore = avv
                    self.msg_key = "wins"
                    imposta_msg(self, "wins", _mn(avv))
                    self.msg_chi = avv
                    return
                dice("foul_and_a_miss")
                self.msg_key = "sn_miss"
                imposta_msg(self, "sn_miss", (pena, _mn(io)))
                self.msg_chi = io
                self.sn_riparti()
                return

            self.missati = 0
            for n in rimetti:
                self.rimetti_palla(n)
            dice("foul")
            if cue_dentro:
                self.rimetti_bianca()
                dice("ball_in_hand")
            self.turno = avv
            self.msg_key = "sn_foul"
            imposta_msg(self, "sn_foul", (pena, _mn(avv)))
            self.msg_chi = avv
            self.sn_riparti()
            # chi entra adesso e' imbrigliato? allora ha il free ball
            if self.sn_snookerato():
                self.free_ball = True
                dice("free_ball")
            return

        self.missati = 0

        if era_free and buone:
            # la palla nominata vale come quella che dovevi giocare, e
            # torna al suo posto invece di restare in buca
            guadagno = vale_come * len(buone)
            rimetti = [n for n in buone if n in SN_COLORI or n in SN_ROSSI]
        else:
            guadagno = sum(sn_valore(n) for n in buone)
        self.punti[io] += guadagno
        self.serie_punti += guadagno
        for n in buone:
            k = n if n in SN_COLORI else SN_ROSSI[0]
            self.conto_break[k] = self.conto_break.get(k, 0) + 1
        for n in rimetti:
            self.rimetti_palla(n)

        if buone:
            self.serie += 1
            if self.serie_punti > 0:
                dice("n_%03d" % min(147, self.serie_punti))
            if self.serie_punti >= 30:
                self.festa = "applauso_a"
            elif self.serie_punti >= 16:
                self.festa = "applauso_b"
            elif len(buone) > 1 or self.serie >= 2:
                self.festa = "applauso_c"
            # cosa si gioca adesso
            if self.sn_rossi_rimasti() > 0:
                if self.on_quale is None and self.on_rosso:
                    self.on_rosso = False       # preso un rosso: ora il colore
                else:
                    self.on_rosso = True
            else:
                self.sn_riparti()
            self.msg_key = "continues"
            imposta_msg(self, "continues", _mn(io))
            self.msg_chi = io
        else:
            self.serie = 0
            self.serie_punti = 0
            self.conto_break = {}
            self.turno = avv
            self.msg_key = "to_play"
            imposta_msg(self, "to_play", _mn(avv))
            self.msg_chi = avv
            self.sn_riparti()

        self.sn_finita()

    def sn_snookerato(self):
        """Se dalla bianca non si vede nessuna palla di quelle da
        giocare, ne' da una parte ne' dall'altra, si e' imbrigliati: e'
        quello che fa scattare il free ball."""
        cue = self.cue()
        if cue is None or cue.dentro:
            return False
        for b in self.palle:
            if b.dentro or b.num not in self.sn_bersagli():
                continue
            if _strada_libera(self.palle, cue.pos, b.pos, (cue, b),
                              luce=BALL_R * 1.05):
                return False
        return True

    def foto(self):
        """Una fotografia del tavolo prima del colpo: serve al miss, che
        rimette tutto com'era e fa ritirare."""
        self.scatto = [(b.num, Vector2(b.pos), b.dentro) for b in self.palle]
        self.era_snookerato = self.sn_snookerato() if self.gioco in (2, 6) else False

    def rimetti_foto(self):
        if not getattr(self, "scatto", None):
            return
        dove = dict((n, (p, d)) for n, p, d in self.scatto)
        for b in self.palle:
            if b.num in dove:
                p, d = dove[b.num]
                b.pos.update(p)
                b.dentro = d
                b.vel.update(0, 0)

    def sn_riparti(self):
        """Cosa si gioca dopo: un rosso finche' ce ne sono, se no i
        colori in ordine."""
        if self.sn_rossi_rimasti() > 0:
            self.on_rosso, self.on_quale = True, None
        else:
            self.on_rosso = False
            self.on_quale = self.sn_prossimo_colore()

    def sn_finita(self):
        """Finite le palle, vince chi ha piu' punti."""
        if self.finita:
            return
        vivi = [b for b in self.palle if not b.dentro and b.num != 0]
        if vivi:
            return
        self.finita = True
        dice("game")
        self.festa = "vittoria"
        if self.punti[0] == self.punti[1]:
            self.msg_key = "sn_pari"
            imposta_msg(self, "sn_pari")
            self.msg_chi = 0
            return
        chi = 0 if self.punti[0] > self.punti[1] else 1
        self.vincitore = chi
        self.msg_key = "wins"
        imposta_msg(self, "wins", _mn(chi))
        self.msg_chi = chi

    def rimetti_palla(self, num):
        """Rimette una palla sul tavolo, sul pallino o poco dietro se il
        posto e' occupato."""
        for b in self.palle:
            if b.num != num:
                continue
            b.dentro = False
            b.vel.update(0, 0)
            if self.gioco in (2, 6) and num in SN_COLORI:
                b.pos.update(self.posto_colore(num))
                return
            p = Vector2(sn_posti()[num] if num in SN_COLORI else PALLINO)
            for _ in range(60):
                if self.posto_libero(p):
                    break
                p.x += BALL_R * 1.2
                if p.x > PLAY.right - BALL_R * 2:
                    p.x = PALLINO.x
                    p.y += BALL_R * 1.2
            b.pos.update(p)
            return

    def scaduto(self):
        """Finito il tempo per tirare: fallo, e palla in mano all'altro,
        come al tavolo vero con l'orologio."""
        avv = 1 - self.turno
        self.ultimo_fallo = True
        self.serie = 0
        self.turno = avv
        self.ball_in_hand = self.gioco not in (3, 7)
        if self.gioco in (3, 7):
            self.punti[avv] += BI_FALLO
            rifai_castello(self.palle)
        dice("time", "foul", "ball_in_hand")
        self.msg_key = "foul"
        imposta_msg(self, "foul", (_mt("f_time"), _mn(avv)))
        self.msg_chi = avv

    def rimetti_bianca(self):
        c = self.cue()
        c.dentro = False
        c.vel.update(0, 0)
        if self.gioco in (2, 6):
            c.pos.update(PLAY.left + PLAY.w * BAULK - BALL_R * 2,
                         PLAY.centery)
        else:
            c.pos.update(LINEA_X - PLAY.w * 0.07, PLAY.centery)
        self.ball_in_hand = True

    def dentro_la_d(self, p):
        """Il semicerchio di partenza dello snooker: mezzo cerchio verso
        la sponda corta, linea compresa."""
        baulk = PLAY.left + PLAY.w * BAULK
        raggio = PLAY.h * RAGGIO_D
        if p.x > baulk:
            return False
        d = Vector2(p) - Vector2(baulk, PLAY.centery)
        return d.length() <= raggio - BALL_R * 0.2

    def spot_libero(self, p, num):
        """Un colore ci sta se non tocca nessun'altra palla, bianca
        compresa, e resta dentro il campo."""
        if not (PLAY.left + BALL_R < p.x < PLAY.right - BALL_R):
            return False
        for b in self.palle:
            if b.dentro or b.num == num:
                continue
            if (b.pos - p).length() < BALL_R * 2 + 0.5:
                return False
        return True

    def posto_colore(self, num):
        """La regola dello snooker: il colore torna sul suo spot. Se e'
        occupato va sullo spot libero di valore piu' alto; se sono tutti
        occupati va il piu' vicino possibile al suo spot, sulla linea di
        mezzo, verso la sponda in fondo; se nemmeno li' c'e' posto, il
        piu' vicino possibile dall'altra parte."""
        posti = sn_posti()
        mio = Vector2(posti[num])
        if self.spot_libero(mio, num):
            return mio
        for n in (SN_NERO, SN_ROSA, SN_BLU, SN_MARRONE, SN_VERDE,
                  SN_GIALLO):
            if self.spot_libero(Vector2(posti[n]), num):
                return Vector2(posti[n])
        passo = 0.5
        for verso in (1.0, -1.0):
            p = Vector2(mio)
            while PLAY.left + BALL_R < p.x < PLAY.right - BALL_R:
                p.x += verso * passo
                if self.spot_libero(p, num):
                    return p
        return mio

    def posto_libero(self, p):
        if not PLAY.collidepoint(p):
            return False
        if self.gioco in (2, 6) and not self.dentro_la_d(p):
            return False
        # piramide: la palla in mano si mette dietro la linea
        if self.gioco == 8 and p.x > LINEA_X - BALL_R:
            return False
        # prima di spaccare si gioca da dietro la linea di testa, come al
        # tavolo vero
        if self.spaccata and p.x > LINEA_X - BALL_R:
            return False
        if not (PLAY.left + BALL_R < p.x < PLAY.right - BALL_R):
            return False
        if not (PLAY.top + BALL_R < p.y < PLAY.bottom - BALL_R):
            return False
        for b in self.palle:
            if b.dentro or b.num == 0:
                continue
            if (b.pos - p).length() < BALL_R * 2 + 1:
                return False
        for q in BUCHE:
            if (p - q).length() < PRESA_R + BALL_R:
                return False
        return True


# ----------------------------------------------------------- il torneo

# Gli avversari del torneo, uno per livello. Sono nomi inventati: se
# arrivi in fondo ricomincia da capo, ma non li ripete finche' non li ha
# finiti tutti.
AVVERSARI = [
    "Allison Fisher", "Jeanette Lee", "Reanne Evans", "Kelly Fisher",
    "Karen Corr", "Kim Ga-young", "Jasmin Ouschan", "Chou Chieh-yu",
    "Chezka Centeno", "Han Yu", "Chen Siming", "Liu Shasha",
    "Ewa Mataya Laurance", "Ng On-yee", "Mink Nutcharut",
    "Baipat Siripaporn", "Pan Xiaoting", "Rubilen Amit",
    "Daniela Romiti", "Valentina Romeo", "Maria Cristina Pulcini",
    "Therese Klompenhouwer", "Orie Hida", "Sruong Pheavy",
    "Yuko Nishimoto", "Ayako Sakai", "Estela Cardoso", "Karina Jetten",
    "Gulsen Degener", "Charlotte Sorensen", "Vivian Villarreal",
    "Loree Jon Hasson", "Jennifer Barretta", "Helena Thornfeldt",
    "Line Kjorsvik", "Kristina Tkach", "Diana Stateczny", "Wendy Jans",
    "Maria Catalano", "Laura Evans", "Rebecca Kenna", "Emma Parker",
    "Suzie Opacic", "Ploychompoo Laokiatphong", "Seo Han-sol",
    "Lee Shin-young", "Diana Mironova", "Anna Kostanian",
    "Ekaterina Warezhkina", "Chantal Stadler",
    "Ronnie O'Sullivan", "Stephen Hendry", "Steve Davis", "John Higgins",
    "Mark Selby", "Judd Trump", "Neil Robertson", "Mark Williams",
    "Luca Brecel", "Jimmy White", "Ding Junhui", "Kyren Wilson",
    "Alex Higgins", "Ray Reardon", "Efren Reyes", "Earl Strickland",
    "Shane Van Boening", "Francisco Bustamante", "Johnny Archer",
    "Willie Mosconi", "Ralph Greenleaf", "Mike Sigel", "Steve Mizerak",
    "Niels Feijen", "Alex Pagulayan", "Darren Appleton",
    "Joshua Filler", "Ko Pin-yi", "Carlo Biado", "Dennis Orcollo",
    "Albin Ouschan", "Jayson Shaw", "Fedor Gorst", "Marco Zanetti",
    "Torbjorn Blomdahl", "Raymond Ceulemans", "Frederic Caudron",
    "Dick Jaspers", "Dani Sanchez", "Semih Sayginer", "Cho Jae-ho",
    "Andrea Quarta", "Michelangelo Aniello", "Matteo Gualemi",
    "Gustavo Zito", "Marcello Lotti", "Carlo Cifala", "Daniel Lopez",
    "Crocefisso Maggio", "Andrea Ragonesi",
]

# Di dov'e' ognuno: serve alla bandiera che gli sta accanto al nome.
# I codici sono quelli dei file dentro biliardo_gfx/bandiere.
PAESI = {
    "Allison Fisher": "gb-eng", "Jeanette Lee": "us",
    "Reanne Evans": "gb-eng", "Kelly Fisher": "gb-eng",
    "Karen Corr": "gb-nir", "Kim Ga-young": "kr",
    "Jasmin Ouschan": "at", "Chou Chieh-yu": "tw",
    "Chezka Centeno": "ph", "Han Yu": "cn", "Chen Siming": "cn",
    "Liu Shasha": "cn", "Ewa Mataya Laurance": "se", "Ng On-yee": "hk",
    "Mink Nutcharut": "th", "Baipat Siripaporn": "th",
    "Pan Xiaoting": "cn", "Rubilen Amit": "ph", "Daniela Romiti": "it",
    "Valentina Romeo": "it", "Maria Cristina Pulcini": "it",
    "Therese Klompenhouwer": "nl", "Orie Hida": "jp",
    "Sruong Pheavy": "kh", "Yuko Nishimoto": "jp", "Ayako Sakai": "jp",
    "Estela Cardoso": "es", "Karina Jetten": "nl",
    "Gulsen Degener": "tr", "Charlotte Sorensen": "dk",
    "Vivian Villarreal": "us", "Loree Jon Hasson": "us",
    "Jennifer Barretta": "us", "Helena Thornfeldt": "se",
    "Line Kjorsvik": "no", "Kristina Tkach": "ru",
    "Diana Stateczny": "de", "Wendy Jans": "be",
    "Maria Catalano": "gb-eng", "Laura Evans": "gb-wls",
    "Rebecca Kenna": "gb-eng", "Emma Parker": "gb-eng",
    "Suzie Opacic": "gb-eng", "Ploychompoo Laokiatphong": "th",
    "Seo Han-sol": "kr", "Lee Shin-young": "kr",
    "Diana Mironova": "ru", "Anna Kostanian": "ua",
    "Ekaterina Warezhkina": "ru", "Chantal Stadler": "de",
    "Ronnie O'Sullivan": "gb-eng", "Stephen Hendry": "gb-sct",
    "Steve Davis": "gb-eng", "John Higgins": "gb-sct",
    "Mark Selby": "gb-eng", "Judd Trump": "gb-eng",
    "Neil Robertson": "au", "Mark Williams": "gb-wls",
    "Luca Brecel": "be", "Jimmy White": "gb-eng", "Ding Junhui": "cn",
    "Kyren Wilson": "gb-eng", "Alex Higgins": "gb-nir",
    "Ray Reardon": "gb-wls", "Efren Reyes": "ph",
    "Earl Strickland": "us", "Shane Van Boening": "us",
    "Francisco Bustamante": "ph", "Johnny Archer": "us",
    "Willie Mosconi": "us", "Ralph Greenleaf": "us",
    "Mike Sigel": "us", "Steve Mizerak": "us", "Niels Feijen": "nl",
    "Alex Pagulayan": "ph", "Darren Appleton": "gb-eng",
    "Joshua Filler": "de", "Ko Pin-yi": "tw", "Carlo Biado": "ph",
    "Dennis Orcollo": "ph", "Albin Ouschan": "at",
    "Jayson Shaw": "gb-sct", "Fedor Gorst": "us",
    "Marco Zanetti": "it", "Torbjorn Blomdahl": "se",
    "Raymond Ceulemans": "be", "Frederic Caudron": "be",
    "Dick Jaspers": "nl", "Dani Sanchez": "es",
    "Semih Sayginer": "tr", "Cho Jae-ho": "kr", "Andrea Quarta": "it",
    "Michelangelo Aniello": "it", "Matteo Gualemi": "it",
    "Gustavo Zito": "ar", "Marcello Lotti": "it", "Carlo Cifala": "it",
    "Daniel Lopez": "ar", "Crocefisso Maggio": "it",
    "Andrea Ragonesi": "it",
}


# Il tavolo di casa: quello che si trova in multiplayer e contro il
# computer quando nelle impostazioni il panno e il legno sono su "a
# caso". Nei tornei invece si cambia a ogni livello.
TAVOLO_CASA = ("verde", "ciliegio")

# A ogni panno il suo legno. Nel torneo il panno lo tira fuori il giro,
# e il legno viene da qui: un abbinamento fisso, non una combinazione a
# caso che stona.
ABBINAMENTI = {
    "verde": "ciliegio",
    "verde-erba": "ciliegio",
    "verde-2": "noce-italiano",
    "verde-3": "mogano",
    "verde-impero": "wenge",
    "verde-muschio": "rovere",
    "verde-oliva": "ulivo",
    "blu": "ebano",
    "azzurro": "frassino",
    "celeste": "bamboo",
    "carta-da-zucchero": "quercia",
    "viola": "wenge",
    "lilla": "faggio",
    "rosso-ferrari": "ebano",
    "rosso-antico": "mogano",
    "vinaccia": "palissandro",
    "ruggine": "castagno",
    "arancione": "noce-americano",
    "senape": "olmo",
    "camel": "noce-americano",
    "sabbia": "bamboo",
    "marrone": "castagno",
    "grigio-chiaro": "zebrano",
    "nero": "ebano",
}


# Il torneo comincia dal tavolo classico e poi cambia a ogni livello,
# senza mai ripetere un panno o un legno finche' non li ha girati tutti.
TORNEO_CLASSICO = TAVOLO_CASA


def _giro(quanti, primo=None):
    """Un giro completo mescolato: tutti gli indici, uno per volta, e
    quello scelto per primo davanti a tutti."""
    q = list(range(quanti))
    random.shuffle(q)
    if primo is not None and 0 <= primo < quanti:
        q.remove(primo)
        q.insert(0, primo)
    return q


def _quale(elenco, pezzo):
    """L'indice della prima texture che ha quella parola nel nome."""
    for i, (nome_t, percorso) in enumerate(elenco):
        if pezzo in os.path.basename(percorso).lower():
            return i
    return 0


def tavoli_torneo():
    """Le combinazioni panno e legno del torneo, in due giri separati:
    il primo livello e' il classico, verde e mogano."""
    p = _giro(len(PANNI), _quale(PANNI, TORNEO_CLASSICO[0])) if PANNI else [0]
    b = _giro(len(BORDI), _quale(BORDI, TORNEO_CLASSICO[1])) if BORDI else [0]
    return p, b


def legno_di(i_panno):
    """Il legno che va con quel panno. Se il panno non e' in elenco si
    tiene quello che c'e', senza inventare accostamenti."""
    if not PANNI or not BORDI or not (0 <= i_panno < len(PANNI)):
        return None
    f = os.path.basename(PANNI[i_panno][1]).lower()
    # il nome piu' lungo che combacia vince: "verde-erba" prima di "verde"
    for chiave in sorted(ABBINAMENTI, key=len, reverse=True):
        if chiave in f:
            k = _quale(BORDI, ABBINAMENTI[chiave])
            return k
    return None


# I tavoli del torneo, scelti uno per uno: per ogni disciplina i sei
# turni, dal primo alla finale. Il primo dell'8-Ball e' il tavolo di
# casa, verde erba e ciliegio; poi si cambia aria a ogni turno e i
# materiali si fanno piu' importanti man mano che si va avanti.
# I sei tavoli del torneo, uno per turno, dal primo alla finale. Sono
# gli stessi per tutte le discipline: non servono ventiquattro tavoli,
# ne bastano sei fatti bene. Si sale di materiale man mano che si va
# avanti, e la finale e' coccodrillo nero e panno antracite.
TORNEO_SEI = (
    ("verde.png", "ciliegio.png"),
    ("blu.png", "marmo.png"),
    ("bordeaux.png", "Maglia.jpg"),
    ("crema.png", "foglia-oro.png"),
    ("viola.png", "fibra-di-carbonio-1.png"),
    ("antracite.png", "cocco.png"),
)
TORNEO_TAVOLI = {disc: list(TORNEO_SEI) for disc in range(9)}
# blackball: stesso panno, qualche cornice diversa
TORNEO_TAVOLI[4][1] = ("blu.png", "nero-1.png")
# Le palle di ogni tavolo del torneo: il nome del set, uguale per tutti i
# giochi, o un dizionario gioco -> set. Quelli che mancano: le sue.
TORNEO_PALLE = {
    1: {"pool": "set_classico", "snooker": "set_classico",
        "birilli": "set_classico", "piramide": "set_classico",
        "blackball": "set_pro"},
    2: {"pool": "set_marmo_chiaro", "blackball": "set_club2"},
    3: {"pool": "set_zigzag"},
    4: {"pool": "set_retro"},
    5: {"pool": "set_scacchi"},
    6: {"pool": "set_bersaglio"},
}
PALLE_TORNEO = [None]   # il set del tavolo del torneo di adesso
TURNO_ORA = [None]      # il turno del torneo che si sta giocando


def indice_di(elenco, nome_file):
    """Dove sta quella texture nell'elenco, cercandola per nome di file."""
    for i, (_, percorso) in enumerate(elenco):
        if os.path.basename(percorso) == nome_file:
            return i
    return None


def tavolo_fisso(disc, turno):
    """Il tavolo di quel turno secondo la tabella qui sopra. Ritorna gli
    indici, o None se la casella non c'e' o se una texture e' sparita
    dalla cartella."""
    coppie = TORNEO_TAVOLI.get(disc)
    if not coppie or not 1 <= turno <= len(coppie):
        return None
    nome_panno, nome_legno = coppie[turno - 1]
    i_panno = indice_di(PANNI, nome_panno)
    i_bordo = indice_di(BORDI, nome_legno)
    if i_panno is None or i_bordo is None:
        return None
    return i_panno, i_bordo


TURNI_TORNEO = 6        # sei partite per vincere un torneo da 64


def chiave_tavolo(disc, turno):
    return "%d:%d" % (disc, turno)


def tavolo_scritto(disc, turno):
    """Il tavolo assegnato a mano a quel turno di quella disciplina, se
    c'e'. Si tiene per nome di file e non per numero, cosi' resta giusto
    anche aggiungendo altre texture."""
    voce = CFG.get("tavoli", {}).get(chiave_tavolo(disc, turno))
    if not voce or len(voce) != 2:
        return None
    fuori = []
    for elenco, nome_file in ((PANNI, voce[0]), (BORDI, voce[1])):
        k = indice_di(elenco, nome_file)
        if k is None:
            return None
        fuori.append(k)
    return tuple(fuori)


def gia_preso(nome_panno, nome_legno, non_questa=None):
    """Se questa combinazione di panno e legno sta gia' su un'altra
    casella del torneo, dice quale. Serve a non ripetere due tavoli
    uguali in due turni diversi."""
    for chiave, voce in CFG.get("tavoli", {}).items():
        if chiave == non_questa or not voce or len(voce) != 2:
            continue
        if voce[0] == nome_panno and voce[1] == nome_legno:
            return chiave
    return None


def tavolo_del_turno(disc, turno, giri):
    """Il tavolo di quel turno: quello della tabella, e se per qualche
    motivo non c'e' uno pescato dal giro."""
    fisso = tavolo_fisso(disc, turno)
    if fisso is not None:
        return fisso
    return tavolo_del_livello(giri, disc * TURNI_TORNEO + turno - 1)


def tavolo_del_livello(giri, livello):
    """Il ripiego, quando una texture della tabella non si trova: il
    panno viene dal giro, che li passa tutti senza ripetere, e il legno
    e' quello abbinato a quel panno."""
    p, b = giri
    if livello > 0 and livello % max(1, len(p)) == 0:
        p[:] = _giro(len(p))
    i_panno = p[livello % len(p)]
    i_bordo = legno_di(i_panno)
    if i_bordo is None:
        if livello > 0 and livello % max(1, len(b)) == 0:
            b[:] = _giro(len(b))
        i_bordo = b[livello % len(b)]
    return i_panno, i_bordo


def bravura_del_turno(tab):
    """Piu' si va avanti nel tabellone, piu' forti sono: ai primi turni
    capitano quelli che sbagliano, in fondo i campioni."""
    return max(0, min(len(LIVELLI) - 1, tab["vinte"]))


def bravura_del_livello(livello):
    """Quanto e' forte l'avversario al livello dato: si sale a scaglioni
    e dal sedicesimo in poi sono tutti campioni."""
    return max(0, min(len(LIVELLI) - 1, (livello - 1) // 3))


def avversario_del_livello(livello, giro):
    return AVVERSARI[giro[(livello - 1) % len(giro)]]


# ----------------------------------------------------------- il tabellone

# Il torneo e' a eliminazione diretta, come un mondiale: si parte in
# sessantaquattro, meta' tabellone per parte, e chi perde va a casa.
# Sessantaquattro e non cento perche' il tabellone deve dimezzarsi fino
# in fondo: con cento al secondo turno ne resterebbero cinquanta, poi
# venticinque, e venticinque non si accoppiano.
TAB_QUANTI = 64
TURNI = ("r_64", "r_32", "r_16", "r_8", "r_4", "r_2")


def tabellone_nuovo():
    """Il sorteggio: sessantatre presi fra i cento e tu in mezzo a loro,
    in un posto a caso."""
    gente = random.sample(AVVERSARI, min(TAB_QUANTI - 1, len(AVVERSARI)))
    while len(gente) < TAB_QUANTI - 1:
        gente.append(random.choice(AVVERSARI))
    mio = random.randrange(TAB_QUANTI)
    gente.insert(mio, None)             # None sei tu
    # il trofeo di questo torneo: uno a caso fra quelli che ci sono, e
    # resta lo stesso per tutti e sei i turni
    return {"turni": [gente], "mio": mio, "fuori": False, "vinte": 0,
            "trofeo": random.randrange(len(TROFEI)) if TROFEI else 0}


def tab_oggi(tab):
    return tab["turni"][-1]


def tab_avversario(tab):
    """Chi ti tocca adesso: il vicino di coppia."""
    return tab_oggi(tab)[tab["mio"] ^ 1]


def tab_turno(tab):
    """Come si chiama il turno che si sta giocando."""
    quanti = len(tab_oggi(tab))
    k = {64: 0, 32: 1, 16: 2, 8: 3, 4: 4, 2: 5}.get(quanti)
    return T(TURNI[k]) if k is not None else ""


def tab_avanza(tab, ho_vinto):
    """Finito il turno: la tua partita l'hai giocata, le altre le decide
    il sorteggio, e si forma il turno dopo."""
    gente = tab_oggi(tab)
    mia = tab["mio"] // 2
    nuovi = []
    for k in range(0, len(gente), 2):
        a, b = gente[k], gente[k + 1]
        if k // 2 == mia:
            nuovi.append(None if ho_vinto else (b if a is None else a))
        else:
            nuovi.append(random.choice((a, b)))
    tab["turni"].append(nuovi)
    tab["mio"] = mia
    if ho_vinto:
        tab["vinte"] += 1
    else:
        tab["fuori"] = True


def _cognome(nome_intero):
    """L'ultima parola del nome: nelle colonne strette non ci sta altro."""
    pezzi = nome_intero.split()
    return pezzi[-1] if pezzi else nome_intero


def _tagliato(testo, font, largo):
    """Il nome accorciato quanto basta a starci dentro. Prima si prova
    intero, poi il solo cognome, poi si taglia con un punto in fondo:
    meglio "Laokiatph." che una scritta che esce dalla casella."""
    if font.size(testo)[0] <= largo:
        return testo
    corto = _cognome(testo)
    if font.size(corto)[0] <= largo:
        return corto
    while corto and font.size(corto + ".")[0] > largo:
        corto = corto[:-1]
    return (corto + ".") if corto else ""


# I trofei: le PNG stanno in biliardo_gfx/trofei, una per file. Sul
# tabellone se ne vede uno solo, quello scelto; col tasto T si girano
# tutti e si legge come si chiama il file, cosi' si scarta quello che
# non piace. La scelta si tiene nelle impostazioni.
TROFEI = []
TROFEI_TAGLIA = {}


def prepara_trofei():
    del TROFEI[:]
    cartella = os.path.join(GFX, "trofei")
    if not os.path.isdir(cartella):
        return
    for f in sorted(os.listdir(cartella)):
        if f.lower().endswith((".png", ".webp", ".jpg", ".jpeg", ".bmp")):
            TROFEI.append((os.path.splitext(f)[0],
                           os.path.join(cartella, f)))


TROFEO_LARGO = 210      # il posto che c'e' in mezzo al tabellone


def trofeo_img(i, alto, largo_max=TROFEO_LARGO):
    """Il trofeo numero i, portato a misura senza deformarlo: sta dentro
    al riquadro che gli si da', alto quanto si chiede a meno che non sia
    cosi' largo da sbordare sulle caselle."""
    if not TROFEI or not 0 <= i < len(TROFEI):
        return None
    chiave = (i, alto, largo_max)
    if chiave not in TROFEI_TAGLIA:
        try:
            img = pygame.image.load(TROFEI[i][1]).convert_alpha()
        except (pygame.error, IOError):
            TROFEI_TAGLIA[chiave] = None
            return None
        w, h = img.get_size()
        if w <= 0 or h <= 0:
            TROFEI_TAGLIA[chiave] = None
            return None
        k = min(alto / float(h), largo_max / float(w))
        TROFEI_TAGLIA[chiave] = pygame.transform.smoothscale(
            img, (max(1, int(round(w * k))), max(1, int(round(h * k)))))
    return TROFEI_TAGLIA[chiave]


def disegna_trofeo(sc, cx, giu, alto, quale=0):
    """Il trofeo di questo torneo, appoggiato col piede a "giu" e
    centrato su cx: cosi' sta sempre sopra le caselle della finale,
    qualunque sia la forma della PNG."""
    if not TROFEI:
        return None
    img = trofeo_img(quale % len(TROFEI), alto)
    if img is None:
        return None
    r = img.get_rect(midbottom=(cx, giu))
    sc.blit(img, r)
    return r


CASELLA_VERDE = (12, 44, 38)    # le caselle coi nomi, sul tabellone
CASELLA_MIA = (26, 84, 70)      # la tua, quando respira
CASELLA_FILO = (120, 98, 54)    # il filo d'oro attorno


def disegna_tabellone(sc, tab, battito):
    """Il tabellone come quello dei mondiali: meta' a sinistra, meta' a
    destra, e via via che si vince le colonne si stringono verso il
    centro. Le caselle dei turni che devono ancora venire si vedono
    vuote, le graffe le collegano come sul tabellone vero, e la riga di
    chi gioca respira."""
    mini = FONTS["mini"]
    y0, alto = s(96), s(588)
    largo_col = s(84)                   # la casella
    passo_col = s(102)                  # da una colonna all'altra: fra le
    quanti_turni = len(tab["turni"])     # due resta l'aria per le graffe
    tutti = len(tab["turni"][0])

    # Tinte da circolo: legno scuro e ottone, che sul verde del fondo
    # stanno insieme. Il grigio-blu di prima ci litigava.
    VUOTA = (8, 30, 26)                 # la casella ancora da riempire
    VUOTA_BORDO = (70, 62, 40)
    PIENA = (70, 55, 36)                # quella con dentro un nome
    GRAFFA = (112, 88, 50)              # le linee che collegano
    SCRITTA = NOME_ACCESO               # nero, come i nomi sulla striscia
    TITOLO = (170, 140, 90)
    ORO = (234, 182, 84)

    ultima = 0                          # l'ultima colonna che ci sta
    while (tutti >> (ultima + 1)) >= 1 and ultima < 8:
        ultima += 1
    ultima -= 1

    def colonna(t, lato):
        return (s(14) + t * passo_col if lato == 0 else
                WIN_W - s(14) - t * passo_col - largo_col)

    def casella(t, lato, i):
        righe = max(1, tutti >> (t + 1))
        passo = alto / float(righe)
        y = y0 + (i + 0.5) * passo
        return pygame.Rect(colonna(t, lato),
                           int(y - min(s(11), passo / 2 - 1)),
                           largo_col, int(min(s(22), passo - s(2))))

    vinci = pygame.Rect(0, 0, s(208), s(30))
    vinci.center = (WIN_W // 2, y0 + alto // 2 + s(52))

    # --- le graffe, sotto a tutto: due caselle si chiudono e vanno al
    # turno dopo, come sul tabellone appeso al muro
    for lato in (0, 1):
        for t in range(ultima):
            righe = max(1, tutti >> (t + 1))
            if righe < 2:
                continue
            if lato == 0:
                x_out = colonna(t, 0) + largo_col
                x_next = colonna(t + 1, 0)
            else:
                x_out = colonna(t, 1)
                x_next = colonna(t + 1, 1) + largo_col
            x_mid = (x_out + x_next) // 2
            for i in range(righe // 2):
                a = casella(t, lato, 2 * i).centery
                b = casella(t, lato, 2 * i + 1).centery
                c = casella(t + 1, lato, i).centery
                pygame.draw.line(sc, GRAFFA, (x_out, a), (x_mid, a))
                pygame.draw.line(sc, GRAFFA, (x_out, b), (x_mid, b))
                pygame.draw.line(sc, GRAFFA, (x_mid, a), (x_mid, b))
                pygame.draw.line(sc, GRAFFA, (x_mid, c), (x_next, c))
        # dalla finale alla casella del vincitore
        f = casella(ultima, lato, 0)
        if lato == 0:
            x_out, x_next = f.right, vinci.left
        else:
            x_out, x_next = f.left, vinci.right
        x_mid = (x_out + x_next) // 2
        pygame.draw.line(sc, GRAFFA, (x_out, f.centery), (x_mid, f.centery))
        pygame.draw.line(sc, GRAFFA, (x_mid, f.centery), (x_mid, vinci.centery))
        pygame.draw.line(sc, GRAFFA, (x_mid, vinci.centery),
                         (x_next, vinci.centery))

    # --- il nome del turno sopra ogni colonna
    for t in range(ultima + 1):
        voce = T("r_%d" % max(2, tutti >> t))
        scritta = mini.render(voce.upper(), True, TITOLO)
        for lato in (0, 1):
            sc.blit(scritta, scritta.get_rect(
                center=(colonna(t, lato) + largo_col // 2, y0 - s(14))))

    # --- il trofeo, appoggiato sopra le caselle della finale
    disegna_trofeo(sc, vinci.centerx, casella(ultima, 0, 0).top - s(18),
                   s(150), tab.get("trofeo", 0))

    # --- la casella del vincitore, vuota finche' non c'e'
    if quanti_turni <= ultima + 1:
        pygame.draw.rect(sc, VUOTA, vinci)
        pygame.draw.rect(sc, VUOTA_BORDO, vinci, max(1, s(1)))

    # --- le caselle dei turni che devono ancora venire
    for t in range(quanti_turni, ultima + 1):
        righe = max(1, tutti >> (t + 1))
        for lato in (0, 1):
            for i in range(righe):
                riga = casella(t, lato, i)
                pygame.draw.rect(sc, VUOTA, riga)
                pygame.draw.rect(sc, VUOTA_BORDO, riga, max(1, s(1)))

    # --- i turni gia' sorteggiati
    for t in range(quanti_turni):
        gente = tab["turni"][t]
        if len(gente) == 1:
            chi = gente[0]
            io_sono = (chi is None)
            pygame.draw.rect(sc, CASELLA_VERDE, vinci)
            pygame.draw.rect(sc, ORO_LUCE, vinci, max(1, s(2)))
            ban = bandiera(BANDIERA[0] if io_sono
                           else PAESI.get(chi, ""), s(12))
            testo = NOMI[0] if io_sono else chi
            nome_r = FONTS["font"].render(testo, True, AVORIO)
            largo_tot = nome_r.get_width() + (
                ban.get_width() + s(6) if ban else 0)
            x = vinci.centerx - largo_tot // 2
            if ban:
                sc.blit(ban, ban.get_rect(midleft=(x, vinci.centery)))
                x += ban.get_width() + s(6)
            sc.blit(nome_r, nome_r.get_rect(midleft=(x, vinci.centery)))
            continue
        meta = max(1, len(gente) // 2)
        passo = alto / float(meta)
        for lato in (0, 1):
            for i in range(meta):
                k = i if lato == 0 else meta + i
                if k >= len(gente):
                    continue
                chi = gente[k]
                io_sono = (chi is None)
                testo = NOMI[0] if io_sono else (
                    _cognome(chi) if passo < s(26) else chi)
                col = AVORIO
                riga = casella(t, lato, i)
                # la casella col nome: verde scuro col filo d'oro, il nome
                # bianco sopra
                if io_sono:
                    # la tua respira, cosi' ti trovi a colpo d'occhio
                    k = 0.6 + 0.4 * battito
                    fondo = tuple(int(a + (b - a) * k) for a, b in
                                  zip(CASELLA_VERDE, CASELLA_MIA))
                    pygame.draw.rect(sc, fondo, riga)
                    pygame.draw.rect(sc, ORO_LUCE, riga, max(1, s(2)))
                else:
                    pygame.draw.rect(sc, CASELLA_VERDE, riga)
                    pygame.draw.rect(sc, CASELLA_FILO, riga, max(1, s(1)))
                ban = bandiera(BANDIERA[0] if io_sono
                               else PAESI.get(chi, ""), s(9))
                # a destra si legge da destra: la bandiera sul bordo
                # esterno e il nome che va verso il centro
                if lato == 0:
                    tx = riga.x + s(4)
                    if ban is not None and riga.h >= s(11):
                        sc.blit(ban, ban.get_rect(midleft=(tx, riga.centery)))
                        tx += ban.get_width() + s(4)
                    nome_r = mini.render(
                        _tagliato(testo, mini, riga.right - tx - s(3)),
                        True, col)
                    sc.blit(nome_r, nome_r.get_rect(midleft=(tx,
                                                             riga.centery)))
                else:
                    tx = riga.right - s(4)
                    if ban is not None and riga.h >= s(11):
                        sc.blit(ban, ban.get_rect(midright=(tx,
                                                            riga.centery)))
                        tx -= ban.get_width() + s(4)
                    nome_r = mini.render(
                        _tagliato(testo, mini, tx - riga.x - s(3)),
                        True, col)
                    sc.blit(nome_r, nome_r.get_rect(midright=(tx,
                                                              riga.centery)))

def schermata_tabellone(sc, clock, logo, tab, titolo, sotto, voci, chiavi,
                        scelte=False):
    """La schermata del tabellone, con le scelte in fondo. Con scelte=True
    davanti ai bottoni ci sono la stecca e il gessetto per l'incontro:
    si cambiano con su e giu', con invio o cliccando a destra o a
    sinistra del bottone."""
    base_v, base_k = list(voci), list(chiavi)
    n_sc = 2 if scelte else 0
    sel = n_sc
    rett = []

    def cambia(i, passo):
        if i == 0:
            gira_stecca_cfg(passo)
        else:
            gira_gesso(passo)
        salva_config()
        suona_fx("menu_tic", 0.6)

    while True:
        clock.tick(60)
        mouse = mouse_gioco()
        if scelte:
            voci = ["%s: %s" % (T("cue"), nome_stecca_cfg()),
                    "%s: %s" % (T("chalk_row"), nome_gesso_scelto())] + base_v
            chiavi = ["_st", "_ge"] + base_k
        for ev in eventi():
            if ev.type == pygame.QUIT:
                return "quit"
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    return chiavi[-1]
                if ev.key in (pygame.K_RIGHT, pygame.K_TAB):
                    sel = (sel + 1) % len(voci)
                if ev.key == pygame.K_LEFT:
                    sel = (sel - 1) % len(voci)
                if sel < n_sc and ev.key in (pygame.K_UP, pygame.K_DOWN):
                    cambia(sel, 1 if ev.key == pygame.K_DOWN else -1)
                elif ev.key in (pygame.K_RETURN, pygame.K_KP_ENTER,
                                pygame.K_SPACE):
                    if sel < n_sc:
                        cambia(sel, 1)
                    else:
                        return chiavi[sel]
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                for i, r in enumerate(rett):
                    if r.collidepoint(mouse):
                        if i < n_sc:
                            sel = i
                            cambia(i, -1 if mouse[0] < r.centerx else 1)
                        else:
                            return chiavi[i]

        font, grande, small = FONTS["font"], FONTS["grande"], FONTS["small"]
        sfondo_menu(sc, None)
        battito = 0.5 + 0.5 * math.sin(pygame.time.get_ticks() / 260.0)
        disegna_tabellone(sc, tab, battito)

        # lo stemma del torneo in alto al centro, al posto della scritta
        # del turno; la scritta scende nella riga sotto il tabellone
        st = stemma_ora(s(88))
        riga = sotto
        if st is not None:
            # a meta', sulla riga dei nomi dei turni (ottavi, quarti...)
            sc.blit(st, st.get_rect(center=(WIN_W // 2, s(96) - s(14))))
            riga = ("%s  -  %s" % (titolo, sotto)) if sotto else titolo
        else:
            t = FONTS["classico"].render(titolo, True, (236, 216, 164))
            sc.blit(t, t.get_rect(center=(WIN_W // 2, s(40))))

        if riga:
            t = font.render(riga, True, (232, 146, 52))
            sc.blit(t, t.get_rect(center=(WIN_W // 2, s(704))))

        rett = []
        stac = s(20)
        larghi = [s(300) if i < n_sc else (s(170) if n_sc else s(200))
                  for i in range(len(voci))]
        x0 = WIN_W // 2 - (sum(larghi) + stac * (len(voci) - 1)) // 2
        tic_menu(("tabellone",) + tuple(voci[n_sc:]), max(0, sel - n_sc))
        x = x0
        for i, v in enumerate(voci):
            largo = larghi[i]
            r = pygame.Rect(x, s(724), largo, s(40))
            x += largo + stac
            if MOUSE_VIVO[0] and r.collidepoint(mouse):
                sel = i
            acceso = (i == sel)
            q = pygame.Surface(r.size, pygame.SRCALPHA)
            q.fill((255, 255, 255, 26) if acceso else (255, 255, 255, 10))
            sc.blit(q, r)
            if acceso:
                pygame.draw.rect(sc, COL_GIOC[0], (r.x, r.y, 3, r.h))
            col = (255, 255, 255) if acceso else (190, 196, 208)
            if i < n_sc:
                # le scelte: il valore in oro, con le frecce ai lati
                tv = small.render(v, True, ORO_SCELTA if acceso
                                  else ORO_SOTTO)
                sc.blit(tv, tv.get_rect(center=r.center))
                if acceso:
                    for lato, segno in ((r.left + s(12), "<"),
                                        (r.right - s(12), ">")):
                        f = small.render(segno, True, ORO_SCELTA)
                        sc.blit(f, f.get_rect(center=(lato, r.centery)))
            else:
                tv = FONTS.get("elegante_voce", font).render(tit_el(v), True,
                                                             col)
                sc.blit(tv, tv.get_rect(center=r.center))
            rett.append(r)
        presenta()


# ------------------------------------------------------------ il computer

# Quanto sbaglia il computer, un livello per riga: il nome della voce,
# l'errore di mira in gradi, quello di potenza, e ogni quanto rinuncia
# al tiro migliore per prendersi il secondo. Il campione perdona poco.
# I tempi del computer, in secondi: quanto ci mette a girare la stecca
# dalla parte dov'era fino alla palla che ha scelto, quanto tiene poi la
# mira facendo le stoccate a vuoto, e quanto ci mette a sistemare la
# bianca quando ha palla in mano. Serve a seguire quello che fa: se
# tira appena il tavolo si ferma non si capisce niente.
CPU_CERCA = 2.2
CPU_MIRA = 2.8
CPU_PIAZZA = 1.5

# Sei livelli, uno per turno del torneo. Per ognuno: il nome, l'errore di
# mira in gradi, quello di potenza, ogni quanto si accontenta del secondo
# tiro invece del migliore, e quanti tiri prova di nascosto prima di
# scegliere. Il principiante ne prova pochi e sbaglia la mira; il
# campione li prova tutti, combinazioni comprese, e non sbaglia quasi mai.
LIVELLI = [("l_facile", 3.2, 0.18, 0.40, 3),
           ("l_medio", 2.0, 0.12, 0.25, 5),
           ("l_club", 1.2, 0.08, 0.15, 7),
           ("l_forte", 0.7, 0.05, 0.08, 10),
           ("l_maestro", 0.35, 0.03, 0.03, 14),
           ("l_campione", 0.12, 0.015, 0.00, 20)]


def livello_cpu(livello):
    return LIVELLI[max(0, min(len(LIVELLI) - 1, livello))]


def _strada_libera(palle, a, b, saltare, luce=None):
    """Se fra due punti non c'e' nessuna palla di mezzo. La luce e' poco
    meno di due raggi: quanto basta perche' la palla ci passi."""
    if luce is None:
        luce = BALL_R * 1.9
    d = b - a
    lung = d.length()
    if lung < 1e-6:
        return True
    u = d / lung
    for p in palle:
        if p.dentro or p in saltare:
            continue
        v = p.pos - a
        t = v.dot(u)
        if t <= 0.0 or t >= lung:
            continue
        if abs(v.x * u.y - v.y * u.x) < luce:
            return False
    return True


def palle_da_fare(partita):
    """Quali palle puo' giocare chi ha il turno: alla palla 9 solo la
    piu' bassa; alla palla 8 le sue, o tutte quante a tavolo aperto, o
    soltanto l'otto quando ha finito il gruppo."""
    if partita.gioco == 8:
        cue = partita.cue()
        return [q for q in partita.palle if not q.dentro and q is not cue]
    if partita.gioco in (1, 5):
        b = partita.bassa()
        return [q for q in partita.palle if not q.dentro and q.num == b]
    if partita.gioco in (2, 6):
        quali = partita.sn_bersagli()
        return [q for q in partita.palle if not q.dentro and q.num in quali]
    if partita.puo_tirare_8(partita.turno):
        return [b for b in partita.palle if not b.dentro and b.num == 8]
    g = partita.gruppo[partita.turno]
    if g is None:
        return [b for b in partita.palle
                if not b.dentro and b.num not in (0, 8)]
    return partita.restanti(g)


def tiri_visti(partita, da=None):
    """Tutti i tiri diretti che si vedono: per ogni palla giocabile e per
    ogni buca, dove va colpita perche' ci finisca dentro. Il voto pesa
    quanto e' di taglio e quanto e' lontana, che un taglio sottile da
    mezzo tavolo non entra quasi mai."""
    cue = partita.cue()
    c = Vector2(da) if da is not None else Vector2(cue.pos)
    fuori = []
    for b in palle_da_fare(partita):
        for buca in BUCHE:
            verso = buca - b.pos
            if verso.length() < 1e-6:
                continue
            verso = verso.normalize()
            # il punto fantasma: dove deve arrivare la bianca perche' la
            # palla parta verso la buca
            ghost = b.pos - verso * (BALL_R * 2.0)
            d = ghost - c
            if d.length() < BALL_R:
                continue
            d = d.normalize()
            taglio = d.dot(verso)
            if taglio < 0.18:              # oltre gli ottanta gradi, lascia
                continue
            if not _strada_libera(partita.palle, c, ghost, (cue, b)):
                continue
            if not _strada_libera(partita.palle, b.pos, buca, (cue, b)):
                continue
            lungo = (ghost - c).length() + (buca - b.pos).length()
            voto = taglio ** 2 * (1.0 - min(0.85, lungo / (PLAY.w * 2.4)))
            fuori.append((voto, d, lungo, taglio))
    fuori.sort(key=lambda t: -t[0])
    return fuori


def _sicurezza(partita):
    """Quando non c'e' niente da imbucare: tocca piano la sua palla piu'
    vicina fra quelle che vede, cosi' almeno non regala il fallo."""
    cue = partita.cue()
    mire = palle_da_fare(partita)
    if not mire:
        return Vector2(1, 0), 0.30
    mire.sort(key=lambda b: (b.pos - cue.pos).length())
    for b in mire:
        if _strada_libera(partita.palle, cue.pos, b.pos, (cue, b)):
            d = b.pos - cue.pos
            if d.length_squared() > 1e-6:
                return d.normalize(), 0.34
    d = mire[0].pos - cue.pos
    if d.length_squared() < 1e-6:
        return Vector2(1, 0), 0.34
    return d.normalize(), 0.34


def colpo_cpu_birilli(partita, livello):
    """Ai birilli non c'e' buca da cercare: si manda la bilia
    dell'avversario addosso al castello, che e' il tiro di tutti."""
    _, err_mira, err_forza, _, _ = livello_cpu(livello)
    mia = partita.cue()
    avv = None
    for b in partita.palle:
        if b.num == partita.bi_avv():
            avv = b
    if mia is None or avv is None:
        return Vector2(1, 0), 0.4
    castello = Vector2(PLAY.centerx, PLAY.centery)
    verso = castello - avv.pos
    if verso.length_squared() < 1e-6:
        verso = Vector2(1, 0)
    fantasma = avv.pos - verso.normalize() * (BALL_R * 2.0)
    d = fantasma - mia.pos
    if d.length_squared() < 1e-6:
        d = avv.pos - mia.pos
    d = d.normalize()
    lungo = (avv.pos - mia.pos).length()
    forza = 0.30 + 0.40 * min(1.0, lungo / (PLAY.w * 1.1))
    sbaglio = max(-3.0 * err_mira, min(3.0 * err_mira,
                                       random.gauss(0.0, err_mira)))
    d = d.rotate(sbaglio)
    forza *= 1.0 + random.gauss(0.0, err_forza)
    return d, max(0.16, min(1.0, forza))


def colpo_cpu(partita, livello):
    """Il colpo del computer, tutto in una volta: serve alle prove. Al
    tavolo invece pensa un pezzo per fotogramma, con pensa_cpu."""
    g = pensa_cpu(partita, livello)
    while True:
        try:
            next(g)
        except StopIteration as fine:
            return fine.value


def colpo_cpu_semplice(partita, livello):
    """Il colpo a occhio, senza provarlo: per la spaccata, dove conta
    solo tirare forte nel mucchio."""
    if partita.gioco in (3, 7):
        return colpo_cpu_birilli(partita, livello)
    _, err_mira, err_forza, rinuncia, _ = livello_cpu(livello)
    tiri = tiri_visti(partita)
    scelto = None
    if tiri:
        if len(tiri) > 1 and random.random() < rinuncia:
            scelto = tiri[1]
        else:
            scelto = tiri[0]

    if scelto is None:
        d, forza = _sicurezza(partita)
    else:
        _, d, lungo, taglio = scelto
        # piu' lontana e piu' di taglio, piu' bisogna spingere. La base
        # e' bassa apposta: su una palla a due centimetri dalla buca si
        # accompagna, non si spacca.
        # col panno che scorre, la stessa forza porta la palla molto piu'
        # lontano: provato a tavolino, cosi' imbuca di piu'
        forza = 0.13 + 0.24 * min(1.0, lungo / (PLAY.w * 1.1))
        forza += 0.10 * (1.0 - taglio)
        if partita.gioco in (2, 6):
            forza *= 0.80           # allo snooker si gioca di tocco

    if partita.spaccata:
        forza = 1.0                        # la spaccata si tira e basta

    sbaglio = max(-3.0 * err_mira, min(3.0 * err_mira,
                                       random.gauss(0.0, err_mira)))
    d = d.rotate(sbaglio)
    forza *= 1.0 + random.gauss(0.0, err_forza)
    return d, max(0.14, min(1.0, forza))


# ------------------------------------------------ il computer che prova
#
# Prima di tirare il computer prova di nascosto i tiri che ha in mente,
# con la stessa fisica e le stesse regole della partita vera: su una
# copia del tavolo tira, aspetta che tutto si fermi e fa decidere
# all'arbitro. Cosi' sa se il tiro imbuca, se e' fallo, se chiude la
# partita, e dove resta la bianca. Poi sceglie il migliore e solo allora
# ci mette sopra l'errore del suo livello.
SIMULO = [False]        # vero mentre il computer prova: niente voce
PROVA_DT = 1.0 / 60.0
PROVA_MAX = 10.0        # secondi di gioco al massimo per una prova


def _clona_palle(palle):
    fuori = []
    for b in palle:
        c = copy.copy(b)
        for k, v in list(vars(c).items()):
            if isinstance(v, Vector2):
                setattr(c, k, Vector2(v))
        fuori.append(c)
    return fuori


def prova_colpo(partita, d, forza):
    """Un tiro provato su una copia: torna la partita come sarebbe dopo,
    gia' giudicata dall'arbitro. Il tavolo vero non si tocca."""
    castello = list(BIRILLI)
    in_piedi = [b.in_piedi for b in castello]
    palle = _clona_palle(partita.palle)
    p2 = copy.deepcopy(partita, {id(partita.palle): palle})
    p2.foto()
    for q in palle:
        q.di_sponda = False
    cue = p2.cue()
    cue.vel = Vector2(d) * (TIRO_MAX * spinta(forza))
    stato = {"imbucate": [], "prima": None, "sponda": False,
             "bilia": cue.num, "spin_x": 0.0, "spin_y": 0.0}
    SIMULO[0] = True
    try:
        t = 0.0
        while t < PROVA_MAX:
            vmax = max((b.vel.length() for b in palle if not b.dentro),
                       default=0.0)
            n = max(1, min(40, int(vmax * PROVA_DT / (BALL_R * 0.45)) + 1))
            for _ in range(n):
                passo_fisica(palle, PROVA_DT / n, stato)
            t += PROVA_DT
            if tutto_fermo(palle):
                break
        p2.valuta(stato)
    finally:
        SIMULO[0] = False
        BIRILLI[:] = castello
        for b, v in zip(castello, in_piedi):
            b.in_piedi = v
    return p2, stato


def voto_colpo(partita, p2):
    """Quanto vale quello che e' successo, per chi ha tirato. Vincere
    vale tutto, perdere toglie tutto; poi il fallo, i punti, tenere il
    turno e da dove si riparte. Se il turno passa, conta quanto e'
    difficile il tavolo che lascia all'altro."""
    io = partita.turno
    if p2.finita:
        if p2.vincitore == io:
            return 10000.0
        if p2.vincitore is None:
            return 0.0
        return -10000.0
    v = 0.0
    if p2.ultimo_fallo:
        v -= 600.0
    v += 40.0 * ((p2.punti[io] - partita.punti[io]) -
                 (p2.punti[1 - io] - partita.punti[1 - io]))
    if partita.gioco in (0, 1, 4, 5):
        v += 40.0 * (len(p2.mie[io]) - len(partita.mie[io]))
    if partita.gioco in (3, 7):
        return v
    if p2.turno == io and not p2.ultimo_fallo:
        v += 300.0
        if not p2.ball_in_hand:
            dopo = tiri_visti(p2)
            v += 220.0 * (dopo[0][0] if dopo else -0.3)
    elif not p2.ultimo_fallo:
        lascia = tiri_visti(p2)         # ora e' il turno dell'altro
        v -= 160.0 * (lascia[0][0] if lascia else 0.0)
    return v


def forza_per(lungo, taglio, gioco):
    forza = 0.13 + 0.24 * min(1.0, lungo / (PLAY.w * 1.1))
    forza += 0.10 * (1.0 - taglio)
    if gioco in (2, 6):
        forza *= 0.80           # allo snooker si gioca di tocco
    return forza


def combinazioni(partita, quante):
    """I tiri di combinazione: la bianca colpisce una palla che puo'
    giocare, e quella ne manda un'altra in buca. Alla palla 9 e' il modo
    di chiudere con la 9 anche quando non tocca a lei."""
    cue = partita.cue()
    c = Vector2(cue.pos)
    fuori = []
    for b in palle_da_fare(partita):
        for o in partita.palle:
            if o.dentro or o is b or o is cue:
                continue
            for buca in BUCHE:
                vo = buca - o.pos
                if vo.length() < 1e-6:
                    continue
                vo = vo.normalize()
                ghost_o = o.pos - vo * (BALL_R * 2.0)
                vb = ghost_o - b.pos
                if (o.pos - b.pos).length() < BALL_R * 1.9:
                    continue
                # palle quasi a contatto: la prima parte dritta verso la
                # buca della seconda
                vb = vo if vb.length() < BALL_R * 0.5 else vb.normalize()
                t2 = vb.dot(vo)
                if t2 < 0.5:
                    continue
                ghost_b = b.pos - vb * (BALL_R * 2.0)
                d = ghost_b - c
                if d.length() < BALL_R:
                    continue
                d = d.normalize()
                t1 = d.dot(vb)
                if t1 < 0.35:
                    continue
                if not _strada_libera(partita.palle, c, ghost_b, (cue, b)):
                    continue
                if not _strada_libera(partita.palle, b.pos, ghost_o,
                                      (b, o)):
                    continue
                if not _strada_libera(partita.palle, o.pos, buca, (o,)):
                    continue
                lungo = ((ghost_b - c).length() + (ghost_o - b.pos).length()
                         + (buca - o.pos).length())
                voto = (t1 * t2) ** 2 * (1.0 - min(0.85,
                                                   lungo / (PLAY.w * 3.0)))
                if partita.gioco in (1, 5) and o.num == partita.palla_vince():
                    voto += 1.0         # la 9: si prova per prima
                fuori.append((voto, d, lungo, min(t1, t2)))
    fuori.sort(key=lambda t: -t[0])
    return fuori[:quante]


def candidati_cpu(partita, livello):
    """I tiri da provare: i diretti migliori, le combinazioni, e qualche
    tocco di sicurezza. Ognuno con due o tre forze diverse."""
    quanti = livello_cpu(livello)[4]
    fuori = []
    if partita.gioco == 8:
        return candidati_piramide(partita, livello, quanti)
    if partita.gioco in (3, 7):
        mia = partita.cue()
        avv = None
        for b in partita.palle:
            if b.num == partita.bi_avv():
                avv = b
        if mia is None or avv is None:
            return fuori
        verso = avv.pos - mia.pos
        if verso.length_squared() < 1e-6:
            return fuori
        verso = verso.normalize()
        fianco = Vector2(-verso.y, verso.x)
        passi = max(3, min(9, quanti // 2))
        for k in range(passi):
            off = (k / float(passi - 1) - 0.5) * 3.2 * BALL_R
            d = (avv.pos + fianco * off - mia.pos).normalize()
            for f in (0.32, 0.5, 0.72):
                fuori.append((d, f))
        return fuori
    for _, d, lungo, taglio in tiri_visti(partita)[:quanti]:
        f = forza_per(lungo, taglio, partita.gioco)
        for k in (1.0, 1.35, 0.75):
            fuori.append((d, f * k))
    if livello >= 1:
        for _, d, lungo, taglio in combinazioni(partita,
                                                 max(2, quanti // 2)):
            f = forza_per(lungo, taglio, partita.gioco) * 1.2
            for k in (1.0, 1.4):
                fuori.append((d, f * k))
    d, f = _sicurezza(partita)
    for k in (0.7, 1.0, 1.5):
        fuori.append((d, f * k))
    fuori.extend(difese_cpu(partita, livello))
    return fuori


def difese_cpu(partita, livello):
    """I tiri per non regalare niente: le palle che si possono colpire,
    prese piene o di fino da una parte e dall'altra. Se non se ne vede
    nessuna, si va di sponda: si mira all'immagine della palla riflessa
    nella sponda, come si fa al tavolo vero per uscire da uno snooker."""
    cue = partita.cue()
    c = Vector2(cue.pos)
    mire = sorted(palle_da_fare(partita), key=lambda b: (b.pos - c).length())
    fuori = []
    viste = 0
    for b in mire[:8]:
        if viste >= 3:
            break
        verso = b.pos - c
        if verso.length_squared() < 1e-6:
            continue
        verso = verso.normalize()
        fianco = Vector2(-verso.y, verso.x)
        vista = False
        for off in (0.0, 0.9, -0.9, 1.6, -1.6):
            punto = b.pos + fianco * (off * BALL_R)
            # si tiene solo se la bianca ci arriva senza toccare altro:
            # anche una palla coperta a meta' si prende di fino
            if not _strada_libera(partita.palle, c, punto, (cue, b)):
                continue
            d = punto - c
            if d.length_squared() < 1e-6:
                continue
            vista = True
            for f in (0.26, 0.45):
                fuori.append((d.normalize(), f))
        viste += vista
    if viste or livello < 1:
        return fuori
    sx, dx = PLAY.left + BALL_R, PLAY.right - BALL_R
    su, giu = PLAY.top + BALL_R, PLAY.bottom - BALL_R
    for b in mire[:3]:
        for img in (Vector2(2 * sx - b.pos.x, b.pos.y),
                    Vector2(2 * dx - b.pos.x, b.pos.y),
                    Vector2(b.pos.x, 2 * su - b.pos.y),
                    Vector2(b.pos.x, 2 * giu - b.pos.y)):
            d = img - c
            if d.length_squared() < 1e-6:
                continue
            for f in (0.4, 0.62):
                fuori.append((d.normalize(), f))
    return fuori


def candidati_piramide(partita, livello, quanti):
    """Alla piramide si puo' tirare con qualunque palla: per ognuna si
    guardano i tiri diretti, e si tengono i migliori di tutte. Ogni
    candidato si porta dietro con che palla si tira."""
    era = partita.bilia_tiro
    tutti = []
    vive = [b.num for b in partita.palle if not b.dentro]
    if partita.spaccata:
        vive = [0]                  # si spacca con la rossa
    elif livello < 2:
        vive = vive[:1] + random.sample(vive[1:], min(3, len(vive) - 1))
    for st in vive:
        partita.bilia_tiro = st
        for v, d, lungo, taglio in tiri_visti(partita)[:3]:
            tutti.append((v, d, forza_per(lungo, taglio, 0), st))
    tutti.sort(key=lambda t: -t[0])
    fuori = []
    for _, d, f, st in tutti[:quanti]:
        for k in (1.0, 1.35):
            fuori.append((d, f * k, st))
    partita.bilia_tiro = era
    d, f = _sicurezza(partita)
    for k in (0.8, 1.3):
        fuori.append((d, f * k, era))
    return fuori


def pensa_cpu(partita, livello):
    """Il ragionamento del computer, un tiro provato per volta: e' un
    generatore, cosi' al tavolo si puo' distribuire su piu' fotogrammi e
    il gioco non si pianta mentre pensa. Alla fine torna direzione e
    potenza, con gia' dentro l'errore del livello."""
    _, err_mira, err_forza, rinuncia, _ = livello_cpu(livello)
    if partita.spaccata and partita.gioco in (0, 1, 4, 5):
        return colpo_cpu_semplice(partita, livello)
    prove = []
    era = getattr(partita, "bilia_tiro", 0)
    for c in candidati_cpu(partita, livello):
        d, f = c[0], max(0.12, min(1.0, c[1]))
        st = c[2] if len(c) > 2 else None
        if st is not None:
            partita.bilia_tiro = st     # piramide: la palla con cui si tira
        p2, _ = prova_colpo(partita, d, f)
        prove.append((voto_colpo(partita, p2), d, f, st))
        yield
    partita.bilia_tiro = era
    if not prove:
        return colpo_cpu_semplice(partita, livello)
    prove.sort(key=lambda t: -t[0])
    # I migliori si riprovano un filo storti, di qua e di la': un tiro
    # che entra solo se e' perfetto non vale quanto uno che entra anche
    # sbagliando di poco. Si tiene la media delle tre prove.
    if livello >= 2:
        storto = max(0.35, err_mira * 1.2)
        rifatti = []
        for v, d, f, st in prove[:4]:
            somma = v
            if st is not None:
                partita.bilia_tiro = st
            for giro in (storto, -storto):
                p2, _ = prova_colpo(partita, Vector2(d).rotate(giro), f)
                somma += voto_colpo(partita, p2)
                yield
            rifatti.append((somma / 3.0, d, f, st))
        partita.bilia_tiro = era
        prove = sorted(rifatti, key=lambda t: -t[0]) + prove[4:]
    scelto = prove[0]
    if len(prove) > 1 and random.random() < rinuncia \
            and prove[1][0] > -500.0:
        scelto = prove[1]
    _, d, forza, st = scelto
    if st is not None:
        partita.bilia_tiro = st         # tira con quella che ha scelto
    sbaglio = max(-3.0 * err_mira, min(3.0 * err_mira,
                                       random.gauss(0.0, err_mira)))
    d = Vector2(d).rotate(sbaglio)
    forza *= 1.0 + random.gauss(0.0, err_forza)
    return d, max(0.12, min(1.0, forza))



def stecca_prova(passato, forza):
    """Le stoccate a vuoto prima di tirare. Mentre tiene la mira la
    stecca va avanti e indietro due volte e mezzo, e all'ultima resta
    tirata indietro quanto serve: cosi' quando parte il colpo la stecca
    e' gia' dove deve essere, come al tavolo vero."""
    t = max(0.0, min(1.0, passato / max(0.01, CPU_MIRA)))
    onda = (1.0 - math.cos(2.0 * math.pi * 2.5 * t)) / 2.0
    return forza * (0.12 + 0.88 * onda)


def mira_cpu(da, tiro, resta):
    """Come si vede la stecca mentre il computer si prepara. Prima gira,
    dalla parte dov'era fino alla palla che ha scelto, passando per la
    via piu' corta e rallentando in fondo; quando e' arrivato sta fermo
    sulla mira e fa le stoccate a vuoto. Ritorna la direzione e quanto
    e' tirata indietro la stecca."""
    verso, forza = tiro
    if resta > CPU_MIRA:
        t = max(0.0, min(1.0, 1.0 - (resta - CPU_MIRA) / CPU_CERCA))
        t = t * t * (3.0 - 2.0 * t)             # parte piano, si ferma piano
        giro = (da.angle_to(verso) + 180.0) % 360.0 - 180.0
        return da.rotate(giro * t), forza * 0.12
    return verso, stecca_prova(CPU_MIRA - resta, forza)


def posto_cpu(partita, livello):
    """Dove mette la bianca quando ha palla in mano: prova un mucchio di
    posti buoni e tiene quello da cui vede il tiro migliore. Il
    principiante ne prova pochi e si accontenta."""
    quanti = (30, 50, 80, 120, 180, 240)[max(0, min(5, livello))]
    meglio, voto_meglio = None, -1.0
    for _ in range(quanti):
        if partita.spaccata or partita.gioco == 8:
            x = random.uniform(PLAY.left + BALL_R * 2, LINEA_X - BALL_R * 1.2)
        else:
            x = random.uniform(PLAY.left + BALL_R * 2, PLAY.right - BALL_R * 2)
        y = random.uniform(PLAY.top + BALL_R * 2, PLAY.bottom - BALL_R * 2)
        p = Vector2(x, y)
        if not partita.posto_libero(p):
            continue
        visti = tiri_visti(partita, p)
        voto = visti[0][0] if visti else 0.0
        if voto > voto_meglio:
            meglio, voto_meglio = p, voto
    return meglio


# -------------------------------------------------------------- grafica


# Il triangolo che tiene le palle prima della spaccata. I disegni sono
# tremila per tremila con la punta in basso, e dentro il vuoto misura
# 2574 per 2296 esatto al centro dell'immagine: con queste due misure si
# porta sul tavolo grande quanto le palle, senza andare a tentativi.
TRIANGOLI = ("pool_triangle_wooden.png", "pool_triangle_black.png",
             "pool_triangle_white.png")
TRI_VUOTO = (2574.0, 2296.0)    # il buco dentro il disegno, largo e alto
TRI_ARIA = 6.0                  # quanto sta piu' largo delle palle
TRI_TEMPO = 2.0                 # quanti secondi resta in vista
TRI_FATTI = {}


def misura_rack():
    """Quanto e' ingombrante il mucchio di palle appena messo: largo
    quanto la fila di fondo, lungo dall'apice a quella fila, e dove sta
    il suo centro."""
    passo = BALL_R * 2 + 0.6
    lungo = 4 * passo * 0.866 + BALL_R * 2       # dall'apice alla base
    largo = 4 * passo + BALL_R * 2               # la fila di fondo
    centro = (PALLINO.x + 4 * passo * 0.866 / 2.0, PALLINO.y)
    return lungo, largo, centro


def triangolo(quale):
    """Il triangolo pronto da appoggiare: portato a misura sul mucchio
    di palle e girato con la punta verso la sponda corta, dove sta
    l'apice."""
    if quale in TRI_FATTI:
        return TRI_FATTI[quale]
    TRI_FATTI[quale] = None
    percorso = os.path.join(GFX, TRIANGOLI[quale % len(TRIANGOLI)])
    if not os.path.exists(percorso):
        return None
    try:
        img = pygame.image.load(percorso).convert_alpha()
    except (pygame.error, IOError):
        return None
    lungo, largo, _ = misura_rack()
    # nel disegno l'asse punta-base e' verticale: girandolo di un quarto
    # diventa orizzontale, percio' le due misure si incrociano
    kx = (largo + TRI_ARIA) / TRI_VUOTO[0]
    ky = (lungo + TRI_ARIA) / TRI_VUOTO[1]
    q = pygame.transform.smoothscale(
        img, (max(8, int(img.get_width() * kx)),
              max(8, int(img.get_height() * ky))))
    TRI_FATTI[quale] = pygame.transform.rotate(q, -90)
    return TRI_FATTI[quale]


def posa_triangolo(sc, quale, quanto):
    """Lo appoggia attorno alle palle appena messe, e lo fa sparire
    piano nell'ultimo mezzo secondo."""
    q = triangolo(quale)
    if q is None or quanto <= 0.0:
        return
    if quanto < 0.5:
        # La dissolvenza non si fa con set_alpha su una copia: su Mac quella
        # strada perde il modo di fusione e attorno al triangolo compare il
        # rettangolo nero. Si moltiplica invece il canale alfa.
        velo = pygame.Surface(q.get_size(), pygame.SRCALPHA)
        velo.blit(q, (0, 0))
        velo.fill((255, 255, 255, int(255 * quanto / 0.5)), None,
                  pygame.BLEND_RGBA_MULT)
        q = velo
    sc.blit(q, q.get_rect(center=misura_rack()[2]))


TAVOLO = None
TAVOLO_VERO = {}
SAGOMA = None
COMPOSTO = {}


def sagoma_legno(misura):
    """Una maschera con dentro la sagoma del tavolo: moltiplicata sopra
    il legno, gli toglie tutto quello che resta fuori dal bordo. Gli
    angoli del disegno nuovo sono tondi, non tagliati a quarantacinque
    gradi, e il raggio e' misurato sulla figura. Si disegna in grande e
    si rimpicciolisce, se no la curva viene a scaletta."""
    global SAGOMA
    if SAGOMA is None:
        SU = 3
        grande = pygame.Surface((misura[0] * SU, misura[1] * SU),
                                pygame.SRCALPHA)
        r = pygame.Rect(LEGNO_SU.x * SU, LEGNO_SU.y * SU,
                        LEGNO_SU.w * SU, LEGNO_SU.h * SU)
        pygame.draw.rect(grande, (255, 255, 255, 255), r,
                         border_radius=int(LEGNO_RAGGIO * SU))
        SAGOMA = pygame.transform.smoothscale(grande, misura)
    return SAGOMA


def file_tavolo(disc=None):
    """Quale disegno di tavolo va usato per quella disciplina."""
    if disc is None:
        disc = GIOCO[0]
    if 0 <= disc < len(TAV_FILE_DI):
        return TAV_FILE_DI[disc]
    return TAV_FILE


def tavolo_vero(quale=None):
    """La PNG com'e', senza toccarla: serve a misura piena per montarci
    sotto il panno prima di ridurre tutto insieme."""
    quale = quale or file_tavolo()
    if quale in TAVOLO_VERO:
        return TAVOLO_VERO[quale]
    f = os.path.join(GFX, quale)
    if not os.path.exists(f):
        TAVOLO_VERO[quale] = False
        return False
    try:
        TAVOLO_VERO[quale] = pygame.image.load(f).convert_alpha()
    except pygame.error:
        TAVOLO_VERO[quale] = False
    return TAVOLO_VERO[quale]


# La luce sul panno. Il primo numero e' quanto scurisce l'ombra sotto
# la sponda, il secondo quanto e' larga quella fascia in pixel della
# figura, il terzo quanto schiarisce il centro rispetto ai bordi.
OMBRA_SPONDA = 0.34
OMBRA_LARGA = 30.0
LUCE_CENTRO = 0.11


OMBRA_SFUMA = 5.0       # quanto sfuma l'ombra dove la sponda finisce
SPALLA_ANG = 11.0       # quanto rientra la spalla della sponda, d'angolo
SPALLA_MID = 14.0       # e alla buca centrale


def sponde_ombra(buche=True):
    """I pezzi di sponda che fanno ombra, misurati sulla figura. Ogni
    pezzo e' due punti piu' la normale, cioe' da che parte sta il panno.

    Dove c'e' la buca la sponda non si taglia di netto: finisce con una
    spalla che rientra dentro la bocca, a quarantacinque gradi agli
    angoli e quasi diritta alle centrali. Quella spalla fa ombra come il
    resto, e senza di lei la bocca sembra squadrata."""
    x0, y0, x1, y1 = TAV_PLAY
    xm = (x0 + x1) / 2.0
    if not buche:
        return [((x0, y0), (x1, y0), (0.0, 1.0)),
                ((x0, y1), (x1, y1), (0.0, -1.0)),
                ((x0, y0), (x0, y1), (1.0, 0.0)),
                ((x1, y0), (x1, y1), (-1.0, 0.0))]

    va, vm = VARCO_FIG, VARCO_MID_FIG
    ga, gm = SPALLA_ANG, SPALLA_MID
    pezzi = []
    for y, verso in ((y0, 1.0), (y1, -1.0)):
        pezzi.append(((x0 + va, y), (xm - vm, y), (0.0, verso)))
        pezzi.append(((xm + vm, y), (x1 - va, y), (0.0, verso)))
        for x, lato in ((x0 + va, -1.0), (x1 - va, 1.0)):
            pezzi.append(((x, y), (x + lato * ga, y - verso * ga),
                          (lato, verso)))
        for x, lato in ((xm - vm, 1.0), (xm + vm, -1.0)):
            pezzi.append(((x, y), (x + lato * gm * 0.14, y - verso * gm),
                          (lato, verso * 0.14)))
    for x, verso in ((x0, 1.0), (x1, -1.0)):
        pezzi.append(((x, y0 + va), (x, y1 - va), (verso, 0.0)))
        for y, lato in ((y0 + va, -1.0), (y1 - va, 1.0)):
            pezzi.append(((x, y), (x - verso * ga, y + lato * ga),
                          (verso, lato)))
    return pezzi


def luce_panno(base, buche=True):
    """La lampada sopra il tavolo: il centro del panno e' piu' chiaro,
    gli angoli scuriscono, e sotto il filo delle sponde corre la riga
    d'ombra della gomma. Senza, il panno e' un rettangolo di tinta
    piatta e il tavolo non ha spessore.

    L'ombra e' quella della gomma, quindi finisce dove finisce la gomma:
    davanti alle buche la sponda e' interrotta e l'ombra deve sparire,
    se no il tavolo sembra chiuso tutt'intorno come quello dei birilli."""
    if not HA_NUMPY:
        return
    r = PANNO_SU
    x0, y0, x1, y1 = TAV_PLAY
    xs = np.arange(r.left, r.left + r.w, dtype=np.float32)
    ys = np.arange(r.top, r.top + r.h, dtype=np.float32)

    # Un'ombra per ogni pezzo di sponda: si guarda quanto sei lontano dal
    # suo filo e quanto sei dentro alla sua lunghezza. Dove due pezzi si
    # sovrappongono vince il piu' scuro. La normale tiene l'ombra dalla
    # parte del panno, cosi' sopra la gomma non ci finisce mai: il tavolo
    # ha le luci sopra e la sponda vista da sopra non e' scura.
    X, Y = np.meshgrid(xs, ys, indexing="ij")
    ombra = np.zeros(X.shape, dtype=np.float32)
    for (ax, ay), (bx, by), (nx, ny) in sponde_ombra(buche):
        ux, uy = bx - ax, by - ay
        lungo_tot = math.hypot(ux, uy)
        nn = math.hypot(nx, ny)
        if lungo_tot < 1e-6 or nn < 1e-6:
            continue
        ux, uy = ux / lungo_tot, uy / lungo_tot
        nx, ny = nx / nn, ny / nn
        vx, vy = X - ax, Y - ay
        # distanza vera dal pezzo di sponda, con le punte tonde: cosi'
        # dove un pezzo finisce e comincia il successivo l'ombra gira
        # attorno allo spigolo invece di tagliarsi di netto
        lungo = np.clip(vx * ux + vy * uy, 0.0, lungo_tot)
        sx = vx - lungo * ux
        sy = vy - lungo * uy
        d = np.sqrt(sx * sx + sy * sy)
        stacco = vx * nx + vy * ny
        q = np.where(stacco >= 0.0,
                     np.clip(1.0 - d / OMBRA_LARGA, 0.0, 1.0) ** 1.6, 0.0)
        np.maximum(ombra, q.astype(np.float32), out=ombra)

    if not buche:
        # Il tavolo dei birilli non ha bocche: la sponda gira tutt'intorno
        # e l'ombra sta tutta dentro al campo, senza girare da nessuna
        # parte. Qui si taglia sul filo, com'era prima.
        dx = np.minimum(xs - x0, x1 - xs)
        dy = np.minimum(ys - y0, y1 - ys)
        dentro = np.minimum(dx[:, None], dy[None, :])
        ombra = np.where(dentro >= 0.0, ombra, 0.0)

    # la luce: una macchia morbida al centro
    cx, cy = (x0 + x1) / 2.0, (y0 + y1) / 2.0
    rx = (xs - cx) / ((x1 - x0) / 2.0)
    ry = (ys - cy) / ((y1 - y0) / 2.0)
    rad = np.sqrt(rx[:, None] ** 2 * 0.62 + ry[None, :] ** 2)
    luce = (1.0 + LUCE_CENTRO * np.clip(1.0 - rad, 0.0, 1.0)
            - LUCE_CENTRO * np.clip(rad - 0.55, 0.0, 1.0) * 1.4)

    k = (luce * (1.0 - OMBRA_SPONDA * ombra)).astype(np.float32)
    px = pygame.surfarray.pixels3d(base)
    fetta = px[r.left:r.left + r.w, r.top:r.top + r.h, :]
    fetta[:] = np.clip(fetta * k[:, :, None], 0, 255).astype(np.uint8)
    del px


# ------------------------------------------------------------ i diamanti

# I segni sul legno. Non stanno piu' dentro le PNG: si disegnano qui,
# cosi' ogni tavolo puo' portare la sua forma e un giorno si potra'
# sceglierla come si sceglie il panno. Le misure sono quelle della
# figura, prima di ridurre.
DIAMANTE_LARGO = 7.0            # di traverso alla sponda
DIAMANTE_LUNGO = 12.0           # lungo la sponda
FORME_DIAMANTE = ("rombo", "tondo", "quadro", "barra", "mandorla")

# La tinta del segno non e' mai bianca fissa: dipende dalla cornice.
# Sul legno si sta in famiglia - sabbia e cammello sui legni scuri,
# bruno di wenge' sui legni chiari - e il segno tira un filo verso la
# tinta del legno, cosi' sembra intarsiato invece che appiccicato sopra.
# Su tutto quello che legno non e' (marmo, acciaio, laccati, pelle,
# rosso ferrari) si va di contrasto netto: bianco sugli scuri e un nero
# morbido sui chiari, che il nero pieno su un marmo fa cartone.
DIAMANTE_CHIARO = (238, 222, 188)       # sabbia, cammello
DIAMANTE_SCURO = (54, 34, 20)           # wenge'
DIAMANTE_BIANCO = (250, 250, 252)
DIAMANTE_NERO = (34, 32, 36)
DIAMANTE_SOGLIA = 112.0                 # sotto questa luce la cornice e' scura
DIAMANTE_TIRA = 0.82                    # quanto va verso la tinta, sul legno
DIAMANTE_TIRA_FINTO = 0.92              # e su quello che legno non e'

# Quali cornici sono di materiale caldo e naturale: i legni e le pelli.
# Su queste il segno resta in famiglia, come un intarsio di osso o di
# radica. Tutto il resto - marmo, acciaio, laccati, foglie metalliche,
# vetro - va di contrasto. Il nome e' quello del file, senza il numero
# in coda. Attenzione a "cocco": non e' la palma, e' il coccodrillo,
# cioe' pelle.
CORNICI_CALDE = frozenset((
    "bamboo", "castagno", "ciliegio", "ebano", "faggio", "frassino",
    "invecchiato", "mogano", "noce-americano", "noce-italiano", "olmo",
    "palissandro", "quercia", "rovere", "tinto-noce", "ulivo", "wenge",
    "zebrano",
    "cocco", "pelle-liscia", "pelle-martellata", "pelle-traforata",
    "scamosciato", "maglia"))


def tinta_legno(percorso):
    """Il colore medio vero di una texture. Non si usa colore_medio, che
    rimpicciolisce a un pixel solo e su immagini grandi sbaglia di
    parecchio: qui serve giusta, se no il segno finisce del colore
    sbagliato."""
    if percorso not in MEDIE_VERE:
        try:
            img = pygame.image.load(percorso).convert()
            MEDIE_VERE[percorso] = tuple(
                pygame.transform.average_color(img)[:3])
        except (pygame.error, IOError):
            MEDIE_VERE[percorso] = (120, 70, 40)
    return MEDIE_VERE[percorso]


MEDIE_VERE = {}


def cornice_calda(percorso):
    nome = os.path.splitext(os.path.basename(percorso))[0].lower()
    while nome and nome[-1].isdigit():
        nome = nome[:-1]
    return nome.rstrip("-_ ") in CORNICI_CALDE

# Che segni porta ognuno dei due tavoli.
DIAMANTE_BUCHE = "rombo"
DIAMANTE_BIRILLI = "tondo"


def posti_diamanti(buche=True):
    """Dove vanno i segni sul legno, sulla figura.

    Il tavolo con le buche li porta a ogni ottavo della lunghezza, ma
    quello di mezzo e' la buca centrale e quindi salta, e a ogni quarto
    della larghezza: sei per sponda lunga e tre per la corta. Il tavolo
    dei birilli li porta a ogni ottavo angoli compresi, e cinque per la
    corta, come si usa sul tavolo all'italiana."""
    x0, y0, x1, y1 = TAV_PLAY
    vx, vy, vw, vh = LEGNO_SU
    # in mezzo alla fascia di legno: dal filo esterno al filo della gomma
    su = (vy + y0 - TAV_GOMMA) / 2.0
    giu = (vy + vh + y1 + TAV_GOMMA) / 2.0
    sin = (vx + x0 - TAV_GOMMA) / 2.0
    des = (vx + vw + x1 + TAV_GOMMA) / 2.0

    if buche:
        ottavi = [k for k in range(1, 8) if k != 4]
        quarti = [1, 2, 3]
    else:
        ottavi = list(range(0, 9))
        quarti = [0, 1, 2, 3, 4]

    fuori = []
    for k in ottavi:
        x = x0 + (x1 - x0) * k / 8.0
        fuori.append((x, su, True))
        fuori.append((x, giu, True))
    for k in quarti:
        y = y0 + (y1 - y0) * k / 4.0
        fuori.append((sin, y, False))
        fuori.append((des, y, False))
    return fuori


def tinta_diamante(i_bordo=0):
    """Il segno si legge sempre: chiaro sulla cornice scura, scuro sulla
    cornice chiara. Sul legno resta in famiglia, sul resto va di
    contrasto."""
    if BORDI and 0 <= i_bordo < len(BORDI):
        percorso = BORDI[i_bordo][1]
        fondo = tinta_legno(percorso)
        calda = cornice_calda(percorso)
    else:
        fondo, calda = (120, 70, 40), True
    luce = 0.299 * fondo[0] + 0.587 * fondo[1] + 0.114 * fondo[2]
    scura = luce < DIAMANTE_SOGLIA
    if calda:
        verso = DIAMANTE_CHIARO if scura else DIAMANTE_SCURO
        k = DIAMANTE_TIRA
    else:
        verso = DIAMANTE_BIANCO if scura else DIAMANTE_NERO
        k = DIAMANTE_TIRA_FINTO
    return tuple(int(round(fondo[i] * (1.0 - k) + verso[i] * k))
                 for i in range(3))


def segna_diamante(sc, cx, cy, forma, orizzontale, tinta=(246, 247, 250)):
    """Un segno solo. Il lato lungo sta sempre di traverso alla sponda,
    come sui tavoli veri."""
    a = DIAMANTE_LARGO / 2.0            # meta' di traverso
    b = DIAMANTE_LUNGO / 2.0            # meta' nel verso lungo
    if orizzontale:                     # sponda lunga: il segno e' in piedi
        rx, ry = a, b
    else:                               # sponda corta: coricato
        rx, ry = b, a

    if forma == "tondo":
        r = int(round(min(rx, ry) * 1.15))
        pygame.draw.circle(sc, tinta, (int(round(cx)), int(round(cy))), r)
        return
    if forma == "quadro":
        q = pygame.Rect(0, 0, int(round(rx * 1.5)), int(round(ry * 1.5)))
        q.center = (int(round(cx)), int(round(cy)))
        pygame.draw.rect(sc, tinta, q)
        return
    if forma == "barra":
        q = pygame.Rect(0, 0, int(round(rx * 1.1)), int(round(ry * 2.0)))
        q.center = (int(round(cx)), int(round(cy)))
        pygame.draw.rect(sc, tinta, q,
                         border_radius=int(round(min(q.w, q.h) / 2.0)))
        return
    if forma == "mandorla":
        q = pygame.Rect(0, 0, int(round(rx * 2.1)), int(round(ry * 1.8)))
        q.center = (int(round(cx)), int(round(cy)))
        pygame.draw.ellipse(sc, tinta, q)
        return
    # rombo, quello di prima
    pygame.draw.polygon(sc, tinta,
                        [(cx, cy - ry), (cx + rx, cy),
                         (cx, cy + ry), (cx - rx, cy)])


def disegna_diamanti(base, buche=True, i_bordo=0):
    """Tutti i segni del tavolo, sul legno gia' steso."""
    forma = DIAMANTE_BUCHE if buche else DIAMANTE_BIRILLI
    tinta = tinta_diamante(i_bordo)
    for cx, cy, orizzontale in posti_diamanti(buche):
        segna_diamante(base, cx, cy, forma, orizzontale, tinta)


def tavolo_composto(i_panno, i_bordo=0, quale=None):
    """Il tavolo montato a strati: prima il legno su tutta la sagoma, poi
    il panno a quadretti dentro PANNO_SU, cioe' fin dove arriva la
    sponda e non oltre; sopra ci va la PNG, che con le sue buche e il
    suo scuro copre il panno dove serve. Si monta alla misura vera
    dell'immagine e si riduce tutto insieme una volta sola: cosi'
    all'angolo il panno finisce esatto contro la buca invece di restare
    tagliato in linea."""
    quale = quale or file_tavolo()
    chiave = (i_panno, i_bordo, quale)
    if chiave in COMPOSTO:
        return COMPOSTO[chiave]
    vero = tavolo_vero(quale)
    if not vero:
        return None
    base = pygame.Surface(vero.get_size(), pygame.SRCALPHA)
    if BORDI and 0 <= i_bordo < len(BORDI):
        l = texture(BORDI[i_bordo][1], (LATO_LEGNO, LATO_LEGNO))
        if l is not None:
            legno = pygame.Surface(base.get_size(), pygame.SRCALPHA)
            for x in range(0, legno.get_width(), LATO_LEGNO):
                for y in range(0, legno.get_height(), LATO_LEGNO):
                    legno.blit(l, (x, y))
            legno.blit(sagoma_legno(base.get_size()), (0, 0),
                       special_flags=pygame.BLEND_RGBA_MULT)
            base.blit(legno, (0, 0))
    if PANNI and 0 <= i_panno < len(PANNI):
        q = texture(PANNI[i_panno][1], (LATO_PANNO, LATO_PANNO))
        if q is not None:
            campo = base.subsurface(PANNO_SU)
            for x in range(0, campo.get_width(), LATO_PANNO):
                for y in range(0, campo.get_height(), LATO_PANNO):
                    campo.blit(q, (x, y))
            luce_panno(base, quale != TAV_FILE_DI[3])
    disegna_diamanti(base, quale != TAV_FILE_DI[3], i_bordo)
    base.blit(vero, (0, 0))
    if len(COMPOSTO) > 3:            # non tenerne in piedi ventiquattro
        COMPOSTO.clear()
    COMPOSTO[chiave] = pygame.transform.smoothscale(
        base, (int(TAV_W * SCALA), int(TAV_H * SCALA)))
    return COMPOSTO[chiave]


MINIATURE = {}
MINI_LARGA = 480        # quanto e' larga l'anteprima nelle impostazioni
MINI_FETTA = (0.0, 0.66, 0.50, 0.34)   # che pezzo di tavolo si guarda


def tavolo_mini(i_panno, i_bordo, quale=None):
    """L'anteprima delle impostazioni: non tutto il tavolo, che a quella
    misura non si vedrebbe niente, ma solo l'angolo in basso a sinistra
    con la sua buca, ingrandito. Cosi' si vede la trama del panno, il
    materiale della sponda e come vengono insieme."""
    quale = quale or file_tavolo()
    chiave = (i_panno, i_bordo, quale)
    if chiave not in MINIATURE:
        grande = tavolo_composto(i_panno, i_bordo, quale)
        if grande is None:
            return None
        w, h = grande.get_size()
        fx, fy, fw, fh = MINI_FETTA
        fetta = pygame.Rect(int(w * fx), int(h * fy),
                            int(w * fw), int(h * fh))
        fetta = fetta.clip(grande.get_rect())
        pezzo = grande.subsurface(fetta)
        alta = int(MINI_LARGA * fetta.h / float(fetta.w))
        if len(MINIATURE) > 24:
            MINIATURE.clear()
        MINIATURE[chiave] = pygame.transform.smoothscale(
            pezzo, (MINI_LARGA, alta))
    return MINIATURE[chiave]


def carica_tavolo():
    """La PNG del tavolo, portata alla misura del gioco. Dentro ci sono
    solo le linee e il nero delle buche: tutto il resto e' trasparente, e
    i materiali ci vanno sotto."""
    global TAVOLO
    if TAVOLO is not None:
        return TAVOLO
    f = os.path.join(GFX, TAV_FILE)
    if not os.path.exists(f):
        TAVOLO = False
        return TAVOLO
    try:
        img = pygame.image.load(f).convert_alpha()
    except pygame.error:
        TAVOLO = False
        return TAVOLO
    TAVOLO = pygame.transform.smoothscale(
        img, (int(TAV_W * SCALA), int(TAV_H * SCALA)))
    return TAVOLO


def disegna_tavolo(sc, i_panno=0, i_bordo=0, quale=None, gioco=None):
    """Il tavolo e' gia' tutto in un pezzo solo: qui si appoggia e
    basta. Linea di partenza, D e puntini dello snooker stanno gia'
    dentro il disegno."""
    sc.blit(fondo(), (0, 0))
    tav = tavolo_composto(i_panno, i_bordo, quale)
    if tav:
        sc.blit(tav, TAV_POS)


def disegna_palla(sc, b, font):
    x, y = int(b.pos.x), int(b.pos.y)
    r = int(BALL_R)

    if HA_NUMPY:
        if OMBRA is not None:
            sc.blit(OMBRA, OMBRA.get_rect(center=(x + 3, y + 4)))
        disegna_sfera(sc, b)
        return

    # ombra sul panno
    pygame.draw.circle(sc, (8, 44, 68), (x + 2, y + 3), r)

    if b.num == 0:
        base = (244, 244, 240)
    else:
        base = colore_palla(b.num)

    pygame.draw.circle(sc, base, (x, y), r)

    # le mezze hanno la fascia bianca sopra e sotto
    if b.mezza:
        pygame.draw.circle(sc, (244, 244, 240), (x, y), r)
        h = int(r * 0.98)
        pygame.draw.ellipse(sc, base, pygame.Rect(x - r, y - h // 2, r * 2, h))

    # numero nel cerchietto bianco
    if b.num != 0:
        pygame.draw.circle(sc, (248, 248, 246), (x, y), int(r * 0.52))
        t = font.render(str(b.num), True, (26, 26, 30))
        sc.blit(t, t.get_rect(center=(x, y)))

    # luce in alto a sinistra
    luce = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
    pygame.draw.circle(luce, (255, 255, 255, 90),
                       (int(r * 0.62), int(r * 0.58)), int(r * 0.42))
    sc.blit(luce, (x - r, y - r))
    pygame.draw.circle(sc, (0, 0, 0, 60), (x, y), r, 1)


def disegna_birillo(sc, bir):
    """Il birillo visto da sopra: un cerchietto con la sua ombra. Se e'
    caduto non si disegna, torna al tiro dopo."""
    if not bir.in_piedi:
        return
    x, y = int(bir.pos.x), int(bir.pos.y)
    r = max(2, int(round(BIRILLO_R)))
    pygame.draw.circle(sc, (10, 46, 30), (x + 1, y + 2), r)
    st = set_birilli()
    centrale = st[5] if len(st) > 5 else (188, 40, 34)
    altri = st[6] if len(st) > 6 else (238, 234, 222)
    pygame.draw.circle(sc, centrale if bir.rosso else altri, (x, y), r)
    pygame.draw.circle(sc, (52, 44, 36), (x, y), r, 1)


PROVA = [False]         # F3: fa vedere dove il gioco crede che sia il tavolo
# Prove in partita: T gira i sei tavoli del torneo, B i set di palle.
# In alto a sinistra si legge per un attimo cosa c'e' adesso.
TAV_PROVA = [None]
BORDO_PROVA = [None]    # R: le cornici sul panno di adesso
BORDO_ORA = [0]         # la cornice che si sta disegnando
PANNO_ORA = [0]         # e il panno
SCRITTA_PROVA = ["", 0]


def prova_tasto(key):
    """T e B in partita. Ritorna True se il tasto era suo."""
    if not DENTRO_PARTITA[0] or key not in (pygame.K_t, pygame.K_b,
                                            pygame.K_r):
        return False
    if key == pygame.K_r:
        if not BORDI:
            return True
        k = (BORDO_ORA[0] + 1) % len(BORDI)
        BORDO_PROVA[0] = k
        testo = "Frame: %s" % os.path.basename(BORDI[k][1]).rsplit(".", 1)[0]
    elif key == pygame.K_t:
        k = 0 if TAV_PROVA[0] is None else (TAV_PROVA[0] + 1) % 6
        TAV_PROVA[0] = k
        BORDO_PROVA[0] = None
        pa, le = TORNEO_TAVOLI.get(GIOCO[0], TORNEO_SEI)[k]
        testo = "Table %d: %s + %s" % (k + 1, pa.rsplit(".", 1)[0],
                                       le.rsplit(".", 1)[0])
    else:
        tp = tipo_palle()
        elenco = elenco_set(tp)
        k = (scelta_palle(tp) + 1) % len(elenco)
        PALLE_TORNEO[0] = None      # in prova comanda B
        d = dict(CFG.get("palle") or {})
        d[tp] = k
        CFG["palle"] = d
        applica_palle()
        testo = "Balls: %s" % T(elenco[k][0])
    SCRITTA_PROVA[0], SCRITTA_PROVA[1] = testo, pygame.time.get_ticks()
    return True


def scritta_prova(sc):
    """Toccato T, B o R, in alto a destra restano i nomi di palle, panno
    e cornice di adesso, per tutta la partita."""
    if not SCRITTA_PROVA[0]:
        return
    tp = tipo_palle()
    nome = lambda el, i: (os.path.basename(el[i][1]).rsplit(".", 1)[0]
                          if 0 <= i < len(el) else "-")
    righe = ["Balls: %s" % T(elenco_set(tp)[scelta_palle(tp)][0]),
             "Cloth: %s" % nome(PANNI, PANNO_ORA[0]),
             "Frame: %s" % nome(BORDI, BORDO_ORA[0])]
    if TAV_PROVA[0] is not None:
        righe.insert(0, "Table %d" % (TAV_PROVA[0] + 1))
    tt = [FONTS["mini"].render(r, True, (255, 255, 255)) for r in righe]
    w = max(t.get_width() for t in tt) + s(16)
    h = sum(t.get_height() for t in tt) + s(10)
    q = pygame.Surface((w, h), pygame.SRCALPHA)
    q.fill((0, 0, 0, 170))
    y = s(5)
    for t in tt:
        q.blit(t, (w - s(8) - t.get_width(), y))
        y += t.get_height()
    y_su = (ALTO + BASSO) // 2 - s(95) - h - s(40)
    sc.blit(q, (WIN_W - w - s(12), max(s(60), y_su)))


def disegna_prova(sc):
    """Il controllo delle misure: fa vedere in rosso dove la fisica crede
    che stiano le buche e dove crede che finisca la sponda, cosi' si
    confronta a occhio col disegno. Si accende e si spegne con F3."""
    ROSSO = (255, 60, 60)
    ROSA = (255, 150, 150)
    BLU = (80, 200, 255)
    GIALLO = (255, 220, 60)

    # il campo: dove batte la palla
    pygame.draw.rect(sc, BLU, PLAY, 1)

    for i, q in enumerate(BUCHE):
        c = (int(q.x), int(q.y))
        # il nero come sta sul disegno
        pygame.draw.circle(sc, GIALLO, c,
                           int((R_MID if i in (1, 4) else R_ANG)), 1)
        # dove la palla viene presa, e la presa larga della rete
        pygame.draw.circle(sc, ROSSO, c, int(PRESA[i]), 1)
        pygame.draw.circle(sc, ROSA, c, int(PRESA_FUORI[i]), 1)
        pygame.draw.line(sc, ROSSO, (c[0] - 4, c[1]), (c[0] + 4, c[1]))
        pygame.draw.line(sc, ROSSO, (c[0], c[1] - 4), (c[0], c[1] + 4))

    # dove la sponda si interrompe: i tratti verdi sono sponda viva
    for y in (PLAY.top, PLAY.bottom):
        tratti = [(PLAY.left + VARCO, PLAY.centerx - VARCO_MID),
                  (PLAY.centerx + VARCO_MID, PLAY.right - VARCO)]
        for a, b in tratti:
            pygame.draw.line(sc, (60, 255, 120), (a, y), (b, y), 2)
    for x in (PLAY.left, PLAY.right):
        pygame.draw.line(sc, (60, 255, 120), (x, PLAY.top + VARCO),
                         (x, PLAY.bottom - VARCO), 2)

    f = FONTS["mini"]
    righe = ["F3  prova misure",
             "campo %d x %d px" % (PLAY.w, PLAY.h),
             "palla r %.1f   presa %.1f / %.1f" % (BALL_R, PRESA_ANG,
                                                  PRESA_MID),
             "varco %.1f / %.1f" % (VARCO, VARCO_MID)]
    for k, riga in enumerate(righe):
        t = f.render(riga, True, ROSSO)
        sc.blit(t, (10, 10 + k * 13))


def traccia_mira(sc, partita, mira, potenza, linea=True):
    """Linea di mira: si ferma sulla prima palla incontrata. Senza linea
    resta solo la stecca: e' quello che si vede quando tira il computer,
    che dove mira lo deve capire chi guarda, non leggerlo scritto."""
    cue = partita.cue()
    if cue is None or cue.dentro:
        return

    p = Vector2(cue.pos)
    d = Vector2(mira)
    if d.length_squared() < 1e-6:
        return
    d = d.normalize()

    if not linea:
        disegna_stecca(sc, p, d, potenza, partita.turno)
        return

    # distanza fino alla prima palla sulla traiettoria
    meglio = None
    colpita = None
    for b in partita.palle:
        # si salta la bilia con cui si sta tirando, non la bianca: ai
        # birilli il secondo giocatore tira con la gialla e la bianca
        # diventa una bilia da mirare come le altre
        if b.dentro or b is cue:
            continue
        f = b.pos - p
        proj = f.dot(d)
        if proj <= 0:
            continue
        perp2 = f.length_squared() - proj * proj
        soglia = (BALL_R * 2) ** 2
        if perp2 > soglia:
            continue
        t = proj - math.sqrt(soglia - perp2)
        if t < 0:
            continue
        if meglio is None or t < meglio:
            meglio = t
            colpita = b

    # se non incontra niente, tira fino alla sponda
    asse_sponda = None
    if meglio is None:
        meglio = 4000.0
        for bordo, asse in ((PLAY.left + BALL_R, 0), (PLAY.right - BALL_R, 0),
                            (PLAY.top + BALL_R, 1), (PLAY.bottom - BALL_R, 1)):
            dd = d.x if asse == 0 else d.y
            pp = p.x if asse == 0 else p.y
            if abs(dd) > 1e-6:
                t = (bordo - pp) / dd
                if 0 < t < meglio:
                    meglio = t
                    asse_sponda = asse
    # quanto crescono le righe con la stecca
    f = max(0.0, min(1.0, (doti_di(partita.turno)[0] - 10) / 90.0))
    corta = PLAY.w * 80.0 / 950.0
    gesso = GESSO[partita.turno] if partita.turno in (0, 1) else 1.0
    # col gesso che cala le righe dopo il colpo sbiadiscono
    opaco = 1.0 - 0.65 * (1.0 - gesso) / (1.0 - GESSO_MIN)

    # Se la prima palla che prendi non e' delle tue, il cerchietto diventa
    # rosso: quel tiro sarebbe fallo.
    ok = colpita is None or partita.prima_legale(colpita.num)
    col = (255, 255, 255) if ok else (236, 72, 72)

    fine = p + d * meglio
    # dalla bianca alla palla fantasma: un fascio chiaro, che parte dopo
    # la bianca e si ferma al cerchio
    fascio(sc, p + d * BALL_R, d, meglio - 2 * BALL_R, col,
           BALL_R * 0.34, 0.35)
    anello(sc, col, fine, BALL_R)
    if not ok:
        anello(sc, col, fine, BALL_R + 3)

    # dove andra' la palla colpita
    if colpita is not None:
        via = (colpita.pos - fine)
        if via.length_squared() > 1e-6:
            via = via.normalize()
            # quanto manca alla sponda, lungo la strada della palla
            fino = 4000.0
            for bordo, asse in ((PLAY.left + BALL_R, 0),
                                (PLAY.right - BALL_R, 0),
                                (PLAY.top + BALL_R, 1),
                                (PLAY.bottom - BALL_R, 1)):
                dd = via.x if asse == 0 else via.y
                pp = colpita.pos.x if asse == 0 else colpita.pos.y
                if abs(dd) > 1e-6:
                    t = (bordo - pp) / dd
                    if 0 < t < fino:
                        fino = t
            # la prima stecca un filo meno di prima; la leggenda arriva
            # fino in buca
            diag = math.hypot(PLAY.w, PLAY.h)
            lunga = fino if f >= 1.0 else min(
                fino, corta + (diag - corta) * f ** 1.3)
            lunga *= gesso
            fascio(sc, colpita.pos + via * BALL_R, via, lunga - BALL_R,
                   col, BALL_R * 0.36, opaco=opaco)
            # e dove va la bianca dopo il colpo: a novanta gradi dalla
            # palla colpita. Cresce poco: dalla meta' della riga corta
            # fino alla riga corta intera.
            tang = d - via * d.dot(via)
            if tang.length_squared() > 0.02:
                tang = tang.normalize()
                corta_b = corta * (0.5 + 0.5 * f) * gesso
                fascio(sc, fine + tang * BALL_R, tang, corta_b, col,
                       BALL_R * 0.26, 0.8, opaco)
    elif asse_sponda is not None:
        # sulla sponda: l'angolo del rimbalzo, dalla meta' della riga corta
        # fino al doppio
        rimb = Vector2(-d.x, d.y) if asse_sponda == 0 else Vector2(d.x, -d.y)
        fino = 4000.0           # non oltre la sponda di fronte
        for bordo, asse in ((PLAY.left + BALL_R, 0), (PLAY.right - BALL_R, 0),
                            (PLAY.top + BALL_R, 1), (PLAY.bottom - BALL_R, 1)):
            dd = rimb.x if asse == 0 else rimb.y
            pp = fine.x if asse == 0 else fine.y
            if abs(dd) > 1e-6:
                t = (bordo - pp) / dd
                if 1e-3 < t < fino:
                    fino = t
        fascio(sc, fine + rimb * BALL_R, rimb,
               min(fino - BALL_R, corta * (0.5 + 1.5 * f) * gesso), col,
               BALL_R * 0.30, 0.8, opaco)

    disegna_stecca(sc, p, d, potenza, partita.turno)


def disegna_stecca(sc, p, d, potenza, chi=0):
    """La stecca dietro la bianca: piu' e' carica, piu' si tira indietro.
    Ogni giocatore ha la sua: quella dell'avversario e' sempre un'altra."""
    indietro = 24 + potenza * 80
    p0 = Vector2(p) - d * indietro          # il cuoio
    lung = PLAY.w * 145.0 / 254.0           # stecca da 145 cm
    # i 13 mm della ghiera, i 20 della giunzione e i 30 del fondello
    raggi = (PLAY.w * 1.30 / 254.0 / 2.0, PLAY.w * 2.00 / 254.0 / 2.0,
             PLAY.w * 3.00 / 254.0 / 2.0)
    # la stecca si vede solo sopra il tavolo: fuori ci sono le scritte
    vista = pygame.Rect(int(TAV_POS[0] + LEGNO_SU.x * SCALA),
                        int(TAV_POS[1] + LEGNO_SU.y * SCALA),
                        int(LEGNO_SU.w * SCALA), int(LEGNO_SU.h * SCALA))
    prima = sc.get_clip()
    sc.set_clip(vista.clip(prima))
    disegna_stecca_su(sc, p0, d, lung, raggi, stecca_di(chi))
    sc.set_clip(prima)


def _tinta(c, k):
    """Il colore piu' scuro (k < 1) o piu' chiaro (k > 1)."""
    if k <= 1.0:
        return tuple(max(0, int(v * k)) for v in c[:3])
    return tuple(min(255, int(v + (255 - v) * (k - 1.0))) for v in c[:3])


def _materiale(sc, punto, pezzo, raggio, a, b, colore, mat, lung):
    """Sopra il colore del tratto, il disegno del materiale."""
    lpx = (b - a) * lung                     # quanto e' lungo in pixel
    rm = raggio((a + b) / 2.0)
    if lpx < 2 or rm < 1.0:
        return
    if mat == "legno":
        # le venature: fili un po' ondulati lungo la stecca
        c = _tinta(colore, 0.80)
        passi = max(3, int(lpx / 6))
        for k, tt in enumerate((-0.62, -0.18, 0.28, 0.66)):
            fase = k * 1.7 + a * 40.0
            pts = [punto(a + (b - a) * i / passi,
                         tt + 0.10 * math.sin(fase + i * 0.9))
                   for i in range(passi + 1)]
            if len(pts) > 1:
                pygame.draw.aalines(sc, c, False, pts)
    elif mat == "lino":
        # il filo avvolto: tante righine di traverso
        c = _tinta(colore, 1.25)
        passo = max(2.0, rm * 0.55)
        k = 0
        while k * passo < lpx:
            f = a + k * passo / lung
            pygame.draw.aaline(sc, c, punto(f, -0.9), punto(f, 0.9))
            k += 1
    elif mat == "pelle":
        c = _tinta(colore, 1.18)
        pygame.draw.aaline(sc, c, punto(a, 0.35), punto(b, 0.35))
    elif mat == "lacca":
        # lucida: un riflesso netto
        c = _tinta(colore, 1.55)
        pygame.draw.aaline(sc, c, punto(a, 0.30), punto(b, 0.30))
        pygame.draw.aaline(sc, _tinta(colore, 1.25), punto(a, 0.40),
                           punto(b, 0.40))
    elif mat == "metallo":
        # spazzolato: fili chiari e scuri, e un riflesso forte
        for tt, k in ((-0.70, 0.72), (-0.35, 0.86), (0.05, 1.12),
                      (0.25, 1.60), (0.55, 1.20)):
            pygame.draw.aaline(sc, _tinta(colore, k), punto(a, tt),
                               punto(b, tt))
    elif mat in ("carbonio", "scacchi"):
        # la trama: quadretti alterni, due di traverso
        if mat == "scacchi":
            c1, c2 = colore, NERO
            passo = max(3.0, rm * 1.6)
        else:
            c1, c2 = colore, (_tinta(colore, 1.14) if sum(colore[:3]) < 450
                              else _tinta(colore, 0.88))
            passo = max(2.5, rm * 0.9)
        k = 0
        while k * passo < lpx:
            f0 = a + k * passo / lung
            f1 = min(b, a + (k + 1) * passo / lung)
            for mezza, (t0, t1) in enumerate(((-1.0, 0.0), (0.0, 1.0))):
                c = c2 if (k + mezza) % 2 else c1
                if c != colore:
                    pezzo([punto(f0, t0), punto(f1, t0), punto(f1, t1),
                           punto(f0, t1)], c)
            k += 1
    elif mat in ("madreperla", "radica", "forgiato"):
        # macchie sparse, sempre le stesse per quel tratto
        rnd = random.Random(int(a * 1000) * 7 + int(b * 1000))
        if mat == "madreperla":
            tinte = [_tinta(colore, 1.35), (170, 210, 220), (210, 190, 230),
                     (190, 230, 200), _tinta(colore, 0.85)]
        elif mat == "radica":
            tinte = [_tinta(colore, 0.62), _tinta(colore, 0.75)]
        else:
            tinte = [_tinta(colore, 1.45), _tinta(colore, 1.25),
                     _tinta(colore, 0.7)]
        quante = int(lpx / max(1.5, rm * 0.7))
        for _ in range(quante):
            f = a + (b - a) * rnd.random()
            t = rnd.uniform(-0.8, 0.8)
            df = rm * rnd.uniform(0.25, 0.8) / lung
            dt = rnd.uniform(0.12, 0.3)
            pezzo([punto(f - df, t), punto(f, t + dt), punto(f + df, t),
                   punto(f, t - dt)], rnd.choice(tinte))


def _decora(sc, punto, pezzo, raggio, deco, lung):
    """Le decorazioni intarsiate sopra la stecca."""
    tipo = deco[0]
    if tipo == "strisce":
        for f0, f1 in deco[1]:
            pezzo([punto(f0, -1), punto(f1, -1), punto(f1, 1),
                   punto(f0, 1)], deco[2])
    elif tipo == "spirale":
        _, a, b, quante, colore, largo = deco
        storto = 2.2 * raggio((a + b) / 2.0) / lung
        passo = (b - a) / float(quante)
        for k in range(quante):
            f0 = a + k * passo
            f1 = min(b - storto, f0 + largo)
            if f1 <= f0:
                continue
            pezzo([punto(f0, -1), punto(f1, -1), punto(f1 + storto, 1),
                   punto(f0 + storto, 1)], colore)
    elif tipo == "rombi":
        _, dove, colore, mezzo = deco
        for f in dove:
            pezzo([punto(f - mezzo, 0), punto(f, 0.72),
                   punto(f + mezzo, 0), punto(f, -0.72)], colore)
    elif tipo == "punti":
        _, dove, colore = deco
        for f in dove:
            q = punto(f, 0)
            r = max(1, int(round(raggio(f) * 0.32)))
            gfxdraw.filled_circle(sc, int(q.x), int(q.y), r, colore)
            gfxdraw.aacircle(sc, int(q.x), int(q.y), r, colore)


def disegna_stecca_su(sc, p0, d, lung, raggi, stecca):
    """Una stecca qualunque: dal cuoio in p0, lunga lung, verso -d. Non e'
    un'immagine, e' disegnata: un tronco di cono coi suoi tratti, le
    punte intarsiate se ce le ha, e sopra la luce e l'ombra del tondo."""
    p1 = p0 - d * lung
    n = Vector2(-d.y, d.x)
    r0, rg, r1 = raggi
    # La stecca non e' un cono dritto: dalla punta resta sottile per una
    # trentina di centimetri, poi ingrossa fino alla giunzione a meta' e
    # da li' fino al calcio.
    DRITTA = 30.0 / 145.0

    def raggio(f):
        if f <= DRITTA:
            return r0
        if f <= 0.5:
            return r0 + (rg - r0) * (f - DRITTA) / (0.5 - DRITTA)
        return rg + (r1 - rg) * (f - 0.5) / 0.5

    def pezzo(punti, colore):
        q = [(int(round(x)), int(round(y))) for x, y in punti]
        gfxdraw.filled_polygon(sc, q, colore)
        gfxdraw.aapolygon(sc, q, colore)

    def punto(f, t):
        """Il punto sulla stecca: f lungo, t di traverso da -1 a 1."""
        return p0 + (p1 - p0) * f + n * (raggio(f) * t)

    for tratto in stecca[1]:
        a, b, colore = tratto[0], tratto[1], tratto[2]
        pa = p0 + (p1 - p0) * a
        pb = p0 + (p1 - p0) * b
        ra, rb = raggio(a), raggio(b)
        pezzo([pa + n * ra, pb + n * rb, pb - n * rb, pa - n * ra], colore)
        if len(tratto) > 3 and tratto[3]:
            _materiale(sc, punto, pezzo, raggio, a, b, colore, tratto[3],
                       lung)

    # Le punte: i triangoli intarsiati che dal manico entrano nel legno
    # davanti, con sotto la venatura, un filo di un altro colore.
    if len(stecca) > 2 and stecca[2]:
        colore, vena, a, b = stecca[2]
        pa = p0 + (p1 - p0) * a
        pb = p0 + (p1 - p0) * b
        rb = raggio(b)
        for fetta, c in ((0.96, vena), (0.80, colore)):
            punta = pb + (pa - pb) * fetta
            pezzo([pb + n * rb * fetta, punta, pb - n * rb * fetta], c)

    # le decorazioni: strisce, spirali, rombi e punti intarsiati
    for deco in (stecca[3] if len(stecca) > 3 else ()):
        _decora(sc, punto, pezzo, raggio, deco, lung)

    # il tondo: una riga di luce da una parte e una d'ombra dall'altra
    box = pygame.Rect(0, 0, 0, 0)
    pts = [p0 + n * r0, p0 - n * r0, p1 + n * r1, p1 - n * r1]
    box.x = int(min(q.x for q in pts)) - 2
    box.y = int(min(q.y for q in pts)) - 2
    box.w = int(max(q.x for q in pts)) - box.x + 4
    box.h = int(max(q.y for q in pts)) - box.y + 4
    box = box.clip(sc.get_rect())
    if box.w <= 0 or box.h <= 0:
        return
    velo = pygame.Surface(box.size, pygame.SRCALPHA)
    o = Vector2(box.x, box.y)
    q = [(int(round(x)), int(round(y))) for x, y in
         (p0 + n * (r0 * 0.10) - o, p1 + n * (r1 * 0.10) - o,
          p1 + n * (r1 * 0.58) - o, p0 + n * (r0 * 0.58) - o)]
    gfxdraw.filled_polygon(velo, q, (255, 255, 255, 44))
    q = [(int(round(x)), int(round(y))) for x, y in
         (p0 - n * (r0 * 0.42) - o, p1 - n * (r1 * 0.42) - o,
          p1 - n * r1 - o, p0 - n * r0 - o)]
    gfxdraw.filled_polygon(velo, q, (0, 0, 0, 70))
    sc.blit(velo, box.topleft)


# Le stecche fra cui si sceglie. Ognuna e' fatta di tratti, dal cuoio al
# calcio, con la frazione di lunghezza dove comincia e dove finisce. Il
# primo tratto e' sempre il cuoio e l'ultimo il fondello.
def fai_stecca(nome, fusto, giunto, davanti, manico, calcio, punte=None,
               cuoio=(58, 108, 168), anelli=None, strisce=None,
               fondello=(28, 26, 26)):
    """Una stecca montata come quelle vere: cuoio, ghiera, fusto fino
    alla giunzione, il legno davanti, il manico da impugnare, il calcio e
    il fondello di gomma. Anelli e strisce si aggiungono sopra."""
    t = [(0.000, 0.012, cuoio), (0.012, 0.032, (242, 240, 234)),
         (0.032, 0.500, fusto), (0.500, 0.518, giunto),
         (0.518, 0.720, davanti), (0.720, 0.905, manico),
         (0.905, 0.985, calcio), (0.985, 1.000, fondello)]
    for a, b, c in (strisce or ()):
        t.append((a, b, c))
    for x, c in (anelli or ()):
        t.append((x, x + 0.007, c))
    return (nome, t, punte)


ARGENTO = (206, 210, 216)
ORO = (214, 172, 74)
NERO = (22, 22, 24)
ACERO = (222, 188, 134)
ACERO_CHIARO = (234, 216, 180)

def _strisce(da, a, n, colore, largo=0.010):
    """n strisce uguali fra da e a."""
    passo = (a - da) / float(n)
    return [(da + k * passo, da + k * passo + largo, colore)
            for k in range(n)]


BIANCO = (246, 244, 238)
# ---------------------------------------------------------------------------
# Le 55 stecche, in ordine di come si sbloccano: prima i legni semplici,
# poi i legni lavorati, le laccate, la linea in carbonio, i metalli e in
# fondo le stecche da leggenda. Ogni tratto puo' avere il suo materiale
# (legno, lino, pelle, lacca, madreperla, radica, carbonio, forgiato,
# metallo, scacchi) e sopra ci vanno le decorazioni.
# ---------------------------------------------------------------------------
L_ACERO = (222, 188, 134)
L_FRASSINO = (230, 212, 172)
L_CILIEGIO = (168, 92, 58)
L_NOCE = (102, 70, 46)
L_ROVERE = (192, 152, 98)
L_BETULLA = (238, 222, 190)
L_MOGANO = (122, 52, 36)
L_PALISSANDRO = (86, 36, 30)
L_EBANO = (30, 26, 24)
L_ZEBRANO = (200, 164, 104)
L_WENGE = (70, 50, 36)
L_ULIVO = (202, 178, 124)
L_PADOUK = (172, 62, 42)
L_SERPENTE = (150, 82, 42)
L_RADICA = (172, 112, 62)
L_COCOBOLO = (150, 72, 42)
AVORIO = (238, 228, 206)
OTTONE = (196, 160, 80)
LINO_NERO = (30, 30, 32)
CARBONIO = (36, 36, 40)
CUOIO_BLU = (58, 108, 168)


def nuova_stecca(nome, fusto, giunto, davanti, manico, calcio,
                 mat=("legno", "legno", "lino", "legno"), cuoio=CUOIO_BLU,
                 anelli=(), punte=None, deco=(), fondello=(28, 26, 26)):
    """Una stecca come quelle vere, con il materiale di ogni pezzo:
    mat = (fusto, davanti, manico, calcio)."""
    mf, md, mm, mc = mat
    t = [(0.000, 0.012, cuoio), (0.012, 0.032, (242, 240, 234)),
         (0.032, 0.500, fusto, mf), (0.500, 0.518, giunto),
         (0.518, 0.720, davanti, md), (0.720, 0.905, manico, mm),
         (0.905, 0.985, calcio, mc), (0.985, 1.000, fondello)]
    for x, c in anelli:
        t.append((x, x + 0.007, c))
    return (nome, t, punte, tuple(deco))


def _righe(da, a, n, colore, largo=0.010):
    """n strisce dritte uguali fra da e a."""
    passo = (a - da) / float(n)
    return ("strisce", [(da + k * passo, da + k * passo + largo)
                        for k in range(n)], colore)


# (chiave, en, it, fr, es)
NOMI_STECCHE_55 = (
    ("sk_acero", "Maple", "Acero", "Erable", "Arce"),
    ("sk_frassino", "Ash", "Frassino", "Frene", "Fresno"),
    ("sk_ciliegio", "Cherry", "Ciliegio", "Merisier", "Cerezo"),
    ("sk_noce", "Walnut", "Noce", "Noyer", "Nogal"),
    ("sk_rovere", "Oak", "Rovere", "Chene", "Roble"),
    ("sk_betulla", "Birch", "Betulla", "Bouleau", "Abedul"),
    ("sk_mogano", "Mahogany", "Mogano", "Acajou", "Caoba"),
    ("sk_palissandro", "Rosewood", "Palissandro", "Palissandre",
     "Palisandro"),
    ("sk_ebano", "Ebony", "Ebano", "Ebene", "Ebano"),
    ("sk_zebrano", "Zebrawood", "Zebrano", "Zebrano", "Cebrano"),
    ("sk_occhio", "Bird's-eye", "Occhio di pernice", "Oeil d'oiseau",
     "Ojo de perdiz"),
    ("sk_wenge", "Wenge", "Wenge", "Wenge", "Wengue"),
    ("sk_ulivo", "Olive", "Ulivo", "Olivier", "Olivo"),
    ("sk_padouk", "Padauk", "Padouk", "Padouk", "Padauk"),
    ("sk_serpente", "Snakewood", "Legno serpente", "Amourette",
     "Palo serpiente"),
    ("sk_radica", "Burl", "Radica", "Loupe", "Raiz"),
    ("sk_cocobolo", "Cocobolo", "Cocobolo", "Cocobolo", "Cocobolo"),
    ("sk_vintage", "Vintage", "Vintage", "Vintage", "Vintage"),
    ("sk_spirale", "Spiral", "Spirale", "Spirale", "Espiral"),
    ("sk_intarsio", "Marquetry", "Intarsio", "Marqueterie", "Marqueteria"),
    ("sk_pianoforte", "Piano Black", "Nero pianoforte", "Noir piano",
     "Negro piano"),
    ("sk_neve", "Snow", "Neve", "Neige", "Nieve"),
    ("sk_corsa", "Racing", "Corsa", "Course", "Carreras"),
    ("sk_marina", "Navy", "Marina", "Marine", "Marino"),
    ("sk_smeraldo", "Emerald", "Smeraldo", "Emeraude", "Esmeralda"),
    ("sk_perla", "Pearl", "Perla", "Perle", "Perla"),
    ("sk_abalone", "Abalone", "Abalone", "Abalone", "Abulon"),
    ("sk_avorio", "Ivory", "Avorio", "Ivoire", "Marfil"),
    ("sk_tigre", "Tiger", "Tigre", "Tigre", "Tigre"),
    ("sk_scacchi", "Checker", "Scacchi", "Damier", "Ajedrez"),
    ("sk_carbonio", "Carbon", "Carbonio", "Carbone", "Carbono"),
    ("sk_carb_rosso", "Carbon Red", "Carbonio rosso", "Carbone rouge",
     "Carbono rojo"),
    ("sk_carb_blu", "Carbon Blue", "Carbonio blu", "Carbone bleu",
     "Carbono azul"),
    ("sk_carb_oro", "Carbon Gold", "Carbonio oro", "Carbone or",
     "Carbono oro"),
    ("sk_carb_neon", "Carbon Neon", "Carbonio neon", "Carbone neon",
     "Carbono neon"),
    ("sk_carb_bianco", "White Carbon", "Carbonio bianco", "Carbone blanc",
     "Carbono blanco"),
    ("sk_forgiato", "Forged Carbon", "Carbonio forgiato", "Carbone forge",
     "Carbono forjado"),
    ("sk_kevlar", "Kevlar", "Kevlar", "Kevlar", "Kevlar"),
    ("sk_carb_spirale", "Carbon Spiral", "Carbonio spirale",
     "Carbone spirale", "Carbono espiral"),
    ("sk_ibrida", "Hybrid", "Ibrida", "Hybride", "Hibrida"),
    ("sk_alluminio", "Aluminium", "Alluminio", "Aluminium", "Aluminio"),
    ("sk_acciaio", "Steel", "Acciaio", "Acier", "Acero"),
    ("sk_bronzo", "Bronze", "Bronzo", "Bronze", "Bronce"),
    ("sk_rame", "Copper", "Rame", "Cuivre", "Cobre"),
    ("sk_titanio", "Titanium", "Titanio", "Titane", "Titanio"),
    ("sk_cromo", "Chrome", "Cromo", "Chrome", "Cromo"),
    ("sk_anod_blu", "Anodized Blue", "Blu anodizzato", "Bleu anodise",
     "Azul anodizado"),
    ("sk_anod_viola", "Anodized Violet", "Viola anodizzato",
     "Violet anodise", "Violeta anodizado"),
    ("sk_argento", "Engraved Silver", "Argento inciso", "Argent grave",
     "Plata grabada"),
    ("sk_oro", "Gold", "Oro", "Or", "Oro"),
    ("sk_ossidiana", "Obsidian", "Ossidiana", "Obsidienne", "Obsidiana"),
    ("sk_zaffiro", "Sapphire", "Zaffiro", "Saphir", "Zafiro"),
    ("sk_rubino", "Ruby", "Rubino", "Rubis", "Rubi"),
    ("sk_platino", "Platinum", "Platino", "Platine", "Platino"),
    ("sk_leggenda", "Legend", "Leggenda", "Legende", "Leyenda"),
)

_S = nuova_stecca
_LL = ("legno", "legno", "lino", "legno")       # legni con manico in lino
_LP = ("legno", "legno", "pelle", "legno")      # legni con manico in pelle
_LACCA = ("legno", "lacca", "lino", "lacca")
_LACCA_P = ("legno", "lacca", "pelle", "lacca")
_CARB = ("carbonio", "carbonio", "lino", "carbonio")
_CARB_P = ("carbonio", "carbonio", "pelle", "carbonio")
_MET = ("legno", "metallo", "lino", "metallo")
_MET_C = ("carbonio", "metallo", "pelle", "metallo")
TIGRE = (232, 132, 30)

STECCHE = (
    # --- 1-10: legni semplici ---
    _S("sk_acero", L_ACERO, (240, 236, 226), (206, 166, 106),
       (206, 166, 106), (156, 104, 58), mat=("legno",) * 4),
    _S("sk_frassino", L_FRASSINO, NERO, L_FRASSINO, LINO_NERO, L_FRASSINO),
    _S("sk_ciliegio", L_ACERO, AVORIO, L_CILIEGIO, (70, 30, 24), L_CILIEGIO,
       anelli=((0.718, NERO), (0.903, NERO))),
    _S("sk_noce", L_ACERO, AVORIO, L_NOCE, (40, 30, 24), L_NOCE),
    _S("sk_rovere", L_ACERO, (240, 236, 226), L_ROVERE, (110, 70, 40),
       L_ROVERE, mat=_LP, deco=(_righe(0.935, 0.945, 1, L_NOCE, 0.012),)),
    _S("sk_betulla", L_ACERO, AVORIO, L_BETULLA, LINO_NERO, L_NOCE,
       punte=(L_NOCE, AVORIO, 0.56, 0.72)),
    _S("sk_mogano", L_ACERO, AVORIO, L_MOGANO, LINO_NERO, L_MOGANO,
       deco=(_righe(0.60, 0.64, 2, L_ACERO, 0.006),
             _righe(0.93, 0.95, 2, L_ACERO, 0.005))),
    _S("sk_palissandro", L_ACERO, AVORIO, L_ACERO, LINO_NERO, L_PALISSANDRO,
       punte=(L_PALISSANDRO, AVORIO, 0.55, 0.72)),
    _S("sk_ebano", L_ACERO, AVORIO, L_ACERO, L_EBANO, L_EBANO,
       punte=(L_EBANO, AVORIO, 0.54, 0.72),
       anelli=((0.718, AVORIO), (0.903, AVORIO))),
    _S("sk_zebrano", L_ACERO, NERO, L_ZEBRANO, LINO_NERO, L_ZEBRANO,
       deco=(_righe(0.525, 0.715, 11, L_NOCE, 0.006),
             _righe(0.91, 0.98, 4, L_NOCE, 0.006))),

    # --- 11-20: legni lavorati, intarsi ---
    _S("sk_occhio", L_ACERO, L_EBANO, L_FRASSINO, LINO_NERO, L_EBANO,
       mat=("legno", "radica", "lino", "legno"),
       anelli=((0.718, L_EBANO),)),
    _S("sk_wenge", L_ACERO, AVORIO, L_WENGE, (46, 34, 26), L_WENGE,
       punte=(L_ACERO, NERO, 0.55, 0.72),
       deco=(("rombi", (0.945,), L_ACERO, 0.018),)),
    _S("sk_ulivo", L_ACERO, OTTONE, L_ULIVO, (44, 52, 32), L_ULIVO,
       anelli=((0.718, OTTONE), (0.903, OTTONE))),
    _S("sk_padouk", L_ACERO, AVORIO, L_PADOUK, LINO_NERO, L_PADOUK,
       punte=(L_EBANO, AVORIO, 0.55, 0.72),
       anelli=((0.718, AVORIO), (0.903, AVORIO))),
    _S("sk_serpente", L_ACERO, NERO, L_SERPENTE, LINO_NERO, L_SERPENTE,
       mat=("legno", "radica", "lino", "radica"),
       anelli=((0.718, NERO), (0.903, NERO))),
    _S("sk_radica", L_ACERO, ORO, L_RADICA, (104, 64, 36), L_RADICA,
       mat=("legno", "radica", "pelle", "radica"),
       anelli=((0.518, ORO), (0.718, ORO), (0.903, ORO))),
    _S("sk_cocobolo", L_ACERO, OTTONE, L_COCOBOLO, LINO_NERO, L_COCOBOLO,
       punte=(NERO, OTTONE, 0.55, 0.72),
       anelli=((0.708, OTTONE), (0.718, OTTONE), (0.903, OTTONE),
               (0.913, OTTONE))),
    _S("sk_vintage", L_ACERO, AVORIO, L_ACERO, LINO_NERO, L_PALISSANDRO,
       punte=(L_EBANO, (40, 120, 70), 0.54, 0.72),
       deco=(("punti", (0.535, 0.555), AVORIO),),
       anelli=((0.718, AVORIO), (0.903, AVORIO))),
    _S("sk_spirale", L_ACERO, NERO, L_ACERO, LINO_NERO, L_NOCE,
       deco=(("spirale", 0.522, 0.716, 6, L_NOCE, 0.014),
             ("spirale", 0.908, 0.982, 3, L_ACERO, 0.008))),
    _S("sk_intarsio", L_ACERO, AVORIO, L_EBANO, LINO_NERO, L_EBANO,
       deco=(("rombi", (0.56, 0.62, 0.68), AVORIO, 0.020),
             ("punti", (0.59, 0.65), AVORIO),
             ("rombi", (0.945,), AVORIO, 0.020)),
       anelli=((0.718, AVORIO), (0.903, AVORIO))),

    # --- 21-30: laccate e finiture speciali ---
    _S("sk_pianoforte", L_ACERO, ARGENTO, NERO, NERO, NERO, mat=_LACCA_P,
       anelli=((0.718, ARGENTO), (0.903, ARGENTO))),
    _S("sk_neve", L_ACERO, ARGENTO, BIANCO, LINO_NERO, BIANCO, mat=_LACCA,
       anelli=((0.718, ARGENTO), (0.903, ARGENTO))),
    _S("sk_corsa", L_ACERO, BIANCO, (200, 24, 30), LINO_NERO, (200, 24, 30),
       mat=_LACCA, cuoio=(40, 40, 44),
       deco=(_righe(0.60, 0.62, 2, BIANCO, 0.006),
             _righe(0.93, 0.95, 2, BIANCO, 0.006))),
    _S("sk_marina", L_ACERO, ARGENTO, (24, 40, 92), (18, 26, 56),
       (24, 40, 92), mat=_LACCA, punte=(ARGENTO, BIANCO, 0.55, 0.72),
       anelli=((0.903, ARGENTO),)),
    _S("sk_smeraldo", L_ACERO, ORO, (16, 100, 60), NERO, (16, 100, 60),
       mat=_LACCA_P, punte=(ORO, NERO, 0.55, 0.72),
       anelli=((0.718, ORO), (0.903, ORO))),
    _S("sk_perla", L_ACERO, ARGENTO, (236, 232, 240), (180, 178, 190),
       (236, 232, 240), mat=("legno", "madreperla", "lino", "madreperla"),
       anelli=((0.718, ARGENTO), (0.903, ARGENTO))),
    _S("sk_abalone", L_ACERO, ARGENTO, (40, 84, 96), LINO_NERO, (40, 84, 96),
       mat=("legno", "madreperla", "lino", "madreperla"),
       anelli=((0.718, ARGENTO), (0.903, ARGENTO))),
    _S("sk_avorio", L_ACERO, ORO, AVORIO, (92, 60, 40), AVORIO, mat=_LACCA_P,
       punte=(L_NOCE, ORO, 0.55, 0.72),
       anelli=((0.718, ORO), (0.903, ORO))),
    _S("sk_tigre", L_ACERO, NERO, TIGRE, LINO_NERO, TIGRE, mat=_LACCA,
       deco=(("spirale", 0.524, 0.714, 7, NERO, 0.010),
             ("spirale", 0.908, 0.980, 3, NERO, 0.008))),
    _S("sk_scacchi", L_ACERO, NERO, BIANCO, LINO_NERO, BIANCO,
       mat=("legno", "scacchi", "lino", "scacchi")),

    # --- 31-40: la linea in carbonio ---
    _S("sk_carbonio", CARBONIO, ARGENTO, CARBONIO, NERO, CARBONIO,
       mat=_CARB_P, cuoio=(40, 40, 44),
       anelli=((0.718, ARGENTO), (0.903, ARGENTO))),
    _S("sk_carb_rosso", CARBONIO, (200, 30, 36), CARBONIO, (110, 18, 22),
       CARBONIO, mat=_CARB, cuoio=(40, 40, 44),
       punte=((200, 30, 36), NERO, 0.55, 0.72),
       anelli=((0.903, (200, 30, 36)),)),
    _S("sk_carb_blu", CARBONIO, (40, 110, 220), CARBONIO, (20, 44, 110),
       CARBONIO, mat=_CARB, cuoio=(40, 40, 44),
       deco=(("spirale", 0.524, 0.714, 5, (40, 110, 220), 0.005),),
       anelli=((0.718, (40, 110, 220)), (0.903, (40, 110, 220)))),
    _S("sk_carb_oro", CARBONIO, ORO, CARBONIO, NERO, CARBONIO, mat=_CARB_P,
       cuoio=(40, 40, 44), punte=(ORO, NERO, 0.55, 0.72),
       anelli=((0.718, ORO), (0.903, ORO))),
    _S("sk_carb_neon", CARBONIO, (60, 255, 140), CARBONIO, LINO_NERO,
       CARBONIO, mat=_CARB, cuoio=(40, 40, 44),
       deco=(_righe(0.56, 0.70, 3, (60, 255, 140), 0.008),
             _righe(0.92, 0.97, 2, (60, 255, 140), 0.007))),
    _S("sk_carb_bianco", (222, 224, 228), NERO, (222, 224, 228), LINO_NERO,
       (222, 224, 228), mat=_CARB, cuoio=(40, 40, 44),
       anelli=((0.718, NERO), (0.903, NERO))),
    _S("sk_forgiato", CARBONIO, ARGENTO, (46, 46, 50), NERO, (46, 46, 50),
       mat=("carbonio", "forgiato", "pelle", "forgiato"),
       cuoio=(40, 40, 44), anelli=((0.718, ARGENTO), (0.903, ARGENTO))),
    _S("sk_kevlar", CARBONIO, NERO, (206, 164, 40), LINO_NERO,
       (206, 164, 40), mat=_CARB, cuoio=(40, 40, 44),
       anelli=((0.718, NERO), (0.903, NERO))),
    _S("sk_carb_spirale", CARBONIO, ARGENTO, CARBONIO, LINO_NERO, CARBONIO,
       mat=_CARB, cuoio=(40, 40, 44),
       deco=(("spirale", 0.522, 0.716, 6, ARGENTO, 0.006),
             ("spirale", 0.908, 0.982, 3, ARGENTO, 0.005))),
    _S("sk_ibrida", CARBONIO, ARGENTO, L_ACERO, LINO_NERO, CARBONIO,
       mat=("carbonio", "legno", "lino", "carbonio"), cuoio=(40, 40, 44),
       punte=((48, 48, 54), ARGENTO, 0.54, 0.72)),

    # --- 41-50: i metalli ---
    _S("sk_alluminio", L_ACERO, NERO, (192, 196, 202), LINO_NERO,
       (192, 196, 202), mat=_MET),
    _S("sk_acciaio", L_ACERO, NERO, (142, 148, 156), NERO, (142, 148, 156),
       mat=("legno", "metallo", "pelle", "metallo"),
       deco=(_righe(0.60, 0.64, 2, (60, 64, 70), 0.006),)),
    _S("sk_bronzo", L_ACERO, (60, 40, 28), (176, 120, 70), (60, 40, 28),
       (176, 120, 70), mat=_MET,
       anelli=((0.718, (60, 40, 28)), (0.903, (60, 40, 28)))),
    _S("sk_rame", L_ACERO, (60, 40, 32), (202, 112, 62), LINO_NERO,
       (202, 112, 62), mat=_MET, punte=((70, 40, 30), (240, 170, 120),
                                        0.55, 0.72)),
    _S("sk_titanio", CARBONIO, (60, 110, 200), (122, 126, 134), NERO,
       (122, 126, 134), mat=_MET_C, cuoio=(40, 40, 44),
       anelli=((0.718, (60, 110, 200)), (0.903, (60, 110, 200)))),
    _S("sk_cromo", CARBONIO, NERO, (222, 226, 232), LINO_NERO,
       (222, 226, 232), mat=("carbonio", "metallo", "lino", "metallo"),
       cuoio=(40, 40, 44),
       deco=(_righe(0.61, 0.63, 2, NERO, 0.005),
             _righe(0.93, 0.95, 2, NERO, 0.005))),
    _S("sk_anod_blu", CARBONIO, ARGENTO, (40, 92, 196), NERO,
       (40, 92, 196), mat=_MET_C, cuoio=(40, 40, 44),
       anelli=((0.718, ARGENTO), (0.903, ARGENTO))),
    _S("sk_anod_viola", CARBONIO, ARGENTO, (132, 60, 192), NERO,
       (132, 60, 192), mat=_MET_C, cuoio=(40, 40, 44),
       anelli=((0.718, ARGENTO), (0.903, ARGENTO))),
    _S("sk_argento", CARBONIO, NERO, (214, 218, 224), NERO, (214, 218, 224),
       mat=_MET_C, cuoio=(40, 40, 44),
       deco=(("rombi", (0.56, 0.62, 0.68), (70, 74, 80), 0.016),
             ("punti", (0.59, 0.65), (70, 74, 80)),
             ("rombi", (0.945,), (70, 74, 80), 0.016))),
    _S("sk_oro", CARBONIO, NERO, ORO, NERO, ORO, mat=_MET_C,
       cuoio=(40, 40, 44),
       deco=(("rombi", (0.59, 0.65), NERO, 0.018),
             ("rombi", (0.945,), NERO, 0.018))),

    # --- 51-55: le leggende ---
    _S("sk_ossidiana", CARBONIO, (150, 70, 210), (14, 14, 18), NERO,
       (14, 14, 18), mat=("carbonio", "lacca", "pelle", "lacca"),
       cuoio=(40, 40, 44), punte=((150, 70, 210), (60, 60, 70), 0.55, 0.72),
       deco=(("rombi", (0.945,), (150, 70, 210), 0.018),),
       anelli=((0.718, (150, 70, 210)), (0.903, (150, 70, 210)))),
    _S("sk_zaffiro", CARBONIO, ARGENTO, (22, 46, 140), (14, 22, 60),
       (22, 46, 140), mat=("carbonio", "lacca", "pelle", "lacca"),
       cuoio=(40, 40, 44), punte=(ARGENTO, BIANCO, 0.55, 0.72),
       deco=(("rombi", (0.535, 0.945), BIANCO, 0.014),),
       anelli=((0.718, ARGENTO), (0.903, ARGENTO))),
    _S("sk_rubino", CARBONIO, ORO, (150, 16, 30), NERO, (150, 16, 30),
       mat=("carbonio", "lacca", "pelle", "lacca"), cuoio=(40, 40, 44),
       punte=(ORO, NERO, 0.55, 0.72),
       deco=(("rombi", (0.535, 0.945), ORO, 0.014),),
       anelli=((0.718, ORO), (0.903, ORO))),
    _S("sk_platino", CARBONIO, NERO, (228, 230, 234), NERO, (228, 230, 234),
       mat=_MET_C, cuoio=(40, 40, 44), punte=(NERO, (228, 230, 234), 0.55,
                                               0.72),
       deco=(("rombi", (0.945,), NERO, 0.016),),
       anelli=((0.518, NERO), (0.718, NERO), (0.903, NERO))),
    _S("sk_leggenda", CARBONIO, ORO, CARBONIO, NERO, ORO,
       mat=("carbonio", "carbonio", "pelle", "metallo"), cuoio=(40, 40, 44),
       punte=(ORO, NERO, 0.54, 0.72),
       deco=(("rombi", (0.53,), BIANCO, 0.012),
             ("punti", (0.60, 0.64, 0.68), BIANCO),
             ("rombi", (0.945,), NERO, 0.016)),
       anelli=((0.718, ORO), (0.728, ORO), (0.893, ORO), (0.903, ORO))),
)


STECCA_ORA = [0]        # quale stecca in questa partita, quando e' a caso
STECCA_AVV = [1]        # e quella dell'avversario: sempre un'altra


def _doti_stecche():
    """Le tre doti di ogni stecca, in percentuale: mira (quanto e' lunga
    la riga della palla colpita), potenza e effetto. Salgono piano dalla
    prima all'ultima; ogni stecca ha il suo carattere: una tira piu'
    lungo ma meno forte, una e' piu' forte ma con meno effetto..."""
    doti = []
    ultima = max(1, len(STECCHE) - 1)
    for i in range(len(STECCHE)):
        t = i / float(ultima)
        mira = 10 + 90 * t
        pot = 58 + 52 * t
        eff = 90 + 28 * t
        carattere = i % 4 if 0 < i < ultima else 0
        if carattere == 1:          # mira lunga, un filo meno forte
            mira, pot = mira + 7, pot - 2
        elif carattere == 2:        # forte, meno effetto
            pot, eff = pot + 3, eff - 4
        elif carattere == 3:        # tanto effetto, mira piu' corta
            eff, mira = eff + 5, mira - 5
        doti.append((int(round(mira)), int(round(pot)), int(round(eff))))
    # l'ultima, la leggenda, resta la migliore in tutto
    top = doti[-1]
    return [tuple(min(v, top[k]) for k, v in enumerate(d)) for d in doti]


DOTI = _doti_stecche()


def fascio(sc, da, verso, lung, colore, largo, sfuma=0.8, opaco=1.0):
    """La riga della palla colpita: un fascio leggero che parte pieno e
    sfuma fino a sparire."""
    if lung < 2:
        return
    largo *= 0.7                # delicato: stretto e leggero
    fine = da + verso * lung
    n = Vector2(-verso.y, verso.x)
    x0 = int(min(da.x, fine.x) - largo - 2)
    y0 = int(min(da.y, fine.y) - largo - 2)
    x1 = int(max(da.x, fine.x) + largo + 2)
    y1 = int(max(da.y, fine.y) + largo + 2)
    velo = pygame.Surface((max(1, x1 - x0), max(1, y1 - y0)),
                          pygame.SRCALPHA)
    o = Vector2(x0, y0)
    pezzi = max(8, min(60, int(lung / 8)))
    for strato, (mezzo, forza) in enumerate(((largo, 0.30),
                                             (largo * 0.45, 0.85))):
        for k in range(pezzi):
            f0, f1 = k / float(pezzi), (k + 1) / float(pezzi)
            a = int(135 * forza * opaco * (1.0 - sfuma * f0) ** 1.3)
            if a <= 0:
                continue
            # si stringe un poco andando avanti
            m0 = mezzo * (1.0 - 0.45 * sfuma * f0)
            m1 = mezzo * (1.0 - 0.45 * sfuma * f1)
            p0 = da + verso * (lung * f0) - o
            p1 = da + verso * (lung * f1) - o
            q = [p0 + n * m0, p1 + n * m1, p1 - n * m1, p0 - n * m0]
            q = [(int(round(v.x)), int(round(v.y))) for v in q]
            pygame.draw.polygon(velo, colore[:3] + (a,), q)
    sc.blit(velo, (x0, y0))


def stecche_mie():
    """Le stecche che hai: la prima c'e' sempre, le altre si comprano."""
    mie = set([0])
    for i in CFG.get("stecche_mie") or []:
        try:
            if 0 <= int(i) < len(STECCHE):
                mie.add(int(i))
        except (TypeError, ValueError):
            pass
    return sorted(mie)


def stecche_sbloccate():
    """Quante stecche hai."""
    return len(stecche_mie())


# I prezzi delle stecche: la prima e' tua, poi salgono a gruppi di dieci.
# Fra un punto e l'altro si va dritti, arrotondando a cinquanta.
_PREZZI_PUNTI = ((1, 60), (9, 170), (10, 190), (19, 375), (20, 410),
                 (29, 655), (30, 710), (39, 1030), (40, 1125),
                 (49, 1595), (50, 1875), (54, 3750))


def prezzo_stecca(i):
    if i <= 0:
        return 0
    for (a, pa), (b, pb) in zip(_PREZZI_PUNTI, _PREZZI_PUNTI[1:]):
        if a <= i <= b:
            v = pa + (pb - pa) * (i - a) / float(b - a)
            return int(round(v / 10.0)) * 10
    return _PREZZI_PUNTI[-1][1]


# I gessetti: nome, quanti usi dura un cubetto, prezzo, colore. Il primo,
# il blu col cartoncino verde, e' quello di sempre.
GESSI = (("blu", 10, 20, (52, 108, 206)),
         ("grigio", 11, 28, (168, 172, 178)),
         ("rosso", 12, 36, (200, 44, 48)),
         ("verde", 13, 45, (36, 150, 84)),
         ("nero", 14, 55, (46, 46, 52)),
         ("bianco", 15, 65, (236, 234, 228)),
         ("giallo", 16, 75, (236, 196, 40)),
         ("viola", 17, 85, (132, 64, 190)),
         ("arancio", 18, 95, (236, 124, 32)),
         ("oro", 20, 110, (214, 172, 70)))


def gessi_miei():
    """I gessetti fra cui scegliere: quelli di cui hai cubetti, anche solo
    un cubetto gia' aperto o messo da parte."""
    scorta = CFG.get("gessi") or {}
    avanzi = CFG.get("avanzi") or {}
    aperti = set(CFG.get(k_t) for k_c, k_t in CUBO_K
                 if int(CFG.get(k_c, 0)) > 0)
    return [g[0] for g in GESSI
            if int(scorta.get(g[0], 0)) > 0 or int(avanzi.get(g[0], 0)) > 0
            or g[0] in aperti]


def nome_gesso_scelto():
    miei = gessi_miei()
    if not miei:
        return T("ch_none")
    t = CFG.get("gesso_tipo", "blu")
    if t not in miei:
        t = miei[0]
        CFG["gesso_tipo"] = t
    n = int((CFG.get("gessi") or {}).get(t, 0))
    return "%s (%d)" % (T("ch_" + t), n)


def gira_gesso(passo):
    miei = gessi_miei()
    if not miei:
        return
    t = CFG.get("gesso_tipo", "blu")
    k = miei.index(t) if t in miei else 0
    CFG["gesso_tipo"] = miei[(k + passo) % len(miei)]


def gira_stecca_cfg(passo):
    giro = [-1] + stecche_mie()
    ora = CFG.get("stecca", 0)
    k = giro.index(ora) if ora in giro else 0
    CFG["stecca"] = giro[(k + passo) % len(giro)]


def nome_stecca_cfg():
    i = CFG.get("stecca", 0)
    if i not in stecche_mie():
        return T("random")
    return "%d. %s" % (i + 1, T(STECCHE[i][0]))


def gesso_dati(tipo):
    for g in GESSI:
        if g[0] == tipo:
            return g
    return GESSI[0]


def soldi(n=None):
    """Quanti soldi hai, o ne aggiunge (anche in meno)."""
    if n:
        CFG["soldi"] = max(0, int(CFG.get("soldi", 0)) + int(n))
    return int(CFG.get("soldi", 0))


def dollari(n):
    return "$%s" % "{:,}".format(int(n))


def doti_di(chi):
    """Le doti della stecca di chi tira."""
    st = stecca_di(chi)
    for i, q in enumerate(STECCHE):
        if q is st:
            return DOTI[i]
    return DOTI[0]


# Il gesso: ogni tre tiri la stecca ne perde un po' e le righe di mira si
# accorciano del 2 per cento, fino a perdere al massimo il 10. Col tasto
# del gesso torna piena.
GESSO = [1.0, 1.0]
GESSO_TIRI = [0, 0]
GESSO_OGNI = 1          # a ogni tiro...
GESSO_CALO = 0.0067     # ...un filo: dopo 15 tiri si e' perso il 10%
GESSO_MIN = 0.90


def consuma_gesso(chi):
    GESSO_TIRI[chi] += 1
    if GESSO_TIRI[chi] % GESSO_OGNI == 0:
        GESSO[chi] = max(GESSO_MIN, round(GESSO[chi] - GESSO_CALO, 4))


# Il cubetto: ogni volta che dai il gesso ne consumi un uso. Finito il
# cubetto se ne apre un altro dei tuoi; se non ne hai piu', niente gesso
# finche' non li ricompri al negozio. In due si usa la stessa scorta.
GESSO_QUANDO = [0, 0]   # quando si e' dato il gesso, per l'animazione
GESSO_PNG = {}
# Ognuno ha il suo cubetto aperto, come il serbatoio di ogni macchina; i
# cubetti nuovi escono tutti dalla stessa scorta, quella del giocatore 1.
CUBO_K = (("cubo", "cubo_tipo"), ("cubo2", "cubo2_tipo"))
# Il computer il gesso lo fa per finta: un cubetto a partita, del colore
# del suo livello, e lo da' tanto piu' spesso quanto piu' e' bravo.
CPU_ORA = [None]        # il livello del computer in questa partita
# In due sullo stesso computer si gioca alla buona: gessetto blu per
# tutti e due e non finisce mai.
GESSO_INF = [False]
CPU_CUBO = [0]


def gesso_cpu_tipo(livello):
    scala = (0, 1, 3, 5, 7, 9)
    k = scala[max(0, min(len(scala) - 1, int(livello)))]
    return GESSI[min(len(GESSI) - 1, k)][0]


def gesso_pronto(chi=0):
    """C'e' un cubetto aperto, o se ne puo' aprire uno."""
    if int(CFG.get(CUBO_K[chi][0], 0)) > 0:
        return True
    return any(int(v) > 0 for v in (CFG.get("gessi") or {}).values())


def apri_cubetto(chi=0):
    """Si apre un cubetto nuovo, ma solo del gessetto scelto per la
    partita: finiti quelli, niente gesso fino alla partita dopo."""
    gessi = CFG.setdefault("gessi", {})
    t = CFG.get("gesso_tipo", "blu")
    if int(gessi.get(t, 0)) > 0:
        gessi[t] = int(gessi[t]) - 1
        CFG[CUBO_K[chi][0]] = gesso_dati(t)[1]
        CFG[CUBO_K[chi][1]] = t
        return True
    return False


def prepara_gessi(due):
    """A inizio partita ognuno prende in mano il gessetto scelto: se aveva
    aperto un cubetto di un altro colore lo mette da parte (non si butta),
    e se ne aveva uno mezzo usato del colore scelto lo riprende."""
    t = CFG.get("gesso_tipo", "blu")
    avanzi = CFG.setdefault("avanzi", {})
    for chi in ((0, 1) if due else (0,)):
        k_cubo, k_tipo = CUBO_K[chi]
        aperto, tipo = int(CFG.get(k_cubo, 0)), CFG.get(k_tipo, t)
        if aperto > 0 and tipo == t:
            continue
        if aperto > 0:
            avanzi[tipo] = int(avanzi.get(tipo, 0)) + aperto
        resto = int(avanzi.pop(t, 0))
        CFG[k_cubo] = resto
        CFG[k_tipo] = t
    for chi in ((0, 1) if due else (0,)):
        if int(CFG.get(CUBO_K[chi][0], 0)) <= 0:
            apri_cubetto(chi)       # si parte col cubetto intero, al 100%
    salva_config()


def gesso_del_computer():
    """Prima di tirare il computer guarda la sua stecca: se il gesso e'
    calato abbastanza, e il cubetto non e' finito, lo da'."""
    liv = CPU_ORA[0] or 0
    soglia = 0.92 + 0.012 * liv
    if GESSO[1] <= soglia + 1e-6 and CPU_CUBO[0] > 0:
        CPU_CUBO[0] -= 1
        GESSO[1] = 1.0
        GESSO_TIRI[1] = 0
        GESSO_QUANDO[1] = pygame.time.get_ticks()
        if SUONI.get("gesso"):
            suona_fx("gesso")


def metti_gesso(chi):
    """Il gesso sulla stecca: la riga torna piena e il cubetto cala. Se la
    riga e' gia' piena non si spreca niente."""
    if GESSO[chi] >= 0.999:
        return False
    if GESSO_INF[0]:
        GESSO[chi] = 1.0
        GESSO_TIRI[chi] = 0
        GESSO_QUANDO[chi] = pygame.time.get_ticks()
        if SUONI.get("gesso"):
            suona_fx("gesso")
        return True
    k = CUBO_K[chi][0]
    if int(CFG.get(k, 0)) <= 0 and not apri_cubetto(chi):
        return False
    CFG[k] = int(CFG[k]) - 1
    salva_config()
    GESSO[chi] = 1.0
    GESSO_TIRI[chi] = 0
    GESSO_QUANDO[chi] = pygame.time.get_ticks()
    if SUONI.get("gesso"):
        suona_fx("gesso")
    return True


def icona_gesso(lato, tipo="blu"):
    """Il PNG del gessetto, alla misura che serve: pool_chalk_<tipo>.png
    se c'e', se no quello di sempre."""
    chiave = (lato, tipo)
    if chiave not in GESSO_PNG:
        GESSO_PNG[chiave] = None
        for nome in ("pool_chalk_%s.png" % tipo, "pool_chalk.png"):
            try:
                im = pygame.image.load(os.path.join(GFX, nome))
            except (pygame.error, FileNotFoundError):
                continue
            GESSO_PNG[chiave] = pygame.transform.smoothscale(
                im.convert_alpha(), (lato, lato))
            break
    return GESSO_PNG[chiave]


def stecca_di(chi):
    """La stecca di chi tira: il giocatore uno ha la sua, l'altro una
    diversa, cosi' si vede subito chi ha in mano la stecca. In due sullo
    stesso computer si gioca alla buona: la stecca base per tutti e due."""
    if GESSO_INF[0]:
        return STECCHE[0]
    if chi == 1 and 0 <= STECCA_AVV[0] < len(STECCHE):
        return STECCHE[STECCA_AVV[0]]
    return stecca_scelta()


def stecca_avversario(nome):
    """La stecca di un avversario: ognuno ha la sua, sempre quella, scelta
    dal suo nome. Mai la base: sono giocatori veri."""
    somma = sum(ord(c) * (k + 1) for k, c in enumerate(nome or ""))
    return 1 + somma % (len(STECCHE) - 1)


def sorteggia_stecca_avv(tutte=True):
    """A ogni partita l'avversario pesca una stecca, mai la tua. Il
    computer puo' avere qualunque stecca; il secondo giocatore vero solo
    quelle gia' sbloccate."""
    mia = CFG.get("stecca", 0)
    if mia < 0:
        mia = STECCA_ORA[0]
    giro = list(range(len(STECCHE))) if tutte else stecche_mie()
    if tutte and NOMI[1] in AVVERSARI:
        k = stecca_avversario(NOMI[1])
        if k == mia:
            k = 1 + k % (len(STECCHE) - 1)
        STECCA_AVV[0] = k
        return
    sua = CFG.get("stecca2", -1)
    if not tutte and sua in giro:
        STECCA_AVV[0] = sua          # il giocatore 2 l'ha scelta lui
        return
    altre = [i for i in giro if i != mia] or [mia]
    if altre:
        STECCA_AVV[0] = random.choice(altre)


def stecca_scelta():
    i = CFG.get("stecca", 0)
    if i < 0:
        i = STECCA_ORA[0]
    if not 0 <= i < len(STECCHE):
        i = 0
    if i not in stecche_mie():
        i = stecche_mie()[-1]
    return STECCHE[i]


def sorteggia_tavolo():
    """Quando nelle impostazioni si e' lasciato "a caso", si tira a sorte
    a ogni partita: panno, legno e stecca. Non nel torneo, che il tavolo
    se lo porta da solo."""
    if STECCHE:
        STECCA_ORA[0] = random.choice(stecche_mie())
    i_panno = (random.randrange(len(PANNI)) if PANNI
               else 0) if CFG["panno"] < 0 else CFG["panno"]
    i_bordo = (random.randrange(len(BORDI)) if BORDI
               else 0) if CFG["bordo"] < 0 else CFG["bordo"]
    if not 0 <= i_panno < len(PANNI):
        i_panno = _quale(PANNI, TAVOLO_CASA[0])
    if not 0 <= i_bordo < len(BORDI):
        i_bordo = _quale(BORDI, TAVOLO_CASA[1])
    return i_panno, i_bordo

INGR = 4        # di quanto si disegna in grande prima di rimpicciolire


def anello(sc, col, centro, r, spess=1):
    """Un cerchio vuoto senza scalettatura: disegnato quattro volte piu'
    grande e poi rimpicciolito."""
    d = int(r * 2) + 4
    s = pygame.Surface((d * INGR, d * INGR), pygame.SRCALPHA)
    pygame.draw.circle(s, col, (d * INGR // 2, d * INGR // 2),
                       int(r * INGR), max(1, spess * INGR))
    s = pygame.transform.smoothscale(s, (d, d))
    sc.blit(s, s.get_rect(center=(int(centro[0]), int(centro[1]))))


def disegna_spin(sc, spin, x, y, r=19):
    d = (r + 2) * 2
    s = pygame.Surface((d * INGR, d * INGR), pygame.SRCALPHA)
    c = d * INGR // 2
    pygame.draw.circle(s, (244, 244, 240), (c, c), r * INGR)
    pygame.draw.circle(s, (90, 92, 100), (c, c), r * INGR, INGR)
    px = c + spin.x * r * 0.75 * INGR
    py = c - spin.y * r * 0.75 * INGR
    pygame.draw.circle(s, (200, 40, 40), (int(px), int(py)),
                       max(3, int(round(r * 3.0 / 13.0))) * INGR)
    s = pygame.transform.smoothscale(s, (d, d))
    sc.blit(s, s.get_rect(center=(x, y)))


def _sfuma(a, b, t):
    return tuple(int(a[k] + (b[k] - a[k]) * t) for k in range(3))


def colore_precisione(t):
    """Piena e' viola; calando va verso l'arancione e in fondo il rosso."""
    t = max(0.0, min(1.0, t))
    if t >= 0.5:
        return _sfuma((242, 144, 52), COL_DOTI[0], (t - 0.5) / 0.5)
    return _sfuma((222, 52, 52), (242, 144, 52), t / 0.5)


def barra_sottile(sc, x, y, w, h, val, col):
    """Una barra in piedi, sottile e pulita: il fondo scuro e sopra il
    pieno, arrotondati, senza cornice."""
    q = pygame.Surface((w * INGR, h * INGR), pygame.SRCALPHA)
    r = q.get_rect()
    tondo = (w * INGR) // 2
    pygame.draw.rect(q, (255, 255, 255, 26), r, border_radius=tondo)
    if val > 0:
        alta = max(w * INGR, int(h * val) * INGR)
        pygame.draw.rect(q, col, (0, r.h - alta, r.w, alta),
                         border_radius=tondo)
    sc.blit(pygame.transform.smoothscale(q, (w, h)), (x, y))


def barra_precisione(sc, x, y, w, h, val, t=1.0):
    barra_sottile(sc, x, y, w, h, val, colore_precisione(t))


def scritta_in_piedi(sc, testo, font, col, cx, cy):
    """Una scritta girata in verticale, che si legge dal basso in alto."""
    t = pygame.transform.rotate(font.render(testo, True, col), 90)
    sc.blit(t, t.get_rect(center=(int(cx), int(cy))))


def barra_potenza(sc, x, y, w, h, val, su=False):
    """La barra della potenza. Con su=True si riempie dal basso verso
    l'alto, com'e' naturale quando sta in piedi di lato."""
    s = pygame.Surface((w * INGR, h * INGR), pygame.SRCALPHA)
    r = s.get_rect()
    pygame.draw.rect(s, (42, 44, 50), r, border_radius=4 * INGR)
    if val > 0:
        col = (int(90 + 165 * val), int(200 - 150 * val), 60)
        if su:
            alta = int((h - 4) * val) * INGR
            pygame.draw.rect(s, col, (2 * INGR, r.h - 2 * INGR - alta,
                                      (w - 4) * INGR, alta),
                             border_radius=3 * INGR)
        else:
            pygame.draw.rect(s, col, (2 * INGR, 2 * INGR,
                                      int((w - 4) * val) * INGR,
                                      (h - 4) * INGR),
                             border_radius=3 * INGR)
    pygame.draw.rect(s, (110, 112, 120), r, width=INGR, border_radius=4 * INGR)
    sc.blit(pygame.transform.smoothscale(s, (w, h)), (x, y))


def col_messaggio(partita):
    """Il messaggio in mezzo sta in bianco. Colorarlo come il giocatore
    faceva a pugni con le due targhette ai lati, che il colore ce l'hanno
    per dire di chi e' il turno. Restano a colori solo il fallo, che e'
    un avviso, e la vittoria."""
    if partita.msg_key == "foul":
        return (236, 96, 84)
    if partita.msg_key in ("wins", "wins_early"):
        return COL_GIOC[partita.msg_chi]
    return TESTO


TEMPI = (0, 30, 45, 60)         # i valori dell'orologio, zero = spento
MATCH = (1, 3, 5, 7)            # quanti frame per partita, a scelta

# Nel torneo il match si allunga man mano: primi turni al meglio di tre,
# in fondo al meglio di nove. Qui sono i frame che servono per vincerlo.
FRAME_TURNO = (2, 2, 3, 3, 4, 5)
TEMPO_TORNEO = 60               # nel torneo non si sceglie: un minuto,
                                # che il colpo bisogna anche studiarlo


def smorzata(q, quanto):
    """Una copia piu' trasparente. Non si usa set_alpha su una copia: su
    Mac quella strada perde il modo di fusione e resta il rettangolo
    nero. Si moltiplica il canale alfa."""
    velo = pygame.Surface(q.get_size(), pygame.SRCALPHA)
    velo.blit(q, (0, 0))
    velo.fill((255, 255, 255, quanto), None, pygame.BLEND_RGBA_MULT)
    return velo


# Il fondo delle due strisce e i colori: oro come quello della
# televisione, chiaro sopra e piu' carico sotto, col filo chiaro in cima
# e quello scuro in fondo che le stacca dal nero dello sfondo.
ORO_SU = (252, 214, 104)
ORO_GIU = (230, 180, 54)
ORO_FILO_SU = (255, 236, 172)
ORO_FILO_GIU = (142, 100, 18)
VERDONE = (18, 120, 112)        # il riquadro in mezzo, quello dei frame
NOME_ACCESO = (24, 20, 10)      # chi sta tirando: nero pieno


def striscia(sc, r, su, giu):
    """Il fondo di una striscia: una sfumatura verticale con i due fili."""
    f = pygame.Surface(r.size)
    for i in range(r.h):
        k = i / float(max(1, r.h - 1))
        f.fill(tuple(int(su[j] + (giu[j] - su[j]) * k) for j in range(3)),
               (0, i, r.w, 1))
    sc.blit(f, r)
    pygame.draw.line(sc, ORO_FILO_SU, (r.left, r.top), (r.right, r.top))
    pygame.draw.line(sc, ORO_FILO_GIU, (r.left, r.bottom - 1),
                     (r.right, r.bottom - 1))


def barra_tv(sc, partita, resta=None, livello=0, vinti=None, serve=1):
    """La striscia del punteggio come quella della televisione: fondo
    oro largo quanto la finestra, bandiera e nome ai due capi, la
    freccia nera dalla parte di chi sta tirando e in mezzo i riquadri
    coi numeri. Nei due bianchi ci stanno i punti del frame in corso,
    nel verde in mezzo i frame vinti del match e fra parentesi quanti
    se ne gioca."""
    font, small = FONTS["font"], FONTS["small"]
    r = BANDA_PUNTI
    # niente fondo giallo: nomi bianchi e due fili d'oro che portano al
    # punteggio in mezzo, come nel logo

    # i tre riquadri, attaccati, in mezzo alla striscia
    alto = r.h - s(8)
    verde = pygame.Rect(0, 0, s(134), alto)
    verde.center = r.center
    bianco_sx = pygame.Rect(0, 0, s(76), alto)
    bianco_dx = pygame.Rect(0, 0, s(76), alto)
    bianco_sx.midright = verde.midleft
    bianco_dx.midleft = verde.midright
    pygame.draw.rect(sc, (252, 252, 250), bianco_sx)
    pygame.draw.rect(sc, (252, 252, 250), bianco_dx)
    pygame.draw.rect(sc, VERDONE, verde)

    # nei bianchi: allo snooker e ai birilli i punti, agli altri giochi
    # quante palle ha gia' fatto
    if partita.gioco in (2, 3, 6, 7):
        conto = (partita.punti[0], partita.punti[1])
    else:
        conto = (len(partita.prese(partita.gruppo[0], 0)),
                 len(partita.prese(partita.gruppo[1], 1)))
    for q, v in ((bianco_sx, conto[0]), (bianco_dx, conto[1])):
        t = font.render(str(v), True, (20, 20, 24))
        sc.blit(t, t.get_rect(center=q.center))

    # nel verde: i frame del match, o la serie in corso se match non ce n'e'
    if vinti:
        t = font.render(str(vinti[0]), True, (255, 255, 255))
        sc.blit(t, t.get_rect(midleft=(verde.left + s(16), verde.centery)))
        t = font.render(str(vinti[1]), True, (255, 255, 255))
        sc.blit(t, t.get_rect(midright=(verde.right - s(16), verde.centery)))
        t = small.render("(%d)" % (serve * 2 - 1), True, (168, 226, 220))
        sc.blit(t, t.get_rect(center=verde.center))
    elif partita.gioco in (2, 3, 6, 7) and partita.serie_punti:
        t = font.render("(%d)" % partita.serie_punti, True, (255, 255, 255))
        sc.blit(t, t.get_rect(center=verde.center))
    else:
        t = small.render("-", True, (128, 192, 186))
        sc.blit(t, t.get_rect(center=verde.center))

    # bandiera e nome ai due capi, tutti e due pieni: di chi e' il turno
    # lo dice la freccia, sbiadire il nome fa solo sporco
    carattere = FONTS.get("nomi_hud") or font
    fine_nome = [0, 0]
    for gi in (0, 1):
        t = carattere.render(nome(gi), True, AVORIO)
        ban = bandiera(BANDIERA[gi], s(22))
        if gi == 0:
            x = r.left + s(14)
            if ban:
                sc.blit(ban, ban.get_rect(midleft=(x, r.centery)))
                x += ban.get_width() + s(12)
            q = t.get_rect(midleft=(x, r.centery))
            fine_nome[0] = q.right
        else:
            x = r.right - s(14)
            if ban:
                sc.blit(ban, ban.get_rect(midright=(x, r.centery)))
                x -= ban.get_width() + s(12)
            q = t.get_rect(midright=(x, r.centery))
            fine_nome[1] = q.left
        sc.blit(t, q)

    # la freccia sta dalla parte di chi tira e punta verso il suo nome
    meta, lungo, stacco = s(9), s(12), s(14)
    spessore = max(1, s(1))
    y = r.centery
    for gi in (0, 1):
        if gi == 0:
            da, a = fine_nome[0] + s(16), bianco_sx.left - stacco - lungo - s(8)
        else:
            da, a = fine_nome[1] - s(16), bianco_dx.right + stacco + lungo + s(8)
        if (a - da) * (1 if gi == 0 else -1) > s(20):
            # il filo d'oro, con una perlina dove parte e una dove arriva
            pygame.draw.line(sc, ORO_LOGO, (da, y), (a, y), spessore)
            pygame.draw.circle(sc, ORO_LOGO, (da, y), max(2, s(2)))
            pygame.draw.circle(sc, ORO_LUCE, (a, y), max(2, s(3)))
    if partita.turno == 0:
        x = bianco_sx.left - stacco
        pt = [(x - lungo, y), (x, y - meta), (x, y + meta)]
    else:
        x = bianco_dx.right + stacco
        pt = [(x + lungo, y), (x, y - meta), (x, y + meta)]
    pygame.draw.polygon(sc, ORO_LUCE, pt)
    return r


def fascia_palle(sc, partita, resta=None):
    """La striscia di sotto: le palle che ognuno ha gia' imbucato, le sue
    dalla sua parte, e in mezzo l'orologio del tiro e di che palle e'
    fatto il break."""
    mini, font = FONTS["mini"], FONTS["font"]
    r = BANDA_PALLE
    # Niente fondo: qui sotto si lascia vedere lo sfondo. In televisione
    # la fanno bianca, ma con le palle colorate sopra il trasparente
    # tiene meglio.

    def palla_icona(n, cx):
        q = icona_ridotta(n, True)
        sc.blit(q, q.get_rect(center=(cx, r.centery)))

    def fila(gi, x, verso):
        if partita.gioco in (0, 4):
            # alla palla 8 e al blackball, al contrario: sotto il nome le
            # palle che ti tocca ancora imbucare, col disegno del set; una
            # alla volta spariscono. Finite le tue, resta la nera.
            g = partita.gruppo[gi]
            if g is None:
                return
            prese = sorted(b.num for b in partita.palle
                           if not b.dentro and b.gruppo() == g)
            if not prese and any(b.num == 8 and not b.dentro
                                 for b in partita.palle):
                prese = [8]
        else:
            prese = partita.prese(partita.gruppo[gi], gi)
        for i, n in enumerate(prese):
            cx = int(x + verso * i * (ICONA_PICCOLA + s(4)))
            ic = ICONE.get(n)
            if ic is not None:
                q = icona_ridotta(n, True)
                sc.blit(q, q.get_rect(center=(cx, r.centery)))
                continue
            rr = ICONA_PICCOLA // 2
            pygame.draw.circle(sc, colore_palla(n), (cx, r.centery), rr)
            if 9 <= n <= 15:
                pygame.draw.circle(sc, (244, 244, 240), (cx, r.centery), rr)
                pygame.draw.ellipse(sc, colore_palla(n),
                                    pygame.Rect(cx - rr,
                                                r.centery - rr // 2,
                                                rr * 2, rr))
            pygame.draw.circle(sc, (30, 30, 34), (cx, r.centery), rr, 1)

    if partita.gioco not in (1, 2, 3, 5, 6, 7):
        fila(0, r.left + s(16) + ICONA_PICCOLA // 2, 1)
        fila(1, r.right - s(16) - ICONA_PICCOLA // 2, -1)

    # in mezzo: l'orologio del tiro
    x = r.centerx
    if partita.gioco in (1, 5):
        # 9-ball e 10-ball: niente gruppi, in mezzo le palle ancora sul
        # tavolo, in fila; imbucate spariscono
        restano = sorted(b.num for b in partita.palle
                         if not b.dentro and b.num != 0)
        passo = ICONA_PICCOLA + s(4)
        largo = len(restano) * passo
        x0 = r.centerx - largo // 2 + passo // 2
        if resta is not None:
            x0 += s(24)
            x = x0 - passo // 2 - s(24)
        for i, n in enumerate(restano):
            palla_icona(n, int(x0 + i * passo))
        if resta is not None:
            t = FONTS.get("orologio", font).render(
                "%d" % max(0, int(math.ceil(resta))), True, ORO_SCELTA)
            sc.blit(t, t.get_rect(center=(x, r.centery)))
        resta = None
    if resta is not None:
        # l'orologio del tiro: carattere con le grazie, normale, in oro
        t = FONTS.get("orologio", font).render(
            "%d" % max(0, int(math.ceil(resta))), True, ORO_SCELTA)
        sc.blit(t, t.get_rect(center=(x, r.centery)))
        x += s(34)

    # e di che palle e' fatto il break: dodici rossi, tre blu, quattro
    # rosa e cinque neri fanno ottantasei
    if partita.gioco in (2, 6) and partita.serie_punti > 0:
        pezzi = [(n, partita.conto_break.get(n, 0))
                 for n in (SN_ROSSI[0],) + SN_COLORI
                 if partita.conto_break.get(n, 0)]
        if pezzi:
            largo = len(pezzi) * s(24)
            x = (x - largo // 2 + s(12) if resta is None
                 else x + s(12))
            for num, quante in pezzi:
                pygame.draw.circle(sc, sn_tinta(num), (x, r.centery), s(10))
                pygame.draw.circle(sc, (245, 245, 250), (x, r.centery),
                                   s(10), max(1, s(1)))
                col = (20, 20, 24) if num in (SN_GIALLO, SN_ROSA) \
                    else (250, 250, 252)
                q = mini.render(str(quante), True, col)
                sc.blit(q, q.get_rect(center=(x, r.centery)))
                x += s(24)
    return r


def pannello(sc, partita, potenza, resta=None, livello=0, vinti=None,
             serve=1):
    font, small = FONTS["font"], FONTS["small"]
    barra_tv(sc, partita, resta, livello, vinti, serve)
    fascia_palle(sc, partita, resta)

    # Il messaggio in cima, dove prima stava la striscia, con accanto la
    # palla da giocare.
    pezzi = []
    if partita.gioco in (2, 6) and not partita.finita:
        if getattr(partita, "free_ball", False):
            dritta, tinta = T("sn_free"), (250, 250, 250)
        elif partita.on_quale is not None:
            dritta, tinta = None, sn_tinta(partita.on_quale)
        elif partita.on_rosso:
            dritta, tinta = T("sn_red"), SN_ROSSO
        else:
            dritta, tinta = T("sn_colour"), (210, 210, 214)
        d = s(22)
        pallina = pygame.Surface((d, d), pygame.SRCALPHA)
        pygame.draw.circle(pallina, tinta, (d // 2, d // 2), s(9))
        pygame.draw.circle(pallina, (20, 20, 24), (d // 2, d // 2),
                           s(9), max(1, s(1)))
        pezzi.append(pallina)
        if dritta:
            pezzi.append(small.render(" " + dritta + "   ", True,
                                      (206, 210, 220)))
    # il messaggio col carattere classico, piu' piccolo e un po' piu'
    # giu', vicino al tavolo invece che attaccato al bordo
    pezzi.append(FONTS.get("messaggio", font).render(
        messaggio_ora(partita), True, col_messaggio(partita)))
    # i messaggi stanno tutti in basso, sopra il punteggio, fra il tavolo
    # e la striscia; in cima c'e' il nome del gioco
    largo = sum(q.get_width() for q in pezzi)
    x = WIN_W // 2 - largo // 2
    giu_tavolo = TAV_POS[1] + LEGNO_SU.bottom * SCALA
    y_msg = int((giu_tavolo + BANDA_PUNTI.top) / 2.0)
    for q in pezzi:
        sc.blit(q, q.get_rect(midleft=(x, y_msg)))
        x += q.get_width()
    scritta_logo(sc, WIN_W // 2, s(44), 0.55)
    # ai lati del logo le stecche dei due giocatori, la punta verso il
    # centro; quella di chi tira non c'e': ce l'ha in mano
    lung_h = s(300)
    k_h = 1.25 * lung_h / 145.0 / 2.0
    for gi in (0, 1):
        if gi == partita.turno and not partita.finita:
            continue
        verso = Vector2(1, 0) if gi == 0 else Vector2(-1, 0)
        punta = Vector2(WIN_W // 2 + (-1 if gi == 0 else 1) * s(215), s(44))
        disegna_stecca_su(sc, punta, verso, lung_h,
                          (1.3 * k_h, 2.0 * k_h, 3.0 * k_h), stecca_di(gi))
        # sotto, in corsivo, il numero e il nome
        st = stecca_di(gi)
        num = next((i for i, q in enumerate(STECCHE) if q is st), 0) + 1
        t = FONTS.get("elegante_mini", FONTS["mini"]).render(
            "%d. %s" % (num, T(st[0])), True, ORO_SOTTO)
        cx = punta.x - verso.x * lung_h / 2.0
        sc.blit(t, t.get_rect(center=(int(cx), s(44) + s(17))))

    # ai due capi della riga in cima: il livello del computer e l'aiuto
    mini = FONTS["mini"]
    if livello:
        t = mini.render(T("t_level") % livello, True, (232, 146, 52))
        sc.blit(t, t.get_rect(midleft=(s(16), ALTO // 2)))
    # i comandi in fondo, in mezzo, sotto le due strisce
    h = (riga_pad(small) if modo_comandi() == "pad" and ICONE_TASTI_OK()
         else small.render(aiuto_comandi(), True, (150, 156, 168)))
    sc.blit(h, h.get_rect(center=(WIN_W // 2,
                                  (BANDA_PALLE.bottom + WIN_H) // 2)))

    # Potenza, effetto e gesso: il giocatore 1 sul fianco sinistro, il 2
    # (o il computer) sul destro, a specchio. Si accende il fianco di chi
    # tira; l'altro resta a riposo col suo gesso.
    x_lato = max(s(30), int((TAV_POS[0] + TAV_VISTA[0] * SCALA) / 2.0))
    for gi, x in ((0, x_lato), (1, WIN_W - x_lato)):
        fianco(sc, partita, gi, x, potenza, mini)


def infinito(sc, cx, cy, a, col):
    """Il segno dell'infinito, disegnato: non tutti i caratteri ce l'hanno."""
    pts = []
    for k in range(49):
        t = k / 48.0 * 2.0 * math.pi
        d = 1.0 + math.sin(t) ** 2
        pts.append((cx + a * math.cos(t) / d,
                    cy + a * math.sin(t) * math.cos(t) / d))
    pygame.draw.aalines(sc, col, True, pts)
    pygame.draw.lines(sc, col, True, pts, max(1, s(2)))


def fianco(sc, partita, gi, x_lato, potenza, mini):
    attivo = (partita.turno == gi and not partita.finita)
    col_et = TESTO_OPACO
    alto_barra = s(190)
    y_barra = (ALTO + BASSO) // 2 - alto_barra // 2
    # due barre una accanto all'altra, ognuna con la sua scritta in piedi
    # sulla sinistra: la potenza e la precisione (il gesso sulla stecca)
    x_pot, x_pre = x_lato - s(18), x_lato + s(18)
    scritta_in_piedi(sc, T("power"), mini, col_et, x_pot - s(10),
                     y_barra + alto_barra // 2)
    pot = potenza if attivo else 0.0
    barra_sottile(sc, x_pot, y_barra, s(6), alto_barra, pot,
                  (int(90 + 165 * pot), int(200 - 150 * pot), 60))
    scritta_in_piedi(sc, T("precision"), mini, col_et, x_pre - s(10),
                     y_barra + alto_barra // 2)
    t_g = (GESSO[gi] - GESSO_MIN) / (1.0 - GESSO_MIN)
    prec = 0.4 + 0.6 * t_g
    barra_precisione(sc, x_pre, y_barra, s(6), alto_barra,
                     max(0.0, min(1.0, prec)), t_g)
    y_spin = y_barra + alto_barra + s(50)
    disegna_spin(sc, partita.spin if attivo else Vector2(0, 0), x_lato,
                 y_spin, s(19))
    lab = mini.render(T("spin"), True, col_et)
    sc.blit(lab, lab.get_rect(center=(x_lato, y_spin + s(32))))
    # il gessetto: sotto, quanto resta del suo cubetto. Quando la riga ha
    # perso meta' di quello che puo' perdere, pulsa piano; finito il
    # cubetto resta spento.
    g = GESSO[gi]
    if GESSO_INF[0]:
        tipo_c, cubo, scorta, pronto = "blu", 1.0, 0, True
    elif gi == 1 and CPU_ORA[0] is not None:
        tipo_c = gesso_cpu_tipo(CPU_ORA[0])
        cubo = CPU_CUBO[0] / float(gesso_dati(tipo_c)[1])
        scorta = 0
        pronto = CPU_CUBO[0] > 0
    else:
        k_cubo, k_tipo = CUBO_K[gi]
        tipo_c = CFG.get(k_tipo, "blu")
        if int(CFG.get(k_cubo, 0)) > 0:
            cubo = int(CFG[k_cubo]) / float(gesso_dati(tipo_c)[1])
        else:
            cubo = 0.0
            tipo_c = CFG.get("gesso_tipo", "blu")
        scorta = int((CFG.get("gessi") or {}).get(tipo_c, 0))
        pronto = gesso_pronto(gi)
    ora = pygame.time.get_ticks()
    lato = s(48)      # il cubetto grande quanto la pallina dell'effetto
    passati = (ora - GESSO_QUANDO[gi]) / 1000.0
    if 0.0 <= passati < 0.5:
        lato = int(lato * (1.0 + 0.35 * (1.0 - passati / 0.5)))
    im = icona_gesso(lato, tipo_c)
    if im is not None:
        im = im.copy()
        if not pronto:
            im.set_alpha(70)
        elif g <= 1.0 - (1.0 - GESSO_MIN) / 2.0 + 1e-6:
            im.set_alpha(int(110 + 145 * (0.5 + 0.5 * math.sin(ora / 250.0))))
        sc.blit(im, im.get_rect(center=(x_lato, y_spin + s(72))))
    lab = mini.render(T("chalk"), True, col_et)
    sc.blit(lab, lab.get_rect(center=(x_lato, y_spin + s(108))))
    if GESSO_INF[0]:
        infinito(sc, x_lato, y_spin + s(124), s(9), ORO_SCELTA)
    else:
        q = mini.render("%d%%" % int(round(cubo * 100)), True,
                        ORO_SCELTA if pronto else (232, 96, 72))
        sc.blit(q, q.get_rect(center=(x_lato, y_spin + s(124))))


# ------------------------------------------------------- musica ed effetti

# Le tracce stanno in una cartella "biliardo_audio" accanto al gioco. Una
# a caso per partita, in loop finche' la partita dura. Se la cartella non
# c'e', o la scheda audio non parte, il gioco va avanti in silenzio: la
# musica non deve mai essere un motivo per non giocare.

MUSICA_OK = False
ULTIMA_TRACCIA = None


def apri_audio():
    global MUSICA_OK
    try:
        pygame.mixer.init()
        MUSICA_OK = True
    except pygame.error:
        MUSICA_OK = False


def tracce():
    if not os.path.isdir(AUDIO):
        return []
    return sorted(f for f in os.listdir(AUDIO)
                  if f.lower().endswith((".ogg", ".mp3", ".wav", ".flac")))


def musica_nuova(volume=None):
    """Cambia traccia: una a caso, ma non la stessa di prima se ce n'e'
    piu' d'una. Il volume si puo' passare, perche' quello del menu e
    quello del tavolo sono due cose diverse."""
    global ULTIMA_TRACCIA
    if not MUSICA_OK:
        return None
    lista = tracce()
    if not lista:
        return None
    if volume is None:
        volume = CFG.get("musica", 20)
    altre = [f for f in lista if f != ULTIMA_TRACCIA]
    scelta = random.choice(altre if altre else lista)
    try:
        if volume <= 0:
            pygame.mixer.music.stop()
            return None
        pygame.mixer.music.load(os.path.join(AUDIO, scelta))
        pygame.mixer.music.set_volume(volume / 100.0)
        pygame.mixer.music.play(-1)
    except pygame.error:
        return None
    ULTIMA_TRACCIA = scelta
    return scelta


def _volume_musica(v):
    """Porta la musica a quel volume, o la fa sfumare se e' zero."""
    try:
        if v <= 0:
            pygame.mixer.music.fadeout(500)
        else:
            pygame.mixer.music.set_volume(v / 100.0)
    except pygame.error:
        pass


def musica_menu():
    """Nel menu. Se sta gia' andando le si mette il volume del menu, se
    no ne parte una a caso. La chiama lo sfondo dei menu, quindi vale
    per tutte le schermate senza scriverlo in ognuna."""
    if not MUSICA_OK:
        return
    v = CFG.get("musica", 20)
    if v <= 0:
        _volume_musica(0)
        return
    try:
        if pygame.mixer.music.get_busy():
            pygame.mixer.music.set_volume(v / 100.0)
            return
    except pygame.error:
        return
    musica_nuova(v)


def musica_gioco():
    """Al tavolo. Sono due volumi separati apposta: c'e' chi la musica
    la vuole solo nel menu e al tavolo vuole sentire le palle, e c'e'
    chi la vuole anche mentre gioca. A zero la musica sfuma e al tavolo
    resta il rumore del gioco."""
    if not MUSICA_OK:
        return
    v = CFG.get("musica_gioco", 20)
    if v <= 0:
        _volume_musica(0)
        return
    try:
        if not pygame.mixer.music.get_busy():
            musica_nuova(v)
        else:
            pygame.mixer.music.set_volume(v / 100.0)
    except pygame.error:
        pass


# Gli effetti stanno in "biliardo_fx", divisi per come comincia il nome del
# file: cue = la stecca che colpisce, ball = palla contro palla,
# rail = la sponda, pocket = la palla che cade in buca. Se di un tipo ce n'e'
# piu' d'uno, il numero nel nome dice l'ordine: ball_1_leggero,
# ball_2_medio, ball_3_forte. Si sceglie in base a quanto e' stata forte
# la botta. L'ordine lo dai tu col numero e non si misura da solo: i
# campioni arrivano da registrazioni diverse, uno piano puo' benissimo
# essere inciso piu' forte di uno tosto, e verrebbe messo al posto
# sbagliato. Il volume poi lo decide il gioco, non il file.

TIPI_FX = ("cue", "ball", "rail", "pocket", "turno", "orologio", "pausa",
           "triangolo", "bravo", "menu_tic", "menu_apri", "menu_chiudi",
           "gesso")
TIC_DA = 10             # da quanti secondi comincia il tic dell'orologio

# I suoni del pubblico non hanno un nome ordinato come gli altri: si
# riconoscono dalla parola che si trova dentro al file, cosi' vanno bene
# anche scaricati con il nome che hanno.
PUBBLICO = (("vittoria", ("vittoria", "victory", "winner")),
            ("applauso", ("applaus", "clap", "cheer")),
            ("delusione", ("disappoint", "delus", "shock", "sigh", "aww")))
SUONI = {}
CANALE_FESTA = None     # gli applausi hanno un canale loro, se no li
                        # tronca il primo rumore di palle che arriva


def carica_fx():
    global CANALE_FESTA
    if not MUSICA_OK or not os.path.isdir(FX):
        return
    pygame.mixer.set_num_channels(24)
    try:
        pygame.mixer.set_reserved(1)
        CANALE_FESTA = pygame.mixer.Channel(0)
    except pygame.error:
        CANALE_FESTA = None
    for f in sorted(os.listdir(FX)):
        if not f.lower().endswith((".ogg", ".wav", ".mp3", ".flac")):
            continue
        nome = os.path.splitext(f)[0].lower()
        chiave, peso = None, ordine(nome)
        for come_si_chiama, parole in PUBBLICO:
            if any(p in nome for p in parole):
                # fra i suoi, il leggero prima e il forte dopo
                chiave = come_si_chiama
                peso = (1 if "forte" in nome else 0, nome)
                break
        if chiave is None:
            for k in TIPI_FX:
                if nome.startswith(k):
                    chiave = k
                    break
        if chiave is not None:
            try:
                SUONI.setdefault(chiave, []).append(
                    (peso, pygame.mixer.Sound(os.path.join(FX, f))))
            except pygame.error:
                pass
    for chiave in SUONI:
        SUONI[chiave].sort()
        SUONI[chiave] = [s for _, s in SUONI[chiave]]
    # Per i colpi, davanti ai file veri si mettono due tocchi piu'
    # leggeri ricavati dal primo: cosi' la scala va dal tic al colpo
    # pieno, e chi sceglie il campione per forza ne trova uno giusto.
    for chiave in COLPI:
        gruppo = SUONI.get(chiave)
        if chiave in ("rail", "cue", "pocket"):
            continue    # questi suonano sempre col file vero
        if gruppo and HA_NUMPY:
            SUONI[chiave] = varianti_piano(gruppo[0]) + gruppo


# I rumori che dipendono da quanto forte e' la botta.
COLPI = ("cue", "ball", "rail", "pocket")


def varianti_piano(suono):
    """Da un colpo forte, due colpi piu' leggeri che suonano diversi,
    non solo piu' bassi. Un colpo preso piano sulla gomma o fra due
    palle non fa lo stesso "bum" col volume giu': perde il basso, che
    e' il corpo della botta, e si spegne subito. Resta un tic secco.
    Il primo e' il tocco leggero, il secondo quello medio.

    Si toglie il basso sottraendo la media mobile, che e' un modo
    semplice di separare il rimbombo dal colpo; e si spegne la coda con
    una discesa esponenziale corta. Se qualcosa va storto non si
    aggiunge niente e resta il suono com'era."""
    try:
        a = pygame.sndarray.array(suono).astype(np.float32)
        freq = pygame.mixer.get_init()[0]
    except (pygame.error, ValueError, TypeError):
        return []
    mono = (a.ndim == 1)
    x = a[:, None] if mono else a
    n = x.shape[0]
    if n < 64:
        return []
    t = np.arange(n, dtype=np.float32) / float(freq)
    picco_x = float(np.max(np.abs(x))) or 1.0
    fuori = []
    # taglio del basso in Hz, quanto dura la coda in secondi, livello
    for taglio, coda, livello in ((900.0, 0.030, 0.50),
                                  (320.0, 0.075, 0.78)):
        lung = max(3, int(freq / taglio))
        nucleo = np.ones(lung, dtype=np.float32) / lung
        basso = np.stack([np.convolve(x[:, c], nucleo, mode="same")
                          for c in range(x.shape[1])], axis=1)
        y = (x - basso) * np.exp(-t / coda)[:, None]
        picco = float(np.max(np.abs(y))) or 1.0
        y *= picco_x * livello / picco
        vivo = np.nonzero(np.max(np.abs(y), axis=1) > 30.0)[0]
        if len(vivo):
            y = y[:vivo[-1] + 1]
        y = np.clip(y, -32767, 32767).astype(np.int16)
        if mono:
            y = y[:, 0]
        try:
            fuori.append(pygame.sndarray.make_sound(np.ascontiguousarray(y)))
        except (pygame.error, ValueError):
            return []
    return fuori


ARBITRO = os.path.join(CARTELLA, "biliardo_voce", "pool")
ARBITRO_SN = os.path.join(CARTELLA, "biliardo_voce", "snooker")
VOCI = {}               # le frasi dell'arbitro gia' caricate
CANALE_VOCE = None
CODA_VOCE = []          # quello che deve ancora dire, una alla volta


def carica_voce():
    """Le frasi dell'arbitro, quelle che stanno in biliardo_voce/pool.
    Se la cartella non c'e' il gioco va uguale, muto."""
    global CANALE_VOCE
    if not MUSICA_OK:
        return
    for cartella in (ARBITRO, ARBITRO_SN):
        if not os.path.isdir(cartella):
            continue
        for nome_f in sorted(os.listdir(cartella)):
            if not nome_f.lower().endswith((".mp3", ".wav", ".ogg")):
                continue
            try:
                VOCI[os.path.splitext(nome_f)[0].lower()] = \
                    pygame.mixer.Sound(os.path.join(cartella, nome_f))
            except pygame.error:
                pass
    try:
        pygame.mixer.set_reserved(2)        # zero il pubblico, uno l'arbitro
        CANALE_VOCE = pygame.mixer.Channel(1)
    except pygame.error:
        CANALE_VOCE = None


def dice(*codici):
    """Mette in fila quello che l'arbitro deve dire. Una frase per volta,
    aspettando che finisca la precedente: se no si accavallano."""
    if SIMULO[0]:
        return              # il computer sta provando i tiri: zitto
    for c in codici:
        if c in VOCI:
            CODA_VOCE.append(c)


def aggiorna_voce():
    """Da chiamare a ogni fotogramma: fa partire la frase dopo appena
    l'arbitro ha finito quella prima."""
    if not CODA_VOCE or CANALE_VOCE is None:
        return
    if CANALE_VOCE.get_busy():
        return
    v = CFG.get("effetti", 100) / 100.0
    s = VOCI.get(CODA_VOCE.pop(0))
    if s is None or v <= 0.0:
        return
    s.set_volume(min(1.0, v))
    CANALE_VOCE.play(s)


def zittisci():
    """Chiude la bocca a tutti: applausi, arbitro e frasi in coda. Si
    chiama uscendo dal tavolo, se no gli applausi della vittoria
    continuano a sentirsi sul menu."""
    del CODA_VOCE[:]
    ferma_orologio()
    for canale in (CANALE_FESTA, CANALE_VOCE):
        if canale is None:
            continue
        try:
            canale.fadeout(250)
        except pygame.error:
            pass


def suona_festa(quale):
    """Gli applausi: uno corto quando fa un bel colpo, quello lungo
    quando vince la partita. Vanno sul canale loro, cosi' non li tronca
    il rumore delle palle e non tronca lui gli altri effetti."""
    if not quale:
        return
    testa = quale.split("_")[0]
    if testa == "applauso":
        # sui bei colpi l'applauso corto, uno a caso; il piu' tiepido
        # (due buche di fila e simili) non suona, se no diventa una lagna
        if quale.endswith("_c"):
            return
        testa = "bravo"
    gruppo = SUONI.get(testa)
    if testa == "vittoria" and not gruppo:
        gruppo = SUONI.get("applauso")      # a fine frame, uno a caso
    if not gruppo:
        return
    v = CFG.get("effetti", 100) / 100.0
    if v <= 0.0:
        return
    if testa == "delusione":
        s = gruppo[-1] if quale.endswith("_forte") and len(gruppo) > 1 \
            else gruppo[0]
    elif testa == "applauso":
        # a, b, c come sono chiamati i file: il primo e' il piu' caldo
        k = {"a": 0, "b": 1, "c": 2}.get(quale[-1], 0)
        s = gruppo[min(k, len(gruppo) - 1)]
    else:
        s = random.choice(gruppo)
    s.set_volume(v * (0.75 if testa == "vittoria" else 0.55))
    if CANALE_FESTA is not None:
        CANALE_FESTA.stop()
        CANALE_FESTA.play(s)
    else:
        s.play()


def ordine(nome):
    """Il primo numero che si trova nel nome del file. Senza numero va
    in fondo, in ordine alfabetico."""
    cifre = ""
    for c in nome:
        if c.isdigit():
            cifre += c
        elif cifre:
            break
    return (int(cifre) if cifre else 999, nome)


def segna(stato, nome, forza):
    """La fisica non suona: prende nota e basta. In un fotogramma ci sono
    decine di sottopassi, se suonasse a ogni urto sarebbe una mitragliata."""
    d = stato.setdefault("suoni", {})
    if forza > d.get(nome, 0.0):
        d[nome] = forza


ULTIMO_TIC = [0]        # a che secondo si e' sentito l'ultimo tic


def suona_orologio(resta):
    """Gli ultimi dieci secondi: un tic a ogni secondo esatto, da 10 a 1,
    cosi' il suono va insieme ai numeri."""
    if resta > TIC_DA:
        ULTIMO_TIC[0] = 0
        return
    sec = int(math.ceil(resta))
    if sec <= 0 or sec == ULTIMO_TIC[0]:
        return
    ULTIMO_TIC[0] = sec
    gruppo = SUONI.get("orologio")
    if not gruppo:
        return
    v = CFG.get("effetti", 100) / 100.0
    if v <= 0.0:
        return
    gruppo[0].set_volume(min(1.0, v))
    gruppo[0].play()


def ferma_orologio(azzera=True):
    """Si e' tirato prima della fine: il conto si zittisce. In pausa si
    zittisce e basta: riprendendo non riparte da capo, se no non
    tornerebbe piu' coi secondi veri."""
    if ULTIMO_TIC[0]:
        gruppo = SUONI.get("orologio")
        if gruppo:
            try:
                gruppo[0].fadeout(150)
            except pygame.error:
                pass
    if azzera:
        ULTIMO_TIC[0] = 0


def suona_fx(nome, quanto=0.8):
    """Un effetto dei menu, se c'e' il file."""
    gruppo = SUONI.get(nome)
    if not gruppo:
        return
    v = CFG.get("effetti", 100) / 100.0
    if v <= 0.0:
        return
    s = random.choice(gruppo)
    s.set_volume(min(1.0, v * quanto))
    s.play()


ULTIMO_SEL = [None, None]


def tic_menu(chiave, sel):
    """Il tic quando ci si sposta da una voce all'altra di un menu."""
    if ULTIMO_SEL[0] == chiave and ULTIMO_SEL[1] != sel:
        suona_fx("menu_tic", 0.6)
    ULTIMO_SEL[0], ULTIMO_SEL[1] = chiave, sel


def suona_pausa():
    """Il suono della pausa che si apre, quando si preme ESC al tavolo."""
    if SUONI.get("menu_apri"):
        suona_fx("menu_apri")
        return
    gruppo = SUONI.get("pausa")
    if not gruppo:
        return
    v = CFG.get("effetti", 100) / 100.0
    if v <= 0.0:
        return
    s = gruppo[0]
    s.set_volume(min(1.0, v * 0.8))
    s.play()


def suona_triangolo():
    """Il triangolo che si alza a inizio frame, quando le palle sono
    appena state messe."""
    gruppo = SUONI.get("triangolo")
    if not gruppo:
        return
    v = CFG.get("effetti", 100) / 100.0
    if v <= 0.0:
        return
    s = random.choice(gruppo)
    s.set_volume(min(1.0, v * 0.8))
    s.play()


def suona_turno():
    """Il suonino del cambio di mano: si sente quando la mano passa
    all'altro, cosi' te ne accorgi anche se stai guardando le palle."""
    gruppo = SUONI.get("turno")
    if not gruppo:
        return
    v = CFG.get("effetti", 100) / 100.0
    if v <= 0.0:
        return
    s = random.choice(gruppo)
    s.set_volume(min(1.0, v * 0.7))
    s.play()


# A che velocita' ogni suono arriva al pieno, come parte del tiro piu'
# forte. Sotto si abbassa: una sponda presa piano deve sentirsi appena,
# il colpo sordo pieno e' solo per la botta vera. Sono frazioni di
# TIRO_MAX e non pixel, cosi' valgono uguale a ogni risoluzione.
PIENO_SUONO = {"cue": 1.00, "ball": 0.60, "rail": 0.50, "pocket": 0.40}
SOTTO_NIENTE = 0.012    # sotto questa quota non suona: e' un appoggio
# la sponda si sente solo quando la botta e' forte: sotto, silenzio
SOGLIA_SUONO = {"rail": 0.15}


def forza_suono(nome, forza):
    """Dalla botta al volume. Non e' una riga dritta: l'orecchio sente il
    forte molto piu' del piano, quindi si eleva a una potenza e i tocchi
    leggeri scendono davvero, invece di restare tutti a meta' volume."""
    pieno = PIENO_SUONO.get(nome)
    if pieno is None:
        return 1.0, 1.0
    quota = max(0.0, forza / (TIRO_MAX * pieno))
    if quota < SOGLIA_SUONO.get(nome, SOTTO_NIENTE):
        return 0.0, 0.0
    quota = min(1.0, quota)
    # adesso la differenza la fa soprattutto il suono, che al piano e'
    # un altro: il volume accompagna e basta
    return 0.18 + 0.82 * quota ** 1.2, quota


def suona_eventi(stato):
    """Un colpo solo per tipo a fotogramma, quello piu' forte, e il volume
    va con la botta."""
    d = stato.get("suoni")
    if not d:
        return
    for nome, forza in d.items():
        gruppo = SUONI.get(nome)
        if not gruppo:
            continue
        v, quota = forza_suono(nome, forza)
        if v <= 0.0:
            continue
        # la stecca pesca a caso fra i suoi file; gli altri li sceglie la
        # botta: piano il primo, forte l'ultimo
        if nome == "cue":
            s = random.choice(gruppo)
        elif nome == "rail" and len(gruppo) >= 4:
            # quattro file dal piano al fortissimo: la prima botta veloce
            # prende l'ultimo, poi a ogni sponda la palla rallenta e scende
            if quota < 0.30:
                s = gruppo[0]
            elif quota < 0.45:
                s = gruppo[1]
            elif quota < 0.65:
                s = gruppo[2]
            else:
                s = gruppo[3]
        else:
            s = gruppo[min(len(gruppo) - 1, int(quota * len(gruppo)))]
        s.set_volume(v * CFG.get("effetti", 100) / 100.0)
        s.play()
    d.clear()


# ----------------------------------------------------------- le lingue

LINGUE = [("en", "English"), ("it", "Italiano"), ("fr", "Francais"),
          ("es", "Espanol")]


# ------------------------------------------------------ le lingue a schermo

# Tutto quello che si legge nel gioco sta qui dentro. La chiave e' un
# nome corto, il valore la frase nelle cinque lingue. Quello che manca in
# una lingua ricasca sull'inglese, cosi' se un domani aggiungiamo una voce
# nuova il gioco non resta col buco.

TESTI = {
    "en": {
        "free": "Multiplayer", "settings": "Settings", "quit": "Quit",
        "sub": "two players, one keyboard",
        "settings_t": "SETTINGS", "sub_set": "click the arrows, or left and right",
        "language": "Language", "voice": "Voice", "cloth": "Cloth",
        "rails": "Rails", "back": "Back", "random": "Random",
        "on": "on", "off": "off",
        "novoice": "missing - run crea_voci",
        "player": "Player %d", "solids": "solids", "stripes": "stripes",
        "breaks": "%s breaks", "to_play": "%s to play",
        "continues": "%s continues", "wins": "%s wins",
        "wins_early": "%s wins, 8 ball potted early",
        "foul": "Foul: %s - %s, ball in hand",
        "names": "WHO IS PLAYING", "sub_names": "type the names, then Start",
        "start": "Start", "pause": "PAUSE", "resume": "Resume game",
        "mainmenu": "End game", "music": "Music", "effects": "Effects",
        "newgame": "New game",
        "f_nohit": "no ball hit", "f_cue": "cue ball potted",
        "f_norail": "no rail after contact",
        "f_eight": "hit the 8 ball first",
        "f_group": "wrong group hit first",
        "power": "POWER", "spin": "SPIN",
        "aiuto": "W/S top-back spin   A/D side spin   arrows fine aim   "
                 "E clear spin     ESC pause",
        "fine": "ESC to exit",
    },
    "it": {
        "free": "Multiplayer", "settings": "Impostazioni", "quit": "Esci",
        "sub": "due giocatori, una tastiera",
        "settings_t": "IMPOSTAZIONI", "sub_set": "clicca le frecce, o destra e sinistra",
        "language": "Lingua", "voice": "Voce", "cloth": "Panno",
        "rails": "Bordi", "back": "Indietro", "random": "A caso",
        "on": "si", "off": "no",
        "novoice": "mancano - lancia crea_voci",
        "player": "Giocatore %d", "solids": "piene", "stripes": "mezze",
        "breaks": "Spacca %s",
        "to_play": "Tocca a %s",
        "continues": "%s continua",
        "wins": "Vince %s",
        "wins_early": "Vince %s, 8 imbucata prima del tempo",
        "foul": "Fallo: %s - %s, palla in mano",
        "names": "CHI GIOCA", "sub_names": "scrivi i nomi, poi Comincia",
        "start": "Comincia", "pause": "PAUSA", "resume": "Continua partita",
        "mainmenu": "Termina partita", "music": "Musica", "effects": "Effetti",
        "newgame": "Nuova partita",
        "f_nohit": "nessuna palla toccata", "f_cue": "bianca in buca",
        "f_norail": "nessuna sponda dopo il contatto",
        "f_eight": "toccata prima l'8",
        "f_group": "toccato prima il gruppo sbagliato",
        "power": "POTENZA", "spin": "EFFETTO",
        "aiuto": "W/S effetto alto-basso   A/D laterale   frecce mira fine   "
                 "E azzera effetto     ESC pausa",
        "fine": "ESC per uscire",
    },
    "fr": {
        "free": "Multiplayer", "settings": "Reglages", "quit": "Quitter",
        "sub": "deux joueurs, un clavier",
        "settings_t": "REGLAGES", "sub_set": "cliquez les fleches, ou gauche et droite",
        "language": "Langue", "voice": "Voix", "cloth": "Tapis",
        "rails": "Bandes", "back": "Retour", "random": "Au hasard",
        "on": "oui", "off": "non",
        "novoice": "manquantes - lancez crea_voci",
        "player": "Joueur %d", "solids": "les pleines", "stripes": "les rayees",
        "breaks": "%s casse",
        "to_play": "A %s de jouer",
        "continues": "%s continue",
        "wins": "%s gagne",
        "wins_early": "%s gagne, la 8 est tombee trop tot",
        "foul": "Faute: %s - %s, bille en main",
        "names": "QUI JOUE", "sub_names": "entrez les noms, puis Jouer",
        "start": "Jouer", "pause": "PAUSE", "resume": "Reprendre la partie",
        "mainmenu": "Terminer la partie", "music": "Musique", "effects": "Effets",
        "newgame": "Nouvelle partie",
        "f_nohit": "aucune bille touchee", "f_cue": "blanche empochee",
        "f_norail": "aucune bande apres le contact",
        "f_eight": "la 8 touchee en premier",
        "f_group": "mauvais groupe touche en premier",
        "power": "PUISSANCE", "spin": "EFFET",
        "aiuto": "W/S effet haut-bas   A/D lateral   fleches visee fine   "
                 "E annuler     ESC pause",
        "fine": "ESC pour quitter",
    },
    "es": {
        "free": "Multiplayer", "settings": "Ajustes", "quit": "Salir",
        "sub": "dos jugadores, un teclado",
        "settings_t": "AJUSTES", "sub_set": "pulsa las flechas, o izquierda y derecha",
        "language": "Idioma", "voice": "Voz", "cloth": "Pano",
        "rails": "Bandas", "back": "Atras", "random": "Al azar",
        "on": "si", "off": "no",
        "novoice": "faltan - ejecuta crea_voci",
        "player": "Jugador %d", "solids": "las lisas", "stripes": "las rayadas",
        "breaks": "Rompe %s",
        "to_play": "Juega %s",
        "continues": "%s continua",
        "wins": "Gana %s",
        "wins_early": "Gana %s, la 8 cayo antes de tiempo",
        "foul": "Falta: %s - %s, bola en mano",
        "names": "QUIEN JUEGA", "sub_names": "escribe los nombres, luego Empezar",
        "start": "Empezar", "pause": "PAUSA", "resume": "Continuar partida",
        "mainmenu": "Terminar partida", "music": "Musica", "effects": "Efectos",
        "newgame": "Nueva partida",
        "f_nohit": "ninguna bola tocada", "f_cue": "blanca embocada",
        "f_norail": "ninguna banda tras el contacto",
        "f_eight": "tocada antes la 8",
        "f_group": "tocado antes el grupo equivocado",
        "power": "POTENCIA", "spin": "EFECTO",
        "aiuto": "W/S efecto alto-bajo   A/D lateral   flechas mira fina   "
                 "E anular     ESC pausa",
        "fine": "ESC para salir",
    },
    "ja": {
        "free": "\u30de\u30eb\u30c1\u30d7\u30ec\u30a4",
        "settings": "\u8a2d\u5b9a", "quit": "\u7d42\u4e86",
        "sub": "\u4e8c\u4eba\u3067\u30d7\u30ec\u30a4",
        "settings_t": "\u8a2d\u5b9a",
        "sub_set": "\u5de6\u53f3\u30ad\u30fc\u3067\u5909\u66f4",
        "language": "\u8a00\u8a9e", "voice": "\u30dc\u30a4\u30b9",
        "cloth": "\u30e9\u30b7\u30e3", "rails": "\u30af\u30c3\u30b7\u30e7\u30f3",
        "back": "\u623b\u308b", "random": "\u30e9\u30f3\u30c0\u30e0",
        "on": "\u30aa\u30f3", "off": "\u30aa\u30d5",
        "novoice": "\u306a\u3057 - crea_voci \u3092\u5b9f\u884c",
        "player": "\u30d7\u30ec\u30a4\u30e4\u30fc%d",
        "solids": "\u30bd\u30ea\u30c3\u30c9", "stripes": "\u30b9\u30c8\u30e9\u30a4\u30d7",
        "breaks": "%s \u306e\u30d6\u30ec\u30a4\u30af",
        "to_play": "%s \u306e\u756a",
        "continues": "%s \u7d9a\u884c",
        "wins": "%s \u306e\u52dd\u3061",
        "wins_early": "%s \u306e\u52dd\u3061\uff088\u756a\u3092\u5148\u306b\u843d\u3068\u3057\u305f\uff09",
        "foul": "\u30d5\u30a1\u30a6\u30eb: %s - %s \u30dc\u30fc\u30eb\u30a4\u30f3\u30cf\u30f3\u30c9",
        "names": "\u30d7\u30ec\u30a4\u30e4\u30fc",
        "sub_names": "\u540d\u524d\u3092\u5165\u529b\u3057\u3066\u30b9\u30bf\u30fc\u30c8",
        "start": "\u30b9\u30bf\u30fc\u30c8", "pause": "\u30dd\u30fc\u30ba",
        "resume": "\u30b2\u30fc\u30e0\u3092\u518d\u958b", "mainmenu": "\u30b2\u30fc\u30e0\u3092\u7d42\u4e86",
        "music": "\u97f3\u697d", "effects": "\u52b9\u679c\u97f3",
        "newgame": "\u65b0\u3057\u3044\u30b2\u30fc\u30e0",
        "f_nohit": "\u30dc\u30fc\u30eb\u306b\u5f53\u305f\u3089\u306a\u3044",
        "f_cue": "\u624b\u7389\u3092\u843d\u3068\u3057\u305f",
        "f_norail": "\u63a5\u89e6\u5f8c\u306b\u30af\u30c3\u30b7\u30e7\u30f3\u306a\u3057",
        "f_eight": "8\u756a\u306b\u5148\u306b\u5f53\u305f\u3063\u305f",
        "f_group": "\u9055\u3046\u30b0\u30eb\u30fc\u30d7\u306b\u5148\u306b\u5f53\u305f\u3063\u305f",
        "power": "\u30d1\u30ef\u30fc", "spin": "\u30b9\u30d4\u30f3",
        "aiuto": "W/S \u7e26\u306e\u30b9\u30d4\u30f3     A/D \u6a2a\u306e\u30b9\u30d4\u30f3     "
                 "E \u89e3\u9664     ESC \u30dd\u30fc\u30ba",
        "fine": "ESC \u3067\u7d42\u4e86",
    },
}


FONTS = {}


# Le voci del computer. Stanno qui sotto e non dentro il blocco di
# sopra per non rimescolarlo tutto: si infilano nello stesso posto.

CPU_TESTI = {
    "en": {"avanti": "press a key for the next frame", "match": "Match", "m_uno": "single frame", "m_best": "best of %d", "sn_miss": "Foul and a miss, %d away - %s plays again", "sn_free": "free ball", "sn_foul": "Foul, %d away - %s to play", "sn_pari": "frame tied", "sn_break": "break %d", "sn_on": "on: %s", "sn_red": "red", "sn_colour": "a colour", "f_low": "wrong ball first", "r_64": "Round of 64", "r_32": "Round of 32", "r_16": "Round of 16", "r_8": "Quarter-finals", "r_4": "Semi-finals", "r_2": "Final", "t_champ": "TOURNAMENT WON", "t_bracket": "the draw", "t_slot": "Tournament level", "t_set": "set", "t_empty": "empty", "soon": "soon", "sub_disc": "pick the game", "sub_mode": "pick how you want to play", "shotclock": "Shot clock", "f_time": "time up", "flag": "Flag", "tournament": "Tournament", "t_level": "LEVEL %d",
           "t_vs": "against %s", "t_go": "Play", "t_won": "YOU BEAT %s",
           "t_lost": "%s BEAT YOU", "t_next": "Next level",
           "t_reach": "you got to level %d", "t_record": "best: level %d",
           "t_again": "Start over", "t_sub": "win and you go up a level",
           "cpu": "Vs Computer", "computer": "Computer", "level": "Level",
           "l_facile": "Beginner", "l_medio": "Amateur",
           "l_club": "Club player", "l_forte": "Pro",
           "l_maestro": "Master", "l_campione": "Champion",
           "sub_cpu": "pick the level, then Start"},
    "it": {"avanti": "premi un tasto per il frame successivo", "match": "Match", "m_uno": "un frame", "m_best": "al meglio di %d", "sn_miss": "Fallo e miss, %d punti - ritira %s", "sn_free": "free ball", "sn_foul": "Fallo, %d punti - tocca a %s", "sn_pari": "frame pari", "sn_break": "serie %d", "sn_on": "gioca: %s", "sn_red": "un rosso", "sn_colour": "un colore", "f_low": "non la piu' bassa", "r_64": "Trentaduesimi", "r_32": "Sedicesimi", "r_16": "Ottavi", "r_8": "Quarti", "r_4": "Semifinale", "r_2": "Finale", "t_champ": "TORNEO VINTO", "t_bracket": "il tabellone", "t_slot": "Livello torneo", "t_set": "assegnato", "t_empty": "vuoto", "soon": "presto", "sub_disc": "scegli la disciplina", "sub_mode": "scegli il tipo di partita", "shotclock": "Tempo", "f_time": "tempo scaduto", "cpu": "Contro il computer", "computer": "Computer",
           "level": "Livello", "l_facile": "Principiante",
           "l_medio": "Dilettante", "l_club": "Giocatore di club",
           "l_forte": "Esperto", "l_maestro": "Maestro",
           "l_campione": "Campione",
           "sub_cpu": "scegli il livello, poi Comincia"},
    "fr": {"cpu": "Contre l'ordinateur", "computer": "Ordinateur",
           "level": "Niveau", "l_facile": "Debutant",
           "l_medio": "Amateur", "l_forte": "Expert",
           "l_campione": "Champion",
           "sub_cpu": "choisis le niveau, puis Jouer"},
    "es": {"cpu": "Contra el ordenador", "computer": "Ordenador",
           "level": "Nivel", "l_facile": "Principiante",
           "l_medio": "Aficionado", "l_forte": "Experto",
           "l_campione": "Campeon",
           "sub_cpu": "elige el nivel, luego Empezar"},
    "ja": {"cpu": "\u30b3\u30f3\u30d4\u30e5\u30fc\u30bf\u5bfe\u6226",
           "computer": "\u30b3\u30f3\u30d4\u30e5\u30fc\u30bf",
           "level": "\u30ec\u30d9\u30eb",
           "l_facile": "\u3084\u3055\u3057\u3044",
           "l_medio": "\u3075\u3064\u3046",
           "l_forte": "\u3080\u305a\u304b\u3057\u3044",
           "l_campione": "\u9054\u4eba",
           "sub_cpu": "\u30ec\u30d9\u30eb\u3092\u9078\u3093\u3067"
                      "\u304b\u3089\u958b\u59cb"},
}

TORNEO_TESTI = {
    "it": {"flag": "Bandiera", "tournament": "Torneo", "t_level": "LIVELLO %d",
           "t_vs": "contro %s", "t_go": "Gioca",
           "t_won": "HAI BATTUTO %s", "t_lost": "%s TI HA BATTUTO",
           "t_next": "Livello successivo", "t_reach": "sei arrivato al livello %d",
           "t_record": "record: livello %d", "t_again": "Ricomincia",
           "t_sub": "chi vince sale di livello"},
    "fr": {"avanti": "une touche pour la manche suivante", "match": "Match", "m_uno": "une manche", "m_best": "au meilleur de %d", "sn_miss": "Faute et miss, %d points - %s rejoue", "sn_free": "bille libre", "sn_foul": "Faute, %d points - a %s de jouer", "sn_pari": "frame a egalite", "sn_break": "serie %d", "sn_on": "a jouer : %s", "sn_red": "une rouge", "sn_colour": "une couleur", "f_low": "mauvaise bille", "r_64": "32es de finale", "r_32": "16es de finale", "r_16": "8es de finale", "r_8": "Quarts", "r_4": "Demi-finales", "r_2": "Finale", "t_champ": "TOURNOI GAGNE", "t_bracket": "le tableau", "t_slot": "Niveau du tournoi", "t_set": "attribue", "t_empty": "vide", "soon": "bientot", "sub_disc": "choisis le jeu", "sub_mode": "choisis le type de partie", "shotclock": "Chrono", "f_time": "temps ecoule", "flag": "Drapeau", "tournament": "Tournoi", "t_level": "NIVEAU %d",
           "t_vs": "contre %s", "t_go": "Jouer",
           "t_won": "TU AS BATTU %s", "t_lost": "%s T'A BATTU",
           "t_next": "Niveau suivant", "t_reach": "tu es arrive au niveau %d",
           "t_record": "record : niveau %d", "t_again": "Recommencer",
           "t_sub": "qui gagne monte d'un niveau"},
    "es": {"avanti": "pulsa una tecla para el siguiente frame", "match": "Match", "m_uno": "un frame", "m_best": "al mejor de %d", "sn_miss": "Falta y miss, %d puntos - repite %s", "sn_free": "bola libre", "sn_foul": "Falta, %d puntos - juega %s", "sn_pari": "frame empatado", "sn_break": "serie %d", "sn_on": "juega: %s", "sn_red": "una roja", "sn_colour": "un color", "f_low": "bola equivocada", "r_64": "Treintaidosavos", "r_32": "Dieciseisavos", "r_16": "Octavos", "r_8": "Cuartos", "r_4": "Semifinales", "r_2": "Final", "t_champ": "TORNEO GANADO", "t_bracket": "el cuadro", "t_slot": "Nivel del torneo", "t_set": "asignado", "t_empty": "vacio", "soon": "pronto", "sub_disc": "elige el juego", "sub_mode": "elige el tipo de partida", "shotclock": "Tiempo", "f_time": "tiempo agotado", "flag": "Bandera", "tournament": "Torneo", "t_level": "NIVEL %d",
           "t_vs": "contra %s", "t_go": "Jugar",
           "t_won": "HAS GANADO A %s", "t_lost": "%s TE HA GANADO",
           "t_next": "Nivel siguiente", "t_reach": "llegaste al nivel %d",
           "t_record": "record: nivel %d", "t_again": "Empezar de nuevo",
           "t_sub": "quien gana sube de nivel"},
    "ja": {"avanti": "\u6b21\u306e\u30d5\u30ec\u30fc\u30e0\u3078", "match": "\u30de\u30c3\u30c1", "m_uno": "1\u30d5\u30ec\u30fc\u30e0", "m_best": "%d\u30d5\u30ec\u30fc\u30e0\u5148\u53d6", "sn_miss": "\u30d5\u30a1\u30a6\u30eb\u30df\u30b9 %d \u70b9 - %s", "sn_free": "\u30d5\u30ea\u30fc\u30dc\u30fc\u30eb", "sn_foul": "\u30d5\u30a1\u30a6\u30eb %d \u70b9 - %s", "sn_pari": "\u540c\u70b9", "sn_break": "\u30d6\u30ec\u30a4\u30af %d", "sn_on": "\u6b21: %s", "sn_red": "\u30ec\u30c3\u30c9", "sn_colour": "\u30ab\u30e9\u30fc", "f_low": "\u6700\u5c0f\u756a\u53f7\u3067\u306a\u3044", "r_64": "64\u5f37", "r_32": "32\u5f37", "r_16": "16\u5f37", "r_8": "\u6e96\u3005\u6c7a\u52dd", "r_4": "\u6e96\u6c7a\u52dd", "r_2": "\u6c7a\u52dd", "t_champ": "\u512a\u52dd", "t_bracket": "\u30c8\u30fc\u30ca\u30e1\u30f3\u30c8\u8868", "t_slot": "\u30c8\u30fc\u30ca\u30e1\u30f3\u30c8\u306e\u30ec\u30d9\u30eb", "t_set": "\u8a2d\u5b9a\u6e08", "t_empty": "\u672a\u8a2d\u5b9a", "soon": "\u8fd1\u65e5\u516c\u958b", "sub_disc": "\u7a2e\u76ee\u3092\u9078\u3076", "sub_mode": "\u5bfe\u5c40\u3092\u9078\u3076", "shotclock": "\u6301\u3061\u6642\u9593", "f_time": "\u6642\u9593\u5207\u308c", "flag": "\u56fd\u65d7", "tournament": "\u30c8\u30fc\u30ca\u30e1\u30f3\u30c8",
           "t_level": "\u30ec\u30d9\u30eb %d",
           "t_vs": "%s \u3068\u5bfe\u6226",
           "t_go": "\u958b\u59cb",
           "t_won": "%s \u306b\u52dd\u3063\u305f",
           "t_lost": "%s \u306b\u8ca0\u3051\u305f",
           "t_next": "\u6b21\u306e\u30ec\u30d9\u30eb",
           "t_reach": "\u30ec\u30d9\u30eb %d \u307e\u3067\u5230\u9054",
           "t_record": "\u6700\u9ad8\uff1a\u30ec\u30d9\u30eb %d",
           "t_again": "\u6700\u521d\u304b\u3089",
           "t_sub": "\u52dd\u3066\u3070\u30ec\u30d9\u30eb\u30a2\u30c3\u30d7"},
}

for _l, _d in CPU_TESTI.items():
    TESTI.setdefault(_l, {}).update(_d)
for _l, _d in TORNEO_TESTI.items():
    TESTI.setdefault(_l, {}).update(_d)


# La riga della risoluzione. Si applica riaprendo il gioco, e la riga lo
# dice, perche' le misure si calcolano una volta sola all'avvio.
RIS_TESTI = {
    "en": {"resolution": "Resolution", "riavvia": ""},
    "it": {"resolution": "Risoluzione", "riavvia": ""},
    "fr": {"resolution": "Resolution", "riavvia": ""},
    "es": {"resolution": "Resolucion", "riavvia": ""},
    "ja": {"resolution": "\u89e3\u50cf\u5ea6",
           "riavvia": ""},
}
for _l, _d in RIS_TESTI.items():
    TESTI.setdefault(_l, {}).update(_d)


# Le tre porte delle impostazioni.
PAGINE_TESTI = {
    "en": {"mus_menu": "Menu music", "mus_gioco": "Music in game",
           "p_audio": "Sound", "p_regole": "Rules", "p_tavolo": "Table",
           "p_grafica": "Graphics", "screen": "Screen",
           "s_pieno": "fullscreen", "s_finestra": "window"},
    "it": {"mus_menu": "Musica nel menu", "mus_gioco": "Musica in gioco",
           "p_audio": "Audio", "p_regole": "Regole", "p_tavolo": "Tavolo",
           "p_grafica": "Grafica", "screen": "Schermo",
           "s_pieno": "tutto schermo", "s_finestra": "finestra"},
    "fr": {"mus_menu": "Musique du menu", "mus_gioco": "Musique en jeu",
           "p_audio": "Son", "p_regole": "Regles", "p_tavolo": "Table",
           "p_grafica": "Graphismes", "screen": "Ecran",
           "s_pieno": "plein ecran", "s_finestra": "fenetre"},
    "es": {"mus_menu": "Musica del menu", "mus_gioco": "Musica en juego",
           "p_audio": "Sonido", "p_regole": "Reglas", "p_tavolo": "Mesa",
           "p_grafica": "Graficos", "screen": "Pantalla",
           "s_pieno": "pantalla completa", "s_finestra": "ventana"},
    "ja": {"mus_menu": "\u30e1\u30cb\u30e5\u30fc\u306e\u97f3\u697d",
           "mus_gioco": "\u30d7\u30ec\u30a4\u4e2d\u306e\u97f3\u697d",
           "p_audio": "\u30b5\u30a6\u30f3\u30c9",
           "p_regole": "\u30eb\u30fc\u30eb",
           "p_tavolo": "\u30c6\u30fc\u30d6\u30eb",
           "p_grafica": "\u753b\u9762",
           "screen": "\u8868\u793a",
           "s_pieno": "\u5168\u753b\u9762",
           "s_finestra": "\u30a6\u30a3\u30f3\u30c9\u30a6"},
}
for _l, _d in PAGINE_TESTI.items():
    TESTI.setdefault(_l, {}).update(_d)


def fai_fonts():
    """Il giapponese ha bisogno di un carattere che abbia i suoi segni:
    DejaVu non ce l'ha e verrebbero fuori dei quadratini. Si prende il
    primo nome della lista che esiste sul computer."""
    if CFG.get("lingua") == "ja":
        fam = ("yugothic,yugothicui,msgothic,meiryo,notosanscjkjp,"
               "notosansjp,dejavusans")
    else:
        fam = "dejavusans"
    # Le misure passano per K: a risoluzione doppia le lettere si
    # disegnano grandi il doppio, non si ingrandiscono dopo. E' tutta
    # qui la differenza fra nitido e sgranato.
    FONTS["font"] = pygame.font.SysFont(fam, s(20), bold=True)
    FONTS["grande"] = pygame.font.SysFont(fam, s(52), bold=True)
    FONTS["medio"] = pygame.font.SysFont(fam, s(30), bold=True)
    # Un carattere con le grazie per i titoli delle schermate: da circolo
    # inglese, non da pannello di controllo. Si prende il primo che c'e'.
    FONTS["classico"] = pygame.font.SysFont(
        "didot,baskerville,hoeflertext,palatino,georgia,garamond,"
        "timesnewroman,liberationserif,dejavuserif", s(36), italic=True)
    FONTS["small"] = pygame.font.SysFont(fam, s(15))
    # l'orologio del tiro: con le grazie, non grassetto
    FONTS["orologio"] = pygame.font.SysFont(
        "georgia,baskerville,palatino,timesnewroman,liberationserif,"
        "dejavuserif", s(24))
    # i nomi dei giocatori sotto il tavolo: il carattere di sempre,
    # in bianco
    FONTS["nomi_hud"] = FONTS["font"]
    FONTS["mini"] = pygame.font.SysFont(fam, max(8, s(10)))
    # per il titolo: un grazia in corsivo, che con il bastone del resto
    # del menu fa contrasto
    FONTS["titolo"] = pygame.font.SysFont(
        "georgia,timesnewroman,liberationserif,dejavuserif", s(40),
        italic=True)
    # questo no: sta dentro alla texture della palla, non sullo schermo
    FONTS["num"] = pygame.font.SysFont("dejavusans", 11, bold=True)
    # Il carattere elegante per i titoli dei menu, dalla cartella font
    # del gioco: cosi' si vede uguale su ogni computer. Se manca, si
    # resta coi caratteri di prima.
    FONTS["elegante"] = carattere_elegante(s(58)) or FONTS["grande"]
    FONTS["elegante_p"] = carattere_elegante(s(42)) or FONTS["titolo"]
    FONTS["elegante_voce"] = carattere_elegante(s(28)) or FONTS["font"]
    FONTS["elegante_mini"] = carattere_elegante(s(15)) or FONTS["mini"]
    # il messaggio della partita, in alto: il carattere elegante
    FONTS["messaggio"] = carattere_elegante(s(22)) or FONTS["font"]
    return FONTS


def tit_el(testo):
    """Nel corsivo elegante le maiuscole tutte di fila non si leggono:
    "PAUSE" diventa "Pause"."""
    testo = str(testo)
    return testo.title() if testo.isupper() else testo


def carattere_elegante(misura):
    cartella = os.path.join(GFX, "font")
    if not os.path.isdir(cartella):
        return None
    for f in sorted(os.listdir(cartella)):
        if f.lower().endswith((".ttf", ".otf")):
            try:
                return pygame.font.Font(os.path.join(cartella, f), misura)
            except (pygame.error, OSError):
                continue
    return None


NOMI = ["", ""]
BANDIERA = ["", ""]     # il paese dei due giocatori


def nome(i):
    """Il nome scritto dal giocatore, o "Giocatore 1" se non ne ha messo
    nessuno."""
    return NOMI[i] or (T("player") % (i + 1))


# Le frasi del cinque birilli, infilate come quelle del computer.
BIR_TESTI = {
    "en": {"bi_foul": "Foul, %d to %s", "bi_punti": "%s scores %d",
           "bi_zero": "no score"},
    "it": {"bi_foul": "Fallo, %d punti a %s", "bi_punti": "%s fa %d punti",
           "bi_zero": "niente punti"},
    "fr": {"bi_foul": "Faute, %d points pour %s",
           "bi_punti": "%s marque %d points", "bi_zero": "aucun point"},
    "es": {"bi_foul": "Falta, %d puntos para %s",
           "bi_punti": "%s hace %d puntos", "bi_zero": "sin puntos"},
    "ja": {"bi_foul": "\u30d5\u30a1\u30a6\u30eb %d \u70b9 %s",
           "bi_punti": "%s %d \u70b9", "bi_zero": "\u5f97\u70b9\u306a\u3057"},
}
for _l, _d in BIR_TESTI.items():
    TESTI.setdefault(_l, {}).update(_d)

STECCA_TESTI = {'en': {'cue': 'Cue', 'cue_acero': 'Maple', 'cue_ebano': 'Ebony', 'cue_palissandro': 'Rosewood', 'cue_sneaky': 'Sneaky Pete', 'cue_carbonio': 'Carbon', 'cue_avorio': 'Ivory'}, 'it': {'cue': 'Stecca', 'cue_acero': 'Acero', 'cue_ebano': 'Ebano', 'cue_palissandro': 'Palissandro', 'cue_sneaky': 'Sneaky Pete', 'cue_carbonio': 'Carbonio', 'cue_avorio': 'Avorio'}, 'fr': {'cue': 'Queue', 'cue_acero': 'Erable', 'cue_ebano': 'Ebene', 'cue_palissandro': 'Palissandre', 'cue_sneaky': 'Sneaky Pete', 'cue_carbonio': 'Carbone', 'cue_avorio': 'Ivoire'}, 'es': {'cue': 'Taco', 'cue_acero': 'Arce', 'cue_ebano': 'Ebano', 'cue_palissandro': 'Palisandro', 'cue_sneaky': 'Sneaky Pete', 'cue_carbonio': 'Carbono', 'cue_avorio': 'Marfil'}, 'ja': {'cue': 'キュー', 'cue_acero': 'メープル', 'cue_ebano': 'エボニー', 'cue_palissandro': 'ローズウッド', 'cue_sneaky': 'スニーキーピート', 'cue_carbonio': 'カーボン', 'cue_avorio': 'アイボリー'}}
for _l, _d in STECCA_TESTI.items():
    TESTI.setdefault(_l, {}).update(_d)

# i nomi delle stecche nuove
_NOMI_STECCHE = (
    ("cue_zaffiro", "Sapphire", "Zaffiro"), ("cue_rubino", "Ruby", "Rubino"),
    ("cue_smeraldo", "Emerald", "Smeraldo"),
    ("cue_oro_nero", "Black Gold", "Oro nero"),
    ("cue_bocote", "Bocote", "Bocote"), ("cue_zebrano", "Zebrawood", "Zebrano"),
    ("cue_ciliegio", "Cherry", "Ciliegio"), ("cue_ghiaccio", "Ice", "Ghiaccio"),
    ("cue_lava", "Lava", "Lava"), ("cue_viola", "Amethyst", "Ametista"),
    ("cue_pianoforte", "Piano", "Pianoforte"),
    ("cue_mogano", "Mahogany", "Mogano"), ("cue_wenge", "Wenge", "Wenge"),
    ("cue_titanio", "Titanium", "Titanio"), ("cue_corallo", "Coral", "Corallo"),
    ("cue_oceano", "Ocean", "Oceano"), ("cue_tigre", "Tiger", "Tigre"),
    ("cue_rosa", "Rose", "Rosa"), ("cue_militare", "Army", "Militare"),
    ("cue_arcobaleno", "Rainbow", "Arcobaleno"),
    ("cue_menta", "Mint", "Menta"), ("cue_limone", "Lemon", "Limone"),
    ("cue_lavanda", "Lavender", "Lavanda"), ("cue_pesca", "Peach", "Pesca"),
    ("cue_cielo", "Sky", "Cielo"), ("cue_fragola", "Strawberry", "Fragola"),
    ("cue_turchese", "Turquoise", "Turchese"),
    ("cue_cioccolato", "Chocolate", "Cioccolato"),
    ("cue_neon", "Neon", "Neon"), ("cue_magenta", "Magenta", "Magenta"),
    ("cue_bosco", "Forest", "Bosco"), ("cue_sabbia", "Sand", "Sabbia"),
    ("cue_notte", "Midnight", "Notte"), ("cue_tramonto", "Sunset", "Tramonto"),
    ("cue_ciano", "Cyan", "Ciano"), ("cue_vino", "Wine", "Vino"),
    ("cue_perla", "Pearl", "Perla"), ("cue_rame", "Copper", "Rame"),
    ("cue_scacchi", "Checker", "Scacchi"), ("cue_cobalto", "Cobalt", "Cobalto"),
    ("cue_giada", "Jade", "Giada"), ("cue_bubblegum", "Bubblegum",
                                      "Gomma da masticare"),
    ("cue_fumo", "Smoke", "Fumo"), ("cue_sole", "Sun", "Sole"),
    ("cue_avorio", "Ivory", "Avorio"), ("cue_ambra", "Amber", "Ambra"),
    ("cue_bronzo", "Bronze", "Bronzo"),
    ("cue_ossidiana", "Obsidian", "Ossidiana"),
    ("cue_platino", "Platinum", "Platino"))
for _l, _d in (("en", {"t_saved": "Tournament in progress",
                       "t_continue": "Continue", "t_new": "New tournament",
                       "t_choose": "Choose your tournament",
                       "crests": "Crests", "cr_classici": "classic",
                       "cr_moderni": "modern"}),
               ("it", {"t_saved": "Torneo in corso",
                       "t_continue": "Continua", "t_new": "Nuovo torneo",
                       "t_choose": "Scegli il torneo",
                       "crests": "Stemmi", "cr_classici": "classici",
                       "cr_moderni": "moderni"})):
    TESTI.setdefault(_l, {}).update(_d)
for _l, _d in (("en", {"balls": "Balls", "set_classico": "Classic",
                       "set_pastello": "Pastel", "set_neon": "Neon", "set_nere": "Black", "set_club2": "Club 2", "set_legend": "The Legend", "set_marmo": "Marble Dark", "set_marmo_chiaro": "Marble Light", "set_continental": "Continental",
                       "set_retro": "Vintage", "set_doppia": "Twin Line",
                       "set_zigzag": "Zigzag", "set_bersaglio": "Target",
                       "set_scacchi": "Checkered", "set_pro": "Pro",
                       "set_perla": "Pearl", "set_notte": "Night",
                       "set_club": "Club", "set_blu": "Blue", "set_verde": "Green", "set_classico_nero": "Classic Black", "set_blu_nero": "Blue Black", "set_verde_nero": "Green Black", "set_bi_marmo": "Marble White", "set_bi_marmo_nero": "Marble Black", "set_black": "Black", "set_marmo_bianco": "Marble White", "set_marmo_nero": "Marble Black", "bb_visit": "%s - second visit",
                       "set_bianco": "White", "set_ambra": "Amber",
                       "pir_aiuto": "RIGHT CLICK / %s / RB: choose ball"}),
               ("it", {"balls": "Palle", "set_classico": "Classico",
                       "set_pastello": "Pastello", "set_neon": "Neon", "set_nere": "Nere", "set_club2": "Club 2", "set_legend": "The Legend", "set_marmo": "Marmo scuro", "set_marmo_chiaro": "Marmo chiaro", "set_continental": "Continental",
                       "set_retro": "Vintage", "set_doppia": "Doppia riga",
                       "set_zigzag": "Zig-zag", "set_bersaglio": "Bersaglio",
                       "set_scacchi": "Scacchi", "set_pro": "Pro",
                       "set_perla": "Perla", "set_notte": "Notte",
                       "set_club": "Club", "set_blu": "Blu", "set_verde": "Verde", "set_classico_nero": "Classico Black", "set_blu_nero": "Blu Black", "set_verde_nero": "Verde Black", "set_bi_marmo": "Marmo Bianco", "set_bi_marmo_nero": "Marmo Nero", "set_black": "Black", "set_marmo_bianco": "Marmo Bianco", "set_marmo_nero": "Marmo Nero",
                       "bb_visit": "%s - seconda visita",
                       "set_bianco": "Bianco", "set_ambra": "Ambra",
                       "pir_aiuto": "TASTO DESTRO / %s / RB: scegli la palla"})):
    TESTI.setdefault(_l, {}).update(_d)
# i nomi delle discipline, delle famiglie e dei tipi di palle
_NOMI_GIOCHI = {
    "en": ("8-Ball", "9-Ball", "Snooker", "5-Pins", "Blackball", "10-Ball",
           "6-Red Snooker", "Goriziana", "Russian Pyramid",
           ("Pool", "Snooker", "Pins")),
    "it": ("8-Ball", "9-Ball", "Snooker", "5 Birilli", "Blackball", "10-Ball",
           "Snooker a 6 rosse", "Goriziana", "Piramide russa",
           ("Pool", "Snooker", "Birilli")),
    "fr": ("8-Ball", "9-Ball", "Snooker", "5 Quilles", "Blackball", "10-Ball",
           "Snooker a 6 rouges", "Goriziana", "Pyramide russe",
           ("Pool", "Snooker", "Quilles")),
    "es": ("8-Ball", "9-Ball", "Snooker", "5 Bolos", "Blackball", "10-Ball",
           "Snooker de 6 rojas", "Goriziana", "Piramide rusa",
           ("Pool", "Snooker", "Bolos")),
}
for _l, _v in _NOMI_GIOCHI.items():
    _d = dict(("g_%d" % i, n) for i, n in enumerate(_v[:9]))
    _d.update(("cat_%d" % i, n) for i, n in enumerate(_v[9]))
    _d.update({"tp_pool": "Pool", "tp_snooker": "Snooker",
               "tp_blackball": "Blackball",
               "tp_birilli": _v[9][2], "tp_piramide": _v[8]})
    TESTI.setdefault(_l, {}).update(_d)
for _k, _en, _it in _NOMI_STECCHE:
    TESTI.setdefault("en", {})[_k] = _en
    TESTI.setdefault("it", {})[_k] = _it


def T(chiave):
    """La frase nella lingua scelta. Se manca, quella inglese."""
    d = TESTI.get(CFG.get("lingua", "en"), TESTI["en"])
    return d.get(chiave, TESTI["en"].get(chiave, chiave))


# ------------------------------------------------------- le impostazioni

CONFIG = os.path.join(DATI, "biliardo_config.json")
CFG = {"lingua": "en", "panno": -1, "bordo": -1, "nomi": ["", ""],
       "musica": 20,                     # volume della musica nel menu
       "musica_gioco": 20,               # e al tavolo, lo stesso: se no
                                         # non si scopre che c'e
       "effetti": 100,                   # volumi in percentuale
       "livello": 1,                     # bravura del computer, 0..3
       "torneo_record": 0,               # il livello piu' alto raggiunto
       "bandiere": ["it", "gb"],         # il paese dei due giocatori
       "stecca": 0,
       "stecche_vinte": 0,
       "stecca2": -1,                    # quella del giocatore 2
       "avversario": "",                 # contro il computer: chi, o a caso
       "soldi": 0,                       # il portafoglio
       "stecche_mie": [0],               # le stecche comprate
       "gessi": {"blu": 1},              # i cubetti ancora da aprire
       "gesso_tipo": "blu",              # il gessetto che si usa
       "cubo": 0,                        # gli usi rimasti nel cubetto aperto
       "cubo_tipo": "blu",
       "cubo2": 0,                       # il cubetto aperto del giocatore 2
       "cubo2_tipo": "blu",
       "avanzi": {},                     # cubetti aperti messi da parte               # incontri di torneo vinti                      # quale stecca, fra quelle disegnate
       "risoluzione": [1280, 820],       # si applica alla riapertura
       "tempo": 0,                       # secondi per tirare, 0 = niente
       "match": 1,                       # frame per partita: 1, 3, 5, 7
       "tavoli": {},                     # livello -> [panno, legno] scelti a mano
       "comandi": "mouse",               # mouse, tastiera o pad
       "palle": {},                      # il set di palle, per gioco
       "stemmi": "classici",             # gli stemmi dei tornei
       "tasti": {},                      # i tasti cambiati a mano
       "pieno": False}                   # tutto schermo, col tasto F11


PRIMA_VOLTA = [True]        # non c'era ancora un file di impostazioni


def carica_config():
    try:
        with open(CONFIG, "r") as f:
            d = json.load(f)
        for k in CFG:
            if k in d:
                CFG[k] = d[k]
        PRIMA_VOLTA[0] = False
    except (IOError, ValueError):
        pass
    # chi aveva gia' sbloccato stecche vincendo i tornei se le tiene
    vinte = int(CFG.get("stecche_vinte", 0) or 0)
    if vinte > 0 and len(CFG.get("stecche_mie") or []) <= 1:
        CFG["stecche_mie"] = list(range(1 + vinte))
    # una lingua che non c'e' piu' (il giapponese) torna all'inglese
    if CFG.get("lingua") not in [c for c, _ in LINGUE]:
        CFG["lingua"] = "en"


def tavolo_di_partenza():
    """Alla prima apertura si gioca sul tavolo di casa, verde e ciliegio,
    non su uno a caso. "A caso" resta nelle impostazioni per chi lo
    vuole, ma se lo sceglie lui. Va chiamata dopo prepara_texture, che
    prima gli elenchi sono vuoti."""
    if not PRIMA_VOLTA[0]:
        return
    if PANNI:
        CFG["panno"] = _quale(PANNI, TAVOLO_CASA[0])
    if BORDI:
        CFG["bordo"] = _quale(BORDI, TAVOLO_CASA[1])


def salva_config():
    try:
        with open(CONFIG, "w") as f:
            json.dump(CFG, f, indent=2)
    except IOError:
        pass


def a_caso_o_fisso(chiave, quanti, attuale):
    """Quale panno o quale bordo per la partita che comincia: quello
    fissato nelle impostazioni, o uno a caso diverso da quello di adesso."""
    i = CFG.get(chiave, -1)
    if 0 <= i < quanti:
        return i
    scelte = [k for k in range(quanti) if k != attuale]
    return random.choice(scelte if scelte else range(quanti))


# ------------------------------------------------------------- il menu


def sfondo_menu(sc, palla_grossa, tinta=None):
    musica_menu()
    sc.blit(fondo(tinta), (0, 0))
    # una luce dall'alto, come la lampada sopra un tavolo da biliardo
    alone = pygame.Surface((WIN_W, WIN_H), pygame.SRCALPHA)
    for i in range(26):
        r = s(620 - i * 22)
        a = 3 + i // 4
        pygame.draw.ellipse(alone, (120, 175, 225, a),
                            pygame.Rect(WIN_W // 2 - r, s(120) - r // 3,
                                        r * 2, r))
    sc.blit(alone, (0, 0))
    if palla_grossa is not None:
        sc.blit(palla_grossa,
                palla_grossa.get_rect(center=(WIN_W // 2, s(196))))
    aiuto_menu(sc)


# Il logo: un gruppetto di palle invece di una sola. Ognuna e' girata di
# poco per conto suo, se no i numeri sono tutti perfettamente in faccia e
# si vede che sono lo stesso disegno ripetuto.
LOGO_PALLE = [
    (12,  -54, -40, 42,  0.16),
    (9,  -110,  22, 40, -0.30),
    (3,   104,  26, 42,  0.26),
    (8,    18,   6, 62, -0.08),
]


# ------------------------------------------------------------ il logo
#
# Lo stemma del gioco, disegnato: niente palle, un sigillo da circolo.
# Due anelli d'oro, l'alloro ai lati, due stecche incrociate e sopra la
# corona; in mezzo un rombo come i segni sulla sponda. Si disegna al
# triplo e si rimpicciolisce, cosi' le curve vengono lisce.
ORO_LOGO = (214, 176, 92)
ORO_LUCE = (246, 220, 150)
ORO_OMBRA = (140, 104, 44)
AVORIO = (246, 242, 230)


def _foglia(sup, c, cx, cy, lungo, largo, ang, col):
    """Una foglia d'alloro: un'ellisse girata."""
    f = pygame.Surface((int(lungo), int(largo)), pygame.SRCALPHA)
    pygame.draw.ellipse(f, col, f.get_rect())
    f = pygame.transform.rotate(f, ang)
    sup.blit(f, f.get_rect(center=(int(cx), int(cy))))


def logo_elegante(alto):
    SU = 3
    D = alto * SU
    sup = pygame.Surface((D, D), pygame.SRCALPHA)
    c = D / 2.0
    R = D * 0.40
    # il disco scuro dietro, e i due anelli d'oro
    pygame.draw.circle(sup, (10, 30, 28, 235), (int(c), int(c)), int(R))
    pygame.draw.circle(sup, ORO_LOGO, (int(c), int(c)), int(R), int(D * 0.018))
    pygame.draw.circle(sup, ORO_OMBRA, (int(c), int(c)), int(R * 0.86),
                       max(1, int(D * 0.006)))
    # le perline fra i due anelli
    for k in range(36):
        a = math.tau * k / 36.0
        x = c + math.cos(a) * R * 0.93
        y = c + math.sin(a) * R * 0.93
        pygame.draw.circle(sup, ORO_LUCE if k % 3 == 0 else ORO_LOGO,
                           (int(x), int(y)), max(2, int(D * 0.006)))
    # l'alloro: due rami che salgono dal basso ai lati
    for lato in (-1, 1):
        # il gambo: un arco sottile appena fuori dall'anello
        punti = []
        for k in range(24):
            t = k / 23.0
            a = math.radians(90 + lato * (22 + t * 100))
            punti.append((c + math.cos(a) * R * 1.07,
                          c + math.sin(a) * R * 1.07))
        pygame.draw.lines(sup, ORO_OMBRA, False, punti, max(1, int(D * 0.006)))
        for k in range(11):
            t = k / 10.0
            a = math.radians(90 + lato * (26 + t * 94))
            for fuori in (1.0, -1.0):
                # una foglia fuori e una dentro, inclinate verso l'alto
                rr = R * (1.07 + fuori * 0.055)
                x = c + math.cos(a) * rr
                y = c + math.sin(a) * rr
                tang = a + lato * math.pi / 2.0
                ang = -math.degrees(tang) + lato * fuori * 28
                _foglia(sup, c, x, y, D * 0.068, D * 0.026, ang,
                        ORO_LUCE if (k + (fuori > 0)) % 2 else ORO_LOGO)
    # le due stecche incrociate: il calcio scuro, il fusto d'avorio, il
    # cuoio blu in punta
    for lato in (-1, 1):
        p0 = Vector2(c + lato * R * 0.62, c + R * 0.62)       # calcio
        p1 = Vector2(c - lato * R * 0.58, c - R * 0.58)       # punta
        d = (p1 - p0).normalize()
        n = Vector2(-d.y, d.x)
        lung = (p1 - p0).length()
        for a, b, col, r0, r1 in ((0.0, 0.42, ORO_OMBRA, 0.030, 0.024),
                                  (0.42, 0.46, ORO_LUCE, 0.024, 0.023),
                                  (0.46, 0.97, AVORIO, 0.023, 0.013),
                                  (0.97, 1.0, (60, 110, 170), 0.013, 0.013)):
            pa, pb = p0 + d * lung * a, p0 + d * lung * b
            ra, rb = D * r0, D * r1
            pygame.draw.polygon(sup, col, [pa + n * ra, pb + n * rb,
                                           pb - n * rb, pa - n * ra])
    # il rombo in mezzo, come i segni sulla sponda, e la palla bianca
    rombo = [(c, c - R * 0.30), (c + R * 0.17, c), (c, c + R * 0.30),
             (c - R * 0.17, c)]
    pygame.draw.polygon(sup, ORO_LOGO, rombo)
    pygame.draw.polygon(sup, ORO_LUCE, rombo, max(1, int(D * 0.006)))
    pygame.draw.circle(sup, AVORIO, (int(c), int(c)), int(R * 0.11))
    pygame.draw.circle(sup, ORO_OMBRA, (int(c), int(c)), int(R * 0.11),
                       max(1, int(D * 0.004)))
    # la corona in cima, appoggiata sull'anello
    cy = c - R * 1.02
    w = R * 0.42
    base = [(c - w, cy + w * 0.35), (c + w, cy + w * 0.35)]
    punte = [(c - w, cy + w * 0.35), (c - w * 1.05, cy - w * 0.35),
             (c - w * 0.5, cy + w * 0.02), (c, cy - w * 0.55),
             (c + w * 0.5, cy + w * 0.02), (c + w * 1.05, cy - w * 0.35),
             (c + w, cy + w * 0.35)]
    pygame.draw.polygon(sup, ORO_LOGO, punte)
    pygame.draw.polygon(sup, ORO_LUCE, punte, max(1, int(D * 0.005)))
    pygame.draw.rect(sup, ORO_OMBRA, pygame.Rect(int(c - w), int(cy + w * 0.3),
                                                 int(w * 2), int(w * 0.22)))
    for x, y in ((c - w * 1.05, cy - w * 0.35), (c, cy - w * 0.55),
                 (c + w * 1.05, cy - w * 0.35)):
        pygame.draw.circle(sup, AVORIO, (int(x), int(y)), int(D * 0.012))
    return pygame.transform.smoothscale(sup, (alto, alto))


def scritta_logo(sc, cx, cy, k=1.0):
    """Il nome del gioco sotto lo stemma: "Classic" in corsivo d'oro e
    POOL in maiuscole con le grazie, larghe, fra due fili d'oro. Con k
    si rimpicciolisce tutto insieme, per la riga in cima al tavolo."""
    def m(v):
        return max(1, int(round(s(v) * k)))
    chiave = ("logo_serif", m(46))
    serif = FONTS.get(chiave)
    if serif is None:
        serif = pygame.font.SysFont(
            "didot,bodoni72,baskerville,hoeflertext,georgia,"
            "timesnewroman,liberationserif,dejavuserif", m(46))
        FONTS[chiave] = serif
    chiave = ("logo_corsivo", m(42))
    corsivo = FONTS.get(chiave)
    if corsivo is None:
        corsivo = carattere_elegante(m(42)) or FONTS["titolo"]
        FONTS[chiave] = corsivo
    lettere = [serif.render(ch, True, AVORIO) for ch in "POOL"]
    spazio = m(16)
    largo = sum(l.get_width() for l in lettere) + spazio * (len(lettere) - 1)
    x = cx - largo // 2
    for l in lettere:
        sc.blit(l, l.get_rect(midleft=(x, cy + m(18))))
        x += l.get_width() + spazio
    # i fili d'oro ai lati di POOL
    for lato in (-1, 1):
        x0 = cx + lato * (largo // 2 + m(14))
        x1 = cx + lato * (largo // 2 + m(74))
        pygame.draw.line(sc, ORO_LOGO, (x0, cy + m(18)), (x1, cy + m(18)),
                         max(1, m(1)))
        pygame.draw.circle(sc, ORO_LOGO, (x1, cy + m(18)), max(2, m(3)))
    c = corsivo.render("Classic", True, ORO_LUCE)
    sc.blit(c, c.get_rect(center=(cx, cy - m(22))))



def palla_da_menu(num=8, raggio=74.0):
    """Il mucchietto di palle che fa da logo."""
    if not HA_NUMPY or M_FACCIA is None:
        return None
    larg = s(300)
    alt = s(190)
    sup = pygame.Surface((larg, alt), pygame.SRCALPHA)
    for n, dx, dy, r, ang in LOGO_PALLE:
        r = s(r)
        M = _rot((0.0, 0.0, 1.0), ang) @ M_FACCIA
        M = _rot((0.0, 1.0, 0.0), ang * 0.5) @ M
        pal = rendi_sfera(n, M, float(r), 0.5, 0.5)
        if pal is None:
            continue
        cx = larg // 2 + s(dx)
        cy = alt // 2 + s(dy)
        d = r * 2 + s(8)
        ombra = pygame.Surface((d, d), pygame.SRCALPHA)
        pygame.draw.circle(ombra, (0, 0, 0, 90), (d // 2, d // 2), r)
        sup.blit(ombra, ombra.get_rect(center=(cx + s(4), cy + s(7))))
        sup.blit(pal, pal.get_rect(center=(cx, cy)))
    return sup


# Come e' fatta la parte destra di una riga, contando dal centro della
# finestra: prima il quadretto della texture, poi la freccia, poi il nome
# in mezzo, poi l'altra freccia. Sono posti fissi, cosi' un nome lungo non
# sposta piu' niente.
ANTE_X = s(20)
FRECCIA_SX = s(74)
VALORE_X = s(164)
FRECCIA_DX = s(254)
VALORE_MAX = s(150)     # oltre questa larghezza il nome rimpicciolisce
RIGA_W = s(520)         # quanto e' larga una riga di menu
RIGA_MEZZO = RIGA_W // 2


# l'oro dei sottotitoli e dei valori nei menu
ORO_SOTTO = (206, 172, 96)
ORO_SCELTA = (250, 212, 118)


def disegna_voci(sc, voci, sel, font, small, y0, passo, frecce=False,
                 ante=None, rosse=None, porte=None):
    """Una lista di righe: a sinistra l'etichetta, a destra il valore.
    Con frecce=True la riga scelta si porta dietro un < e un > su cui si
    puo' cliccare, se no col mouse si potrebbe solo aumentare."""
    tic_menu(tuple(et for et, _ in voci), sel)
    rett = []
    for i, (et, val) in enumerate(voci):
        y = y0 + i * passo
        acceso = (i == sel)
        allarme = bool(rosse) and i in rosse
        col = (255, 255, 255) if acceso else (196, 200, 208)
        if allarme:
            col = (240, 96, 96)
        if acceso:
            alta = passo - s(8)
            b = pygame.Surface((RIGA_W, alta), pygame.SRCALPHA)
            b.fill((255, 255, 255, 18))
            sc.blit(b, (WIN_W // 2 - RIGA_MEZZO, y - alta // 2))
            pygame.draw.rect(sc, COL_GIOC[0],
                             (WIN_W // 2 - RIGA_MEZZO, y - alta // 2,
                              max(1, s(3)), alta))
        # le voci dei menu col carattere elegante, come i titoli
        t = FONTS.get("elegante_voce", font).render(tit_el(et), True, col)
        sc.blit(t, t.get_rect(midleft=(WIN_W // 2 - s(232), y)))
        if val is not None:
            # le scelte in oro: piu' acceso sulla riga scelta
            cv = ORO_SCELTA if acceso else ORO_SOTTO
            if allarme:
                cv = (240, 96, 96)
            v = small.render(val, True, cv)
            if frecce and v.get_width() > VALORE_MAX:
                v = FONTS["mini"].render(val, True, cv)
            if frecce:
                sc.blit(v, v.get_rect(center=(WIN_W // 2 + VALORE_X, y)))
                # le porte non si girano, ci si entra: niente freccette
                if acceso and not (porte and i in porte):
                    for x, segno in ((WIN_W // 2 + FRECCIA_SX, "<"),
                                     (WIN_W // 2 + FRECCIA_DX, ">")):
                        f = font.render(segno, True, cv)
                        sc.blit(f, f.get_rect(center=(x, y)))
            else:
                sc.blit(v, v.get_rect(midright=(WIN_W // 2 + s(236), y)))
        if ante and i in ante and ante[i] is not None:
            q = ante[i]
            r = q.get_rect(center=(WIN_W // 2 + ANTE_X, y))
            sc.blit(q, r)
            pygame.draw.rect(sc, (70, 74, 84), r.inflate(s(2), s(2)),
                             max(1, s(1)))
        rett.append(pygame.Rect(WIN_W // 2 - RIGA_MEZZO, y - passo // 2,
                                RIGA_W, passo))
    return rett


# Le discipline. Per ora si gioca solo a palla 8: le altre stanno nel
# menu con scritto "presto" e non si aprono, cosi' il giro del menu e'
# gia' quello definitivo e non cambia piu' quando arrivano.
GIOCHI = (("8-Ball", True),
          ("9-Ball", True),
          ("Snooker", True),
          ("5-Pins", True),
          ("Blackball", True),
          ("10-Ball", True),
          ("6-Red Snooker", True),
          ("Goriziana", True),
          ("Russian Pyramid", True))
# l'ordine nel menu: i pool insieme, poi gli snooker, poi i birilli
ORDINE_GIOCHI = (0, 1, 5, 4, 8, 2, 6, 3, 7)
GIOCO = [0]             # la disciplina scelta adesso


# Il menu principale per famiglie: pool, snooker e birilli, e dentro
# ognuna le sue discipline. Otto righe di fila erano troppe.
def nome_categoria(i):
    return T("cat_%d" % i)


def nome_gioco(g):
    """Il nome della disciplina nella lingua scelta."""
    return T("g_%d" % g)


CATEGORIE = (("Pool", (0, 1, 5, 4, 8)),
             ("Snooker", (2, 6)),
             ("Pins", (3, 7)))


def schermata_menu(sc, clock, logo):
    """Il primo menu: prima la famiglia, poi la disciplina. Ritorna
    "gioca" quando se n'e' scelta una, se no "settings" o "quit"."""
    # tre piani: il menu principale (None), le famiglie ("fam") e i
    # giochi di una famiglia (il suo numero)
    categoria = None
    sel = 0
    rett = []

    def voci_ora():
        if categoria is None:
            return [T("games"), T("rules"), T("shop"), T("bag"),
                    T("settings"), T("quit")]
        if categoria == "fam":
            return [nome_categoria(i) for i in range(len(CATEGORIE))] + [
                T("back")]
        return [nome_gioco(g) for g in CATEGORIE[categoria][1]] + [T("back")]

    def indietro():
        nonlocal categoria, sel
        if categoria == "fam":
            categoria, sel = None, 0
        elif categoria is not None:
            sel, categoria = categoria, "fam"

    def scelta(i):
        nonlocal categoria, sel
        if categoria is None:
            if i == 0:
                categoria, sel = "fam", 0
                return None
            return ("regole", "negozio", "borsa", "settings", "quit")[i - 1]
        if categoria == "fam":
            if i < len(CATEGORIE):
                categoria, sel = i, 0
            else:
                indietro()
            return None
        giochi = CATEGORIE[categoria][1]
        if i < len(giochi):
            GIOCO[0] = giochi[i]
            return "gioca"
        indietro()
        return None

    while True:
        clock.tick(60)
        mouse = mouse_gioco()
        voci = voci_ora()
        n = len(voci)
        for ev in eventi():
            if ev.type == pygame.QUIT:
                return "quit"
            if ev.type == pygame.KEYDOWN:
                if ev.key in (pygame.K_DOWN, pygame.K_s):
                    sel = (sel + 1) % n
                if ev.key in (pygame.K_UP, pygame.K_w):
                    sel = (sel - 1) % n
                if ev.key in (pygame.K_RETURN, pygame.K_KP_ENTER,
                              pygame.K_SPACE):
                    q = scelta(sel)
                    if q:
                        return q
                    break
                if ev.key == pygame.K_ESCAPE:
                    if categoria is None:
                        return "quit"
                    indietro()
                    break
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                for i, r in enumerate(rett):
                    if r.collidepoint(mouse):
                        q = scelta(i)
                        if q:
                            return q
                        break
        voci = voci_ora()
        sel = min(sel, len(voci) - 1)

        font, grande, small = FONTS["font"], FONTS["grande"], FONTS["small"]
        sfondo_menu(sc, logo)
        scritta_logo(sc, WIN_W // 2, s(340))
        sotto = ("" if categoria is None else T("sub_disc")
                 if categoria == "fam" else nome_categoria(categoria))
        t = small.render(sotto, True, ORO_SOTTO)
        sc.blit(t, t.get_rect(center=(WIN_W // 2, s(396))))

        rett = disegna_voci(sc, [(v, None) for v in voci], sel, font, small,
                            s(448), s(40) if len(voci) > 7 else
                            s(46) if len(voci) > 6 else s(52))
        for i, r in enumerate(rett):
            if MOUSE_VIVO[0] and r.collidepoint(mouse):
                sel = i
        presenta()


# ----------------------------------------------------------- le regole
#
# Le regole di ogni disciplina, come le applica il gioco. Una riga vuota
# stacca un paragrafo; una riga che comincia con "- " e' un punto.
REGOLE = {
    "en": {
        0: """Two players, 15 numbered balls and the cue ball.
- Balls 1 to 7 are solids, 9 to 15 are stripes, the 8 is black.
- The table is open until someone pots a ball: that group becomes theirs, the other goes to the opponent.
- You must hit one of your own balls first. After contact a ball must be potted or any ball must reach a cushion.
- Pot a ball of your group and you keep shooting; miss and the turn passes.
- Foul (no contact, wrong ball first, cue ball potted, no cushion): your opponent gets ball in hand anywhere.
- When your group is cleared you play the 8. Pot it legally and you win.
- Pot the 8 early, or with the cue ball, and you lose the frame.""",
        1: """Nine balls in a diamond, the 1 in front and the 9 in the middle.
- You must always hit the lowest numbered ball on the table first.
- Any ball potted on a legal shot keeps you at the table.
- Pot the 9 on a legal shot, even with a combination, and you win.
- Foul (no contact, lowest ball not hit first, cue ball potted, no cushion): ball in hand anywhere for the opponent. A 9 potted on a foul comes back on the spot.""",
        5: """Ten balls in a triangle, the 1 in front and the 10 in the middle.
- Same rules as 9-Ball: always hit the lowest ball first.
- Any ball potted on a legal shot keeps you at the table.
- Pot the 10 on a legal shot, even with a combination, and you win.
- Foul: ball in hand anywhere for the opponent. A 10 potted on a foul comes back on the spot.""",
        4: """The English pub game: 7 reds, 7 yellows, the black and the cue ball, no numbers.
- Like 8-Ball: the first colour you pot is yours, then you clear it and pot the black.
- You must hit one of your colour first.
- After a foul the opponent has ball in hand and TWO visits: if they miss the first shot, they shoot again.
- Pot the black early, or with the cue ball, and you lose the frame.""",
        8: """Russian pyramid, free version: 15 numbered white balls and the red, slightly bigger than pool balls.
- The break is played with the red, from behind the line.
- After the break you can strike ANY ball: choose it with right click, the change key (C) or X on the controller. The chosen ball has a gold ring.
- Every ball that drops counts, including the ball you struck if it hit another ball first.
- Pot a ball and you keep shooting. The first to 8 balls wins.
- Foul (no contact, or nothing potted and no ball reaching a cushion): the balls potted return to the spot, you give back one of your balls, and the opponent gets ball in hand behind the line.""",
        2: """15 reds worth 1 point and six colours: yellow 2, green 3, brown 4, blue 5, pink 6, black 7.
- You must pot a red first, then a colour, then a red again, and so on. Colours come back on their spot while reds are left.
- When the reds are gone, the colours are potted in order from yellow to black.
- A colour potted returns to its own spot; if it is taken, to the highest free spot.
- Foul: the opponent gets at least 4 points, or the value of the ball involved if higher.
- Miss: if you don't really try to hit the ball on, the opponent can make you play again from the same position. Three misses in a row when not snookered lose the frame.
- Free ball: after a foul that leaves you snookered, you can play any ball as the ball on.
- The highest score wins the frame.""",
        6: """Snooker with 6 reds instead of 15: shorter frames, same rules.
- Red first, then a colour, then a red again; with the reds gone, the colours in order.
- Fouls, misses and free ball work as in normal snooker.
- The highest score wins the frame.""",
        3: """The Italian game without pockets: 5 pins in the middle, the white, the yellow and the small red ball.
- Each player has their own ball and must hit the opponent's ball first.
- Points come from pins knocked down by the opponent's ball or by the red: white pin 2, red pin with others 4, red pin alone 10.
- Hitting the red ball after the opponent's ball scores extra points.
- Pins knocked down by your own ball go to the opponent. Not hitting the opponent's ball first is a foul: the opponent scores.
- The pins are set up again after every shot. First to 60 wins.""",
        7: """Goriziana: like 5-Pins but with 9 pins in a diamond, the red one in the middle.
- Hit the opponent's ball first; pins knocked down by it or by the red score for you.
- White pin 2, red pin with others 4, red pin alone 10. Pins knocked by your own ball go to the opponent.
- The pins are set up again after every shot. First to 120 wins.""",
    },
    "it": {
        0: """Due giocatori, 15 palle numerate e la bianca.
- Dall'1 al 7 sono le piene, dal 9 al 15 le mezze, l'8 e' la nera.
- Il tavolo e' aperto finche' qualcuno imbuca: quel gruppo diventa suo, l'altro va all'avversario.
- Devi colpire per prima una palla tua. Dopo il contatto deve entrare una palla o una palla deve toccare una sponda.
- Imbuchi una tua e continui; sbagli e passa il turno.
- Fallo (niente contatto, palla sbagliata, bianca in buca, nessuna sponda): l'avversario ha la bianca in mano dove vuole.
- Finito il gruppo si gioca l'8: imbucata regolarmente, vinci.
- Imbuchi l'8 prima del tempo, o insieme alla bianca, e perdi il frame.""",
        1: """Nove palle a rombo, l'1 davanti e il 9 in mezzo.
- Devi colpire sempre per prima la palla col numero piu' basso.
- Ogni palla imbucata con un tiro regolare ti fa continuare.
- Imbuchi il 9 con un tiro regolare, anche di combinazione, e vinci.
- Fallo (niente contatto, non la piu' bassa per prima, bianca in buca, nessuna sponda): bianca in mano all'avversario. Il 9 entrato su fallo torna sul punto.""",
        5: """Dieci palle a triangolo, l'1 davanti e il 10 in mezzo.
- Come il 9-Ball: si colpisce sempre per prima la piu' bassa.
- Ogni palla imbucata con un tiro regolare ti fa continuare.
- Imbuchi il 10 con un tiro regolare, anche di combinazione, e vinci.
- Fallo: bianca in mano all'avversario. Il 10 entrato su fallo torna sul punto.""",
        4: """Il biliardo dei pub inglesi: 7 rosse, 7 gialle, la nera e la bianca, senza numeri.
- Come l'8-Ball: il primo colore che imbuchi e' tuo, lo finisci e poi imbuchi la nera.
- Devi colpire per prima una palla del tuo colore.
- Dopo un fallo l'avversario ha la bianca in mano e DUE visite: se sbaglia il primo tiro, tira ancora.
- Imbuchi la nera prima del tempo, o insieme alla bianca, e perdi il frame.""",
        8: """La piramide russa, versione libera: 15 palle bianche numerate e la rossa, un po' piu' grosse di quelle del pool.
- Si spacca con la rossa, da dietro la linea.
- Dopo la spaccata si puo' tirare con QUALSIASI palla: la scegli col tasto destro, col tasto cambia (C) o con X sul joystick. La palla scelta ha il cerchio dorato.
- Vale ogni palla che entra, anche quella con cui hai tirato se prima ne ha toccata un'altra.
- Se imbuchi continui. Vince chi arriva prima a 8 palle.
- Fallo (niente contatto, oppure non entra niente e nessuna palla tocca una sponda): le palle entrate tornano sul punto, restituisci una delle tue e l'avversario ha la palla in mano da dietro la linea.""",
        2: """15 rosse da 1 punto e sei colori: giallo 2, verde 3, marrone 4, blu 5, rosa 6, nero 7.
- Si imbuca prima una rossa, poi un colore, poi di nuovo una rossa e cosi' via. Finche' ci sono rosse i colori tornano sul loro punto.
- Finite le rosse, i colori si imbucano in ordine dal giallo al nero.
- Il colore torna sul suo punto; se e' occupato, sul punto libero di valore piu' alto.
- Fallo: all'avversario almeno 4 punti, o il valore della palla coinvolta se e' di piu'.
- Miss: se non provi davvero a colpire la palla giusta, l'avversario puo' farti ritirare dalla stessa posizione. Tre miss di fila senza essere snookerati fanno perdere il frame.
- Free ball: dopo un fallo che ti lascia snookerato puoi giocare qualunque palla come se fosse quella giusta.
- Vince il frame chi fa piu' punti.""",
        6: """Lo snooker con 6 rosse invece di 15: frame piu' corti, stesse regole.
- Prima una rossa, poi un colore, poi di nuovo una rossa; finite le rosse, i colori in ordine.
- Falli, miss e free ball come nello snooker normale.
- Vince il frame chi fa piu' punti.""",
        3: """Il biliardo all'italiana senza buche: 5 birilli in mezzo, la bianca, la gialla e il pallino rosso.
- Ognuno ha la sua bilia e deve colpire per prima quella dell'avversario.
- Fanno punto i birilli buttati giu' dalla bilia avversaria o dal pallino: birillo bianco 2, rosso insieme ad altri 4, rosso da solo 10.
- Colpire il pallino dopo la bilia avversaria da' punti in piu'.
- I birilli buttati giu' dalla propria bilia vanno all'avversario. Non colpire per prima la bilia avversaria e' fallo: segna l'altro.
- I birilli si rimettono in piedi dopo ogni tiro. Vince chi arriva a 60.""",
        7: """La goriziana: come il 5 birilli ma con 9 birilli a rombo, il rosso in mezzo.
- Si colpisce per prima la bilia avversaria; i birilli buttati giu' da lei o dal pallino segnano per te.
- Birillo bianco 2, rosso insieme ad altri 4, rosso da solo 10. Quelli presi dalla tua bilia vanno all'avversario.
- I birilli si rimettono in piedi dopo ogni tiro. Vince chi arriva a 120.""",
    },
}


def testo_regole(disc):
    lingua = CFG.get("lingua", "en")
    d = REGOLE.get(lingua, REGOLE["en"])
    return d.get(disc, REGOLE["en"].get(disc, ""))


def _a_capo(testo, font, largo):
    """Il testo spezzato in righe che stanno nella larghezza data. I
    punti che vanno a capo rientrano sotto il loro testo."""
    righe = []
    for par in testo.split("\n"):
        if not par.strip():
            righe.append(("", 0))
            continue
        punto = par.startswith("- ")
        rientro = font.size("- ")[0] if punto else 0
        parole = par.split(" ")
        riga = ""
        prima = True
        for p in parole:
            prova = (riga + " " + p) if riga else p
            spazio = largo - (0 if prima else rientro)
            if font.size(prova)[0] <= spazio:
                riga = prova
            else:
                righe.append((riga, 0 if prima else rientro))
                riga, prima = p, False
        righe.append((riga, 0 if prima else rientro))
    return righe


def pagina_regole(sc, clock, logo, disc):
    """Una disciplina: il nome in alto e le regole sotto, da scorrere
    con le frecce o la rotella se non ci stanno."""
    font, small = FONTS["font"], FONTS["small"]
    largo = s(820)
    righe = _a_capo(testo_regole(disc), small, largo)
    passo = small.get_height() + s(6)
    alto_vista = WIN_H - s(260)
    massimo = max(0, len(righe) * passo - alto_vista)
    giu = 0
    while True:
        clock.tick(60)
        for ev in eventi():
            if ev.type == pygame.QUIT:
                return "quit"
            if ev.type == pygame.KEYDOWN:
                if ev.key in (pygame.K_ESCAPE, pygame.K_RETURN,
                              pygame.K_KP_ENTER, pygame.K_SPACE,
                              pygame.K_BACKSPACE):
                    return "su"
                if ev.key in (pygame.K_DOWN, pygame.K_s):
                    giu = min(massimo, giu + passo * 3)
                if ev.key in (pygame.K_UP, pygame.K_w):
                    giu = max(0, giu - passo * 3)
            if ev.type == pygame.MOUSEWHEEL:
                giu = max(0, min(massimo, giu - ev.y * passo * 2))
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                return "su"
        sfondo_menu(sc, None)
        t = FONTS["elegante"].render(tit_el(nome_gioco(disc)), True, (236, 216, 164))
        sc.blit(t, t.get_rect(center=(WIN_W // 2, s(90))))
        area = pygame.Rect(WIN_W // 2 - largo // 2, s(160), largo,
                           alto_vista)
        vecchio = sc.get_clip()
        sc.set_clip(area)
        y = area.top - giu
        for testo, rientro in righe:
            if testo:
                col = (226, 228, 234)
                if testo.startswith("- ") and not rientro:
                    q = small.render("-", True, (232, 190, 90))
                    sc.blit(q, (area.left, y))
                    testo_r = small.render(testo[2:], True, col)
                    sc.blit(testo_r, (area.left + small.size("- ")[0], y))
                else:
                    q = small.render(testo, True, col)
                    sc.blit(q, (area.left + rientro, y))
            y += passo
        sc.set_clip(vecchio)
        nota = FONTS["mini"].render(T("rg_back"), True, (150, 156, 168))
        sc.blit(nota, nota.get_rect(center=(WIN_W // 2, WIN_H - s(60))))
        presenta()


def schermata_regole(sc, clock, logo):
    """Le regole: prima la famiglia, poi la disciplina, poi la pagina."""
    categoria = None
    sel = 0
    rett = []
    while True:
        clock.tick(60)
        mouse = mouse_gioco()
        if categoria is None:
            voci = [nome_categoria(i) for i in range(len(CATEGORIE))] + [T("back")]
        else:
            voci = [nome_gioco(g) for g in CATEGORIE[categoria][1]] \
                + [T("back")]
        n = len(voci)
        entra = None
        for ev in eventi():
            if ev.type == pygame.QUIT:
                return "quit"
            if ev.type == pygame.KEYDOWN:
                if ev.key in (pygame.K_DOWN, pygame.K_s):
                    sel = (sel + 1) % n
                if ev.key in (pygame.K_UP, pygame.K_w):
                    sel = (sel - 1) % n
                if ev.key in (pygame.K_RETURN, pygame.K_KP_ENTER,
                              pygame.K_SPACE):
                    entra = sel
                if ev.key == pygame.K_ESCAPE:
                    entra = n - 1
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                for i, r in enumerate(rett):
                    if r.collidepoint(mouse):
                        entra = i
        if entra is not None:
            if entra == n - 1:                  # indietro
                if categoria is None:
                    return "menu"
                sel, categoria = categoria, None
                continue
            if categoria is None:
                categoria, sel = entra, 0
                continue
            if pagina_regole(sc, clock, logo,
                             CATEGORIE[categoria][1][entra]) == "quit":
                return "quit"
            continue
        font, grande, small = FONTS["font"], FONTS["grande"], FONTS["small"]
        sfondo_menu(sc, logo)
        t = FONTS["elegante"].render(tit_el(T("rules")), True, (240, 240, 244))
        sc.blit(t, t.get_rect(center=(WIN_W // 2, s(336))))
        sotto = (T("rg_sub") if categoria is None
                 else nome_categoria(categoria))
        t = small.render(sotto, True, ORO_SOTTO)
        sc.blit(t, t.get_rect(center=(WIN_W // 2, s(396))))
        rett = disegna_voci(sc, [(v, None) for v in voci], sel, font, small,
                            s(448), s(52))
        for i, r in enumerate(rett):
            if MOUSE_VIVO[0] and r.collidepoint(mouse):
                sel = i
        presenta()


for _l, _d in (("en", {"rules": "Rules", "rg_sub": "how each game is played",
                       "rg_back": "arrows or wheel to scroll  -  ENTER or ESC to go back"}),
               ("it", {"rules": "Regole", "rg_sub": "come si gioca ogni disciplina",
                       "rg_back": "frecce o rotella per scorrere  -  INVIO o ESC per tornare"})):
    TESTI.setdefault(_l, {}).update(_d)



# Le parole nuove in francese e spagnolo, e le regole.
_FR = {
    "l_club": "Joueur de club", "l_maestro": "Maitre",
    "t_saved": "Tournoi en cours", "t_continue": "Continuer",
    "t_new": "Nouveau tournoi", "t_choose": "Choisis ton tournoi",
    "crests": "Blasons", "cr_classici": "classiques", "cr_moderni": "modernes",
    "balls": "Billes", "set_classico": "Classique", "set_pastello": "Pastel",
    "set_neon": "Neon", "set_nere": "Noires", "set_club2": "Club 2", "set_legend": "The Legend", "set_marmo": "Marbre sombre", "set_marmo_chiaro": "Marbre clair", "set_continental": "Continental", "set_retro": "Vintage",
    "set_doppia": "Double ligne",
    "set_zigzag": "Zigzag", "set_bersaglio": "Cible",
    "set_scacchi": "Damier", "set_pro": "Pro", "set_perla": "Perle",
    "set_notte": "Nuit", "set_club": "Club", "set_blu": "Bleu", "set_verde": "Vert", "set_classico_nero": "Classique Noir", "set_blu_nero": "Bleu Noir", "set_verde_nero": "Vert Noir", "set_bi_marmo": "Marbre Blanc", "set_bi_marmo_nero": "Marbre Noir", "set_black": "Noir", "set_marmo_bianco": "Marbre Blanc", "set_marmo_nero": "Marbre Noir", "set_bianco": "Blanc",
    "set_ambra": "Ambre", "bb_visit": "%s - deuxieme visite",
    "pir_aiuto": "CLIC DROIT / %s / RB : choisir la bille",
    "cue_zaffiro": "Saphir", "cue_rubino": "Rubis", "cue_smeraldo": "Emeraude",
    "cue_oro_nero": "Or noir", "cue_bocote": "Bocote",
    "cue_zebrano": "Zebrano", "cue_ciliegio": "Merisier",
    "cue_ghiaccio": "Glace", "cue_lava": "Lave", "cue_viola": "Amethyste",
    "cue_pianoforte": "Piano", "cue_mogano": "Acajou", "cue_wenge": "Wenge",
    "cue_titanio": "Titane", "cue_corallo": "Corail", "cue_oceano": "Ocean",
    "cue_tigre": "Tigre", "cue_rosa": "Rose", "cue_militare": "Militaire",
    "cue_arcobaleno": "Arc-en-ciel", "cue_menta": "Menthe",
    "cue_limone": "Citron", "cue_lavanda": "Lavande", "cue_pesca": "Peche",
    "cue_cielo": "Ciel", "cue_fragola": "Fraise", "cue_turchese": "Turquoise",
    "cue_cioccolato": "Chocolat", "cue_neon": "Neon", "cue_magenta": "Magenta",
    "cue_bosco": "Foret", "cue_sabbia": "Sable", "cue_notte": "Minuit",
    "cue_tramonto": "Coucher de soleil", "cue_ciano": "Cyan",
    "cue_vino": "Vin", "cue_perla": "Perle", "cue_rame": "Cuivre",
    "cue_scacchi": "Damier", "cue_cobalto": "Cobalt", "cue_giada": "Jade",
    "cue_bubblegum": "Chewing-gum", "cue_fumo": "Fumee", "cue_sole": "Soleil",
    "cue_avorio": "Ivoire", "cue_ambra": "Ambre", "cue_bronzo": "Bronze",
    "cue_ossidiana": "Obsidienne", "cue_platino": "Platine",
    "rules": "Regles", "rg_sub": "comment se joue chaque discipline",
    "rg_back": "fleches ou molette pour defiler  -  ENTREE ou ECHAP pour revenir",
    "p_comandi": "Commandes", "input": "Jouer avec", "in_mouse": "souris",
    "in_tastiera": "clavier", "in_pad": "manette",
    "k_aim_l": "Viser a gauche", "k_aim_r": "Viser a droite",
    "k_fine": "Visee fine (maintenir)", "k_shoot": "Tirer (maintenir)",
    "k_ball_u": "Bille en main haut", "k_ball_d": "Bille en main bas",
    "k_top": "Effet haut", "k_back": "Effet bas", "k_left": "Effet gauche",
    "k_right": "Effet droit", "k_clear": "Enlever l'effet",
    "k_reset": "Touches d'origine", "k_switch": "Changer de bille (pyramide)",
    "k_press": "Appuie sur une touche   (ECHAP annule)",
    "aiuto_mouse": "%s/%s effet haut-bas   %s/%s lateral   %s/%s visee fine   %s enlever     ECHAP pause",
    "aiuto_tast": "%s maintenir pour tirer   %s/%s viser   %s fin   %s/%s/%s/%s effet   %s enlever     ECHAP pause",
    "aiuto_pad": "stick G viser   LB fin   A/RT maintenir pour tirer   stick D effet   Y enlever     START pause",
    "pa_aim": "viser", "pa_fine": "fin", "pa_shoot": "maintenir pour tirer",
    "pa_spin": "effet", "pa_clear": "enlever l'effet", "pa_pause": "START pause",
    "pa_select": "choisir", "pa_back": "retour",
}
_ES = {
    "l_club": "Jugador de club", "l_maestro": "Maestro",
    "t_saved": "Torneo en curso", "t_continue": "Continuar",
    "t_new": "Nuevo torneo", "t_choose": "Elige tu torneo",
    "crests": "Escudos", "cr_classici": "clasicos", "cr_moderni": "modernos",
    "balls": "Bolas", "set_classico": "Clasico", "set_pastello": "Pastel",
    "set_neon": "Neon", "set_nere": "Negras", "set_club2": "Club 2", "set_legend": "The Legend", "set_marmo": "Marmol oscuro", "set_marmo_chiaro": "Marmol claro", "set_continental": "Continental", "set_retro": "Vintage",
    "set_doppia": "Doble linea",
    "set_zigzag": "Zigzag", "set_bersaglio": "Diana",
    "set_scacchi": "Ajedrez", "set_pro": "Pro", "set_perla": "Perla",
    "set_notte": "Noche", "set_club": "Club", "set_blu": "Azul", "set_verde": "Verde", "set_classico_nero": "Clasico Negro", "set_blu_nero": "Azul Negro", "set_verde_nero": "Verde Negro", "set_bi_marmo": "Marmol Blanco", "set_bi_marmo_nero": "Marmol Negro", "set_black": "Negro", "set_marmo_bianco": "Marmol Blanco", "set_marmo_nero": "Marmol Negro", "set_bianco": "Blanco",
    "set_ambra": "Ambar", "bb_visit": "%s - segunda visita",
    "pir_aiuto": "CLIC DERECHO / %s / RB: elegir la bola",
    "cue_zaffiro": "Zafiro", "cue_rubino": "Rubi", "cue_smeraldo": "Esmeralda",
    "cue_oro_nero": "Oro negro", "cue_bocote": "Bocote",
    "cue_zebrano": "Zebrano", "cue_ciliegio": "Cerezo",
    "cue_ghiaccio": "Hielo", "cue_lava": "Lava", "cue_viola": "Amatista",
    "cue_pianoforte": "Piano", "cue_mogano": "Caoba", "cue_wenge": "Wengue",
    "cue_titanio": "Titanio", "cue_corallo": "Coral", "cue_oceano": "Oceano",
    "cue_tigre": "Tigre", "cue_rosa": "Rosa", "cue_militare": "Militar",
    "cue_arcobaleno": "Arcoiris", "cue_menta": "Menta",
    "cue_limone": "Limon", "cue_lavanda": "Lavanda", "cue_pesca": "Melocoton",
    "cue_cielo": "Cielo", "cue_fragola": "Fresa", "cue_turchese": "Turquesa",
    "cue_cioccolato": "Chocolate", "cue_neon": "Neon", "cue_magenta": "Magenta",
    "cue_bosco": "Bosque", "cue_sabbia": "Arena", "cue_notte": "Medianoche",
    "cue_tramonto": "Atardecer", "cue_ciano": "Cian", "cue_vino": "Vino",
    "cue_perla": "Perla", "cue_rame": "Cobre", "cue_scacchi": "Ajedrez",
    "cue_cobalto": "Cobalto", "cue_giada": "Jade", "cue_bubblegum": "Chicle",
    "cue_fumo": "Humo", "cue_sole": "Sol",
    "cue_avorio": "Marfil", "cue_ambra": "Ambar", "cue_bronzo": "Bronce",
    "cue_ossidiana": "Obsidiana", "cue_platino": "Platino",
    "rules": "Reglas", "rg_sub": "como se juega cada disciplina",
    "rg_back": "flechas o rueda para desplazar  -  ENTER o ESC para volver",
    "p_comandi": "Controles", "input": "Jugar con", "in_mouse": "raton",
    "in_tastiera": "teclado", "in_pad": "mando",
    "k_aim_l": "Apuntar a la izquierda", "k_aim_r": "Apuntar a la derecha",
    "k_fine": "Punteria fina (mantener)", "k_shoot": "Tirar (mantener)",
    "k_ball_u": "Bola en mano arriba", "k_ball_d": "Bola en mano abajo",
    "k_top": "Efecto alto", "k_back": "Efecto bajo", "k_left": "Efecto izquierdo",
    "k_right": "Efecto derecho", "k_clear": "Quitar efecto",
    "k_reset": "Teclas de fabrica", "k_switch": "Cambiar bola (piramide)",
    "k_press": "Pulsa una tecla   (ESC cancela)",
    "aiuto_mouse": "%s/%s efecto alto-bajo   %s/%s lateral   %s/%s punteria fina   %s quitar     ESC pausa",
    "aiuto_tast": "%s mantener para tirar   %s/%s apuntar   %s fino   %s/%s/%s/%s efecto   %s quitar     ESC pausa",
    "aiuto_pad": "stick izq. apuntar   LB fino   A/RT mantener para tirar   stick der. efecto   Y quitar     START pausa",
    "pa_aim": "apuntar", "pa_fine": "fino", "pa_shoot": "mantener para tirar",
    "pa_spin": "efecto", "pa_clear": "quitar efecto", "pa_pause": "START pausa",
    "pa_select": "elegir", "pa_back": "volver",
}
for _l, _d in (("fr", _FR), ("es", _ES)):
    TESTI.setdefault(_l, {}).update(_d)

# la legenda dei comandi di joystick e mouse
for _l, _d in (
        ("en", {"c_aim": "Aim", "c_spin": "Spin", "c_ball": "Ball in hand",
                "c_pause": "Pause", "c_select": "Select (menus)",
                "c_back": "Back (menus)", "c_mouse": "MOUSE",
                "c_drag": "LEFT BUTTON, drag back", "c_right": "RIGHT CLICK"}),
        ("it", {"c_aim": "Mira", "c_spin": "Effetto", "c_ball": "Bianca in mano",
                "c_pause": "Pausa", "c_select": "Scegli (menu)",
                "c_back": "Indietro (menu)", "c_mouse": "MOUSE",
                "c_drag": "TASTO SINISTRO, tira indietro",
                "c_right": "TASTO DESTRO"}),
        ("fr", {"c_aim": "Viser", "c_spin": "Effet", "c_ball": "Bille en main",
                "c_pause": "Pause", "c_select": "Choisir (menus)",
                "c_back": "Retour (menus)", "c_mouse": "SOURIS",
                "c_drag": "BOUTON GAUCHE, tirer en arriere",
                "c_right": "CLIC DROIT"}),
        ("es", {"c_aim": "Apuntar", "c_spin": "Efecto", "c_ball": "Bola en mano",
                "c_pause": "Pausa", "c_select": "Elegir (menus)",
                "c_back": "Volver (menus)", "c_mouse": "RATON",
                "c_drag": "BOTON IZQUIERDO, tirar hacia atras",
                "c_right": "CLIC DERECHO"})):
    TESTI.setdefault(_l, {}).update(_d)

REGOLE["fr"] = {
    0: """Deux joueurs, 15 billes numerotees et la blanche.
- Les billes 1 a 7 sont les pleines, 9 a 15 les rayees, la 8 est noire.
- La table est ouverte jusqu'a ce que quelqu'un empoche : ce groupe devient le sien, l'autre va a l'adversaire.
- Tu dois toucher d'abord une de tes billes. Apres le contact une bille doit entrer ou une bille doit toucher une bande.
- Tu empoches une des tiennes et tu continues ; tu rates et la main passe.
- Faute (pas de contact, mauvaise bille, blanche empochee, pas de bande) : l'adversaire a la bille en main ou il veut.
- Ton groupe fini, tu joues la 8 : empochee regulierement, tu gagnes.
- La 8 empochee trop tot, ou avec la blanche, te fait perdre la manche.""",
    1: """Neuf billes en losange, la 1 devant et la 9 au milieu.
- Tu dois toujours toucher d'abord la bille au plus petit numero.
- Toute bille empochee sur un coup regulier te fait continuer.
- Empoche la 9 sur un coup regulier, meme en combinaison, et tu gagnes.
- Faute : bille en main pour l'adversaire. La 9 entree sur faute revient sur le point.""",
    5: """Dix billes en triangle, la 1 devant et la 10 au milieu.
- Comme au 9-Ball : toujours la plus petite d'abord.
- Toute bille empochee sur un coup regulier te fait continuer.
- Empoche la 10 sur un coup regulier, meme en combinaison, et tu gagnes.
- Faute : bille en main pour l'adversaire. La 10 entree sur faute revient sur le point.""",
    4: """Le billard des pubs anglais : 7 rouges, 7 jaunes, la noire et la blanche, sans numeros.
- Comme au 8-Ball : la premiere couleur empochee est la tienne, tu la finis puis tu empoches la noire.
- Tu dois toucher d'abord une bille de ta couleur.
- Apres une faute l'adversaire a la bille en main et DEUX visites : s'il rate le premier coup, il rejoue.
- La noire empochee trop tot, ou avec la blanche, te fait perdre la manche.""",
    8: """La pyramide russe, version libre : 15 billes blanches numerotees et la rouge, un peu plus grosses qu'au pool.
- La casse se joue avec la rouge, derriere la ligne.
- Apres la casse tu peux jouer avec N'IMPORTE QUELLE bille : choisis-la avec le clic droit, la touche changer (C) ou X sur la manette. La bille choisie a un cercle dore.
- Chaque bille qui entre compte, meme celle que tu as jouee si elle a touche une autre bille avant.
- Tu empoches et tu continues. Le premier a 8 billes gagne.
- Faute (pas de contact, ou rien n'entre et aucune bille ne touche une bande) : les billes entrees reviennent sur le point, tu rends une des tiennes et l'adversaire a la bille en main derriere la ligne.""",
    2: """15 rouges a 1 point et six couleurs : jaune 2, vert 3, marron 4, bleu 5, rose 6, noir 7.
- On empoche une rouge, puis une couleur, puis une rouge et ainsi de suite. Tant qu'il y a des rouges, les couleurs reviennent sur leur point.
- Les rouges finies, les couleurs s'empochent dans l'ordre du jaune au noir.
- Une couleur revient sur son point ; s'il est occupe, sur le point libre de plus grande valeur.
- Faute : au moins 4 points a l'adversaire, ou la valeur de la bille concernee si elle est plus haute.
- Miss : si tu n'essaies pas vraiment de toucher la bonne bille, l'adversaire peut te faire rejouer de la meme position. Trois miss de suite sans etre snooker font perdre la manche.
- Free ball : apres une faute qui te laisse snooker, tu peux jouer n'importe quelle bille comme bonne bille.
- Le plus haut score gagne la manche.""",
    6: """Le snooker a 6 rouges au lieu de 15 : manches plus courtes, memes regles.
- Une rouge, puis une couleur, puis une rouge ; les rouges finies, les couleurs dans l'ordre.
- Fautes, miss et free ball comme au snooker normal.
- Le plus haut score gagne la manche.""",
    3: """Le billard italien sans poches : 5 quilles au milieu, la blanche, la jaune et la petite rouge.
- Chacun a sa bille et doit toucher d'abord celle de l'adversaire.
- Marquent les quilles renversees par la bille adverse ou par la rouge : quille blanche 2, rouge avec d'autres 4, rouge seule 10.
- Toucher la rouge apres la bille adverse donne des points en plus.
- Les quilles renversees par ta propre bille vont a l'adversaire. Ne pas toucher d'abord la bille adverse est une faute : l'autre marque.
- Les quilles sont relevees apres chaque coup. Le premier a 60 gagne.""",
    7: """La goriziana : comme le 5 quilles mais avec 9 quilles en losange, la rouge au milieu.
- On touche d'abord la bille adverse ; les quilles renversees par elle ou par la rouge marquent pour toi.
- Quille blanche 2, rouge avec d'autres 4, rouge seule 10. Celles renversees par ta bille vont a l'adversaire.
- Les quilles sont relevees apres chaque coup. Le premier a 120 gagne.""",
}
REGOLE["es"] = {
    0: """Dos jugadores, 15 bolas numeradas y la blanca.
- Las bolas 1 a 7 son lisas, 9 a 15 rayadas, la 8 es negra.
- La mesa esta abierta hasta que alguien mete una bola: ese grupo es suyo, el otro para el rival.
- Debes tocar primero una de tus bolas. Tras el contacto debe entrar una bola o una bola debe tocar una banda.
- Metes una tuya y sigues; fallas y pasa el turno.
- Falta (sin contacto, bola equivocada, blanca metida, sin banda): el rival tiene bola en mano donde quiera.
- Terminado tu grupo juegas la 8: metida bien, ganas.
- Meter la 8 antes de tiempo, o junto a la blanca, te hace perder la partida.""",
    1: """Nueve bolas en rombo, la 1 delante y la 9 en el centro.
- Siempre debes tocar primero la bola de numero mas bajo.
- Cualquier bola metida con un tiro legal te hace seguir.
- Mete la 9 con un tiro legal, incluso en combinacion, y ganas.
- Falta: bola en mano para el rival. La 9 metida en falta vuelve al punto.""",
    5: """Diez bolas en triangulo, la 1 delante y la 10 en el centro.
- Como el 9-Ball: siempre primero la mas baja.
- Cualquier bola metida con un tiro legal te hace seguir.
- Mete la 10 con un tiro legal, incluso en combinacion, y ganas.
- Falta: bola en mano para el rival. La 10 metida en falta vuelve al punto.""",
    4: """El billar de los pubs ingleses: 7 rojas, 7 amarillas, la negra y la blanca, sin numeros.
- Como el 8-Ball: el primer color que metes es tuyo, lo terminas y luego metes la negra.
- Debes tocar primero una bola de tu color.
- Tras una falta el rival tiene bola en mano y DOS visitas: si falla el primer tiro, vuelve a tirar.
- Meter la negra antes de tiempo, o junto a la blanca, te hace perder la partida.""",
    8: """La piramide rusa, version libre: 15 bolas blancas numeradas y la roja, un poco mas grandes que las del pool.
- Se abre con la roja, desde detras de la linea.
- Tras la apertura puedes tirar con CUALQUIER bola: elige con clic derecho, la tecla cambiar (C) o X en el mando. La bola elegida tiene un circulo dorado.
- Cuenta cada bola que entra, incluso la que has tirado si antes toco otra.
- Si metes, sigues. Gana el primero que llega a 8 bolas.
- Falta (sin contacto, o no entra nada y ninguna bola toca banda): las bolas metidas vuelven al punto, devuelves una de las tuyas y el rival tiene bola en mano detras de la linea.""",
    2: """15 rojas de 1 punto y seis colores: amarilla 2, verde 3, marron 4, azul 5, rosa 6, negra 7.
- Se mete una roja, luego un color, luego otra roja y asi. Mientras haya rojas, los colores vuelven a su punto.
- Sin rojas, los colores se meten en orden de la amarilla a la negra.
- Un color vuelve a su punto; si esta ocupado, al punto libre de mayor valor.
- Falta: al rival al menos 4 puntos, o el valor de la bola implicada si es mayor.
- Miss: si no intentas de verdad tocar la bola correcta, el rival puede hacerte repetir desde la misma posicion. Tres miss seguidos sin estar snookereado pierden la partida.
- Free ball: tras una falta que te deja snookereado puedes jugar cualquier bola como la correcta.
- Gana la partida quien hace mas puntos.""",
    6: """El snooker con 6 rojas en lugar de 15: partidas mas cortas, mismas reglas.
- Una roja, luego un color, luego otra roja; sin rojas, los colores en orden.
- Faltas, miss y free ball como en el snooker normal.
- Gana la partida quien hace mas puntos.""",
    3: """El billar italiano sin troneras: 5 bolos en el centro, la blanca, la amarilla y la bolita roja.
- Cada uno tiene su bola y debe tocar primero la del rival.
- Puntuan los bolos tirados por la bola rival o por la roja: bolo blanco 2, rojo con otros 4, rojo solo 10.
- Tocar la roja despues de la bola rival da puntos extra.
- Los bolos tirados por tu propia bola van para el rival. No tocar primero la bola rival es falta: puntua el otro.
- Los bolos se levantan despues de cada tiro. Gana el primero que llega a 60.""",
    7: """La goriziana: como el 5 bolos pero con 9 bolos en rombo, el rojo en el centro.
- Se toca primero la bola rival; los bolos tirados por ella o por la roja puntuan para ti.
- Bolo blanco 2, rojo con otros 4, rojo solo 10. Los tirados por tu bola van para el rival.
- Los bolos se levantan despues de cada tiro. Gana el primero que llega a 120.""",
}


def schermata_modo(sc, clock, logo):
    """Scelta la disciplina, qui si sceglie come giocarci: da soli contro
    il computer, in due, o il torneo."""
    voci = [T("free"), T("cpu"), T("tournament"), T("back")]
    chiavi = ("free", "cpu", "torneo", "menu")
    sel = 0
    rett = []
    while True:
        clock.tick(60)
        mouse = mouse_gioco()
        for ev in eventi():
            if ev.type == pygame.QUIT:
                return "quit"
            if ev.type == pygame.KEYDOWN:
                if ev.key in (pygame.K_DOWN, pygame.K_s):
                    sel = (sel + 1) % len(voci)
                if ev.key in (pygame.K_UP, pygame.K_w):
                    sel = (sel - 1) % len(voci)
                if ev.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                    return chiavi[sel]
                if ev.key == pygame.K_ESCAPE:
                    return "menu"
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                for i, r in enumerate(rett):
                    if r.collidepoint(mouse):
                        return chiavi[i]

        font, grande, small = FONTS["font"], FONTS["grande"], FONTS["small"]
        sfondo_menu(sc, logo)
        t = FONTS["elegante"].render(tit_el(nome_gioco(GIOCO[0])), True, (240, 240, 244))
        sc.blit(t, t.get_rect(center=(WIN_W // 2, s(336))))
        t = small.render(T("sub_mode"), True, ORO_SOTTO)
        sc.blit(t, t.get_rect(center=(WIN_W // 2, s(396))))
        rett = disegna_voci(sc, [(v, None) for v in voci], sel,
                            font, small, s(456), s(56))
        for i, r in enumerate(rett):
            if MOUSE_VIVO[0] and r.collidepoint(mouse):
                sel = i
        presenta()


def volume_riga(chiave):
    v = CFG.get(chiave, 0)
    return T("off") if v <= 0 else "%d%%" % v


def riapri_il_gioco():
    """La risoluzione cambia solo all'avvio, perche' tutte le misure si
    calcolano una volta sola. Invece di scrivere "riavvia il gioco", il
    gioco si riavvia da solo: salva, chiude pygame e riparte con lo
    stesso comando. Se il sistema non lo lascia fare si esce e basta, e
    la risoluzione arrivera' alla prossima apertura."""
    salva_config()
    try:
        pygame.mixer.music.stop()
    except pygame.error:
        pass
    pygame.quit()
    try:
        os.execv(sys.executable, [sys.executable] + sys.argv)
    except (OSError, AttributeError, ValueError):
        sys.exit(0)


def ris_cambiata():
    """Vero se la risoluzione scelta non e' quella con cui stiamo
    girando adesso."""
    w, h = CFG.get("risoluzione", [BASE_W, BASE_H])[:2]
    return (int(w), int(h)) != (WIN_W, WIN_H)


def _ris_scritta():
    """La risoluzione scelta. Se non e' quella in uso lo dice, perche'
    si applica solo riaprendo il gioco."""
    w, h = CFG.get("risoluzione", [BASE_W, BASE_H])[:2]
    return "%d x %d" % (w, h)


# Chi ha fatto la musica. Va scritto, e sta sotto le righe dell'audio.
CREDITI_MUSICA = "Music by Alex Morgan from Pixabay"


def _nome_tex(elenco, chiave):
    k = CFG[chiave]
    if not elenco or k < 0 or k >= len(elenco):
        return T("random")
    return titolo_tex(elenco[k][1])


# ---------------------------------------------------------- i comandi
#
# Tre modi di giocare: col mouse come prima, solo con la tastiera, o col
# joystick. I tasti si possono cambiare dalle impostazioni; quelli che
# non sono stati toccati restano questi.
COMANDI = ("mouse", "tastiera", "pad")
AZIONI = (("mira_sx", "k_aim_l", pygame.K_LEFT),
          ("mira_dx", "k_aim_r", pygame.K_RIGHT),
          ("fine", "k_fine", pygame.K_LSHIFT),
          ("tiro", "k_shoot", pygame.K_SPACE),
          ("palla_su", "k_ball_u", pygame.K_UP),
          ("palla_giu", "k_ball_d", pygame.K_DOWN),
          ("eff_su", "k_top", pygame.K_w),
          ("eff_giu", "k_back", pygame.K_s),
          ("eff_sx", "k_left", pygame.K_a),
          ("eff_dx", "k_right", pygame.K_d),
          ("eff_via", "k_clear", pygame.K_e),
          ("cambia", "k_switch", pygame.K_c),
          ("gesso", "k_chalk", pygame.K_g))
TASTI_BASE = dict((a, k) for a, _, k in AZIONI)
VIETATI = (pygame.K_ESCAPE, pygame.K_F11, pygame.K_F3)
CARICA_T = 1.4          # secondi per arrivare alla potenza piena
GIRO_TAST = 45.0        # gradi al secondo, la mira da tastiera
GIRO_FINE = 1.6         # e col tasto fine tenuto giu'
GIRO_PAD = 110.0        # la levetta tutta di lato
MANO_V = 300.0          # la bianca in mano, pixel al secondo a misura uno
MORTA = 0.18            # la levetta sotto questo non conta


# Niente scelta: comanda l'ultima cosa toccata. Il mouse quando si muove o
# si clicca, la tastiera quando si tira con il suo tasto (frecce, effetto
# e gesso vanno bene anche col mouse), il controller appena lo si usa.
INPUT_ORA = ["mouse"]
FOOTER_VIS = [0.0, 0]   # quanto si vede la fascia dei comandi, e da quando
FOOTER_ORA = [None]     # la fascia di questo giro: alta quanto, di che colore


def modo_comandi():
    m = INPUT_ORA[0]
    return m if m in COMANDI else "mouse"


def segna_input(ev):
    """Guarda un evento vero (non uno fatto dal joystick) e decide chi
    comanda adesso."""
    if ev.type == pygame.MOUSEBUTTONDOWN:
        INPUT_ORA[0] = "mouse"
    elif ev.type == pygame.MOUSEMOTION:
        dx, dy = ev.rel
        if dx * dx + dy * dy >= 9:
            INPUT_ORA[0] = "mouse"
    elif ev.type == pygame.KEYDOWN and not getattr(ev, "dal_pad", False):
        if ev.key == tasto("tiro"):
            INPUT_ORA[0] = "tastiera"
        elif INPUT_ORA[0] == "pad":
            INPUT_ORA[0] = "tastiera"


def segna_pad(ev):
    if ev.type == pygame.CONTROLLERBUTTONDOWN:
        INPUT_ORA[0] = "pad"
    elif ev.type == pygame.CONTROLLERAXISMOTION and abs(ev.value) > 12000:
        INPUT_ORA[0] = "pad"


def tasto(azione):
    try:
        return int(CFG.get("tasti", {}).get(azione, TASTI_BASE[azione]))
    except (TypeError, ValueError):
        return TASTI_BASE[azione]


def giu(azione, tasti=None):
    """Vero se il tasto di quell'azione e' tenuto premuto."""
    tasti = tasti or pygame.key.get_pressed()
    k = tasto(azione)
    try:
        if tasti[k]:
            return True
    except IndexError:
        pass
    # il tasto fine vale con tutti e due gli shift
    if azione == "fine" and k in (pygame.K_LSHIFT, pygame.K_RSHIFT):
        return bool(tasti[pygame.K_LSHIFT] or tasti[pygame.K_RSHIFT])
    return False


def nome_tasto(k):
    if int(k) in (pygame.K_LSHIFT, pygame.K_RSHIFT):
        return "SHIFT"
    n = pygame.key.name(int(k)) or "?"
    return n.upper()


def tasti_cambiati():
    return any(tasto(a) != TASTI_BASE[a] for a in TASTI_BASE)


def aiuto_comandi():
    """La riga d'aiuto: alla piramide prima di tutto come si sceglie la
    palla con cui tirare."""
    riga = _aiuto_comandi()
    if modo_comandi() == "pad":
        riga = riga.replace("START", "X %s     START" % T("pa_chalk"), 1)
    else:
        riga += "     %s %s" % (nome_tasto(tasto("gesso")), T("pa_chalk"))
    if GIOCO[0] == 8:
        riga = T("pir_aiuto") % nome_tasto(tasto("cambia")) + "     " + riga
    return riga


def _aiuto_comandi():
    m = modo_comandi()
    if m == "pad":
        return T("aiuto_pad")
    n = dict((a, nome_tasto(tasto(a))) for a in TASTI_BASE)
    if m == "tastiera":
        return T("aiuto_tast") % (n["tiro"], n["mira_sx"], n["mira_dx"],
                                   n["fine"], n["eff_su"], n["eff_giu"],
                                   n["eff_sx"], n["eff_dx"], n["eff_via"])
    if not tasti_cambiati():
        return T("aiuto")
    return T("aiuto_mouse") % (n["eff_su"], n["eff_giu"], n["eff_sx"],
                                n["eff_dx"], n["mira_sx"], n["mira_dx"],
                                n["eff_via"])


# Il joystick passa per i controller di SDL: cosi' il tasto A e' A su
# qualunque pad, Xbox o PlayStation che sia. Nei menu i suoi tasti
# diventano frecce, invio ed ESC, e i menu non se ne accorgono.
try:
    from pygame._sdl2 import controller as PAD_SDL
except Exception:
    PAD_SDL = None
PADS = {}
PAD_LEVA = {"x": 0, "y": 0}     # dove era la levetta, per i menu
PAD_PRONTO = [False]
MOUSE_VIVO = [False]            # il mouse si e' mosso in questo giro


def pad_avvia():
    if PAD_PRONTO[0] or PAD_SDL is None:
        return
    PAD_PRONTO[0] = True
    try:
        PAD_SDL.init()
        for i in range(PAD_SDL.get_count()):
            pad_apri(i)
    except Exception:
        pass


def pad_apri(i):
    try:
        if PAD_SDL.is_controller(i):
            c = PAD_SDL.Controller(i)
            PADS[c.as_joystick().get_instance_id()] = c
    except Exception:
        pass


def pad():
    """Il primo joystick attaccato, o niente."""
    for c in list(PADS.values()):
        try:
            if c.attached():
                return c
        except Exception:
            pass
    return None


def pad_asse(c, asse):
    try:
        v = c.get_axis(asse) / 32767.0
    except Exception:
        return 0.0
    return 0.0 if abs(v) < MORTA else max(-1.0, min(1.0, v))


def pad_tasto(c, b):
    try:
        return bool(c.get_button(b))
    except Exception:
        return False


def pad_tira(c):
    """Il tiro col joystick: A tenuto, o il grilletto destro."""
    if c is None:
        return False
    try:
        grilletto = c.get_axis(pygame.CONTROLLER_AXIS_TRIGGERRIGHT) / 32767.0
    except Exception:
        grilletto = 0.0
    return pad_tasto(c, pygame.CONTROLLER_BUTTON_A) or grilletto > 0.4


PAD_TASTI = {}
if PAD_SDL is not None:
    PAD_TASTI = {pygame.CONTROLLER_BUTTON_DPAD_UP: pygame.K_UP,
                 pygame.CONTROLLER_BUTTON_DPAD_DOWN: pygame.K_DOWN,
                 pygame.CONTROLLER_BUTTON_DPAD_LEFT: pygame.K_LEFT,
                 pygame.CONTROLLER_BUTTON_DPAD_RIGHT: pygame.K_RIGHT,
                 pygame.CONTROLLER_BUTTON_A: pygame.K_RETURN,
                 pygame.CONTROLLER_BUTTON_B: pygame.K_ESCAPE,
                 pygame.CONTROLLER_BUTTON_START: pygame.K_ESCAPE}


def finto_tasto(k):
    return pygame.event.Event(pygame.KEYDOWN, key=k, mod=0, unicode="",
                              scancode=0, dal_pad=True)


def pad_evento(ev, fuori):
    """Un evento del joystick: se serve lo trasforma in un tasto."""
    if ev.type == pygame.CONTROLLERDEVICEADDED:
        pad_apri(ev.device_index)
    elif ev.type == pygame.CONTROLLERDEVICEREMOVED:
        PADS.pop(getattr(ev, "instance_id", -1), None)
    elif ev.type == pygame.CONTROLLERBUTTONDOWN:
        k = PAD_TASTI.get(ev.button)
        if ev.button == pygame.CONTROLLER_BUTTON_X:
            k = tasto("gesso")          # il gesso sulla stecca
        if ev.button == pygame.CONTROLLER_BUTTON_RIGHTSHOULDER:
            k = tasto("cambia")         # piramide: la palla dopo
        if k is not None:
            fuori.append(finto_tasto(k))
    elif ev.type == pygame.CONTROLLERAXISMOTION and ev.axis in (
            pygame.CONTROLLER_AXIS_LEFTX, pygame.CONTROLLER_AXIS_LEFTY):
        # la levetta nei menu: uno scatto per spinta, non una raffica
        chi = "x" if ev.axis == pygame.CONTROLLER_AXIS_LEFTX else "y"
        v = ev.value / 32767.0
        verso = 1 if v > 0.6 else -1 if v < -0.6 else 0
        if abs(v) < 0.3:
            PAD_LEVA[chi] = 0
        elif verso and verso != PAD_LEVA[chi]:
            PAD_LEVA[chi] = verso
            if chi == "x":
                k = pygame.K_RIGHT if verso > 0 else pygame.K_LEFT
            else:
                k = pygame.K_DOWN if verso > 0 else pygame.K_UP
            fuori.append(finto_tasto(k))


def aspetta_tasto(sc, clock, sotto):
    """Aspetta il tasto nuovo per un comando. ESC lascia com'era."""
    while True:
        clock.tick(60)
        for ev in eventi():
            if ev.type == pygame.QUIT:
                return None
            if ev.type == pygame.KEYDOWN and not getattr(ev, "dal_pad",
                                                         False):
                if ev.key == pygame.K_ESCAPE:
                    return None
                if ev.key not in VIETATI:
                    return ev.key
        sc.blit(sotto, (0, 0))
        velo = pygame.Surface((WIN_W, WIN_H), pygame.SRCALPHA)
        velo.fill((6, 8, 12, 200))
        sc.blit(velo, (0, 0))
        t = FONTS["font"].render(T("k_press"), True, (240, 240, 244))
        sc.blit(t, t.get_rect(center=(WIN_W // 2, WIN_H // 2)))
        presenta()


def cambia_tasto(azione, k):
    """Mette il tasto nuovo. Se lo usava gia' un altro comando, i due si
    scambiano: cosi' non restano mai due comandi sullo stesso tasto."""
    tasti = dict(CFG.get("tasti", {}))
    vecchio = tasto(azione)
    for a in TASTI_BASE:
        if a != azione and tasto(a) == k:
            tasti[a] = vecchio
    tasti[azione] = k
    CFG["tasti"] = dict((a, v) for a, v in tasti.items()
                        if v != TASTI_BASE.get(a))



# Le icone dei tasti del joystick, disegnate bianche: qui si tingono coi
# colori del pad, A verde, B rosso, X blu, Y giallo, e il resto grigio
# come la scritta.
TASTI_GFX = os.path.join(GFX, "tasti")
TINTE_TASTI = {"a": (96, 186, 70), "b": (222, 64, 56), "x": (48, 128, 224),
               "y": (240, 190, 40)}
GRIGIO_AIUTO = (150, 156, 168)
ICONE_TASTO = {}
RIGA_PAD = {}


def icona_tasto(nome, alto):
    chiave = (nome, alto)
    if chiave not in ICONE_TASTO:
        f = os.path.join(TASTI_GFX, nome + ".png")
        q = None
        try:
            q = pygame.image.load(f).convert_alpha()
            q = pygame.transform.smoothscale(
                q, (max(1, int(q.get_width() * alto / float(q.get_height()))),
                    alto))
            # tutte bianche: piu' eleganti delle icone colorate
            q.fill((236, 236, 240, 255), special_flags=pygame.BLEND_RGBA_MULT)
        except (pygame.error, OSError, FileNotFoundError):
            q = None
        ICONE_TASTO[chiave] = q
    return ICONE_TASTO[chiave]


def ICONE_TASTI_OK():
    return os.path.isfile(os.path.join(TASTI_GFX, "a.png"))


RIGA_GIOCO = ((("l",), "pa_aim"), (("lb",), "pa_fine"),
              (("a", "rt"), "pa_shoot"), (("r",), "pa_spin"),
              (("y",), "pa_clear"), (("x",), "pa_chalk"),
              ((), "pa_pause"))
RIGA_MENU = ((("a",), "pa_select"), (("b",), "pa_back"))


def aiuto_menu(sc):
    """Nei menu, col joystick: A per scegliere, B per tornare. La fascia
    compare piano appena tocchi il controller e sparisce piano appena
    torni a mouse o tastiera."""
    if not ICONE_TASTI_OK():
        return
    ora = pygame.time.get_ticks()
    dt = min(0.1, max(0.0, (ora - FOOTER_VIS[1]) / 1000.0))
    FOOTER_VIS[1] = ora
    verso = 1.0 if modo_comandi() == "pad" else -1.0
    FOOTER_VIS[0] = max(0.0, min(1.0, FOOTER_VIS[0] + verso * dt * 4.0))
    if FOOTER_VIS[0] <= 0.0:
        return
    r = riga_pad(FONTS["small"], RIGA_MENU)
    # una fascia scura per tutta la larghezza, alta quanto la riga
    alto = r.get_height() + s(12)
    fascia = pygame.Surface((WIN_W, alto), pygame.SRCALPHA)
    # dello stesso colore del fondo della schermata, appena piu' scuro
    t = TINTA_ORA[0]
    bordo = FONDI_TINTE[t][1] if t in FONDI_TINTE else SFONDO_BORDO
    col_f = tuple(int(v * 0.6) for v in bordo) + (235,)
    fascia.fill(col_f)
    FOOTER_ORA[0] = (alto, col_f, FOOTER_VIS[0])
    fascia.blit(r, r.get_rect(center=(WIN_W // 2, alto // 2)))
    fascia.set_alpha(int(255 * FOOTER_VIS[0]))
    sc.blit(fascia, (0, WIN_H - alto))


def riga_pad(small, voci=RIGA_GIOCO):
    """La riga d'aiuto col joystick: icona del tasto e cosa fa."""
    chiave = (CFG.get("lingua"), small.get_height(), voci)
    if chiave in RIGA_PAD:
        return RIGA_PAD[chiave]
    alto = max(s(16), (small.get_height() + s(8)) // 2 + s(4))
    pezzi = []
    for tasti, testo in voci:
        for i, t in enumerate(tasti):
            if i:
                pezzi.append(small.render("/", True, GRIGIO_AIUTO))
            q = icona_tasto(t, alto)
            pezzi.append(q if q is not None
                         else small.render(t.upper(), True, GRIGIO_AIUTO))
        pezzi.append(small.render(" " + T(testo) + "     ", True,
                                  GRIGIO_AIUTO))
    largo = sum(p.get_width() for p in pezzi)
    riga = pygame.Surface((largo, alto), pygame.SRCALPHA)
    x = 0
    for p in pezzi:
        riga.blit(p, p.get_rect(midleft=(x, alto // 2)))
        x += p.get_width()
    RIGA_PAD[chiave] = riga
    return riga


COMANDI_TESTI = {
    "en": {"p_comandi": "Controls", "input": "Play with",
           "in_mouse": "mouse", "in_tastiera": "keyboard",
           "in_pad": "controller",
           "k_aim_l": "Aim left", "k_aim_r": "Aim right",
           "k_fine": "Fine aim (hold)", "k_shoot": "Shoot (hold)",
           "k_ball_u": "Ball in hand up", "k_ball_d": "Ball in hand down",
           "k_top": "Top spin", "k_back": "Back spin",
           "k_left": "Left spin", "k_right": "Right spin",
           "k_clear": "Clear spin", "k_reset": "Default keys",
           "k_switch": "Change ball (pyramid)",
           "k_press": "Press a key   (ESC cancels)",
           "aiuto_mouse": "%s/%s top-back spin   %s/%s side spin   "
                          "%s/%s fine aim   %s clear spin     ESC pause",
           "aiuto_tast": "%s hold to shoot   %s/%s aim   %s fine   "
                         "%s/%s/%s/%s spin   %s clear     ESC pause",
           "aiuto_pad": "L stick aim   LB fine   A/RT hold to shoot   "
                        "R stick spin   Y clear     START pause",
           "pa_aim": "aim", "pa_fine": "fine", "pa_shoot": "hold to shoot",
           "pa_spin": "spin", "pa_clear": "clear spin",
           "pa_pause": "START pause", "pa_select": "select",
           "pa_back": "back"},
    "it": {"p_comandi": "Comandi", "input": "Gioca con",
           "in_mouse": "mouse", "in_tastiera": "tastiera",
           "in_pad": "joystick",
           "k_aim_l": "Mira a sinistra", "k_aim_r": "Mira a destra",
           "k_fine": "Mira fine (tieni)", "k_shoot": "Tiro (tieni)",
           "k_ball_u": "Bianca in mano su", "k_ball_d": "Bianca in mano giu",
           "k_top": "Effetto alto", "k_back": "Effetto basso",
           "k_left": "Effetto sinistro", "k_right": "Effetto destro",
           "k_clear": "Togli effetto", "k_reset": "Tasti di fabbrica",
           "k_switch": "Cambia palla (piramide)",
           "k_press": "Premi un tasto   (ESC annulla)",
           "aiuto_mouse": "%s/%s effetto alto-basso   %s/%s laterale   "
                          "%s/%s mira fine   %s togli     ESC pausa",
           "aiuto_tast": "%s tieni per tirare   %s/%s mira   %s fine   "
                         "%s/%s/%s/%s effetto   %s togli     ESC pausa",
           "aiuto_pad": "levetta sin. mira   LB fine   A/RT tieni per "
                        "tirare   levetta des. effetto   Y togli     "
                        "START pausa",
           "pa_aim": "mira", "pa_fine": "fine", "pa_shoot": "tieni per tirare",
           "pa_spin": "effetto", "pa_clear": "togli effetto",
           "pa_pause": "START pausa", "pa_select": "scegli",
           "pa_back": "indietro"},
}
for _l, _d in COMANDI_TESTI.items():
    TESTI.setdefault(_l, {}).update(_d)
for _l, _d in (
        ("en", {"unl_title": "New cue unlocked", "st_aim": "Aim",
                "st_power": "Power", "st_spin": "Spin",
                "st_count": "%d of %d cues", "chalk": "CHALK",
                "k_chalk": "Chalk the cue", "shop": "Shop", "games": "Games",
                "p_mouse": "Mouse", "p_pad": "Controller", "p_tastiera": "Keyboard",
                "precision": "PRECISION",
                "wallet": "Wallet: %s", "buy": "Buy", "use": "Use",
                "in_use": "In use", "chalk_row": "Chalk",
                "buy_chalk": "Buy chalk", "no_money": "Not enough money",
                "buy_done": "Cue purchased", "premio": "+%s",
                "ch_info": "%s: %d uses - you have %d",
                "ch_uso": "in use: %s", "ch_grigio": "Grey",
                "ch_blu": "Blue", "ch_rosso": "Red", "ch_verde": "Green",
                "ch_nero": "Black", "ch_bianco": "White",
                "ch_giallo": "Yellow", "ch_viola": "Purple",
                "ch_arancio": "Orange", "ch_oro": "Gold",
                "ch_none": "none", "owned": "Owned",
                "inventory": "Your chalk", "bag": "Bag",
                "all_owned": "You own every cue", "bought": "Purchased",
                "ch_uses": "%d uses per cube", "ch_have": "you have %d",
                "ch_open": "open cube: %d uses left",
                "ch_spare": "spare: %d", "pa_chalk": "chalk"}),
        ("it", {"unl_title": "Nuova stecca sbloccata", "st_aim": "Mira",
                "st_power": "Potenza", "st_spin": "Effetto",
                "st_count": "%d di %d stecche", "chalk": "GESSO",
                "k_chalk": "Gesso sulla stecca", "shop": "Negozio",
                "p_mouse": "Mouse", "p_pad": "Controller", "p_tastiera": "Tastiera",
                "precision": "PRECISIONE",
                "games": "Giochi",
                "wallet": "Portafoglio: %s", "buy": "Compra", "use": "Usa",
                "in_use": "In uso", "chalk_row": "Gessetto",
                "buy_chalk": "Compra gessetto",
                "no_money": "Soldi insufficienti",
                "buy_done": "Stecca acquistata", "premio": "+%s",
                "ch_info": "%s: %d usi - ne hai %d",
                "ch_uso": "in uso: %s", "ch_grigio": "Grigio",
                "ch_blu": "Blu", "ch_rosso": "Rosso", "ch_verde": "Verde",
                "ch_nero": "Nero", "ch_bianco": "Bianco",
                "ch_giallo": "Giallo", "ch_viola": "Viola",
                "ch_arancio": "Arancio", "ch_oro": "Oro",
                "ch_none": "nessuno", "owned": "Tua",
                "inventory": "I tuoi gessetti", "bag": "Borsa",
                "all_owned": "Hai tutte le stecche", "bought": "Acquistato",
                "ch_uses": "%d usi a cubetto", "ch_have": "ne hai %d",
                "ch_open": "cubetto aperto: restano %d usi",
                "ch_spare": "scorta: %d", "pa_chalk": "gesso"}),
        ("fr", {"unl_title": "Nouvelle queue debloquee", "st_aim": "Visee",
                "st_power": "Puissance", "st_spin": "Effet",
                "st_count": "%d sur %d queues", "chalk": "CRAIE",
                "k_chalk": "Craie sur la queue", "shop": "Boutique",
                "p_mouse": "Souris", "p_pad": "Manette", "p_tastiera": "Clavier",
                "precision": "PRECISION",
                "games": "Jeux",
                "wallet": "Porte-monnaie : %s", "buy": "Acheter",
                "use": "Utiliser", "in_use": "Utilisee",
                "chalk_row": "Craie", "buy_chalk": "Acheter une craie",
                "no_money": "Pas assez d'argent",
                "buy_done": "Queue achetee", "premio": "+%s",
                "ch_info": "%s : %d utilisations - tu en as %d",
                "ch_uso": "utilisee : %s", "ch_grigio": "Grise",
                "ch_blu": "Bleue", "ch_rosso": "Rouge", "ch_verde": "Verte",
                "ch_nero": "Noire", "ch_bianco": "Blanche",
                "ch_giallo": "Jaune", "ch_viola": "Violette",
                "ch_arancio": "Orange", "ch_oro": "Doree",
                "ch_none": "aucune", "owned": "A toi",
                "inventory": "Tes craies", "bag": "Sac",
                "all_owned": "Tu as toutes les queues", "bought": "Achete",
                "ch_uses": "%d utilisations par cube",
                "ch_have": "tu en as %d",
                "ch_open": "cube ouvert : %d utilisations",
                "ch_spare": "reserve : %d", "pa_chalk": "craie"}),
        ("es", {"unl_title": "Nuevo taco desbloqueado",
                "st_aim": "Punteria", "st_power": "Potencia",
                "st_spin": "Efecto", "st_count": "%d de %d tacos",
                "chalk": "TIZA", "k_chalk": "Tiza en el taco",
                "shop": "Tienda", "wallet": "Cartera: %s", "buy": "Comprar",
                "p_mouse": "Raton", "p_pad": "Mando", "p_tastiera": "Teclado",
                "precision": "PRECISION",
                "games": "Juegos",
                "use": "Usar", "in_use": "En uso", "chalk_row": "Tiza",
                "buy_chalk": "Comprar tiza",
                "no_money": "Dinero insuficiente",
                "buy_done": "Taco comprado", "premio": "+%s",
                "ch_info": "%s: %d usos - tienes %d",
                "ch_uso": "en uso: %s", "ch_grigio": "Gris",
                "ch_blu": "Azul", "ch_rosso": "Roja", "ch_verde": "Verde",
                "ch_nero": "Negra", "ch_bianco": "Blanca",
                "ch_giallo": "Amarilla", "ch_viola": "Morada",
                "ch_arancio": "Naranja", "ch_oro": "Dorada",
                "ch_none": "ninguna", "owned": "Tuyo",
                "inventory": "Tus tizas", "bag": "Bolsa",
                "all_owned": "Tienes todos los tacos", "bought": "Comprado",
                "ch_uses": "%d usos por cubo", "ch_have": "tienes %d",
                "ch_open": "cubo abierto: quedan %d usos",
                "ch_spare": "reserva: %d", "pa_chalk": "tiza"})):
    TESTI.setdefault(_l, {}).update(_d)
for _k, _en, _it, _fr, _es in NOMI_STECCHE_55:
    for _l, _v in (("en", _en), ("it", _it), ("fr", _fr), ("es", _es)):
        TESTI.setdefault(_l, {})[_k] = _v


def righe_setting(pagina, blocca_tavolo):
    """Le righe di una pagina delle impostazioni: un nome interno, quello
    che si legge e il valore. Il nome interno dice cosa cambiare, cosi'
    non si va piu' per numero di riga e aggiungere una voce non sposta
    niente."""
    if pagina == "audio":
        return [("musica", T("mus_menu"), volume_riga("musica")),
                ("musica_gioco", T("mus_gioco"),
                 volume_riga("musica_gioco")),
                ("effetti", T("effects"), volume_riga("effetti"))]
    if pagina == "regole":
        tempo = (T("off") if CFG.get("tempo", 0) <= 0
                 else "%d s" % CFG["tempo"])
        n = CFG.get("match", 1)
        return [("tempo", T("shotclock"), tempo),
                ("match", T("match"),
                 T("m_uno") if n <= 1 else T("m_best") % n)]
    if pagina == "tavolo":
        # a partita cominciata la stecca e' quella: non si cambia
        righe = [] if DENTRO_PARTITA[0] else [
            ("stecca", T("cue"), T("random")
             if CFG.get("stecca", 0) < 0
             else "%d. %s" % (STECCHE.index(stecca_scelta()) + 1,
                              T(stecca_scelta()[0])))]
        tp = tipo_palle()
        if DENTRO_PARTITA[0]:
            # al tavolo si scorrono solo le palle del gioco in corso
            righe.append(("palle", "%s (%s)" % (T("balls"), T("tp_" + tp)),
                          T(elenco_set(tp)[scelta_palle(tp)][0])))
        else:
            # dal menu si vedono tutte: pool, poi snooker, poi birilli
            righe.append(("palle", T("balls"), "%s  %s" % (
                T("tp_" + tp), T(elenco_set(tp)[scelta_palle(tp)][0]))))
        if not blocca_tavolo:
            righe.append(("panno", T("cloth"), _nome_tex(PANNI, "panno")))
            righe.append(("bordo", T("rails"), _nome_tex(BORDI, "bordo")))
        return righe
    if pagina == "mouse":
        return [("v_mira", T("c_aim"), T("c_mouse")),
                ("v_tiro", T("k_shoot"), T("c_drag")),
                ("v_cambia", T("k_switch"), T("c_right"))]
    if pagina == "pad":
        righe = []
        if True:
            # col joystick i tasti sono fissi: la legenda e basta
            for chiave, testo, val in (
                    ("v_mira", "c_aim", "L STICK / D-PAD"),
                    ("v_fine", "k_fine", "LB"),
                    ("v_tiro", "k_shoot", "A / RT"),
                    ("v_eff", "c_spin", "R STICK"),
                    ("v_via", "k_clear", "Y"),
                    ("v_mano", "c_ball", "L STICK / D-PAD + A"),
                    ("v_cambia", "k_switch", "RB"),
                    ("v_gesso", "k_chalk", "X"),
                    ("v_pausa", "c_pause", "START"),
                    ("v_scegli", "c_select", "A"),
                    ("v_torna", "c_back", "B")):
                righe.append((chiave, T(testo), val))
            return righe
    if pagina == "comandi":
        # mouse, tastiera e controller vanno sempre tutti e tre: qui si
        # vede solo cosa fa ogni tasto, e quelli della tastiera si cambiano
        return [("p_mouse", T("p_mouse"), None),
                ("p_tastiera", T("p_tastiera"), None),
                ("p_pad", T("p_pad"), None)]
    if pagina == "tastiera":
        righe = []
        for a, testo, _ in AZIONI:
            righe.append(("t_" + a, T(testo), nome_tasto(tasto(a))))
        righe.append(("t_base", T("k_reset"), ""))
        return righe
    if pagina == "grafica":
        return [("risoluzione", T("resolution"), _ris_scritta()),
                ("pieno", T("screen"),
                 T("s_pieno") if PIENO else T("s_finestra"))]
    nomi_l = dict(LINGUE)
    return [("lingua", T("language"),
             nomi_l.get(CFG["lingua"], CFG["lingua"])),
            ("p_audio", T("p_audio"), None),
            ("p_regole", T("p_regole"), None),
            ("p_tavolo", T("p_tavolo"), None),
            ("p_grafica", T("p_grafica"), None),
            ("p_comandi", T("p_comandi"), None)]


def cambia_setting(nome, cambia, blocca_tavolo):
    """Gira di un passo il valore di quella riga."""
    if nome == "lingua":
        codici = [c for c, _ in LINGUE]
        i = codici.index(CFG["lingua"]) if CFG["lingua"] in codici else 0
        CFG["lingua"] = codici[(i + cambia) % len(codici)]
        fai_fonts()
    elif nome in ("musica", "musica_gioco", "effetti"):
        CFG[nome] = max(0, min(100, CFG.get(nome, 20) + cambia * 10))
        if nome == "musica":
            # si sente subito, che siamo nel menu
            musica_menu()
    elif nome == "tempo":
        i = TEMPI.index(CFG["tempo"]) if CFG["tempo"] in TEMPI else 0
        CFG["tempo"] = TEMPI[(i + cambia) % len(TEMPI)]
    elif nome == "match":
        i = (MATCH.index(CFG.get("match", 1))
             if CFG.get("match", 1) in MATCH else 0)
        CFG["match"] = MATCH[(i + cambia) % len(MATCH)]
    elif nome == "stecca":
        giro = [-1] + stecche_mie()
        ora = CFG.get("stecca", 0)
        k = giro.index(ora) if ora in giro else len(giro) - 1
        CFG["stecca"] = giro[(k + cambia) % len(giro)]
    elif nome in ("panno", "bordo") and not blocca_tavolo:
        quanti = max(1, len(PANNI if nome == "panno" else BORDI))
        CFG[nome] = CFG[nome] + cambia
        if CFG[nome] >= quanti:
            CFG[nome] = -1
        if CFG[nome] < -1:
            CFG[nome] = quanti - 1
    elif nome == "palle":
        tp = tipo_palle()
        scelta_palle(tp)                    # sistema il vecchio formato
        if DENTRO_PARTITA[0]:
            CFG["palle"][tp] = ((scelta_palle(tp) + cambia)
                                % len(elenco_set(tp)))
        else:
            # un solo giro con tutti i set: finiti quelli di un gioco si
            # passa al gioco dopo. Ognuno tiene la sua scelta.
            tutti = [(t, k) for t in TIPI_PALLE
                     for k in range(len(elenco_set(t)))]
            i = tutti.index((tp, scelta_palle(tp)))
            t, k = tutti[(i + cambia) % len(tutti)]
            # passando oltre un gioco senza fermarsi, quello resta con la
            # scelta che aveva quando si e' aperta la pagina
            if t != tp and tp in PALLE_ERA:
                CFG["palle"][tp] = PALLE_ERA[tp]
            CFG["palle"][t] = k
            PALLE_VISTA[0] = t
        applica_palle()
    elif nome == "comandi":
        i = COMANDI.index(modo_comandi())
        CFG["comandi"] = COMANDI[(i + cambia) % len(COMANDI)]
    elif nome == "stemmi":
        CFG["stemmi"] = ("moderni" if CFG.get("stemmi", "classici")
                         == "classici" else "classici")
        STEMMI.clear()
    elif nome == "pieno":
        # questa si vede subito, non serve riaprire, e si salva adesso
        # cosi' la prossima apertura parte com'e' stata lasciata
        apri_finestra(not PIENO)
        CFG["pieno"] = PIENO
        salva_config()
    elif nome == "risoluzione":
        # si applica alla riapertura: le misure si calcolano una volta
        # sola, all'avvio
        ora = tuple(CFG.get("risoluzione", [BASE_W, BASE_H]))
        elenco = list(RISOLUZIONI)
        i = elenco.index(ora) if ora in elenco else 0
        CFG["risoluzione"] = list(elenco[(i + cambia) % len(elenco)])
        salva_config()


def schermata_setting(sc, clock, logo, blocca_tavolo=False, pagina="radice",
                      puo_riaprire=False):
    """Le impostazioni, divise in pagine: la prima ha la lingua, le tre
    porte - audio, regole, tavolo - e la risoluzione. Dentro ogni porta
    ci sono solo le cose che c'entrano fra loro, cosi' l'elenco resta
    corto e si trova quello che si cerca.

    Nel torneo il panno e il legno non si scelgono: li decide il torneo
    livello per livello, e quelle due righe non ci sono proprio."""
    sel = 0
    rett = []
    if pagina == "tavolo":
        if not DENTRO_PARTITA[0] and PALLE_VISTA[0] is None:
            PALLE_VISTA[0] = tipo_palle(GIOCO[0])
        PALLE_ERA.clear()
        for t in TIPI_PALLE:
            PALLE_ERA[t] = scelta_palle(t)
        applica_palle()         # l'anteprima col set del gioco scelto
    while True:
        clock.tick(60)
        mouse = mouse_gioco()
        righe = righe_setting(pagina, blocca_tavolo)
        voci = [(et, val) for _, et, val in righe]
        voci.append((T("back"), None))
        indietro = len(voci) - 1
        sel = min(sel, indietro)

        font, grande, small = FONTS["font"], FONTS["grande"], FONTS["small"]
        cambia = 0
        entra = False
        for ev in eventi():
            if ev.type == pygame.QUIT:
                return "quit"
            if ev.type == pygame.KEYDOWN:
                if ev.key in (pygame.K_DOWN, pygame.K_s):
                    sel = (sel + 1) % len(voci)
                if ev.key in (pygame.K_UP, pygame.K_w):
                    sel = (sel - 1) % len(voci)
                if ev.key in (pygame.K_RIGHT, pygame.K_d):
                    cambia = 1
                if ev.key in (pygame.K_LEFT, pygame.K_a):
                    cambia = -1
                if ev.key in (pygame.K_RETURN, pygame.K_KP_ENTER,
                              pygame.K_SPACE):
                    if sel == indietro:
                        salva_config()
                        if pagina == "radice" and puo_riaprire \
                                and ris_cambiata():
                            riapri_il_gioco()
                        return "menu" if pagina == "radice" else "su"
                    entra = True
                    cambia = 1
                if ev.key == pygame.K_ESCAPE:
                    salva_config()
                    if pagina == "radice" and puo_riaprire \
                            and ris_cambiata():
                        riapri_il_gioco()
                    return "menu" if pagina == "radice" else "su"
            if ev.type == pygame.MOUSEWHEEL:
                for i, r in enumerate(rett):
                    if r.collidepoint(mouse) and i < indietro:
                        sel = i
                        cambia = 1 if ev.y > 0 else -1
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                for i, r in enumerate(rett):
                    if not r.collidepoint(mouse):
                        continue
                    sel = i
                    if i == indietro:
                        salva_config()
                        if pagina == "radice" and puo_riaprire \
                                and ris_cambiata():
                            riapri_il_gioco()
                        return "menu" if pagina == "radice" else "su"
                    entra = True
                    # meta' destra aumenta, meta' sinistra diminuisce:
                    # la riga e' fatta per essere toccata sulle freccette
                    cambia = 1 if mouse[0] > WIN_W // 2 + VALORE_X else -1

        if cambia and sel < indietro:
            nome = righe[sel][0]
            if nome.startswith("p_"):
                # e' una porta: dentro ci si entra, non si gira
                if entra:
                    dentro = schermata_setting(sc, clock, logo,
                                               blocca_tavolo, nome[2:],
                                               puo_riaprire)
                    if dentro == "quit":
                        return "quit"
                    if dentro == "menu":
                        return "menu"
            elif nome == "t_base":
                if entra:
                    CFG["tasti"] = {}
            elif nome.startswith("t_"):
                # il tasto nuovo si prende premendo invio sulla riga
                if entra:
                    k = aspetta_tasto(sc, clock, sc.copy())
                    if k is not None:
                        cambia_tasto(nome[2:], k)
            else:
                cambia_setting(nome, cambia, blocca_tavolo)

        # Sulla prima pagina il logo del gioco, come nel menu principale;
        # il tavolo col panno e il legno scelti si vede solo nella pagina
        # del tavolo, dove si sceglie. Sulle altre il nome della pagina.
        sfondo_menu(sc, logo if pagina == "radice" else None)
        mini = None
        if pagina == "tavolo":
            vp = (CFG["panno"] if 0 <= CFG["panno"] < len(PANNI)
                  else _quale(PANNI, TAVOLO_CASA[0]))
            vb = (CFG["bordo"] if 0 <= CFG["bordo"] < len(BORDI)
                  else _quale(BORDI, TAVOLO_CASA[1]))
            mini = tavolo_mini(vp, vb)
        if mini is not None:
            r = mini.get_rect(center=(WIN_W // 2, s(214)))
            pygame.draw.rect(sc, (16, 18, 24), r.inflate(s(10), s(10)))
            sc.blit(mini, r)
            pygame.draw.rect(sc, (70, 74, 84), r.inflate(s(10), s(10)),
                             max(1, s(1)))
            sotto_y = r.bottom + s(22)
        else:
            titolo = T("settings_t") if pagina == "radice" \
                else T("p_" + pagina)
            t = FONTS["elegante"].render(tit_el(titolo), True, (240, 240, 244))
            # i comandi hanno tante righe: il titolo sale per fargli posto
            alto_t = (s(84) if pagina in ("tastiera", "pad") else
                      s(326) if pagina == "radice" else s(244))
            sc.blit(t, t.get_rect(center=(WIN_W // 2, alto_t)))
            sotto_y = alto_t + (s(50) if pagina == "radice" else s(56))
        t = small.render(T("sub_set"), True, ORO_SOTTO)
        sc.blit(t, t.get_rect(center=(WIN_W // 2, sotto_y)))

        # l'anteprima della texture scelta, un quadretto accanto al nome
        ante = {}
        for i, (nome, _, _) in enumerate(righe):
            if nome == "panno" and PANNI and 0 <= CFG["panno"] < len(PANNI):
                ante[i] = texture(PANNI[CFG["panno"]][1], (s(34), s(34)))
            elif nome == "bordo" and BORDI and 0 <= CFG["bordo"] < len(BORDI):
                ante[i] = texture(BORDI[CFG["bordo"]][1], (s(34), s(34)))
        porte = set(i for i, (n, _, _) in enumerate(righe)
                    if n.startswith(("p_", "t_", "v_")))
        if pagina in ("tastiera", "pad"):
            rett = disegna_voci(sc, voci, sel, font, small, s(200), s(38),
                                frecce=True, ante=ante, porte=porte)
        else:
            rett = disegna_voci(sc, voci, sel, font, small,
                                s(436) if pagina == "radice" else s(408),
                                s(44), frecce=True, ante=ante, porte=porte)
        # la stecca scelta, disegnata per intero sotto le righe
        if pagina == "tavolo" and 0 <= CFG.get("stecca", 0) < len(STECCHE):
            lung = s(760)
            k = 1.6 * lung / 145.0 / 2.0        # un filo piu' grossa del vero
            y = rett[-1].bottom + s(46)
            disegna_stecca_su(sc, Vector2(WIN_W // 2 + lung // 2, y),
                              Vector2(1, 0), lung,
                              (1.3 * k, 2.0 * k, 3.0 * k),
                              stecca_scelta())
            dm, dp, de = DOTI[STECCHE.index(stecca_scelta())]
            c = FONTS["mini"].render(
                "%s %d%%     %s %d%%     %s %d%%     -     %s" % (
                    T("st_aim"), dm, T("st_power"), dp, T("st_spin"), de,
                    T("st_count") % (stecche_sbloccate(), len(STECCHE))),
                True, ORO_SCELTA)
            sc.blit(c, c.get_rect(center=(WIN_W // 2, y + s(26))))
        # e il set di palle, in fila: la bianca e le quindici
        if pagina == "tavolo" and HA_NUMPY and M_FACCIA is not None:
            r_p = s(15)
            passo = r_p * 2 + s(6)
            tp = tipo_palle()
            fila = (list(range(16)) if tp == "pool" else
                    [0, 1, 2, 3, 9, 10, 11, 8] if tp == "blackball" else
                    [0, 1, 2, 3, 4, 5, 6] if tp == "piramide" else
                    [0, SN_ROSSI[0]] + list(SN_COLORI) if tp == "snooker"
                    else [0, BI_GIALLA, BI_PALLINO])
            x0 = WIN_W // 2 - passo * len(fila) // 2
            y = rett[-1].bottom + s(100)
            for i_p, n_p in enumerate(fila):
                q = rendi_sfera(n_p, M_FACCIA, r_p, 1.5, 1.5)
                if q is not None:
                    sc.blit(q, q.get_rect(center=(x0 + i_p * passo + passo // 2,
                                                  y)))
        # chi ha fatto la musica, sotto le righe dell'audio
        if pagina == "audio":
            c = FONTS["mini"].render(CREDITI_MUSICA, True, (140, 148, 160))
            sc.blit(c, c.get_rect(center=(WIN_W // 2,
                                          rett[-1].bottom + s(40))))
        for i, r in enumerate(rett):
            if MOUSE_VIVO[0] and r.collidepoint(mouse):
                sel = i
        presenta()


def schermata_pausa(sc, clock, sotto=None):
    """Il menu che si apre con ESC durante la partita: schermata piena,
    stesso fondo del gioco, niente tavolo in trasparenza dietro."""
    voci = [T("resume"), T("newgame"), T("settings"), T("mainmenu")]
    esiti = ["continua", "nuova", "settings", "menu"]
    sel = 0
    rett = []
    while True:
        clock.tick(60)
        mouse = mouse_gioco()
        font, grande, small = FONTS["font"], FONTS["grande"], FONTS["small"]
        for ev in eventi():
            if ev.type == pygame.QUIT:
                return "quit"
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    return "continua"
                if ev.key in (pygame.K_DOWN, pygame.K_s):
                    sel = (sel + 1) % len(voci)
                if ev.key in (pygame.K_UP, pygame.K_w):
                    sel = (sel - 1) % len(voci)
                if ev.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                    return esiti[sel]
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                for i, r in enumerate(rett):
                    if r.collidepoint(mouse):
                        return esiti[i]

        sc.blit(fondo(), (0, 0))
        aiuto_menu(sc)
        t = FONTS["elegante"].render(tit_el(T("pause")), True, (240, 240, 244))
        sc.blit(t, t.get_rect(center=(WIN_W // 2, s(250))))
        rett = disegna_voci(sc, [(v, None) for v in voci], sel,
                            font, small, s(360), s(56))
        for i, r in enumerate(rett):
            if MOUSE_VIVO[0] and r.collidepoint(mouse):
                sel = i
        presenta()


def _via_nomi(nomi, bandiere, livello, contro_cpu):
    """Si comincia: nomi, bandiere e livello restano scritti nel file, e
    contro il computer il secondo giocatore prende il nome del computer.
    La sua bandiera la mette il torneo, che sa di dov'e' l'avversario."""
    CFG["nomi"] = nomi
    CFG["bandiere"] = bandiere
    CFG["livello"] = livello
    NOMI[0] = nomi[0]
    BANDIERA[0] = bandiere[0]
    if contro_cpu:
        # un avversario a sorte, con la sua bandiera: giocare contro uno
        # che si chiama "Computer" non e' la stessa cosa
        scelto = CFG.get("avversario", "")
        if scelto in AVVERSARI:
            NOMI[1] = scelto
        else:
            NOMI[1] = random.choice(AVVERSARI) if AVVERSARI \
                else T("computer")
        BANDIERA[1] = PAESI.get(NOMI[1], "")
    else:
        NOMI[1] = nomi[1]
        BANDIERA[1] = bandiere[1]
    salva_config()
    return "free_go"


def schermata_nomi(sc, clock, logo, contro_cpu=False, scegli_livello=True):
    """Chi gioca, su due colonne: a sinistra il giocatore 1, a destra il
    giocatore 2 (o il livello del computer). Sotto, in mezzo, quello che
    vale per tutti e due: il gessetto e quanti frame. In fondo Comincia e
    Indietro, uno accanto all'altro. Su e giu' passano da una riga
    all'altra, anche da una colonna all'altra; destra e sinistra cambiano
    la scelta. Nel torneo solo nome e bandiera: il resto lo decide lui."""
    nomi = [CFG["nomi"][0], CFG["nomi"][1]]
    paesi = list(CFG.get("bandiere", ["it", "gb"]))[:2]
    while len(paesi) < 2:
        paesi.append("")
    livello = max(0, min(len(LIVELLI) - 1, CFG.get("livello", 1)))
    tutte = elenco_bandiere()
    libera = scegli_livello                  # partita libera, non torneo
    # (tipo, giocatore, dove): dove e' 0 colonna sinistra, 1 destra,
    # "c" in mezzo, "b" i bottoni in fondo
    righe = []
    for gi in ((0,) if contro_cpu else (0, 1)):
        righe += [("nome", gi, gi), ("band", gi, gi)]
        if libera and contro_cpu:
            # in due si gioca alla buona: la stecca base per tutti e due
            righe.append(("stecca", gi, gi))
    if contro_cpu and libera:
        # a destra il computer: chi e' (o a caso), il livello, la sua stecca
        righe += [("avv", 1, 1), ("liv", 1, 1), ("stavv", 1, 1)]
    if libera and contro_cpu:
        righe.append(("gesso", 0, "c"))
    if libera:
        righe.append(("match", 0, "c"))
    righe += [("via", 0, "b"), ("indietro", 0, "b")]
    n_voci = len(righe)
    sel = 0
    rett = []
    MAX = 14
    CHIAVE_ST = ("stecca", "stecca2")

    def gira(riga, passo):
        nonlocal livello
        tipo, gi, _ = riga
        if tipo == "band" and tutte:
            try:
                k = tutte.index(paesi[gi])
            except ValueError:
                k = 0
            paesi[gi] = tutte[(k + passo) % len(tutte)]
        elif tipo == "stecca":
            giro = [-1] + stecche_mie()
            ora = CFG.get(CHIAVE_ST[gi], -1)
            k = giro.index(ora) if ora in giro else 0
            CFG[CHIAVE_ST[gi]] = giro[(k + passo) % len(giro)]
        elif tipo == "liv":
            livello = (livello + passo) % len(LIVELLI)
        elif tipo == "avv":
            giro = [""] + sorted(AVVERSARI)
            ora = CFG.get("avversario", "")
            k = giro.index(ora) if ora in giro else 0
            CFG["avversario"] = giro[(k + passo) % len(giro)]
        elif tipo == "gesso":
            gira_gesso(passo)
        elif tipo == "match":
            i = (MATCH.index(CFG.get("match", 1))
                 if CFG.get("match", 1) in MATCH else 0)
            CFG["match"] = MATCH[(i + passo) % len(MATCH)]

    def nome_stecca(gi):
        i = CFG.get(CHIAVE_ST[gi], -1)
        if i not in stecche_mie():
            return T("random")
        return "%d. %s" % (i + 1, T(STECCHE[i][0]))

    def via():
        return _via_nomi(nomi, paesi, livello, contro_cpu)

    # dove stanno le cose
    passo = s(52)
    y_col = s(236)
    larga = s(540)
    x_col = (WIN_W // 2 - s(300), WIN_W // 2 + s(300))

    def passa(da, verso):
        """La riga dopo (o prima), saltando quelle che non si scelgono."""
        i = da
        while True:
            i += verso
            if i < 0 or i > n_voci - 2:
                return da
            if righe[i][0] != "stavv":
                return i

    def posti(dove):
        """Quanti posti occupa una colonna: la stecca ne prende due, uno
        per il disegno sopra la sua riga."""
        n = 0
        for r in righe:
            if r[2] == dove:
                n += 2 if r[0] in ("stecca", "stavv") else 1
        return n

    def cella(i):
        tipo, gi, dove = righe[i]
        if dove in (0, 1):
            k = 0
            for j, r in enumerate(righe):
                if r[2] != dove:
                    continue
                if r[0] in ("stecca", "stavv"):
                    k += 1          # il posto del disegno
                if j == i:
                    break
                k += 1
            return pygame.Rect(x_col[dove] - larga // 2,
                               y_col + k * passo - passo // 2 + s(3),
                               larga, passo - s(6))
        n_col = max(posti(0), posti(1))
        y_c = y_col + n_col * passo + s(20)
        if dove == "c":
            k = [j for j, r in enumerate(righe) if r[2] == "c"].index(i)
            y = y_c + k * passo
            return pygame.Rect(WIN_W // 2 - s(320), y - passo // 2 + s(3),
                               s(640), passo - s(6))
        n_c = len([r for r in righe if r[2] == "c"])
        k = 0 if tipo == "via" else 1
        return pygame.Rect(WIN_W // 2 - s(210) + k * s(220),
                           y_c + n_c * passo + s(24), s(200), s(42))

    while True:
        clock.tick(60)
        mouse = mouse_gioco()
        font, small = FONTS["font"], FONTS["small"]
        tipo_sel, gi_sel, dove_sel = righe[sel]
        scrive = (tipo_sel == "nome")

        for ev in eventi():
            if ev.type == pygame.QUIT:
                return "quit"
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    return "menu"
                if ev.key in (pygame.K_DOWN, pygame.K_TAB):
                    if dove_sel != "b":
                        sel = passa(sel, 1)
                elif ev.key == pygame.K_UP:
                    if dove_sel == "b":
                        sel = passa(n_voci - 2, -1)
                    else:
                        sel = passa(sel, -1)
                elif ev.key in (pygame.K_LEFT, pygame.K_RIGHT):
                    passo_k = -1 if ev.key == pygame.K_LEFT else 1
                    if dove_sel == "b":
                        sel = n_voci - 2 if passo_k < 0 else n_voci - 1
                    else:
                        gira(righe[sel], passo_k)
                elif ev.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    if tipo_sel == "indietro":
                        return "menu"
                    return via()
                elif ev.key == pygame.K_BACKSPACE and scrive:
                    nomi[gi_sel] = nomi[gi_sel][:-1]
                elif scrive and ev.unicode and ev.unicode.isprintable():
                    if len(nomi[gi_sel]) < MAX:
                        nomi[gi_sel] += ev.unicode
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                for i, r in enumerate(rett):
                    if not r.collidepoint(mouse):
                        continue
                    sel = i
                    tipo = righe[i][0]
                    if tipo == "via":
                        return via()
                    if tipo == "indietro":
                        return "menu"
                    gira(righe[i], -1 if mouse[0] < r.right - s(140) else 1)

        sfondo_menu(sc, None)
        t = FONTS["elegante"].render(tit_el(T("names")), True, (240, 240, 244))
        sc.blit(t, t.get_rect(center=(WIN_W // 2, s(96))))
        t = small.render(T("sub_cpu") if contro_cpu and libera
                         else T("sub_names"), True, ORO_SOTTO)
        sc.blit(t, t.get_rect(center=(WIN_W // 2, s(142))))

        tic_menu(tuple(r[0] + str(r[1]) for r in righe), sel)
        rett = []
        for i, (tipo, gi, dove) in enumerate(righe):
            r = cella(i)
            rett.append(r)
            acceso = (i == sel)
            if dove == "b":
                q = pygame.Surface(r.size, pygame.SRCALPHA)
                q.fill((255, 255, 255, 26) if acceso else (255, 255, 255, 10))
                sc.blit(q, r)
                if acceso:
                    pygame.draw.rect(sc, COL_GIOC[0], (r.x, r.y, 3, r.h))
                col = (255, 255, 255) if acceso else (190, 196, 208)
                tv = FONTS["elegante_voce"].render(
                    tit_el(T("start") if tipo == "via" else T("back")),
                    True, col)
                sc.blit(tv, tv.get_rect(center=r.center))
                continue
            if acceso:
                q = pygame.Surface(r.size, pygame.SRCALPHA)
                q.fill((255, 255, 255, 18))
                sc.blit(q, r)
            # il colore del giocatore lungo la sua riga del nome, e sulla
            # riga scelta
            if tipo == "nome":
                pygame.draw.rect(sc, COL_GIOC[gi],
                                 (r.x, r.y, max(1, s(3)), r.h))
            elif acceso:
                pygame.draw.rect(sc, COL_GIOC[0],
                                 (r.x, r.y, max(1, s(3)), r.h))
            ante = None
            if tipo == "nome":
                et = T("player") % (gi + 1)
                val = nomi[gi]
                if acceso:
                    val += ("_" if (pygame.time.get_ticks() // 400) % 2
                            else " ")
                elif not val:
                    val = T("player") % (gi + 1)
            elif tipo == "band":
                et, val = T("flag"), paesi[gi].upper()
                ante = bandiera(paesi[gi], s(20))
            elif tipo == "stecca":
                et, val = T("cue"), nome_stecca(gi)
                # la stecca scelta, disegnata sopra la sua riga
                i_s = CFG.get(CHIAVE_ST[gi], -1)
                if i_s in stecche_mie():
                    lung = s(480)
                    k_s = 1.5 * lung / 145.0 / 2.0
                    disegna_stecca_su(
                        sc, Vector2(r.centerx + lung // 2, r.centery - passo),
                        Vector2(1, 0), lung, (1.3 * k_s, 2.0 * k_s,
                                              3.0 * k_s), STECCHE[i_s])
            elif tipo == "liv":
                et, val = T("level"), T(LIVELLI[livello][0])
            elif tipo == "avv":
                chi = CFG.get("avversario", "")
                et = T("computer")
                val = chi if chi in AVVERSARI else T("random")
                if chi in AVVERSARI:
                    ante = bandiera(PAESI.get(chi, ""), s(20))
            elif tipo == "stavv":
                chi = CFG.get("avversario", "")
                et = T("cue")
                if chi in AVVERSARI:
                    i_s = stecca_avversario(chi)
                    val = "%d. %s" % (i_s + 1, T(STECCHE[i_s][0]))
                    lung = s(480)
                    k_s = 1.5 * lung / 145.0 / 2.0
                    disegna_stecca_su(
                        sc, Vector2(r.centerx + lung // 2, r.centery - passo),
                        Vector2(1, 0), lung, (1.3 * k_s, 2.0 * k_s,
                                              3.0 * k_s), STECCHE[i_s])
                else:
                    val = T("random")
            elif tipo == "gesso":
                et, val = T("chalk_row"), nome_gesso_scelto()
            else:
                n = CFG.get("match", 1)
                et = T("match")
                val = T("m_uno") if n <= 1 else T("m_best") % n
            col = (255, 255, 255) if acceso else (196, 200, 208)
            tv = FONTS["elegante_voce"].render(tit_el(et), True, col)
            sc.blit(tv, tv.get_rect(midleft=(r.x + s(22), r.centery)))
            cv = ORO_SCELTA if acceso else ORO_SOTTO
            xv = r.right - s(140)
            v = small.render(val, True, cv)
            if v.get_width() > s(170):
                v = FONTS["mini"].render(val, True, cv)
            sc.blit(v, v.get_rect(center=(xv, r.centery)))
            if acceso and tipo not in ("nome", "stavv"):
                for x, segno in ((xv - s(106), "<"), (xv + s(106), ">")):
                    f = font.render(segno, True, cv)
                    sc.blit(f, f.get_rect(center=(x, r.centery)))
            if ante is not None:
                qa = ante.get_rect(center=(xv - s(150), r.centery))
                sc.blit(ante, qa)
                pygame.draw.rect(sc, (70, 74, 84), qa.inflate(s(2), s(2)),
                                 max(1, s(1)))
        for i, r in enumerate(rett):
            if MOUSE_VIVO[0] and r.collidepoint(mouse):
                sel = i
        presenta()


def schermata_torneo(sc, clock, logo, titolo, sotto, nota, voci, chiavi,
                     paese=None):
    """Le schermate fra una partita e l'altra del torneo: un titolo, due
    righe sotto e due scelte. Tutte uguali, cambia solo cosa c'e' scritto."""
    sel = 0
    rett = []
    while True:
        clock.tick(60)
        mouse = mouse_gioco()
        for ev in eventi():
            if ev.type == pygame.QUIT:
                return "quit"
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    return chiavi[-1]
                if ev.key in (pygame.K_DOWN, pygame.K_TAB):
                    sel = (sel + 1) % len(voci)
                elif ev.key == pygame.K_UP:
                    sel = (sel - 1) % len(voci)
                elif ev.key in (pygame.K_RETURN, pygame.K_KP_ENTER,
                                pygame.K_SPACE):
                    return chiavi[sel]
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                for i, r in enumerate(rett):
                    if r.collidepoint(mouse):
                        return chiavi[i]

        font, grande, small = FONTS["font"], FONTS["grande"], FONTS["small"]
        sfondo_menu(sc, logo)
        t = FONTS["elegante"].render(tit_el(titolo), True, (240, 240, 244))
        sc.blit(t, t.get_rect(center=(WIN_W // 2, s(330))))
        t = font.render(sotto, True, ORO_SCELTA)
        r = t.get_rect(center=(WIN_W // 2, s(382)))
        ban = bandiera(paese, s(22)) if paese else None
        if ban:
            # titolo e bandiera insieme al centro, la bandiera davanti
            r.x += (ban.get_width() + s(10)) // 2
            sc.blit(ban, ban.get_rect(midright=(r.left - s(10), r.centery)))
        sc.blit(t, r)
        if nota:
            t = small.render(nota, True, ORO_SOTTO)
            sc.blit(t, t.get_rect(center=(WIN_W // 2, s(418))))
        rett = disegna_voci(sc, [(v, None) for v in voci], sel,
                            font, small, s(486), s(56))
        for i, r in enumerate(rett):
            if MOUSE_VIVO[0] and r.collidepoint(mouse):
                sel = i
        presenta()


SALVA_TORNEO = os.path.join(DATI, "biliardo_torneo.json")

# I tornei: tre per disciplina, da un frame, al meglio di tre e al meglio
# di cinque. Ognuno ha il suo nome e il suo stemma, che sta in
# biliardo_gfx/stemmi/classici o moderni col nome del file qui sotto.
TORNEI = {
    0: (("eclipse_masters", "The Eclipse 8-Ball Masters", 3),),
    1: (("phoenix_cup", "Phoenix Cue Cup", 3),),
    5: (("golden_diamond", "Golden Diamond Classic", 3),),
    4: (("royal_break", "Royal Break Open", 3),),
    2: (("velvet_championship", "The Velvet Cue Championship", 3),),
    6: (("emerald_open", "Emerald Table Open", 3),),
    3: (("shadow_strike", "Shadow Strike League", 3),),
    7: (("iron_pocket", "Iron Pocket Invitational", 3),),
    8: (("titanium_rack", "Titanium Rack Tournament", 3),),
}
TORNEO_ORA = [None]     # il torneo che si sta giocando: (disciplina, k)
TORNEO_TURNO = [0]      # quanti sono rimasti nel turno che si gioca
STEMMI = {}


def stemma(chiave, alto):
    """Lo stemma del torneo, alto quanto si chiede. Si prende dal set
    scelto nelle impostazioni; se li' manca, dall'altro."""
    set_ = "classici"           # gli stemmi sono quelli: niente scelta
    k = (chiave, alto, set_)
    if k not in STEMMI:
        img = None
        for cartella in (set_, "classici", "moderni"):
            f = os.path.join(GFX, "stemmi", cartella, chiave + ".png")
            if os.path.exists(f):
                try:
                    img = pygame.image.load(f).convert_alpha()
                    break
                except pygame.error:
                    img = None
        if img is not None:
            w, h = img.get_size()
            img = pygame.transform.smoothscale(
                img, (max(1, int(w * alto / float(h))), alto))
        STEMMI[k] = img
    return STEMMI[k]


def stemma_ora(alto):
    if TORNEO_ORA[0] is None:
        return None
    d, k = TORNEO_ORA[0]
    return stemma(TORNEI[d][k][0], alto)


def scelta_torneo(sc, clock, logo, disc):
    """I tre tornei della disciplina, uno accanto all'altro con lo
    stemma, il nome e quanti frame. Si sceglie con le frecce o col mouse."""
    elenco = TORNEI.get(disc, TORNEI[0])
    sel = 0
    salvati = _tornei_salvati()
    while True:
        clock.tick(60)
        mouse = mouse_gioco()
        font, small, grande = FONTS["font"], FONTS["small"], FONTS["grande"]
        largo, stacco = s(330), s(30)
        x0 = WIN_W // 2 - (largo * 3 + stacco * 2) // 2
        carte = [pygame.Rect(x0 + i * (largo + stacco), s(190), largo,
                             s(470)) for i in range(3)]
        for ev in eventi():
            if ev.type == pygame.QUIT:
                return "quit"
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    return "menu"
                if ev.key in (pygame.K_RIGHT, pygame.K_d, pygame.K_TAB):
                    sel = (sel + 1) % 3
                if ev.key in (pygame.K_LEFT, pygame.K_a):
                    sel = (sel - 1) % 3
                if ev.key in (pygame.K_RETURN, pygame.K_KP_ENTER,
                              pygame.K_SPACE):
                    return sel
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                for i, r in enumerate(carte):
                    if r.collidepoint(mouse):
                        return i
        for i, r in enumerate(carte):
            if MOUSE_VIVO[0] and r.collidepoint(mouse):
                sel = i
        tic_menu(("tornei", disc), sel)

        sfondo_menu(sc, None)
        t = FONTS["elegante"].render(tit_el(T("t_choose")), True, (236, 216, 164))
        sc.blit(t, t.get_rect(center=(WIN_W // 2, s(110))))
        for i, (chiave, nome_t, frame) in enumerate(elenco):
            r = carte[i]
            acceso = (i == sel)
            q = pygame.Surface(r.size, pygame.SRCALPHA)
            q.fill((255, 255, 255, 24) if acceso else (255, 255, 255, 8))
            sc.blit(q, r)
            if acceso:
                pygame.draw.rect(sc, COL_GIOC[0], r, max(1, s(2)))
            img = stemma(chiave, s(300))
            if img is not None:
                if img.get_width() > r.w - s(20):
                    k = (r.w - s(20)) / float(img.get_width())
                    img = pygame.transform.smoothscale(
                        img, (int(img.get_width() * k),
                              int(img.get_height() * k)))
                sc.blit(img, img.get_rect(midtop=(r.centerx, r.y + s(16))))
            col = (255, 255, 255) if acceso else (200, 204, 214)
            testo = _tagliato(nome_t, small, r.w - s(16))
            tn = small.render(testo, True, col)
            sc.blit(tn, tn.get_rect(center=(r.centerx, r.bottom - s(92))))
            tf = font.render(T("m_uno") if frame <= 1 else
                             T("m_best") % frame, True, (232, 190, 90))
            sc.blit(tf, tf.get_rect(center=(r.centerx, r.bottom - s(60))))
            if "%d_%d" % (disc, i) in salvati:
                tv = FONTS["mini"].render(T("t_saved"), True, (120, 200, 150))
                sc.blit(tv, tv.get_rect(center=(r.centerx,
                                                r.bottom - s(28))))
        presenta()


def disegna_stemma_gioco(sc, turno=None):
    """Lo stemma durante la partita, grande come sul tabellone: in alto a
    sinistra, sopra la barra della potenza e in colonna con lei."""
    img = stemma_ora(s(88))
    if img is None:
        return
    x_lato = max(s(30), int((TAV_POS[0] + TAV_VISTA[0] * SCALA) / 2.0))
    largo = max(s(40), x_lato * 2 - s(8))
    if img.get_width() > largo:
        k = largo / float(img.get_width())
        img = pygame.transform.smoothscale(
            img, (int(img.get_width() * k), int(img.get_height() * k)))
    r = img.get_rect(midtop=(x_lato, ALTO + s(10)))
    sc.blit(img, r)
    # sotto, il turno che si sta giocando, scritto come sul tabellone e
    # tradotto adesso: se si cambia lingua in pausa cambia anche lui
    if TORNEO_TURNO[0]:
        turno = T("r_%d" % max(2, TORNEO_TURNO[0]))
        t = FONTS["mini"].render(turno.upper(), True, (170, 140, 90))
        sc.blit(t, t.get_rect(midtop=(x_lato, r.bottom + s(6))))




def _tornei_salvati():
    try:
        with open(SALVA_TORNEO, "r") as f:
            d = json.load(f)
        return d if isinstance(d, dict) else {}
    except (IOError, ValueError):
        return {}


def carica_torneo(disc):
    """Il torneo lasciato a meta' in quella disciplina, se c'e'."""
    t = _tornei_salvati().get(str(disc))
    if not isinstance(t, dict) or "tab" not in t:
        return None
    return t


def salva_torneo(disc, tab, giri, nome_mio, bandiera_mia, in_corso=None):
    """Tutto quello che serve per riprendere: il tabellone, i tavoli dei
    turni, chi sei, e se c'era un match a meta' i frame gia' giocati."""
    d = _tornei_salvati()
    d[str(disc)] = {"tab": tab, "giri": [list(giri[0]), list(giri[1])],
                    "nome": nome_mio, "bandiera": bandiera_mia,
                    "partita": in_corso}
    try:
        with open(SALVA_TORNEO, "w") as f:
            json.dump(d, f, indent=1)
    except IOError:
        pass


def cancella_torneo(disc):
    d = _tornei_salvati()
    if str(disc) in d:
        del d[str(disc)]
        try:
            with open(SALVA_TORNEO, "w") as f:
                json.dump(d, f, indent=1)
        except IOError:
            pass


def torneo(sc, clock, logo):
    """Il torneo a eliminazione diretta: sessantaquattro al via, si
    passa il turno solo vincendo, e chi arriva in fondo alza la coppa.
    Prima di ogni partita si vede il tabellone, con la propria riga che
    lampeggia. Il torneo si salva da solo: a ogni turno passato e a ogni
    frame finito, e la volta dopo si riprende da li'."""
    disc = GIOCO[0]
    if len(TORNEI.get(disc, ())) > 1:
        k_t = scelta_torneo(sc, clock, logo, disc)
        if k_t in ("menu", "quit"):
            return k_t
    else:
        k_t = 0                 # un torneo solo: si va dritti
    try:
        TORNEO_ORA[0] = (disc, k_t)
        return _torneo(sc, clock, logo, disc, k_t)
    finally:
        TORNEO_ORA[0] = None
        TORNEO_TURNO[0] = 0


def schermata_sblocco(sc, clock, i, titolo=None, tinta=None):
    """Hai vinto l'incontro: la stecca nuova, disegnata in grande, col
    suo numero, il nome e le sue doti."""
    st = STECCHE[i]
    doti = DOTI[i]
    massimi = [max(d[k] for d in DOTI) for k in range(3)]
    if SUONI.get("menu_apri"):
        suona_fx("menu_apri")
    while True:
        clock.tick(60)
        for ev in eventi():
            if ev.type == pygame.QUIT:
                return "quit"
            if ev.type == pygame.KEYDOWN and ev.key in (
                    pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE,
                    pygame.K_ESCAPE):
                return "ok"
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                return "ok"
        sc.blit(fondo(tinta), (0, 0))
        aiuto_menu(sc)
        t = FONTS["elegante"].render(tit_el(titolo or T("unl_title")), True,
                                     (240, 240, 244))
        sc.blit(t, t.get_rect(center=(WIN_W // 2, s(220))))
        n = FONTS["elegante_voce"].render(
            "%d. %s" % (i + 1, T(st[0])), True, ORO_SCELTA)
        sc.blit(n, n.get_rect(center=(WIN_W // 2, s(300))))
        lung = s(900)
        k = 1.6 * lung / 145.0 / 2.0
        disegna_stecca_su(sc, Vector2(WIN_W // 2 + lung // 2, s(390)),
                          Vector2(1, 0), lung, (1.3 * k, 2.0 * k, 3.0 * k),
                          st)
        # le tre doti, con la loro barra
        largo = s(320)
        for r, (chiave, v, m) in enumerate(zip(
                ("st_aim", "st_power", "st_spin"), doti, massimi)):
            y = s(470) + r * s(44)
            e = FONTS["font"].render(T(chiave), True, (236, 236, 240))
            sc.blit(e, e.get_rect(midright=(WIN_W // 2 - largo // 2 - s(20),
                                            y)))
            fondo_b = pygame.Rect(WIN_W // 2 - largo // 2, y - s(6),
                                  largo, s(12))
            pygame.draw.rect(sc, (30, 40, 36), fondo_b, border_radius=s(6))
            pieno = fondo_b.copy()
            pieno.w = max(s(8), int(largo * v / float(m)))
            pygame.draw.rect(sc, COL_DOTI[r], pieno, border_radius=s(6))
            q = FONTS["font"].render("%d%%" % v, True, COL_DOTI[r])
            sc.blit(q, q.get_rect(midleft=(fondo_b.right + s(20), y)))
        c = FONTS["small"].render(
            T("st_count") % (stecche_sbloccate(), len(STECCHE)), True,
            ORO_SOTTO)
        sc.blit(c, c.get_rect(center=(WIN_W // 2, s(620))))
        presenta()


# i colori delle tre doti: mira viola, potenza arancione, effetto blu
COL_DOTI = ((176, 118, 236), (242, 144, 52), (84, 154, 242))


def _anteprima_stecca(sc, i, y):
    """La stecca in grande, col nome sopra e le tre doti sotto."""
    n = FONTS["elegante_voce"].render("%d. %s" % (i + 1, T(STECCHE[i][0])),
                                      True, ORO_SCELTA)
    sc.blit(n, n.get_rect(center=(WIN_W // 2, y - s(62))))
    lung = s(900)
    k = 1.6 * lung / 145.0 / 2.0
    disegna_stecca_su(sc, Vector2(WIN_W // 2 + lung // 2, y), Vector2(1, 0),
                      lung, (1.3 * k, 2.0 * k, 3.0 * k), STECCHE[i])
    massimi = [max(d[k2] for d in DOTI) for k2 in range(3)]
    largo = s(130)
    for j, (chiave, v) in enumerate(zip(("st_aim", "st_power", "st_spin"),
                                        DOTI[i])):
        cx = WIN_W // 2 + (j - 1) * s(300)
        e = FONTS["mini"].render(T(chiave), True, (220, 222, 228))
        sc.blit(e, e.get_rect(center=(cx, y + s(48))))
        fondo_b = pygame.Rect(cx - largo // 2, y + s(62), largo, s(8))
        pygame.draw.rect(sc, (30, 40, 36), fondo_b, border_radius=s(4))
        pieno = fondo_b.copy()
        pieno.w = max(s(4), int(largo * v / float(massimi[j])))
        pygame.draw.rect(sc, COL_DOTI[j], pieno, border_radius=s(4))
        q = FONTS["mini"].render("%d%%" % v, True, COL_DOTI[j])
        sc.blit(q, q.get_rect(center=(cx, y + s(84))))


def _anteprima_gesso(sc, tipo, y, righe):
    """Il gessetto in grande, col nome sopra e i suoi dati sotto."""
    n = FONTS["elegante_voce"].render(T("ch_" + tipo), True, ORO_SCELTA)
    sc.blit(n, n.get_rect(center=(WIN_W // 2, y - s(84))))
    im = icona_gesso(s(120), tipo)
    if im is not None:
        sc.blit(im, im.get_rect(center=(WIN_W // 2, y)))
    for j, testo in enumerate(righe):
        q = FONTS["mini"].render(testo, True, (220, 222, 228))
        sc.blit(q, q.get_rect(center=(WIN_W // 2, y + s(74) + j * s(20))))


def _righe_vetrina(sc, voci, sel, y0, passo):
    """Le righe del negozio e della borsa: il nome a sinistra, la scelta
    con le frecce in mezzo, il prezzo (o quanti ne hai) in fondo."""
    tic_menu(tuple(v[0] for v in voci), sel)
    cx = WIN_W // 2
    rett = []
    for i, (et, val, prezzo, rosso, frecce) in enumerate(voci):
        y = y0 + i * passo
        acceso = (i == sel)
        r = pygame.Rect(cx - s(380), y - passo // 2 + s(4), s(760),
                        passo - s(8))
        if acceso:
            b = pygame.Surface(r.size, pygame.SRCALPHA)
            b.fill((255, 255, 255, 18))
            sc.blit(b, r)
            pygame.draw.rect(sc, COL_GIOC[0], (r.x, r.y, max(1, s(3)), r.h))
        col = (255, 255, 255) if acceso else (196, 200, 208)
        t = FONTS["elegante_voce"].render(tit_el(et), True, col)
        sc.blit(t, t.get_rect(midleft=(cx - s(350), y)))
        if val is not None:
            cv = ORO_SCELTA if acceso else ORO_SOTTO
            v = FONTS["small"].render(val, True, cv)
            sc.blit(v, v.get_rect(center=(cx + s(90), y)))
            if acceso and frecce:
                for x, segno in ((cx - s(50), "<"), (cx + s(230), ">")):
                    f = FONTS["font"].render(segno, True, cv)
                    sc.blit(f, f.get_rect(center=(x, y)))
        if prezzo:
            cp = (240, 96, 96) if rosso else (ORO_SCELTA if acceso
                                               else ORO_SOTTO)
            q = FONTS["small"].render(prezzo, True, cp)
            sc.blit(q, q.get_rect(midright=(cx + s(360), y)))
        rett.append(r)
    return rett


def schermata_vetrina(sc, clock, logo, negozio=True):
    """Il negozio (negozio=True) o la borsa. Nel negozio ci sono solo le
    stecche che non hai e tutti i gessetti, e con A si compra quello
    della riga. Nella borsa c'e' quello che hai, da guardare: stecca e
    gessetto si scelgono prima di ogni partita."""
    tipi = [g[0] for g in GESSI]
    i_st, i_g = 0, 0
    sel = 0
    vista = 0               # cosa si vede sopra: 0 la stecca, 1 il gessetto
    rett = []
    avviso = ["", 0, ORO_SCELTA]

    def dice(testo, col=(240, 96, 96)):
        avviso[0], avviso[1], avviso[2] = (testo,
                                           pygame.time.get_ticks() + 1600,
                                           col)

    def stecche_qui():
        mie = stecche_mie()
        if negozio:
            return [i for i in range(len(STECCHE)) if i not in mie]
        return mie

    def gessi_qui():
        return tipi if negozio else gessi_miei()

    def compra(riga):
        nonlocal i_st
        st, ge = stecche_qui(), gessi_qui()
        if riga == 0 and st:
            i = st[i_st % len(st)]
            prezzo = prezzo_stecca(i)
            if soldi() < prezzo:
                dice(T("no_money"))
                return None
            soldi(-prezzo)
            CFG["stecche_mie"] = stecche_mie() + [i]
            salva_config()
            if schermata_sblocco(sc, clock, i, T("buy_done"),
                                 "negozio") == "quit":
                return "quit"
        elif riga == 1 and ge:
            t = ge[i_g % len(ge)]
            prezzo = gesso_dati(t)[2]
            if soldi() < prezzo:
                dice(T("no_money"))
                return None
            soldi(-prezzo)
            gessi = CFG.setdefault("gessi", {})
            gessi[t] = int(gessi.get(t, 0)) + 1
            salva_config()
            dice(T("bought"), ORO_SCELTA)
            if SUONI.get("menu_apri"):
                suona_fx("menu_apri")
        return None

    def gira(riga, passo):
        nonlocal i_st, i_g
        if riga == 0 and stecche_qui():
            i_st = (i_st + passo) % len(stecche_qui())
        elif riga == 1 and gessi_qui():
            i_g = (i_g + passo) % len(gessi_qui())

    while True:
        clock.tick(60)
        mouse = mouse_gioco()
        st, ge = stecche_qui(), gessi_qui()
        for ev in eventi():
            if ev.type == pygame.QUIT:
                return "quit"
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    return "menu"
                if ev.key in (pygame.K_DOWN, pygame.K_s, pygame.K_TAB):
                    sel = (sel + 1) % 3
                elif ev.key in (pygame.K_UP, pygame.K_w):
                    sel = (sel - 1) % 3
                elif ev.key in (pygame.K_LEFT, pygame.K_RIGHT, pygame.K_a,
                                pygame.K_d):
                    gira(sel, -1 if ev.key in (pygame.K_LEFT, pygame.K_a)
                         else 1)
                elif ev.key in (pygame.K_RETURN, pygame.K_KP_ENTER,
                                pygame.K_SPACE):
                    if sel == 2:
                        return "menu"
                    if negozio:
                        q = compra(sel)
                        if q:
                            return q
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                for i, r in enumerate(rett):
                    if not r.collidepoint(mouse):
                        continue
                    sel = i
                    if i == 2:
                        return "menu"
                    x = mouse[0] - WIN_W // 2
                    if -s(80) < x < s(260):
                        gira(i, -1 if x < s(90) else 1)
                    elif negozio:
                        q = compra(i)
                        if q:
                            return q
        if sel in (0, 1):
            vista = sel
        st, ge = stecche_qui(), gessi_qui()

        sfondo_menu(sc, None, "negozio" if negozio else "borsa")
        t = FONTS["elegante"].render(tit_el(T("shop" if negozio else "bag")),
                                     True, (240, 240, 244))
        sc.blit(t, t.get_rect(center=(WIN_W // 2, s(70))))

        # sopra, quello che si sta guardando, coi suoi dati
        y_prev = s(300)
        scorta = CFG.get("gessi") or {}
        if vista == 0:
            if st:
                _anteprima_stecca(sc, st[i_st % len(st)], y_prev)
            else:
                q = FONTS["small"].render(T("all_owned"), True, ORO_SOTTO)
                sc.blit(q, q.get_rect(center=(WIN_W // 2, y_prev)))
        elif ge:
            tg = ge[i_g % len(ge)]
            righe = [T("ch_uses") % gesso_dati(tg)[1],
                     T("ch_have") % int(scorta.get(tg, 0))]
            for k_c, k_t in CUBO_K:
                if int(CFG.get(k_c, 0)) > 0 and CFG.get(k_t) == tg:
                    righe.append(T("ch_open") % int(CFG[k_c]))
                    break
            _anteprima_gesso(sc, tg, y_prev, righe)

        # le righe: stecca, gessetto, indietro
        if st:
            i = st[i_st % len(st)]
            v_st = "%d. %s" % (i + 1, T(STECCHE[i][0]))
            p_st = dollari(prezzo_stecca(i)) if negozio else ""
            r_st = negozio and soldi() < prezzo_stecca(i)
        else:
            v_st, p_st, r_st = "-", "", False
        if ge:
            tg = ge[i_g % len(ge)]
            v_ge = T("ch_" + tg)
            if negozio:
                p_ge = dollari(gesso_dati(tg)[2])
                r_ge = soldi() < gesso_dati(tg)[2]
            else:
                p_ge, r_ge = "x%d" % int(scorta.get(tg, 0)), False
        else:
            v_ge, p_ge, r_ge = T("ch_none"), "", False
        voci = [(T("cue"), v_st, p_st, r_st, len(st) > 1),
                (T("chalk_row"), v_ge, p_ge, r_ge, len(ge) > 1),
                (T("back"), None, "", False, False)]
        rett = _righe_vetrina(sc, voci, sel, s(520), s(58))
        if avviso[0] and pygame.time.get_ticks() < avviso[1]:
            c = FONTS["small"].render(avviso[0], True, avviso[2])
            sc.blit(c, c.get_rect(center=(WIN_W // 2, s(716))))
        aiuto_menu(sc)
        for i, r in enumerate(rett):
            if MOUSE_VIVO[0] and r.collidepoint(mouse):
                sel = i
        presenta()


PREMI_TORNEO = (50, 75, 100, 150, 200, 300)     # incontro vinto, per turno
PREMIO_CAMPIONE = 150


def _torneo(sc, clock, logo, disc_vera, k_t):
    """Il torneo scelto. Il salvataggio e' per torneo: se ne possono
    tenere a meta' anche piu' d'uno."""
    disc = "%d_%d" % (disc_vera, k_t)
    frame_t = TORNEI.get(disc_vera, TORNEI[0])[k_t][2]
    salvato = carica_torneo(disc)
    if salvato:
        tab = salvato["tab"]
        scelta = schermata_torneo(
            sc, clock, logo, T("t_saved"),
            "%s  -  %s" % (tab_turno(tab), T("t_vs") % tab_avversario(tab)),
            None, [T("t_continue"), T("t_new"), T("back")],
            ["continua", "nuovo", "menu"])
        if scelta in ("menu", "quit"):
            return scelta
        if scelta == "nuovo":
            cancella_torneo(disc)
            salvato = None

    in_corso = None
    if salvato:
        tab = salvato["tab"]
        giri = (list(salvato["giri"][0]), list(salvato["giri"][1]))
        NOMI[0] = salvato.get("nome") or CFG["nomi"][0]
        BANDIERA[0] = salvato.get("bandiera") or ""
        in_corso = salvato.get("partita")
    else:
        esito = schermata_nomi(sc, clock, logo, True, False)
        if esito != "free_go":
            return esito
        giri = tavoli_torneo()
        tab = tabellone_nuovo()
        salva_torneo(disc, tab, giri, NOMI[0], BANDIERA[0])

    while True:
        avv = tab_avversario(tab)
        if avv is None:                     # non dovrebbe capitare
            return "menu"
        NOMI[1] = avv
        BANDIERA[1] = PAESI.get(avv, "")
        i_panno, i_bordo = tavolo_del_turno(
            disc_vera, tab["vinte"] + 1, giri)
        TURNO_ORA[0] = tab["vinte"] + 1
        record = CFG.get("torneo_record", 0)
        quanti = (frame_t + 1) // 2         # i frame da vincere

        def a_fine_frame(vinti, n_frame, tab=tab, giri=giri):
            salva_torneo(disc, tab, giri, NOMI[0], BANDIERA[0],
                         {"vinti": vinti, "n_frame": n_frame})

        if in_corso and max(in_corso.get("vinti", [0, 0])) >= quanti:
            # il match era gia' chiuso quando si e' usciti: vale il
            # risultato, non si rigioca
            v = in_corso["vinti"]
            fine = "vinto" if v[0] > v[1] else "perso"
        else:
            scelta = schermata_tabellone(
                sc, clock, logo, tab, tab_turno(tab),
                T("t_vs") % avv, [T("t_go"), T("back")], ["gioca", "menu"],
                scelte=True)
            if scelta != "gioca":
                return scelta

            musica_gioco()
            TORNEO_TURNO[0] = len(tab_oggi(tab))
            fine = gioca(sc, clock, logo, bravura_del_turno(tab),
                         torneo=tab_turno(tab), panno=i_panno, bordo=i_bordo,
                         serve=quanti, inizio=in_corso,
                         a_fine_frame=a_fine_frame)
            if fine in ("quit", "menu"):
                return fine
        in_corso = None

        vinto = (fine == "vinto")
        tab_avanza(tab, vinto)
        premio = 0
        if vinto:
            k = max(0, min(len(PREMI_TORNEO) - 1, tab["vinte"] - 1))
            premio = PREMI_TORNEO[k]
            if len(tab_oggi(tab)) == 1:
                premio += PREMIO_CAMPIONE
            soldi(premio)
            salva_config()
        if tab["vinte"] > CFG.get("torneo_record", 0):
            CFG["torneo_record"] = tab["vinte"]
            salva_config()
        record = CFG.get("torneo_record", 0)
        sotto_t = T("t_record") % record
        if premio:
            sotto_t += "     " + T("premio") % dollari(premio)
        # fuori o campione il torneo e' chiuso; se no si salva il turno
        if tab["fuori"] or len(tab_oggi(tab)) == 1:
            cancella_torneo(disc)
        else:
            salva_torneo(disc, tab, giri, NOMI[0], BANDIERA[0])

        if vinto and len(tab_oggi(tab)) == 1:
            dopo = schermata_tabellone(
                sc, clock, logo, tab, T("t_champ"),
                sotto_t,
                [T("t_again"), T("back")], ["ancora", "menu"])
        elif vinto:
            dopo = schermata_tabellone(
                sc, clock, logo, tab, T("t_won") % avv,
                sotto_t,
                [T("t_next"), T("back")], ["avanti", "menu"])
        else:
            dopo = schermata_tabellone(
                sc, clock, logo, tab, T("t_lost") % avv,
                T("t_record") % record,
                [T("t_again"), T("back")], ["ancora", "menu"])
        if dopo in ("menu", "quit"):
            return dopo
        if dopo == "ancora":
            tab = tabellone_nuovo()
            giri = tavoli_torneo()
            salva_torneo(disc, tab, giri, NOMI[0], BANDIERA[0])


# ------------------------------------------------------------- la partita


def applica_tavolo(i_panno, i_bordo):
    """Dopo le impostazioni: se hai fissato un panno o un bordo si vede
    subito, senza aspettare la partita dopo. Se sono su "a caso" resta
    quello che c'e' gia'."""
    if 0 <= CFG["panno"] < len(PANNI):
        i_panno = CFG["panno"]
    if 0 <= CFG["bordo"] < len(BORDI):
        i_bordo = CFG["bordo"]
    return i_panno, i_bordo


PAGA_CPU = 10           # per frame, vincendo contro il computer...
PAGA_LIVELLO = 2        # ...piu' questo per ogni livello sopra il primo
PAGA_PERSA = 5          # per frame, perdendo: non copre tutto il gesso
PAGA_DUE = 8            # per frame, in due sullo stesso computer


def gioca(sc, clock, logo, cpu=None, torneo=False, panno=None, bordo=None,
          serve=1, inizio=None, a_fine_frame=None):
    """Una partita, e uscendo silenzio: qualunque strada si prenda per
    lasciare il tavolo, il pubblico e l'arbitro si fermano."""
    DENTRO_PARTITA[0] = True
    TAV_PROVA[0] = BORDO_PROVA[0] = None    # le prove valgono una partita
    SCRITTA_PROVA[0] = ""
    PALLE_VISTA[0] = None
    misura_palle(GIOCO[0])
    try:
        return _gioca(sc, clock, logo, cpu, torneo, panno, bordo, serve,
                      inizio, a_fine_frame)
    finally:
        DENTRO_PARTITA[0] = False
        misura_palle(0)
        zittisci()


def _gioca(sc, clock, logo, cpu=None, torneo=False, panno=None, bordo=None,
           serve=1, inizio=None, a_fine_frame=None):
    """Una sessione al tavolo. ESC apre la pausa. Con cpu diverso da
    None il secondo giocatore e' il computer, e quel numero e' il suo
    livello. Nel torneo il tavolo lo passa il torneo e alla fine si
    torna indietro con "vinto" o "perso". Serve e' quanti frame bisogna
    vincere per prendersi il match."""
    font, small, fnum = FONTS["font"], FONTS["num"], FONTS["num"]
    small = FONTS["small"]
    if panno is not None and bordo is not None:
        i_panno, i_bordo = panno, bordo         # nel torneo lo sceglie lui
    else:
        # quello scelto nelle impostazioni; se e' "a caso" si sorteggia
        # adesso, a ogni partita un tavolo diverso
        i_panno, i_bordo = sorteggia_tavolo()
    musica_gioco()

    partita = Partita(GIOCO[0])
    PALLE_TORNEO[0] = (TORNEO_PALLE.get(TURNO_ORA[0]) if torneo
                       else None)
    applica_palle()             # le palle col set di questo gioco
    sorteggia_stecca_avv(cpu is not None)
    GESSO[:] = [1.0, 1.0]
    GESSO_TIRI[:] = [0, 0]
    GESSO_INF[0] = (cpu is None and not torneo)
    if not GESSO_INF[0]:
        prepara_gessi(False)
    CPU_ORA[0] = cpu
    if cpu is not None:
        CPU_CUBO[0] = gesso_dati(gesso_cpu_tipo(cpu))[1]
    if partita.gioco not in (3, 7):          # ai birilli il triangolo non c'e'
        suona_triangolo()
    del CODA_VOCE[:]
    dice("break")
    carico = False              # sto trascinando la stecca
    potenza = 0.0               # 0..1, quanto e' tirata indietro
    dir_tiro = Vector2(1, 0)    # direzione, bloccata quando comincio a tirare
    ancora = Vector2(0, 0)      # dov'era il mouse quando ho premuto
    stato = None
    cpu_tiro = None             # il colpo che il computer ha gia' deciso
    cpu_pensa = None            # il ragionamento in corso, a pezzi
    cpu_attesa = 0.0            # il tempo che si prende prima di muovere
    cpu_da = Vector2(1, 0)      # da dove parte la stecca quando va a mirare
    # La mira resta del mouse, ma non e' piu' il punto dove sta la
    # freccia a decidere l'angolo. Se sposti di colpo, la mira salta
    # dove punti, come prima. Se muovi piano, ogni pixel gira la mira di
    # un ventesimo di grado: e' come avere un braccio lungo dodici volte
    # il tavolo, e sui tagli sottili si dosa invece di saltare.
    mira_ang = None             # l'angolo della mira, in gradi
    mouse_era = Vector2(mouse_gioco())
    mano = None                 # la bianca in mano, senza mouse
    tiro_era = True             # il tasto del tiro era gia' giu'

    i_tri = random.randrange(len(TRIANGOLI))
    resta_tri = TRI_TEMPO       # il triangolo si vede due secondi e poi via
    # l'orologio del tiro: nel torneo e' fisso, se no lo decidono le
    # impostazioni, e a zero non c'e' proprio
    orologio = TEMPO_TORNEO if torneo else CFG.get("tempo", 0)
    resta_t = float(orologio)
    vinti = [0, 0]              # i frame vinti nel match
    n_frame = 0                 # quanti se ne sono giocati
    contato = False             # il frame finito e' gia' stato messo a conto
    premio_ora = 0              # quanto si e' guadagnato a fine match
    # si riprende un match salvato: i frame gia' vinti e chi spacca
    if inizio:
        vinti = list(inizio.get("vinti", [0, 0]))[:2]
        n_frame = int(inizio.get("n_frame", 0))
        partita.turno = n_frame % 2
        imposta_msg(partita, "breaks", _mn(partita.turno))
        partita.msg_chi = partita.turno

    while True:
        dt = clock.tick(60) / 1000.0
        musica_gioco()
        mouse = Vector2(mouse_gioco())
        scarto = mouse - mouse_era
        mouse_era = Vector2(mouse)
        modo = modo_comandi()
        usa_mouse = (modo == "mouse")
        c_pad = pad() if modo == "pad" else None
        in_moto = stato is not None
        # quando tocca al computer il mouse non comanda piu' niente
        suo = (cpu is not None and partita.turno == 1
               and not partita.finita and not in_moto)

        for ev in eventi():
            if ev.type == pygame.QUIT:
                return "quit"

            if partita.finita and ev.type in (
                    pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE \
                        and not torneo:
                    return "menu"
                if max(vinti) >= serve:
                    # match chiuso
                    if torneo:
                        return "vinto" if vinti[0] > vinti[1] else "perso"
                    return "menu"
                # un frame e' finito ma il match no: si rimette il tavolo
                n_frame += 1
                partita.reset()
                partita.turno = n_frame % 2     # si spacca a turno
                imposta_msg(partita, "breaks", _mn(partita.turno))
                partita.msg_chi = partita.turno
                del CODA_VOCE[:]
                dice("break")
                stato = None
                contato = False
                potenza, carico = 0.0, False
                cpu_tiro, cpu_attesa, cpu_pensa = None, 0.0, None
                i_tri = random.randrange(len(TRIANGOLI))
                resta_tri = TRI_TEMPO
                resta_t = float(orologio)
                clock.tick(60)
                continue

            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    # a partita finita non c'e' niente da riprendere:
                    # ESC porta dritto al menu
                    if partita.finita:
                        return "menu"
                    fermo = True
                    ferma_orologio(False)   # in pausa il conto tace
                    suona_pausa()
                    # la foto del tavolo si scatta una volta sola: se no
                    # tornando dalle impostazioni la pausa si ridisegna
                    # sopra la schermata delle impostazioni
                    sotto = sc.copy()
                    while fermo:
                        scelta = schermata_pausa(sc, clock, sotto)
                        if scelta == "settings":
                            if schermata_setting(sc, clock, logo,
                                                 panno is not None) == "quit":
                                return "quit"
                            if panno is None:
                                i_panno, i_bordo = applica_tavolo(
                                    i_panno, i_bordo)
                            # anche l'orologio: se lo spegni dalla pausa
                            # deve sparire subito, non alla partita dopo
                            orologio = (TEMPO_TORNEO if torneo
                                        else CFG.get("tempo", 0))
                        else:
                            fermo = False
                    resta_t = float(orologio)
                    # il tasto che ha chiuso la pausa non deve anche tirare
                    tiro_era = True
                    if scelta in ("quit", "menu"):
                        return scelta
                    suona_fx("menu_chiudi")
                    if scelta == "nuova":
                        partita.reset()
                        del CODA_VOCE[:]
                        dice("break")
                        stato = None
                        cpu_tiro, cpu_attesa, cpu_pensa = None, 0.0, None
                        i_tri = random.randrange(len(TRIANGOLI))
                        resta_tri = TRI_TEMPO
                        resta_t = float(orologio)
                        potenza, carico = 0.0, False
                        if panno is None:
                            i_panno, i_bordo = applica_tavolo(
                                i_panno, i_bordo)
                    clock.tick(60)
                    continue
                if not in_moto and not partita.finita and not suo \
                        and not getattr(ev, "dal_pad", False):
                    if ev.key == tasto("eff_su"):
                        partita.spin.y = min(1.0, partita.spin.y + 0.25)
                    if ev.key == tasto("eff_giu"):
                        partita.spin.y = max(-1.0, partita.spin.y - 0.25)
                    if ev.key == tasto("eff_dx"):
                        partita.spin.x = min(1.0, partita.spin.x + 0.25)
                    if ev.key == tasto("eff_sx"):
                        partita.spin.x = max(-1.0, partita.spin.x - 0.25)
                    if ev.key == tasto("eff_via"):
                        partita.spin.update(0, 0)

            # il gesso: quando tocca a te e le palle sono ferme
            if ev.type == pygame.KEYDOWN and ev.key == tasto("gesso") \
                    and not (in_moto or suo or partita.finita or carico):
                metti_gesso(partita.turno)

            # piramide: si sceglie la palla con cui tirare. Col mouse il
            # tasto destro sulla palla, da tastiera e joystick si scorre
            if partita.gioco == 8 and not (partita.finita or in_moto or suo
                                           or partita.ball_in_hand
                                           or carico or partita.spaccata):
                if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 3:
                    for q in partita.palle:
                        if not q.dentro and \
                                (q.pos - mouse).length() < BALL_R * 1.3:
                            partita.bilia_tiro = q.num
                            mira_ang = None if usa_mouse else mira_ang
                            suona_fx("menu_tic", 0.6)
                            break
                if ev.type == pygame.KEYDOWN and ev.key == tasto("cambia"):
                    partita.cambia_bilia(1)
                    if usa_mouse:
                        mira_ang = None
                    suona_fx("menu_tic", 0.6)

            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                if partita.finita or in_moto or suo or not usa_mouse:
                    pass
                elif partita.ball_in_hand:
                    if partita.posto_libero(mouse):
                        partita.cue().pos.update(mouse)
                        partita.ball_in_hand = False
                        mira_ang = None         # la mira riparte da capo
                        partita.msg_key = "to_play"
                        imposta_msg(partita, "to_play", _mn(partita.turno))
                        partita.msg_chi = partita.turno
                else:
                    d = (Vector2(1, 0).rotate(mira_ang)
                         if mira_ang is not None
                         else mouse - partita.cue().pos)
                    if d.length_squared() > 1e-6:
                        dir_tiro = d.normalize()
                        ancora = Vector2(mouse)
                        potenza = 0.0
                        carico = True

            if ev.type == pygame.MOUSEBUTTONUP and ev.button == 1:
                if carico and not in_moto and not partita.finita and not suo \
                        and usa_mouse:
                    carico = False
                    if potenza > 0.02:
                        partita.foto()
                        _, d_pot, d_eff = doti_di(partita.turno)
                        consuma_gesso(partita.turno)
                        partita.cue().vel = dir_tiro * (
                            TIRO_MAX * spinta(potenza) * d_pot / 100.0)
                        for q in partita.palle:
                            q.di_sponda = False
                        stato = {"imbucate": [], "prima": None,
                                 "sponda": False,
                                 "bilia": partita.cue().num,
                                 "spin_x": partita.spin.x * d_eff / 100.0,
                                 "spin_y": partita.spin.y * d_eff / 100.0}
                        segna(stato, "cue", TIRO_MAX * potenza)
                    potenza = 0.0

        # La potenza e' quanto tiri indietro lungo la linea di mira:
        # vai indietro e carica, torni avanti e scarica. La direzione resta
        # quella del momento in cui hai premuto, cosi' trascinando non
        # cambi anche la mira.
        # La mira: il mouse comanda, ma in due modi. Spostamento largo,
        # la mira va dove punti; spostamento piccolo, si gira di poco
        # per volta e i tagli sottili si dosano. Le frecce fanno lo
        # stesso ancora piu' fine, per chi le preferisce.
        if not in_moto and not suo and not partita.finita and not carico:
            cue = partita.cue()
            if cue is not None and not cue.dentro and not usa_mouse:
                # senza mouse la mira parte da dove era la stecca
                if mira_ang is None:
                    mira_ang = math.degrees(math.atan2(dir_tiro.y,
                                                       dir_tiro.x))
            elif cue is not None and not cue.dentro:
                if mira_ang is None:
                    v = mouse - cue.pos
                    if v.length_squared() < 1e-6:
                        v = Vector2(1, 0)
                    mira_ang = math.degrees(math.atan2(v.y, v.x))
                elif scarto.length_squared() > 0.0:
                    # Due modi che si mescolano, senza scalini: il
                    # movimento piccolo gira la mira di pochissimo, il
                    # movimento largo la porta dove punti. In mezzo si
                    # passa dall'uno all'altro un po' per volta, cosi'
                    # la stecca non salta mai da una palla all'altra.
                    quanto = scarto.length()
                    peso = max(0.0, min(1.0, (quanto - SALTO_PIANO) /
                                        (SALTO_MIRA - SALTO_PIANO)))
                    d = Vector2(1, 0).rotate(mira_ang)
                    fianco = scarto.dot(Vector2(-d.y, d.x))
                    mira_ang += math.degrees(fianco / BRACCIO_MIRA) * \
                        (1.0 - peso)
                    v = mouse - cue.pos
                    if peso > 0.0 and v.length_squared() > 1e-6:
                        punta = math.degrees(math.atan2(v.y, v.x))
                        gira = (punta - mira_ang + 540.0) % 360.0 - 180.0
                        mira_ang += gira * peso

            if cue is not None and not cue.dentro and mira_ang is not None:
                tasti = pygame.key.get_pressed()
                giro = (1 if giu("mira_dx", tasti) else 0) - \
                       (1 if giu("mira_sx", tasti) else 0)
                piano = giu("fine", tasti)
                veloce = 14.0 if usa_mouse else GIRO_TAST
                if c_pad is not None:
                    giro += ((1 if pad_tasto(
                        c_pad, pygame.CONTROLLER_BUTTON_DPAD_RIGHT) else 0) -
                        (1 if pad_tasto(
                            c_pad, pygame.CONTROLLER_BUTTON_DPAD_LEFT)
                         else 0))
                    piano = piano or pad_tasto(
                        c_pad, pygame.CONTROLLER_BUTTON_LEFTSHOULDER)
                    # la levetta: poco di lato gira piano, tutta gira forte
                    lx = pad_asse(c_pad, pygame.CONTROLLER_AXIS_LEFTX)
                    if lx:
                        mira_ang += (math.copysign(abs(lx) ** 2.5, lx) *
                                     (GIRO_FINE * 4 if piano else GIRO_PAD)
                                     * dt)
                if giro:
                    mira_ang += giro * (GIRO_FINE if piano else veloce) * dt

        # l'effetto col joystick: la levetta destra sposta il punto come un
        # cursore, e lasciandola il punto resta dov'e'. Prima lo metteva
        # dove puntava la levetta, e quando tornava al centro da sola se lo
        # riportava dietro.
        if c_pad is not None and not in_moto and not suo \
                and not partita.finita:
            rx = pad_asse(c_pad, pygame.CONTROLLER_AXIS_RIGHTX)
            ry = pad_asse(c_pad, pygame.CONTROLLER_AXIS_RIGHTY)
            if rx or ry:
                e = partita.spin + Vector2(rx, -ry) * (1.6 * dt)
                if e.length() > 1.0:
                    e.scale_to_length(1.0)
                partita.spin.update(e)
            if pad_tasto(c_pad, pygame.CONTROLLER_BUTTON_Y):
                partita.spin.update(0, 0)

        # Senza mouse: la bianca in mano si sposta coi tasti o con la
        # levetta e si posa col tasto del tiro; il tiro si carica tenendo
        # giu' e parte quando si lascia.
        if not usa_mouse:
            tasti = pygame.key.get_pressed()
            premuto = (pad_tira(c_pad) if modo == "pad"
                       else giu("tiro", tasti))
            scatto = premuto and not tiro_era
            tiro_era = premuto
            libero = not (in_moto or suo or partita.finita)
            if libero and partita.ball_in_hand:
                carico = False
                if mano is None:
                    cue = partita.cue()
                    if cue is not None and not cue.dentro:
                        mano = Vector2(cue.pos)
                    elif partita.gioco in (2, 6):
                        mano = Vector2(sn_posti()[SN_MARRONE])
                    else:
                        mano = Vector2(LINEA_X, PLAY.centery)
                sposta = Vector2(
                    (1 if giu("mira_dx", tasti) else 0) -
                    (1 if giu("mira_sx", tasti) else 0),
                    (1 if giu("palla_giu", tasti) else 0) -
                    (1 if giu("palla_su", tasti) else 0))
                piano = giu("fine", tasti)
                if c_pad is not None:
                    sposta += Vector2(
                        pad_asse(c_pad, pygame.CONTROLLER_AXIS_LEFTX),
                        pad_asse(c_pad, pygame.CONTROLLER_AXIS_LEFTY))
                    for b, v in ((pygame.CONTROLLER_BUTTON_DPAD_RIGHT,
                                  (1, 0)),
                                 (pygame.CONTROLLER_BUTTON_DPAD_LEFT,
                                  (-1, 0)),
                                 (pygame.CONTROLLER_BUTTON_DPAD_DOWN,
                                  (0, 1)),
                                 (pygame.CONTROLLER_BUTTON_DPAD_UP,
                                  (0, -1))):
                        if pad_tasto(c_pad, b):
                            sposta += Vector2(v)
                    piano = piano or pad_tasto(
                        c_pad, pygame.CONTROLLER_BUTTON_LEFTSHOULDER)
                if sposta.length_squared() > 1.0:
                    sposta.scale_to_length(1.0)
                mano += sposta * MANO_V * K * (0.2 if piano else 1.0) * dt
                mano.x = max(PLAY.left + BALL_R, min(PLAY.right - BALL_R,
                                                     mano.x))
                mano.y = max(PLAY.top + BALL_R, min(PLAY.bottom - BALL_R,
                                                    mano.y))
                if scatto and partita.posto_libero(mano):
                    partita.cue().pos.update(mano)
                    partita.ball_in_hand = False
                    partita.msg_key = "to_play"
                    imposta_msg(partita, "to_play", _mn(partita.turno))
                    partita.msg_chi = partita.turno
            elif libero and mira_ang is not None:
                mano = None
                if scatto and not carico:
                    dir_tiro = Vector2(1, 0).rotate(mira_ang)
                    potenza = 0.0
                    carico = True
                elif carico and premuto:
                    potenza = min(1.0, potenza + dt / CARICA_T)
                elif carico:
                    carico = False
                    if potenza > 0.02:
                        partita.foto()
                        _, d_pot, d_eff = doti_di(partita.turno)
                        consuma_gesso(partita.turno)
                        partita.cue().vel = dir_tiro * (
                            TIRO_MAX * spinta(potenza) * d_pot / 100.0)
                        for q in partita.palle:
                            q.di_sponda = False
                        stato = {"imbucate": [], "prima": None,
                                 "sponda": False,
                                 "bilia": partita.cue().num,
                                 "spin_x": partita.spin.x * d_eff / 100.0,
                                 "spin_y": partita.spin.y * d_eff / 100.0}
                        segna(stato, "cue", TIRO_MAX * potenza)
                    potenza = 0.0
            else:
                carico = False

        if carico and usa_mouse:
            dietro = (mouse - ancora).dot(-dir_tiro)
            potenza = max(0.0, min(1.0, dietro / TRASCINO))

        # ---------------------------------------------- tocca al computer
        # Non risponde sul colpo. Prende la stecca dov'era, la gira fino
        # alla palla che ha scelto, fa le sue stoccate a vuoto e solo
        # allora tira. Se no sembra che sapesse gia' tutto.
        if suo:
            if partita.ball_in_hand:
                if cpu_attesa <= 0.0:
                    cpu_attesa = CPU_PIAZZA
                cpu_attesa -= dt
                if cpu_attesa <= 0.0:
                    dove_bianca = posto_cpu(partita, cpu)
                    if dove_bianca is not None:
                        partita.cue().pos.update(dove_bianca)
                    partita.ball_in_hand = False
                    partita.msg_key = "to_play"
                    imposta_msg(partita, "to_play", _mn(partita.turno))
                    partita.msg_chi = partita.turno
                    cpu_attesa = 0.0
            else:
                if cpu_tiro is None:
                    # pensa un pezzo per fotogramma, finche' ha deciso
                    if cpu_pensa is None:
                        cpu_pensa = pensa_cpu(partita, cpu)
                    fino = pygame.time.get_ticks() + 14
                    try:
                        while pygame.time.get_ticks() < fino:
                            next(cpu_pensa)
                    except StopIteration as fatto:
                        cpu_tiro = fatto.value
                        cpu_pensa = None
                        cpu_da = Vector2(dir_tiro)
                        giro = (cpu_da.angle_to(cpu_tiro[0]) + 180.0) \
                            % 360.0 - 180.0
                        if abs(giro) < 12.0:
                            # se la stecca era gia' li' non si vedrebbe
                            # girare
                            cpu_da = cpu_tiro[0].rotate(-38.0)
                        cpu_attesa = CPU_CERCA + CPU_MIRA
                if cpu_tiro is not None:
                    cpu_attesa -= dt
                if cpu_tiro is not None and cpu_attesa <= 0.0:
                    d_cpu, f_cpu = cpu_tiro
                    gesso_del_computer()
                    consuma_gesso(1)
                    dir_tiro = Vector2(d_cpu)
                    partita.foto()
                    partita.cue().vel = d_cpu * (TIRO_MAX * f_cpu)
                    for q in partita.palle:
                        q.di_sponda = False
                    stato = {"imbucate": [], "prima": None, "sponda": False,
                             "bilia": partita.cue().num,
                             "spin_x": 0.0, "spin_y": 0.0}
                    segna(stato, "cue", TIRO_MAX * f_cpu)
                    cpu_tiro, cpu_attesa, cpu_pensa = None, 0.0, None
        else:
            cpu_tiro, cpu_attesa, cpu_pensa = None, 0.0, None

        if orologio:
            if stato is None and not partita.finita:
                resta_t -= dt
                suona_orologio(resta_t)
                if resta_t <= 0.0:
                    partita.scaduto()
                    suona_festa("delusione_forte")
                    resta_t = float(orologio)
                    carico, potenza = False, 0.0
                    cpu_tiro, cpu_attesa, cpu_pensa = None, 0.0, None
            elif stato is not None:
                resta_t = float(orologio)
                ferma_orologio()

        if resta_tri > 0.0 and (stato is not None or not partita.spaccata):
            resta_tri = 0.0         # si e' tirato: via il triangolo
        elif resta_tri > 0.0:
            resta_tri -= dt

        aggiorna_voce()

        # come sono girate le palle: una volta per fotogramma, basta e avanza
        ruota_palle(partita.palle, dt)

        # simulazione a sottopassi, cosi' a palla veloce niente attraversamenti
        if stato is not None:
            vmax = max((b.vel.length() for b in partita.palle if not b.dentro),
                       default=0.0)
            n = max(1, min(40, int(vmax * dt / (BALL_R * 0.45)) + 1))
            for _ in range(n):
                passo_fisica(partita.palle, dt / n, stato)
            suona_eventi(stato)
            if tutto_fermo(partita.palle):
                chi_era = partita.turno
                partita.valuta(stato)
                partita.delusione(stato)
                suona_festa(partita.festa)
                if partita.turno != chi_era and not partita.finita:
                    suona_turno()
                if partita.finita and not contato:
                    contato = True
                    if partita.vincitore is not None:
                        vinti[partita.vincitore] += 1
                    # match chiuso fuori dal torneo: si guadagna qualcosa
                    # per ogni frame giocato, abbastanza per i gessetti
                    if not torneo and max(vinti) >= serve:
                        frame_g = n_frame + 1
                        if cpu is None:
                            premio_ora = PAGA_DUE * frame_g
                        elif vinti[0] > vinti[1]:
                            premio_ora = (PAGA_CPU + PAGA_LIVELLO * cpu) \
                                * frame_g
                        else:
                            premio_ora = PAGA_PERSA * frame_g
                        soldi(premio_ora)
                        salva_config()
                    # salvataggio a ogni frame finito: riaprendo si
                    # riparte dal frame dopo, col punteggio di adesso
                    if a_fine_frame is not None:
                        a_fine_frame(list(vinti), n_frame + 1)
                partita.spin.update(0, 0)
                stato = None

        # ------------------------------------------------------ disegno
        if TAV_PROVA[0] is not None:
            i_panno, i_bordo = tavolo_fisso(GIOCO[0], TAV_PROVA[0] + 1) or \
                (i_panno, i_bordo)
        if BORDO_PROVA[0] is not None:
            i_bordo = BORDO_PROVA[0]
        BORDO_ORA[0] = i_bordo
        PANNO_ORA[0] = i_panno
        disegna_tavolo(sc, i_panno, i_bordo, gioco=partita.gioco)

        for bir in BIRILLI:
            disegna_birillo(sc, bir)

        for b in partita.palle:
            if not b.dentro:
                disegna_palla(sc, b, fnum)

        if PROVA[0]:
            disegna_prova(sc)

        if resta_tri > 0.0 and partita.gioco not in (3, 7):
            posa_triangolo(sc, i_tri, resta_tri)

        if suo:
            if cpu_tiro is not None:
                d_vista, f_vista = mira_cpu(cpu_da, cpu_tiro, cpu_attesa)
                traccia_mira(sc, partita, d_vista, f_vista, linea=False)
        elif partita.ball_in_hand and not partita.finita:
            punto = mouse if usa_mouse or mano is None else mano
            ok = partita.posto_libero(punto)
            col = (255, 255, 255) if ok else (220, 70, 70)
            anello(sc, col, punto, BALL_R, 2)
        elif stato is None and not partita.finita:
            # piramide: la palla scelta ha il suo cerchio, e le altre un
            # cerchietto sottile che dice che si possono scegliere
            if partita.gioco == 8 and partita.cue() is not None \
                    and not partita.spaccata:
                for q in partita.palle:
                    if not q.dentro and q is not partita.cue():
                        anello(sc, (150, 160, 170), q.pos, BALL_R + 2, 1)
                anello(sc, (255, 206, 60), partita.cue().pos, BALL_R + 3, 2)
            if carico:
                verso = dir_tiro
            elif mira_ang is not None:
                verso = Vector2(1, 0).rotate(mira_ang)
            else:
                verso = mouse - partita.cue().pos
            traccia_mira(sc, partita, verso, potenza)

        pot_vista = potenza
        if suo and cpu_tiro is not None:
            pot_vista = mira_cpu(cpu_da, cpu_tiro, cpu_attesa)[1]
        pannello(sc, partita, pot_vista,
                 resta_t if (orologio and not partita.finita)
                 else None,
                 torneo if isinstance(torneo, int) and torneo is not True
                 else 0,
                 vinti if serve > 1 else None, serve)
        if torneo:
            disegna_stemma_gioco(sc, torneo)

        if partita.finita:
            col_premio = bool(premio_ora and max(vinti) >= serve)
            box = pygame.Surface((s(520), s(170) if col_premio else s(110)),
                                 pygame.SRCALPHA)
            box.fill((10, 10, 14, 225))
            sc.blit(box, box.get_rect(center=(
                WIN_W // 2, WIN_H // 2 + (s(30) if col_premio else 0))))
            t = font.render(messaggio_ora(partita), True, col_messaggio(partita))
            sc.blit(t, t.get_rect(center=(WIN_W // 2, WIN_H // 2 - s(14))))
            t = small.render(T("avanti") if max(vinti) < serve else T("fine"),
                             True, TESTO_OPACO)
            sc.blit(t, t.get_rect(center=(WIN_W // 2, WIN_H // 2 + s(20))))
            if premio_ora and max(vinti) >= serve:
                t = font.render(T("premio") % dollari(premio_ora), True,
                                ORO_SCELTA)
                sc.blit(t, t.get_rect(center=(WIN_W // 2,
                                              WIN_H // 2 + s(80))))

        scritta_prova(sc)
        presenta()


# ------------------------------------------------------------------ main


# La finestra si puo' allargare e mettere a tutto schermo, ma il gioco
# disegna sempre su una scena di misura fissa: alla fine la scena viene
# ingrandita per riempire lo schermo tenendo le proporzioni, con due
# bande nere se la forma non coincide. Cosi' dentro non si deforma niente
# e tutte le coordinate restano quelle di sempre.
SCENA = None
SCHERMO = None
VISTA = [1.0, 0, 0]             # scala, spostamento x, spostamento y
PIENO = False


def apri_finestra(pieno=False):
    """A schermo intero si chiede proprio la risoluzione scelta, non
    "quella che c'e'": cosi' su uno schermo fitto i pixel che disegniamo
    finiscono uno sopra l'altro con quelli veri e le scritte restano
    nitide. Se il monitor non sa fare quella misura, SDL prende la piu'
    vicina e ci pensa misura_vista a centrare il disegno."""
    global SCHERMO, SCENA, PIENO
    PIENO = pieno
    if pieno:
        try:
            SCHERMO = pygame.display.set_mode((WIN_W, WIN_H),
                                              pygame.FULLSCREEN)
        except pygame.error:
            SCHERMO = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    else:
        SCHERMO = pygame.display.set_mode((WIN_W, WIN_H), pygame.RESIZABLE)
    if SCENA is None:
        SCENA = pygame.Surface((WIN_W, WIN_H)).convert()
    misura_vista()
    return SCENA


def misura_vista():
    global BORDI_VISTA
    BORDI_VISTA = None
    w, h = SCHERMO.get_size()
    k = min(w / float(WIN_W), h / float(WIN_H))
    VISTA[0] = k
    VISTA[1] = int((w - WIN_W * k) / 2)
    VISTA[2] = int((h - WIN_H * k) / 2)


BORDI_VISTA = None


def presenta():
    """Porta la scena sullo schermo, ingrandita quanto ci sta. Le bande
    che avanzano ai lati non restano nere: ci va lo stesso fondo della
    schermata, stirato a tutto schermo, e la fascia dei comandi le
    attraversa da un lato all'altro. Sullo schermo si copiano solo
    superfici piene: quelle trasparenti sul Mac si rovinano."""
    global BORDI_VISTA
    portafoglio(SCENA)
    k, ox, oy = VISTA
    if abs(k - 1.0) < 0.001 and ox == 0 and oy == 0:
        SCHERMO.blit(SCENA, (0, 0))
    else:
        misura = SCHERMO.get_size()
        tinta = TINTA_ORA[0]
        if BORDI_VISTA is None or BORDI_VISTA[0] != (misura, tinta):
            BORDI_VISTA = ((misura, tinta), pygame.transform.smoothscale(
                fondo(tinta), misura))
        SCHERMO.blit(BORDI_VISTA[1], (0, 0))
        if FOOTER_ORA[0] is not None:
            alto, col_f, vis = FOOTER_ORA[0]
            t = FONDI_TINTE[tinta][1] if tinta in FONDI_TINTE \
                else SFONDO_BORDO
            a = vis * col_f[3] / 255.0
            pieno = tuple(int(col_f[c] * a + t[c] * (1.0 - a))
                          for c in range(3))
            y = int(oy + (WIN_H - alto) * k)
            SCHERMO.fill(pieno, pygame.Rect(0, y, misura[0], misura[1] - y))
        SCHERMO.blit(pygame.transform.smoothscale(
            SCENA, (int(WIN_W * k), int(WIN_H * k))), (ox, oy))
    FOOTER_ORA[0] = None
    pygame.display.flip()


def portafoglio(sc):
    """Il portafoglio, sempre in alto a destra: nei menu e in partita."""
    f = FONTS.get("small")
    if f is None:
        return
    try:
        t = f.render(T("wallet") % dollari(soldi()), True, ORO_SCELTA)
    except (KeyError, TypeError, ValueError):
        return
    sc.blit(t, t.get_rect(topright=(WIN_W - s(24), s(12))))


def mouse_gioco():
    """Dove sta il mouse in coordinate della scena, non dello schermo."""
    mx, my = pygame.mouse.get_pos()
    k, ox, oy = VISTA
    return ((mx - ox) / k, (my - oy) / k)


def eventi():
    """Gli eventi, dopo aver gestito da solo ingrandimento e tutto
    schermo: cosi' funzionano in ogni schermata senza ripetere il codice."""
    fuori = []
    pad_avvia()
    MOUSE_VIVO[0] = False
    for ev in pygame.event.get():
        if ev.type == pygame.MOUSEMOTION:
            MOUSE_VIVO[0] = True
        if PAD_SDL is not None and pygame.CONTROLLERAXISMOTION <= ev.type \
                <= pygame.CONTROLLERDEVICEREMAPPED:
            segna_pad(ev)
            pad_evento(ev, fuori)
            continue
        segna_input(ev)
        if ev.type == pygame.VIDEORESIZE and not PIENO:
            pygame.display.set_mode(ev.size, pygame.RESIZABLE)
            misura_vista()
            continue
        if ev.type == pygame.KEYDOWN and ev.key in (pygame.K_F11,):
            apri_finestra(not PIENO)
            CFG["pieno"] = PIENO        # anche da F11 se lo ricorda
            salva_config()
            continue
        if ev.type == pygame.KEYDOWN and ev.key == pygame.K_F3:
            PROVA[0] = not PROVA[0]     # il controllo delle misure
            continue
        if ev.type == pygame.KEYDOWN and prova_tasto(ev.key):
            continue
        fuori.append(ev)
    return fuori


def barra_scura():
    """La barra del titolo di Windows: bianca su una finestra tutta scura
    stona. Si chiede a Windows di usare la versione scura; su Windows 10
    vecchi l'attributo aveva un altro numero, si provano tutti e due. Su
    Linux e Mac non succede niente e va bene cosi'."""
    try:
        import ctypes
        hwnd = pygame.display.get_wm_info().get("window")
        if not hwnd:
            return
        uno = ctypes.c_int(1)
        for attr in (20, 19):
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                ctypes.c_void_p(hwnd), ctypes.c_int(attr),
                ctypes.byref(uno), ctypes.sizeof(uno))
    except Exception:
        pass


def main():
    pygame.init()
    # Le impostazioni si leggono prima di aprire la finestra: se no
    # "tutto schermo" salvato non veniva mai guardato, perche' CFG era
    # ancora quello di partenza.
    carica_config()
    sc = apri_finestra(CFG.get("pieno", False))
    pygame.display.set_caption("Classic Pool")
    clock = pygame.time.Clock()
    # magro di proposito: il grassetto a questa misura si impasta.
    # Il primo nome che esiste vince: Arial su Windows, Liberation su Linux
    ftex = pygame.font.SysFont("arial,liberationsans,helvetica,dejavusans", 96)

    prepara_texture()
    prepara_trofei()
    tavolo_di_partenza()
    prepara_bandiere()
    NOMI[0], NOMI[1] = CFG["nomi"][0], CFG["nomi"][1]
    band = list(CFG.get("bandiere", ["it", "gb"]))[:2]
    BANDIERA[0] = band[0] if band else ""
    BANDIERA[1] = band[1] if len(band) > 1 else ""
    fai_fonts()
    barra_scura()
    prepara_sfere(ftex)
    apri_audio()
    carica_fx()
    carica_voce()
    logo = logo_elegante(s(190))

    dove = "menu"
    while dove != "quit":
        if dove == "menu":
            dove = schermata_menu(sc, clock, logo)
        elif dove == "gioca":
            dove = schermata_modo(sc, clock, logo)
        elif dove == "settings":
            dove = schermata_setting(sc, clock, logo, puo_riaprire=True)
        elif dove == "regole":
            dove = schermata_regole(sc, clock, logo)
        elif dove == "negozio":
            dove = schermata_vetrina(sc, clock, logo, True)
        elif dove == "borsa":
            dove = schermata_vetrina(sc, clock, logo, False)
        elif dove == "torneo":
            dove = torneo(sc, clock, logo)
            if dove == "menu":
                dove = "gioca"
        elif dove in ("free", "cpu"):
            contro = (dove == "cpu")
            dove = schermata_nomi(sc, clock, logo, contro)
            if dove == "free_go":
                musica_gioco()
                n = CFG.get("match", 1)
                dove = gioca(sc, clock, logo,
                             CFG.get("livello", 1) if contro else None,
                             serve=(n + 1) // 2)
            # si torna dove si era: alla scelta del tipo di partita
            if dove == "menu":
                dove = "gioca"

    CFG["pieno"] = PIENO
    salva_config()
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
