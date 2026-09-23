"""Golden Break - le carte.

Il tavolo da carte, uguale per tutti i giochi di carte: la stessa misura
del tavolo da biliardo, cosi' i fianchi e la barra in basso restano
liberi. Sotto il legno scelto, dentro il panno scelto, sopra la PNG
table_cards.png con la linea che divide il panno dal legno. Niente
sponde e niente buche: al posto delle ombre della sponda, quella morbida
di un tavolo normale.

Si appoggia a biliardo.py per tutto il resto: finestra, caratteri,
sfondo, menu, texture di panni e cornici.
"""
import sys

import pygame


def _base():
    """Il modulo del biliardo gia' aperto: se il gioco e' partito da
    biliardo.py e' __main__, e non va importato una seconda volta (avrebbe
    impostazioni e finestra sue)."""
    m = sys.modules.get("__main__")
    if m is not None and hasattr(m, "tavolo_composto"):
        return m
    import biliardo
    return biliardo


B = _base()

TAVOLO_CARTE = "table_cards.png"
# il panno: dentro la linea della PNG, fin dove arriva il legno
PANNO_CARTE = pygame.Rect(120, 117, 1277, 662)
LEGNO_FUORI = pygame.Rect(95, 88, 1327, 720)    # il bordo esterno del legno
OMBRA_LEGNO = 14        # quanto si allarga l'ombra del panno sul legno
OMBRA_SUL_LEGNO = 120   # quanto scurisce il legno contro il panno (0-255)
LUCE_MEZZO = 26         # quanto schiarisce il centro del panno

COMPOSTO = {}


OMBRA_PANNO = False     # True: il panno rialzato con le ombre


def ombra_tavolo(base, r):
    """Il panno qualche millimetro piu' alto del legno, come sui tavoli da
    carte: niente ombra dentro il panno (quella fa sembrare una sponda),
    ma un'ombra morbida che il panno butta sul legno tutto intorno, piu'
    forte in basso a destra, e sul bordo del panno un filo di luce in
    alto e un filo di scuro in basso. Al centro un filo di luce."""
    # l'ombra sul legno, fuori dal panno
    om = pygame.Surface(base.get_size(), pygame.SRCALPHA)
    for i in range(OMBRA_LEGNO, 0, -1):
        a = int(OMBRA_SUL_LEGNO * (1.0 - i / float(OMBRA_LEGNO + 1)) ** 1.6)
        q = r.inflate(i * 2, i * 2).move(i // 3, i // 2)
        pygame.draw.rect(om, (0, 0, 0, a), q, border_radius=i)
    om.fill((0, 0, 0, 0), r)        # solo sul legno, non sotto il panno
    base.blit(om, (0, 0))
    campo = base.subsurface(r)
    w, h = campo.get_size()
    # il bordo del panno, alzato: luce sopra e a sinistra, scuro sotto
    bordo = pygame.Surface((w, h), pygame.SRCALPHA)
    for k in range(3):
        a_l, a_s = 55 - k * 18, 45 - k * 15
        pygame.draw.line(bordo, (255, 255, 255, a_l), (k, k), (w - 1 - k, k))
        pygame.draw.line(bordo, (255, 255, 255, a_l), (k, k), (k, h - 1 - k))
        pygame.draw.line(bordo, (0, 0, 0, a_s), (k, h - 1 - k),
                         (w - 1 - k, h - 1 - k))
        pygame.draw.line(bordo, (0, 0, 0, a_s), (w - 1 - k, k),
                         (w - 1 - k, h - 1 - k))
    campo.blit(bordo, (0, 0))
    luce = pygame.Surface((w, h), pygame.SRCALPHA)
    for i in range(12):
        k = 1.0 - i / 12.0
        q = pygame.Rect(0, 0, int(w * (0.35 + 0.6 * k)),
                        int(h * (0.35 + 0.6 * k)))
        q.center = (w // 2, h // 2)
        pygame.draw.ellipse(luce, (255, 255, 255, max(1, LUCE_MEZZO // 12)),
                            q)
    campo.blit(luce, (0, 0))


def tavolo_carte(i_panno, i_bordo):
    """Il tavolo montato a strati e ridotto alla misura del biliardo."""
    chiave = (i_panno, i_bordo)
    if chiave in COMPOSTO:
        return COMPOSTO[chiave]
    vero = B.tavolo_vero(os.path.join(cartella_carte(), TAVOLO_CARTE))
    if not vero:
        return None
    base = pygame.Surface(vero.get_size(), pygame.SRCALPHA)
    if B.BORDI and 0 <= i_bordo < len(B.BORDI):
        l = B.texture(B.BORDI[i_bordo][1], (B.LATO_LEGNO, B.LATO_LEGNO))
        if l is not None:
            legno = pygame.Surface(base.get_size(), pygame.SRCALPHA)
            for x in range(0, legno.get_width(), B.LATO_LEGNO):
                for y in range(0, legno.get_height(), B.LATO_LEGNO):
                    legno.blit(l, (x, y))
            legno.blit(B.sagoma_legno(base.get_size()), (0, 0),
                       special_flags=pygame.BLEND_RGBA_MULT)
            base.blit(legno, (0, 0))
    if B.PANNI and 0 <= i_panno < len(B.PANNI):
        q = B.texture(B.PANNI[i_panno][1], (B.LATO_PANNO, B.LATO_PANNO))
        if q is not None:
            campo = base.subsurface(PANNO_CARTE)
            for x in range(0, campo.get_width(), B.LATO_PANNO):
                for y in range(0, campo.get_height(), B.LATO_PANNO):
                    campo.blit(q, (x, y))
    if OMBRA_PANNO:
        ombra_tavolo(base, PANNO_CARTE)
    diamanti_posti(base)
    base.blit(vero, (0, 0))
    if len(COMPOSTO) > 3:
        COMPOSTO.clear()
    COMPOSTO[chiave] = pygame.transform.smoothscale(
        base, (int(B.TAV_W * B.SCALA), int(B.TAV_H * B.SCALA)))
    return COMPOSTO[chiave]


def scelta_tavolo():
    """Il tavolo delle carte: la cornice e' sempre quella di ciliegio, il
    panno si sceglie dal menu delle carte (le stesse texture del
    biliardo). Non segue il tavolo scelto per il biliardo."""
    i = B.CFG.get("panno_carte", -1)
    if i == -1 and B.PANNI:
        i = random.randrange(len(B.PANNI))      # a caso, a ogni partita
    if not isinstance(i, int) or not (0 <= i < len(B.PANNI)):
        i = B._quale(B.PANNI, B.TAVOLO_CASA[0])
    return i, B._quale(B.BORDI, B.TAVOLO_CASA[1])


# ------------------------------------------------------------ le carte
#
# Per ora solo la sagoma: carta bianca davanti, dorso grigio chiaro con
# una cornicetta. Serve a provare come entrano, escono e si muovono sul
# tavolo; la grafica vera arriva dopo, sopra le stesse misure.

import math
import random

CARTA_W, CARTA_H = 61, 88       # alla misura del disegno, poi s()

# I suoni delle carte, nella cartella carte_fx accanto al gioco:
# servi (una carta dal mazzo), giocata (una carta sul tavolo), cattura
# (le carte prese), errore (una mossa che non si puo' fare), colpo (il
# colpo grosso: la scopa, il blackjack), gameover, levelup. Se due file
# finiscono col numero sono lo stesso suono, a caso. Se mancano, silenzio.
# La musica: i loop di carte_audio, uno a caso per partita.
import os
SUONI_CARTE = {}


def carica_suoni():
    if SUONI_CARTE or not B.MUSICA_OK:
        return
    cartella = os.path.join(B.SUONI_DIR, "carte", "fx")
    if not os.path.isdir(cartella):
        return
    for f in sorted(os.listdir(cartella)):
        if not f.lower().endswith((".mp3", ".ogg", ".wav")):
            continue
        nome = os.path.splitext(f)[0].lower().rstrip("0123456789")
        try:
            SUONI_CARTE.setdefault(nome, []).append(
                pygame.mixer.Sound(os.path.join(cartella, f)))
        except pygame.error:
            pass


def musica_carte():
    """Un loop jazz a caso, in ripetizione, al volume della musica di
    gioco. Uscendo sfuma e il menu rimette la sua."""
    if not B.MUSICA_OK:
        return
    cartella = os.path.join(B.SUONI_DIR, "carte", "musica")
    if not os.path.isdir(cartella):
        return
    tracce = [f for f in os.listdir(cartella)
              if f.lower().endswith((".mp3", ".ogg", ".wav"))]
    v = B.CFG.get("musica_gioco", 20)
    if not tracce or v <= 0:
        return
    try:
        pygame.mixer.music.load(os.path.join(cartella, random.choice(tracce)))
        pygame.mixer.music.set_volume(v / 100.0)
        pygame.mixer.music.play(-1)
    except pygame.error:
        pass


def fine_musica_carte():
    if B.MUSICA_OK:
        try:
            pygame.mixer.music.fadeout(500)
        except pygame.error:
            pass


def suona(nome, quanto=0.9):
    gruppo = SUONI_CARTE.get(nome)
    v = B.CFG.get("effetti", 100) / 100.0
    if not gruppo or v <= 0:
        return
    s_ = random.choice(gruppo)
    s_.set_volume(min(1.0, v * quanto))
    s_.play()
TEMPO_VOLO = 0.32               # secondi per andare da un posto all'altro
TEMPO_GIRO = 0.22               # secondi per girarla
FACCIA = {}


# Le carte vere: le facce stanno in biliardo_gfx/carte/facce/<tipo>/,
# un file per carta col suo codice (1d = asso di denari, 10s = re di
# spade: d denari, c coppe, s spade, b bastoni). Ogni mazzo ha la sua
# cartella in carte/mazzi/<nome>/ con dorso.png e scatola.png; il tipo
# di facce si capisce dal nome della cartella (napoletane, toscane,
# francesi). Se una carta manca si disegna la sagoma bianca.
SEMI_IT = ("d", "c", "s", "b")
IMG_CARTE = {}


def cartella_carte():
    return os.path.join(B.IMMAGINI, "carte")


# I tipi di facce: il nome della cartella del mazzo dice quali usare.
# Vanno in ordine, il primo che sta dentro al nome vince.
TIPI_FACCE = ("poker", "napoli", "napoletane", "toscane", "francesi")

# A che famiglia appartengono: i mazzi nostri si comportano come quelli
# veri, cosi' finiscono nei giochi giusti.
FAMIGLIE = {"napoli": "napoletane", "poker": "francesi"}


def tipo_di(nome):
    """Che facce usa un mazzo. Vale la prima parola del nome della
    cartella; se non e' un tipo che conosciamo si cerca dentro al nome,
    come si faceva prima."""
    basso = nome.lower()
    primo = basso.split("_")[0]
    if primo in TIPI_FACCE:
        return primo
    return next((t for t in TIPI_FACCE if t in basso), "napoletane")


def famiglia(tipo=None):
    """Se le carte sono francesi o italiane, mazzi di prova compresi."""
    t = MAZZO_ORA[1] if tipo is None else tipo
    return FAMIGLIE.get(t, t)


def mazzi_disponibili():
    """I mazzi che ci sono: (nome della cartella, tipo di facce)."""
    base = os.path.join(cartella_carte(), "mazzi")
    fuori = []
    if os.path.isdir(base):
        for nome in sorted(os.listdir(base)):
            if not os.path.isdir(os.path.join(base, nome)):
                continue
            tipo = tipo_di(nome)
            fuori.append((nome, tipo))
    return fuori


MAZZO_ORA = [None, "napoletane"]    # la cartella del mazzo e il tipo


def scegli_mazzo(i=0):
    m = mazzi_disponibili()
    if m:
        MAZZO_ORA[0], MAZZO_ORA[1] = m[i % len(m)]
    FACCIA.clear()


def mazzo_codici():
    """I codici delle 40 carte italiane."""
    return ["%d%s" % (n, sm) for sm in SEMI_IT for n in range(1, 11)]


def _immagine(percorso):
    if percorso not in IMG_CARTE:
        try:
            IMG_CARTE[percorso] = pygame.image.load(percorso).convert_alpha()
        except (pygame.error, FileNotFoundError, IOError):
            IMG_CARTE[percorso] = None
    return IMG_CARTE[percorso]


def immagine_carta(codice):
    if codice is None:
        return None
    base = os.path.join(cartella_carte(), "facce", MAZZO_ORA[1])
    for est in (".png", ".jpg", ".jpeg", ".webp"):
        f = os.path.join(base, codice + est)
        if os.path.exists(f):
            return _immagine(f)
    return None


def _solo_pieno(img):
    """Toglie il bordo trasparente o mezzo trasparente attorno alla
    carta: si tiene solo il rettangolo dove la carta e' piena, cosi' non
    resta un filo chiaro quando la si porta alla nostra misura."""
    if img is None:
        return None
    try:
        a = pygame.surfarray.pixels_alpha(img)
        import numpy as np
        pieno = np.asarray(a) >= 250
        del a
        cols = np.nonzero(pieno.any(axis=1))[0]
        righe = np.nonzero(pieno.any(axis=0))[0]
        if len(cols) and len(righe):
            # dentro anche gli angoli tondi: si entra di un paio di pixel
            m = max(2, int(min(img.get_size()) * 0.012))
            r = pygame.Rect(cols[0] + m, righe[0] + m,
                            cols[-1] - cols[0] - 2 * m,
                            righe[-1] - righe[0] - 2 * m)
            return img.subsurface(r).copy()
    except Exception:
        pass
    return img


def immagine_mazzo(che, cartella=None):
    """dorso o scatola del mazzo scelto (o di quello dato: nel ramino si
    gioca con due mazzi, rosso e blu). Il dorso senza bordo vuoto."""
    cartella = cartella or MAZZO_ORA[0]
    if cartella is None:
        return None
    f = os.path.join(cartella_carte(), "mazzi", cartella, che + ".png")
    if not os.path.exists(f):
        return None
    if che != "dorso":
        return _immagine(f)
    chiave = f + "#pieno"
    if chiave not in IMG_CARTE:
        IMG_CARTE[chiave] = _solo_pieno(_immagine(f))
    return IMG_CARTE[chiave]


def misura_carta():
    """Alta sempre uguale; larga come le carte del mazzo scelto (le
    napoletane sono piu' strette delle francesi)."""
    h = B.s(CARTA_H)
    prima = "AS" if famiglia() == "francesi" else "1d"
    img = immagine_carta(prima) or immagine_mazzo("dorso")
    if img is not None:
        return max(1, int(h * img.get_width() / float(img.get_height()))), h
    return B.s(CARTA_W), h


def _riduci(img, w, h):
    """Rimpicciolisce bene: Lanczos e un filo di nitidezza (con PIL se
    c'e'), altrimenti a meta' per volta con smoothscale."""
    try:
        from PIL import Image
        src = img.convert_alpha()
        p = Image.frombytes("RGBA", src.get_size(),
                            pygame.image.tostring(src, "RGBA"))
        p = p.resize((w, h), Image.LANCZOS)
        return pygame.image.fromstring(p.tobytes(), (w, h),
                                       "RGBA").convert_alpha()
    except Exception:
        while img.get_width() > 2 * w and img.get_height() > 2 * h:
            img = pygame.transform.smoothscale(
                img, (img.get_width() // 2, img.get_height() // 2))
        return pygame.transform.smoothscale(img, (w, h))


def _dentro(img, w, h, fondo=(255, 255, 255)):
    """Ci sta tutta: l'immagine si rimpicciolisce finche' entra in w x h
    senza tagliare niente, e quello che avanza resta bianco come il bordo
    della carta. Serve ai dorsi, che non hanno sempre la stessa forma
    delle facce."""
    iw, ih = img.get_size()
    k = min(w / float(iw), h / float(ih))
    q = _riduci(img, max(1, int(round(iw * k))), max(1, int(round(ih * k))))
    sup = pygame.Surface((w, h), pygame.SRCALPHA)
    sup.fill(fondo)
    sup.blit(q, q.get_rect(center=(w // 2, h // 2)))
    return sup


def _copri(img, w, h):
    """Porta l'immagine a w x h senza stirarla: si ingrandisce in modo
    uguale nei due sensi e si taglia quello che avanza, in mezzo."""
    iw, ih = img.get_size()
    k = max(w / float(iw), h / float(ih))
    cw, ch = min(iw, int(round(w / k))), min(ih, int(round(h / k)))
    r = pygame.Rect((iw - cw) // 2, (ih - ch) // 2, cw, ch)
    return _riduci(img.subsurface(r).copy(), w, h)


def _arrotonda(img, r):
    """Gli angoli tondi di una carta vera."""
    # la maschera si disegna 4 volte piu' grande e si rimpicciolisce:
    # cosi' gli angoli vengono morbidi e non a scalini
    w, h = img.get_size()
    g = pygame.Surface((w * 4, h * 4), pygame.SRCALPHA)
    pygame.draw.rect(g, (255, 255, 255, 255), g.get_rect(),
                     border_radius=r * 4)
    m = pygame.transform.smoothscale(g, (w, h))
    out = img.copy().convert_alpha()
    out.blit(m, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
    return out


def faccia_carta(scoperta, codice=None, k=1.0, dorso=None):
    """La superficie della carta, dritta, con la sua ombra. k: quanto
    e' ingrandito lo schermo, la carta nasce gia' a quella misura."""
    k = round(k, 3)
    chiave = (scoperta, codice if scoperta else dorso, k)
    if chiave in FACCIA:
        return FACCIA[chiave]
    w, h = misura_carta()
    w, h = max(1, int(w * k)), max(1, int(h * k))
    q = lambda v: max(1, int(round(B.s(v) * k)))
    r = max(3, q(6))
    sup = pygame.Surface((w + q(6), h + q(6)), pygame.SRCALPHA)
    # l'ombra, spostata in basso a destra
    pygame.draw.rect(sup, (0, 0, 0, 28), pygame.Rect(q(2), q(3), w, h),
                     border_radius=r)
    corpo = pygame.Rect(0, 0, w, h)
    img = immagine_carta(codice) if scoperta else \
        immagine_mazzo("dorso", dorso)
    if img is not None:
        # le facce danno la forma alla carta, quindi ci stanno esatte; i
        # dorsi possono avere proporzioni diverse e non si tagliano mai
        img = _arrotonda(_copri(img, w, h) if scoperta
                         else _dentro(img, w, h), r)
        sup.blit(img, (0, 0))
    elif scoperta:
        pygame.draw.rect(sup, (250, 250, 246), corpo, border_radius=r)
        pygame.draw.rect(sup, (170, 170, 176), corpo, 1, border_radius=r)
    else:
        pygame.draw.rect(sup, (214, 216, 222), corpo, border_radius=r)
        dentro = corpo.inflate(-q(14), -q(14))
        pygame.draw.rect(sup, (186, 190, 200), dentro, q(2),
                         border_radius=max(2, r - q(4)))
        pygame.draw.rect(sup, (150, 152, 160), corpo, 1, border_radius=r)
    FACCIA[chiave] = sup
    return sup


def scatola_doppia(cartelle):
    """La confezione doppia, quella rettangolare da due mazzi: si cerca
    scatola_doppia.png nelle cartelle dei due mazzi. Se non c'e' si
    disegnano le due scatole singole nello stesso spazio."""
    for cartella in cartelle:
        img = immagine_mazzo("scatola_doppia", cartella)
        if img is not None:
            return img
    return None


def disegna_scatola(sc, centro, alto, z=1.0, cartelle=None):
    """La scatola accanto al mazzo. Con due mazzi (ramino): la confezione
    doppia se c'e', se no le due scatoline affiancate nello stesso posto.
    z: l'ingrandimento dello schermo."""
    if alto <= 0:
        return
    alto = max(1, int(alto * z))
    cartelle = [x for x in (cartelle or []) if x]
    doppia = scatola_doppia(cartelle) if len(cartelle) > 1 else None
    if doppia is not None or len(cartelle) < 2:
        imgs = [doppia if doppia is not None
                else immagine_mazzo("scatola", cartelle[0] if cartelle
                                    else None)]
        nomi = [cartelle[0] if cartelle else MAZZO_ORA[0]]
        if doppia is not None:
            nomi = ["doppia+" + "+".join(cartelle)]
    else:
        imgs = [immagine_mazzo("scatola", x) for x in cartelle]
        nomi = list(cartelle)
        alto = max(1, int(alto * 0.72))     # due scatole nello stesso spazio
    imgs = [(n, i) for n, i in zip(nomi, imgs) if i is not None]
    if not imgs:
        return
    pezzi = []
    for nome, img in imgs:
        k = alto / float(img.get_height())
        chiave = ("scatola", nome, alto)
        if chiave not in FACCIA:
            FACCIA[chiave] = _riduci(img, max(1, int(img.get_width() * k)),
                                     alto)
        pezzi.append(FACCIA[chiave])
    gap = max(2, int(B.s(4) * z))
    largo = sum(p.get_width() for p in pezzi) + gap * (len(pezzi) - 1)
    c = (int(centro[0] * z), int(centro[1] * z))
    x = c[0] - largo // 2
    for q in pezzi:
        r = q.get_rect(midleft=(x, c[1]))
        om = pygame.Surface(q.get_size(), pygame.SRCALPHA)
        om.fill((0, 0, 0, 40))
        sc.blit(om, r.move(int(B.s(2) * z), int(B.s(3) * z)))
        sc.blit(q, r)
        x += q.get_width() + gap


def morbido(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


ALONI = {}


def alone(w, h, m, col, r):
    """Un alone di luce attorno a un rettangolo w x h: pieno sul bordo
    della carta, sempre piu' trasparente man mano che si allontana."""
    chiave = (w, h, m, col, r)
    if chiave not in ALONI:
        s = pygame.Surface((w + 2 * m, h + 2 * m), pygame.SRCALPHA)
        for i in range(m, 0, -1):
            a = int(150 * (1.0 - i / float(m + 1)) ** 2) + 6
            q = pygame.Surface(s.get_size(), pygame.SRCALPHA)
            pygame.draw.rect(q, col + (a,), pygame.Rect(m - i, m - i,
                                                        w + 2 * i, h + 2 * i),
                             border_radius=r + i)
            s.blit(q, (0, 0))
        ALONI[chiave] = s
    return ALONI[chiave]


class Carta:
    """Una carta sul tavolo: dove sta, dove va, com'e' girata."""

    def __init__(self, pos, angolo=0.0, scoperta=False, codice=None):
        self.codice = codice
        self.pos = pygame.Vector2(pos)
        self.da = pygame.Vector2(pos)
        self.a = pygame.Vector2(pos)
        self.ang, self.ang_da, self.ang_a = angolo, angolo, angolo
        self.scoperta = scoperta
        self.gira_a = scoperta          # come deve finire
        self.t = 1.0                    # 1 = arrivata
        self.ritardo = 0.0
        self.su = 0.0                   # quanto si alza sotto il mouse
        self.suono = None               # da suonare quando parte
        # quanto e' grande rispetto al mazzo: in volo cresce o cala piano
        self.g = self.g_da = self.g_a = 1.0
        self.dorso = None               # il mazzo del dorso, se non e' quello scelto

    def vai(self, dove, angolo=None, scoperta=None, ritardo=0.0,
            suono=None, grande=None):
        self.da = pygame.Vector2(self.pos)
        self.a = pygame.Vector2(dove)
        self.ang_da = self.ang
        self.ang_a = self.ang if angolo is None else angolo
        if scoperta is not None:
            self.gira_a = scoperta
        self.t = 0.0
        self.ritardo = ritardo
        self.suono = suono
        self.g_da = self.g
        self.g_a = self.g if grande is None else grande

    def passo(self, dt):
        if self.ritardo > 0:
            self.ritardo -= dt
            return
        if self.suono:
            suona(self.suono)
            self.suono = None
        if self.t < 1.0:
            self.t = min(1.0, self.t + dt / TEMPO_VOLO)
            k = morbido(self.t)
            self.pos = self.da.lerp(self.a, k)
            self.ang = self.ang_da + (self.ang_a - self.ang_da) * k
            self.g = self.g_da + (self.g_a - self.g_da) * k

    def disegna(self, sc, z=1.0, bordo=None):
        # la girata: a meta' volo si stringe fino a sparire e rinasce
        # dall'altra parte, come una carta che ruota
        k = 1.0
        scoperta = self.scoperta
        if self.gira_a != self.scoperta:
            if self.t >= 1.0 and self.ritardo <= 0:
                self.scoperta = self.gira_a
                scoperta = self.scoperta
            else:
                k = abs(math.cos(math.pi * max(0.0, self.t)))
                scoperta = self.gira_a if self.t > 0.5 else self.scoperta
        # la misura va a scatti piccoli: in volo non si rifa' la carta
        # a ogni fotogramma
        g = self.g_a if self.t >= 1.0 else round(self.g * 20) / 20.0
        img = faccia_carta(scoperta, self.codice, z * g, self.dorso)
        if bordo is not None:
            # la carta scelta: un alone di luce dorata tutto intorno, che
            # sfuma verso fuori
            w, h = misura_carta()
            w, h = max(1, int(w * z * g)), max(1, int(h * z * g))
            al = alone(w, h, max(4, int(B.s(12) * z)), bordo,
                       max(3, int(B.s(6) * z * g)))
            m = (al.get_width() - w) // 2
            tutto = pygame.Surface((max(al.get_width(), img.get_width() + m),
                                    max(al.get_height(),
                                        img.get_height() + m)),
                                   pygame.SRCALPHA)
            tutto.blit(al, (0, 0))
            tutto.blit(img, (m, m))
            img = tutto
        if k < 0.999:
            img = pygame.transform.smoothscale(
                img, (max(1, int(img.get_width() * k)), img.get_height()))
        if abs(self.ang) > 0.1:
            img = pygame.transform.rotozoom(img, self.ang, 1.0)
        sc.blit(img, img.get_rect(center=(int(self.pos.x * z),
                                          int((self.pos.y - self.su) * z))))


def zona_panno():
    """Il panno sullo schermo."""
    k = B.SCALA
    x, y = B.TAV_POS
    return pygame.Rect(int(x + PANNO_CARTE.x * k), int(y + PANNO_CARTE.y * k),
                       int(PANNO_CARTE.w * k), int(PANNO_CARTE.h * k))


def posti(n_mano, g=1.0):
    """Dove vanno le carte di ognuno: tu in basso a ventaglio, uno sopra,
    uno a sinistra e uno a destra, girati verso il centro."""
    z = zona_panno()
    passo = B.s(CARTA_W) * 0.62 * g
    ch = B.s(CARTA_H) * g
    out = {0: [], 1: [], 2: [], 3: []}
    for i in range(n_mano):
        off = (i - (n_mano - 1) / 2.0)
        out[0].append(((z.centerx + off * passo * 1.25,
                        z.bottom - ch * 0.62 + abs(off) * B.s(3)),
                       -off * 3.0))
        out[1].append(((z.centerx + off * passo * 0.7,
                        z.top + ch * 0.55), 180.0))
        out[2].append(((z.left + ch * 0.6,
                        z.centery + off * passo * 0.7), -90.0))
        out[3].append(((z.right - ch * 0.6,
                        z.centery + off * passo * 0.7), 90.0))
    return out


# I quattro posti hanno ognuno il suo seme, coi colori tedeschi: quadri
# arancione, fiori blu, cuori rosso, picche verde. Il segno sul legno e
# quello nella targhetta sono lo stesso, cosi' si capisce chi e' chi.
SEMI_POSTI = ("quadri", "fiori", "cuori", "picche")
COL_POSTI = ((255, 136, 0), (20, 70, 210), (221, 26, 30), (0, 136, 0))
SEMI_IMG = {}


def simbolo_posto(chi, alto):
    """Il simbolo del seme di quel posto, alto cosi'."""
    alto = max(4, int(alto))
    chiave = (chi, alto)
    if chiave not in SEMI_IMG:
        f = os.path.join(cartella_carte(), "semi",
                         SEMI_POSTI[chi % 4] + ".png")
        img = _immagine(f)
        if img is None:
            SEMI_IMG[chiave] = None
        else:
            largo = max(4, int(alto * img.get_width() / img.get_height()))
            SEMI_IMG[chiave] = pygame.transform.smoothscale(img,
                                                            (largo, alto))
    return SEMI_IMG[chiave]


def rombo(sc, centro, col, rx, ry, chi=None):
    """Il segno di un posto: il simbolo del seme se c'e', se no il
    vecchio diamantino piatto."""
    x, y = centro
    if chi is not None:
        # il simbolo non si schiaccia: sempre alto quanto il lato lungo
        q = simbolo_posto(chi, max(rx, ry) * 2.1)
        if q is not None:
            sc.blit(q, q.get_rect(center=(int(x), int(y))))
            return
    pygame.draw.polygon(sc, col, [(x, y - ry), (x + rx, y), (x, y + ry),
                                  (x - rx, y)])


def targhetta(sc, nome, punti, centro, col, attivo=False):
    """Pallino, nome e punteggio di un giocatore, in una targhetta scura.
    Ritorna quanto e' larga, per metterle in fila."""
    f = B.FONTS["small"]
    tn = f.render(nome, True, (240, 240, 244))
    tp = f.render(str(punti), True, B.ORO_SCELTA)
    pad, gap, rp = B.s(12), B.s(14), B.s(7)
    w = pad + rp * 2 + B.s(10) + tn.get_width() + gap + tp.get_width() + pad
    h = max(tn.get_height(), tp.get_height()) + B.s(8)
    r = pygame.Rect(0, 0, w, h)
    r.center = (int(centro[0]), int(centro[1]))
    q = pygame.Surface(r.size, pygame.SRCALPHA)
    pygame.draw.rect(q, (0, 0, 0, 150), q.get_rect(),
                     border_radius=h // 2)
    sc.blit(q, r)
    if attivo:
        pygame.draw.rect(sc, B.ORO_SCELTA, r, max(1, B.s(2)),
                         border_radius=h // 2)
    rombo(sc, (r.x + pad + rp, r.centery), col, rp * 0.7, rp)
    x = r.x + pad + rp * 2 + B.s(10)
    sc.blit(tn, tn.get_rect(midleft=(x, r.centery)))
    sc.blit(tp, tp.get_rect(midright=(r.right - pad, r.centery)))
    return w


def larga_targhetta(nome, punti):
    f = B.FONTS["small"]
    return (B.s(12) * 2 + B.s(14) * 2 + B.s(10) + f.size(nome)[0] +
            B.s(14) + f.size(str(punti))[0])


def diamanti_posti(base):
    """Un diamantino colorato a meta' di ogni lato, intarsiato nel legno
    come i segni del biliardo: di chi e' quel posto. Si disegna sulla PNG
    a misura piena, prima di ridurre."""
    p, e = PANNO_CARTE, LEGNO_FUORI
    a, b = B.DIAMANTE_LARGO * 0.8, B.DIAMANTE_LUNGO * 0.8
    dove = {0: (p.centerx, (p.bottom + e.bottom) / 2.0, True),
            1: (p.centerx, (e.top + p.top) / 2.0, True),
            2: ((e.left + p.left) / 2.0, p.centery, False),
            3: ((p.right + e.right) / 2.0, p.centery, False)}
    for chi, (x, y, in_piedi) in dove.items():
        rx, ry = (a, b) if in_piedi else (b, a)
        rombo(base, (x, y), COL_POSTI[chi], rx, ry, chi)


def cella_giocatore(sc, r, nome, punti, col, sinistra, attivo, chi=None):
    """Meta' fascia per un giocatore: diamantino e nome dalla parte del
    bordo, poi un filo d'oro corto e subito il riquadro verde col
    punteggio. Il centro della fascia resta libero. A destra a specchio."""
    carattere = B.FONTS.get("nomi_hud") or B.FONTS["font"]
    font = B.FONTS["font"]
    alto = r.h - B.s(8)
    y = r.centery
    xd = r.left + B.s(26) if sinistra else r.right - B.s(26)
    rombo(sc, (xd, y), col, B.s(6), B.s(10), chi)
    if attivo:
        m, d = B.s(7), B.s(18)
        xf = xd - d if sinistra else xd + d
        verso = 1 if sinistra else -1
        pygame.draw.polygon(sc, B.ORO_LUCE, [(xf, y - m),
                                             (xf + verso * B.s(9), y),
                                             (xf, y + m)])
    t = carattere.render(nome, True, B.AVORIO)
    box = pygame.Rect(0, 0, B.s(64), alto)
    if sinistra:
        q = t.get_rect(midleft=(xd + B.s(18), y - B.s(2)))
        box.midleft = (q.right + B.s(14), y)
        da, a = xd - B.s(6), box.right + B.s(8)
    else:
        q = t.get_rect(midright=(xd - B.s(18), y - B.s(2)))
        box.midright = (q.left - B.s(14), y)
        da, a = xd + B.s(6), box.left - B.s(8)
    sc.blit(t, q)
    # sotto il nome, dal diamantino al punteggio, un filo d'oro che lo
    # sottolinea, con la perlina ai due capi come nel logo
    yl = max(q.bottom, box.bottom) + B.s(7)
    pygame.draw.line(sc, B.ORO_LOGO, (da, yl), (a, yl), max(1, B.s(1)))
    pygame.draw.circle(sc, B.ORO_LOGO, (da, yl), max(2, B.s(2)))
    pygame.draw.circle(sc, B.ORO_LUCE, (a, yl), max(2, B.s(2)))
    pygame.draw.rect(sc, B.VERDONE, box)
    t = font.render(str(punti), True, (255, 255, 255))
    sc.blit(t, t.get_rect(center=box.center))


def fila_targhette(sc, nomi, punti, attivo=0):
    """La fascia del punteggio divisa fra sopra e sotto il tavolo, ognuno
    dalla parte del suo diamantino: sotto tu (oro) a sinistra e il verde
    a destra, sopra il rosso a sinistra e il blu a destra."""
    # sopra: a meta' fra il bordo della finestra e il legno. Sotto: alla
    # stessa distanza dal legno, cosi' sono uguali tutte e due
    sotto = B.BANDA_PUNTI.copy()
    sopra = sotto.copy()        # stessa larghezza e stesso inizio di sotto
    legno_su = B.TAV_POS[1] + LEGNO_FUORI.top * B.SCALA
    legno_giu = B.TAV_POS[1] + LEGNO_FUORI.bottom * B.SCALA
    sopra.centery = int(legno_su / 2)
    sotto.centery = int(legno_giu + (legno_su - sopra.centery))
    meta = sotto.w // 2
    posto = {0: (sotto, True), 3: (sotto, False),
             2: (sopra, True), 1: (sopra, False)}
    # il nome del gioco in mezzo alla fascia di sopra
    B.scritta_logo(sc, sopra.centerx, sopra.centery - B.s(2), 0.55)
    for chi in range(len(nomi)):
        fascia, sinistra = posto[chi]
        r = pygame.Rect(fascia.x + (0 if sinistra else meta), fascia.y,
                        meta, fascia.h)
        cella_giocatore(sc, r, nomi[chi], punti[chi], COL_POSTI[chi],
                        sinistra, chi == attivo, chi)


def prova_carte(sc, clock, logo):
    """La prova delle carte: D distribuisce, clic su una tua carta la
    gioca al centro, R raccoglie tutto nel mazzo e lo rimescola. ESC
    torna al menu."""
    ip, ib = scelta_tavolo()
    z = zona_panno()
    # il mazzo fuori dal tavolo, a sinistra: dove nel biliardo ci sono
    # potenza e precisione
    legno_sx = int(B.TAV_POS[0] + LEGNO_FUORI.left * B.SCALA)
    x_lato = max(B.s(30), legno_sx // 2)
    scegli_mazzo(0)
    P = {}

    def disponi():
        """Dove stanno mazzo e scatola: si rifà quando si cambia mazzo."""
        # il mazzo nella fascia a sinistra del tavolo, la scatola in
        # quella a destra, sempre con le sue proporzioni
        sb = immagine_mazzo("scatola")
        legno_dx = int(B.TAV_POS[0] + LEGNO_FUORI.right * B.SCALA)
        alto_sc = 0
        if sb is not None:
            largo = B.WIN_W - legno_dx - B.s(20)
            alto_sc = max(B.s(30), min(B.s(150), int(
                largo * sb.get_height() / float(sb.get_width()))))
        P["scatola"] = ((legno_dx + B.WIN_W) // 2, z.centery)
        P["mazzo"] = (x_lato, z.centery + B.s(7))
        P["alto"] = alto_sc
    disponi()

    def posto_mazzo(k):
        return (P["mazzo"][0] + k * 0.2, P["mazzo"][1] - k * 0.35)
    carte = []
    mani = {0: [], 1: [], 2: [], 3: []}
    centro = []

    def nuovo_mazzo():
        del carte[:]
        codici = mazzo_codici()
        random.shuffle(codici)
        for k, cod in enumerate(codici):
            c = Carta(posto_mazzo(k), codice=cod)
            carte.append(c)
        for m in mani.values():
            del m[:]
        del centro[:]

    def distribuisci(n=5):
        pos = posti(n)
        rit = 0.0
        for i in range(n):
            for chi in (0, 1, 2, 3):
                if not carte:
                    return
                c = carte.pop()
                mani[chi].append(c)
                dove, ang = pos[chi][i]
                c.vai(dove, ang, scoperta=(chi == 0), ritardo=rit,
                      suono="servi")
                rit += 0.07

    def rimetti_mano():
        """Dopo una giocata la mano si richiude al centro."""
        pos = posti(len(mani[0]))
        for i, c in enumerate(mani[0]):
            c.vai(pos[0][i][0], pos[0][i][1])

    def gioca(c):
        mani[0].remove(c)
        centro.append(c)
        n = len(centro)
        c.su = 0.0
        c.vai((z.centerx + (n - 1) * B.s(18) - B.s(20),
               z.centery + random.uniform(-4, 4)),
              random.uniform(-8, 8), scoperta=True, suono="giocata")
        rimetti_mano()

    def raccogli():
        rit = 0.0
        tutte = centro + mani[0] + mani[1] + mani[2] + mani[3]
        if tutte:
            suona("cattura")
        for c in tutte:
            carte.insert(0, c)
        for m in mani.values():
            del m[:]
        del centro[:]
        random.shuffle(carte)
        # ognuna torna al suo posto nella pila, dritta e giu' dal sollevo
        for k, c in enumerate(carte):
            c.su = 0.0
            if c in tutte:
                c.vai(posto_mazzo(k), 0.0, scoperta=False, ritardo=rit)
                rit += 0.02
            else:
                c.vai(posto_mazzo(k), 0.0, scoperta=False)

    def sopra_scena(sup, z):
        """Scatola e carte si disegnano dopo l'ingrandimento, alla misura
        vera dello schermo: cosi' restano nitide."""
        disegna_scatola(sup, P["scatola"], P["alto"], z)
        # prima quelle ferme nel mazzo, poi il centro, poi le mani
        for c in carte:
            c.disegna(sup, z)
        for c in centro:
            c.disegna(sup, z)
        for chi in (1, 2, 3, 0):
            for c in mani[chi]:
                c.disegna(sup, z)

    scelta = [0]

    def cambia_mazzo():
        """T: il mazzo dopo, per provarli tutti. Torna il nome."""
        m = mazzi_disponibili()
        if not m:
            return None
        scelta[0] = (scelta[0] + 1) % len(m)
        scegli_mazzo(scelta[0])
        disponi()
        for k, c in enumerate(carte):
            c.vai(posto_mazzo(k), 0.0)
        return m[scelta[0]][0]

    B.SOPRA_SCENA[0] = sopra_scena
    try:
        return _giro_carte(sc, clock, carte, mani, centro, nuovo_mazzo,
                           distribuisci, gioca, raccogli, ip, ib,
                           cambia_mazzo)
    finally:
        B.SOPRA_SCENA[0] = None


def _giro_carte(sc, clock, carte, mani, centro, nuovo_mazzo, distribuisci,
                gioca, raccogli, ip, ib, cambia_mazzo):
    nomi = [B.NOMI[0] or "Player 1"] + random.sample(B.AVVERSARI, 3)
    cartello = ["", 0.0]    # il nome del mazzo, per un paio di secondi
    punti = [0, 0, 0, 0]
    carica_suoni()
    musica_carte()
    nuovo_mazzo()
    while True:
        dt = clock.tick(60) / 1000.0
        mouse = B.mouse_gioco()
        sopra = None
        for c in reversed(mani[0]):
            w, h = misura_carta()
            if pygame.Rect(c.pos.x - w / 2, c.pos.y - h / 2 - c.su, w,
                           h).collidepoint(mouse) and c.t >= 1.0:
                sopra = c
                break
        for ev in B.eventi():
            if ev.type == pygame.QUIT:
                return "quit"
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    fine_musica_carte()
                    return "menu"
                if ev.key == pygame.K_d and not any(mani.values()):
                    distribuisci()
                if ev.key == pygame.K_r:
                    raccogli()
                if ev.key == pygame.K_t:
                    nome = cambia_mazzo()
                    if nome:
                        cartello[:] = [nome.replace("_", " ").title(), 2.0]
            if ev.type == pygame.MOUSEBUTTONDOWN:
                if ev.button == 3:
                    fine_musica_carte()
                    return "menu"
                if ev.button == 1 and sopra is not None:
                    gioca(sopra)
        for c in mani[0]:
            voglio = B.s(18) if c is sopra else 0.0
            c.su += (voglio - c.su) * min(1.0, dt * 14)
        for c in carte + centro + sum(mani.values(), []):
            c.passo(dt)

        sc.blit(B.fondo(), (0, 0))
        tav = tavolo_carte(ip, ib)
        if tav is not None:
            sc.blit(tav, B.TAV_POS)
        fila_targhette(sc, nomi, punti)
        aiuto = FONT_AIUTO()
        if aiuto is not None:
            t = aiuto.render("D  deal     click  play a card     R  collect"
                             "     T  deck     ESC  back", True, (190, 196, 208))
            sc.blit(t, t.get_rect(center=(B.WIN_W // 2,
                                          B.WIN_H - B.s(40))))
        if cartello[1] > 0 and aiuto is not None:
            cartello[1] -= dt
            t = aiuto.render(cartello[0], True, B.ORO_LUCE)
            z = zona_panno()
            sc.blit(t, t.get_rect(center=(z.centerx, z.top + B.s(24))))
        B.presenta()


def FONT_AIUTO():
    return B.FONTS.get("small")


def schermata_carte(sc, clock, logo):
    """Dal menu del casino': il menu dei giochi di carte."""
    import carte_giochi
    return carte_giochi.menu_carte(sc, clock, logo)
