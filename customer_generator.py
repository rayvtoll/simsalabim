from typing import List
import salabim as sim
from charging_station import ChargingStation

from customer import Customer
from data import Truck


class CustomerGenerator(sim.Component):
    def __init__(
        self,
        waiting_room: sim.Queue,
        env: sim.App,
        clerks: List[ChargingStation],
        wait_times: List,
        time_before_service: List,
        shedual: List[Truck]
    ):
        super().__init__(name="Generator")
        self.waiting_room = waiting_room
        self.env = env
        self.clerks = clerks
        self.debug = False
        self.wait_times = wait_times
        self.time_before_service = time_before_service
        self.shedual = shedual
        self.mode.monitor(False)
        self.status.monitor(False)

    def process(self):
        previous_arrival = 0
        while True:
            # Check if there ia an truck left in the list
            if len(self.shedual) > 0:
                # Get the next truck out of the list
                truck = self.shedual.pop(0)
            else:
                # Break when there are no more trucks to create
                break
            
            # Create a truck object
            Customer(
                creation_time=self.env.now(),
                waiting_room=self.waiting_room,
                env=self.env,
                stations=self.clerks,
                wait_times=self.wait_times,
                time_before_service=self.time_before_service,
                battery_charge=truck.battery,
            )

            # Hold the simmulation until the next truck is sheduald
            self.hold(truck.arrival_time - previous_arrival)

            # Set the previous time
            previous_arrival = truck.arrival_time