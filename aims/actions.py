import numpy as np

from matrxs.actions.action import Action, ActionResult
from matrxs.actions.move_actions import MoveActionResult
from matrxs.actions.object_actions import GrabObjectResult
from matrxs.objects.agent_body import AgentBody
from matrxs.objects.simple_objects import AreaTile
from aims.objects import EpiCenter, Door2, Wall2
from matrxs.utils.message import Message



class MoveToLocation(Action):
    def __init__(self, duration_in_ticks=0):
        super().__init__(duration_in_ticks)

    def mutate(self, grid_world, agent_id, location=(0, 0), **kwargs):
        grid_world.registered_agents[agent_id].change_property(
            'location', location)

        result = ActionResult(ActionResult.ACTION_SUCCEEDED, True)

        return result

    def is_possible(self, grid_world, agent_id, location=(0, 0), **kwargs):
        result = possible_movement_to_location(grid_world, agent_id, location)
        return result


class PickUpVictim(Action):
    def __init__(self, duration_in_ticks=0):
        super().__init__(duration_in_ticks)

    def is_possible(self, grid_world, agent_id, **kwargs):
        # Set default values check
        object_id = None if 'object_id' not in kwargs else kwargs['object_id']
        max_objects = np.inf if 'max_objects' not in kwargs else kwargs['max_objects']
        return is_possible_grab(grid_world, agent_id=agent_id, object_id=object_id,
                                max_objects=max_objects)

    def mutate(self, grid_world, agent_id, **kwargs):
        # Additional check
        assert 'object_id' in kwargs.keys()
        assert 'max_objects' in kwargs.keys()

        # if possible:
        object_id = kwargs['object_id']  # assign

        # Loading properties
        reg_ag = grid_world.registered_agents[agent_id]  # Registered Agent
        # Environment object
        env_obj = grid_world.environment_objects[object_id]

        # Updating properties
        env_obj.carried_by.append(agent_id)
        reg_ag.is_carrying.append(env_obj)  # we add the entire object!

        # Remove it from the grid world (it is now stored in the is_carrying list of the AgentAvatar
        succeeded = grid_world.remove_from_grid(
            object_id=env_obj.obj_id, remove_from_carrier=False)
        if not succeeded:
            return GrabObjectResult(GrabObjectResult.FAILED_TO_REMOVE_OBJECT_FROM_WORLD.replace("{OBJECT_ID}",
                                                                                                env_obj.obj_id), False)

        # Updating Location (done after removing from grid, or the grid will search the object on the wrong location)
        env_obj.location = reg_ag.location

        return GrabObjectResult(GrabObjectResult.RESULT_SUCCESS, True)


# Check if grab action is possible
def is_possible_grab(grid_world, agent_id, object_id, max_objects):
    reg_ag = grid_world.registered_agents[agent_id]  # Registered Agent
    loc_agent = reg_ag.location  # Agent location

    if object_id is None:
        return GrabObjectResult(GrabObjectResult.RESULT_NO_OBJECT, False)

    # Already carries an object
    if len(reg_ag.is_carrying) >= max_objects:
        return GrabObjectResult(GrabObjectResult.RESULT_CARRIES_OBJECT, False)

    # TODO if robots are used: check if the object is still available at the specific location

    # Check if object_id is the id of an agent
    if object_id in grid_world.registered_agents.keys():
        # If it is an agent at that location, grabbing is not possible
        return GrabObjectResult(GrabObjectResult.RESULT_AGENT, False)

    # Check if it is an object
    if object_id in grid_world.environment_objects.keys():
        # Environment object
        env_obj = grid_world.environment_objects[object_id]
        # Check if the object is not carried by another agent
        if len(env_obj.carried_by) != 0:
            return GrabObjectResult(GrabObjectResult.RESULT_OBJECT_CARRIED.replace("{AGENT_ID}",
                                                                                   str(env_obj.carried_by)), False)
        elif not env_obj.properties["is_movable"]:
            return GrabObjectResult(GrabObjectResult.RESULT_OBJECT_UNMOVABLE, False)
        else:
            # Success
            return GrabObjectResult(GrabObjectResult.RESULT_SUCCESS, True)
    else:
        return GrabObjectResult(GrabObjectResult.RESULT_UNKNOWN_OBJECT_TYPE, False)


# Check if movement to specific location is possible (default function had delta movement)
def possible_movement_to_location(grid_world, agent_id, location):
    agent_avatar = grid_world.get_env_object(agent_id, obj_type=AgentBody)
    assert agent_avatar is not None

    new_loc = [location[0], location[1]]
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


class UpdateRoomContent(Action):
    def __init__(self, duration_in_ticks=0):
        super().__init__(duration_in_ticks)

    def mutate(self, grid_world, agent_id, victims, agents, **kwargs):
        grid_world.registered_agents[agent_id].change_property(
            'victims', victims)
        grid_world.registered_agents[agent_id].change_property(
            'agents', agents)

        result = ActionResult(ActionResult.ACTION_SUCCEEDED, True)

        return result

    def is_possible(self, grid_world, agent_id, victims, agents, **kwargs):
        return ActionResult(ActionResult.ACTION_SUCCEEDED, True)


class InspectVictim(Action):
    def __init__(self, duration_in_ticks=5):
        super().__init__(duration_in_ticks)

    def mutate(self, grid_world, agent_id, object_id, **kwargs):
        # change the health status in the memory of the agent who treated the victim
        update_agent_memory(grid_world, object_id, agent_id)

        return ActionResult(ActionResult.ACTION_SUCCEEDED, True)

    def is_possible(self, grid_world, agent_id, object_id, **kwargs):
        if object_id is None:
            return ActionResult(ActionResult.ACTION_NOT_POSSIBLE, False)
        if 'Victim' in grid_world.environment_objects[object_id].properties['class_inheritance']:
            return ActionResult(ActionResult.ACTION_SUCCEEDED, True)
        else:
            return ActionResult(ActionResult.ACTION_NOT_POSSIBLE, False)


class HurtVictim(Action):
    def __init__(self, duration_in_ticks=0):
        super().__init__(duration_in_ticks)

    def mutate(self, grid_world, agent_id, victims, **kwargs):
        for victim in victims:
            # we can't reach picked up victims
            if victim not in grid_world.environment_objects:
                continue
            treatment_need = grid_world.environment_objects[victim].properties['treatment_need']

            if treatment_need < 3:
                grid_world.environment_objects[victim].change_property(
                    'treatment_need', treatment_need + 1)
            else:
                grid_world.environment_objects[victim].change_property(
                    'alive', False)

            # Update color
            alive = grid_world.environment_objects[victim].properties['alive']
            treatment_need = grid_world.environment_objects[victim].properties['treatment_need']
            if alive:
                if treatment_need == 0:
                    grid_world.environment_objects[victim].change_property(
                        'visualize_colour', '#70AD47')
                    grid_world.environment_objects[victim].change_property(
                        "img_name", "/static/images/victim_status_healthy.png")
                elif treatment_need == 1:
                    grid_world.environment_objects[victim].change_property(
                        'visualize_colour', '#FFC000')
                    grid_world.environment_objects[victim].change_property(
                        "img_name", "/static/images/victim_status_injured.png")
                elif treatment_need == 2:
                    grid_world.environment_objects[victim].change_property(
                        'visualize_colour', '#ED7D31')
                    grid_world.environment_objects[victim].change_property(
                        "img_name", "/static/images/victim_status_badly_injured.png")
                elif treatment_need == 3:
                    grid_world.environment_objects[victim].change_property(
                        'visualize_colour', '#FF0000')
                    grid_world.environment_objects[victim].change_property(
                        "img_name", "/static/images/victim_status_extremely_injured.png")
            else:
                grid_world.environment_objects[victim].change_property(
                    'visualize_colour', '#000000')
                grid_world.environment_objects[victim].change_property(
                    "img_name", "/static/images/victim_status_dead.png")

        return ActionResult(ActionResult.ACTION_SUCCEEDED, True)

    def is_possible(self, grid_world, agent_id, victims, **kwargs):
        return ActionResult(ActionResult.ACTION_SUCCEEDED, True)


def update_agent_memory(grid_world, victim_id, agent_id):
    """
    Agents have memories, in which they save information about the world.
    Given a specific agent, this function updates their memory on the health status of a victim,
    such that their memory corresponds with the real health status of the victim at this moment
    """

    alive = grid_world.environment_objects[victim_id].properties['alive']
    treatment_need = grid_world.environment_objects[victim_id].properties['treatment_need']
    img_name = None
    # find the correct image corresponding with health status
    if alive:
        if treatment_need == 0:
            img_name = "/static/images/victim_status_healthy.png"
        elif treatment_need == 1:
            img_name = "/static/images/victim_status_injured.png"
        elif treatment_need == 2:
            img_name = "/static/images/victim_status_badly_injured.png"
        elif treatment_need == 3:
            img_name = "/static/images/victim_status_extremely_injured.png"
    else:
        img_name = "/static/images/victim_status_dead.png"

    # change memory of the agent to the real current health status of the victim
    memory = grid_world.registered_agents[agent_id].properties['memory']
    memory[victim_id]['alive'] = alive
    memory[victim_id]['treatment_need'] = treatment_need
    memory[victim_id]['img_name'] = img_name

    # update the memory in the agent
    grid_world.registered_agents[agent_id].change_property('memory', memory)


class TreatVictim(Action):
    def __init__(self, duration_in_ticks=20):
        super().__init__(duration_in_ticks)

    def mutate(self, grid_world, agent_id, object_id, **kwargs):
        # change the health status of the victim to 1 step better than it was
        treatment_need = grid_world.environment_objects[object_id].properties['treatment_need'] - 1
        grid_world.environment_objects[object_id].change_property(
            'treatment_need', treatment_need)
        # grid_world.environment_objects[object_id].change_property('need_increase_time', 0)
        vis_colour = None
        img_name = None
        if treatment_need == 0:
            vis_colour = '#70AD47'
            img_name = "/static/images/victim_status_healthy.png"
        elif treatment_need == 1:
            vis_colour = '#FFC000'
            img_name = "/static/images/victim_status_injured.png"
        elif treatment_need == 2:
            vis_colour = '#ED7D31'
            img_name = "/static/images/victim_status_badly_injured.png"
        elif treatment_need == 3:
            vis_colour = '#FF0000'
            img_name = "/static/images/victim_status_extremely_injured.png"

        grid_world.environment_objects[object_id].change_property(
            'visualize_colour', vis_colour)
        grid_world.environment_objects[object_id].change_property(
            'img_name', img_name)

        # change the health status in the memory of the agent who treated the victim
        update_agent_memory(grid_world, object_id, agent_id)

        return ActionResult(ActionResult.ACTION_SUCCEEDED, True)

    def is_possible(self, grid_world, agent_id, object_id, **kwargs):
        if object_id is None:
            return ActionResult(ActionResult.ACTION_NOT_POSSIBLE, False)

        # check if it is an victim
        if 'Victim' in grid_world.environment_objects[object_id].properties['class_inheritance']:
            alive = grid_world.environment_objects[object_id].properties['alive']
            treatment_need = grid_world.environment_objects[object_id].properties['treatment_need']

            # check that it is alive and not already (almost) healthy
            if alive and treatment_need > 1:

                # check that it is not in the command post
                if object_id not in grid_world.registered_agents['command_post'].properties['victims']:
                    return ActionResult(ActionResult.ACTION_SUCCEEDED, True)

        return ActionResult(ActionResult.ACTION_NOT_POSSIBLE, False)


# Sets energy level of another agent back to its original value
class ReplaceBattery(Action):
    def __init__(self, duration_in_ticks=20):
        super().__init__(duration_in_ticks)

    def mutate(self, grid_world, agent_id, object_id, **kwargs):
        print("Replacing battery")

        # Update energy level
        custom_properties = grid_world.registered_agents[object_id].custom_properties
        custom_properties['energy'] = custom_properties['energy_full']
        grid_world.registered_agents[object_id].change_property(
            'custom_properties', custom_properties)

        # Update score batteries replaced
        batteries_replaced = grid_world.environment_objects['score'].properties['batteries_replaced']
        grid_world.environment_objects['score'].change_property(
            'batteries_replaced', batteries_replaced + 1)

        return ActionResult(ActionResult.ACTION_SUCCEEDED, True)

    def is_possible(self, grid_world, agent_id, object_id, **kwargs):
        batteries_replaced = grid_world.environment_objects['score'].properties['batteries_replaced']
        max_battery_replacements = grid_world.environment_objects[
            'settings'].properties['max_battery_replacements']
        if object_id is None:
            return ActionResult(ActionResult.ACTION_NOT_POSSIBLE, False)
        elif batteries_replaced < max_battery_replacements:
            return ActionResult(ActionResult.ACTION_NOT_POSSIBLE, True)
        else:
            return ActionResult(ActionResult.ACTION_NOT_POSSIBLE, False)


class StartEarthquake(Action):
    def __init__(self, duration_in_ticks=0):
        super().__init__(duration_in_ticks)

    def mutate(self, grid_world, agent_id, **kwargs):
        # add bg tiles to serve as a flash, indicating the earthquake happened
        for x in range(grid_world.shape[0]):
            for y in range(grid_world.shape[1]):
                tile = AreaTile([x, y], name=str([x, y]),
                                visualize_colour='#363131')
                grid_world._register_env_object(tile)   # Add tile to the world

        result = ActionResult(ActionResult.ACTION_SUCCEEDED, True)

        return result

    def is_possible(self, grid_world, agent_id, **kwargs):
        return ActionResult(ActionResult.ACTION_SUCCEEDED, True)


class EndEarthquake(Action):
    def __init__(self, duration_in_ticks=0):
        super().__init__(duration_in_ticks)

    def mutate(self, grid_world, agent_id, **kwargs):
        # remove the "flash" earthquake tiles
        for x in range(grid_world.shape[0]):
            for y in range(grid_world.shape[1]):
                obj_id = str([x, y])
                # Remove earthquake area tile from the world
                grid_world.remove_from_grid(obj_id)

        result = ActionResult(ActionResult.ACTION_SUCCEEDED, True)

        return result

    def is_possible(self, grid_world, agent_id, **kwargs):
        return ActionResult(ActionResult.ACTION_SUCCEEDED, True)


class ManualEarthquake(Action):
    def __init__(self, duration_in_ticks=0):
        super().__init__(duration_in_ticks)

    def mutate(self, grid_world, agent_id, **kwargs):
        settings = grid_world.environment_objects['settings'].properties

        # add background tiles to emulate flash
        for x in range(grid_world.shape[0]):
            for y in range(grid_world.shape[1]):
                tile = AreaTile([x, y], name=str([x, y]),
                                visualize_colour='#363131')
                grid_world._register_env_object(tile)   # Add tile to the world

        # Add epicenter to the world
        epicenter = settings['epicenter']
        radius = settings['earthquake_radius']
        epicenter_tile = EpiCenter([epicenter[0] - radius, epicenter[1] - radius], name='epicenter', visualize_colour='#7A30A0',
                                   visualize_shape="img", img_name="/static/images/epicenter_circle_large_transparent.png",
                                   visualize_size=radius*2, visualize_depth=0)
        grid_world._register_env_object(epicenter_tile)

        # Collapse buildings
        affected_buildings = settings['affected_buildings']
        for building in affected_buildings:
            grid_world.registered_agents[building.lower()].change_property(
                'collapsed', True)

        for obj_id, obj in grid_world.environment_objects.items():
            if 'location' in obj.properties:
                if 'Wall2' in obj.properties['class_inheritance'] and obj.properties['room'] in affected_buildings:
                    grid_world.environment_objects[obj_id].change_property(
                        'collapsed', True)
                    grid_world.environment_objects[obj_id].change_property(
                        'visualize_colour', '#595751')
                elif 'Door2' in obj.properties['class_inheritance'] and obj.properties['room'] in affected_buildings:
                    door = grid_world.environment_objects[obj_id]
                    door.change_property('collapsed', True)
                    door.collapsed = True
                    # close the door
                    door.close_door()



        # Hurt victims
        affected_victims = settings['affected_victims']
        for victim in affected_victims:
            # don't hurt a victim if they are already in the CP / saved
            if victim not in grid_world.registered_agents['command_post'].properties['victims'] and victim in grid_world.environment_objects:
                victim_obj = grid_world.filter_env_objects(
                    victim)[0].properties['obj_id']
                grid_world.environment_objects[victim_obj].change_property(
                    'treatment_need', 3)
                grid_world.environment_objects[victim_obj].change_property(
                    'visualize_colour', '#FF0000')
                grid_world.environment_objects[victim_obj].change_property(
                    'img_name', "/static/images/victim_status_extremely_injured.png")

        # Drain explorer energy
        custom_properties = grid_world.registered_agents['explorer'].custom_properties
        energy = custom_properties['energy']
        settings_obj_id = grid_world.filter_env_objects(
            'settings')[0].properties['obj_id']
        energy_cost_earthquake = grid_world.environment_objects[
            settings_obj_id].properties['energy_cost_earthquake']
        energy_new = energy - energy_cost_earthquake
        if energy_new < 0:
            energy_new = 0
        custom_properties['energy'] = energy_new
        grid_world.registered_agents[agent_id].change_property(
            'custom_properties', custom_properties)

        result = ActionResult(ActionResult.ACTION_SUCCEEDED, True)

        return result

    def is_possible(self, grid_world, agent_id, **kwargs):
        return ActionResult(ActionResult.ACTION_SUCCEEDED, True)


class Collapse(Action):
    """ Collapse of a room: the rooms and its walls, the managing room agent, and hurt any victims in that room
     with a chance P, as specified in the json config file """

    def __init__(self, duration_in_ticks=0):
        super().__init__(duration_in_ticks)

    def mutate(self, grid_world, agent_id, walls, victims, **kwargs):
        grid_world.registered_agents[agent_id].change_property(
            'collapsed', True)
        for wall in walls:
            grid_world.environment_objects[wall].change_property(
                'collapsed', True)
            grid_world.environment_objects[wall].change_property(
                'visualize_colour', '#595751')

        p_gets_hurt = grid_world.environment_objects[
            'settings'].properties['p_victim_gets_hurt_after_room_collapse']
        affected_victim = grid_world.environment_objects[
            'settings'].properties['p_victim_gets_hurt_after_room_collapse']
        for victim in victims:
            # Each victim has a 0.8 probability of getting hurt when a room collapses
            gets_hurt = np.random.choice(
                [True, False], p=[p_gets_hurt, 1 - p_gets_hurt])
            if gets_hurt and victim in grid_world.environment_objects:
                grid_world.environment_objects[victim].change_property(
                    'treatment_need', 3)
                grid_world.environment_objects[victim].change_property(
                    'visualize_colour', '#FF0000')

        result = ActionResult(ActionResult.ACTION_SUCCEEDED, True)

        return result

    def is_possible(self, grid_world, agent_id, walls, victims, **kwargs):
        return ActionResult(ActionResult.ACTION_SUCCEEDED, True)


class UpdateScore(Action):
    def __init__(self, duration_in_ticks=0):
        super().__init__(duration_in_ticks)

    def mutate(self, grid_world, agent_id, victims_alive, victims_retrieved, ticks_elapsed, **kwargs):
        score_obj = grid_world.filter_env_objects(
            'score')[0].properties['obj_id']
        grid_world.environment_objects[score_obj].change_property(
            'victims_alive', victims_alive)
        grid_world.environment_objects[score_obj].change_property(
            'victims_retrieved', victims_retrieved)
        grid_world.environment_objects[score_obj].change_property(
            'ticks_elapsed', ticks_elapsed)

        result = ActionResult(ActionResult.ACTION_SUCCEEDED, True)

        return result

    def is_possible(self, grid_world, agent_id, victims_alive, victims_retrieved, ticks_elapsed, **kwargs):
        return ActionResult(ActionResult.ACTION_SUCCEEDED, True)


class UpdateEnergy(Action):
    def __init__(self, duration_in_ticks=0):
        super().__init__(duration_in_ticks)

    def mutate(self, grid_world, agent_id, agent, energy, **kwargs):
        custom_properties = grid_world.registered_agents[agent].custom_properties
        # make sure the battery doesn't dip below 0
        if energy < 0:
            energy = 0
        custom_properties['energy'] = energy
        grid_world.registered_agents[agent].change_property(
            'custom_properties', custom_properties)
        result = ActionResult(ActionResult.ACTION_SUCCEEDED, True)

        return result

    def is_possible(self, grid_world, agent_id, agent, energy, **kwargs):
        return ActionResult(ActionResult.ACTION_SUCCEEDED, True)


class EndTrial(Action):
    def __init__(self, duration_in_ticks=0):
        super().__init__(duration_in_ticks)

    def mutate(self, grid_world, agent_id, **kwargs):
        # grid_world.is_done = True

        # grid_world.environment_objects['score']

        result = ActionResult(ActionResult.ACTION_SUCCEEDED, True)

        return result

    def is_possible(self, grid_world, agent_id, **kwargs):
        return ActionResult(ActionResult.ACTION_SUCCEEDED, True)


class InspectBuilding(Action):
    def __init__(self, duration_in_ticks=0):
        super().__init__(duration_in_ticks)

    def mutate(self, grid_world, agent_id, **kwargs):
        result = ActionResult(ActionResult.ACTION_SUCCEEDED, True)

        agent = grid_world.registered_agents[agent_id]
        agent_memory = agent.properties['memory']

        wall = grid_world.get_env_object(requested_id=kwargs['object_id'], obj_type=Wall2)

        # The room to which the wall belongs
        room = wall.properties['room']

        # If the room was not already stored in memory, add it and its collapsed status
        if room not in agent_memory:

            # update the memory
            agent_memory[room] = wall.properties
            agent.change_property('memory', agent_memory)

            # also update the memory of the rescue worker
            rescue_worker = grid_world.registered_agents['rescue_worker']
            rescue_worker_memory = rescue_worker.properties['memory']
            if room not in rescue_worker_memory:
                rescue_worker_memory[room] = wall.properties
                rescue_worker.change_property('memory', rescue_worker_memory)

        return result

    def is_possible(self, grid_world, agent_id, **kwargs):
        # check that we found a wall
        if kwargs['object_id'] is None or grid_world.get_env_object(requested_id=kwargs['object_id'], obj_type=Wall2) is None:
            return ActionResult(ActionResult.ACTION_NOT_POSSIBLE, False)

        return ActionResult(ActionResult.ACTION_SUCCEEDED, True)
