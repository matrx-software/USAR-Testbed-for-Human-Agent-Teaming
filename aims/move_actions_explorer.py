from matrxs.actions.action import Action, ActionResult
from matrxs.objects.agent_body import AgentBody


# Custom move actions that cost energy

def act_move(grid_world, agent_id, dx, dy):
    agent_avatar = grid_world.get_env_object(agent_id, obj_type=AgentBody)
    loc = agent_avatar.location
    new_loc = [loc[0] + dx, loc[1] + dy]
    grid_world.registered_agents[agent_id].location = new_loc

    # A move action costs energy
    custom_properties = grid_world.registered_agents[agent_id].custom_properties
    energy = custom_properties['energy']
    energy_cost_move = grid_world.environment_objects['settings'].properties['energy_cost_move']
    energy_new = energy - energy_cost_move
    custom_properties['energy'] = energy_new
    grid_world.registered_agents[agent_id].change_property('custom_properties', custom_properties)

    return MoveActionResult(MoveActionResult.RESULT_SUCCESS, succeeded=True)


def is_possible_movement(grid_world, agent_id, dx, dy):
    energy = grid_world.registered_agents[agent_id].custom_properties['energy']
    energy_cost_move = grid_world.environment_objects['settings'].properties['energy_cost_move']
    if energy > energy_cost_move:
        return possible_movement(grid_world, agent_id, dx, dy)
    else:
        return MoveActionResult(MoveActionResult.RESULT_NOT_ENOUGH_ENERGY, succeeded=False)


def possible_movement(grid_world, agent_id, dx, dy):

    agent_avatar = grid_world.get_env_object(agent_id, obj_type=AgentBody)
    assert agent_avatar is not None

    loc = agent_avatar.location
    new_loc = [loc[0] + dx, loc[1] + dy]
    if 0 <= new_loc[0] < grid_world.shape[0] and 0 <= new_loc[1] < grid_world.shape[1]:
        loc_obj_ids = grid_world.grid[new_loc[1], new_loc[0]]
        if loc_obj_ids is None:
            # there is nothing at that location
            return MoveActionResult(MoveActionResult.RESULT_SUCCESS, succeeded=True)
        else:
            # Go through all objects at the desired locations
            for loc_obj_id in loc_obj_ids:
                # Check if loc_obj_id is the id of an agent
                if loc_obj_id in grid_world.registered_agents.keys():
                    # get the actual agent
                    loc_obj = grid_world.registered_agents[loc_obj_id]
                    # Check if the agent that takes the move action is not that agent at that location (meaning that
                    # for some reason the move action has no effect. If this is the case, we send the apriopriate
                    # result
                    if loc_obj_id == agent_id:
                        # The desired location contains a different agent and we cannot step at locations with agents
                        return MoveActionResult(MoveActionResult.RESULT_NO_MOVE, succeeded=False)
                    # Check if the agent on the other location (if not itself) is traverable. Otherwise we return that
                    # the location is occupied.
                    elif not loc_obj.is_traversable:
                        return MoveActionResult(MoveActionResult.RESULT_OCCUPIED, succeeded=False)
                # If there are no agents at the desired location or we can move on top of other agents, we check if
                # there are objects in the way that are not passable.
                if loc_obj_id in grid_world.environment_objects.keys():
                    # get the actual object
                    loc_obj = grid_world.environment_objects[loc_obj_id]
                    # Check if the object is not passable, if this is not the case is_traversable is False
                    if not loc_obj.is_traversable:
                        # The desired location contains an object that is not passable
                        return MoveActionResult(MoveActionResult.RESULT_NOT_PASSABLE_OBJECT, succeeded=False)

        # Either the desired location contains the agent at previous tick, and/or all objects there are passable
        return MoveActionResult(MoveActionResult.RESULT_SUCCESS, succeeded=True)
    else:
        return MoveActionResult(MoveActionResult.RESULT_OUT_OF_BOUNDS, succeeded=False)


class MoveActionResult(ActionResult):
    RESULT_NO_MOVE = 'Move action resulted in a new location with the agent already present.'
    RESULT_SUCCESS = 'Move action success'
    RESULT_OUT_OF_BOUNDS = 'Move action out of bounds'
    RESULT_OCCUPIED = 'Move action towards occupied space'
    RESULT_NOT_PASSABLE_OBJECT = 'Move action toward space which is not traversable by agent due object'
    RESULT_NOT_ENOUGH_ENERGY = 'Not enough energy to perform move action'

    def __init__(self, result, succeeded):
        super().__init__(result, succeeded)


class Move(Action):
    def __init__(self, duration_in_ticks=0):
        super().__init__(duration_in_ticks)
        self.dx = 0
        self.dy = 0

    def is_possible(self, grid_world, agent_id, **kwargs):
        result = is_possible_movement(grid_world, agent_id=agent_id, dx=self.dx, dy=self.dy)
        return result

    def mutate(self, grid_world, agent_id, **kwargs):
        return act_move(grid_world, agent_id=agent_id, dx=self.dx, dy=self.dy)


class MoveNorth2(Move):
    def __init__(self):
        super().__init__()
        self.dx = 0
        self.dy = -1


class MoveEast2(Move):

    def __init__(self):
        super().__init__()
        self.dx = +1
        self.dy = 0


class MoveSouth2(Move):

    def __init__(self):
        super().__init__()
        self.dx = 0
        self.dy = +1


class MoveWest2(Move):

    def __init__(self):
        super().__init__()
        self.dx = -1
        self.dy = 0
