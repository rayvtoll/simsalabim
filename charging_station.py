import random
import time
import salabim as sim
from data import Consumption
from limit import limit

from power_supply import PowerSupply


class ChargingStation(sim.Component):
    def __init__(
        self,
        waiting_room: sim.Queue,
        env: sim.App,
        power_supply: PowerSupply,
        max_power_delivery: int,
    ):
        super().__init__(name="Station")
        random.seed(time.time())
        self.waiting_room = waiting_room
        self.vehicle = 0
        self.power_supply = power_supply
        self.env = env
        self.max_power_delivery = max_power_delivery
        self.power_consumption = Consumption(0, 0, 0)

        # Append the power consumption to the consumtion list
        self.power_supply.power_used_list.append(self.power_consumption)
        self.power_consumption.max_power_request = self.max_power_delivery
        self.mode.monitor(False)
        self.status.monitor(False)

    def process(self):
        while True:
            # Continu looping until a vehicle shows up in the waiting line
            while len(self.waiting_room) == 0:
                self.passivate()
            self.vehicle = self.waiting_room.pop()
            self.charge_car()

    # This method charges car and stops when the car has been charged
    def charge_car(self):
        loop = 0
        add_charge = 0
        self.vehicle.wait_times.append(self.env.now() - self.vehicle.creation_time)

        while self.vehicle.battery_charge < 100:
            # Determine the max power delivery that the charging station is able to give
            if self.vehicle.battery_charge < 100 - self.max_power_delivery:
                add_charge = self.power_consumption.max_power_consumption
                self.hold(1)
            else:
                add_charge = limit(
                    0,
                    self.power_consumption.max_power_consumption,
                    100 - self.vehicle.battery_charge,
                )
                self.hold(add_charge)

            # Note to the power supply much power is being used from it
            self.power_consumption.power_consumption = add_charge

            # Hold the simulation for 1 minute
            self.vehicle.battery_charge += add_charge
            loop += 1

        # Calculate the time that the complete charging procedure took
        del self.vehicle
        return loop

    # This method calculates the maximum amount of charge the charging pole is allowed to give
    def max_power_consumption(self):
        # Calculate the total amount of power already used by the charging stations
        """TODO power_user is unused"""
        power_used = 0
        for i in self.power_supply.power_used:
            power_used += i
