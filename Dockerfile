FROM ubuntu:14.04
ADD websocketd /root/websocketd
ADD stockfish_10_x64 /root/stockfish_10_x64
EXPOSE 3000
CMD /root/websocketd --port=3000 /root/stockfish_10_x64

