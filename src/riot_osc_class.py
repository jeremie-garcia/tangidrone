from oscpy.server import OSCThreadServer
import math
import keyboard
from threading import Thread,Lock
from time import sleep

class riot_osc():
    '''classe principale pour le controle du drone par le capteur'''
    #NOTTODO : fonction atterissage;
    #TODO : si tous les modes (surtout avec multiranger en même temps - si thread parallel -> probleme?)
    #todo : orientation fonctionne (lag visible (- une seconde ~250ms)), altitude: pbs pas trop deterministe
    # vitesses max évitement
        #bien modifiée en paramètres mais evolution dynamique bizarre, tests multi-ranger pas faits.
    #cnotrol manuel fonctionne avec clavier directionnel + u et d pour altitude (plutot reactif (comme orientaiton voir moins))

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


    def set_orig(self, *args, axes = "all"):
        #fonction lancée au début du programme qui récupère les valeurs initiales du capteur pour définir une origine pour la suite
        if axes == "all" or axes == "x": 
            self.orig_x = self._normalize__(args[18],0)
        if axes == "all" or axes == "z": 
            self.orig_z = self._normalize__(args[20],0)

        self.osc.unbind(b'/0/raw',self.set_orig)
        self.osc.bind(b'/0/raw',self.callback)


    def _normalize__(self, value, orig):
        #fonction qui prend en paramètre une valeur renvoyé par le capteur et l'origine définit au lancement
        #qui normalise cette valeur entre 0 et 360
        value = round(value)
        if value < 0:
            value = 360 + value
        value -= orig
        if value < 0 : value += 360
        return value

    def callback(self, *args):
        #fonction principale de callback liée au capteur
        self.euler_z = self._normalize__(args[20], self.orig_z)
        try:
            self.euler_y = round(args[19])
        except:
            self.euler_y = -90
        #print(self.euler_x, self.euler_y, self.euler_z)
        if abs(self.euler_z) <= 10 and abs(self.euler_y) <= 10:
            #appel de la fonction de contrôle de l'orientation
            self.callback_x(*args)
        elif abs(self.euler_z - 90) <= 10  and abs(self.euler_y) <= 10:
            #appel de la fonction d'atterrissage
            self.landing()
        elif abs(self.euler_z - 270) <= 10 and abs(self.euler_y) <= 10:
            #appel de la fonction de contrôle de la vitesse d'évitement
            self.set_velocity(*args)
        elif abs(self.euler_z - 180) <= 15 and abs(self.euler_y) <= 12:
            #appel de la fonction de vol stationaire
            self.idle()
        elif abs(self.euler_y - 90) <= 10:
            #appel de la fonction de contrôle de l'altitude
            self.callback_z(*args)
        elif abs(self.euler_y + 90) <= 20:
            #appel de la fonctoin pour controler manuellement le drone
            self.manual_control()
        else:
            pass
        

    def landing(self):
        #fonction d'atterrisage, besoin de valider par appui sur espace
        print("appuyer sur espace quelque seconde pour atterrir et ensuite arrêter le drone")
        if keyboard.is_pressed("space"):
            self.keep_flying = False
            print("Atterrissage...")
        

    def idle(self):
        #fonction de vol stationnaire
        print("idle...")
        pass

    def set_velocity(self, *args):
        #fonction pour modifier la vitesse d'évitement du multiranger
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
        
    def callback_z(self, *args):
        #fonction de contrôle de l'altitude
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
        #fonction de contrôle de l'orientation (lacet)
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
        self.ante_x = self.euler_x

    def manual_control(self):
        #fonction de contrôle manuel du drone
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

    def sock_connect(self):
        #fonction qui établit la connection avec le capteur au  lancement
        self.sock = self.osc.listen(address='0.0.0.0', port=8000, default=True)

    def run(self):
        #fonction principale qui établit la position d'origine puis lie la fonction de callback au capteur 
        #et lance une boucle infinie tant que la fonction d'aterrrissage n'est pas lancée
        try:
            self.sock_connect()
            self.osc.bind(b'/0/raw',self.set_orig)
            print(self.keep_flying)
            while self.keep_flying:
                sleep(0.05)
        except KeyboardInterrupt:
            self.osc.stop_all()
            print('stopped all for keyboard interupt')
        self.thread_multirange.join()

    def stop(self):
        #fonction qui libère le capteur à la fin du programme
        self.osc.stop(self.sock)
        print("Stopped OCS")

    def multirange_push(self):
        #fonction appelée par le thread du multiranger qui permet de la faire tourner en concurrence avec les fonctions
        #de contrôle de l'orientation et autre
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