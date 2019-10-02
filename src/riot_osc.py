from oscpy.server import OSCThreadServer
from time import sleep
import math as math
import sys

if __name__ == '__main__':

    def OSCcallback(*args):
        acc_x = args[0]
        acc_y = args[1]
        acc_z = args[2]

        gyro_x = args[3]
        gyro_y = args[4]
        gyro_z = args[5]

        mag_x = args[6]
        mag_y = args[7]
        mag_z = args[8]

        temp = args[9]

        btn = args[10]
        switch = args[11]

        analog_1 = args[12]
        analog_2 = args[13]

        quat_x = args[14]
        quat_y = args[15]
        quat_z = args[16]
        quat_w = args[17]

        euler_x = args[18]
        euler_y = args[19]
        euler_z = args[20]
        euler_bonus = args[21]

        #signal processing
        phi = math.atan2(2*(quat_x*quat_w+quat_z*quat_z),1-2*(quat_x**2+quat_y**2))
        phi = (phi*180)/math.pi
        #print('temp ' + str(phi)+ ' ' + str(euler_x) + ' ' + str(euler_x+phi))
        print('temp ' + str(euler_x))


    print("testing OSC in python")
    osc = OSCThreadServer()

    try :
        sock = osc.listen(address='0.0.0.0', port=8000, default=True)
        osc.bind(b'/0/raw', OSCcallback)
        sleep(5)
        osc.stop(sock)
        print('stopped OSC')

    except KeyboardInterrupt:
        osc.stop_all()
        print('stopped all for keyboard interupt')




