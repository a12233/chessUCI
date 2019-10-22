# -*- coding: utf-8 -*-
"""
I. About the script

1. It takes a pgn file with games in it and analyze those
   games there one by one if there are more than one game
2. It mainly uses Stockfish uci engine during development.
   Other uci engines can be used provided those engines support
   multipv mode

   
II. Application references and dependencies

1. Developed under python 2.7.11
2. Using python-chess library version 0.14.1
   site: http://python-chess.readthedocs.org/en/v0.14.1/
3. Tested under Windows 7, and Linux Mint


III. License notice

This program is free software, you can redistribute it and/or modify
it under the terms of the GPLv3 License as published by the
Free Software Foundation.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY. See the GNU General Public License
for more details.

You should have received a copy of the GNU General Public License (LICENSE)
along with this program, if not visit https://www.gnu.org/licenses/gpl.html


IV. Release notes

1. Release date: August 15, 2016
2. Files: 
   a. game_analyzer_v39.11.beta.py
   b. game_analyzer_v39.11.beta.exe
   c. runChessGameAnalyzer.bat
   d. sampleInput.pgn
   e. LICENSE
   f. chessGameAnalyzerReadme.txt


V. Chess Game Analyzer Development log

A. Notes:
1. Interesting positions are saved in puzzle.epd
2. Existing comments in the original pgn will not be copied to the analyzed game
3. Original pgn file will not be changed by the script
4. Installation of python 2.7.11 or later (not tested though) and
   python-chess v0.14.1 on your computer are needed for the script to work

B. Changes:
v39.11.beta
1. Modify writing of pv2 line
2. Modify condition of writing !! and ! to game move NAG, now also depends
on complexity number. score >= +1.0 and move changes >= 5 for !! and >= 3 for !
3. Remove saving of interesting position as puzzle
4. Use utf-8 encoding, for reading input file and writing to output file.

v39.10
1. Added comment at the end of a game for number of blunders,
mistakes and dubious moves.

Decisive advantage: v >= 3P
Moderate advantage: v >= 1.5P and v < 3P
Slight advantage: v >= 0.25P and v < 1.5P

Blunder (??): From non-decisive to decisive advantage for opp
Mistakes (?): From non-moderate to moderate advantage for opp
Dubious (?!): From non-slight to slight advantage for opp

2. Change blundermargincp to addvariationmargincp
3. Change only move symbol margin from +3 pawns to +1.5 pawns

v39.9
1. Modify position_nags(), do not return $0 instead return None
2. Verify that we will get search info when trying to get threat move
and threat pv

v39.8
1. Do not add $0 after a game move when there is an analysis to be written

v39.7
1. Correct spelling of possibility
2. Added French translation
3. Fixed double output of result after the game notation if there is comment
"A model game for white, black or white and black".

v39.6.beta
1. Added --cerebellum option, so that the tool will be able to comment in the
book moves of a player
2. Handle properly when the analyzing engine does not return a search info when
told to analyze a position. A comment is added {No search output from Annotator}
3. Modify comment when polyglot book is used
4. When --bookfile <polyglot book filename> and --cerebellum <1> is used,
Only the polyglot book will be probed.

v39.5
1. Added # -*- coding: utf-8 -*- at the top
2. Added --lang option as language option, default is ENG, other value is GER
3. Added german language for comments, note there are unicode
string in the comments for german translation
4. Change comment_key() to get_good_comment()
5. Change comments to list instead of dict except good comment

v39.4
1. Remove empty comment in REASON_COMMENT list
2. Update usage()

v39.3
1. Add model game comment only when last move of a player or both players
are all analyzed
2. Added more alternative comment
3. Added more reason comment

v39.2
1. Create a new function analyze_games()
2. Modify Function names
3. Modify Good comment

v39.1
1. Check if process created has been terminated by commmunicate()

v39
1. Added Model game comment at the end of every game,
   if game has no blunder beyond 50 cp. It can be a model game
   for white, for black and for white and black
2. Added player name option, to analyze only the game of specific player
3. Modify condition of parsing pv lines, there should be
   "score cp" or "score mate" in the pv line

v38
1. Use command line options instead of interactive user input

v37
1. Copy the original headers completely into analyzedGame.pgn
2. Tested using Stockfish 7 under OS windows 7
3. Calculation of position complexity by "pv move changes"
   starts at iteration depth equal to 9
4. Print statements are now converted to function for python 3.0 and later
   compatibility

v36.1
1. Upgrade to use Python-chess version 0.13.0

v36
1. Added polyglot book, to not analyze game move if it is in the book.
   The book filename should be book.bin, and should be located in the
   same directory of this tool.
2. Added option to set blunder margin in cp. If this value is low, expect
   to have more analysis lines will be shown.
3. Modify Annotator tag, added blunder margin in cp
4. Added position NAG (+/-, +- ) to a line "color is threatening" variation
"""


from __future__ import print_function
import chess
import codecs
import sys
from chess import pgn
import os
import subprocess
import random
from chess import polyglot
import getopt
from io import StringIO
import chess.engine 


# Constants
APP_NAME = "Chess Game Analyzer"
APP_VERSION = "39.11.beta"
INF = 32000
MAX_PLY = 128
BAD_SCORE = -INF
ONLY_MOVE_SCORE = 1.5
ANALYSIS_MARGIN = 10.0
PUZZLE_MARGIN = 0.80
GOOD_SCORE = 1.5
WHITE = 1
BLACK = 0
MODEL_GAME_MARGIN = 0.5


WHITE_MATE_THREAT_COMMENT = {'ENG': 'White is threatening mate in',
                             'FRA': 'Les blancs menacent mat en',
                             'GER': 'Weiß droht mir in'}

BLACK_MATE_THREAT_COMMENT = {'ENG': 'Black is threatening mate in',
                             'FRA': 'Les noirs menacent mat en',
                             'GER': 'Schwarz droht mir in'}

MOVE_FROM_COMMENT = {'ENG': 'Move from',
                     'FRA': 'Coup de la bibliotheque',
                     'GER': 'Verschieben von'}

BOOK_RECOMMENDS_COMMENT = {'ENG': 'recommends:',
                           'FRA': 'recommande :',
                           'GER': 'empfiehlt :'}

WHITE_THREAT_COMMENT = {'ENG': 'White is threatening',
                        'FRA': 'Les blancs menacent',
                        'GER': 'Weiß droht'}

BLACK_THREAT_COMMENT = {'ENG': 'Black is threatening',
                        'FRA': 'Les noirs menacent',
                        'GER': 'Schwarz droht'}

WHITE_MODEL_COMMENT = {'ENG': 'A Model game for White.',
                       'FRA': 'Un jeu exemplaire de la part des blancs.',
                       'GER': 'Ein Modell für White Spiel.'}

BLACK_MODEL_COMMENT = {'ENG': 'A Model game for Black.',
                       'FRA': 'Un jeu exemplaire de la part des noirs.',
                       'GER': 'Ein Modell für Schwarz-Spiel.'}

WHITE_BLACK_MODEL_COMMENT = {'ENG': 'A Model game for White and Black.',
                             'FRA': 'Un jeu exemplaire de la part des blancs et des noirs.',
                             'GER': 'Ein Model Spiel für Weiß und Schwarz.'}

# Random comment
BAD_COMMENT = ['Not good is',
               'But not',
               'Bad is',
               'Inferior is',
               'Not reliable is',
               'Incorrect is',
               'Unsatisfactory is'
               ]

REASON_COMMENT = ['due to',
                  'in view of',
                  'thanks to',
                  'considering',
                  'on the grounds of',
                  'because of',
                  'for the reason of',
                  ]

GOOD_COMMENT = {1: 'A nice try could be',
                2: 'Better is',
                3: 'More accurate is',
                4: 'Superior is',
                5: 'Excellent is'
                }

ALTERNATIVE_COMMENT = ['Also playable is',
               'Another interesting line is',
               'One that deserves attention is',
               'A good alternative is',
               'Also sufficient is',
               'Worthy of consideration is',
               'Also practical is',
               'A fine line worth of consideration is',
               'Also capable is',
               'Also promising is',
               'Another modest line is',
               'Another possibility is',
               'A good one too is',
               'Not to be underestimated is'
               ]

GER_BAD_COMMENT = ['Nicht gut ist',
               'Aber nicht',
               'Schlecht ist',
               'Schwächer ist',
               'Ungeeignet ist',
               'Inkorrekt ist',
               'Ungenau ist'
               ]

GER_REASON_COMMENT = ['wegen',
                  'in Anbetracht von',
                  'aufgrund von',
                  'berücksichtigt',
                  'mit der Begründung',
                  'infolge von',
                  'aus dem einfachen Grund',
                  ]

GER_GOOD_COMMENT = {1: 'Ein guter Versuch wäre',
                2: 'Besser ist',
                3: 'Genauer ist',
                4: 'Viel besser ist',
                5: 'Exzellent ist'
                }

GER_ALTERNATIVE_COMMENT = ['Ebenso spielbar ist',
               'Ein interessanter Zug ist',
               'Beachtung verdient auch',
               'Eine gute Alternative ist',
               'Ausreichend ist auch',
               'Eine Überlegung wert ist auch',
               'Spielbar ist auch',
               'Vielversprechend erscheint auch',
               'Ausreichend ist auch',
               'Chancenreich erscheint',
               'Ein anderer solider Zug ist',
               'Eine andere Möglichkeit ist',
               'Gut wäre auch',
               'Nicht zu unterschätzen ist'
               ]

FRA_BAD_COMMENT = ['Pas acceptable serait',
                    'Non pas',
                    'Mauvais serait',
                    'Inférieur serait',
                    'Aventureux serait',
                    'Incorrect serait',
                    'Insuffisant serait'
                   ]

FRA_REASON_COMMENT = ['en raison de',
                    'à la vue de',
                    'grâce à',
                    'étant donné que',
                    'parce que',
                    'à cause de',
                    'au motif de'
                     ]

FRA_GOOD_COMMENT = {1:'Une bonne démarche serait',
                    2:'Meilleur serait',
                    3:'Plus précis serait',
                    4:'Supérieur serait',
                    5:'Excellent serait'
                   }

FRA_ALTERNATIVE_COMMENT = ["Aussi jouable :",
                    "Une autre ligne intéressante :",
                    "Sollicite aussi l'attention :",
                    "Une bonne alternative est",
                    "Aussi suffisant :",
                    "Mérite aussi l'attention :",
                    "Jouable aussi :",
                    "Une ligne attrayante est",
                    "Aussi efficace :",
                    "Aussi prometteur est",
                    "Une autre ligne convenable :",
                    "Une autre possibilité est",
                    "Très bien aussi :",
                    "À ne pas sous-estimer :"
                   ]

def usage():
    """ List of options that can be used """
    print('Usage:')
    print('appname -f g.pgn --engine Sf7.exe --eoption "Hash value 128, Threads value 1"')
    print('\nOptions:')
    print('-f or --file <input pgn filename>')
    print('--engine <uci engine filename>')
    print('--movetime <time in ms per move, default: 1000 ms>')
    print('--eoption "<opt_name1> value <opt_value1>, <opt_name2> value <opt_value2>"')
    print('--outfile <filename>')
    print('--startmove <move number>')
    print('--endmove <move number>')
    print('--bookfile <polyglot book filename>')
    print('--addvariationmargincp <value in centipawn>')
    print('--lang <value ENG or GER or FRA>')
    print('--cerebellum <0 or 1>')
    print('--bookannotationonly <0 or 1>')
    print('--player <player name in the game found in either White or Black pgn tag>')
   

def random_reason(_lang):
    """ Returns a string as reason comment """
    res = []
    if _lang == 'GER':
        MY_REASON_COMMENT = GER_REASON_COMMENT
    elif _lang == 'FRA':
        MY_REASON_COMMENT = FRA_REASON_COMMENT
    else:
        MY_REASON_COMMENT = REASON_COMMENT
    for i in MY_REASON_COMMENT:
        res.append(i)
    random.shuffle(res)
    idx = random.randint(0,len(res)-1)
    if _lang == 'GER' or _lang == 'FRA':
        return res[idx].decode('utf-8')
    return res[idx]


def random_bad(_lang):
    """ Returns a string for bad comment """
    res = []
    if _lang == 'GER':
        MY_BAD_COMMENT = GER_BAD_COMMENT
    elif _lang == 'FRA':
        MY_BAD_COMMENT = FRA_BAD_COMMENT
    else:
        MY_BAD_COMMENT = BAD_COMMENT
    for i in MY_BAD_COMMENT:
        res.append(i)
    random.shuffle(res)
    if _lang == 'GER' or _lang == 'FRA':
        return res[0].decode('utf-8')
    return res[0]


def get_alternative_comment(com, inc, _lang):
    """ Returns comment based on index inc """
    if inc >= len(com):
        # Randomize again
        random_alternative(_lang)
        inc = 0
    val = com[inc]
    if _lang == 'GER' or _lang == 'FRA':
        val = val.decode('utf-8')
    inc += 1
    return (val, inc)


def random_alternative(_lang):
    """ Returns a list of comments in a different order.
        Call this once per new game parsed.
    """
    res = []
    if _lang == 'GER':
        MY_ALTERNATIVE_COMMENT = GER_ALTERNATIVE_COMMENT
    elif _lang == 'FRA':
        MY_ALTERNATIVE_COMMENT = FRA_ALTERNATIVE_COMMENT
    else:
        MY_ALTERNATIVE_COMMENT = ALTERNATIVE_COMMENT
    for i in MY_ALTERNATIVE_COMMENT:
        res.append(i)
    random.shuffle(res)
    return res


def get_good_comment(cvalue, hvalue, side_tomove, _lang):
    """ Returns a comment from GOOD_COMMENT and GER_GOOD_COMMENT
        based on scores,
        cvalue = analyzer score of its bestmove
        hvalue = analyzer score of human move
    """    
    comment_num = 2
    if side_tomove == WHITE:
        if cvalue - hvalue >= 3.0:
            comment_num = 5
            # If already lossing
            if cvalue <= -3.0:
                comment_num = 1
        elif cvalue - hvalue >= 1.5:
            comment_num = 4
            if cvalue <= -3.0:
                comment_num = 1
        elif cvalue - hvalue >= 0.50:
            comment_num = 3
            if cvalue <= -3.0:
                comment_num = 1
    else:
        if cvalue - hvalue <= -3.0:
            comment_num = 5
            if cvalue >= 3.0:
                comment_num = 1
        elif cvalue - hvalue <= -1.5:
            comment_num = 4
            if cvalue >= 3.0:
                comment_num = 1
        elif cvalue - hvalue <= -0.5:
            comment_num = 3
            if cvalue >= 3.0:
                comment_num = 1
    if _lang == 'GER':
        return GER_GOOD_COMMENT[comment_num].decode('utf-8')
    elif _lang == 'FRA':
        return FRA_GOOD_COMMENT[comment_num].decode('utf-8')
    return GOOD_COMMENT[comment_num]
        
    
def mate_indicator(d2m):
    """ Returns +/-M for mate score indication """
    
    if d2m > 0:
        return 'White will mate black in %d moves' % abs(d2m)
    elif d2m < 0:
        return 'Black will mate white in %d moves' % abs(d2m)
    return 'None'


def GetMaxMoveNumber(game):
    """ Take a game object and returns max number of moves """
    fmvn = 0
    while len(game.variations):
        fmvn = game.board().fullmove_number
        next_node = game.variation(0)
        game = next_node
    return int(fmvn)
    

def get_engine_detailed_data(data, side):
    """ Will extract score, depth, move and pv from input data """
    
    # data = -0.79/15 20...Qa5 21.Nxd6 Bxa4 22.Bb6 Rxd6 23.Bxa5 Rxd3 24.cxd3 Bxd1
    # data = -0.79/15 21.Nxd6 Bxa4 22.Bb6 Rxd6 23.Bxa5 Rxd3 24.cxd3 Bxd1
    list_value = data.split(' ')
    score_and_depth = list_value[0]
    list_sd = score_and_depth.split('/')
    eval_value = float(list_sd[0])
    # Change sign if side is black
    if side == BLACK:
        eval_value = -1*eval_value
    depth = list_sd[1].strip()
    depth = int(depth)

    move = list_value[1]
    if '...' in move:
        move = move.split('.')
        move = move[3]
    else:
        move = move.split('.')
        move = move[1]
    move = move.strip()

    pvar = ' '.join(list_value[1:])

    return (eval_value, depth, move, pvar)

    
def get_score_and_depth(data, side_to_move):
    """ Will extract score and depth from data.
        The returned score is WPOV
    """
    
    # data = -0.79/15 20... Qa5 21. Nxd6 Bxa4 22. Bb6 Rxd6 23. Bxa5 Rxd3 24. cxd3 Bxd1
    d_split = data.split(' ')
    left_val = d_split[0]
    token = left_val.split('/')
    val = float(token[0])
    
    # Change sign from point of view of player
    # We did this because we let the engine analyze
    # the fen + move of the player
    val = -1*val
    
    # Change sign if side is black, because we
    # use white POV in the analyzed output pgn file.
    # Move NAGS !?, ? and others are easier to append by
    # checking whether the value is positive or negative
    if side_to_move == BLACK:
        val = -1*val
    depth = token[1].strip()
    depth = int(depth)

    return (val, depth)
    

def save_headers(game, outputFN, engine_name, num_threads, nMoveTime):
    """ Print to file the headers of a game including
        annotator name or the engine that analyzes the game
    """

    # # Save headers
    # for key, value in game.headers.iteritems():
    #     with open(outputFN, 'a+') as f:
    #         if key != 'Annotator':
    #             f.write('[%s \"%s\"]\n' %(key, value))

    # # Write the Annotator last
    # with open(outputFN, 'a+') as f:
    #     f.write('[Annotator "%s (%0.1fs/pos, thread=%d)"]\n\n' %(engine_name,
    #                     float(nMoveTime)/1000, num_threads))
    

def is_number(s):
    """ Check if input is a number """
    
    try:
        float(s)
        return True
    except ValueError:
        return False


def position_nags(v):
    """ Returns the NAGs based on input value v """    
    nag = None    
    if abs(v) < 0.25:
        nag = "$10" # even =
    if v >= 3.0:
        nag = "$18"  # White has decisive adv +-
    elif v >= 1.0:
        nag = "$16"  # White has moderate adv +/-
    elif v >= 0.25:
        nag = "$14"  # White has slight adv +/=
    elif v <= -3.0:
        nag = "$19"  # Black has decisive adv -+ 
    elif v <= -1.0:  
        nag = "$17"  # Black has moderate adv +/-
    elif v <= -0.25:
        nag = "$15"  # Black has slight adv =/+
    assert nag is not None
    return nag


def move_nags(s, v1, v2):
    """ Returns move NAGs for v2 based on side to move,
        engine score v1 and human score v2
    """
    nag = None
    if (s == WHITE and v1 > -3.0 and v2 <= -3.0) or (s == BLACK and v1 < 3.0 and v2 >= +3.0):
        nag = "$4"  # ??
    elif (s == WHITE and v1 >= +3.0 and v2 < 0.25) or (s == BLACK and v1 <= -3.0 and v2 > -0.25):
        nag = "$4"  # ??        
    elif (s == WHITE and v1 > -2.99 and v2 <= -1.0) or (s == BLACK and v1 < +2.99 and v2 >= +1.0):
        nag = "$2"  # ?
    elif (s == WHITE and v1 > -0.99 and v2 <= -0.25) or (s == BLACK and v1 < +0.99 and v2 >= +0.25):
        nag = "$6"  # ?!
    return nag


def one_value_move_nags(s, v):
    """ Returns move NAGs for based on side and v
    """
    nag = None
    if (s == WHITE and v <= -3.0) or (s == BLACK and v >= +3.0):
        nag = "$4"  # ??        
    elif (s == WHITE and v <= -1.0) or (s == BLACK and v >= +1.0):
        nag = "$2"  # ?
    elif (s == WHITE and v <= -0.25) or (s == BLACK and v >= +0.25):
        nag = "$6"  # ?!
    return nag


# Converts the uci pv to san pv
def ucipv_to_sanpv(fen, pv):
    """ Converts uci pv to SAN pv format """    
    board = chess.Board(fen)
    side = board.turn    
    # Store uci pv in a list and update the board
    # then we pop and save the move in san    
    a = pv.split(' ')
    for m in a:
        try:
            board.push_uci(m)            
        except ValueError:
            print('Illegal move')            
    # Pop the moves, and save it in SAN
    pvSan = []
    for i in range(len(a)):
        san = board.san(board.pop())
        pvSan.append(san)
    # Reverse it
    pvSan = list(reversed(pvSan))
    newPv = ' '.join(pvSan[0:])
    # We put number to our pv 1. e4 e5 2. Nf3 ...
    fmvn = fen.split(' ')
    fmvn = fmvn[-1]
    fmvn = int(fmvn)

    numPv = []
    newPvList = newPv.split(' ')
    if side == WHITE:
        for i, m in enumerate(newPvList):
            if i == 0 or i%2 == 0:  # Even
                c = fmvn + i/2
                b = str(c) + '.' + m
                numPv.append(b)
            else:
                b = m
                numPv.append(b)
    # else if side is black
    else:
        for i, m in enumerate(newPvList):
            if i == 0:
                c = fmvn
                b = str(c) + '...' + m
                numPv.append(b)
            else:
                if i%2 != 0:  # Even
                    c = fmvn + i/2 + 1
                    b = str(c) + '.' + m
                    numPv.append(b)
                else:
                    b = m
                    numPv.append(b)

    numPv = ' '.join(numPv[0:])
    return numPv      

      
def mate_distance_to_value(d):
    """ returns value given distance to mate """
    value = 0
    if d < 0:
        value = -2*d - INF
    elif d > 0:
        value = INF - 2*d + 1
    return value


def value_to_mate(value):
    """ return number of move to mate """
    d = 0
    value = int(value)
    if abs(value) < INF - MAX_PLY:
        d = 0
    else:
        if value > 0:
            d = (INF - value + 1) / 2
        elif value < 0:
            d = (-INF-value) / 2
    return d


def get_time_key(item):
    """ Sort time """
    return item[2]


def get_depth_key(item):
    """ Sort depth """
    return item[0]


def analyze_complexity(engineName, fen, _eng_option, movetimev, multipvv, nshortPv):
    """ Position is complex when the engine pv move, changes more than once """
    assert multipvv == 1
    multipv_num = multipvv
    record = []
    moveChanges = 0
    bestScore = -INF-1
    engineIsUsingBook = True
    scorev = BAD_SCORE
    
    p = subprocess.Popen(engineName, stdin=subprocess.PIPE,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT)
    p.stdin.write("uci\n")
    for eline in iter(p.stdout.readline, ''):
        eline = eline.strip()
        if "uciok" in eline:
            break

    # Send the engine options except multipv
    for n in _eng_option:
        if "multipv" in n.lower():
            pass
        else:
            p.stdin.write("setoption name %s\n" %(n))
    p.stdin.write("setoption name MultiPV value %d\n" %(multipvv))
    
    p.stdin.write("isready\n")
    for rline in iter(p.stdout.readline, ''):
        rline = rline.strip()
        if "readyok" in rline:
            break
    p.stdin.write("ucinewgame\n")
    p.stdin.write("position fen " + fen + "\n")        
    p.stdin.write("go movetime " + str(movetimev) + "\n")  # mt = movetime in ms

    # Parse engine output
    for eline in iter(p.stdout.readline, ''):
        
        a = eline.strip()

        # Process analysis output if there is depth, score and pv
        if "depth" in a and "score" in a and "pv" in a:
            engineIsUsingBook = False

            b = a.split(' ')

            i = b.index("depth")
            depthv = int(b[i+1])

            # Translate mate to value
            if "mate" in a:
                i = b.index("score")
                d2m = int(b[i+2])
                scorev = mate_distance_to_value(d2m)
            elif "score cp" in a:
                i = b.index("score")
                scorev = int(b[i+2])

            # Split at pv
            i = b.index("pv")
            c = b[i+1:]
            
            pvv = "None"

            # Shorten pv
            lenPv = len(c)

            if lenPv >= nshortPv:
                cc = b[i+1 : i+1+nshortPv]
                d = ' '.join(cc)
                pvv = d.strip()
            else:
                cc = b[i+1:]
                d = ' '.join(cc)
                pvv = d.strip()

            # Save only a single move from the pv
            singleMove = pvv.split(' ')
            singleMove = singleMove[0]

            # Record everything then sort later
            record.append([depthv, scorev, singleMove])
            
        if "bestmove" in a:
            bestScore = scorev
            break
    # Quit the engine
    p.communicate('quit\n')
    p.poll()
    if p.returncode is None:
        print('Warning!! the process has not terminated yet in analyze_complexity()')

    if engineIsUsingBook:
        assert moveChanges == 0
        return moveChanges, False
    
    # Check the move and score
    for i, item in enumerate(record):

        # Move changes, starts comparison at iteration depth equal to 9
        if item[0] >= 10:
            if record[i][2] != record[i-1][2]:
                moveChanges += 1

    mate = False
    if bestScore != -INF-1 and (bestScore >= INF - MAX_PLY) or (bestScore <= -INF + MAX_PLY):
        mate = True
    return (moveChanges, mate)


def max_depth_in_analysis(analysis_data):
    """ Find maximum depth in the list"""    
    max_depth = 0
    for item in analysis_data:
        if item[0] > max_depth:
            max_depth = item[0]            
    return max_depth


def alter_pv(pv):
    """ remove top depth pv """
    new_pv = []
    for n in pv:
        if pv[0][0] == n[0]:
            pass
        else:
            new_pv.append(n)
    return new_pv


def good_pv_depth(pv, mpv):
    """ returns true if depth of top pvs is the same """
    # For 2 pv only
    if mpv == 2:
        if pv[0][0] == pv[1][0]:
            return True
        else:
            return False
    return False


def good_pv_moves(pv):
    """ returns true if top pvs moves is not the same, applies only to 2 pv """
    pvmove1 = pv[0][4]
    pvmove1 = pvmove1.split(' ')
    pvmove1 = pvmove1[0]

    pvmove2 = pv[1][4]
    pvmove2 = pvmove2.split(' ')
    pvmove2 = pvmove2[0]

    if pvmove1 != pvmove2:
        return True
    return False


def get_summarized_pv(analysis_data, multipvv):
    """ Save the best pv lines return pv list in depth descending order """
    final_pv_list = []
    max_depth = max_depth_in_analysis(analysis_data)    
    for i in range(max_depth):
        record_depth = []

        # Parse the data and save to new list based on depth
        for item in analysis_data:
            if i+1 == item[0]:
                record_depth.append(item)

        # Sort time
        time_sorted_list = sorted(record_depth, key=get_time_key, reverse=True)

        # In temp list only save the pv with high time for multipv 1 and 2
        temp_list = []
        for j in range(multipvv):            
            ind = j + 1
            # Find the pv with this ind and high time and save it
            for n in time_sorted_list:
                if ind == n[1]:  # multipv 1 or 2
                    temp_list.append(n)
                    break        
        
        for n in temp_list:
            final_pv_list.append(n)
    
    final_pv_list = sorted(final_pv_list, key=get_depth_key, reverse=True)  
    
    # [18, 1, 2356, 3, 'e1g1 c8a6 d3a6 a8a6 f3d2 e4d2 c2d2']
    # [17, 1, 1920, 12, 'd1e2 g7g5 f4g3 f8f7 e1g1 e4g3 h2g3']
    # [17, 2, 1920, 3, 'e1g1 c8a6 d3a6 a8a6 f3d2 e4d2 c2d2']
    # [16, 1, 1654, 5, 'e1g1 c8a6 d3a6 a8a6 f3d2 e4d2 d1d2']
    # [16, 2, 1654, 0, 'd1e2 g7g5 f4g3 f8f7 e1g1 e4g3 f2g3']

    # Filter out same pv move if multipv > 1 at given depth
    if multipvv > 1:
        # Make sure that multipv is the same as num pvs at same depth
        # and pv moves among multipv are not the same
        trials = 0
        while True and len(final_pv_list) > 1:
            if trials >= 3:
                pass
            trials += 1
            if good_pv_depth(final_pv_list, multipvv):
                if good_pv_moves(final_pv_list):
                    break
                else:
                    new_pv = alter_pv(final_pv_list)
                    final_pv_list = []
                    final_pv_list = new_pv
            else:
                new_pv = alter_pv(final_pv_list)
                final_pv_list = []
                final_pv_list = new_pv
    
    return final_pv_list


def get_cerebellum_book_move(engineName, fen, _eng_option, movetimev, multipvv, nshortPv):
    """ Returns a uci move and True/False from stockfish that uses cerebellum book.
        If True the bestmove is from cerebellum book """    
    depth_cnt = 0

    # Execute the engine
    p = subprocess.Popen(engineName, stdin=subprocess.PIPE,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT)
    p.stdin.write("uci\n")
    for eline in iter(p.stdout.readline, ''):
        eline = eline.strip()
        if "uciok" in eline:
            break

    # Send the engine options except multipv
    for n in _eng_option:
        if "multipv" in n.lower():
            pass
        else:
            p.stdin.write("setoption name %s\n" %(n))
    p.stdin.write("setoption name MultiPV value %d\n" %(multipvv))
    
    p.stdin.write("isready\n")
    for rline in iter(p.stdout.readline, ''):
        rline = rline.strip()
        if "readyok" in rline:
            break
    p.stdin.write("ucinewgame\n")
    p.stdin.write("position fen " + fen + "\n")
    p.stdin.write("go movetime " + str(movetimev) + "\n")

    # Parse engine output
    for eline in iter(p.stdout.readline, ''):        
        engine_output = eline.strip()
        if "depth" in engine_output:
            depth_cnt += 1
        if "bestmove" in engine_output:
            bestmove = engine_output.split()[1]
            break
    # Quit the engine
    p.communicate('quit\n')
    p.poll()
    if p.returncode is None:
        print('Warning!! the process has not terminated yet in analyze_fen()')
    return bestmove, True if depth_cnt == 0 else False


def analyze_fen(engineName, fen, _eng_option, movetimev, multipvv, nshortPv):
    """ This will output engine analysis in a list
        and the score returned is side POV.
        Returns None if engine does not search
    """    
    multipv_num = multipvv
    record = []
    engineIsUsingBook = True

    # Execute the engine
    p = subprocess.Popen(engineName, stdin=subprocess.PIPE,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT)
    p.stdin.write(str.encode("uci\n"))
    for eline in iter(p.stdout.readline, ''):
        eline = eline.strip()
        if "uciok" in eline:
            break

    # Send the engine options except multipv
    for n in _eng_option:
        if "multipv" in n.lower():
            pass
        else:
            p.stdin.write("setoption name %s\n" %(n))
            # print('setoption name %s\n' %(n))
    p.stdin.write("setoption name MultiPV value %d\n" %(multipvv))
    
    p.stdin.write("isready\n")
    for rline in iter(p.stdout.readline, ''):
        rline = rline.strip()
        if "readyok" in rline:
            break
    p.stdin.write("ucinewgame\n")
    p.stdin.write("position fen " + fen + "\n")

    # New command so that only 1 depth will be reported
    p.stdin.write("go movetime " + str(movetimev) + "\n")

    # Parse engine output
    for eline in iter(p.stdout.readline, ''):        
        engine_output = eline.strip()

        # Process engine analysis output
        if "depth" in engine_output\
                    and ("score cp" in engine_output)\
                    or ("score mate" in engine_output)\
                    and "time" in engine_output\
                    and "pv" in engine_output\
                    and not "upperbound" in engine_output\
                    and not "lowerbound" in engine_output:
            engineIsUsingBook = False

            b = engine_output.split(' ')

            i = b.index("depth")
            depthv = int(b[i+1])
               
            if "multipv" in engine_output:
                i = b.index("multipv")
                multipvv = int(b[i+1])
            else:
                multipvv = 1
               
            i = b.index("time")
            timev = int(b[i+1])

            # Translate mate to value
            if "mate" in engine_output:
                i = b.index("score")
                d2m = int(b[i+2])
                scorev = mate_distance_to_value(d2m)
            else:
                i = b.index("score")
                scorev = int(b[i+2])

            # Split at pv
            i = b.index("pv")
            c = b[i+1:]
            
            pvv = "None"

            # Shorten pv
            lenPv = len(c)

            # If score is mate save all pv otherwise use nshortPv
            if lenPv >= nshortPv and abs(scorev) < INF-MAX_PLY:
                cc = b[i+1 : i+1+nshortPv]
                d = ' '.join(cc)
                pvv = d.strip()
            else:
                cc = b[i+1:]
                d = ' '.join(cc)
                pvv = d.strip()

            # Record everything then sort later
            record.append([depthv, multipvv, timev, scorev, pvv])
            
        if "bestmove" in engine_output:
            break
    # Quit the engine
    p.communicate('quit\n')
    p.poll()
    if p.returncode is None:
        print('Warning!! the process has not terminated yet in analyze_fen()')

    if engineIsUsingBook:
        return None

    # Save the engine analysis
    final_list = get_summarized_pv(record, multipvv)

    old_depth = 0
    return_list = []
    save_cnt = 0
    for n in final_list:        
        scorev = n[3]

        # Convert LAN pv to SAN
        san_pv = ucipv_to_sanpv(fen, n[4])
        analysis_line = ("%+0.2f/%d %s" %(float(n[3])/100, n[0], san_pv))

        # Before saving the second pv make sure that the depth of the first pv
        # is the same with the depth of the second pv
        if save_cnt == 1:
            if old_depth == n[0]:                
                return_list.append(analysis_line)
                save_cnt += 1
            else:
                # Replace the old item
                return_list[0] = analysis_line
        elif save_cnt == 0:
            return_list.append(analysis_line)
            save_cnt += 1

            if multipvv == 1:
                break
            
        if save_cnt == 2:
            break
            
        old_depth = n[0]
        
    return return_list


def get_engine_id(enginefn):
    """ Returns id name of an engine """
    engine_idname = 'Engine'
    # print(engine_idname + enginefn)
    p = subprocess.Popen(enginefn, stdin=subprocess.PIPE,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT)
    p.stdin.write(str.encode('uci\n'))
    for eline in iter(p.stdout.readline, ''):
        eline = eline.strip()
        if str.encode('id name') in eline:
            a = eline.split()
            engine_idname = ' '.join(a[2:])
        elif str.encode('uciok') in eline:
            break
        else:
            break
    engine_idname = str(eline)
    # Quit the engine
    p.communicate(str.encode('quit\n'))
    p.poll()
    if p.returncode is None:
        print('Warning!! the process has not terminated yet in get_engine_id()')
    return engine_idname


def OnlyMove(s, anaMove, gameMove, anaValue1, anaValue2):
    """ Returns true if this is the only move that is best and
        other moves are bad
        ONLY_MOVE_SCORE = 1.5 pawns
    """
    if anaMove == gameMove:
        if s == WHITE:
            if anaValue1 - anaValue2 >= ONLY_MOVE_SCORE\
                and anaValue1 >= -0.25 and anaValue1 < 3.0:
                return True
        else:
            assert s == BLACK
            if anaValue1 - anaValue2 <= -ONLY_MOVE_SCORE\
                and anaValue1 <= +0.25 and anaValue1 > -3:
                return True
    return False
           

def analyze_games(argv):
    """ argv is a list of option and values
        ['--file', 'bilbaomast16win.pgn', ...]
    """
    # Init
    sEngine = None
    pgn_file = None
    nHash = 32  # Default memory in mb
    nThreads = 1
    nMoveTime = 1000
    nMultiPv = 1
    nshortPv = 7
    startFmvn = 2
    lastFmvn = 200
    outputFN = "analyzedGame.pgn"
    gameCnt = 0
    complexityTime = 1000
    flag = 1
    option_use_book = 0
    book_fn = None
    option_add_variation_margin = 0.15  # in cp
    e_option = []
    eng_option = []
    option_player = None
    lang = 'ENG' # 'GER', 'FRA'
    option_use_cerebellum_book = 0
    option_book_anno_only = 0

    try:
        opts, args = getopt.getopt(argv, "-f", ["file=", "engine=", "movetime=",
                                               "eoption=", "startmove=",
                                               "endmove=", "bookfile=", "addvariationmargincp=",
                                               "outfile=", "player=", "lang=", 'cerebellum=',
                                               'bookannotationonly='])

        print(opts)
    except getopt.GetoptError as err:
        print(str(err))
        usage()
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-f", "--file"):
            pgn_file = arg
        elif opt in ("--outfile"):
            outputFN = arg
        elif opt in ("--engine"):
            sEngine = arg
            print(sEngine)
        elif opt in ("--player"):
            option_player = arg
        elif opt in ("--bookfile"):
            book_fn = arg
            option_use_book = 1
        elif opt in ("--movetime"):
            nMoveTime = int(arg)
        elif opt in ("--startmove"):
            startFmvn = int(arg)
        elif opt in ("--endmove"):
            lastFmvn = int(arg)
        elif opt in ("--addvariationmargincp"):
            option_add_variation_margin = int(arg)
        elif opt in ("--eoption"):
            e_option = arg.split(',')
        elif opt in ("--lang"):
            lang = arg
        elif opt in ("--cerebellum"):
            option_use_cerebellum_book = int(arg)
        elif opt in ("--bookannotationonly"):
            option_book_anno_only = int(arg)

    # Clear the engine option of whitespace chars at beginning and ending
    for n in e_option:
        n = n.strip()
        if 'Threads' in n:
            nThreads = n.split(' ')
            nThreads = int(nThreads[2])
        eng_option.append(n)

    # Exit if engine and input pgn file is missing
    if sEngine is None:
        print('Error!! engine filename was not defined')
        usage()
        sys.exit(1)
    if pgn_file is None:
        print('input pgn filename was not defined')
        usage()
        sys.exit(1)

    engine_id = get_engine_id(sEngine)
    option_add_variation_margin = float(option_add_variation_margin)/100.0

    # Send warning of book is missing
    if option_use_book and not os.path.isfile(book_fn):
        print('Warning!! the required book \"%s\" was not found' % book_fn)
        option_use_book = 0  # Set to 0
        
    complexityTime = nMoveTime

    # Open pgn file for reading
    # ifo = open(pgn_file, 'r')
    with open("game.pgn", 'r+') as f:
        ifo = f.read()
    
    game = chess.pgn.read_game(StringIO(ifo)) 
    alt_index = 0

    # Read the games in the pgn file one by one
    while game != None:
        gameCnt += 1
        maxMoveNum = GetMaxMoveNumber(game)
        Blunder = {}
        Mistake = {}
        Dubious = {}        
        Blunder['white'] = 0
        Blunder['black'] = 0
        Mistake['white'] = 0
        Mistake['black'] = 0
        Dubious['white'] = 0
        Dubious['black'] = 0

        if option_book_anno_only:
            modelGameWhite = False
            modelGameBlack = False
        else:
            modelGameWhite = True
            modelGameBlack = True            

        # Randomize alternate comment
        ALTER_COM = random_alternative(lang)

        # Save result header for writing at end of a game
        try:
            hre = game.headers['Result']
        except:
            hre = '*'

        wplayer = game.headers['White']
        bplayer = game.headers['Black']

        # Skip this game if player is not in the game
        if option_player != None and option_player != wplayer\
               and option_player != bplayer:
            game = chess.pgn.read_game(ifo)
            continue

        # A model game comment can only be added for analyzed side
        if option_player != None and option_player == wplayer:
            modelGameBlack = False
        elif option_player != None and option_player == bplayer:
            modelGameWhite = False

        # Save headers to output file
        save_headers(game, outputFN, engine_id, nThreads,
                     nMoveTime)  
        
        game_node = game
        # Loop thru the main moves and comments on this game
        while len(game_node.variations):
            side = game_node.board().turn

            fmvn = game_node.board().fullmove_number
            fmvn = int(fmvn)
            
            next_node = game_node.variation(0)
            move = next_node.move
            uci_game_move = str(move)
            
            sanMove = game_node.board().san(move)

            strFEN = str(game_node.board().fen())
            puzzleEpd = str(game_node.board().epd(bm=sanMove))

            # Show game num and fen in console
            print('Game: %d, maxMoveNum: %d' %(gameCnt, maxMoveNum))
            print('FEN: %s' %(strFEN))
            print('Player move: %s' %(sanMove))

            # Init
            threat_depth = 0
            threatValue = BAD_SCORE
            anaValue = BAD_SCORE
            anaValue2 = BAD_SCORE
            gameMoveValue = BAD_SCORE
            anaPvMove = "None"
            isOnlyMove = False
            moveChanges = 0
            writeAnalyzerBestLine = False
            matePos = False
            moveIsInPolyglotBook = False
            moveIsInCereBook = False
            anaPv2Len = 0
            
            if option_player != None and ((option_player == wplayer and not side)\
                                          or (option_player == bplayer and side)):
                with codecs.open(outputFN, 'a', 'utf8') as f:
                    if side == WHITE:
                        f.write('%d. %s ' %(fmvn, game_node.board().san(next_node.move)))
                    else:
                        f.write('%s ' %(game_node.board().san(next_node.move)))
                game_node = next_node
                continue  # Parse the next pos in this game

            # Probe polyglot book, don't analyze if a game move is in the book
            if option_use_book:
                bestPolyBookMove = None
                ployBookCnt = 0
                with chess.polyglot.open_reader(book_fn) as reader:
                    for entry in reader.find_all(game_node.board()):
                        ployBookCnt += 1
                        book_move = str(entry.move())
                        if ployBookCnt == 1:
                            bestPolyBookMove = book_move
                        if book_move == uci_game_move:
                            moveIsInPolyglotBook = True
                            break

                if moveIsInPolyglotBook:
                    with codecs.open(outputFN, 'a', 'utf8') as f:
                        if side == WHITE:
                            f.write('%d. %s {%s %s} ' %(fmvn, game_node.board().san(next_node.move),
                                                        MOVE_FROM_COMMENT[lang], book_fn))
                        else:
                            f.write('%d...%s {%s %s} ' %(fmvn, game_node.board().san(next_node.move),
                                                         MOVE_FROM_COMMENT[lang], book_fn))
                    game_node = next_node
                    continue  # Parse the next pos in this game
                
                elif bestPolyBookMove is not None:
                    with codecs.open(outputFN, 'a', 'utf8') as f:
                        tempBoard = game_node.board()
                        tempBoard.push_uci(bestPolyBookMove)
                        move = tempBoard.pop()
                        san_move = tempBoard.san(move)
                        book_comment = '%s %s %s' %(book_fn, BOOK_RECOMMENDS_COMMENT[lang], san_move)
                        if side == WHITE:
                            f.write('%d. %s {%s} ' %(fmvn, game_node.board().san(next_node.move), book_comment))
                        else:
                            f.write('%d...%s {%s} ' %(fmvn, game_node.board().san(next_node.move), book_comment))
                    game_node = next_node
                    continue                    
                
            # Use cerebellum book
            elif option_use_cerebellum_book:
                moveTimeMs = 100
                multiPVNum = 1
                pvLenNum = 1
                bestmove, validCereBook = get_cerebellum_book_move(sEngine,
                        strFEN, eng_option, moveTimeMs, multiPVNum, pvLenNum)
                if bestmove == uci_game_move and validCereBook:
                    moveIsInCereBook = True

                if moveIsInCereBook:
                    with codecs.open(outputFN, 'a', 'utf8') as f:
                        if side == WHITE:
                            f.write('%d. %s {%s cerebellum} ' %(fmvn, game_node.board().san(next_node.move), MOVE_FROM_COMMENT[lang]))
                        else:
                            f.write('%d...%s {%s cerebellum} ' %(fmvn, game_node.board().san(next_node.move), MOVE_FROM_COMMENT[lang]))
                    game_node = next_node
                    continue
                elif validCereBook:
                    with codecs.open(outputFN, 'a', 'utf8') as f:
                        tempBoard = game_node.board()
                        tempBoard.push_uci(bestmove)
                        move = tempBoard.pop()
                        san_move = tempBoard.san(move)
                        book_comment = 'Cerebellum %s %s' %(BOOK_RECOMMENDS_COMMENT[lang], san_move)
                        if side == WHITE:
                            f.write('%d. %s {%s} ' %(fmvn, game_node.board().san(next_node.move), book_comment))
                        else:
                            f.write('%d...%s {%s} ' %(fmvn, game_node.board().san(next_node.move), book_comment))
                    game_node = next_node
                    continue

            # If book annotation only
            if option_book_anno_only:
                with codecs.open(outputFN, 'a', 'utf8') as f:
                    if side == WHITE:
                        f.write('%d. %s ' %(fmvn, game_node.board().san(next_node.move)))
                    else:
                        f.write('%s ' %(game_node.board().san(next_node.move)))
                game_node = next_node
                continue  # Parse the next pos in this game

            # Analyze pos if fmvn is within startFmvn and lastFmvn input from user
            if fmvn >= startFmvn and fmvn <= lastFmvn:

                # (0) Get the score of the game move by running the engine.
                # Invert the score after the analysis since we are analyzing fen + move,
                # and invert the score if current side is black too
                # because we use white POV (point of view) and engine is analyzing at side POV

                # Use temp so we will not mess with the current board
                tempBoard = game_node.board()
                tempBoard.push(move)  # make the move on the temp board
                # Don't send position to analyze without a legal move
                if not game_node.board().is_checkmate()\
                       and not game_node.board().is_stalemate()\
                       and not tempBoard.is_checkmate()\
                       and not tempBoard.is_stalemate():
                    tFEN = str(tempBoard.fen())  
                    mpv = 1

                    # Get the score/depth pv <moves> in a list, list[0] = 1st pv,
                    # The expected return value is,
                    # "+0.89/11 32. Nc6 Nh5 33. Qf2 Qd1 34. Nb4", for nshortPv = 5
                    gameMoveAnalysisList = analyze_fen(sEngine,
                                                       tFEN,
                                                       eng_option,
                                                       nMoveTime,
                                                       mpv,
                                                       nshortPv)                    

                    # If engine does not return a search info then just write the move
                    # This happens when the engine used is using its own book
                    if gameMoveAnalysisList is None:
                        with codecs.open(outputFN, 'a', 'utf8') as f:
                            if side == WHITE:
                                f.write('%d. %s {No search output from Annotator} ' %(fmvn, game_node.board().san(next_node.move)))
                            else:
                                f.write('%d...%s {No search output from Annotator} ' %(fmvn, game_node.board().san(next_node.move)))
                        game_node = next_node
                        continue

                    gameMoveAnalysis = gameMoveAnalysisList[0]
                    
                    # The return value is from the point of view of the opponent,
                    # so we must negate it before comparing with engine analysis score
                    # gameMoveValue is in pawn unit and is of type float, it is also WPOV
                    gameMoveValue, gameMoveDepth = get_score_and_depth(gameMoveAnalysis, side)

                    # Write to console as update
                    print('Engine analysis of player move: %+0.2f/%d\n'\
                              %(gameMoveValue, gameMoveDepth))
                    
                # Analyze position to get engine recommendation

                # (1) Get complexity of the position using multipv 1,
                # use 1s or nominal search time entered by user
                if gameMoveValue != BAD_SCORE and (gameMoveValue > -0.15 and side == WHITE)\
                           or (gameMoveValue < 0.15 and side == BLACK):
                    complexityMultiPV = 1
                    moveChanges, matePos = analyze_complexity(sEngine,
                                    strFEN, eng_option,
                                    complexityTime,
                                    complexityMultiPV, nshortPv)                

                # (2) Get the engine analysis when engine is to move in this position
                if not game_node.board().is_checkmate()\
                           and not game_node.board().is_stalemate():
                    nMultiPv = 2
                    
                    # Increase engine time when move changes >= 3
                    newAllocTime = nMoveTime
                    if moveChanges >= 3:
                        newAllocTime = 3*nMoveTime

                    # If position has mate score then we extend the pv length,
                    # this is only applicable for pv1
                    pvLen = nshortPv
                    if matePos:
                        pvLen = 200  # nshortPv                
                        
                    analysisList = analyze_fen(sEngine, strFEN, eng_option,
                                    newAllocTime, nMultiPv, pvLen)

                    # If engine does not return a search info then just write the move
                    # This happens when the engine used is using its own book
                    if analysisList is None:
                        with codecs.open(outputFN, 'a', 'utf8') as f:
                            if side == WHITE:
                                f.write('%d. %s {No search output from Annotator} ' %(fmvn, game_node.board().san(next_node.move)))
                            else:
                                f.write('%d...%s {No search output from Annotator} ' %(fmvn, game_node.board().san(next_node.move)))
                        game_node = next_node
                        continue

                    # Get score, depth, and pv of the 1st pv line from multipv
                    # anaValue is white POV
                    analysisData = analysisList[0]
                    anaValue, anaDepth, anaPvMove, anaPv = get_engine_detailed_data(analysisData, side)

                    # Add model comment if there is no blunder
                    if (anaValue - gameMoveValue > MODEL_GAME_MARGIN) and side==WHITE:
                        modelGameWhite = False
                    elif (anaValue - gameMoveValue < -MODEL_GAME_MARGIN) and side==BLACK:
                        modelGameBlack = False
                    
                    # Get score, depth and pv of the 2nd pv if there is
                    # There is a possibility that a multi pv will not return 2nd pv
                    if len(analysisList) > 1:
                        analysisData2 = analysisList[1]
                        anaValue2, anaDepth2, anaPvMove2,\
                                   anaPv2 = get_engine_detailed_data(analysisData2, side)
                        
                        anaPv2List = anaPv2.split(' ')
                        anaPv2Len = len(anaPv2List)
                        # print('pv: %s, len %d' %(anaPv2, anaPv2Len))

                # If move is singular
                isOnlyMove = OnlyMove(side, anaPvMove, sanMove, anaValue, anaValue2)

                # (3) Check if analyzer best line is to be appended to the game
                # ANALYSIS_MARGIN = 10.0 pawns
                if anaPvMove == sanMove or gameMoveValue == BAD_SCORE or anaValue == BAD_SCORE\
                        or (abs(gameMoveValue) >= ANALYSIS_MARGIN and abs(anaValue) >= ANALYSIS_MARGIN)\
                        or ((anaValue - gameMoveValue < option_add_variation_margin and side == WHITE) or\
                        (anaValue - gameMoveValue > -option_add_variation_margin and side == BLACK)):
                    writeAnalyzerBestLine = False
                else:
                    writeAnalyzerBestLine = True

                    # Find the threat of the last move of opp by doing a null move
                    # from this current position. If this value is positive then
                    # the current side to move is in trouble because by doing
                    # nothing the opponent gains score. This will also detect initiative
                    if not game_node.board().is_check() and not game_node.board().is_stalemate():
                        tempBoardt = game_node.board()
                        tempBoardt.push(move.null())  # Send null move
                        tFENt = str(tempBoardt.fen())  
                        nMultiPv = 1
                        gameMoveThreatList = analyze_fen(sEngine, tFENt, eng_option,\
                                                         nMoveTime, nMultiPv, nshortPv)
                        if gameMoveThreatList is not None:
                            gameMoveThreat = gameMoveThreatList[0]
                            # gameMoveThreat = +0.00/20 27.Rc4 b6 28.Rc3 Rh1 29.a4 Rh2+ 30.Kf3
                            threatPvStr = gameMoveThreat.split(' ')
                            tpvlen = len(threatPvStr)
                            # Display odd number of moves in the pv, the first item in threatPvStr is score/depth
                            if tpvlen >= 3:
                                if tpvlen%2 == 0:
                                    threatPv = ' '.join(threatPvStr[1:])
                                else:
                                    threatPv = ' '.join(threatPvStr[1:-1])
                            else:
                                threatPv = ' '.join(threatPvStr[1:])
                            threatEval = threatPvStr[0]
                            threatEvalSplit = threatEval.split('/')
                            threatValue = float(threatEvalSplit[0])
                            threat_depth = int(threatEvalSplit[1])                            

            # (4) (a) Write singular move symbol or (b) alternative bad lines
            # or (c) good or very good move symbols to a game move
            if not writeAnalyzerBestLine:
                with codecs.open(outputFN, 'a', 'utf8') as f:
                    # If position is complex
                    if anaPvMove == sanMove and abs(anaValue) < +6.0\
                            and abs(anaValue2) < +6.0:
                        # If moveChanges is high add !! to the gameMoveNag, if low just add !
                        gameMoveNag = None
                        if moveChanges >= 5 and abs(gameMoveValue) >= +1.0:
                            gameMoveNag = '$3'
                        elif moveChanges >= 3 and abs(gameMoveValue) >= +1.0:
                            gameMoveNag = '$1'
                        writeInferiorLine = False
                        # Write inferior line if pv2 score is not too close and not too far from pv1 score
                        if (side == WHITE and anaValue - anaValue2 >= +option_add_variation_margin\
                                and anaValue - anaValue2 < (+3.0 + option_add_variation_margin)) or\
                                (side == BLACK and anaValue - anaValue2 <= -option_add_variation_margin\
                                 and anaValue - anaValue2 > (-3.0 - option_add_variation_margin)):
                            writeInferiorLine = True
                            posNag = position_nags(anaValue2)
                            gamePosNag = position_nags(gameMoveValue)
                            pv2MoveNag = one_value_move_nags(side, anaValue2)
                            if pv2MoveNag is not None:
                                # Get the move in pv2 and add a NAG
                                anaPv2Rev = anaPv2.split(' ')
                                # There must be more than 1 move in pv
                                if len(anaPv2Rev) >= 2:
                                    pv2_move = anaPv2Rev[0]
                                    pv2_move = pv2_move + ' ' + pv2MoveNag  + ' { ' + random_reason(lang) + ' } '
                                    mvRem = ' '.join(anaPv2Rev[1:-1])
                                    newAnaPv2 = pv2_move + ' ' + mvRem
                                    # Get random bad comment and append it before the pv2
                                    badComment = random_bad(lang)
                                    # Write the bad variation depends on white and black
                                    if gameMoveNag is None:
                                        if side == WHITE:
                                            f.write('%d. %s %s {%+0.2f/%d} ({%s} %s %s {%+0.2f/%d}) '\
                                                    %(fmvn, sanMove,
                                                    gamePosNag, gameMoveValue, gameMoveDepth,
                                                    badComment,
                                                    newAnaPv2, posNag, anaValue2, anaDepth2))
                                        else:
                                            f.write('%s %s {%+0.2f/%d} ({%s} %s %s {%+0.2f/%d}) '\
                                                    %(sanMove,
                                                    gamePosNag, gameMoveValue, gameMoveDepth,
                                                    badComment,
                                                    newAnaPv2, posNag, anaValue2, anaDepth2))
                                    else:
                                        if side == WHITE:
                                            f.write('%d. %s %s %s {%+0.2f/%d} ({%s} %s %s {%+0.2f/%d}) '\
                                                    %(fmvn, sanMove,
                                                    gameMoveNag, gamePosNag, gameMoveValue, gameMoveDepth,
                                                    badComment,
                                                    newAnaPv2, posNag, anaValue2, anaDepth2))
                                        else:
                                            f.write('%s %s %s {%+0.2f/%d} ({%s} %s %s {%+0.2f/%d}) '\
                                                    %(sanMove,
                                                    gameMoveNag, gamePosNag, gameMoveValue, gameMoveDepth,
                                                    badComment,
                                                    newAnaPv2, posNag, anaValue2, anaDepth2))                                
                        # if writing inferior line is not possible
                        if not writeInferiorLine or pv2MoveNag is None or len(anaPv2Rev) < 2:
                            if gameMoveNag is None:
                                if side == WHITE:
                                    f.write('%d. %s ' %(fmvn, sanMove))
                                else:
                                    f.write('%s ' %(sanMove))
                            else:
                                if side == WHITE:
                                    f.write('%d. %s %s ' %(fmvn, sanMove, gameMoveNag))
                                else:
                                    f.write('%s %s ' %(sanMove, gameMoveNag))
                    # else if easy move
                    else:
                        if isOnlyMove:
                            assert anaPvMove == sanMove
                            # $7 = Singular move comment
                            if side == WHITE:
                                f.write('%d. %s %s ' %(fmvn, sanMove, "$7"))
                            else:
                                f.write('%s %s ' %(sanMove, "$7"))
                        else:  # Write the game move only
                            if side == WHITE:
                                f.write('%d. %s ' %(fmvn, sanMove))
                            else:
                                f.write('%s ' %(sanMove))

            # Else write the pv as suggested by the engine      
            else:
                assert writeAnalyzerBestLine
                # Get position NAG for pv. The pv is a line based from engine
                PvPosNag = position_nags(anaValue)                
                # Get move NAG for game move
                assert sanMove != anaPvMove
                gameMoveNag = move_nags(side, anaValue, gameMoveValue)                
                # Get position NAG for position after this game move
                gamePosNag = position_nags(gameMoveValue)
                # Select a comment based on difference between engine score and game move score
                goodComment = get_good_comment(anaValue, gameMoveValue, side, lang)
                with codecs.open(outputFN, 'a', 'utf8') as f:
                    # If game move pos assessment is a mate due to perhaps of
                    # a blunder then show +/-M, instead of score/depth
                    move_score_val = "%+0.2f" % gameMoveValue
                    posGameMoveComment = str(move_score_val) + '/' + str(gameMoveDepth)                  
                    if (int(100*gameMoveValue) >= INF-MAX_PLY) or (int(100*gameMoveValue) <= -INF+MAX_PLY):
                        assert gameMoveValue != BAD_SCORE
                        num_mate = value_to_mate(100*gameMoveValue)
                        assert num_mate != 0
                        smate = mate_indicator(num_mate)
                        posGameMoveComment = smate
                    # If pv1 score is a mate then show +/-M, instead of score/depth
                    pv1_score_val = "%+0.2f" % anaValue
                    posPv1Comment = str(pv1_score_val) + '/' + str(anaDepth)
                    pv1MateScore = False
                    if (int(100*anaValue) >= INF-MAX_PLY and side == WHITE) or\
                               (int(100*anaValue) <= -INF+MAX_PLY and side == BLACK):
                        assert anaValue != BAD_SCORE
                        num_mate = value_to_mate(100*anaValue)
                        assert num_mate != 0
                        smate = mate_indicator(num_mate)                        
                        posPv1Comment = smate
                        pv1MateScore = True                      
                    # Break down the pv to get the first move
                    pv1_split = anaPv.split(' ')
                    # Get the first move in the pv including the move number
                    pv1_move = pv1_split[0]
                    # Insert the pv1_move_nag after the first move
                    if pv1MateScore:
                        new_mv = pv1_move + ' ' + '{with mate attack} '
                    else:
                        new_mv = pv1_move + ' '
                    # Reconstruct the pv line
                    new_anaPv = new_mv + ' '.join(pv1_split[1:])
                    # Write the game move and pv variation
                    if side == WHITE:
                        if pv1MateScore:
                            if gameMoveNag is None:
                                f.write('\n%d. %s %s {%s} ({%s} %s %s) '\
                                        %(fmvn, game_node.board().san(next_node.move),
                                        gamePosNag, posGameMoveComment,
                                        goodComment, new_anaPv, PvPosNag))
                            else:
                                f.write('\n%d. %s %s %s {%s} ({%s} %s %s) '\
                                    %(fmvn, game_node.board().san(next_node.move), gameMoveNag,
                                    gamePosNag, posGameMoveComment,
                                    goodComment, new_anaPv, PvPosNag))
                        else:
                            if gameMoveNag is None:
                                f.write('\n%d. %s %s {%s} ({%s} %s %s {%s}) '\
                                    %(fmvn, game_node.board().san(next_node.move),
                                    gamePosNag, posGameMoveComment,
                                    goodComment, new_anaPv, PvPosNag, posPv1Comment))
                            else: 
                                f.write('\n%d. %s %s %s {%s} ({%s} %s %s {%s}) '\
                                        %(fmvn, game_node.board().san(next_node.move), gameMoveNag,
                                        gamePosNag, posGameMoveComment,
                                        goodComment, new_anaPv, PvPosNag, posPv1Comment))
                    else:  # side is black
                        if pv1MateScore:
                            if gameMoveNag is None:
                                f.write('\n%d... %s %s {%s} ({%s} %s %s) '\
                                        %(fmvn, game_node.board().san(next_node.move),
                                        gamePosNag, posGameMoveComment,
                                        goodComment, new_anaPv, PvPosNag))
                            else:
                                f.write('\n%d... %s %s %s {%s} ({%s} %s %s) '\
                                        %(fmvn, game_node.board().san(next_node.move), gameMoveNag,
                                        gamePosNag, posGameMoveComment,
                                        goodComment, new_anaPv, PvPosNag))
                        else:
                            if gameMoveNag is None:                                    
                                f.write('\n%d... %s %s {%s} ({%s} %s %s {%s}) '\
                                        %(fmvn, game_node.board().san(next_node.move),
                                        gamePosNag, posGameMoveComment,
                                        goodComment, new_anaPv, PvPosNag, posPv1Comment))
                            else:
                                f.write('\n%d... %s %s %s {%s} ({%s} %s %s {%s}) '\
                                    %(fmvn, game_node.board().san(next_node.move), gameMoveNag,
                                    gamePosNag, posGameMoveComment,
                                    goodComment, new_anaPv, PvPosNag, posPv1Comment))

                    # If the game move is not the same to that of pv2 move then write it as variation,
                    # depending on the pv2 score and game move score
                    if anaPvMove2 != sanMove and anaValue2 != BAD_SCORE and anaPv2Len >= 2:                        
                        # Get pos nag of pv2
                        pv2PosNag = position_nags(anaValue2)
                        
                        # If pv2 score is equal or better than the game move score then write
                        # it as a playable alternative line
                        if (side == WHITE and anaValue2 >= gameMoveValue) or\
                                   (side == BLACK and anaValue2 <= gameMoveValue):
                            if (side == WHITE and anaValue2 >= -ONLY_MOVE_SCORE) or\
                                       (side == BLACK and anaValue2 <= +ONLY_MOVE_SCORE):
                                
                                # If pv1 showed that this has a mate score then check
                                # if pv2 is also showing mate score, otherwise cut the pv2 length
                                # to nshortPv = 7 plies, as we know we extend the pv length
                                # when there is a mate score from pv1
                                if (int(100*anaValue2) >= INF-MAX_PLY and side == WHITE) or\
                                       (int(100*anaValue2) <= -INF+MAX_PLY and side == BLACK):

                                    # Convert score to mate number
                                    num_mate = value_to_mate(100*anaValue2)
                                    assert num_mate != 0
                                    smate = mate_indicator(num_mate)
                                    posPv2Comment = smate
                                    com_val, alt_index = get_alternative_comment(ALTER_COM, alt_index, lang)
                                    f.write('\n({ %s } %s %s {%s}) '\
                                            %(com_val, anaPv2, pv2PosNag, posPv2Comment))
                                else:
                                    
                                    # Else if not mate score Reduce the pv length to nshortPv = 7 plies (default)
                                    new_ana_pv2 = anaPv2.split(' ')
                                    new_ana_pv2 = ' '.join(new_ana_pv2[:nshortPv])
                                    com_val, alt_index = get_alternative_comment(ALTER_COM, alt_index, lang)
                                    f.write('\n({ %s } %s %s {%+0.2f/%d}) '\
                                        %(com_val, new_ana_pv2, pv2PosNag, anaValue2, anaDepth2))
                        # else if pv2MoveScore < gameMoveScore
                        else:
                            # Add move nag to the first move of pv2
                            anaPv2MoveNag = one_value_move_nags(side, anaValue2)
                            if anaPv2MoveNag is not None:                                
                                # new_ana_pv2 = anaPv2.split(' ')
                                anaPv2List = anaPv2.split(' ')
                                anaPv2WithReason = anaPvMove2 + ' %s { %s } ' % (anaPv2MoveNag, random_reason(lang))
                                # Cut 1 ply at end of pv, to emphasize that the other side is the last mover
                                newAnaPv2 = anaPv2WithReason + ' '.join(anaPv2List[1:-1])
                                badComment = random_bad(lang)
                                f.write('\n({ %s } %s %s {%+0.2f/%d}) '\
                                        %(badComment,
                                          newAnaPv2, pv2PosNag, anaValue2, anaDepth2))
                    # Print the threat pv if score of opponent or last move is good
                    if threatValue > 0.0 and threatValue != BAD_SCORE:                        
                        # Translate threatValue to white pov
                        # Use side == WHITE because we do a null move
                        wpov_threatValue = threatValue
                        if side == WHITE:
                            wpov_threatValue = -1*threatValue
                        if int(100*threatValue) >= +INF-MAX_PLY:
                            num_mate = value_to_mate(100*threatValue)
                            if side == WHITE:
                                f.write('\n({%s %d} %d. %s %s) '\
                                        %(BLACK_MATE_THREAT_COMMENT[lang], abs(num_mate), fmvn, '--', threatPv))
                            else:
                                f.write('\n({%s %d} %d... %s %s) '\
                                        %(WHITE_MATE_THREAT_COMMENT[lang], abs(num_mate), fmvn, '--', threatPv))
                        else:
                            posNag = position_nags(wpov_threatValue)
                            if side == WHITE:
                                f.write('\n({%s} %d. %s %s %s {%+0.2f/%d}) '\
                                        %(BLACK_THREAT_COMMENT[lang], fmvn, '--',
                                          threatPv, posNag, wpov_threatValue, threat_depth))
                            else:
                                f.write('\n({%s} %d... %s %s %s {%+0.2f/%d}) '\
                                        %(WHITE_THREAT_COMMENT[lang], fmvn, '--',
                                          threatPv, posNag, wpov_threatValue, threat_depth))

            # Record blunders and mistakes for summary       
            if anaPvMove != sanMove and writeAnalyzerBestLine:
                mnag = move_nags(side, anaValue, gameMoveValue)
                # $4=??, $2=?, $6=?!
                if side and mnag == '$4':
                    Blunder['white'] += 1
                elif side and mnag == '$2':
                    Mistake['white'] += 1
                elif side and mnag == '$6':
                    Dubious['white'] += 1

                elif not side and mnag == '$4':
                    Blunder['black'] += 1
                elif not side and mnag == '$2':
                    Mistake['black'] += 1
                elif not side and mnag == '$6':
                    Dubious['black'] += 1

            game_node = next_node  # Read next position of this game

        # Print result at the end of notation
        with codecs.open(outputFN, 'a', 'utf8') as output_fo:
            # Add mode game comment only when all moves are analyzed
            if lastFmvn >= maxMoveNum:
                if modelGameWhite and modelGameBlack:
                    output_fo.write('{%s}\n' %(WHITE_BLACK_MODEL_COMMENT[lang]))
                elif modelGameWhite:
                    output_fo.write('{%s}\n' %(WHITE_MODEL_COMMENT[lang]))
                elif modelGameBlack:
                    output_fo.write('{%s}\n' %(BLACK_MODEL_COMMENT[lang]))
            # output_fo.write('{WhiteBlunder: %d, BlackBlunder: %d}\n' %(Blunder['white'], Blunder['black']))
            output_fo.write('{WBlunder: %d, WMistake: %d, WDubious: %d, BBlunder: %d, BMistake: %d, BDubious: %d} %s\n\n'\
                            %(Blunder['white'], Mistake['white'], Dubious['white'],
                              Blunder['black'], Mistake['black'], Dubious['black'], hre))

        game = chess.pgn.read_game(ifo)  # Read next game of the pgn file

    ifo.close()

    print("\nDone!!")


def newMain():
    engine = chess.engine.SimpleEngine.popen_uci("/Users/rli233/Documents/stockfish-10-64")
    board = chess.Board("3r2k1/pp3p2/1b3P2/6B1/6n1/1BNr4/PP5P/3R1R1K w - - 9 28")
    # info = engine.analyse(board, chess.engine.Limit(depth=20))
    # print(engine.play(board, chess.engine.Limit(depth=20)).ponder)
    # print(engine.play(board, chess.engine.Limit(depth=20)).info )
    with engine.analysis(board) as analysis:
        for info in analysis:
            print(info.get("pv"))

            # Arbitrary stop condition.
            if info.get("seldepth", 0) > 20:
                break

    # engine.quit()
    # print("Score:", info["score"])
    # Score: #1

    engine.quit() 

    return 0 

def main(argv):
    """ start """
    print(APP_NAME + ' v' + APP_VERSION + '\n')
    # argv is a list of option and values
    # ['--file', 'bilbaomast16win.pgn',
    # '--engine', 'stockfish_120716_x64_modern.exe',
    # '--eoption', 'Hash value 128, Threads value 1']
    # analyze_games(argv)
    newMain() 

if __name__ == "__main__":
    main(sys.argv[1:])
