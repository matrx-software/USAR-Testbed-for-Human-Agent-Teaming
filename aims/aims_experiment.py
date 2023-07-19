import json
import os

from datetime import datetime

from aims.VictimRescueGoal import VictimRescueGoal
from aims.actions import PickUpVictim, InspectVictim, TreatVictim, ReplaceBattery, \
    ManualEarthquake, InspectBuilding
from aims.door_actions import OpenDoorAimsAction
from aims.agents import RoomAgent, VictimGod, ScoreGod, RescueWorker, \
    Explorer, EnergyGod
from aims.loggers.aims_logger import AimsLogger
from aims.loggers.victims_rescued_logger import VictimsRescuedLogger
from aims.loggers.messages_logger import MessageLogger

from aims.loggers.messages_logger import MessageLogger
from aims.move_actions_explorer import MoveWest2, MoveSouth2, MoveEast2, MoveNorth2
from aims.move_actions_rescue_worker import MoveWest3, MoveSouth3, MoveEast3, MoveNorth3
from aims.objects import Victim, Wall2, Door2, Score, Settings
from matrxs.actions.object_actions import DropObject
from matrxs.logger.log_tick import LogDuration
from matrxs.objects.simple_objects import Wall
from matrxs.world_builder import WorldBuilder
from matrxs.logger.log_idle_agents import LogIdleAgents


def create_factory(mirror_scenario=False):
    # Read scenario config file
    # debug scenario
    # config = json.load(open('aims/simple_scenario.json'))

    # tutorial scenario
    # config = json.load(open('aims/experiment_oefen_scenario.json'))

    # experiment scenario
    config = json.load(open('aims/experiment_scenario_1.json'))

    score_vis_placement = "right"
    if mirror_scenario:
        config = mirror_scenario_config(config)
        score_vis_placement = 'left'

    # Create world
    world = config['world']
    world_builder = WorldBuilder(
        shape=world['shape'], tick_duration=world['tick_duration'], simulation_goal=VictimRescueGoal(),
        run_matrxs_api=True, run_matrxs_visualizer=True, verbose=False)


    # create dir for this experiment with as name the time and date of the experiment
    current_exp_folder = datetime.now().strftime("exp_at_time_%Hh-%Mm-%Ss_date_%dd-%mm-%Yy")
    logger_save_folder = os.path.join("experiment_logs", current_exp_folder)


    # Add loggers
    world_builder.add_logger(logger_class=AimsLogger, save_path=logger_save_folder, file_name_prefix="aimslogs_")
    world_builder.add_logger(logger_class=LogDuration, save_path=logger_save_folder, file_name_prefix="duration_")
    world_builder.add_logger(logger_class=LogIdleAgents, save_path=logger_save_folder, file_name_prefix="idle_")
    world_builder.add_logger(logger_class=VictimsRescuedLogger, save_path=logger_save_folder, file_name_prefix="saved_victims_")
    world_builder.add_logger(logger_class=MessageLogger, save_path=logger_save_folder, file_name_prefix="messages_")

    # Add rooms
    rooms = config['rooms']
    i = 1   # Room ID
    for room in rooms:
        name = 'B' + str(i)
        init_room(world_builder, mirrored=mirror_scenario, room_name=name,
                  top_left=room['top_left'], dimensions=room['dimensions'],
                  door=room['door'], collapsed=room['collapsed'])
        i += 1

    # Add command post
    cp = config['command_post']
    init_command_post(world_builder, mirrored=mirror_scenario, room_name='command_post',
                      top_left=cp['top_left'], dimensions=cp['dimensions'], door=cp['door'])

    # Add victims
    victims = config['victims']
    i = 1   # Victim ID
    for vic in victims:
        # name = 'victim' + str(i)
        name = vic['name']
        world_builder.add_object(vic['location'], name=name, callable_class=Victim,
                                 alive=vic['alive'], treatment_need=vic['treatment_need'],
                                 need_increase_time=vic['need_increase_time'], visualize_depth=110)
        i += 1

    # Add automatically triggered earthquakes
    #earthquakes = config['earthquakes']
    # i = 1  # Earthquake ID
    # for quake in earthquakes:
    #    name = 'earthquake' + str(i)
    #    world_builder.add_agent([0, 0], agent_brain=EarthquakeGod(time=quake['time'], epicenter=quake['epicenter'], radius=quake['radius']), name=name, is_traversable=True, visualize_opacity=0)

    # Add event handling stuff
    world_builder.add_agent([0, 0], agent_brain=VictimGod(
    ), name='victim_god', is_traversable=True, visualize_opacity=0)
    world_builder.add_agent([world['shape'][0] - 1, world['shape'][1] - 1],
                            agent_brain=ScoreGod(), name='score_god', is_traversable=True,
                            visualize_opacity=0)
    world_builder.add_agent([world['shape'][0] - 1, world['shape'][1] - 1], agent_brain=EnergyGod(),
                            name='energy_god', is_traversable=True, visualize_opacity=0,
                            max_battery_replacements=config['max_battery_replacements'])
    world_builder.add_object([world['shape'][0] - 3, world['shape'][1] - 1], name='score',
                             callable_class=Score, victims_total=len(victims),
                             score_vis_placement=score_vis_placement)
    world_builder.add_object([0, 0], name='settings',
                             callable_class=Settings, config=config)

    # Add explorer
    explorer = config['explorer']

    action_map = {
        'w': MoveNorth2.__name__,
        'd': MoveEast2.__name__,
        's': MoveSouth2.__name__,
        'a': MoveWest2.__name__,
        'o': PickUpVictim.__name__,
        'n': DropObject.__name__,
        'r': OpenDoorAimsAction.__name__,
        'b': ManualEarthquake.__name__,
        'i': InspectBuilding.__name__,
        '1': 'battery_status'
    }

    world_builder.add_agent(explorer['location'], agent_brain=Explorer(earthquake_flashes=config['manual_earthquake']['earthquake_flashes']),
                            name=explorer['name'], key_action_map=action_map, is_human_agent=True,
                            visualize_colour=explorer['color'], energy=explorer['energy'],
                            energy_full=explorer['energy'], visualize_depth=125,
                            img_name="/static/images/explorer_small.png", memory={}, visualize_when_busy=True)

    # Add rescue_worker
    rescue_worker = config['rescue_worker']

    action_map = {
        'w': MoveNorth3.__name__,
        'd': MoveEast3.__name__,
        's': MoveSouth3.__name__,
        'a': MoveWest3.__name__,
        'o': PickUpVictim.__name__,
        'n': DropObject.__name__,
        'i': InspectVictim.__name__,
        'b': TreatVictim.__name__,
        'v': ReplaceBattery.__name__,
    }

    world_builder.add_agent(rescue_worker['location'], agent_brain=RescueWorker(),
                            name=rescue_worker['name'], key_action_map=action_map, visualize_depth=150,
                            is_human_agent=True, visualize_colour=rescue_worker['color'],
                            img_name="/static/images/rescue_worker.png", memory={}, visualize_when_busy=True)

    return world_builder


def init_room(world_builder, mirrored, room_name, top_left, dimensions, door, collapsed):
    bottom_right_x = top_left[0] + dimensions[0]
    bottom_right_y = top_left[1] + dimensions[1]
    bottom_right = [bottom_right_x, bottom_right_y]
    world_builder.add_agent(top_left, agent_brain=RoomAgent(top_left, bottom_right),
                            name=room_name, collapsed=collapsed, victims=[], agents=[],
                            visualize_opacity=0)
    #world_builder.add_object(location=top_left, name=room_name, callable_class=RoomObject, top_left=top_left, bottom_right=bottom_right, collapsed=collapsed)

    # set the colours for the walls
    if collapsed:
        color = '#595751' # grey
    else:
        color = '#11889b' # blue

    index = 0
    door_placed = False

    x = top_left[0]
    for y in range(top_left[1], top_left[1] + dimensions[1]):
        obj_name = room_name + '_' + str(index)
        if door == 'left' and not door_placed and y > top_left[1] and not mirrored:
            world_builder.add_object([x, y], name=obj_name, callable_class=Door2,
                                     is_open=False, room=room_name, collapsed=collapsed)
            door_placed = True
        elif door == 'left' and not door_placed and mirrored and y == top_left[1] + dimensions[1] - 2:
            world_builder.add_object([x, y], name=obj_name, callable_class=Door2,
                                     is_open=False, room=room_name, collapsed=collapsed)
            door_placed = True
        else:
            world_builder.add_object([x, y], name=obj_name, callable_class=Wall2,
                                     visualize_colour=color, room=room_name, collapsed=collapsed)
        index += 1

    x = top_left[0] + dimensions[0] - 1
    for y in range(top_left[1], top_left[1] + dimensions[1]):
        obj_name = room_name + '_' + str(index)
        if door == 'right' and not door_placed and y > top_left[1] and not mirrored:
            world_builder.add_object([x, y], name=obj_name, callable_class=Door2,
                                     is_open=False, room=room_name, collapsed=collapsed)
            door_placed = True
        elif door == 'right' and not door_placed and mirrored and y == top_left[1] + dimensions[1] - 2:
            world_builder.add_object([x, y], name=obj_name, callable_class=Door2,
                                     is_open=False, room=room_name, collapsed=collapsed)
            door_placed = True
        else:
            world_builder.add_object([x, y], name=obj_name, callable_class=Wall2,
                                     visualize_colour=color, room=room_name, collapsed=collapsed)
        index += 1

    y = top_left[1]
    for x in range(top_left[0] + 1, top_left[0] + dimensions[0] - 1):
        obj_name = room_name + '_' + str(index)
        if door == 'top' and not door_placed and not mirrored:
            world_builder.add_object([x, y], name=obj_name, callable_class=Door2,
                                     is_open=False, room=room_name, collapsed=collapsed)
            door_placed = True
        elif door == 'top' and not door_placed and mirrored and x == top_left[0] + dimensions[0] - 2:
            world_builder.add_object([x, y], name=obj_name, callable_class=Door2,
                                     is_open=False, room=room_name, collapsed=collapsed)
            door_placed = True
        else:
            world_builder.add_object([x, y], name=obj_name, callable_class=Wall2,
                                     visualize_colour=color, room=room_name, collapsed=collapsed)
        index += 1

    y = top_left[1] + dimensions[1] - 1
    for x in range(top_left[0] + 1, top_left[0] + dimensions[0] - 1):
        obj_name = room_name + '_' + str(index)
        if door == 'bottom' and not door_placed and not mirrored:
            world_builder.add_object([x, y], name=obj_name, callable_class=Door2,
                                     is_open=False, room=room_name, collapsed=collapsed)
            door_placed = True
        elif door == 'bottom' and not door_placed and mirrored and x == top_left[0] + dimensions[0] - 2:
            world_builder.add_object([x, y], name=obj_name, callable_class=Door2,
                                     is_open=False, room=room_name, collapsed=collapsed)
            door_placed = True
        else:
            world_builder.add_object([x, y], name=obj_name, callable_class=Wall2,
                                     visualize_colour=color, room=room_name, collapsed=collapsed)
        index += 1

    return world_builder


def init_command_post(world_builder, mirrored, room_name, top_left, dimensions, door):
    bottom_right_x = top_left[0] + dimensions[0]
    bottom_right_y = top_left[1] + dimensions[1]
    bottom_right = [bottom_right_x, bottom_right_y]
    world_builder.add_agent(top_left, agent_brain=RoomAgent(
        top_left, bottom_right), name=room_name, victims=[], agents=[], visualize_opacity=0)

    color = '#22c91c'

    index = 0
    door_placed = False

    x = top_left[0]
    for y in range(top_left[1], top_left[1] + dimensions[1]):
        obj_name = room_name + '_' + str(index)
        if door == 'left' and not door_placed and not mirrored:
            world_builder.add_object(
                [x, y], name=obj_name, callable_class=Door2, is_open=True)
            door_placed = True
        elif door == 'left' and not door_placed and mirrored and y == top_left[1] + dimensions[1] - 1:
            world_builder.add_object(
                [x, y], name=obj_name, callable_class=Door2, is_open=True)
            door_placed = True
        else:
            world_builder.add_object(
                [x, y], name=obj_name, callable_class=Wall, visualize_colour=color)
        index += 1

    x = top_left[0] + dimensions[0] - 1
    for y in range(top_left[1], top_left[1] + dimensions[1]):
        obj_name = room_name + '_' + str(index)
        if door == 'right' and not door_placed and not mirrored:
            world_builder.add_object(
                [x, y], name=obj_name, callable_class=Door2, is_open=True)
            door_placed = True
        elif door == 'right' and not door_placed and mirrored and y == top_left[1] + dimensions[1] - 1:
            world_builder.add_object(
                [x, y], name=obj_name, callable_class=Door2, is_open=True)
            door_placed = True
        else:
            world_builder.add_object(
                [x, y], name=obj_name, callable_class=Wall, visualize_colour=color)
        index += 1

    y = top_left[1]
    for x in range(top_left[0] + 1, top_left[0] + dimensions[0] - 1):
        obj_name = room_name + '_' + str(index)
        if door == 'top' and not door_placed and not mirrored:
            world_builder.add_object(
                [x, y], name=obj_name, callable_class=Door2, is_open=True)
            door_placed = True
        elif door == 'top' and not door_placed and mirrored and x == top_left[0] + dimensions[0] - 2:
            world_builder.add_object(
                [x, y], name=obj_name, callable_class=Door2, is_open=True)
            door_placed = True
        else:
            world_builder.add_object(
                [x, y], name=obj_name, callable_class=Wall, visualize_colour=color)
        index += 1

    y = top_left[1] + dimensions[1] - 1
    for x in range(top_left[0] + 1, top_left[0] + dimensions[0] - 1):
        obj_name = room_name + '_' + str(index)
        if door == 'bottom' and not door_placed and not mirrored:
            world_builder.add_object(
                [x, y], name=obj_name, callable_class=Door2, is_open=True)
            door_placed = True
        elif door == 'bottom' and not door_placed and mirrored and x == top_left[0] + dimensions[0] - 2:
            world_builder.add_object(
                [x, y], name=obj_name, callable_class=Door2, is_open=True)
            door_placed = True
        else:
            world_builder.add_object(
                [x, y], name=obj_name, callable_class=Wall, visualize_colour=color)
        index += 1

    return world_builder


def init_victim(world_builder, location, name, status, alive):
    world_builder.add_object(location=location, name=name, callable_class=Victim,
                             status=status, alive=alive)
    return world_builder


def mirror_scenario_config(config):
    """
    This function mirrors an AIMS scenario config (.json) file, both horizontally and vertically
    """

    # size of the world
    x_max = config["world"]["shape"][0]
    y_max = config["world"]["shape"][1]
    flip_door = {"top": "bottom", "bottom": "right",
                 "left": "right", "right": "left"}

    # mirror room starting coords horizontally and vertically
    for room in config['rooms']:
        room['top_left'][0] = x_max - \
            room['top_left'][0] - room["dimensions"][0]
        room['top_left'][1] = y_max - \
            room['top_left'][1] - room["dimensions"][1]
        room["door"] = flip_door[room["door"]]

    # command post mirror
    config['command_post']['top_left'][0] = x_max - \
        config['command_post']['top_left'][0] - \
        config['command_post']['dimensions'][0]
    config['command_post']['top_left'][1] = y_max - \
        config['command_post']['top_left'][1] - \
        config['command_post']['dimensions'][1]
    config['command_post']["door"] = flip_door[config['command_post']["door"]]

    # victims
    for victim in config['victims']:
        victim['location'][0] = x_max - victim['location'][0] - 1
        victim['location'][1] = y_max - victim['location'][1] - 1

    # rescue worker
    config['rescue_worker']['location'][0] = x_max - \
        config['rescue_worker']['location'][0] - 1
    config['rescue_worker']['location'][1] = y_max - \
        config['rescue_worker']['location'][1] - 1

    # explorer
    config['explorer']['location'][0] = x_max - \
        config['explorer']['location'][0] - 1
    config['explorer']['location'][1] = y_max - \
        config['explorer']['location'][1] - 1

    # earthquake epicenter
    config['manual_earthquake']['epicenter'][0] = x_max - \
        config['manual_earthquake']['epicenter'][0] - 1
    config['manual_earthquake']['epicenter'][1] = y_max - \
        config['manual_earthquake']['epicenter'][1] - 1

    return config
