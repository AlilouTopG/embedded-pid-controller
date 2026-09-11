CC = gcc
CFLAGS = -Wall -Wextra -Iinclude -O2
SRC = src/main.c src/pid.c
TARGET = build/pid_sim

all: clean $(TARGET)

$(TARGET):
	@mkdir -p build
	$(CC)$(CFLAGS) $(SRC) -o$(TARGET)

run: $(TARGET)
	./$(TARGET)

clean:
	rm -rf build
