from typing import List, Tuple
import salabim as sim
from customer_generator import CustomerGenerator

from power_supply import PowerSupply

from charging_station import ChargingStation
from prepare import Prepare


class SimManager:
    def __init__(self, charging_stations: int, total_time: int):
        self.shedual = Prepare(total_time=total_time)
        self.charging_stations = charging_stations

        # Prepare the truck data
        self.shedual.prepare_data(spread_type=3)
        self.total_time = total_time

        # Create varaibles for monitoring
        self.wait_times = []
        self.time_before_service = []

        # Setup the enviroment
        self.env_sim = sim.App(
            trace=False,
            random_seed="*",
            name="Simmulation",
            do_reset=False,
            yieldless=True,
        )
        # Create the power supply
        self.power_supply_o = PowerSupply(env=self.env_sim, max_power_from_grid=20000)

        # Create the waiting room
        self.waiting_room = sim.Queue(name="waitingline88", monitor=False)
        self.waiting_room.length_of_stay.monitor(value=True)
        self.waiting_room.length_of_stay.reset_monitors(stats_only=True)

        # Create the charing stations
        self.stations = [
            ChargingStation(
                waiting_room=self.waiting_room,
                env=self.env_sim,
                power_supply=self.power_supply_o,
                max_power_delivery=1,
            )
            for _ in range(self.charging_stations)
        ]

        # Create the EV generator
        self.generator = CustomerGenerator(
            waiting_room=self.waiting_room,
            env=self.env_sim,
            clerks=self.stations,
            wait_times=self.wait_times,
            time_before_service=self.time_before_service,
            shedual=self.shedual.trucks,
        )

    # This function runs the simmulation
    def run_sim(self) -> Tuple[int, int, int]:
        # Create random numbers for the max power supplys
        self.power_supply_o.distribution_rl = [1, 1, 1]
        self.power_supply_o.strategy = 2

        # Start the simmulation
        self.env_sim.run(till=self.total_time)

        # Get the output of the simmulation
        avg = sum(self.wait_times) / len(self.wait_times)
        min_o = min(self.wait_times)
        max_o = max(self.wait_times)

        return avg, int(min_o), int(max_o)

    def reset_shedual(
        self,
    ):  # This method resets the complete simmulation to its starting position
        self.env_sim.reset_now(0)

        # Make sure all the charging stations are disabled
        self.shedual.prepare_data(spread_type=3)
        self.generator.shedual = self.shedual.trucks
