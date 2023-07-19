import numpy as np

from matrxs.sim_goals.sim_goal import SimulationGoal


class VictimRescueGoal(SimulationGoal):
    """
    A simulation goal that tracks whether all victims have been rescued and treated (if possible)
    """

    def __init__(self):
        super().__init__()
        self.counter = 0

    def goal_reached(self, grid_world):
        self.counter += 1

        # check if all victims have been retrieved
        if grid_world.environment_objects['score'].properties['victims_total'] == grid_world.environment_objects['score'].properties['victims_retrieved']:
            # wait one tick before stopping, such that an update is sent to the frontend that shows a completion screen
            self.is_done = True

        return self.is_done
