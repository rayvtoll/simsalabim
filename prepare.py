import random
import salabim as sim
import time

from data import Truck

class Prepare:
    '''Class that prepares a car arrival set'''

    def __init__(self, total_time):
        # Create an empty list where we can store the truck scedual
        self.trucks = []
        self.total_time = total_time
        self.arrival_times = sim.Exponential(60 / 40)
        self.service_times = sim.Exponential(60 / 50)
        random.seed(time.time())
        self.avg_wait_time = []

    def prepare_data(self, spread_type):
        self.trucks = []
        time = 0
        first = False

        # Loop until a day is finished
        while time < self.total_time:
            if spread_type == 1:
                # Create a new data object
                truck_data = Truck(
                    battery=sim.Uniform(20, 80).sample(),
                    arrival_Time=time,
                    total_time=0,
                )
            elif spread_type == 2:
                truck_data = Truck(
                    battery=sim.Uniform(40).sample(),
                    arrival_Time=time,
                    total_time=0,
                    total_wait_Time=0,
                )
            elif spread_type == 3:
                arrival, service_time = self.poison()
                self.avg_wait_time.append(service_time)
                service_invert = 100.0 - service_time
                truck_data = Truck(
                    battery=service_invert,
                    arrival_time=time,
                    total_time=0,
                    total_wait_time=0,
                )
            # Append the data to the list
            self.trucks.append(truck_data)

            # Determine the new arrival time
            if first == False:
                time += arrival
            else:
                first = True

    def poison(self):
        # Given parameters

        # Generate inter-arrival times for the students (Poisson process)
        # Generate service times for the students (exponential distribution)

        return self.arrival_times.sample(), self.service_times.sample()
