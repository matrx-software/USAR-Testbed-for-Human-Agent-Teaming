from matrxs.actions.action import Action, ActionResult
from matrxs.objects.agent_body import AgentBody
from aims.objects import Door2

"""
This file is exactly the same as matrxs/move_actions.py.
The only addition is an additional check, that prevents the rescue worker from walking over
collapsed doors: see line 63, in _possible_movement().
"""

def _act_move(grid_world, agent_id, dx, dy):
    agent_avatar = grid_world.get_env_object(agent_id, obj_type=AgentBody)
    loc = agent_avatar.location
    new_loc = [loc[0] + dx, loc[1] + dy]
    grid_world.registered_agents[agent_id].location = new_loc

    return MoveActionResult(MoveActionResult.RESULT_SUCCESS, succeeded=True)


def _is_possible_movement(grid_world, agent_id, dx, dy):
    return _possible_movement(grid_world, agent_id, dx, dy)


def _possible_movement(grid_world, agent_id, dx, dy):
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
                    # for some reason the move action has no effect. If this is the case, we send the appropriate
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

                    # if it is the rescue worker, prevent walking over collapsed doors
                    if agent_id == "rescue_worker":
                        if isinstance(loc_obj, Door2):
                            room_name = loc_obj.properties['room']
                            agents_in_room = grid_world.registered_agents[room_name.lower()].properties['agents']

                            print(" Agents in room:", agents_in_room)
                            print("Rescue worker trying to pass Door 2")
                            # the door of the command post has no room name, so skip it
                            if not room_name:
                                print("room_name == False, True")
                                return MoveActionResult(MoveActionResult.RESULT_SUCCESS, succeeded=True)


                            # the rescue worker can walk out of a collapsed building, even if the
                            # door is open
                            if loc_obj.properties['collapsed'] and agent_id in agents_in_room:
                                print("Room collapsed and agent in it, True" )
                                return MoveActionResult(MoveActionResult.RESULT_SUCCESS, succeeded=True)

                            # the rescue worker cannot walk into a collapsed building, even if the
                            # door is open
                            elif loc_obj.properties['collapsed']:
                                print("collapsed, so no")
                                return MoveActionResult(MoveActionResult.RESULT_NOT_PASSABLE_OBJECT, succeeded=False)

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

    def __init__(self, result, succeeded):
        super().__init__(result, succeeded)


class Move(Action):
    def __init__(self, duration_in_ticks=0):
        super().__init__(duration_in_ticks)
        self.dx = 0
        self.dy = 0

    def is_possible(self, grid_world, agent_id, **kwargs):
        result = _is_possible_movement(
            grid_world, agent_id=agent_id, dx=self.dx, dy=self.dy)
        return result

    def mutate(self, grid_world, agent_id, **kwargs):
        return _act_move(grid_world, agent_id=agent_id, dx=self.dx, dy=self.dy)


class MoveNorth3(Move):
    def __init__(self):
        super().__init__()
        self.dx = 0
        self.dy = -1


class MoveEast3(Move):

    def __init__(self):
        super().__init__()
        self.dx = +1
        self.dy = 0


class MoveSouth3(Move):

    def __init__(self):

        super().__init__()
        self.dx = 0
        self.dy = +1


class MoveWest3(Move):

    def __init__(self):
        super().__init__()
        self.dx = -1
        self.dy = 0
