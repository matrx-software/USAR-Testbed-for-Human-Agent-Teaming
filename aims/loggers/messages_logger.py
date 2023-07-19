from matrxs.logger.logger import GridWorldLogger
from matrxs.grid_world import GridWorld


class MessageLogger(GridWorldLogger):
    """
    For each tick, log how many victims have been saved per health status, and in total
    """

    def __init__(self, save_path="", file_name_prefix="", file_extension=".csv", delimeter=";"):
        super().__init__(save_path=save_path, file_name=file_name_prefix, file_extension=file_extension,
                         delimiter=delimeter, log_strategy=1)

    def log(self, grid_world: GridWorld, agent_data: dict):
        log_data = {
            'total_number_messages': 0,
            'explorer->rescue_worker': 0,
            'rescue_worker->explorer': 0
        }

        gwmm = grid_world.message_manager
        t = grid_world.current_nr_ticks;

        if t == 0:
            return log_data

        # get total number of messages from the first tick to the current tick
        total_messages = 0
        for i in range(0, t):
            total_messages += len(gwmm.global_messages[i]) if i in gwmm.global_messages.keys() else 0

        log_data['total_number_messages'] = total_messages

        # log every individual message of this tick (only use global messages for this experiment)
        if t-1 in gwmm.global_messages:
            for mssg in gwmm.global_messages[t-1]:
                # specify per message the sender, receiver, and content
                to = "rescue_worker" if mssg.from_id == "explorer" else "explorer"
                log_data[f"{mssg.from_id}->{to}"] = f"'{mssg.content}'"

        return log_data


