# -*- coding: utf-8 -*-
#
#     ||          ____  _ __
#  +------+      / __ )(_) /_______________ _____  ___
#  | 0xBC |     / __  / / __/ ___/ ___/ __ `/_  / / _ \
#  +------+    / /_/ / / /_/ /__/ /  / /_/ / / /_/  __/
#   ||  ||    /_____/_/\__/\___/_/   \__,_/ /___/\___/
#
#  Copyright (C) 2016 Bitcraze AB
#
#  Crazyflie Nano Quadcopter Client
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA  02110-1301, USA.
"""
Simple example that connects to the crazyflie at `URI` and runs a figure 8
sequence. This script requires some kind of location system, it has been
tested with (and designed for) the flow deck.
Change the URI variable to your Crazyflie configuration.
"""
import logging
import time

import cflib.crtp
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
from cflib.crazyflie.log import LogConfig

URI = 'radio://0/80/2M'

# Only output errors from the logging framework
logging.basicConfig(level=logging.ERROR)

if __name__ == '__main__':
    # Initialize the low-level drivers (don't list the debug drivers)
    cflib.crtp.init_drivers(enable_debug_driver=False)

    with SyncCrazyflie(URI, cf=Crazyflie(rw_cache='./cache')) as scf:
        cf = scf.cf

        lg = LogConfig("Battery", 1000)  # delay
        lg.add_variable("pm.vbat", "float")
        #lg.add_variable("pm.state", "int8_t")
        try:
            cf.log.add_config(lg)
            lg.data_received_cb.add_callback(lambda e, f, g: print(e, f, g))
            lg.error_cb.add_callback(lambda: print('error'))
            lg.start()
        except KeyError as e:
            print(e)


        cf.param.set_value('kalman.resetEstimation', '1')
        time.sleep(0.1)
        cf.param.set_value('kalman.resetEstimation', '0')
        time.sleep(2)

        delay = 0.2

        current_alt = 0

        for y in range(6):
            current_alt = y / 20
            cf.commander.send_hover_setpoint(0, 0, 0, current_alt)
            time.sleep(delay)

        dist = 0.05 #meters

        cf.commander.send_hover_setpoint(-dist,0,0,current_alt)
        time.sleep(1)

        cf.commander.send_hover_setpoint(dist, 0, 0, current_alt)
        time.sleep(1)

        cf.commander.send_hover_setpoint(0, dist, 0, current_alt)
        time.sleep(1)

        cf.commander.send_hover_setpoint(0, -dist, 0, current_alt)
        time.sleep(1)

        cf.commander.send_hover_setpoint(0, 0, 180, current_alt)
        time.sleep(1)

        cf.commander.send_hover_setpoint(0, 0, -180, current_alt)
        time.sleep(1)

        cf.commander.send_hover_setpoint(0, 0, 0, current_alt)
        time.sleep(2)


        for y in range(6):
            current_alt = (6 - y) / 20
            cf.commander.send_hover_setpoint(0, 0, 0, current_alt)
            print(current_alt)
            time.sleep(delay)

        cf.commander.send_stop_setpoint()