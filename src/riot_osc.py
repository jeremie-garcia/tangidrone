from oscpy.server import OSCThreadServer
from time import sleep
import math as math
import sys

#''' tester for OSC Riot reception'''
if __name__ == '__main__':
    list = [0]
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

        euler_x = args[20]
        euler_x = round(euler_x)
        if euler_x < 0:
            euler_x = 360 + euler_x
        angle = euler_x - list[0]
        angle2 = math.atan2(2*(quat_x*quat_w + quat_y*quat_z), 1-2*(quat_z**2+quat_w**2))
        print(euler_x)
        list[0] = euler_x

    print("testing OSC in python")
    osc = OSCThreadServer()

    try :
        sock = osc.listen(address='0.0.0.0', port=8000, default=True)
        osc.bind(b'/0/raw', OSCcallback)
        sleep(25)
        osc.stop(sock)
        print('stopped OSC')

    except KeyboardInterrupt:
        osc.stop_all()
        print('stopped all for keyboard interupt')




