// Get a reference to the 'status' span to make status updates
var statusSpan = $('#status');

// Keep track of who is controlling each side
var blackBrain = 'human';
var whiteBrain = 'human';

// Thinking time for Stockfish (seconds)
var blackTime = 1;
var whiteTime = 1;

// Populate with the IP address of your Stockfish Container
var HOST = location.origin.replace(/^http/, 'ws');
var stockfishEndpoint = HOST+":"+"3000"

// Use chess.js for valid move determination
var game = new Chess();

// Execute a move using Stockfish
var moveStockfish = function(thinkingTime) {
  var uciOk = false;
  var isReady = false;

    // setup websocket with callbacks
    var HOST = location.origin.replace(/^http/, 'ws')
    var sock = new ReconnectingWebSocket(HOST);

  // Send 'uci' to init the engine (once the WebSocket connection opens)
  sock.onopen = function() {
    sock.send('uci');
  };

  // Handle input from the WebSocket
  sock.onmessage = function(event) {
    if (!uciOk || !isReady) {
      // Wait for 'uciok' response from the engine
      if (event.data === 'uciok') {
        uciOk = true;

        // Turn off ponder
        sock.send('setoption name Ponder value false');

        // Ask the engine if it's ready
        sock.send('isready');
      }

      // Wait for 'readyok' response from the engine
      if (event.data === 'readyok') {
        isReady = true;
      }

      if (uciOk && isReady) {
        // Send the game position in FEN
        sock.send('position fen ' + game.fen());

        // Ask for the next move (think about it for a while)
        sock.send('go movetime ' + thinkingTime * 1000);
      }
    }
    else {
      // Wait for 'bestmove' response
      if (event.data.search(/^bestmove/) !== -1) {
        var move = event.data;

        // Got what we need - close the WebSocket
        sock.close();

        // Extract just the move itself
        move = move.substring(move.indexOf(' ') + 1);
        if (move.indexOf(' ') !== -1) {
          move = move.substring(0, move.indexOf(' '));
        }

        // Make the move
        game.move({ from: move.substring(0, 2), to: move.substring(2, 4) });

        // Trigger onSnapEnd event so everything happens as if a human moved
        onSnapEnd(true);
      }
    }
  };
};

// Execute a move using chess.js
var moveChessJS = function() {
  // Pick a random move from all legal moves
  var moves = game.moves();
  var move = moves[Math.floor(Math.random() * moves.length)];
  game.move(move);

  // Trigger onSnapEnd event so everything happens as if a human moved
  onSnapEnd(true);
};

// Make the engine play (if appropriate)
var enginePlays = function() {
  // Don't play if the game is over
  if (!game.game_over()) {
    // Is the computer playing now?
    if (game.turn() === 'w' && whiteBrain !== 'human') {
      switch(whiteBrain) {
        case 'stockfish':
          moveStockfish(whiteTime);
          break;
        case 'chess.js':
          moveChessJS();
          break;
      }
    }
    else if (game.turn() === 'b' && blackBrain !== 'human') {
      switch(blackBrain) {
        case 'stockfish':
          moveStockfish(blackTime);
          break;
        case 'chess.js':
          moveChessJS();
          break;
        }
    }
  }
};

// Update status span with current game state
var updateStatus = function() {
  var status = '';

  var moveColor = 'White';
  if (game.turn() === 'b') {
    moveColor = 'Black';
  }

  // Is the game over?
  if (game.in_checkmate() === true) {
    // Checkmake!
    status = 'Game over, ' + moveColor + ' is in checkmate.';
  }
  else if (game.in_draw() === true) {
    // Draw
    status = 'Game over, drawn position';
  }
  else {
    // Game still in progress
    if ((game.turn() === 'w' && whiteBrain !== 'human') || (game.turn() === 'b' && blackBrain !== 'human')) {
      status = moveColor + ' is thinking';
    }
    else {
      status = moveColor + ' to move';
    }

    // Check?
    if (game.in_check() === true) {
      status += ', ' + moveColor + ' is in check';
    }
  }

  statusSpan.html(status);
};

// Called when dragging begins
var onDragStart = function(source, piece, position, orientation) {
  // Do not pick up pieces if the game is over
  if (game.game_over() === true) {
     return false;
  }

  // Only allow the player who's turn it is to move
  if ((game.turn() === 'w' && piece.search(/^b/) !== -1) || (game.turn() === 'b' && piece.search(/^w/) !== -1)) {
    return false;
  }

  // Don't allow moving of computer controlled pieces
  if ((game.turn() === 'w' && whiteBrain !== 'human') || ((game.turn() === 'b' && blackBrain !== 'human'))) {
    return false;
  }
};

// Called whenever a piece is dropped
var onDrop = function(source, target, piece, newPos, oldPos, orientation) {
  // See if the move is legal
  var move = game.move({
    from: source,
    to: target,
    promotion: 'q'
  });

  if (move === null) {
    // Illegal move
    return 'snapback';
  }
};

// Called when piece snap animation is complete
var onSnapEnd = function(delay) {
  // Update the board position for castling, en passant, pawn promotion
  board.position(game.fen());

  // Update the status line
  updateStatus();

  // Let the computer have a chance to play
  if (delay) {
    setTimeout(enginePlays, 1000);
  }
  else {
    enginePlays();
  }
};

// Chessboard config options
var cfg = {
  draggable: true,
  position: 'start',
  onDragStart: onDragStart,
  onDrop: onDrop,
  onSnapEnd: onSnapEnd
};
// Use chessboard.js for the board UI
var board = ChessBoard('board', cfg);
// Set initial status
updateStatus();

// Handle when one of the brain selection forms changes
$(document).ready(function() {
  $("input[name='blackBrain']").change(function() {
    blackBrain = $(this).val();
    updateStatus();
    enginePlays();
  });
  $("input[name='whiteBrain']").change(function() {
    whiteBrain = $(this).val();
    updateStatus();
    enginePlays();
  });

  $("input[name='blackTime']").change(function() {
    blackTime = $(this).val();
  });
  $("input[name='whiteTime']").change(function() {
    whiteTime = $(this).val();
  });
});
