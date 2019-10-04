from oscpy.server import OSCThreadServer
from time import sleep

class riot_osc():

    def __init__(self, cf):
        self.osc = OSCThreadServer()
        self.euler_x = 0
        self.ante_x = 0
        self.angle = 0
        self.count = 0
        self.cf = cf
        self.sock = 0

    def callback_x(self, *args):
        self.euler_x = round(args[18])
        if self.euler_x < 0:
            self.euler_x = 360 + self.euler_x
        angle = self.euler_x - self.ante_x
        if angle == 0:
            self.count += 1
        else:
            self.angle += angle
        if self.count == 20:
            print("YES")
            if self.angle <= 0:
                self.cf.turn_left(abs(self.angle), 180)
            else:
                self.cf.turn_right(self.angle, 180)
            self.count = 0
            self.angle = 0
        print(self.euler_x, self.ante_x, angle)
        self.ante_x = self.euler_x

    def get_x(self):
        try:
            self.sock = self.osc.listen(address='0.0.0.0', port=8000, default=True)
            for i in range(50):
                self.osc.bind(b'/0/raw',self.callback_x)
                sleep(0.5)
        except KeyboardInterrupt:
            self.osc.stop_all()
            print('stopped all for keyboard interupt')

    def stop(self):
        self.osc.stop(self.sock)
        print("Stopped OCS")