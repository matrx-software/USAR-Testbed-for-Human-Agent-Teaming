from matrxs.logger.logger import GridWorldLogger
from matrxs.grid_world import GridWorld


class LogDuration(GridWorldLogger):

    def __init__(self, save_path="", file_name_prefix="", file_extension=".csv", delimeter=";"):
        super().__init__(save_path=save_path, file_name=file_name_prefix, file_extension=file_extension,
                         delimiter=delimeter)

    def log(self, grid_world: GridWorld, agent_data: dict):
        log_statement = {
            "tick": grid_world.current_nr_ticks
        }

        return log_statement
