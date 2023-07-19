from matrxs.logger.logger import GridWorldLogger
from matrxs.grid_world import GridWorld


class AimsLogger(GridWorldLogger):

    def __init__(self, save_path="", file_name_prefix="", file_extension=".csv", delimeter=";"):
        super().__init__(save_path=save_path, file_name=file_name_prefix, file_extension=file_extension,
                         delimiter=delimeter, log_strategy=1)

    def log(self, grid_world: GridWorld, agent_data: dict):
        log_data = {}
        for agent_id, agent_body in grid_world.registered_agents.items():
            if agent_id in ['rescue_worker', 'explorer']:
                log_data[agent_id + '_action'] = agent_body.current_action
                log_data[agent_id + '_action_result'] = None
                if agent_body.action_result is not None:
                    log_data[agent_id + '_action_result'] = agent_body.action_result.succeeded
                log_data[agent_id + '_location'] = agent_body.location

        score = grid_world.environment_objects['score'].custom_properties.items()
        for key, value in score:
            log_data[key] = value

        return log_data
