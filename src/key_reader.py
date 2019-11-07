from threading import Thread,Lock
import keyboard

class InputReader (Thread):

    def __init__(self, key):
        Thread.__init__(self)
        self.read_key = key
        self.alive = True

    def run(self):
        while self.alive:
            self.read_key = keyboard.read_key()

