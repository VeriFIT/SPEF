CC=g++
CFLAGS= -lncurses -Wall
BIN=ncurses
SRC=ncurses
ZIP= *.cpp *.h Makefile

$(SRC): $(SRC).o
	$(CC) $(CFLAGS) $(SRC).o -o $(BIN) 

$(SRC).o:
	$(CC) -c $(SRC).cpp 

run: $(SRC)
	make clean && make && ./$(SRC)

clean:
	rm $(BIN) *.o

zip:
	zip -j xdizov00.zip $(ZIP)