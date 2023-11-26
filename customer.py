from typing import List
import numpy as np
import salabim as sim


class Customer(sim.Component):
    def __init__(
        self,
        waiting_room: sim.Queue,
        env: sim.App,
        stations,
        wait_times: List,
        time_before_service: List,
        battery_charge: np.int16,
        creation_time,
    ):
        super().__init__(name="Truck")
        self.waiting_room = waiting_room
        self.env = env
        self.stations = stations
        self.battery_charge = battery_charge
        self.creation_time = creation_time
        self.wait_times = wait_times
        self.time_before_service = time_before_service
        self.mode.monitor(False)
        self.status.monitor(False)

    def process(self):
        # Put the vehicle in the waiting room
        self.enter(self.waiting_room)

        # Check if there is a station that is passive
        for station in self.stations:
            if station.ispassive():
                station.activate()
                break  # activate at most one clerk
        self.passivate()
