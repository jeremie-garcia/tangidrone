from oscpy.server import OSCThreadServer
import math
from time import sleep

class riot_osc():

    def __init__(self, cf = None):
        self.osc = OSCThreadServer()
        self.euler_x = 0
        self.euler_y = 0
        self.euler_z = 0
        self.ante_x = 0
        self.angle = 0
        self.count = 0
        
        self.orig_x = 0
        self.orig_z = 0

        self.cf = cf
        self.flag = False
        self.sock = 0

    def _normalize__(self, value, orig):
        value = round(value)
        if value < 0:
            value = 360 + value
        value -= orig
        if value < 0 : value += 360
        return value

    def set_orig(self, *args):
        self.orig_x = self._normalize__(args[18],0)
        self.orig_z = self._normalize__(args[20],0)
        print(self.orig_x, self.orig_z)

    def callback(self, *args):
        try:
            self.euler_y = round(args[19])
        except:
            self.euler_y = -90
        if self.euler_y<-75:
            self.callback_z(*args)
        else:
            self.callback_x(*args)

    def callback_z(self, *args):
        self.euler_z = self._normalize__(args[20], self.orig_z)
        print("euler_z = ",self.euler_z)
        
    def callback_x(self, *args):
        self.euler_x = self._normalize__(args[18],self.orig_x)
        angle = self.euler_x - self.ante_x
        if abs(angle) >= 180 :
            n_angle = angle % 180
            angle = n_angle if angle > 0 else -angle
        if angle != 0:
            self.flag = True
            self.angle += angle
        else:
            if self.flag : self.count += 1
        if self.count == 20:
            if self.cf != None :
                if self.angle <= 0:
                    self.cf.turn_left(abs(self.angle), 180)
                else:
                    self.cf.turn_right(self.angle, 180)
            self.count = 0
            self.angle = 0
            self.flag = False
        print("euler_x = ",self.euler_x," euler_y = ", self.euler_y)
        self.ante_x = self.euler_x

    def sock_connect(self):
        self.sock = self.osc.listen(address='0.0.0.0', port=8000, default=True)

    def get_x(self):
        try:
            self.sock_connect()
            self.osc.bind(b'/0/raw',self.set_orig)
            sleep(0.02)
            self.osc.unbind(b'/0/raw',self.set_orig)
            for i in range(50):
                self.osc.bind(b'/0/raw',self.callback)
                sleep(0.5)
        except KeyboardInterrupt:
            self.osc.stop_all()
            print('stopped all for keyboard interupt')

    def stop(self):
        self.osc.stop(self.sock)
        print("Stopped OCS")
