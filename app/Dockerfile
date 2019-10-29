FROM ubuntu:14.04
ADD websocketd /root/websocketd
ADD stockfish_10_x64 /root/stockfish_10_x64
ADD index.html /root/app/index.html
CMD /root/websocketd --port=$PORT --staticdir=/root/app  /root/stockfish_10_x64 
# CMD /root/websocketd --port=$PORT/root/stockfish_10_x64


