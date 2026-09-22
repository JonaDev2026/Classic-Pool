"""I giochi di carte di Golden Break: il menu delle carte, il tavolo
comune (mazzo, carte che volano, pulsanti, messaggi) e i giochi.

Ogni gioco e' un generatore: scrive la partita dritta, in ordine
("distribuisci, aspetta, fai scegliere una carta..."), e a ogni yield il
tavolo disegna un fotogramma. Cosi' la logica resta leggibile e le
animazioni vanno da sole."""
import itertools
import random

import pygame

import carte as C

B = C.B

# --------------------------------------------------------------- testi
TXT = {
    "en": {"cards": "Cards", "blackjack": "Blackjack",
           "sette": "Sette e Mezzo", "scopa": "Scopa",
           "briscola": "Briscola", "ramino": "Rummy", "deck": "Deck",
           "back": "Back", "soon": "soon",
           "need_fr": "French cards needed: coming soon",
           "card": "Card", "stand": "Stand", "leave": "Leave",
           "again": "Play again", "menu": "Menu", "next": "Next hand",
           "bet": "Place your bet", "free": "Free play",
           "bust": "Bust!", "you_win": "You win %s",
           "you_lose": "You lose %s", "banker": "Banker",
           "reale": "Sette e mezzo reale!", "banker_bust": "Banker busts",
           "your_turn": "Your turn", "trump": "Trump: %s",
           "left": "Cards left: %d", "scopa_msg": "Scopa!",
           "hand_over": "Hand over", "win_match": "%s wins the match",
           "draw": "Draw", "points": "%s  %d - %d  %s",
           "p_cards": "Cards", "p_coins": "Coins", "p_sette": "Settebello",
           "p_prim": "Primiera", "p_scope": "Scope",
           "d": "Coins", "c": "Cups", "s": "Swords", "b": "Clubs",
           "tie_banker": "Tie: banker wins",
           "hit": "Hit", "bj_stand": "Stand", "double": "Double", "bj": "Blackjack!", "push": "Push", "dealer": "Dealer",
           "play": "Play",
           "rules": "Rules", "settings": "Settings",
           "bet_is": "Bet %s",
           "help_game": "click / ENTER  play      ESC  back"},
    "it": {"cards": "Carte", "blackjack": "Blackjack",
           "sette": "Sette e Mezzo", "scopa": "Scopa",
           "briscola": "Briscola", "ramino": "Ramino", "deck": "Mazzo",
           "back": "Indietro", "soon": "presto",
           "need_fr": "Servono le carte francesi: presto",
           "card": "Carta", "stand": "Sto", "leave": "Esci",
           "again": "Rigioca", "menu": "Menu", "next": "Prossima mano",
           "bet": "Fai la tua puntata", "free": "Gioco libero",
           "bust": "Sballato!", "you_win": "Vinci %s",
           "you_lose": "Perdi %s", "banker": "Banco",
           "reale": "Sette e mezzo reale!", "banker_bust": "Il banco sballa",
           "your_turn": "Tocca a te", "trump": "Briscola: %s",
           "left": "Carte rimaste: %d", "scopa_msg": "Scopa!",
           "hand_over": "Fine mano", "win_match": "%s vince la partita",
           "draw": "Pareggio", "points": "%s  %d - %d  %s",
           "p_cards": "Carte", "p_coins": "Denari", "p_sette": "Settebello",
           "p_prim": "Primiera", "p_scope": "Scope",
           "d": "Denari", "c": "Coppe", "s": "Spade", "b": "Bastoni",
           "tie_banker": "Pari: vince il banco",
           "hit": "Carta", "bj_stand": "Sto", "double": "Raddoppia", "bj": "Blackjack!", "push": "Pareggio", "dealer": "Banco",
           "play": "Gioca",
           "rules": "Regole", "settings": "Impostazioni",
           "bet_is": "Puntata %s",
           "help_game": "clic / INVIO  gioca      ESC  indietro"},
    "fr": {"cards": "Cartes", "blackjack": "Blackjack",
           "sette": "Sette e Mezzo", "scopa": "Scopa",
           "briscola": "Briscola", "ramino": "Rami", "deck": "Jeu",
           "back": "Retour", "soon": "bientot",
           "need_fr": "Cartes francaises requises : bientot",
           "card": "Carte", "stand": "Reste", "leave": "Quitter",
           "again": "Rejouer", "menu": "Menu", "next": "Main suivante",
           "bet": "Placez votre mise", "free": "Jeu libre",
           "bust": "Perdu !", "you_win": "Vous gagnez %s",
           "you_lose": "Vous perdez %s", "banker": "Banque",
           "reale": "Sette e mezzo royal !", "banker_bust": "La banque saute",
           "your_turn": "A vous", "trump": "Atout : %s",
           "left": "Cartes restantes : %d", "scopa_msg": "Scopa !",
           "hand_over": "Fin de la main", "win_match": "%s gagne la partie",
           "draw": "Egalite", "points": "%s  %d - %d  %s",
           "p_cards": "Cartes", "p_coins": "Deniers", "p_sette": "Settebello",
           "p_prim": "Primiera", "p_scope": "Scope",
           "d": "Deniers", "c": "Coupes", "s": "Epees", "b": "Batons",
           "tie_banker": "Egalite : la banque gagne",
           "hit": "Carte", "bj_stand": "Reste", "double": "Doubler", "bj": "Blackjack !", "push": "Egalite", "dealer": "Croupier",
           "play": "Jouer",
           "rules": "Regles", "settings": "Reglages",
           "bet_is": "Mise %s",
           "help_game": "clic / ENTREE  jouer      ECHAP  retour"},
    "es": {"cards": "Cartas", "blackjack": "Blackjack",
           "sette": "Sette e Mezzo", "scopa": "Escoba",
           "briscola": "Brisca", "ramino": "Rummy", "deck": "Baraja",
           "back": "Atras", "soon": "pronto",
           "need_fr": "Faltan las cartas francesas: pronto",
           "card": "Carta", "stand": "Me planto", "leave": "Salir",
           "again": "Otra vez", "menu": "Menu", "next": "Otra mano",
           "bet": "Haz tu apuesta", "free": "Juego libre",
           "bust": "Te pasaste!", "you_win": "Ganas %s",
           "you_lose": "Pierdes %s", "banker": "Banca",
           "reale": "Sette e mezzo real!", "banker_bust": "La banca se pasa",
           "your_turn": "Tu turno", "trump": "Triunfo: %s",
           "left": "Quedan: %d", "scopa_msg": "Escoba!",
           "hand_over": "Fin de la mano", "win_match": "%s gana la partida",
           "draw": "Empate", "points": "%s  %d - %d  %s",
           "p_cards": "Cartas", "p_coins": "Oros", "p_sette": "Settebello",
           "p_prim": "Primiera", "p_scope": "Escobas",
           "d": "Oros", "c": "Copas", "s": "Espadas", "b": "Bastos",
           "tie_banker": "Empate: gana la banca",
           "hit": "Pedir", "bj_stand": "Plantarse", "double": "Doblar", "bj": "Blackjack!", "push": "Empate", "dealer": "Crupier",
           "play": "Jugar",
           "rules": "Reglas", "settings": "Ajustes",
           "bet_is": "Apuesta %s",
           "help_game": "clic / INTRO  jugar      ESC  atras"},
}


# la riga dei comandi col joystick: le scritte vanno anche nei testi del
# biliardo, perche' e' lui che disegna la riga con le icone
RIGA_PAD_CARTE = ((("croce",), "cg_move"), (("a",), "cg_play"),
                  (("b",), "pa_back"))
for _l, _m, _p in (("en", "choose", "play"), ("it", "scegli", "gioca"),
                   ("fr", "choisir", "jouer"), ("es", "elegir", "jugar")):
    B.TESTI.setdefault(_l, {}).update({"cg_move": _m, "cg_play": _p})


_FONT_CARTE = {}


def font_carte(misura):
    """Il carattere elegante a una misura piu' piccola di quelle del
    biliardo, per messaggi e scelte al tavolo."""
    if misura not in _FONT_CARTE:
        _FONT_CARTE[misura] = B.carattere_elegante(B.s(misura)) or \
            B.FONTS["small"]
    return _FONT_CARTE[misura]


def T(k):
    d = TXT.get(B.CFG.get("lingua", "en"), TXT["en"])
    return d.get(k, TXT["en"].get(k, k))


def num(cod):
    return int(cod[:-1])


def seme(cod):
    return cod[-1]


class Esci(Exception):
    pass


# --------------------------------------------------------------- tavolo
class Tavolo:
    """Il tavolo comune a tutti i giochi."""

    def __init__(self, sc, clock, nomi, gioco=""):
        self.sc, self.clock = sc, clock
        self.gioco = gioco      # la chiave del gioco, per il nome in alto
        self.nomi = nomi
        self.punti = [0] * len(nomi)
        self.attivo = 0
        self.ip, self.ib = C.scelta_tavolo()
        self.z = C.zona_panno()
        self.carte = []         # tutte, nell'ordine in cui si disegnano
        self.mazzo = []         # la pila coperta, in cima l'ultima
        self.msg = ["", 0.0]
        self.righe = []         # una o due righe di testo in mezzo
        self.tabella = None     # il riepilogo di fine mano, in colonne
        self.bottoni = []       # le scritte dei pulsanti
        self.rett_bottoni = []
        self.sel_bottone = 0
        self.scegli = []        # le carte che si possono giocare
        self.sel_carta = 0
        self.eventi = []
        self.dt = 0.0
        self.P = {}
        legno_sx = int(B.TAV_POS[0] + C.LEGNO_FUORI.left * B.SCALA)
        self.x_lato = max(B.s(30), legno_sx // 2)
        self.disponi()

    # ---- posti
    def disponi(self):
        """A sinistra del tavolo il mazzo, sotto il numero delle carte e
        sotto ancora la scatola. La fascia a destra e' per le scelte."""
        sb = C.immagine_mazzo("scatola")
        legno_sx = int(B.TAV_POS[0] + C.LEGNO_FUORI.left * B.SCALA)
        _, h = C.misura_carta()
        alto = 0
        if sb is not None:
            largo = legno_sx - B.s(20)
            alto = max(B.s(30), min(B.s(110), int(
                largo * sb.get_height() / float(sb.get_width()))))
        conta = B.FONTS["small"].get_height() + B.s(16)
        tutto = h + conta + alto
        y0 = self.z.centery - tutto // 2 + B.s(10)
        self.P["mazzo"] = (self.x_lato, y0 + h // 2)
        self.P["scatola"] = (self.x_lato, y0 + h + conta + alto // 2)
        self.P["alto"] = alto

    def posto_mazzo(self, k):
        return (self.P["mazzo"][0] + k * 0.2, self.P["mazzo"][1] - k * 0.35)

    def riga(self, n, y, passo=None):
        """n carte in fila, centrate, all'altezza y."""
        w, _ = C.misura_carta()
        passo = passo or w * 1.08
        return [(self.z.centerx + (i - (n - 1) / 2.0) * passo, y)
                for i in range(n)]

    def ventaglio(self, n, sopra=False):
        pos = C.posti(n)[1 if sopra else 0]
        return pos

    # ---- carte
    def nuovo_mazzo(self, codici):
        self.carte, self.mazzo = [], []
        for k, cod in enumerate(codici):
            c = C.Carta(self.posto_mazzo(k), codice=cod)
            self.carte.append(c)
            self.mazzo.append(c)

    def in_cima(self, c):
        if c in self.carte:
            self.carte.remove(c)
        self.carte.append(c)

    def pesca(self):
        c = self.mazzo.pop()
        self.in_cima(c)
        return c

    def sposta(self, c, dove, ang=0.0, scoperta=None, ritardo=0.0,
               suono=None):
        c.su = 0.0
        c.vai(dove, ang, scoperta=scoperta, ritardo=ritardo, suono=suono)
        self.in_cima(c)

    def raccogli_tutto(self):
        """Tutte le carte tornano nel mazzo, coperte."""
        C.suona("cattura")
        random.shuffle(self.carte)
        self.mazzo = list(self.carte)
        for k, c in enumerate(self.mazzo):
            c.su = 0.0
            c.vai(self.posto_mazzo(k), 0.0, scoperta=False,
                  ritardo=k * 0.008)

    # ---- attese (generatori)
    def attendi(self, sec):
        t = sec
        while t > 0:
            t -= self.dt
            yield

    def fermi(self):
        while any(c.t < 1.0 or c.ritardo > 0 for c in self.carte):
            yield

    def messaggio(self, testo, sec=1.6):
        self.msg = [testo, sec]

    def scegli_carta(self, mano, valide=None):
        """Il giocatore sceglie una carta dalla sua mano: clic, oppure
        frecce e INVIO (anche col joystick)."""
        yield from self.fermi()
        valide = list(valide if valide is not None else mano)
        self.scegli = valide
        self.sel_carta = min(self.sel_carta, len(valide) - 1)
        scelta = None
        while scelta is None:
            yield
            sopra = self._carta_sotto_mouse()
            if sopra is not None and B.MOUSE_VIVO[0]:
                self.sel_carta = valide.index(sopra)
            for ev in self.eventi:
                if ev.type == pygame.KEYDOWN:
                    if ev.key in (pygame.K_LEFT, pygame.K_a):
                        self.sel_carta = (self.sel_carta - 1) % len(valide)
                    elif ev.key in (pygame.K_RIGHT, pygame.K_d):
                        self.sel_carta = (self.sel_carta + 1) % len(valide)
                    elif ev.key in (pygame.K_RETURN, pygame.K_KP_ENTER,
                                    pygame.K_SPACE):
                        scelta = valide[self.sel_carta]
                if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1 \
                        and sopra is not None:
                    scelta = sopra
        self.scegli = []
        return scelta

    def _carta_sotto_mouse(self):
        m = B.mouse_gioco()
        w, h = C.misura_carta()
        for c in reversed(self.scegli):
            if pygame.Rect(c.pos.x - w / 2, c.pos.y - h / 2 - c.su, w,
                           h).collidepoint(m):
                return c
        return None

    def chiedi(self, opzioni, sel=0):
        """Pulsanti in basso a destra sul panno. Torna il numero scelto."""
        yield from self.fermi()
        self.bottoni = list(opzioni)
        self.sel_bottone = min(sel, len(opzioni) - 1)
        scelta = None
        while scelta is None:
            yield
            m = B.mouse_gioco()
            for i, r in enumerate(self.rett_bottoni):
                if B.MOUSE_VIVO[0] and r.collidepoint(m):
                    self.sel_bottone = i
            for ev in self.eventi:
                if ev.type == pygame.KEYDOWN:
                    if ev.key in (pygame.K_UP, pygame.K_LEFT, pygame.K_w):
                        self.sel_bottone = (self.sel_bottone - 1) % \
                            len(self.bottoni)
                        B.suona_fx("menu_tic", 0.6)
                    elif ev.key in (pygame.K_DOWN, pygame.K_RIGHT,
                                    pygame.K_s):
                        self.sel_bottone = (self.sel_bottone + 1) % \
                            len(self.bottoni)
                        B.suona_fx("menu_tic", 0.6)
                    elif ev.key in (pygame.K_RETURN, pygame.K_KP_ENTER,
                                    pygame.K_SPACE):
                        scelta = self.sel_bottone
                if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                    for i, r in enumerate(self.rett_bottoni):
                        if r.collidepoint(m):
                            scelta = i
        self.bottoni = []
        return scelta

    # ---- un fotogramma
    def frame(self):
        self.dt = self.clock.tick(60) / 1000.0
        self.eventi = []
        for ev in B.eventi():
            if ev.type == pygame.QUIT:
                raise Esci("quit")
            if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                raise Esci("menu")
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 3:
                raise Esci("menu")
            self.eventi.append(ev)
        # la carta scelta si alza
        sotto = self.scegli[self.sel_carta] if self.scegli else None
        for c in self.carte:
            voglio = B.s(18) if c is sotto else 0.0
            if c.su or voglio:
                c.su += (voglio - c.su) * min(1.0, self.dt * 14)
            c.passo(self.dt)
        self.disegna()
        B.presenta()

    def disegna(self):
        sc = self.sc
        sc.blit(B.fondo(), (0, 0))
        tav = C.tavolo_carte(self.ip, self.ib)
        if tav is not None:
            sc.blit(tav, B.TAV_POS)
        C.fila_targhette(sc, self.nomi, self.punti, self.attivo)
        self._nome_gioco()
        small = B.FONTS["small"]
        self._disegna_bottoni()
        self._conta_mazzo()
        if self.msg[1] > 0:
            self.msg[1] -= self.dt
        self._messaggio_sotto()
        if self.tabella:
            self._disegna_tabella()
        if B.modo_comandi() == "pad" and B.ICONE_TASTI_OK():
            t = B.riga_pad(small, RIGA_PAD_CARTE)
        else:
            t = small.render(T("help_game"), True, (150, 156, 168))
        sc.blit(t, t.get_rect(center=(B.WIN_W // 2, B.WIN_H - B.s(40))))

    def _nome_gioco(self):
        """Il nome del gioco in alto a sinistra, dove nel biliardo sta lo
        stemma del torneo: col carattere elegante, in oro, tradotto. Se
        non ci sta in una riga va a capo."""
        if not self.gioco:
            return
        f = B.FONTS.get("elegante_voce") or B.FONTS["font"]
        largo = max(B.s(40), self.x_lato * 2 - B.s(12))
        parole = B.tit_el(T(self.gioco)).split()
        righe, ora = [], ""
        for p in parole:
            prova = (ora + " " + p).strip()
            if ora and f.size(prova)[0] > largo:
                righe.append(ora)
                ora = p
            else:
                ora = prova
        righe.append(ora)
        y = B.ALTO + B.s(10)
        for r in righe:
            t = f.render(r, True, B.ORO_SCELTA)
            if t.get_width() > largo:
                k = largo / float(t.get_width())
                t = pygame.transform.smoothscale(
                    t, (int(t.get_width() * k), int(t.get_height() * k)))
            self.sc.blit(t, t.get_rect(midtop=(self.x_lato, y)))
            y += t.get_height()

    def _banda_sotto(self):
        sotto = B.BANDA_PUNTI.copy()
        legno_su = B.TAV_POS[1] + C.LEGNO_FUORI.top * B.SCALA
        legno_giu = B.TAV_POS[1] + C.LEGNO_FUORI.bottom * B.SCALA
        sotto.centery = int(legno_giu + (legno_su - int(legno_su / 2)))
        return sotto, legno_giu

    def _messaggio_sotto(self):
        """Il messaggio sotto il tavolo, in mezzo, come nel biliardo: fra
        il legno e la fascia dei punteggi."""
        if self.msg[1] > 0:
            testo = self.msg[0]
        elif self.righe:
            testo = "     ".join(self.righe)
        else:
            return
        sotto, _ = self._banda_sotto()
        t = font_carte(18).render(testo, True, B.TESTO)
        self.sc.blit(t, t.get_rect(center=(B.WIN_W // 2, sotto.centery)))

    def _conta_mazzo(self):
        """Sotto il mazzo, quante carte restano."""
        if not self.mazzo:
            return
        w, h = C.misura_carta()
        t = B.FONTS["small"].render(str(len(self.mazzo)), True, B.ORO_SOTTO)
        self.sc.blit(t, t.get_rect(midtop=(self.P["mazzo"][0],
                                           self.P["mazzo"][1] + h // 2 +
                                           B.s(10))))

    def _scritta(self, sup, testo, font, col, centro, k=1.0):
        """Una scritta bianca sul panno, con un filo d'ombra: niente
        riquadri, il tavolo libero basta."""
        t = font.render(testo, True, col)
        o = font.render(testo, True, (0, 0, 0))
        if k != 1.0:
            dim = (max(1, int(t.get_width() * k)), max(1, int(t.get_height() * k)))
            t = pygame.transform.smoothscale(t, dim)
            o = pygame.transform.smoothscale(o, dim)
        o.set_alpha(110)
        r = t.get_rect(center=(int(centro[0] * k), int(centro[1] * k)))
        sup.blit(o, r.move(max(1, int(B.s(2) * k)), max(1, int(B.s(2) * k))))
        sup.blit(t, r)

    def _disegna_tabella(self):
        """Fine mano: in mezzo le voci (carte, denari...), a sinistra i
        numeri del giocatore in basso, a destra quelli dell'avversario, e
        in cima a ogni colonna il suo diamantino col punteggio."""
        tb = self.tabella
        sc = self.sc
        small, font = B.FONTS["small"], B.FONTS["font"]
        el = B.FONTS.get("elegante_voce") or font
        cx, dx = self.z.centerx, B.s(170)
        passo = small.get_height() + B.s(14)
        n = len(tb["righe"])
        y = self.z.centery - (n + 2) * passo // 2
        if tb.get("titolo"):
            self._scritta(sc, B.tit_el(tb["titolo"]), el, B.ORO_SCELTA,
                          (cx, y - passo))
        for lato, (x, col) in enumerate(((cx - dx, C.COL_POSTI[0]),
                                         (cx + dx, C.COL_POSTI[1]))):
            t = font.render(str(tb["tot"][lato]), True, (255, 255, 255))
            w = B.s(16) + B.s(10) + t.get_width()
            x0 = x - w // 2
            C.rombo(sc, (x0 + B.s(6), y + B.s(2)), col, B.s(6), B.s(10))
            sc.blit(t, t.get_rect(midleft=(x0 + B.s(22), y + B.s(2))))
        y += passo + B.s(8)
        for voce, a, b in tb["righe"]:
            self._scritta(sc, voce, small, B.ORO_SOTTO, (cx, y))
            self._scritta(sc, str(a), small, (255, 255, 255), (cx - dx, y))
            self._scritta(sc, str(b), small, (255, 255, 255), (cx + dx, y))
            y += passo
        if tb.get("fondo"):
            self._scritta(sc, tb["fondo"], font, B.ORO_SCELTA,
                          (cx, y + B.s(10)))

    def _disegna_bottoni(self):
        """Le scelte come nei menu (stesso carattere, la scelta accesa con
        la barretta d'oro), in colonna nella fascia a destra del tavolo."""
        self.rett_bottoni = []
        if not self.bottoni:
            return
        legno_dx = int(B.TAV_POS[0] + C.LEGNO_FUORI.right * B.SCALA)
        x0, x1 = legno_dx + B.s(10), B.WIN_W - B.s(8)
        largo = x1 - x0 - B.s(24)
        f = font_carte(19)
        testi = [B.tit_el(b) for b in self.bottoni]
        B.tic_menu(tuple(self.bottoni), self.sel_bottone)
        passo = f.get_height() + B.s(14)
        y = self.z.centery - (len(testi) - 1) * passo // 2
        for i, testo in enumerate(testi):
            acceso = i == self.sel_bottone
            t = f.render(testo, True, (255, 255, 255) if acceso
                         else (196, 200, 208))
            if t.get_width() > largo:
                k = largo / float(t.get_width())
                t = pygame.transform.smoothscale(
                    t, (int(t.get_width() * k), int(t.get_height() * k)))
            fondo = pygame.Rect(x0, y - (passo - B.s(8)) // 2, x1 - x0,
                                passo - B.s(8))
            if acceso:
                q = pygame.Surface(fondo.size, pygame.SRCALPHA)
                q.fill((255, 255, 255, 18))
                self.sc.blit(q, fondo)
                pygame.draw.rect(self.sc, B.COL_GIOC[0],
                                 (fondo.x, fondo.y, max(1, B.s(3)), fondo.h))
            self.sc.blit(t, t.get_rect(midleft=(x0 + B.s(14), y)))
            self.rett_bottoni.append(fondo)
            y += passo

    def sopra_scena(self, sup, k):
        C.disegna_scatola(sup, self.P["scatola"], self.P["alto"], k)
        for c in self.carte:
            c.disegna(sup, k)

    # ---- il giro
    def gioca(self, partita):
        """Fa girare il generatore della partita. Torna "menu" o "quit"."""
        B.SOPRA_SCENA[0] = self.sopra_scena
        gen = partita(self)
        try:
            while True:
                self.frame()
                try:
                    next(gen)
                except StopIteration as fine:
                    return fine.value or "menu"
        except Esci as e:
            return str(e)
        finally:
            B.SOPRA_SCENA[0] = None


def nome_giocatore():
    return B.NOMI[0] or "Player 1"


# ----------------------------------------------------------- sette e mezzo
def valore_sette(cod):
    n = num(cod)
    return 0.5 if n >= 8 else float(n)


def totale_sette(codici):
    """Il totale, con la matta (il re di denari) al valore migliore."""
    base = sum(valore_sette(c) for c in codici if c != "10d")
    if "10d" not in codici:
        return base
    meglio = base + 0.5
    for v in (0.5, 1, 2, 3, 4, 5, 6, 7):
        if base + v <= 7.5:
            meglio = max(meglio, base + v)
    return meglio


def scritta_sette(v):
    intero = int(v)
    mezzo = v - intero >= 0.5
    if intero == 0 and mezzo:
        return "½"
    return "%d%s" % (intero, "½" if mezzo else "")


def reale(codici):
    return len(codici) == 2 and totale_sette(codici) == 7.5 and \
        any(num(c) == 7 for c in codici)


def partita_sette(T_):
    tv = T_
    puntate = (10, 50, 100, 500)
    y_tu = tv.z.bottom - B.s(C.CARTA_H) * 0.62
    y_banco = tv.z.top + B.s(C.CARTA_H) * 0.62
    while True:
        tv.nuovo_mazzo(C.mazzo_codici())
        random.shuffle(tv.mazzo)
        for k, c in enumerate(tv.mazzo):
            c.vai(tv.posto_mazzo(k), 0.0)
        tv.punti = ["", ""]
        tv.righe = [T("bet")]
        opz = [B.dollari(p) for p in puntate if p <= B.soldi()]
        if not opz:
            opz = [T("free")]
        i = yield from tv.chiedi(opz + [T("leave")])
        if i == len(opz):
            return "menu"
        tv.righe = []
        posta = puntate[i] if opz[0] != T("free") else 0
        tv.righe = [T("bet_is") % B.dollari(posta) if posta else T("free")]
        mia, banco = [], []

        def rifai(mano, y, scoperte=True):
            pos = tv.riga(len(mano), y)
            for c, p in zip(mano, pos):
                tv.sposta(c, p, 0.0, scoperta=scoperte if c is not banco[0]
                          or banco_aperto[0] else False, suono="servi")
        banco_aperto = [False]
        mia.append(tv.pesca())
        banco.append(tv.pesca())
        rifai(mia, y_tu)
        rifai(banco, y_banco)
        tv.punti = [scritta_sette(totale_sette([c.codice for c in mia])), "?"]
        yield from tv.fermi()
        sballato = False
        while True:
            tot = totale_sette([c.codice for c in mia])
            if tot > 7.5:
                sballato = True
                break
            if tot == 7.5:
                break
            tv.attivo = 0
            i = yield from tv.chiedi([T("card"), T("stand")])
            if i == 1:
                break
            mia.append(tv.pesca())
            rifai(mia, y_tu)
            tv.punti[0] = scritta_sette(totale_sette([c.codice for c in mia]))
            yield from tv.fermi()
        codici_miei = [c.codice for c in mia]
        mio = totale_sette(codici_miei)
        vinto = 0
        tv.attivo = 1
        banco_aperto[0] = True
        rifai(banco, y_banco)
        yield from tv.fermi()
        if sballato:
            tv.messaggio(T("bust"))
            vinto = -posta
        else:
            # il banco vede le tue carte tranne la prima
            visto = totale_sette(codici_miei[1:]) if len(mia) > 1 else 0
            while True:
                bt = totale_sette([c.codice for c in banco])
                tv.punti[1] = scritta_sette(bt)
                if bt >= max(5.0, min(7.5, visto + 0.5)) or bt >= 7.5:
                    break
                yield from tv.attendi(0.5)
                banco.append(tv.pesca())
                rifai(banco, y_banco)
                yield from tv.fermi()
            bt = totale_sette([c.codice for c in banco])
            tv.punti[1] = scritta_sette(bt)
            if bt > 7.5:
                tv.messaggio(T("banker_bust"))
                vinto = posta
            elif mio > bt:
                vinto = posta
            elif mio == bt:
                tv.messaggio(T("tie_banker"))
                vinto = -posta
            else:
                vinto = -posta
            if vinto > 0 and reale(codici_miei) and \
                    not reale([c.codice for c in banco]):
                tv.messaggio(T("reale"))
                vinto = posta * 2
        yield from tv.attendi(1.2)
        if vinto:
            B.soldi(vinto)
            B.salva_config()
        C.suona("levelup" if vinto > 0 else "gameover")
        tv.righe = [T("you_win") % B.dollari(vinto) if vinto > 0 else
                    T("you_lose") % B.dollari(-vinto) if vinto < 0 else
                    T("tie_banker")]
        tv.attivo = 0
        i = yield from tv.chiedi([T("next"), T("leave")])
        tv.righe = []
        tv.raccogli_tutto()
        yield from tv.fermi()
        if i == 1:
            return "menu"


# ---------------------------------------------------------------- scopa
PRIMIERA = {7: 21, 6: 18, 1: 16, 5: 15, 4: 14, 3: 13, 2: 12,
            8: 10, 9: 10, 10: 10}


def prese_possibili(cod, tavolo):
    """Le prese che fa una carta: se c'e' una carta uguale si prende
    quella (una sola), se no ogni gruppo che fa la somma."""
    v = num(cod)
    uguali = [[t] for t in tavolo if num(t) == v]
    if uguali:
        return uguali
    out = []
    for n in range(2, len(tavolo) + 1):
        for gr in itertools.combinations(tavolo, n):
            if sum(num(t) for t in gr) == v:
                out.append(list(gr))
    return out


def valuta_presa(cod, presa, tavolo, ultima):
    tutte = presa + [cod]
    p = len(tutte) * 3
    p += sum(8 for t in tutte if seme(t) == "d")
    p += 40 if "7d" in tutte else 0
    p += sum(6 for t in tutte if num(t) == 7)
    p += sum(2 for t in tutte if num(t) == 6)
    if len(presa) == len(tavolo) and not ultima:
        p += 100
    return p


def mossa_cpu_scopa(mano, tavolo, ultima):
    meglio, mossa = -9999, None
    for cod in mano:
        prese = prese_possibili(cod, tavolo)
        if prese:
            for pr in prese:
                v = valuta_presa(cod, pr, tavolo, ultima) + 20
                resto = [t for t in tavolo if t not in pr]
                if resto and sum(num(t) for t in resto) <= 10:
                    v -= 25
                if v > meglio:
                    meglio, mossa = v, (cod, pr)
        else:
            dopo = tavolo + [cod]
            v = -num(cod)
            if sum(num(t) for t in dopo) <= 10:
                v -= 60                     # regalerebbe una scopa
            if seme(cod) == "d":
                v -= 8
            if cod == "7d":
                v -= 50
            if num(cod) == 7:
                v -= 12
            if v > meglio:
                meglio, mossa = v, (cod, [])
    return mossa


def conta_scopa(prese_a, prese_b, scope):
    """I punti di fine mano: [a, b] e le righe del riepilogo."""
    pt = [scope[0], scope[1]]
    righe = []

    def dai(nome, a, b):
        if a > b:
            pt[0] += 1
        elif b > a:
            pt[1] += 1
        righe.append((nome, a, b))
    dai(T("p_cards"), len(prese_a), len(prese_b))
    dai(T("p_coins"), sum(1 for c in prese_a if seme(c) == "d"),
        sum(1 for c in prese_b if seme(c) == "d"))
    sa, sb = ("7d" in prese_a), ("7d" in prese_b)
    dai(T("p_sette"), int(sa), int(sb))

    def primiera(prese):
        tot = 0
        for sm in C.SEMI_IT:
            v = [PRIMIERA[num(c)] for c in prese if seme(c) == sm]
            if not v:
                return 0
            tot += max(v)
        return tot
    dai(T("p_prim"), primiera(prese_a), primiera(prese_b))
    righe.append((T("p_scope"), scope[0], scope[1]))
    return pt, righe


def partita_scopa(tv):
    totali = [0, 0]
    chi_inizia = 0
    y_tavolo = tv.z.centery
    while True:
        tv.nuovo_mazzo(C.mazzo_codici())
        random.shuffle(tv.mazzo)
        for k, c in enumerate(tv.mazzo):
            c.vai(tv.posto_mazzo(k), 0.0)
        mani = [[], []]
        tavolo = []
        prese = [[], []]
        scope = [0, 0]
        ultimo = None
        mucchi = [(tv.z.right - B.s(70), tv.z.bottom - B.s(78)),
                  (tv.z.right - B.s(70), tv.z.top + B.s(78))]
        tv.punti = list(totali)

        def sistema_tavolo():
            w, h = C.misura_carta()
            n = len(tavolo)
            fila = min(n, 8)
            for i, c in enumerate(tavolo):
                r, col = divmod(i, 8)
                nr = fila if r == 0 else n - 8
                pos = tv.riga(nr, y_tavolo - (h * 0.58 if n > 8 else 0)
                              + r * h * 1.16)
                tv.sposta(c, pos[col], 0.0, scoperta=True)

        def distribuisci(prima=False):
            rit = 0.0
            for giro in range(3):
                for chi in (chi_inizia, 1 - chi_inizia):
                    if tv.mazzo:
                        c = tv.pesca()
                        mani[chi].append(c)
            for chi in (0, 1):
                pos = tv.ventaglio(len(mani[chi]), sopra=chi == 1)
                for c, (p, a) in zip(mani[chi], pos):
                    tv.sposta(c, p, a, scoperta=chi == 0, ritardo=rit,
                              suono="servi")
                    rit += 0.06
            if prima:
                for _ in range(4):
                    tavolo.append(tv.pesca())
                sistema_tavolo()

        def rifai_mano(chi):
            pos = tv.ventaglio(len(mani[chi]), sopra=chi == 1)
            for c, (p, a) in zip(mani[chi], pos):
                tv.sposta(c, p, a)

        distribuisci(True)
        yield from tv.fermi()
        turno = chi_inizia
        while mani[0] or mani[1]:
            tv.attivo = turno
            ultima = not tv.mazzo and len(mani[0]) + len(mani[1]) == 1
            codici_tav = [c.codice for c in tavolo]
            if turno == 0:
                c = yield from tv.scegli_carta(mani[0])
                opz = prese_possibili(c.codice, codici_tav)
                presa = max(opz, key=lambda pr: valuta_presa(
                    c.codice, pr, codici_tav, ultima)) if opz else []
            else:
                yield from tv.attendi(0.6)
                cod, presa = mossa_cpu_scopa([x.codice for x in mani[1]],
                                             codici_tav, ultima)
                c = next(x for x in mani[1] if x.codice == cod)
            mani[turno].remove(c)
            rifai_mano(turno)
            tv.sposta(c, (tv.z.centerx, y_tavolo + (B.s(60) if turno == 0
                                                    else -B.s(60))),
                      0.0, scoperta=True, suono="giocata")
            yield from tv.fermi()
            yield from tv.attendi(0.35)
            if presa:
                prendi = [x for x in tavolo if x.codice in presa]
                scopa = len(prendi) == len(tavolo) and not ultima
                for x in prendi:
                    tavolo.remove(x)
                for i, x in enumerate(prendi + [c]):
                    tv.sposta(x, mucchi[turno], 90.0, scoperta=False,
                              ritardo=i * 0.05)
                prese[turno] += [x.codice for x in prendi] + [c.codice]
                ultimo = turno
                C.suona("cattura")
                if scopa:
                    scope[turno] += 1
                    tv.messaggio(T("scopa_msg"))
                    C.suona("colpo")
                    tv.punti[turno] = totali[turno] + scope[turno]
                sistema_tavolo()
            else:
                tavolo.append(c)
                sistema_tavolo()
            yield from tv.fermi()
            turno = 1 - turno
            if not mani[0] and not mani[1] and tv.mazzo:
                distribuisci()
                yield from tv.fermi()
        # le carte rimaste vanno a chi ha preso per ultimo
        if tavolo and ultimo is not None:
            for x in tavolo:
                tv.sposta(x, mucchi[ultimo], 90.0, scoperta=False)
                prese[ultimo].append(x.codice)
            tavolo = []
            C.suona("cattura")
            yield from tv.fermi()
        pt, righe = conta_scopa(prese[0], prese[1], scope)
        totali = [totali[0] + pt[0], totali[1] + pt[1]]
        tv.punti = list(totali)
        tv.tabella = {"titolo": T("hand_over"), "righe": righe,
                      "tot": list(totali)}
        fine = max(totali) >= 11 and totali[0] != totali[1]
        if fine:
            vince = 0 if totali[0] > totali[1] else 1
            tv.tabella["fondo"] = T("win_match") % tv.nomi[vince]
            C.suona("levelup" if vince == 0 else "gameover")
            i = yield from tv.chiedi([T("again"), T("menu")])
            tv.tabella = None
            if i == 1:
                return "menu"
            totali = [0, 0]
        else:
            yield from tv.chiedi([T("next")])
            tv.tabella = None
        tv.raccogli_tutto()
        yield from tv.fermi()
        chi_inizia = 1 - chi_inizia


# ------------------------------------------------------------- briscola
FORZA = {1: 10, 3: 9, 10: 8, 9: 7, 8: 6, 7: 5, 6: 4, 5: 3, 4: 2, 2: 1}
PUNTI_BR = {1: 11, 3: 10, 10: 4, 9: 3, 8: 2}


def vince_presa(prima, seconda, brisc):
    """0 se vince la prima carta, 1 se la seconda."""
    if seme(seconda) == seme(prima):
        return 1 if FORZA[num(seconda)] > FORZA[num(prima)] else 0
    return 1 if seme(seconda) == brisc else 0


def punti_br(cod):
    return PUNTI_BR.get(num(cod), 0)


def mossa_cpu_briscola(mano, sul_tavolo, brisc):
    def costo(c):
        return (punti_br(c) + (15 if seme(c) == brisc else 0) +
                FORZA[num(c)] * 0.1)
    if sul_tavolo is None:
        return min(mano, key=costo)
    vincenti = [c for c in mano if vince_presa(sul_tavolo, c, brisc) == 1]
    in_palio = punti_br(sul_tavolo)
    if vincenti:
        ok = min(vincenti, key=costo)
        stesso_seme = seme(ok) == seme(sul_tavolo)
        if in_palio >= 10 or stesso_seme or (in_palio >= 3 and
                                              punti_br(ok) == 0):
            return ok
    return min(mano, key=costo)


def partita_briscola(tv):
    y_mezzo = tv.z.centery
    chi_inizia = 0
    while True:
        tv.nuovo_mazzo(C.mazzo_codici())
        random.shuffle(tv.mazzo)
        for k, c in enumerate(tv.mazzo):
            c.vai(tv.posto_mazzo(k), 0.0)
        mani = [[], []]
        prese = [[], []]
        mucchi = [(tv.z.right - B.s(70), tv.z.bottom - B.s(78)),
                  (tv.z.right - B.s(70), tv.z.top + B.s(78))]
        tv.punti = [0, 0]

        def rifai_mano(chi, rit=0.0, suono=None):
            pos = tv.ventaglio(len(mani[chi]), sopra=chi == 1)
            for c, (p, a) in zip(mani[chi], pos):
                tv.sposta(c, p, a, scoperta=chi == 0, ritardo=rit,
                          suono=suono)
                rit += 0.06 if suono else 0.0

        for _ in range(3):
            for chi in (chi_inizia, 1 - chi_inizia):
                mani[chi].append(tv.pesca())
        rifai_mano(0, 0.0, "servi")
        rifai_mano(1, 0.2, "servi")
        # la briscola: scoperta, di traverso sotto il mazzo
        br = tv.pesca()
        tv.carte.remove(br)
        tv.carte.insert(0, br)
        tv.mazzo.insert(0, br)
        w, _ = C.misura_carta()
        br.vai((tv.P["mazzo"][0] + w * 0.55, tv.P["mazzo"][1]), 90.0,
               scoperta=True, ritardo=0.5)
        brisc = seme(br.codice)
        yield from tv.fermi()
        turno = chi_inizia
        while mani[0] or mani[1]:
            tv.righe = [T("trump") % T(brisc)]
            giocate = []
            for chi in (turno, 1 - turno):
                tv.attivo = chi
                if chi == 0:
                    c = yield from tv.scegli_carta(mani[0])
                else:
                    yield from tv.attendi(0.6)
                    cod = mossa_cpu_briscola(
                        [x.codice for x in mani[1]],
                        giocate[0].codice if giocate else None, brisc)
                    c = next(x for x in mani[1] if x.codice == cod)
                mani[chi].remove(c)
                rifai_mano(chi)
                dx = -B.s(44) if not giocate else B.s(44)
                tv.sposta(c, (tv.z.centerx + dx,
                              y_mezzo + (B.s(14) if chi == 0 else -B.s(14))),
                          random.uniform(-6, 6), scoperta=True,
                          suono="giocata")
                giocate.append(c)
                yield from tv.fermi()
            yield from tv.attendi(0.7)
            v = vince_presa(giocate[0].codice, giocate[1].codice, brisc)
            chi_vince = turno if v == 0 else 1 - turno
            for i, x in enumerate(giocate):
                tv.sposta(x, mucchi[chi_vince], 90.0, scoperta=False,
                          ritardo=i * 0.06)
                prese[chi_vince].append(x.codice)
            C.suona("cattura")
            tv.punti[chi_vince] = sum(punti_br(x) for x in prese[chi_vince])
            yield from tv.fermi()
            # pesca prima chi ha vinto
            for chi in (chi_vince, 1 - chi_vince):
                if tv.mazzo:
                    c = tv.pesca()
                    mani[chi].append(c)
            if tv.mazzo or len(mani[0]) + len(mani[1]) < 6:
                rifai_mano(0, 0.0, "servi")
                rifai_mano(1, 0.1, "servi")
                yield from tv.fermi()
            turno = chi_vince
        tv.righe = []
        a, b = tv.punti
        if a > b:
            esito = T("win_match") % tv.nomi[0]
            C.suona("levelup")
        elif b > a:
            esito = T("win_match") % tv.nomi[1]
            C.suona("gameover")
        else:
            esito = T("draw")
        tv.tabella = {"titolo": T("hand_over"), "tot": [a, b],
                      "righe": [(T("p_cards"), len(prese[0]), len(prese[1]))],
                      "fondo": esito}
        i = yield from tv.chiedi([T("again"), T("menu")])
        tv.tabella = None
        if i == 1:
            return "menu"
        tv.raccogli_tutto()
        yield from tv.fermi()
        chi_inizia = 1 - chi_inizia


# ------------------------------------------------------------ blackjack
def mazzo_francese(n=1, jolly=0):
    codici = [r + sm for sm in "SHDC" for r in "A23456789TJQK"] * n
    return codici + ["JK"] * jolly


def valore_bj(codici):
    tot, assi = 0, 0
    for c in codici:
        r = c[0]
        if r == "A":
            tot, assi = tot + 11, assi + 1
        elif r in "TJQK":
            tot += 10
        else:
            tot += int(r)
    while tot > 21 and assi:
        tot, assi = tot - 10, assi - 1
    return tot


def partita_blackjack(tv):
    puntate = (10, 50, 100, 500)
    y_tu = tv.z.bottom - B.s(C.CARTA_H) * 0.62
    y_banco = tv.z.top + B.s(C.CARTA_H) * 0.62
    passo = C.misura_carta()[0] * 0.62
    tv.nuovo_mazzo(mazzo_francese(2))
    random.shuffle(tv.mazzo)
    for k, c in enumerate(tv.mazzo):
        c.vai(tv.posto_mazzo(k), 0.0)
    while True:
        if len(tv.mazzo) < 30:          # il sabot si rimescola
            tv.raccogli_tutto()
            yield from tv.fermi()
        tv.punti = ["", ""]
        tv.righe = [T("bet")]
        opz = [B.dollari(p) for p in puntate if p <= B.soldi()]
        libero = not opz
        if libero:
            opz = [T("free")]
        i = yield from tv.chiedi(opz + [T("leave")])
        if i == len(opz):
            return "menu"
        tv.righe = []
        posta = 0 if libero else puntate[i]
        tv.righe = [T("bet_is") % B.dollari(posta) if posta else T("free")]
        mia, banco = [], []
        coperta = [True]

        def rifai(mano, y, e_banco=False):
            pos = tv.riga(len(mano), y, passo)
            for c, p in zip(mano, pos):
                sc_ = not (e_banco and c is banco[1] and coperta[0]) \
                    if len(banco) > 1 else True
                tv.sposta(c, p, 0.0, scoperta=sc_, suono="servi")

        def tot(m):
            return valore_bj([c.codice for c in m])
        for giro in range(2):
            mia.append(tv.pesca())
            rifai(mia, y_tu)
            yield from tv.attendi(0.25)
            banco.append(tv.pesca())
            rifai(banco, y_banco, True)
            yield from tv.attendi(0.25)
        tv.punti = [tot(mia), valore_bj([banco[0].codice])]
        yield from tv.fermi()
        if tot(mia) < 21:
            while True:
                tv.attivo = 0
                scelte = [T("hit"), T("bj_stand")]
                if len(mia) == 2 and (libero or B.soldi() >= posta * 2):
                    scelte.append(T("double"))
                i = yield from tv.chiedi(scelte)
                if i == 1:
                    break
                mia.append(tv.pesca())
                rifai(mia, y_tu)
                tv.punti[0] = tot(mia)
                yield from tv.fermi()
                if i == 2:
                    posta *= 2
                    break
                if tot(mia) >= 21:
                    break
        mio = tot(mia)
        bj_mio = mio == 21 and len(mia) == 2
        tv.attivo = 1
        coperta[0] = False
        rifai(banco, y_banco, True)
        tv.punti[1] = tot(banco)
        yield from tv.fermi()
        if mio <= 21 and not bj_mio:
            while tot(banco) < 17:
                yield from tv.attendi(0.5)
                banco.append(tv.pesca())
                rifai(banco, y_banco, True)
                tv.punti[1] = tot(banco)
                yield from tv.fermi()
        bt = tot(banco)
        bj_banco = bt == 21 and len(banco) == 2
        if mio > 21:
            vinto, testo = -posta, T("bust")
        elif bj_mio and not bj_banco:
            vinto, testo = posta * 3 // 2, T("bj")
        elif bj_banco and not bj_mio:
            vinto, testo = -posta, T("dealer") + " " + T("bj")
        elif bt > 21 or mio > bt:
            vinto, testo = posta, T("you_win") % B.dollari(posta)
        elif mio == bt:
            vinto, testo = 0, T("push")
        else:
            vinto, testo = -posta, T("you_lose") % B.dollari(posta)
        tv.messaggio(testo, 1.4)
        yield from tv.attendi(1.2)
        if vinto:
            B.soldi(vinto)
            B.salva_config()
        C.suona("levelup" if vinto > 0 else "gameover" if vinto < 0
                else "giocata")
        tv.righe = [T("you_win") % B.dollari(vinto)] if vinto > 0 \
            else [testo]
        tv.attivo = 0
        i = yield from tv.chiedi([T("next"), T("leave")])
        tv.righe = []
        # le carte giocate vanno sotto il sabot, coperte
        usate = mia + banco
        for c in usate:
            tv.mazzo.insert(0, c)
            tv.carte.remove(c)
            tv.carte.insert(0, c)
        for k, c in enumerate(tv.mazzo):
            c.vai(tv.posto_mazzo(k), 0.0, scoperta=False)
        yield from tv.fermi()
        if i == 1:
            return "menu"


REGOLE_CARTE = {
    "en": {
        "blackjack": """You play against the dealer with two French decks.
- Place a bet, then you and the dealer get two cards each; one of the dealer's is face down.
- Number cards count their value, J, Q and K count 10, the Ace counts 11 or 1.
- Hit to take a card, Stand to stop. Over 21 you bust and lose.
- Double: on your first two cards you double the bet and take exactly one more card.
- The dealer draws until 17 or more.
- Closer to 21 than the dealer wins even money. Blackjack (Ace and a 10 card) pays 3 to 2. A tie is a push.""",
        "sette": """You play against the banker with the 40 Italian cards.
- Cards 1 to 7 count their value, the figures (Fante, Cavallo, Re) count half a point.
- The King of Coins is the wild card: it takes the value that suits you best.
- Place a bet, then ask for cards or stand. Over seven and a half you bust.
- The banker then draws. A tie goes to the banker.
- Sette e mezzo reale (a 7 and a figure with two cards) pays double.""",
        "scopa": """One against one with the 40 Italian cards: 3 cards each, 4 on the table.
- Play a card: if one on the table has the same value you take it; if not, you can take cards that add up to its value.
- If there is a card of the same value you must take that one, not a sum.
- Clearing the table is a scopa and is worth one point (not on the last play of the hand).
- When the hands are empty, 3 more each until the deck is over. What is left goes to the last to take.
- Points: most cards, most Coins, the Seven of Coins (settebello), the best primiera, one per scopa.
- The first to 11 wins the match.""",
        "briscola": """One against one with the 40 Italian cards: 3 cards each.
- The card under the deck shows the trump suit (briscola).
- The trick goes to the higher card of the suit led, unless a trump is played: the trump wins.
- Order: Ace, Three, King, Cavallo, Fante, 7, 6, 5, 4, 2.
- Points: Ace 11, Three 10, King 4, Cavallo 3, Fante 2. 120 in all.
- Whoever takes draws first. Over 60 points wins.""",
        "ramino": """Coming soon.""",
    },
    "it": {
        "blackjack": """Si gioca contro il banco con due mazzi di carte francesi.
- Fai la puntata, poi tu e il banco ricevete due carte; una del banco e' coperta.
- Le carte numerate valgono il loro numero, J, Q e K valgono 10, l'Asso 11 o 1.
- Carta per prenderne un'altra, Sto per fermarti. Oltre 21 sballi e perdi.
- Raddoppia: sulle prime due carte raddoppi la puntata e prendi una sola carta.
- Il banco pesca finche' non arriva a 17 o piu'.
- Chi va piu' vicino a 21 del banco vince alla pari. Il blackjack (Asso e un 10) paga 3 a 2. Il pari e' patta.""",
        "sette": """Si gioca contro il banco con le 40 carte italiane.
- Le carte da 1 a 7 valgono il loro numero, le figure (Fante, Cavallo, Re) mezzo punto.
- Il Re di denari e' la matta: prende il valore che ti conviene di piu'.
- Fai la puntata, poi chiedi carta o stai. Oltre sette e mezzo sballi.
- Poi gioca il banco. A parita' vince il banco.
- Il sette e mezzo reale (un 7 e una figura con due carte) paga doppio.""",
        "scopa": """Uno contro uno con le 40 carte italiane: 3 carte a testa, 4 in tavola.
- Giochi una carta: se in tavola ce n'e' una dello stesso valore la prendi, se no puoi prendere carte che sommate fanno il suo valore.
- Se c'e' una carta uguale devi prendere quella, non la somma.
- Se porti via tutte le carte in tavola fai scopa: vale un punto (non all'ultima giocata della mano).
- Finite le carte in mano, altre 3 a testa fino alla fine del mazzo. Quelle rimaste vanno a chi ha preso per ultimo.
- Punti: piu' carte, piu' denari, il settebello, la primiera migliore, uno per ogni scopa.
- Vince chi arriva per primo a 11.""",
        "briscola": """Uno contro uno con le 40 carte italiane: 3 carte a testa.
- La carta sotto il mazzo indica il seme di briscola.
- La mano la prende la carta piu' alta del seme giocato per primo, a meno che si giochi una briscola: vince la briscola.
- Ordine: Asso, Tre, Re, Cavallo, Fante, 7, 6, 5, 4, 2.
- Punti: Asso 11, Tre 10, Re 4, Cavallo 3, Fante 2. In tutto 120.
- Chi prende pesca per primo. Vince chi fa piu' di 60 punti.""",
        "ramino": """Presto.""",
    },
    "fr": {
        "blackjack": """On joue contre le croupier avec deux jeux de cartes francaises.
- Misez, puis vous et le croupier recevez deux cartes ; une du croupier est cachee.
- Les cartes numerotees valent leur chiffre, J, Q et K valent 10, l'As 11 ou 1.
- Carte pour en prendre une, Reste pour s'arreter. Au-dela de 21 vous perdez.
- Doubler : sur les deux premieres cartes, la mise double et vous prenez une seule carte.
- Le croupier tire jusqu'a 17 ou plus.
- Plus pres de 21 que le croupier : gain a egalite. Le blackjack (As et un 10) paie 3 pour 2. Egalite : mise rendue.""",
        "sette": """On joue contre la banque avec les 40 cartes italiennes.
- Les cartes de 1 a 7 valent leur chiffre, les figures (Valet, Cavalier, Roi) un demi-point.
- Le Roi de deniers est joker : il prend la valeur qui vous arrange le plus.
- Misez, puis demandez une carte ou restez. Au-dela de sept et demi vous perdez.
- Puis la banque joue. En cas d'egalite la banque gagne.
- Le sette e mezzo royal (un 7 et une figure en deux cartes) paie double.""",
        "scopa": """Un contre un avec les 40 cartes italiennes : 3 cartes chacun, 4 sur la table.
- Jouez une carte : si une carte de meme valeur est sur la table vous la prenez, sinon vous pouvez prendre des cartes dont la somme fait sa valeur.
- S'il y a une carte de meme valeur, il faut prendre celle-la et non une somme.
- Vider la table fait une scopa, qui vaut un point (sauf au dernier coup de la main).
- Mains vides : 3 cartes de plus chacun jusqu'a la fin du paquet. Le reste va au dernier qui a pris.
- Points : plus de cartes, plus de deniers, le sept de deniers, la meilleure primiera, un par scopa.
- Le premier a 11 gagne.""",
        "briscola": """Un contre un avec les 40 cartes italiennes : 3 cartes chacun.
- La carte sous le paquet indique l'atout (briscola).
- Le pli va a la plus haute carte de la couleur jouee, sauf si un atout est joue : l'atout gagne.
- Ordre : As, Trois, Roi, Cavalier, Valet, 7, 6, 5, 4, 2.
- Points : As 11, Trois 10, Roi 4, Cavalier 3, Valet 2. 120 en tout.
- Qui prend pioche en premier. Plus de 60 points gagne.""",
        "ramino": """Bientot.""",
    },
    "es": {
        "blackjack": """Se juega contra el crupier con dos barajas francesas.
- Apuesta, luego tu y el crupier recibis dos cartas; una del crupier esta boca abajo.
- Las cartas numeradas valen su numero, J, Q y K valen 10, el As 11 o 1.
- Pedir para tomar otra carta, Plantarse para parar. Mas de 21 te pasas y pierdes.
- Doblar: con las dos primeras cartas doblas la apuesta y tomas una sola carta.
- El crupier pide hasta 17 o mas.
- Mas cerca de 21 que el crupier gana a la par. El blackjack (As y un 10) paga 3 a 2. El empate devuelve la apuesta.""",
        "sette": """Se juega contra la banca con las 40 cartas italianas.
- Las cartas del 1 al 7 valen su numero, las figuras (Sota, Caballo, Rey) medio punto.
- El Rey de oros es comodin: toma el valor que mas te conviene.
- Apuesta, luego pide carta o plantate. Mas de siete y medio te pasas.
- Luego juega la banca. En caso de empate gana la banca.
- El sette e mezzo real (un 7 y una figura con dos cartas) paga doble.""",
        "scopa": """Uno contra uno con las 40 cartas italianas: 3 cartas cada uno, 4 en la mesa.
- Juegas una carta: si en la mesa hay una del mismo valor la tomas; si no, puedes tomar cartas que sumen su valor.
- Si hay una carta del mismo valor debes tomar esa, no una suma.
- Llevarte todas las cartas de la mesa es escoba y vale un punto (no en la ultima jugada de la mano).
- Sin cartas en mano, 3 mas cada uno hasta acabar el mazo. Lo que queda es del ultimo que tomo.
- Puntos: mas cartas, mas oros, el siete de oros, la mejor primiera, uno por escoba.
- Gana el primero que llega a 11.""",
        "briscola": """Uno contra uno con las 40 cartas italianas: 3 cartas cada uno.
- La carta bajo el mazo indica el palo de triunfo (brisca).
- La baza es de la carta mas alta del palo jugado primero, salvo que se juegue un triunfo: gana el triunfo.
- Orden: As, Tres, Rey, Caballo, Sota, 7, 6, 5, 4, 2.
- Puntos: As 11, Tres 10, Rey 4, Caballo 3, Sota 2. 120 en total.
- Quien gana roba primero. Gana quien hace mas de 60 puntos.""",
        "ramino": """Pronto.""",
    },
}


def testo_regole_carte(chiave):
    d = REGOLE_CARTE.get(B.CFG.get("lingua", "en"), REGOLE_CARTE["en"])
    return d.get(chiave, REGOLE_CARTE["en"][chiave])


# ----------------------------------------------------------------- menu
# (chiave, partita, che carte usa)
GIOCHI = (("blackjack", partita_blackjack, "francesi"),
          ("sette", partita_sette, "italiane"),
          ("scopa", partita_scopa, "italiane"),
          ("briscola", partita_briscola, "italiane"),
          ("ramino", None, "francesi"))


def mazzi_per(tipo):
    m = C.mazzi_disponibili()
    if tipo == "francesi":
        return [x for x in m if x[1] == "francesi"]
    return [x for x in m if x[1] != "francesi"]


def nome_mazzo(cartella):
    return cartella.replace("_", " ").title()


def mazzo_del_gioco(chiave, tipo):
    """Il mazzo scelto per quel gioco (ognuno si ricorda il suo)."""
    m = mazzi_per(tipo)
    if not m:
        return 0
    voglio = B.CFG.get("mazzo_" + chiave)
    i = next((k for k, x in enumerate(m) if x[0] == voglio), 0)
    C.MAZZO_ORA[0], C.MAZZO_ORA[1] = m[i]
    C.FACCIA.clear()
    return i


def gioca_gioco(sc, clock, chiave, partita, tipo):
    mazzo_del_gioco(chiave, tipo)
    nomi = [nome_giocatore(),
            T("banker") if partita is partita_sette else
            T("dealer") if partita is partita_blackjack
            else random.choice(B.AVVERSARI)]
    C.carica_suoni()
    C.musica_carte()
    tv = Tavolo(sc, clock, nomi, chiave)
    esito = tv.gioca(partita)
    C.fine_musica_carte()
    return esito


def lista_menu(sc, clock, logo, sottotitolo, voci_fn, scelta_fn,
               gira_fn=None):
    """Un menu a righe come quelli del biliardo. voci_fn() da' le righe
    (etichetta, valore); scelta_fn(i) torna qualcosa per uscire o None;
    gira_fn(i, verso) cambia il valore della riga con le frecce."""
    sel = 0
    rett = []
    while True:
        clock.tick(60)
        mouse = B.mouse_gioco()
        voci = voci_fn()
        n = len(voci)
        sel = min(sel, n - 1)
        for ev in B.eventi():
            if ev.type == pygame.QUIT:
                return "quit"
            q = None
            if ev.type == pygame.KEYDOWN:
                if ev.key in (pygame.K_DOWN, pygame.K_s):
                    sel = (sel + 1) % n
                elif ev.key in (pygame.K_UP, pygame.K_w):
                    sel = (sel - 1) % n
                elif ev.key in (pygame.K_LEFT, pygame.K_a) and gira_fn:
                    gira_fn(sel, -1)
                elif ev.key in (pygame.K_RIGHT, pygame.K_d) and gira_fn:
                    gira_fn(sel, 1)
                elif ev.key in (pygame.K_RETURN, pygame.K_KP_ENTER,
                                pygame.K_SPACE):
                    q = scelta_fn(sel)
                elif ev.key == pygame.K_ESCAPE:
                    return "back"
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                for i, r in enumerate(rett):
                    if r.collidepoint(mouse):
                        q = scelta_fn(i)
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 3:
                return "back"
            if q is not None:
                return q
        font, small = B.FONTS["font"], B.FONTS["small"]
        B.sfondo_menu(sc, logo)
        t = small.render(sottotitolo() if callable(sottotitolo)
                         else sottotitolo, True, B.ORO_SOTTO)
        sc.blit(t, t.get_rect(center=(B.WIN_W // 2, B.s(270))))
        con_valori = any(v is not None for _, v in voci)
        porte = set(i for i, (_, v) in enumerate(voci) if v is None)
        rett = B.disegna_voci(sc, voci, sel, font, small, B.s(330), B.s(46),
                              frecce=con_valori, porte=porte)
        for i, r in enumerate(rett):
            if B.MOUSE_VIVO[0] and r.collidepoint(mouse):
                sel = i
        B.presenta()


def menu_gioco(sc, clock, logo, chiave, partita, tipo):
    """Il sottomenu di un gioco: Gioca, il mazzo (se ce n'e' da scegliere)
    e Indietro."""
    def mazzi():
        return mazzi_per(tipo)

    def ha_mazzi():
        return len(mazzi()) > 1

    def voci():
        v = [(T("play"), None)]
        if ha_mazzi():
            i = mazzo_del_gioco(chiave, tipo)
            v.append((T("deck"), nome_mazzo(mazzi()[i][0])))
        v += [(T("rules"), None), (T("back"), None)]
        return v

    def gira(i, verso):
        m = mazzi()
        if i == 1 and len(m) > 1:
            k = (mazzo_del_gioco(chiave, tipo) + verso) % len(m)
            B.CFG["mazzo_" + chiave] = m[k][0]
            B.salva_config()
            B.suona_fx("menu_tic", 0.6)

    def scelta(i):
        if i == 0:
            return "gioca"
        if ha_mazzi():
            if i == 1:
                gira(1, 1)
                return None
            i -= 1
        return "regole" if i == 1 else "back"

    while True:
        q = lista_menu(sc, clock, logo, T(chiave), voci, scelta, gira)
        if q == "regole":
            if B.pagina_regole(sc, clock, logo, None, T(chiave),
                               testo_regole_carte(chiave)) == "quit":
                return "quit"
            continue
        if q != "gioca":
            return q
        esito = gioca_gioco(sc, clock, chiave, partita, tipo)
        if esito == "quit":
            return "quit"
        B.musica_menu()


def menu_carte(sc, clock, logo):
    avviso = [-99999]

    def voci():
        v = [(T(k) if f else "%s  (%s)" % (T(k), T("soon")), None)
             for k, f, _ in GIOCHI]
        return v + [(T("settings"), None), (T("back"), None)]

    def sotto():
        if pygame.time.get_ticks() - avviso[0] < 1800:
            return T("soon")
        return T("cards")

    def scelta(i):
        if i < len(GIOCHI):
            if GIOCHI[i][1] is None:
                avviso[0] = pygame.time.get_ticks()
                return None
            return i
        if i == len(GIOCHI):
            return "settings"
        return "back"

    while True:
        q = lista_menu(sc, clock, logo, sotto, voci, scelta)
        if q == "quit":
            return "quit"
        if q == "back":
            return "menu"
        if q == "settings":
            if B.schermata_setting(sc, clock, logo, pagina="generale",
                                   puo_riaprire=True) == "quit":
                return "quit"
            continue
        chiave, partita, tipo = GIOCHI[q]
        if menu_gioco(sc, clock, logo, chiave, partita, tipo) == "quit":
            return "quit"
