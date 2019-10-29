FROM ubuntu:14.04
ADD test/ /root/test
ADD app/ /root/app
ADD index.html /root/index.html
CMD /root/app/websocketd --port=3000 --staticdir=/root  /root/app/stockfish_10_x64 

