BEARSSL ?= $(abspath .bearssl)
CFLAGS  += -O2 -Wall -I../lib/hea_proto -I$(BEARSSL)/inc -I$(BEARSSL)/src
SRC = host_test.c ../lib/hea_proto/hea_proto.c
# build only the BearSSL sources we need (hash, kdf, mac, symcipher, aead)
BSRC = $(wildcard $(BEARSSL)/src/hash/*.c $(BEARSSL)/src/kdf/*.c $(BEARSSL)/src/mac/*.c \
        $(BEARSSL)/src/symcipher/aes_ct*.c $(BEARSSL)/src/aead/*.c $(BEARSSL)/src/codec/*.c \
        $(BEARSSL)/src/int/*.c)
host_test: $(BEARSSL)/inc/bearssl.h $(SRC)
	$(CC) $(CFLAGS) -o $@ $(SRC) $(BSRC)
clean:
	rm -f host_test

# BearSSL as shipped in the ESP8266 Arduino core (same sources the board runs)
$(BEARSSL)/inc/bearssl.h:
	git clone --depth 1 https://github.com/earlephilhower/bearssl-esp8266.git $(BEARSSL)
