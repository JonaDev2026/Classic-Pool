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
           "cont": "Continue", "hand_won": "%s wins the hand",
           "bet": "Place your bet", "free": "Free play",
           "bet_match": "Bet on the match", "bet_won": "Bet",
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
           "tie_again": "Tie: another hand",
           "win0": "You win", "lose0": "You lose",
           "choose_take": "Choose your capture",
           "r_draw": "Draw from deck",
           "r_take": "Take discard",
           "r_meld": "Meld",
           "r_attach": "Lay off",
           "r_discard": "Discard",
           "r_sort": "Sort",
           "r_bad": "Not a valid combination",
           "r_keep": "Keep one card to discard",
           "r_40": "Your first meld must be worth 50", "r_open_first": "Open with 50 points before you lay off", "r_one": "Pick one card to discard",
           "r_use_taken": "Use the card you took first",
           "r_left": "Cards left",
           "r_pay": "Points",
           "cloth": "Cloth",
           "texas": "Texas Hold'em",
           "t_pot": "Pot: %s",
           "t_fold": "Fold",
           "t_call": "Call %s",
           "t_check": "Check",
           "t_bet": "Bet",
           "t_raise": "Raise",
           "t_folds": "The dealer folds",
           "t_checks": "The dealer checks",
           "t_calls": "The dealer calls",
           "t_raises": "The dealer raises",
           "t_won_fold": "Hand won",
           "t_alta": "High card",
           "t_coppia": "Pair",
           "t_doppia": "Two pair",
           "t_tris": "Three of a kind",
           "t_scala": "Straight",
           "t_colore": "Flush",
           "t_full": "Full house",
           "t_poker": "Four of a kind",
           "t_scala_colore": "Straight flush",
           "family": "Card design",
           "col_a": "First deck",
           "col_b": "Second deck",
           "games": "Games",
           "r_open": "To open",
           "r_sel": "Selected",
           "r_down": "Melded",
           "r_hand": "In hand",
           "r_draw_first": "Draw a card first",
           "r_choose": "Your turn",
           "r_no_back": "You can't take that back",
           "r_nothing": "Nothing to do here",
           "r_cards": "Cards",
           "r_messa": "Stake",
           "r_in_mano": "Closed in one turn",
           "r_help": "arrows  move     click / ENTER  draw / discard / meld     %s  pick for melding     %s  move or lay off     %s  sort by best hand",
           "limite": "Match to",
           "r_ncards": "Cards",
           "r_back": "%d points short: cards back in hand",
           "help_game": "click / ENTER  play      ESC  back"},
    "it": {"cards": "Carte", "blackjack": "Blackjack",
           "sette": "Sette e Mezzo", "scopa": "Scopa",
           "briscola": "Briscola", "ramino": "Ramino", "deck": "Mazzo",
           "back": "Indietro", "soon": "presto",
           "need_fr": "Servono le carte francesi: presto",
           "card": "Carta", "stand": "Sto", "leave": "Esci",
           "again": "Rigioca", "menu": "Menu", "next": "Prossima mano",
           "cont": "Continua", "hand_won": "%s vince la mano",
           "bet": "Fai la tua puntata", "free": "Gioco libero",
           "bet_match": "Punta sulla partita", "bet_won": "Puntata",
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
           "tie_again": "Pari: si rigioca la mano",
           "win0": "Hai vinto", "lose0": "Hai perso",
           "choose_take": "Scegli cosa prendere",
           "r_draw": "Pesca dal mazzo",
           "r_take": "Prendi lo scarto",
           "r_meld": "Cala",
           "r_attach": "Attacca",
           "r_discard": "Scarta",
           "r_sort": "Ordina",
           "r_bad": "Combinazione non valida",
           "r_keep": "Tieni una carta da scartare",
           "r_40": "La prima calata deve fare 50", "r_open_first": "Devi aprire con 50 punti prima di attaccare", "r_one": "Scegli una carta da scartare",
           "r_use_taken": "Prima usa la carta che hai preso",
           "r_left": "Carte in mano",
           "r_pay": "Punti",
           "cloth": "Panno",
           "texas": "Texas Hold'em",
           "t_pot": "Piatto: %s",
           "t_fold": "Passo",
           "t_call": "Vedo %s",
           "t_check": "Check",
           "t_bet": "Punto",
           "t_raise": "Rilancio",
           "t_folds": "Il banco passa",
           "t_checks": "Il banco sta",
           "t_calls": "Il banco vede",
           "t_raises": "Il banco rilancia",
           "t_won_fold": "Mano vinta",
           "t_alta": "Carta alta",
           "t_coppia": "Coppia",
           "t_doppia": "Doppia coppia",
           "t_tris": "Tris",
           "t_scala": "Scala",
           "t_colore": "Colore",
           "t_full": "Full",
           "t_poker": "Poker",
           "t_scala_colore": "Scala reale",
           "family": "Disegno",
           "col_a": "Primo mazzo",
           "col_b": "Secondo mazzo",
           "games": "Giochi",
           "r_open": "Per aprire",
           "r_sel": "Scelte",
           "r_down": "Calate",
           "r_hand": "In mano",
           "r_draw_first": "Prima pesca una carta",
           "r_choose": "Tocca a te",
           "r_no_back": "Quella non la puoi riprendere",
           "r_nothing": "Qui non c'e' niente da fare",
           "r_cards": "Carte",
           "r_messa": "Messa",
           "r_in_mano": "Chiusura di mano",
           "r_help": "frecce  muovi     clic / INVIO  pesca / scarta / cala     %s  scegli per calare     %s  sposta o attacca     %s  ordina i giochi migliori",
           "limite": "Punti partita",
           "r_ncards": "Carte",
           "r_back": "Ti mancano %d punti: carte di nuovo in mano",
           "help_game": "clic / INVIO  gioca      ESC  indietro"},
    "fr": {"cards": "Cartes", "blackjack": "Blackjack",
           "sette": "Sette e Mezzo", "scopa": "Scopa",
           "briscola": "Briscola", "ramino": "Rami", "deck": "Jeu",
           "back": "Retour", "soon": "bientot",
           "need_fr": "Cartes francaises requises : bientot",
           "card": "Carte", "stand": "Reste", "leave": "Quitter",
           "again": "Rejouer", "menu": "Menu", "next": "Main suivante",
           "cont": "Continuer", "hand_won": "%s gagne la main",
           "bet": "Placez votre mise", "free": "Jeu libre",
           "bet_match": "Misez sur la partie", "bet_won": "Mise",
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
           "tie_again": "Egalite : on rejoue la main",
           "win0": "Vous gagnez", "lose0": "Vous perdez",
           "choose_take": "Choisissez votre prise",
           "r_draw": "Piocher",
           "r_take": "Prendre la defausse",
           "r_meld": "Poser",
           "r_attach": "Ajouter",
           "r_discard": "Defausser",
           "r_sort": "Trier",
           "r_bad": "Combinaison non valide",
           "r_keep": "Gardez une carte a defausser",
           "r_40": "La premiere pose doit valoir 50", "r_open_first": "Ouvrez avec 50 points avant d'ajouter", "r_one": "Choisissez une carte a defausser",
           "r_use_taken": "Utilisez d'abord la carte prise",
           "r_left": "Cartes en main",
           "r_pay": "Points",
           "cloth": "Tapis",
           "texas": "Texas Hold'em",
           "t_pot": "Pot : %s",
           "t_fold": "Se coucher",
           "t_call": "Suivre %s",
           "t_check": "Parole",
           "t_bet": "Miser",
           "t_raise": "Relancer",
           "t_folds": "La banque se couche",
           "t_checks": "La banque parle",
           "t_calls": "La banque suit",
           "t_raises": "La banque relance",
           "t_won_fold": "Main gagnee",
           "t_alta": "Carte haute",
           "t_coppia": "Paire",
           "t_doppia": "Double paire",
           "t_tris": "Brelan",
           "t_scala": "Quinte",
           "t_colore": "Couleur",
           "t_full": "Full",
           "t_poker": "Carre",
           "t_scala_colore": "Quinte flush",
           "family": "Dessin",
           "col_a": "Premier jeu",
           "col_b": "Second jeu",
           "games": "Jeux",
           "r_open": "Pour ouvrir",
           "r_sel": "Choisies",
           "r_down": "Posees",
           "r_hand": "En main",
           "r_draw_first": "Piochez d'abord",
           "r_choose": "A vous",
           "r_no_back": "Impossible de la reprendre",
           "r_nothing": "Rien a faire ici",
           "r_cards": "Cartes",
           "r_messa": "Mise",
           "r_in_mano": "Fermeture en une fois",
           "r_help": "fleches  deplacer     clic / ENTREE  piocher / defausser / poser     %s  choisir     %s  deplacer ou ajouter     %s  trier les meilleurs jeux",
           "limite": "Partie a",
           "r_ncards": "Cartes",
           "r_back": "Il manque %d points : cartes reprises en main",
           "help_game": "clic / ENTREE  jouer      ECHAP  retour"},
    "es": {"cards": "Cartas", "blackjack": "Blackjack",
           "sette": "Sette e Mezzo", "scopa": "Escoba",
           "briscola": "Brisca", "ramino": "Rummy", "deck": "Baraja",
           "back": "Atras", "soon": "pronto",
           "need_fr": "Faltan las cartas francesas: pronto",
           "card": "Carta", "stand": "Me planto", "leave": "Salir",
           "again": "Otra vez", "menu": "Menu", "next": "Otra mano",
           "cont": "Continuar", "hand_won": "%s gana la mano",
           "bet": "Haz tu apuesta", "free": "Juego libre",
           "bet_match": "Apuesta a la partida", "bet_won": "Apuesta",
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
           "tie_again": "Empate: se repite la mano",
           "win0": "Ganas", "lose0": "Pierdes",
           "choose_take": "Elige que te llevas",
           "r_draw": "Robar del mazo",
           "r_take": "Tomar el descarte",
           "r_meld": "Bajar",
           "r_attach": "Anadir",
           "r_discard": "Descartar",
           "r_sort": "Ordenar",
           "r_bad": "Combinacion no valida",
           "r_keep": "Guarda una carta para descartar",
           "r_40": "La primera bajada debe valer 50", "r_open_first": "Abre con 50 puntos antes de anadir", "r_one": "Elige una carta para descartar",
           "r_use_taken": "Primero usa la carta que tomaste",
           "r_left": "Cartas en mano",
           "r_pay": "Puntos",
           "cloth": "Tapete",
           "texas": "Texas Hold'em",
           "t_pot": "Bote: %s",
           "t_fold": "Retirarse",
           "t_call": "Igualar %s",
           "t_check": "Pasar",
           "t_bet": "Apostar",
           "t_raise": "Subir",
           "t_folds": "La banca se retira",
           "t_checks": "La banca pasa",
           "t_calls": "La banca iguala",
           "t_raises": "La banca sube",
           "t_won_fold": "Mano ganada",
           "t_alta": "Carta alta",
           "t_coppia": "Pareja",
           "t_doppia": "Doble pareja",
           "t_tris": "Trio",
           "t_scala": "Escalera",
           "t_colore": "Color",
           "t_full": "Full",
           "t_poker": "Poker",
           "t_scala_colore": "Escalera de color",
           "family": "Diseno",
           "col_a": "Primera baraja",
           "col_b": "Segunda baraja",
           "games": "Juegos",
           "r_open": "Para abrir",
           "r_sel": "Elegidas",
           "r_down": "Bajadas",
           "r_hand": "En mano",
           "r_draw_first": "Primero roba una carta",
           "r_choose": "Tu turno",
           "r_no_back": "Esa no la puedes recuperar",
           "r_nothing": "Aqui no hay nada que hacer",
           "r_cards": "Cartas",
           "r_messa": "Puesta",
           "r_in_mano": "Cierre de mano",
           "r_help": "flechas  mover     clic / INTRO  robar / descartar / bajar     %s  elegir     %s  mover o anadir     %s  ordena las mejores jugadas",
           "limite": "Partida a",
           "r_ncards": "Cartas",
           "r_back": "Te faltan %d puntos: cartas de vuelta a la mano",
           "help_game": "clic / INTRO  jugar      ESC  atras"},
}


def aiuto_ramino():
    """La riga d'aiuto del ramino con mouse e tastiera: i nomi veri dei
    tasti, presi dalle impostazioni come fa il biliardo."""
    return T("r_help") % (B.nome_tasto(B.tasto("cambia")),
                          B.nome_tasto(B.tasto("gesso")),
                          B.nome_tasto(B.tasto("eff_via")))


# la riga dei comandi col joystick: le scritte vanno anche nei testi del
# biliardo, perche' e' lui che disegna la riga con le icone
RIGA_PAD_CARTE = ((("croce",), "cg_move"), (("a",), "cg_play"),
                  (("b",), "pa_back"))
# nel ramino i tasti sono di piu': ognuno con la sua icona
RIGA_PAD_RAMINO = ((("croce",), "cg_move"), (("a",), "rm_a"),
                   (("y",), "rm_y"), (("x",), "rm_x"), (("rb",), "rm_rb"),
                   (("b",), "pa_back"))
for _l, _d in (
        ("en", {"cg_move": "choose", "cg_play": "play",
                "rm_a": "draw / discard / meld", "rm_y": "pick for melding",
                "rm_x": "move or lay off", "rm_rb": "sort"}),
        ("it", {"cg_move": "scegli", "cg_play": "gioca",
                "rm_a": "pesca / scarta / cala", "rm_y": "scegli per calare",
                "rm_x": "sposta o attacca", "rm_rb": "ordina"}),
        ("fr", {"cg_move": "choisir", "cg_play": "jouer",
                "rm_a": "piocher / defausser / poser", "rm_y": "choisir",
                "rm_x": "deplacer ou ajouter", "rm_rb": "trier"}),
        ("es", {"cg_move": "elegir", "cg_play": "jugar",
                "rm_a": "robar / descartar / bajar", "rm_y": "elegir",
                "rm_x": "mover o anadir", "rm_rb": "ordenar"})):
    B.TESTI.setdefault(_l, {}).update(_d)


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


# gli aloni: verde dove sta il cursore (il tasto A), giallo per le carte
# scelte per calare (Y), azzurro per la carta che stai spostando (X)
VERDE = (104, 226, 132)
ROSSO = (240, 96, 96)       # dove non si puo' fare niente
GIALLO = (255, 206, 72)
AZZURRO = (96, 168, 255)
VIOLA = (190, 126, 255)   # la carta che ha chiuso la mano    # la carta che stai spostando in mano (tasto X)


class Esci(Exception):
    pass


# --------------------------------------------------------------- tavolo
class Tavolo:
    """Il tavolo comune a tutti i giochi."""

    def __init__(self, sc, clock, nomi, gioco=""):
        self.sc, self.clock = sc, clock
        self.gioco = gioco      # la chiave del gioco, per il nome in alto
        # le carte in gioco un terzo piu' grandi del mazzo, tranne nel
        # ramino, dove sul tavolo ce ne sono tante
        self.g = 1.0 if gioco == "ramino" else 4.0 / 3.0
        self.g_mazzo = 4.0 / 3.0    # il mazzo e la scatola, in ogni gioco
        # nel ramino si gioca con due mazzi: le scatole sono due (o una
        # sola, se la confezione doppia c'e' gia')
        self.scatole = list(mazzi_ramino()[1] or []) if gioco == "ramino" \
            else []
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
        self.evidenzia = []     # le carte della presa proposta
        self.cursore = None     # ramino: la carta dove sta il cursore
        self.selezionate = []   # ramino: le carte scelte
        self.viola = []         # le carte da mostrare a fine mano
        self.in_mano = None     # ramino: la carta presa per spostarla
        self.mira = None        # ramino: il cursore sul mazzo o sullo scarto
        self.mira_col = VERDE   # verde se si puo' pescare, rosso se no
        self.pannello = []      # ramino: i punti, nella fascia a destra
        self.aiuto = None       # la riga dei comandi, se il gioco ne vuole una
        self.aiuto_pad = None   # la stessa riga col joystick, con le icone
        self.sel_carta = 0
        self.eventi = []
        self.dt = 0.0
        self.P = {}
        legno_sx = int(B.TAV_POS[0] + C.LEGNO_FUORI.left * B.SCALA)
        self.x_lato = max(B.s(30), legno_sx // 2)
        self.disponi()

    # ---- posti
    def disponi(self):
        """A sinistra del tavolo, dall'alto: la scatola, il mazzo e sotto
        il numero delle carte. La fascia a destra e' per le scelte."""
        sb = C.immagine_mazzo("scatola", self.scatole[0]
                              if self.scatole else None)
        legno_sx = int(B.TAV_POS[0] + C.LEGNO_FUORI.left * B.SCALA)
        _, h = C.misura_carta()
        h = int(h * self.g_mazzo)
        alto = 0
        if sb is not None:
            largo = legno_sx - B.s(20)
            alto = max(B.s(30), min(B.s(146), int(
                largo * sb.get_height() / float(sb.get_width()))))
        spazio = B.s(26)            # fra scatola e mazzo (la pila sale)
        conta = B.FONTS["small"].get_height() + B.s(16)
        tutto = alto + spazio + h + conta
        y0 = self.z.centery - tutto // 2
        self.P["scatola"] = (self.x_lato, y0 + alto // 2)
        self.P["mazzo"] = (self.x_lato, y0 + alto + spazio + h // 2)
        self.P["alto"] = alto

    def posto_mazzo(self, k):
        return (self.P["mazzo"][0] + k * 0.2, self.P["mazzo"][1] - k * 0.35)

    def riga(self, n, y, passo=None):
        """n carte in fila, centrate, all'altezza y."""
        w, _ = C.misura_carta()
        passo = (passo or w * 1.08) * self.g
        return [(self.z.centerx + (i - (n - 1) / 2.0) * passo, y)
                for i in range(n)]

    def ventaglio(self, n, sopra=False):
        pos = C.posti(n, self.g)[1 if sopra else 0]
        return pos

    # ---- carte
    def nuovo_mazzo(self, codici):
        self.carte, self.mazzo = [], []
        for k, cod in enumerate(codici):
            c = C.Carta(self.posto_mazzo(k), codice=cod)
            c.g = c.g_da = c.g_a = self.g_mazzo
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
               suono=None, grande=None):
        c.su = 0.0
        c.vai(dove, ang, scoperta=scoperta, ritardo=ritardo, suono=suono,
              grande=self.g if grande is None else grande)
        self.in_cima(c)

    def fine_mano(self, testo, tabella, opzioni, viola=None):
        """Fine mano in due passi, per non avere carte e punteggi uno
        sopra l'altro: prima chi ha vinto la mano col tavolo ancora in
        vista e "Continua", poi le carte tornano nel mazzo e sul panno
        libero si vedono i punti."""
        self.viola = list(viola or [])
        self.righe = [testo] if testo else []
        yield from self.chiedi([T("cont")])
        self.viola = []
        self.righe = []
        self.raccogli_tutto()
        yield from self.fermi()
        self.tabella = tabella
        i = yield from self.chiedi(opzioni)
        self.tabella = None
        return i

    def raccogli_tutto(self):
        """Tutte le carte tornano nel mazzo, coperte."""
        C.suona("cattura")
        random.shuffle(self.carte)
        self.mazzo = list(self.carte)
        for k, c in enumerate(self.mazzo):
            c.su = 0.0
            c.vai(self.posto_mazzo(k), 0.0, scoperta=False,
                  grande=self.g_mazzo,
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

    def scegli_presa(self, prese):
        """Quando si puo' prendere in piu' modi: le carte della presa
        proposta si illuminano, frecce o rotella passano alla prossima,
        INVIO o clic la confermano. Col mouse basta passare sopra una
        carta per proporre la presa che la contiene."""
        yield from self.fermi()
        k = 0
        vecchie = self.righe
        self.righe = [T("choose_take")]
        scelta = None
        w0, h0 = C.misura_carta()
        while scelta is None:
            self.evidenzia = prese[k]
            yield
            m = B.mouse_gioco()
            sotto = None
            for c in self.carte:
                if any(c in p for p in prese):
                    w, h = w0 * c.g, h0 * c.g
                    if pygame.Rect(c.pos.x - w / 2, c.pos.y - h / 2 - c.su,
                                   w, h).collidepoint(m):
                        sotto = c
            if sotto is not None and B.MOUSE_VIVO[0] and \
                    sotto not in prese[k]:
                k = next(i for i, p in enumerate(prese) if sotto in p)
            for ev in self.eventi:
                if ev.type == pygame.KEYDOWN:
                    if ev.key in (pygame.K_LEFT, pygame.K_UP, pygame.K_a,
                                  pygame.K_w):
                        k = (k - 1) % len(prese)
                        B.suona_fx("menu_tic", 0.6)
                    elif ev.key in (pygame.K_RIGHT, pygame.K_DOWN,
                                    pygame.K_d, pygame.K_s):
                        k = (k + 1) % len(prese)
                        B.suona_fx("menu_tic", 0.6)
                    elif ev.key in (pygame.K_RETURN, pygame.K_KP_ENTER,
                                    pygame.K_SPACE):
                        scelta = prese[k]
                if ev.type == pygame.MOUSEWHEEL:
                    k = (k - ev.y) % len(prese)
                if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1 \
                        and sotto is not None:
                    scelta = prese[k]
        self.evidenzia = []
        self.righe = vecchie
        return scelta

    def _carta_sotto_mouse(self):
        m = B.mouse_gioco()
        w0, h0 = C.misura_carta()
        for c in reversed(self.scegli):
            w, h = w0 * c.g, h0 * c.g
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
        # la carta scelta si alza, e un po' anche quelle della presa
        sotto = self.scegli[self.sel_carta] if self.scegli else None
        for c in self.carte:
            voglio = B.s(24) if c is self.in_mano else \
                B.s(18) if c is sotto else \
                B.s(12) if c in self.evidenzia else \
                B.s(20) if c in self.selezionate else \
                B.s(8) if c is self.cursore else 0.0
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
        self._disegna_pannello()
        self._conta_mazzo()
        if self.msg[1] > 0:
            self.msg[1] -= self.dt
        self._messaggio_sotto()
        if self.tabella:
            self._disegna_tabella()
        col_pad = B.modo_comandi() == "pad" and B.ICONE_TASTI_OK()
        if col_pad:
            t = B.riga_pad(small, self.aiuto_pad or RIGA_PAD_CARTE)
        elif self.aiuto:
            testo = self.aiuto() if callable(self.aiuto) else self.aiuto
            t = small.render(testo, True, (150, 156, 168))
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
        h = h * self.g_mazzo
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
        o.fill((255, 255, 255, 110), special_flags=pygame.BLEND_RGBA_MULT)
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

    def _disegna_pannello(self):
        """I punti nella fascia a destra, dove stanno le scelte."""
        if not self.pannello or self.bottoni:
            return
        legno_dx = int(B.TAV_POS[0] + C.LEGNO_FUORI.right * B.SCALA)
        x0 = legno_dx + B.s(14)
        f = font_carte(16)
        passo = f.get_height() + B.s(10)
        y = self.z.centery - (len(self.pannello) - 1) * passo // 2
        for et, val in self.pannello:
            t = f.render(et, True, B.ORO_SOTTO)
            self.sc.blit(t, (x0, y - t.get_height() // 2))
            v = f.render(str(val), True, (255, 255, 255))
            self.sc.blit(v, v.get_rect(midright=(B.WIN_W - B.s(14), y)))
            y += passo

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
        C.disegna_scatola(sup, self.P["scatola"], self.P["alto"], k,
                          self.scatole)
        if self.mira in ("mazzo", "scarto"):
            w, h = C.misura_carta()
            g = self.g_mazzo if self.mira == "mazzo" else self.g
            centro = self.P.get("mazzo" if self.mira == "mazzo" else "scarti")
            if centro:
                al = C.alone(int(w * g * k), int(h * g * k),
                             max(4, int(B.s(12) * k)), self.mira_col,
                             max(3, int(B.s(6) * g * k)))
                sup.blit(al, al.get_rect(center=(int(centro[0] * k),
                                                 int(centro[1] * k))))
        scelta = self.scegli[self.sel_carta] if self.scegli else None
        for c in self.carte:
            if c in self.viola:
                col = VIOLA                 # la carta che ha chiuso
            elif c is self.in_mano:
                col = AZZURRO               # la carta che stai spostando
            elif c in self.selezionate:
                col = GIALLO                # scelte in mano per calare
            elif c is scelta or c is self.cursore or c in self.evidenzia:
                col = VERDE                 # dove sta il cursore
            else:
                col = None
            c.disegna(sup, k, col)

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
    y_tu = tv.z.bottom - B.s(C.CARTA_H) * 0.62 * tv.g
    y_banco = tv.z.top + B.s(C.CARTA_H) * 0.62 * tv.g
    ripeti = None           # dopo un pari si rigioca con la stessa puntata
    while True:
        tv.nuovo_mazzo(C.mazzo_codici())
        random.shuffle(tv.mazzo)
        for k, c in enumerate(tv.mazzo):
            c.vai(tv.posto_mazzo(k), 0.0)
        tv.punti = ["", ""]
        if ripeti is None:
            tv.righe = [T("bet")]
            opz = [B.dollari(p) for p in puntate if p <= B.soldi()]
            if not opz:
                opz = [T("free")]
            i = yield from tv.chiedi(opz + [T("leave")])
            if i == len(opz):
                return "menu"
            posta = puntate[i] if opz[0] != T("free") else 0
        else:
            posta, ripeti = ripeti, None
        tv.righe = [T("bet_is") % B.dollari(posta) if posta else T("free")]
        mia, banco = [], []

        def rifai(mano, y, scoperte=True):
            # il suono delle carte servite e' gia' una sequenza: una volta
            C.suona("servi")
            pos = tv.riga(len(mano), y)
            for c, p in zip(mano, pos):
                tv.sposta(c, p, 0.0, scoperta=scoperte if c is not banco[0]
                          or banco_aperto[0] else False)
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
        esito = -1              # -1 perso, 0 pari, 1 vinto
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
                vinto, esito = posta, 1
            elif mio > bt:
                vinto, esito = posta, 1
            elif mio == bt:
                vinto, esito = 0, 0
            else:
                vinto = -posta
            if vinto > 0 and reale(codici_miei) and \
                    not reale([c.codice for c in banco]):
                tv.messaggio(T("reale"))
                vinto = posta * 2
        yield from tv.attendi(1.2)
        if esito == 0:
            # pari: nessuno vince, si rigioca subito la mano
            tv.righe = [T("tie_again")]
            C.suona("giocata")
            yield from tv.attendi(1.6)
            tv.righe = []
            tv.raccogli_tutto()
            yield from tv.fermi()
            ripeti = posta
            continue
        if vinto:
            B.soldi(vinto)
            B.salva_config()
        C.suona("levelup" if esito > 0 else "gameover")
        if not posta:
            tv.righe = [T("win0") if esito > 0 else T("lose0")]
        else:
            tv.righe = [T("you_win") % B.dollari(vinto) if esito > 0 else
                        T("you_lose") % B.dollari(-vinto)]
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


PUNTATE_PARTITA = (10, 25, 50, 100, 250, 500, 1000)


def scegli_posta(tv):
    """La puntata sulla partita, nei giochi a punti: si sceglie prima di
    cominciare, da 10 a 1000 dollari (quelli che hai), e chi vince il
    match si prende il doppio. Torna None se preferisci uscire."""
    tv.righe = [T("bet_match")]
    opz = [B.dollari(p) for p in PUNTATE_PARTITA if p <= B.soldi()]
    libero = not opz
    if libero:
        opz = [T("free")]
    i = yield from tv.chiedi(opz + [T("leave")])
    tv.righe = []
    if i == len(opz):
        return None
    posta = 0 if libero else PUNTATE_PARTITA[i]
    if posta:
        B.soldi(-posta)
        B.salva_config()
    return posta


def paga_posta(tv, posta, vince, righe):
    """Fine partita: chi vince incassa il doppio, a pari si riprende la
    sua. La riga va anche nel riepilogo."""
    if not posta:
        return
    if vince is None:
        B.soldi(posta)
        vinto = [posta, posta]
    else:
        if vince == 0:
            B.soldi(posta * 2)
        vinto = [posta * 2 if vince == 0 else 0,
                 posta * 2 if vince == 1 else 0]
    B.salva_config()
    righe.append((T("bet_won"), B.dollari(vinto[0]), B.dollari(vinto[1])))


def partita_scopa(tv):
    totali = [0, 0]
    chi_inizia = 0
    y_tavolo = tv.z.centery
    posta = [None]
    while True:
        if posta[0] is None:
            p = yield from scegli_posta(tv)
            if p is None:
                return "menu"
            posta[0] = p
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
            h *= tv.g
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
            C.suona("servi")
            for chi in (0, 1):
                pos = tv.ventaglio(len(mani[chi]), sopra=chi == 1)
                for c, (p, a) in zip(mani[chi], pos):
                    tv.sposta(c, p, a, scoperta=chi == 0, ritardo=rit)
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
                presa = opz[0] if opz else []
                if len(opz) > 1:
                    # piu' prese possibili: sceglie il giocatore, la carta
                    # giocata resta alzata mentre decide
                    per_carte = [[next(x for x in tavolo if x.codice == cd)
                                  for cd in pr] for pr in opz]
                    per_carte.sort(key=lambda pr: -valuta_presa(
                        c.codice, [x.codice for x in pr], codici_tav, ultima))
                    tv.scegli = [c]
                    tv.sel_carta = 0
                    scelte = yield from tv.scegli_presa(per_carte)
                    tv.scegli = []
                    presa = [x.codice for x in scelte]
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
        tab = {"titolo": T("hand_over"), "righe": righe,
               "tot": list(totali)}
        fine = max(totali) >= 11 and totali[0] != totali[1]
        vince = 0 if pt[0] > pt[1] else 1
        if fine:
            vince = 0 if totali[0] > totali[1] else 1
            tab["fondo"] = T("win_match") % tv.nomi[vince]
            C.suona("levelup" if vince == 0 else "gameover")
            paga_posta(tv, posta[0], vince, righe)
            posta[0] = None
            opz = [T("again"), T("menu")]
        else:
            opz = [T("next")]
        i = yield from tv.fine_mano(T("hand_won") % tv.nomi[vince], tab, opz)
        if fine:
            if i == 1:
                return "menu"
            totali = [0, 0]
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
        posta = yield from scegli_posta(tv)
        if posta is None:
            return "menu"
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
            if suono:
                C.suona(suono)          # una volta sola, non a ogni carta
            pos = tv.ventaglio(len(mani[chi]), sopra=chi == 1)
            for c, (p, a) in zip(mani[chi], pos):
                tv.sposta(c, p, a, scoperta=chi == 0, ritardo=rit)
                rit += 0.06 if suono else 0.0

        for _ in range(3):
            for chi in (chi_inizia, 1 - chi_inizia):
                mani[chi].append(tv.pesca())
        rifai_mano(0, 0.0, "servi")
        rifai_mano(1, 0.2)
        # la briscola: scoperta, di traverso sotto il mazzo
        br = tv.pesca()
        tv.carte.remove(br)
        tv.carte.insert(0, br)
        tv.mazzo.insert(0, br)
        w, _ = C.misura_carta()
        br.vai((tv.P["mazzo"][0] + w * tv.g_mazzo * 0.55,
                tv.P["mazzo"][1]), 90.0,
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
                rifai_mano(1, 0.1)
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
        righe = [(T("p_cards"), len(prese[0]), len(prese[1]))]
        paga_posta(tv, posta, None if a == b else (0 if a > b else 1), righe)
        tab = {"titolo": T("hand_over"), "tot": [a, b],
               "righe": righe, "fondo": esito}
        i = yield from tv.fine_mano(esito, tab, [T("again"), T("menu")])
        if i == 1:
            return "menu"
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
    y_tu = tv.z.bottom - B.s(C.CARTA_H) * 0.62 * tv.g
    y_banco = tv.z.top + B.s(C.CARTA_H) * 0.62 * tv.g
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
            C.suona("servi")
            pos = tv.riga(len(mano), y, passo)
            for c, p in zip(mano, pos):
                sc_ = not (e_banco and c is banco[1] and coperta[0]) \
                    if len(banco) > 1 else True
                tv.sposta(c, p, 0.0, scoperta=sc_)

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
            c.vai(tv.posto_mazzo(k), 0.0, scoperta=False,
                  grande=tv.g_mazzo)
        yield from tv.fermi()
        if i == 1:
            return "menu"


REGOLE_CARTE = {
    "en": {
        "texas": """Heads-up against the dealer with a French deck, fixed limit.
- Both post the blinds, then you get two cards each and five come face up in the middle: three (flop), one (turn), one (river).
- After each stage there is a round of betting: check, bet, call, raise or fold. Up to three raises per round.
- The bet is one big blind before the flop and on the flop, double on the turn and the river.
- The best five cards out of seven win the pot. If someone folds, the other takes it.
- Order: high card, pair, two pair, three of a kind, straight, flush, full house, four of a kind, straight flush.""",
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
- The banker then draws. On a tie the hand is replayed with the same bet.
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
        "ramino": """Heads-up against the computer with two French decks and four jokers, 13 cards each.
- Draw from the deck or take the top of the discard pile, then discard one card to end your turn.
- Sets are three or four of a kind in different suits, runs are three or more cards of the same suit; the Ace goes below the 2 or above the King.
- Jokers stand for any card, but every combination needs at least two real cards.
- If you hold the real card a joker on the table stands for, you can put it in its place and take the joker into your hand.
- Your first meld must be worth at least 50 points, and cards you lay off on melds already on the table count towards it.
- If you do not reach 50 before discarding, everything you put down this turn comes back to your hand, and a card taken from the discard pile goes back too.
- Card values: figures 10, Ace 11 (1 when it is below the 2), joker 25 in hand or the value of the card it replaces.
- The one who runs out of cards closes. The other pays the cards left in hand, rounded (up to 4 down, 5 to 9 up), plus a 50 point stake.
- Closing in one turn, opening and going out together, suspends the stake: nothing is paid, but next hand the stake goes up by 50.
- The first to reach the match points loses.""",
    },
    "it": {
        "texas": """Testa a testa contro il banco con le carte francesi, a puntate fisse.
- Si mettono i bui, poi due carte a testa e cinque scoperte in mezzo: tre (flop), una (turn), una (river).
- Dopo ogni fase c'e' un giro di puntate: check, punto, vedo, rilancio o passo. Al massimo tre rilanci per giro.
- Si punta un buio grande prima del flop e sul flop, il doppio su turn e river.
- Vince il piatto la migliore combinazione di cinque carte su sette. Se uno passa, il piatto va all'altro.
- Ordine: carta alta, coppia, doppia coppia, tris, scala, colore, full, poker, scala reale.""",
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
- Poi gioca il banco. A parita' si rigioca la mano con la stessa puntata.
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
        "ramino": """Uno contro uno col computer, due mazzi francesi e quattro jolly, 13 carte a testa.
- Peschi dal mazzo o prendi lo scarto, poi scarti una carta e il turno finisce.
- I tris sono tre o quattro carte uguali di semi diversi, le scale tre o piu' carte dello stesso seme; l'asso va sotto il 2 o sopra il re.
- I jolly sostituiscono qualsiasi carta, ma in ogni combinazione servono almeno due carte vere.
- Se hai la carta vera che un jolly in tavola sta facendo, la metti al suo posto e il jolly va in mano a te.
- La prima calata deve valere almeno 50 punti, e ci contano anche le carte che attacchi alle combinazioni gia' in tavola, tue o del computer.
- Se prima di scartare non arrivi a 50, tutto quello che hai messo giu' in quel turno torna in mano, e anche la carta presa dallo scarto torna al suo posto.
- Valori: figure 10, asso 11 (1 quando sta sotto il 2), jolly 25 se resta in mano o il valore della carta che sostituisce.
- Chi resta senza carte chiude. L'altro paga le carte che ha in mano, arrotondate (fino a 4 si scende, da 5 a 9 si sale), piu' la messa di 50 punti.
- Chiudendo "di mano", cioe' aprendo e chiudendo nello stesso turno, la messa e' sospesa: non si paga, ma alla mano dopo la messa sale di 50.
- Perde chi arriva per primo ai punti della partita.""",
    },
    "fr": {
        "texas": """Tete-a-tete contre la banque avec un jeu francais, a limite fixe.
- On pose les blindes, puis deux cartes chacun et cinq au milieu : trois (flop), une (turn), une (river).
- Apres chaque etape il y a un tour d'encheres : parole, miser, suivre, relancer ou se coucher. Trois relances au maximum.
- On mise une grosse blinde avant le flop et au flop, le double au turn et a la river.
- La meilleure main de cinq cartes sur sept gagne le pot. Si quelqu'un se couche, l'autre le prend.
- Ordre : carte haute, paire, double paire, brelan, quinte, couleur, full, carre, quinte flush.""",
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
- Puis la banque joue. En cas d'egalite on rejoue la main avec la meme mise.
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
        "ramino": """Tete-a-tete contre l'ordinateur avec deux jeux francais et quatre jokers, 13 cartes chacun.
- Piochez ou prenez la defausse, puis defaussez une carte pour finir le tour.
- Les brelans sont trois ou quatre cartes de meme rang et de couleurs differentes, les suites au moins trois cartes de la meme couleur ; l'As se place sous le 2 ou au-dessus du Roi.
- Les jokers remplacent n'importe quelle carte, mais chaque combinaison demande au moins deux vraies cartes.
- Si vous avez la vraie carte qu'un joker represente, vous la mettez a sa place et prenez le joker en main.
- La premiere pose doit valoir au moins 50 points, et les cartes ajoutees aux combinaisons deja sur la table comptent aussi.
- Si vous n'atteignez pas 50 avant de defausser, tout ce que vous avez pose revient en main, et la carte prise a la defausse y retourne.
- Valeurs : figures 10, As 11 (1 sous le 2), joker 25 en main ou la valeur de la carte remplacee.
- Celui qui n'a plus de cartes ferme. L'autre paie les cartes en main, arrondies (jusqu'a 4 en bas, de 5 a 9 en haut), plus une mise de 50 points.
- Fermer en un seul tour suspend la mise : on ne paie rien, mais a la main suivante la mise monte de 50.
- Le premier a atteindre les points de la partie perd.""",
    },
    "es": {
        "texas": """Mano a mano contra la banca con baraja francesa, a limite fijo.
- Se ponen las ciegas, luego dos cartas cada uno y cinco en el centro: tres (flop), una (turn), una (river).
- Tras cada fase hay una ronda de apuestas: pasar, apostar, igualar, subir o retirarse. Maximo tres subidas por ronda.
- Se apuesta una ciega grande antes del flop y en el flop, el doble en el turn y el river.
- Gana el bote la mejor combinacion de cinco cartas entre siete. Si alguien se retira, el bote es del otro.
- Orden: carta alta, pareja, doble pareja, trio, escalera, color, full, poker, escalera de color.""",
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
- Luego juega la banca. En caso de empate se repite la mano con la misma apuesta.
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
        "ramino": """Mano a mano contra el ordenador con dos barajas francesas y cuatro comodines, 13 cartas cada uno.
- Roba del mazo o toma el descarte, luego descarta una carta y acaba el turno.
- Los trios son tres o cuatro cartas iguales de palos distintos, las escaleras tres o mas cartas del mismo palo; el As va bajo el 2 o sobre el Rey.
- Los comodines sustituyen cualquier carta, pero cada combinacion necesita al menos dos cartas reales.
- Si tienes la carta real que hace un comodin en la mesa, la pones en su lugar y te llevas el comodin a la mano.
- La primera bajada debe valer al menos 50 puntos, y cuentan tambien las cartas que anades a las combinaciones ya en la mesa.
- Si no llegas a 50 antes de descartar, todo lo que has bajado vuelve a tu mano, y la carta tomada del descarte vuelve a su sitio.
- Valores: figuras 10, As 11 (1 cuando va bajo el 2), comodin 25 en mano o el valor de la carta que sustituye.
- Quien se queda sin cartas cierra. El otro paga las cartas en mano, redondeadas (hasta 4 abajo, de 5 a 9 arriba), mas una puesta de 50 puntos.
- Cerrar en un solo turno suspende la puesta: no se paga nada, pero en la mano siguiente la puesta sube 50.
- Pierde el primero que llega a los puntos de la partida.""",
    },
}


def testo_regole_carte(chiave):
    d = REGOLE_CARTE.get(B.CFG.get("lingua", "en"), REGOLE_CARTE["en"])
    return d.get(chiave, REGOLE_CARTE["en"][chiave])


# ---------------------------------------------------------------- ramino
# Due mazzi francesi (uno col dorso blu e uno rosso) e 4 jolly. Due
# giocatori, 13 carte a testa. A ogni turno si pesca (dal mazzo o lo
# scarto), si calano combinazioni o si attaccano carte a quelle in tavola,
# e si scarta una carta. La prima calata deve valere almeno 40 punti.
# Chi resta senza carte chiude; l'altro paga i punti che ha in mano.
RANGHI = "A23456789TJQK"
APERTURA = 50           # i punti della prima calata (la scala 40 fa 40)
MESSA = 50              # il malus fisso di chi perde la mano


def rango(cod):
    return RANGHI.index(cod[0]) + 1         # A=1 ... K=13


def jolly(cod):
    return cod == "JK"


def valore_carta_ramino(r):
    """Il valore di un rango in una combinazione (14 = asso alto)."""
    if r in (1,):
        return 1
    if r == 14:
        return 11
    return 10 if r >= 11 else r


def valida_meld(codici):
    """Se le carte fanno una combinazione valida: (tipo, punti, ordine)
    con l'ordine in cui vanno messe in tavola; se no None. Tris o poker:
    stesso valore, semi diversi. Scala: stesso seme, di fila (l'asso va
    sotto il 2 o sopra il re). I jolly prendono il posto che serve; ci
    vogliono almeno due carte vere."""
    n = len(codici)
    if n < 3:
        return None
    jk = [c for c in codici if jolly(c)]
    nat = [c for c in codici if not jolly(c)]
    if len(nat) < 2:
        return None
    # tris / poker
    ranghi = set(rango(c) for c in nat)
    semi = [seme(c) for c in nat]
    if len(ranghi) == 1 and n <= 4 and len(set(semi)) == len(semi):
        r = ranghi.pop()
        v = 11 if r == 1 else valore_carta_ramino(r)
        ordine = sorted(nat, key=lambda c: "SHDC".index(seme(c))) + jk
        return ("tris", v * n, ordine)
    # scala
    if len(set(semi)) != 1:
        return None
    meglio = None
    for asso_alto in (False, True):
        rs = [14 if (rango(c) == 1 and asso_alto) else rango(c) for c in nat]
        if len(set(rs)) != len(rs):
            continue
        lo, hi = min(rs), max(rs)
        buchi = (hi - lo + 1) - len(rs)
        if buchi > len(jk):
            continue
        extra = len(jk) - buchi
        top = 14 if asso_alto else 13
        su = min(extra, top - hi)
        giu = extra - su
        if lo - giu < 1:
            continue
        lo2, hi2 = lo - giu, hi + su
        per_rango = dict(zip(rs, nat))
        resto = list(jk)
        ordine = []
        for r in range(lo2, hi2 + 1):
            ordine.append(per_rango[r] if r in per_rango else resto.pop())
        v = sum(valore_carta_ramino(r) for r in range(lo2, hi2 + 1))
        if meglio is None or v > meglio[1]:
            meglio = ("scala", v, ordine)
    return meglio


def _ranghi_scala(ordine):
    """I ranghi, posto per posto, di una scala gia' ordinata: serve a
    sapere che carta sta facendo un jolly. L'asso puo' stare sotto il 2 o
    sopra il re."""
    for alto in (False, True):
        base, buona = None, True
        for i, c in enumerate(ordine):
            if jolly(c):
                continue
            r = 14 if (rango(c) == 1 and alto) else rango(c)
            if base is None:
                base = r - i
            elif r - i != base:
                buona = False
                break
        if buona and base is not None:
            return [base + i for i in range(len(ordine))]
    return None


def valore_nel_meld(codici, i):
    """Quanto vale la carta che sta al posto i di una combinazione."""
    veri = [c for c in codici if not jolly(c)]
    if not veri:
        return 0
    ranghi = set(rango(c) for c in veri)
    if len(ranghi) == 1 and len(codici) <= 4:
        r = ranghi.pop()
        return 11 if r == 1 else valore_carta_ramino(r)
    rs = _ranghi_scala(codici)
    if rs is None or i >= len(rs):
        return 0
    return valore_carta_ramino(rs[i])


def jolly_da_prendere(codici, codice, mano=None):
    """Nel ramino il jolly si compra: chi ha la carta vera che il jolly
    sta facendo la mette al suo posto e si prende il jolly in mano.
    Torna il posto del jolly nella combinazione, o None.

    In una scala il jolly fa una carta sola e si sa quale. In un tris
    no: se al tris mancano due semi, il jolly puo' essere l'uno o
    l'altro, e allora si compra solo avendo in mano tutte le carte che
    mancano - se no il jolly lo si porterebbe via a caso."""
    if jolly(codice):
        return None
    # si guarda la combinazione com'e' messa in tavola: il jolly fa la
    # carta del posto che occupa li', non un'altra
    ordine = list(codici)
    posti = [i for i, c in enumerate(ordine) if jolly(c)]
    if not posti:
        return None
    veri = [c for c in ordine if not jolly(c)]
    if not veri or valida_meld(ordine) is None:
        return None
    if len(set(rango(c) for c in veri)) == 1 and len(ordine) <= 4:
        semi = set(seme(c) for c in veri)
        if rango(codice) != rango(veri[0]) or seme(codice) in semi:
            return None
        mancano = set("SHDC") - semi - {seme(codice)}
        if len(mancano) > len(posti) - 1:
            # resterebbe un seme scoperto: servono anche quelle carte
            if mano is None:
                return None
            ho = set(seme(c) for c in mano
                     if not jolly(c) and rango(c) == rango(codice))
            if not mancano <= ho:
                return None
        return posti[0]
    ranghi = _ranghi_scala(ordine)
    if ranghi is None:
        return None
    sm = seme(veri[0])
    for i in posti:
        r = ranghi[i]
        cod = ("A" if r == 14 else RANGHI[r - 1]) + sm
        if cod == codice:
            return i
    return None


def dividi_in_meld(codici):
    """Divide le carte scelte in combinazioni valide, tutte usate. Torna
    la lista delle combinazioni (con i loro punti) o None."""
    if not codici:
        return []
    primo, resto = codici[0], codici[1:]
    for n in range(2, len(resto) + 1):
        for gr in itertools.combinations(range(len(resto)), n):
            prova = [primo] + [resto[i] for i in gr]
            v = valida_meld(prova)
            if v is None:
                continue
            rimasti = [resto[i] for i in range(len(resto)) if i not in gr]
            dopo = dividi_in_meld(rimasti)
            if dopo is not None:
                return [v] + dopo
    return None


def punti_in_mano(codici):
    tot = 0
    for c in codici:
        if jolly(c):
            tot += 25
        else:
            r = rango(c)
            tot += 11 if r == 1 else 10 if r >= 10 else r
    return tot


def meld_cpu(mano):
    """Le combinazioni che la CPU puo' calare: prima le piu' ricche, senza
    usare due volte la stessa carta."""
    cand = []
    nat = [c for c in mano if not jolly(c)]
    jk = [c for c in mano if jolly(c)]
    # tris e poker
    per_rango = {}
    for c in nat:
        per_rango.setdefault(rango(c), {}).setdefault(seme(c), c)
    for r, d in per_rango.items():
        carte_r = list(d.values())
        for n in (4, 3):
            for gr in itertools.combinations(carte_r, n):
                cand.append(list(gr))
        if jk and len(carte_r) >= 2:
            for gr in itertools.combinations(carte_r, 2):
                cand.append(list(gr) + [jk[0]])
    # scale
    for sm in "SHDC":
        cs = [c for c in nat if seme(c) == sm]
        for asso_alto in (False, True):
            per_r = {}
            for c in cs:
                r = 14 if (rango(c) == 1 and asso_alto) else rango(c)
                per_r.setdefault(r, c)
            rs = sorted(per_r)
            for i in range(len(rs)):
                for j in range(i + 2, len(rs)):
                    fila = rs[i:j + 1]
                    if fila[-1] - fila[0] == len(fila) - 1:
                        cand.append([per_r[r] for r in fila])
                    elif jk and fila[-1] - fila[0] == len(fila):
                        cand.append([per_r[r] for r in fila] + [jk[0]])
            for i in range(len(rs) - 1):
                if jk and rs[i + 1] - rs[i] <= 2:
                    cand.append([per_r[rs[i]], per_r[rs[i + 1]], jk[0]])
    valide = []
    for gr in cand:
        v = valida_meld(gr)
        if v:
            valide.append((v[1], len(gr), gr))
    valide.sort(key=lambda x: (-x[0], -x[1]))
    # con due mazzi la stessa carta puo' esserci due volte: si contano
    resto = {}
    for c in mano:
        resto[c] = resto.get(c, 0) + 1
    scelte = []
    for v, n, gr in valide:
        serve = {}
        for c in gr:
            serve[c] = serve.get(c, 0) + 1
        if all(resto.get(c, 0) >= k for c, k in serve.items()):
            for c, k in serve.items():
                resto[c] -= k
            scelte.append(gr)
    return scelte


def arrotonda_ramino(p):
    """I punti delle carte in mano si arrotondano: fino a 4 si segna zero,
    da 5 a 9 si sale alla decina sopra."""
    resto = p % 10
    return p - resto if resto < 5 else p - resto + 10


def punti_partita():
    p = B.CFG.get("ramino_punti", 300)
    return p if p in (100, 200, 300, 500) else 300


def partita_ramino(tv):
    _, due = mazzi_ramino()
    blu, rosso = due if due else (None, None)
    w, h = C.misura_carta()
    y_mano = tv.z.bottom - h * 0.62
    scarti_pos = (tv.z.left + w * 0.9, tv.z.centery)
    totali = [0, 0]
    messa = [MESSA]
    chi_inizia = 0
    posta = [None]
    ordine_semi = [True]            # True: per seme, False: per valore

    def ordina(mano):
        if ordine_semi[0]:
            chiave = lambda c: (5, 0) if jolly(c.codice) else (
                "SHDC".index(seme(c.codice)), rango(c.codice))
        else:
            chiave = lambda c: (99, 0) if jolly(c.codice) else (
                rango(c.codice), "SHDC".index(seme(c.codice)))
        mano.sort(key=chiave)

    while True:
        if posta[0] is None:
            p = yield from scegli_posta(tv)
            if p is None:
                return "menu"
            posta[0] = p
        codici = mazzo_francese(2, 4)
        tv.nuovo_mazzo(codici)
        for k, c in enumerate(tv.carte):
            c.dorso = blu if k < 54 else rosso
        random.shuffle(tv.mazzo)
        tv.carte = list(tv.mazzo)
        for k, c in enumerate(tv.mazzo):
            c.vai(tv.posto_mazzo(k), 0.0)
        mani = [[], []]
        a_mano = [False]        # vero quando le carte le sposti tu
        aperto = [False, False]
        calate = []             # le calate di questo turno, non ancora valide
        punti_calate = [0]
        tavola = []                 # le combinazioni: liste di Carta
        scarti = []
        tv.punti = list(totali)

        def ordina_meglio():
            """RB: mette davanti i giochi migliori che ci sono in mano,
            uno di fila all'altro, e dietro le carte che avanzano."""
            gruppi = meld_cpu([c.codice for c in mani[0]])
            resto = list(mani[0])
            nuovo = []
            for g in gruppi:
                for cod in g:
                    x = next((c for c in resto if c.codice == cod), None)
                    if x is not None:
                        resto.remove(x)
                        nuovo.append(x)
            ordina(resto)
            mani[0][:] = nuovo + resto
            a_mano[0] = True
            rifai_mano(0)

        def rifai_mano(chi, suono=None, rit=0.0):
            """suono: si sente una volta sola, non a ogni carta."""
            if suono:
                C.suona(suono)
                suono = None
            if chi == 0 and not a_mano[0]:
                ordina(mani[0])
            pos = tv.ventaglio(len(mani[chi]), sopra=chi == 1) if chi == 1 \
                else [(p, 0.0) for p in tv.riga(len(mani[0]), y_mano,
                                                 min(w * 0.62,
                                                     (tv.z.w - w * 3) /
                                                     max(1, len(mani[0]))))]
            for c, (p, a) in zip(mani[chi], pos):
                tv.sposta(c, p, a, scoperta=chi == 0, suono=suono,
                          ritardo=rit)
                if suono:
                    rit += 0.03

        def rifai_tavola():
            """Le combinazioni in file sul panno, fra le due mani."""
            x0 = scarti_pos[0] + w * 1.1
            x1 = tv.z.right - w * 0.2
            passo = w * 0.42
            righe_y = [tv.z.centery - h * 0.6, tv.z.centery + h * 0.6,
                       tv.z.centery]
            x, r = x0, 0
            for meld in tavola:
                largo = w + passo * (len(meld) - 1)
                if x + largo > x1 and x > x0:
                    x, r = x0, r + 1
                y = righe_y[min(r, 2)]
                for i, c in enumerate(meld):
                    tv.sposta(c, (x + w / 2 + i * passo, y), 0.0,
                              scoperta=True)
                x += largo + w * 0.35

        def scarta(chi, c):
            mani[chi].remove(c)
            scarti.append(c)
            tv.sposta(c, (scarti_pos[0] + random.uniform(-2, 2),
                          scarti_pos[1] + random.uniform(-2, 2)),
                      random.uniform(-4, 4), scoperta=True, suono="giocata")
            rifai_mano(chi)

        def pesca_mazzo(chi):
            if not tv.mazzo:
                # il mazzo e' finito: gli scarti (tranne l'ultimo) si
                # rimescolano e tornano mazzo
                ultimo = scarti.pop()
                random.shuffle(scarti)
                for k, x in enumerate(scarti):
                    tv.mazzo.append(x)
                    x.vai(tv.posto_mazzo(k), 0.0, scoperta=False,
                          grande=tv.g_mazzo)
                del scarti[:]
                scarti.append(ultimo)
            c = tv.pesca()
            mani[chi].append(c)
            return c

        def cala(chi, gruppi):
            """Mette in tavola le combinazioni (liste di Carta)."""
            messi = []
            for gr in gruppi:
                v = valida_meld([c.codice for c in gr])
                per_cod = list(gr)
                ordinate = []
                for cod in v[2]:
                    x = next(c for c in per_cod if c.codice == cod)
                    per_cod.remove(x)
                    ordinate.append(x)
                for c in ordinate:
                    mani[chi].remove(c)
                tavola.append(ordinate)
                messi.append(ordinate)
                ultima[0] = ordinate[-1]
            C.suona("cattura")
            rifai_tavola()
            rifai_mano(chi)
            return messi

        def completa(meld):
            """Una combinazione chiusa: un poker coi quattro semi, o una
            scala che arriva da una parte all'altra. Non ci si puo'
            attaccare piu' niente."""
            v = valida_meld([x.codice for x in meld])
            if v is None:
                return False
            if v[0] == "tris":
                return len(meld) >= 4
            return len(meld) >= 13

        def pulisci_tavola():
            """Le combinazioni chiuse se ne vanno sotto gli scarti: il
            tavolo resta libero."""
            via = [m for m in tavola if completa(m)]
            for meld in via:
                tavola.remove(meld)
                for c in meld:
                    scarti.insert(0, c)
                    tv.sposta(c, (scarti_pos[0] + random.uniform(-2, 2),
                                  scarti_pos[1] + random.uniform(-2, 2)),
                              random.uniform(-4, 4), scoperta=False)
            if via:
                C.suona("cattura")
                rifai_tavola()
            return bool(via)

        def prendi_jolly(chi, c, quale=None):
            """La carta vera prende il posto del jolly e il jolly va in
            mano a chi l'ha messa: e' la regola del ramino."""
            quali = [quale] if quale is not None else range(len(tavola))
            for i in quali:
                meld = tavola[i]
                dove = jolly_da_prendere(
                    [x.codice for x in meld], c.codice,
                    [x.codice for x in mani[chi] if x is not c])
                if dove is None:
                    continue
                jk = meld[dove] if jolly(meld[dove].codice) else \
                    next(x for x in meld if jolly(x.codice))
                mani[chi].remove(c)
                meld[meld.index(jk)] = c
                mani[chi].append(jk)
                ultima[0] = c
                return "jolly"
            return False

        def attacca(chi, c, quale=None):
            if prendi_jolly(chi, c, quale):
                return True
            quali = [quale] if quale is not None else range(len(tavola))
            for i in quali:
                meld = tavola[i]
                v = valida_meld([x.codice for x in meld] + [c.codice])
                if v:
                    mani[chi].remove(c)
                    tutte = meld + [c]
                    ordinate = []
                    for cod in v[2]:
                        x = next(y for y in tutte if y.codice == cod
                                 and y not in ordinate)
                        ordinate.append(x)
                    tavola[i] = ordinate
                    ultima[0] = c
                    return True
            return False

        # si distribuisce
        for _ in range(13):
            for chi in (chi_inizia, 1 - chi_inizia):
                mani[chi].append(tv.pesca())
        rifai_mano(0, "servi")
        rifai_mano(1, None, 0.2)
        yield from tv.fermi()
        tv.P["scarti"] = scarti_pos
        tv.aiuto = aiuto_ramino
        tv.aiuto_pad = RIGA_PAD_RAMINO
        primo = tv.pesca()
        scarti.append(primo)
        tv.sposta(primo, scarti_pos, 0.0, scoperta=True, suono="giocata")
        yield from tv.fermi()

        turno = chi_inizia
        chiude = None
        ultima = [None]         # l'ultima carta messa in tavola
        in_mano = [False]       # chi chiude ha aperto e chiuso in un turno
        while chiude is None:
            tv.attivo = turno
            if turno == 0:
                prima = aperto[0]
                del calate[:]
                punti_calate[0] = 0
                esito = yield from turno_umano_ramino(
                    tv, mani, aperto, tavola, scarti, pesca_mazzo, scarta,
                    cala, attacca, rifai_mano, rifai_tavola, ordina,
                    ordine_semi, a_mano, calate, punti_calate,
                    ordina_meglio)
                if esito == "chiuso":
                    chiude = 0
                    in_mano[0] = not prima      # aperto e chiuso in un turno
            else:
                yield from tv.attendi(0.5)
                cod_mano = [c.codice for c in mani[1]]
                top = scarti[-1] if scarti else None
                prende_scarto = False
                if top is not None and aperto[1]:
                    prova = meld_cpu(cod_mano + [top.codice])
                    prende_scarto = any(top.codice in m for m in prova) or \
                        any(valida_meld([x.codice for x in m] + [top.codice])
                            for m in tavola)
                if prende_scarto:
                    scarti.pop()
                    mani[1].append(top)
                    preso = top
                else:
                    pesca_mazzo(1)
                    preso = None
                C.suona("cattura")
                rifai_mano(1)
                yield from tv.fermi()
                yield from tv.attendi(0.4)
                gruppi_cod = meld_cpu([c.codice for c in mani[1]])
                apre_ora = False
                if not aperto[1]:
                    if sum(valida_meld(g)[1] for g in gruppi_cod) >= APERTURA:
                        aperto[1] = True
                        apre_ora = True
                    else:
                        gruppi_cod = []
                if gruppi_cod:
                    disponibili = list(mani[1])
                    gruppi = []
                    for g in gruppi_cod:
                        gr = []
                        for cod in g:
                            x = next(c for c in disponibili
                                     if c.codice == cod)
                            disponibili.remove(x)
                            gr.append(x)
                        gruppi.append(gr)
                    # una carta la tiene per scartare
                    if sum(len(g) for g in gruppi) == len(mani[1]) and \
                            len(gruppi) > 0 and len(gruppi[-1]) > 3:
                        gruppi[-1] = gruppi[-1][:-1]
                    cala(1, gruppi)
                    yield from tv.fermi()
                if aperto[1]:
                    for c in list(mani[1]):
                        if len(mani[1]) > 1 and attacca(1, c):
                            rifai_tavola()
                            rifai_mano(1)
                            yield from tv.fermi()
                if preso is not None and preso in mani[1] and \
                        len(mani[1]) > 1:
                    pass
                if not mani[1]:
                    chiude = 1
                    in_mano[0] = apre_ora
                else:
                    # scarta la carta che serve meno: la piu' alta fra
                    # quelle che non hanno compagne vicine
                    def utile(c):
                        if jolly(c.codice):
                            return 100
                        r, sm = rango(c.codice), seme(c.codice)
                        u = 0
                        for x in mani[1]:
                            if x is c or jolly(x.codice):
                                continue
                            if rango(x.codice) == r:
                                u += 3
                            if seme(x.codice) == sm and \
                                    abs(rango(x.codice) - r) <= 2:
                                u += 2
                        return u * 20 - punti_in_mano([c.codice])
                    candidati = [c for c in mani[1] if c is not preso] or \
                        mani[1]
                    c = min(candidati, key=utile)
                    scarta(1, c)
                    yield from tv.fermi()
                    if not mani[1]:
                        chiude = 1
                        in_mano[0] = apre_ora
            tv.righe = []
            if pulisci_tavola():
                yield from tv.fermi()
            turno = 1 - turno
        # fine mano: chi resta paga le carte (arrotondate) piu' la messa.
        # Chiudendo "di mano" la messa salta e la volta dopo raddoppia.
        perde = 1 - chiude
        carte_p = arrotonda_ramino(
            punti_in_mano([c.codice for c in mani[perde]]))
        paga_messa = 0 if in_mano[0] else messa[0]
        if in_mano[0]:
            messa[0] += MESSA
        else:
            messa[0] = MESSA
        paga = carte_p + paga_messa
        totali[perde] += paga
        tv.punti = list(totali)
        C.suona("levelup" if chiude == 0 else "gameover")
        for c in mani[1]:
            tv.sposta(c, c.pos, 0.0, scoperta=True)
        righe = [(T("r_cards"), carte_p if perde == 0 else 0,
                  carte_p if perde == 1 else 0),
                 (T("r_messa"), paga_messa if perde == 0 else 0,
                  paga_messa if perde == 1 else 0)]
        if in_mano[0]:
            righe.append((T("r_in_mano"), "", ""))
        tab = {"titolo": T("hand_over"), "tot": list(totali),
               "righe": righe}
        fine = max(totali) >= punti_partita()
        if fine:
            vince = 0 if totali[0] < totali[1] else 1
            tab["fondo"] = T("win_match") % tv.nomi[vince]
            paga_posta(tv, posta[0], vince, righe)
            posta[0] = None
            opz = [T("again"), T("menu")]
        else:
            opz = [T("next")]
        # l'alone viola sull'ultima carta giocata da chi ha chiuso: si
        # vede subito con che gioco e' uscito
        viola = [ultima[0]] if ultima[0] is not None else []
        i = yield from tv.fine_mano(T("hand_won") % tv.nomi[chiude], tab,
                                    opz, viola)
        if fine:
            if i == 1:
                return "menu"
            totali = [0, 0]
            messa[0] = MESSA
        chi_inizia = 1 - chi_inizia


def turno_umano_ramino(tv, mani, aperto, tavola, scarti, pesca_mazzo, scarta,
                       cala, attacca, rifai_mano, rifai_tavola, ordina,
                       ordine_semi, a_mano, calate, punti_calate,
                       ordina_meglio):
    """Il turno del giocatore, tutto con tre tasti.

    Sinistra e destra portano il cursore su tutto: il mazzo, lo scarto, le
    carte in mano e le combinazioni in tavola.
    A (INVIO) fa la cosa del posto dove sei: pesca dal mazzo, prende lo
    scarto, scarta la carta in mano. Se hai delle carte scelte, le cala.
    Y (il tasto "cambia", C) sceglie o lascia la carta per la calata; sopra
    una combinazione calata in questo turno e non ancora valida, la
    riprende in mano (anche tenendolo premuto tre secondi).
    X (il tasto del gesso, G) prende la carta: con sinistra e destra la
    porti dove vuoi in mano, o su una combinazione in tavola per
    attaccarla; premi di nuovo X e la lasci."""
    mano = mani[0]
    tasto_x, tasto_y = B.tasto("gesso"), B.tasto("cambia")
    tasto_ord = B.tasto("eff_via")      # RB sul joystick: ordina la mano
    sel = []
    sposta = [None]
    # a ogni turno tuo il cursore parte dal mazzo: devi sempre pescare,
    # se vuoi lo scarto ti sposti tu
    pos = [0]               # dove sta il cursore, nell'elenco dei posti
    tieni = [0.0]           # da quanto tieni premuto Y
    dove_va = [None]        # dove sta andando la carta presa con X
    attacchi = []           # le carte attaccate in questo turno
    fase = ["pesca"]
    preso_scarto = [None]

    def vai_su(c):
        """Porta il cursore su quella carta: dopo aver pescato si vede
        subito qual e', fra tante in mano."""
        p = posti_ora()
        for i, (t, d) in enumerate(p):
            if t == "mano" and d is c:
                pos[0] = i
                return

    def posti_ora():
        """L'elenco dei posti: mazzo, scarto, le carte in mano, le
        combinazioni in tavola."""
        p = [("mazzo", None), ("scarto", None)]
        p += [("mano", c) for c in mano]
        p += [("meld", i) for i in range(len(tavola))]
        return p

    def quadro():
        """Quello che si vede a destra: apertura, punti scelti, punti in
        mano, messa."""
        scelti = 0
        gr = dividi_in_meld([c.codice for c in sel]) if sel else None
        if gr:
            scelti = sum(g[1] for g in gr)
        tv.pannello = [
            (T("r_open"), str(APERTURA) if not aperto[0] else "-"),
            (T("r_sel"), str(scelti) if sel else "0"),
            (T("r_down"), str(punti_calate[0])),
            (T("r_hand"), str(punti_in_mano([c.codice for c in mano]))),
            (T("r_ncards"), str(len(mano))),
        ]

    def messaggio(chiave):
        """Un avviso breve sotto il tavolo."""
        tv.messaggio(T(chiave), 1.4)
        C.suona("errore")

    def riprendi(i):
        """Una calata di questo turno torna in mano (solo se non e' ancora
        valida l'apertura)."""
        if aperto[0] or i >= len(tavola) or tavola[i] not in calate:
            messaggio("r_no_back")
            return False
        gruppo = tavola.pop(i)
        calate.remove(gruppo)
        punti_calate[0] -= valida_meld([c.codice for c in gruppo])[1]
        for c in gruppo:
            mano.append(c)
        a_mano[0] = True
        rifai_tavola()
        rifai_mano(0)
        return True

    try:
        while True:
            posti = posti_ora()
            if not mano and fase[0] == "gioca":
                return "chiuso"
            pos[0] = max(0, min(pos[0], len(posti) - 1))
            tipo, dato = posti[pos[0]]
            tv.cursore = dato if tipo == "mano" else None
            tv.mira = tipo if tipo in ("mazzo", "scarto") else None
            # dopo aver pescato, mazzo e scarto diventano rossi
            tv.mira_col = VERDE if fase[0] == "pesca" else ROSSO
            tv.evidenzia = tavola[dato] if tipo == "meld" else []
            tv.selezionate = sel
            tv.in_mano = sposta[0]
            # la carta presa con X segue il cursore: in mano sta al suo
            # posto, sul tavolo si mette accanto alla combinazione
            if sposta[0] is not None and dove_va[0] != (tipo, dato):
                dove_va[0] = (tipo, dato)
                if tipo == "meld":
                    gruppo = tavola[dato]
                    w0, h0 = C.misura_carta()
                    tv.sposta(sposta[0],
                              (gruppo[-1].pos.x + w0 * 0.75,
                               gruppo[-1].pos.y - h0 * 0.12), 0.0,
                              scoperta=True)
                else:
                    rifai_mano(0)
            tv.righe = [T("r_draw_first") if fase[0] == "pesca"
                        else T("r_choose")]
            quadro()
            yield
            azione = None
            # il mouse: il cursore va dove punti, il clic fa come A
            m = B.mouse_gioco()
            w0, h0 = C.misura_carta()
            sopra = None
            for i, (t, d) in enumerate(posti):
                if t == "mano":
                    r = pygame.Rect(d.pos.x - w0 / 2, d.pos.y - h0 / 2 - d.su,
                                    w0, h0)
                elif t == "meld":
                    carte = tavola[d]
                    r = pygame.Rect(carte[0].pos.x - w0 / 2,
                                    carte[0].pos.y - h0 / 2, w0, h0)
                    for c in carte[1:]:
                        r.union_ip(pygame.Rect(c.pos.x - w0 / 2,
                                               c.pos.y - h0 / 2, w0, h0))
                else:
                    centro = tv.P["mazzo"] if t == "mazzo" else tv.P["scarti"]
                    g = tv.g_mazzo if t == "mazzo" else tv.g
                    r = pygame.Rect(centro[0] - w0 * g / 2,
                                    centro[1] - h0 * g / 2, w0 * g, h0 * g)
                if r.collidepoint(m):
                    sopra = i
            if sopra is not None and B.MOUSE_VIVO[0]:
                pos[0] = sopra
            if tieni[0] > 0:
                tieni[0] += tv.dt
                if tieni[0] > 3.0:
                    tieni[0] = 0.0
                    for i in range(len(tavola) - 1, -1, -1):
                        if tavola[i] in calate:
                            riprendi(i)
            for ev in tv.eventi:
                if ev.type == pygame.KEYUP and ev.key == tasto_y:
                    tieni[0] = 0.0
                if ev.type == pygame.KEYDOWN:
                    if ev.key in (pygame.K_LEFT, pygame.K_a, pygame.K_RIGHT,
                                  pygame.K_d):
                        verso = -1 if ev.key in (pygame.K_LEFT,
                                                 pygame.K_a) else 1
                        if sposta[0] is not None and tipo == "mano":
                            # la carta presa si porta dietro il cursore
                            i_mano = mano.index(sposta[0])
                            dove = i_mano + verso
                            if 0 <= dove < len(mano):
                                mano.remove(sposta[0])
                                mano.insert(dove, sposta[0])
                                a_mano[0] = True
                                rifai_mano(0)
                                pos[0] += verso
                            else:
                                pos[0] = (pos[0] + verso) % len(posti)
                        else:
                            pos[0] = (pos[0] + verso) % len(posti)
                    elif ev.key == tasto_y:
                        tieni[0] = 0.0001
                        if fase[0] == "pesca":
                            messaggio("r_draw_first")
                        elif tipo == "mano":
                            if dato in sel:
                                sel.remove(dato)
                            else:
                                sel.append(dato)
                        elif tipo == "meld":
                            riprendi(dato)
                    elif ev.key == tasto_ord:
                        ordina_meglio()
                        vai_su(mano[min(pos[0], len(mano) - 1)]
                               if tipo == "mano" else mano[0])
                    elif ev.key == tasto_x:
                        if fase[0] == "pesca":
                            messaggio("r_draw_first")
                        elif sposta[0] is None and tipo == "mano":
                            sposta[0] = dato
                            dove_va[0] = ("mano", dato)
                        elif sposta[0] is not None:
                            if tipo == "meld":
                                if len(mano) <= 1 and not aperto[0]:
                                    messaggio("r_keep")
                                else:
                                    carta = sposta[0]
                                    prima = valida_meld(
                                        [x.codice for x in tavola[dato]])[1]
                                    fatto = attacca(0, carta, dato)
                                    if fatto:
                                        if carta in sel:
                                            sel.remove(carta)
                                        if carta is preso_scarto[0]:
                                            preso_scarto[0] = None
                                        sposta[0] = None
                                        dove_va[0] = None
                                        if not aperto[0]:
                                            # prima di aprire, anche gli
                                            # attacchi contano per i 50
                                            dopo = valida_meld(
                                                [x.codice
                                                 for x in tavola[dato]])[1]
                                            attacchi.append((dato, carta))
                                            vale = dopo - prima
                                            if fatto == "jolly":
                                                # il jolly esce e la carta
                                                # entra: il totale non
                                                # cambia, ma la carta
                                                # calata vale i suoi punti
                                                cod = [x.codice for x in
                                                       tavola[dato]]
                                                vale = valore_nel_meld(
                                                    cod, [x.codice for x in
                                                          tavola[dato]].index(
                                                        carta.codice))
                                            punti_calate[0] += vale
                                            if punti_calate[0] >= APERTURA:
                                                aperto[0] = True
                                                del calate[:]
                                                del attacchi[:]
                                                C.suona("levelup")
                                        C.suona("cattura")
                                        rifai_tavola()
                                        rifai_mano(0)
                                    else:
                                        messaggio("r_bad")
                            else:
                                sposta[0] = None
                                dove_va[0] = None
                                rifai_mano(0)
                    elif ev.key in (pygame.K_RETURN, pygame.K_KP_ENTER,
                                    pygame.K_SPACE):
                        azione = "a"
                if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                    if sopra is not None:
                        pos[0] = sopra
                        tipo, dato = posti[pos[0]]
                    azione = "a"
            if azione is None:
                continue
            # ---- il tasto A: fa la cosa del posto dove sei
            if fase[0] == "pesca":
                if tipo == "mazzo":
                    nuova = pesca_mazzo(0)
                    C.suona("cattura")
                    rifai_mano(0)
                    vai_su(nuova)
                    fase[0] = "gioca"
                    yield from tv.fermi()
                elif tipo == "scarto" and scarti:
                    c = scarti.pop()
                    mano.append(c)
                    preso_scarto[0] = c
                    a_mano[0] = True
                    C.suona("cattura")
                    rifai_mano(0)
                    vai_su(c)
                    fase[0] = "gioca"
                    yield from tv.fermi()
                else:
                    messaggio("r_draw_first")
                continue
            if sel:
                # cala le carte scelte
                gruppi_cod = dividi_in_meld([c.codice for c in sel])
                if gruppi_cod is None:
                    messaggio("r_bad")
                    continue
                if len(sel) >= len(mano) and not aperto[0]:
                    messaggio("r_keep")
                    continue
                vale = sum(g[1] for g in gruppi_cod)
                disponibili = list(sel)
                gruppi = []
                for g in gruppi_cod:
                    gr = []
                    for cod in g[2]:
                        x = next(c for c in disponibili if c.codice == cod)
                        disponibili.remove(x)
                        gr.append(x)
                    gruppi.append(gr)
                nuove = cala(0, gruppi)
                if not aperto[0]:
                    calate.extend(nuove)
                    punti_calate[0] += vale
                    if punti_calate[0] >= APERTURA:
                        aperto[0] = True
                        del calate[:]       # ormai sono valide
                        C.suona("levelup")
                for c in sel:
                    if c is preso_scarto[0]:
                        preso_scarto[0] = None
                sel = []
                yield from tv.fermi()
                continue
            if tipo == "mano":
                # scarta: finisce il turno
                if not aperto[0] and punti_calate[0]:
                    # non sei arrivato a 50: torna tutto indietro, anche
                    # la carta presa dallo scarto
                    manca = APERTURA - punti_calate[0]
                    for i, carta in reversed(attacchi):
                        if carta in tavola[i]:
                            tavola[i].remove(carta)
                            mano.append(carta)
                    del attacchi[:]
                    for i in range(len(tavola) - 1, -1, -1):
                        if tavola[i] in calate:
                            riprendi(i)
                    punti_calate[0] = 0
                    if preso_scarto[0] is not None and \
                            preso_scarto[0] in mano:
                        c = preso_scarto[0]
                        mano.remove(c)
                        scarti.append(c)
                        tv.sposta(c, tv.P["scarti"], 0.0, scoperta=True)
                        preso_scarto[0] = None
                        fase[0] = "pesca"
                    a_mano[0] = True
                    rifai_tavola()
                    rifai_mano(0)
                    tv.messaggio(T("r_back") % manca, 2.0)
                    C.suona("errore")
                    continue
                if preso_scarto[0] is dato:
                    messaggio("r_use_taken")
                    continue
                scarta(0, dato)
                yield from tv.fermi()
                return "chiuso" if not mano else None
            messaggio("r_nothing")
    finally:
        tv.cursore = None
        tv.selezionate = []
        tv.in_mano = None
        tv.evidenzia = []
        tv.mira = None
        tv.pannello = []
        tv.righe = []


# ------------------------------------------------------------- texas poker
# Testa a testa contro il banco, con le carte francesi. Puntate fisse
# (limit): si punta il buio grande prima e sul flop, il doppio su turn e
# river, al massimo tre rilanci per giro.
CAT_NOMI = ("t_alta", "t_coppia", "t_doppia", "t_tris", "t_scala",
            "t_colore", "t_full", "t_poker", "t_scala_colore")


def valuta5(carte):
    """(categoria, spareggio) per cinque carte: piu' alto e' meglio."""
    rs = sorted((rango(c) for c in carte), reverse=True)
    semi = [seme(c) for c in carte]
    conta = {}
    for r in rs:
        conta[r] = conta.get(r, 0) + 1
    gruppi = sorted(conta.items(), key=lambda x: (-x[1], -x[0]))
    colore = len(set(semi)) == 1
    uniq = sorted(set(rs), reverse=True)
    scala = 0
    if len(uniq) == 5:
        if uniq[0] - uniq[4] == 4:
            scala = uniq[0]
        elif uniq == [13, 4, 3, 2, 1]:      # l'asso vale 1 nella scala bassa
            scala = 4
    if uniq == [13, 12, 11, 10, 1]:         # asso alto
        scala = 14
    if scala and colore:
        return (8, (scala,))
    if gruppi[0][1] == 4:
        return (7, (gruppi[0][0], gruppi[1][0]))
    if gruppi[0][1] == 3 and gruppi[1][1] == 2:
        return (6, (gruppi[0][0], gruppi[1][0]))
    if colore:
        return (5, tuple(14 if r == 1 else r for r in rs))
    if scala:
        return (4, (scala,))
    if gruppi[0][1] == 3:
        resto = [r for r in rs if r != gruppi[0][0]]
        return (3, (gruppi[0][0],) + tuple(resto))
    if gruppi[0][1] == 2 and gruppi[1][1] == 2:
        alta, bassa = sorted((gruppi[0][0], gruppi[1][0]), reverse=True)
        resto = [r for r in rs if r not in (alta, bassa)]
        return (2, (alta, bassa, resto[0]))
    if gruppi[0][1] == 2:
        resto = [r for r in rs if r != gruppi[0][0]]
        return (1, (gruppi[0][0],) + tuple(resto))
    return (0, tuple(14 if r == 1 else r for r in rs))


def _assi_alti(v):
    """L'asso conta 14: si aggiusta il confronto dei ranghi."""
    cat, spar = v
    return (cat, tuple(14 if x == 1 else x for x in spar))


def valuta7(carte):
    """La migliore combinazione di cinque su sette."""
    meglio = None
    for gr in itertools.combinations(carte, 5):
        v = _assi_alti(valuta5(gr))
        if meglio is None or v > meglio[0]:
            meglio = (v, gr)
    return meglio


def forza_pre(due):
    """Quanto vale la mano coperta, alla Chen: serve alla CPU."""
    r = sorted((14 if rango(c) == 1 else rango(c) for c in due), reverse=True)
    val = {14: 10, 13: 8, 12: 7, 11: 6}.get(r[0], r[0] / 2.0)
    if r[0] == r[1]:
        return max(5.0, val * 2)
    p = val
    if seme(due[0]) == seme(due[1]):
        p += 2
    salto = r[0] - r[1]
    p -= (0, 0, 1, 2, 4)[min(salto, 4)] if salto else 0
    if salto <= 2 and r[0] < 12:
        p += 1
    return p


def partita_texas(tv):
    buio = 20                       # il buio grande
    y_tu = tv.z.bottom - B.s(C.CARTA_H) * 0.62 * tv.g
    y_banco = tv.z.top + B.s(C.CARTA_H) * 0.62 * tv.g
    passo = C.misura_carta()[0] * 0.66
    bottone = 0                     # chi ha il bottone (buio piccolo)
    tv.nuovo_mazzo(mazzo_francese(1))
    random.shuffle(tv.mazzo)
    for k, c in enumerate(tv.mazzo):
        c.vai(tv.posto_mazzo(k), 0.0)
    while True:
        libero = B.soldi() < buio * 4
        if len(tv.mazzo) < 12:
            tv.raccogli_tutto()
            yield from tv.fermi()
        mani = [[], []]
        comuni = []
        messo = [0, 0]              # quanto ha messo ognuno in questa mano
        piatto = [0]
        tv.punti = ["", ""]

        def paga(chi, quanto):
            quanto = max(0, quanto)
            messo[chi] += quanto
            piatto[0] += quanto
            if chi == 0 and not libero:
                B.soldi(-quanto)

        def riga_piatto():
            tv.righe = [T("t_pot") % B.dollari(piatto[0])] if not libero \
                else [T("t_pot") % str(piatto[0])]

        # i bui
        paga(bottone, buio // 2)
        paga(1 - bottone, buio)
        riga_piatto()
        for giro in range(2):
            for chi in (bottone, 1 - bottone):
                c = tv.pesca()
                mani[chi].append(c)
                C.suona("servi")
                pos = tv.riga(len(mani[chi]), y_tu if chi == 0 else y_banco,
                              passo)
                for x, p in zip(mani[chi], pos):
                    tv.sposta(x, p, 0.0, scoperta=chi == 0)
        yield from tv.fermi()

        def scopri_comuni(quante):
            for _ in range(quante):
                comuni.append(tv.pesca())
            pos = tv.riga(len(comuni), tv.z.centery,
                          C.misura_carta()[0] * 1.12)
            for x, p in zip(comuni, pos):
                tv.sposta(x, p, 0.0, scoperta=True, suono="giocata")

        chi_perde = [None]

        def giro_puntate(primo, grande):
            """Un giro di puntate. Torna chi lascia, o None."""
            passa = 0
            rilanci = 0
            chi = primo
            while True:
                da_pareggiare = messo[1 - chi] - messo[chi]
                tv.attivo = chi
                riga_piatto()
                if chi == 0:
                    voci = []
                    if da_pareggiare > 0:
                        voci.append((T("t_fold"), "fold"))
                        voci.append((T("t_call") % (
                            B.dollari(da_pareggiare) if not libero
                            else str(da_pareggiare)), "call"))
                    else:
                        voci.append((T("t_check"), "check"))
                    if rilanci < 3 and (libero or B.soldi() >= grande):
                        voci.append(((T("t_raise") if da_pareggiare > 0
                                      else T("t_bet")), "raise"))
                    i = yield from tv.chiedi([v for v, _ in voci])
                    fa = voci[i][1]
                else:
                    yield from tv.attendi(0.7)
                    fa = mossa_cpu_texas(
                        [x.codice for x in mani[1]],
                        [x.codice for x in comuni], da_pareggiare, rilanci)
                    tv.messaggio({"fold": T("t_folds"), "check": T("t_checks"),
                                  "call": T("t_calls"),
                                  "raise": T("t_raises")}[fa], 1.2)
                if fa == "fold":
                    return chi
                if fa == "call":
                    paga(chi, da_pareggiare)
                    C.suona("giocata")
                    riga_piatto()
                    return None
                if fa == "check":
                    passa += 1
                    C.suona("giocata")
                    if passa == 2:
                        return None
                else:
                    paga(chi, da_pareggiare + grande)
                    rilanci += 1
                    passa = 0
                    C.suona("colpo")
                riga_piatto()
                chi = 1 - chi

        # preflop: comincia chi ha il bottone
        chi_perde[0] = yield from giro_puntate(bottone, buio)
        if chi_perde[0] is None:
            for quante, grande in ((3, buio), (1, buio * 2), (1, buio * 2)):
                scopri_comuni(quante)
                yield from tv.fermi()
                chi_perde[0] = yield from giro_puntate(1 - bottone, grande)
                if chi_perde[0] is not None:
                    break
        # si vede chi vince
        vince = None
        if chi_perde[0] is not None:
            vince = 1 - chi_perde[0]
            testo = T("t_won_fold")
        else:
            for c in mani[1]:
                tv.sposta(c, c.pos, 0.0, scoperta=True)
            yield from tv.fermi()
            mie = valuta7([x.codice for x in mani[0] + comuni])
            sue = valuta7([x.codice for x in mani[1] + comuni])
            tv.punti = [T(CAT_NOMI[mie[0][0]]), T(CAT_NOMI[sue[0][0]])]
            if mie[0] > sue[0]:
                vince, testo = 0, T(CAT_NOMI[mie[0][0]])
            elif sue[0] > mie[0]:
                vince, testo = 1, T(CAT_NOMI[sue[0][0]])
            else:
                vince, testo = None, T("draw")
        yield from tv.attendi(0.8)
        if vince == 0:
            B.soldi(0 if libero else piatto[0])      # il piatto e' suo
            C.suona("levelup")
        elif vince == 1:
            C.suona("gameover")
        else:
            B.soldi(0 if libero else messo[0])
        if not libero:
            B.salva_config()
        guadagno = (piatto[0] - messo[0]) if vince == 0 else \
            -messo[0] if vince == 1 else 0
        tv.righe = [testo, (T("you_win") % B.dollari(guadagno)) if guadagno > 0
                    else (T("you_lose") % B.dollari(-guadagno))
                    if guadagno < 0 else T("push")]
        tv.attivo = 0
        i = yield from tv.chiedi([T("next"), T("leave")])
        tv.righe = []
        tv.punti = ["", ""]
        for c in mani[0] + mani[1] + comuni:
            tv.mazzo.insert(0, c)
            tv.carte.remove(c)
            tv.carte.insert(0, c)
        for k, c in enumerate(tv.mazzo):
            c.vai(tv.posto_mazzo(k), 0.0, scoperta=False, grande=tv.g_mazzo)
        yield from tv.fermi()
        if i == 1:
            return "menu"
        bottone = 1 - bottone


def mossa_cpu_texas(mano, comuni, da_pareggiare, rilanci):
    """Come gioca il banco: guarda solo le sue carte e quelle in mezzo."""
    if not comuni:
        f = forza_pre(mano)
        if f >= 9:
            forza = 0.85
        elif f >= 6:
            forza = 0.6
        elif f >= 4:
            forza = 0.4
        else:
            forza = 0.2
    else:
        cat = valuta7(mano + comuni)[0][0]
        forza = min(0.95, 0.18 + cat * 0.11)
        if cat == 0:
            # carta alta: conta se almeno e' alta
            alte = max(14 if rango(c) == 1 else rango(c) for c in mano)
            forza = 0.12 + alte / 60.0
    caso = random.random()
    if da_pareggiare <= 0:
        if forza > 0.62 and rilanci < 3 and caso < 0.75:
            return "raise"
        if caso < 0.08 and rilanci < 3:
            return "raise"          # ogni tanto un bluff
        return "check"
    if forza > 0.72 and rilanci < 3 and caso < 0.6:
        return "raise"
    if forza > 0.35 or caso < 0.12:
        return "call"
    return "fold"


# ----------------------------------------------------------------- menu
# (chiave, partita, che carte usa)
GIOCHI = (("blackjack", partita_blackjack, "francesi"),
          ("sette", partita_sette, "italiane"),
          ("scopa", partita_scopa, "italiane"),
          ("briscola", partita_briscola, "italiane"),
          ("ramino", partita_ramino, "francesi"),
          ("texas", partita_texas, "francesi"))


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
            T("dealer") if partita in (partita_blackjack, partita_texas)
            else random.choice(B.AVVERSARI)]
    C.carica_suoni()
    C.musica_carte()
    tv = Tavolo(sc, clock, nomi, chiave)
    esito = tv.gioca(partita)
    C.fine_musica_carte()
    return esito


def cornice(sc, r):
    """Il filo d'oro attorno a un'anteprima."""
    pygame.draw.rect(sc, B.ORO_LOGO, r.inflate(B.s(6), B.s(6)),
                     max(1, B.s(1)))


def anteprima_panno(sc, i, centro):
    """Il quadratino del panno, come si vede sul tavolo. A caso: un punto
    interrogativo d'oro."""
    lato = B.s(150)
    if i < 0 or not B.PANNI:
        r = pygame.Rect(0, 0, lato, lato)
        r.center = centro
        q = pygame.Surface(r.size, pygame.SRCALPHA)
        q.fill((0, 0, 0, 120))
        sc.blit(q, r)
        cornice(sc, r)
        f = B.FONTS.get("elegante") or B.FONTS["grande"]
        t = f.render("?", True, B.ORO_SCELTA)
        sc.blit(t, t.get_rect(center=r.center))
        return
    if not (0 <= i < len(B.PANNI)):
        return
    q = B.texture(B.PANNI[i][1], (lato, lato))
    if q is None:
        return
    r = q.get_rect(center=centro)
    sc.blit(q, r)
    cornice(sc, r)


def anteprima_mazzo(sc, tipo, centro):
    """Il dorso e una figura del mazzo scelto, uno accanto all'altra."""
    alto = B.s(190)
    figura = "KH" if tipo == "francesi" else "10d"
    pezzi = []
    for img in (C.immagine_mazzo("dorso"), C.immagine_carta(figura)):
        if img is None:
            continue
        largo = max(1, int(img.get_width() * alto / float(img.get_height())))
        pezzi.append(C._riduci(img, largo, alto))
    if not pezzi:
        return
    gap = B.s(12)
    tot = sum(p.get_width() for p in pezzi) + gap * (len(pezzi) - 1)
    x = centro[0] - tot // 2
    for p in pezzi:
        r = p.get_rect(midleft=(x, centro[1]))
        sc.blit(p, r)
        cornice(sc, r)
        x += p.get_width() + gap


def anteprima_due(sc, due, centro):
    """I dorsi dei due mazzi del ramino, uno accanto all'altro."""
    alto = B.s(190)
    pezzi = []
    for cartella in due:
        img = C.immagine_mazzo("dorso", cartella)
        if img is None:
            continue
        largo = max(1, int(img.get_width() * alto / float(img.get_height())))
        pezzi.append(C._riduci(img, largo, alto))
    if not pezzi:
        return
    gap = B.s(12)
    tot = sum(p.get_width() for p in pezzi) + gap * (len(pezzi) - 1)
    x = centro[0] - tot // 2
    for p in pezzi:
        r = p.get_rect(midleft=(x, centro[1]))
        sc.blit(p, r)
        cornice(sc, r)
        x += p.get_width() + gap


def lista_menu(sc, clock, logo, sottotitolo, voci_fn, scelta_fn,
               gira_fn=None, extra_fn=None):
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
        voci = voci_fn()        # dopo i tasti: il valore cambiato si vede
        sel = min(sel, len(voci) - 1)
        font, small = B.FONTS["font"], B.FONTS["small"]
        B.sfondo_menu(sc, logo)
        t = small.render(sottotitolo() if callable(sottotitolo)
                         else sottotitolo, True, B.ORO_SOTTO)
        sc.blit(t, t.get_rect(center=(B.WIN_W // 2, B.s(270))))
        con_valori = any(v is not None for _, v in voci)
        porte = set(i for i, (_, v) in enumerate(voci) if v is None)
        rett = B.disegna_voci(sc, voci, sel, font, small, B.s(330), B.s(46),
                              frecce=con_valori, porte=porte)
        if extra_fn is not None:
            extra_fn(sel, (B.WIN_W // 2 + B.s(420), B.s(470)))
        for i, r in enumerate(rett):
            if B.MOUSE_VIVO[0] and r.collidepoint(mouse):
                sel = i
        B.presenta()


def famiglie_francesi():
    """I mazzi francesi divisi per disegno: francesi_<disegno>_<colore>.
    Nel ramino si gioca con due mazzi dello stesso disegno e si sceglie
    che colori accoppiare."""
    fam = {}
    for cartella, _ in mazzi_per("francesi"):
        pezzi = cartella.split("_")
        disegno = pezzi[1] if len(pezzi) > 2 else cartella
        colore = "_".join(pezzi[2:]) if len(pezzi) > 2 else ""
        fam.setdefault(disegno, []).append((cartella, colore))
    for v in fam.values():
        v.sort()
    return fam


def mazzi_ramino():
    """I due mazzi scelti per il ramino: (cartella A, cartella B)."""
    fam = famiglie_francesi()
    if not fam:
        return None, None
    nomi = sorted(fam)
    dis = B.CFG.get("ramino_disegno")
    if dis not in fam:
        dis = next((d for d in nomi if len(fam[d]) > 1), nomi[0])
    colori = fam[dis]
    def scegli(chiave, difetto):
        c = B.CFG.get(chiave)
        for cartella, _ in colori:
            if cartella == c:
                return cartella
        return colori[min(difetto, len(colori) - 1)][0]
    return dis, (scegli("ramino_a", 0), scegli("ramino_b", 1))


def menu_gioco(sc, clock, logo, chiave, partita, tipo):
    """Il sottomenu di un gioco: Gioca, il mazzo (se ce n'e' da scegliere)
    e Indietro."""
    def mazzi():
        return mazzi_per(tipo)

    doppio = chiave == "ramino"     # due mazzi dello stesso disegno

    def ha_mazzi():
        return len(mazzi()) > 1 and not doppio

    def righe_mazzo():
        """Le righe in piu' fra Gioca e Regole."""
        if doppio:
            dis, due = mazzi_ramino()
            if dis is None:
                return [(T("limite"), str(punti_partita()))]
            colore = lambda c: nome_mazzo("_".join(c.split("_")[2:])
                                          or c)
            return [(T("family"), nome_mazzo(dis)),
                    (T("col_a"), colore(due[0])),
                    (T("col_b"), colore(due[1])),
                    (T("limite"), str(punti_partita()))]
        if ha_mazzi():
            i = mazzo_del_gioco(chiave, tipo)
            return [(T("deck"), nome_mazzo(mazzi()[i][0]))]
        return []

    def voci():
        return [(T("play"), None)] + righe_mazzo() + \
            [(T("rules"), None), (T("back"), None)]

    def gira(i, verso):
        if doppio:
            fam = famiglie_francesi()
            nomi = sorted(fam)
            dis, due = mazzi_ramino()
            if dis is None:
                return
            if i == 1:
                dis = nomi[(nomi.index(dis) + verso) % len(nomi)]
                B.CFG["ramino_disegno"] = dis
                B.CFG.pop("ramino_a", None)
                B.CFG.pop("ramino_b", None)
            elif i in (2, 3):
                colori = [c for c, _ in fam[dis]]
                ora = due[i - 2]
                k = (colori.index(ora) + verso) % len(colori)
                B.CFG["ramino_a" if i == 2 else "ramino_b"] = colori[k]
            elif i == 4:
                scelte = (100, 200, 300, 500)
                k = (scelte.index(punti_partita()) + verso) % len(scelte)
                B.CFG["ramino_punti"] = scelte[k]
            else:
                return
            B.salva_config()
            B.suona_fx("menu_tic", 0.6)
            return
        m = mazzi()
        if i == 1 and len(m) > 1:
            k = (mazzo_del_gioco(chiave, tipo) + verso) % len(m)
            B.CFG["mazzo_" + chiave] = m[k][0]
            B.salva_config()
            B.suona_fx("menu_tic", 0.6)

    def scelta(i):
        if i == 0:
            return "gioca"
        n = len(righe_mazzo())
        if 1 <= i <= n:
            gira(i, 1)
            return None
        return "regole" if i == n + 1 else "back"

    def extra(sel, centro):
        n = len(righe_mazzo())
        if not (1 <= sel <= n):
            return
        if doppio:
            if sel == 4:
                return
            dis, due = mazzi_ramino()
            if dis is None:
                return
            anteprima_due(sc, due, centro)
        else:
            anteprima_mazzo(sc, tipo, centro)

    while True:
        q = lista_menu(sc, clock, logo, T(chiave), voci, scelta, gira, extra)
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


def menu_giochi(sc, clock, logo):
    """La lista dei giochi di carte."""
    avviso = [-99999]

    def voci():
        return [(T(k) if f else "%s  (%s)" % (T(k), T("soon")), None)
                for k, f, _ in GIOCHI] + [(T("back"), None)]

    def sotto():
        if pygame.time.get_ticks() - avviso[0] < 1800:
            return T("soon")
        return T("games")

    def scelta(i):
        if i < len(GIOCHI):
            if GIOCHI[i][1] is None:
                avviso[0] = pygame.time.get_ticks()
                return None
            return i
        return "back"

    while True:
        q = lista_menu(sc, clock, logo, sotto, voci, scelta)
        if q in ("quit", "back"):
            return q
        chiave, partita, tipo = GIOCHI[q]
        if menu_gioco(sc, clock, logo, chiave, partita, tipo) == "quit":
            return "quit"


def menu_carte(sc, clock, logo):
    """Il menu delle carte: i giochi, il panno, le impostazioni."""
    def panno_ora():
        """-1 vuol dire a caso, come nel biliardo."""
        i = B.CFG.get("panno_carte", -1)
        if not isinstance(i, int) or not (-1 <= i < len(B.PANNI)):
            i = -1
        return i

    def gira_panno(i, verso):
        if i != 1 or not B.PANNI:
            return
        # il giro passa anche da "a caso"
        B.CFG["panno_carte"] = (panno_ora() + verso + 1) % \
            (len(B.PANNI) + 1) - 1
        B.salva_config()
        B.suona_fx("menu_tic", 0.6)

    def voci():
        i = panno_ora()
        panno = B.T("random") if i < 0 else \
            B.titolo_tex(B.PANNI[i][1]) if B.PANNI else "-"
        return [(T("games"), None), (T("cloth"), panno),
                (T("settings"), None), (T("back"), None)]

    def scelta(i):
        if i == 1:
            gira_panno(i, 1)
            return None
        return ("giochi", None, "settings", "back")[i]

    def extra(sel, centro):
        if sel == 1:
            anteprima_panno(sc, panno_ora(), centro)

    while True:
        q = lista_menu(sc, clock, logo, T("cards"), voci, scelta, gira_panno,
                       extra)
        if q == "quit":
            return "quit"
        if q == "back":
            return "menu"
        if q == "settings":
            if B.schermata_setting(sc, clock, logo, pagina="generale",
                                   puo_riaprire=True) == "quit":
                return "quit"
            continue
        if q == "giochi" and menu_giochi(sc, clock, logo) == "quit":
            return "quit"
