from threading import Thread,Lock
import time
import keyboard

class globalVars():
    pass

G = globalVars() #empty object to pass around global state
G.lock = Lock() #not really necessary in this case, but useful none the less
G.key = None
G.kill = False

def foo(n): #function doing intense computation
    while True:
        if G.kill:
            G.kill = False
            return
        with G.lock:
            print(G.key)

t = Thread(target=foo, args=(10,))
t.start()

def askinput():
    G.key = keyboard.read_key()
    return 1

while askinput():
    pass