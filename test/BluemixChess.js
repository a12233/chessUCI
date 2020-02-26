// Get a reference to the 'status' span to make status updates
var statusSpan = $('#status');

// Keep track of who is controlling each side
var blackBrain = 'bStockfish';
var whiteBrain = 'human';

// Thinking time for Stockfish (seconds)
var thinkingTime = 1;
var blackTime = 1;
var whiteTime = 1;
var uciOk = false;
var isReady = false;
var thinking = false; 
var wasmSupported = typeof WebAssembly === 'object' && WebAssembly.validate(Uint8Array.of(0x0, 0x61, 0x73, 0x6d, 0x01, 0x00, 0x00, 0x00));
var stockfishRespose; 

var game = new Chess();

var stockfish = new Worker(wasmSupported ? 'stockfish.wasm.js' : 'stockfish.js');

function log(msg) {
  document.getElementById('log').textContent += msg + '\n';
}

stockfish.addEventListener('message', function(event){
  if (event.data === 'uciok') {
    uciOk = true;
    // Turn off ponder
    stockfish.postMessage('setoption name Ponder value false');
    // Ask the engine if it's ready
    stockfish.postMessage('isready');
  }

  // Wait for 'readyok' response from the engine
  if (event.data === 'readyok') {
    isReady = true;
  }

  if (uciOk && isReady) {
    // Send the game position in FEN
    if( thinking == false ){
      stockfish.postMessage('position fen ' + game.fen());
      // Ask for the next move (think about it for a while)
      stockfish.postMessage('go movetime ' + thinkingTime * 1000);
      thinking = true; 
    }
    
    if (event.data.search(/^bestmove/) !== -1) {
      var move = event.data;
      console.log(move)
      // Extract just the move itself
      move = move.substring(move.indexOf(' ') + 1);
      if (move.indexOf(' ') !== -1) {
        move = move.substring(0, move.indexOf(' '));
      }

      // Make the move
      game.move({ from: move.substring(0, 2), to: move.substring(2, 4) });

      // Trigger onSnapEnd event so everything happens as if a human moved
      onSnapEnd(true);
      thinking = false 
    }
  }
  // log('MESSAGE: ' + event.data);
});

// Use chess.js for valid move determination

// Execute a move using Stockfish
var moveStockfish = function() {
  stockfish.postMessage('uci');
};

// Make the engine play (if appropriate)
var enginePlays = function() {
  // Don't play if the game is over
  if (!game.game_over()) { 
    // Is the computer playing now?
    if (game.turn() === 'w' && whiteBrain !== 'human') {
          moveStockfish(whiteTime);
      }
    else if (game.turn() === 'b' && blackBrain !== 'human') { 
      moveStockfish(blackTime);
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
