from oscpy.server import OSCThreadServer
import math
import key_reader
import keyboard
from threading import Thread,Lock
import matplotlib.pyplot as plt
import dyn_plot_ex
from time import sleep

class riot_osc():

    def __init__(self, multiranger, motion_commander, cf = None, to_alt = 0.5, graph = False):
        self.osc = OSCThreadServer()
        #les valeurs d'angle renvoyée par la centrale gyroscopique sur les 3 axes
        self.euler_x = 0
        self.euler_y = 0
        self.euler_z = 0
        #les angles renvoyés lors du signal précedent
        self.ante_x = 0
        self.ante_z = 0
        self.ante_y = 0
        #la valeur d'angle de la commande pour faire tourner le drone
        self.angle = 0
        #compte le nombre de fois où la différence entre la valeur d'angle recu et la valeur précédente, 
        #pour éviter de surcharger le drone de commande
        self.count = 0
        #booléen renseignant sur l'état du drone : en vol ou non
        self.keep_flying = True 

        #altitude du drone
        self.z = to_alt

        #vitesse d'évitement initiale du drone
        self.velocity = 0.5

        self.reader_thread = key_reader.InputReader("x")

        #initialisation des valeurs d'angle sur x et z au commencement du programme
        self.orig_x = 0
        self.orig_z = 0

        #variables propres au drones
        self.cf = cf
        self.multiranger = multiranger
        self.motion_commander = motion_commander

        #variable indiquant si le programme doit commencer à compter (ou pas) le nombre
        #de valeur d'angle non nul 
        self.flag = False
        self.sock = 0

        #Initialisation du thread_multirange
        #ATTENTION A DES POSSIBLES PROBLEMES, LE DRONE EST SUREMENT UNE RESSOURCE CRITIQUE
        self.thread_multirange = Thread(target = self.multirange_push)
        self.thread_multirange.start()

    def _normalize__(self, value, orig):
        value = round(value)
        if value < 0:
            value = 360 + value
        value -= orig
        if value < 0 : value += 360
        return value

    def set_orig(self, *args, axes = "all"):
        if axes == "all" or axes == "x": 
            self.orig_x = self._normalize__(args[18],0)
        if axes == "all" or axes == "z": 
            self.orig_z = self._normalize__(args[20],0)

        self.osc.unbind(b'/0/raw',self.set_orig)
        self.osc.bind(b'/0/raw',self.callback)

    def callback(self, *args):
        if self.graph : self.plot()
        self.euler_z = self._normalize__(args[20], self.orig_z)
        try:
            self.euler_y = round(args[19])
        except:
            self.euler_y = -90
        #print(self.euler_x, self.euler_y, self.euler_z)
        if abs(self.euler_z) <= 10 and abs(self.euler_y) <= 10:
            #print("ca marche bizarre")
            self.callback_x(*args)
        elif abs(self.euler_z - 90) <= 10  and abs(self.euler_y) <= 10:
            self.landing()
            #print("attero")
        elif abs(self.euler_z - 270) <= 10 and abs(self.euler_y) <= 10:
            #print("vitesse")
            self.set_velocity(*args)
        elif abs(self.euler_z - 180) <= 15 and abs(self.euler_y) <= 12:
            #print("rien")
            self.idle()
        elif abs(self.euler_y - 90) <= 10:
            #print("oui")
            self.callback_z(*args)
        elif abs(self.euler_y + 90) <= 20:
            #peut etre faire un mode de commande manuel, avec le clavier et à terme  la manette
            #print("manuel")
            self.manual_control()
        else:
            #sleep(0.1)
            pass
        

    def landing(self):
        """
        A modifier par le code suivant si le on peut enlever le contexte du motion commander:
        self.cf.land(0.2)
        self.keep_flying = False
        """
        print("appuyer sur espace quelque seconde pour atterrir et ensuite arrêter le drone")
        if keyboard.is_pressed("space"):
            self.keep_flying = False
            print("Atterrissage...")
        

    def idle(self):
        print("idle...")
        pass

    def set_velocity(self, *args):
        self.euler_x = self._normalize__(args[18],self.orig_x)
        angle = self.euler_x - self.ante_x
        if abs(angle) >= 180 :
            n_angle = angle % 180
            angle = n_angle if angle > 0 else -n_angle
        if angle != 0 :
            delta = angle/360
            if delta <= self.velocity: self.velocity += delta
            print("La vitesse d'évitement est maintenant de = ", self.velocity, " m/s. ", angle)
        self.ante_x = self.euler_x
        #print(self.euler_y, self.euler_x)
        
    def callback_z(self, *args):
        self.euler_x = self._normalize__(args[18],self.orig_x)
        angle = self.euler_x - self.ante_x
        if abs(angle) >= 180 :
            n_angle = angle % 180
            angle = n_angle if angle > 0 else -n_angle
        if angle != 0:
            self.flag = True
            self.angle += angle
        else:
            if self.flag : self.count += 1
        if self.count == 10:
            if self.cf != None :
                if abs(self.angle) > 0:
                    if self.angle <= 0:
                        self.motion_commander.down(abs(self.angle)/360,0.5)
                        self.z -= abs(self.angle)/360
                        if self.z < 0.15:
                            self.keep_flying = False
                    else:
                        self.motion_commander.up(self.angle/720,0.5)
                        self.z += abs(self.angle)/360
            self.count = 0
            self.angle = 0
            self.flag = False
        self.ante_x = self.euler_x
        
    def callback_x(self, *args):
        self.euler_x = self._normalize__(args[18],self.orig_x)
        angle = self.euler_x - self.ante_x
        if abs(angle) >= 180 :
            n_angle = angle % 180
            angle = n_angle if angle > 0 else -n_angle
        if angle != 0:
            self.flag = True
            self.angle += angle
        else:
            if self.flag : self.count += 1
        if self.count == 10:
            if self.cf != None :
                if abs(self.angle) > 0:
                    if self.angle >= 0:
                        self.motion_commander.turn_left(abs(self.angle), 180)
                    else:
                        self.motion_commander.turn_right(abs(self.angle), 180)
            self.count = 0
            self.angle = 0
            self.flag = False
        #print("angle = ", self.angle)
        self.ante_x = self.euler_x

    def sock_connect(self):
        self.sock = self.osc.listen(address='0.0.0.0', port=8000, default=True)

    def get_x(self):
        self.reader_thread.start()
        #if self.cf != None : self.cf.take_off(self.z,0.5)
        try:
            self.sock_connect()
            self.osc.bind(b'/0/raw',self.set_orig)
            #sleep(0.02)
            

            print(self.keep_flying)
            while self.keep_flying:
                
                sleep(0.05)
        except KeyboardInterrupt:
            self.osc.stop_all()
            print('stopped all for keyboard interupt')
        self.reader_thread.alive = False
        self.reader_thread.join()
        self.thread_multirange.join()

    def plot(self):
        self.d_graph(self.x, self.y, self.z)


    def stop(self):
        self.osc.stop(self.sock)
        print("Stopped OCS")

    def multirange_push(self):
        def is_close(range):
            MIN_DISTANCE = 0.2  # m
            if range is None:
                return False
            else:
                return range < MIN_DISTANCE


        while self.keep_flying:
            velocity_x = 0
            velocity_y = 0

            if is_close(self.multiranger.front):
                velocity_x -= self.velocity
            if is_close(self.multiranger.back):
                velocity_x += self.velocity

            if is_close(self.multiranger.left):
                velocity_y -= self.velocity
            if is_close(self.multiranger.right):
                velocity_y += self.velocity

            if is_close(self.multiranger.up):
                self.keep_flying = False

            self.motion_commander.start_linear_motion(
                velocity_x, velocity_y, 0)

            sleep(0.1)

    def manual_control(self):
        #print("hey")
        velocity_x = 0
        velocity_y = 0
        velocity_z = 0
        VELOCITY = 0.5
        if keyboard.is_pressed("up"):
            velocity_x += VELOCITY
        if keyboard.is_pressed("down"):
            velocity_x -= VELOCITY
        if keyboard.is_pressed("left"):
            velocity_y -= VELOCITY
        if keyboard.is_pressed("right"):
            velocity_y += VELOCITY
        if keyboard.is_pressed("u"):
            velocity_z += VELOCITY
        if keyboard.is_pressed("d"):
            velocity_z -= VELOCITY

        
        self.motion_commander.start_linear_motion(velocity_x, velocity_y, velocity_z)
        print("velocity_x = ", velocity_x, " velocity_y = ", velocity_y, " velocity_z = ", velocity_z)
        #sleep(0.1)