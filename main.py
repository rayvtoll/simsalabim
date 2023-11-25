# pip install stable-baselines3[extra]
# Python version 3.9.18
from gymnasium import Env
from gymnasium.spaces import Discrete, Box
import numpy as np
import random
import os
import time

from dataclasses import dataclass
import salabim as sim


# -------------------------------------------------------------------------------------------
def limit(lower, value, max):
    if value < lower:
        return lower
    elif value > max:
        return max
    else:
        return value


# -------------------------------------------------------------------------------------------
# Struct that holds the information regarding a truck
@dataclass
class Truck:
    Battery: np.int16
    Arrival_Time: np.int16
    total_time: np.int16
    total_wait_Time: np.int16


# Trcuk that hold charging station information
@dataclass
class Consumption:
    Power_Consumption: np.real  # Current consumption
    Max_Power_Consumption: np.real  # Max consumption from the
    Max_Power_Reqeust: np.real  # Max power the charging station is able to get


# -------------------------------------------------------------------------------------------
# Class that prepares a car arrival set
class Prepare:
    def __init__(self, total_time):
        # Create an empty list where we can store the truck scedual
        self.trucks = []
        self.total_time = total_time
        self.arrival_times = sim.Exponential(60 / 40)
        self.service_times = sim.Exponential(60 / 50)
        random.seed(time.time())
        # print(self.service_times.sample())
        self.avg_wait_time = []

    def prepare_data(self, spread_type):
        self.trucks = []
        time = 0
        first = False
        # Loop until a day is finished

        while time < self.total_time:
            if spread_type == 1:
                # Create a new data object
                Truck_Data = Truck(
                    Battery=sim.Uniform(20, 80).sample(),
                    Arrival_Time=time,
                    total_time=0,
                )
            elif spread_type == 2:
                Truck_Data = Truck(
                    Battery=sim.Uniform(40).sample(),
                    Arrival_Time=time,
                    total_time=0,
                    total_wait_Time=0,
                )
            elif spread_type == 3:
                arrival, service_time = self.poison()
                self.avg_wait_time.append(service_time)
                service_invert = 100.0 - service_time
                # print(service_invert)
                Truck_Data = Truck(
                    Battery=service_invert,
                    Arrival_Time=time,
                    total_time=0,
                    total_wait_Time=0,
                )
            # Append the data to the list
            self.trucks.append(Truck_Data)

            # Determine the new arrival time
            if first == False:
                time += arrival
            else:
                first = True

        # print("Avarage = ",sum(self.avg_wait_time)/len(self.avg_wait_time))
        # print(self.trucks)

    def poison(self):
        # Given parameters

        # Generate inter-arrival times for the students (Poisson process)
        # Generate service times for the students (exponential distribution)

        # return 30,60
        return self.arrival_times.sample(), self.service_times.sample()


# -------------------------------------------------------------------------------------------
class CustomerGenerator(sim.Component):
    def __init__(
        self, waiting_room, env, clerks, wait_times, time_before_service, shedual
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
        print(len(self.shedual))
        while True:
            # print("Length in code",len(self.shedual))
            # Check if there ia an truck left in the list
            if len(self.shedual) > 0:
                # Get the next truck out of the list
                truck = self.shedual.pop(0)
            else:
                # print("Break")
                # Break when there are no more trucks to create
                break
            # Create a truck object
            # print("Generate")
            Customer(
                creation_time=self.env.now(),
                waiting_room=self.waiting_room,
                env=self.env,
                stations=self.clerks,
                wait_times=self.wait_times,
                time_before_service=self.time_before_service,
                battery_charge=truck.Battery,
            )

            # Hold the simmulation until the next truck is sheduald
            self.hold(truck.Arrival_Time - previous_arrival)
            # Set the previous time
            previous_arrival = truck.Arrival_Time


class Charging_Station(sim.Component):
    def __init__(self, waiting_room, env, power_supply, max_power_delivery):
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
        self.power_consumption.Max_Power_Reqeust = self.max_power_delivery
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
        add_Charge = 0
        self.vehicle.wait_times.append(self.env.now() - self.vehicle.creation_time)

        while self.vehicle.battery_charge < 100:
            # Determine the max power delivery that the charging station is able to give
            # max_power = limit(0,self.max_power_delivery,self.power_supply.)
            max_power = 0
            # print(self.vehicle.battery_charge,100 - self.max_power_delivery)
            if self.vehicle.battery_charge < 100 - self.max_power_delivery:
                add_Charge = self.power_consumption.Max_Power_Consumption
                # print("hierkomt hij doo")
                # print(add_Charge)
                self.hold(1)
                # add_Charge = limit(0,self.max_power_delivery, 100 - limit(0,self.vehicle.battery_charge,)
            else:
                add_Charge = limit(
                    0,
                    self.power_consumption.Max_Power_Consumption,
                    100 - self.vehicle.battery_charge,
                )
                self.hold(add_Charge)
            # print("add_Charge",add_Charge)
            # Note to the power supply much power is being used from it
            self.power_consumption.Power_Consumption = add_Charge

            # Hold the simulation for 1 minute

            self.vehicle.battery_charge += add_Charge
            loop += 1
        # Calculate the time that the complete charging procedure took
        del self.vehicle
        return loop

    # This method calculates the maximum amount of charge the charging pole is allowed to give
    def max_power_consumption(self):
        # Calculate the total amount of power already used by the charging stations
        power_used = 0
        for i in self.power_supply.power_used:
            power_used += i


class Customer(sim.Component):
    def __init__(
        self,
        waiting_room,
        env,
        stations,
        wait_times,
        time_before_service,
        battery_charge,
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
        # print(len(self.waiting_room))
        # Check if there is a station that is passive
        for station in self.stations:
            if station.ispassive():
                station.activate()
                break  # activate at most one clerk
        self.passivate()


# This class resables the general power supply that the chraging stations are coupled to
class Power_supply(sim.Component):
    def __init__(self, env, max_power_from_Grid):
        super().__init__(name="Supply")
        self.max_power_from_grid = max_power_from_Grid
        self.power_used_list = []
        self.distribution_rl = []
        self.power_used = 0
        self.env = env
        self.strategy = 0
        self.max_reached = False
        self.mode.monitor(False)
        self.status.monitor(False)

    def process(self):
        # Calculate the amount of energy that is currently being used
        while True:
            total = 0
            # Select the charging strategy
            if self.strategy == 0:
                self.__distribute_power_simple()
            elif self.strategy == 1:
                self.__disrtibute_power_share_equal()
            elif self.strategy == 2:
                self.__distribute_power_rl(rl_distribution=self.distribution_rl)
            # Check if the list has members
            if len(self.power_used_list) != 0:
                # Loop through all the charging stations
                for i in self.power_used_list:
                    total += i.Power_Consumption
                self.hold(1)
            else:
                pass
        print("Process_Stop")

    def __distribute_power_simple(
        self,
    ):  # This method resembles the simplest distribution (give max until it is out)
        # Loop through all the power cinsumers
        total_distributed = 0
        for i in self.power_used_list:
            # Calculate the max distribution left
            max_allowd = limit(
                0,
                self.max_power_from_grid - total_distributed,
                self.max_power_from_grid,
            )
            # print("Max_Allowed",max_allowd)
            i.Max_Power_Consumption = limit(0, i.Max_Power_Reqeust, max_allowd)
            # if i.Max_Power_Consumption == 0:
            # print("No power_To_Pole")
            total_distributed += i.Max_Power_Consumption

    def __disrtibute_power_share_equal(
        self,
    ):  # This method resables a equal share to all the charging stations
        # Loop through all the power consumers
        total_distributed = 0
        if len(self.power_used_list) != 0:
            available_per_station = self.max_power_from_grid / len(self.power_used_list)
            for i in self.power_used_list:  # Calculate the total amount
                # Give the allowed power to the stations
                i.Max_Power_Consumption = limit(
                    0, i.Max_Power_Reqeust, available_per_station
                )

    def __distribute_power_rl(
        self, rl_distribution
    ):  # This method is used to distribute the power with the help of reinforcemnt learning
        total_distributed = 0
        counter = 0
        if len(self.power_used_list) != 0:
            for i in self.power_used_list:
                max_allowd = limit(
                    0,
                    self.max_power_from_grid - total_distributed,
                    self.max_power_from_grid,
                )
                max_allowd = limit(0, max_allowd, i.Max_Power_Reqeust)
                max_allowd = limit(
                    0,
                    max_allowd,
                    limit(
                        0,
                        self.max_power_from_grid - total_distributed,
                        self.max_power_from_grid - total_distributed,
                    ),
                )
                # Note to the system when the maximum energy consumption is reached
                if max_allowd == 0:
                    self.max_reached = True
                else:
                    self.max_reached = False
                # Insert the max power consumption from the reinforcement learning model into
                i.Max_Power_Consumption = limit(0, rl_distribution[counter], max_allowd)
                total_distributed += i.Max_Power_Consumption
                counter += 1


# -------------------------------------------------------------------------------------------
class sim_manager:
    def __init__(self, Charging_Stations, total_time):
        self.shedual = Prepare(total_time=total_time)
        self.Charging_stations = Charging_Stations
        # Prepare the truck data
        self.shedual.prepare_data(spread_type=3)
        self.total_time = total_time
        # Create varaibles for monitoring
        self.wait_Times = []
        self.time_before_service = []
        # Setup the enviroment
        self.env_Sim = sim.App(
            trace=False,
            random_seed="*",
            name="Simmulation",
            do_reset=False,
            yieldless=True,
        )
        # self.env_Sim.Monitor('.',stats_only= True)
        # Create the power supply
        self.Power_supply_o = Power_supply(env=self.env_Sim, max_power_from_Grid=20000)
        # Create the waiting room
        self.waiting_room = sim.Queue(name="waitingline88", monitor=False)
        self.waiting_room.length_of_stay.monitor(value=True)
        self.waiting_room.length_of_stay.reset_monitors(stats_only=True)
        # Create the charing stations
        self.stations = [
            Charging_Station(
                waiting_room=self.waiting_room,
                env=self.env_Sim,
                power_supply=self.Power_supply_o,
                max_power_delivery=1,
            )
            for _ in range(self.Charging_stations)
        ]
        # Create the EV generator
        self.generator = CustomerGenerator(
            waiting_room=self.waiting_room,
            env=self.env_Sim,
            clerks=self.stations,
            wait_times=self.wait_Times,
            time_before_service=self.time_before_service,
            shedual=self.shedual.trucks,
        )

    # This function runs the simmulation
    def run_sim(self):
        # Create random numbers for the max power supplys
        # max_power = np.random.randint(20,size=1)
        self.Power_supply_o.distribution_rl = [1, 1, 1]
        # self.Power_supply_o.distribution_rl = [max_power[0],max_power[1],max_power[2]]
        self.Power_supply_o.strategy = 2
        # Start the simmulation

        self.env_Sim.run(till=self.total_time)

        # Get the output of the simmulation
        # if len(self.wait_Times) > 0:
        # print(len(self.wait_Times))
        print("len =", len(self.wait_Times))
        avg = sum(self.wait_Times) / len(self.wait_Times)
        min_o = min(self.wait_Times)
        max_o = max(self.wait_Times)
        # else:
        #   print("Niet goed")
        #  avg = 0
        #  min_o = 0
        # max_o = 0

        return avg, int(min_o), int(max_o)

    def reset_shedual(
        self,
    ):  # This method resets the complete simmulation to its starting position
        self.env_Sim.reset_now(0)

        # print("length of stations", len(self.stations))

        # #dsds
        # self.Power_supply_o.
        # self.generator.__init__(waiting_room= self.waiting_room,env=self.env_Sim,clerks=self.stations,wait_times = self.wait_Times,time_before_service=self.time_before_service,shedual= self.shedual.trucks)
        # print("Reset")
        # Make sure all the charging stations are disabled

        self.shedual.prepare_data(spread_type=3)
        self.generator.shedual = self.shedual.trucks
        # print("Length =",len(self.generator.shedual))
        # print()

if __name__ == '__main__':
    count = 0
    sim_m = sim_manager(1, 500000)
    for i in range(1):
        print(sim_m.run_sim())


    # sim_m.reset_shedual()
# -------------------------------------------------------------------------------------------
# Create a truck enviroment that the model is going to perform in
class TruckEnv(Env):
    def __init__(self):
        self.action_space = Discrete(100)
        # self.action_space = Box(low = -0, high = 10, shape = (1,), dtype = int)
        self.observation_space = Box(low=-3, high=250, shape=(1,), dtype=np.float64)
        self.state = 0
        self.done = False
        self.running = False
        self.sim_env = sim_manager(3, 10000)
        # self.env_sim = env = sim.Environment(trace=False)

    def step(self, action):
        # print(action)
        wait_time = self.sim_env.run_sim(action)

        done = True
        info = {}
        if wait_time > 70 and wait_time < 80:
            reward = 1

        else:
            reward = -1

        return np.float32(self.state), reward, done, False, info

    def render(self):
        pass

    def reset(self, seed=None):
        super().reset(seed=seed)
        # Reset the simmulation enviroment
        self.sim_env.reset_shedual()
        # Get a local copy of the schedule
        schedule = self.sim_env.shedual.trucks

        battery = []
        arriaval_time = []
        # Extract the data from the schedule
        for i in schedule:
            battery.append(i.Battery)
            arriaval_time.append(i.Arrival_Time)
        battery_np = np.array(battery)
        arriaval_time_np = np.array(arriaval_time)
        # Create a
        self.state = 100
        info = {}
        return np.float32(self.state), info


# env = TruckEnv()
# env.reset()
log_path = os.path.join(".", "logs")
# model = PPO('MlpPolicy', env, verbose = 1, tensorboard_log = log_path)

# model.learn(total_timesteps= 10000,progress_bar= True)
