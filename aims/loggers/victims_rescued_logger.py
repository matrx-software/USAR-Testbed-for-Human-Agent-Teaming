from matrxs.logger.logger import GridWorldLogger
from matrxs.grid_world import GridWorld


class VictimsRescuedLogger(GridWorldLogger):
    """
    For each tick, log how many victims have been saved per health status, and in total
    """

    def __init__(self, save_path="", file_name_prefix="", file_extension=".csv", delimeter=";"):
        super().__init__(save_path=save_path, file_name=file_name_prefix, file_extension=file_extension,
                         delimiter=delimeter, log_strategy=1)

    def log(self, grid_world: GridWorld, agent_data: dict):
        log_data = {}
        for agent_id, agent_body in grid_world.registered_agents.items():

            # fetch the command post agent
            if 'command_post' == agent_id:
                log_data = {
                    'total_victims_saved': len(agent_body.properties['victims']),
                    'victims_saved_treatment_need_0': 0,
                    'victims_saved_treatment_need_1': 0,
                    'victims_saved_treatment_need_2': 0,
                    'victims_saved_treatment_need_3': 0,
                    'victims_saved_dead': 0
                }

                # loop through all rescued victims registered in the command post agent
                if len(agent_body.properties['victims']) > 0:
                    for victim in agent_body.properties['victims']:
                        if victim in grid_world.environment_objects:
                            vict = grid_world.environment_objects[victim]

                            # log victim passed but in command post
                            if not vict.properties['alive']:
                                log_data['victims_saved_dead'] += 1

                            # log victim alive and in command post
                            else:
                                log_data[f'victims_saved_treatment_need_{vict.properties["treatment_need"]}'] += 1
        return log_data


