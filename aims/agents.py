import copy

import numpy as np

from matrxs.agents.agent_brain import AgentBrain
from aims.actions import MoveToLocation, PickUpVictim, UpdateRoomContent, InspectVictim, HurtVictim, \
    TreatVictim, StartEarthquake, EndEarthquake, Collapse, UpdateScore, EndTrial, UpdateEnergy, \
    ReplaceBattery, ManualEarthquake, InspectBuilding
from matrxs.agents.human_agent_brain import HumanAgentBrain
from aims.door_actions import OpenDoorAimsAction, CloseDoorAction, OpenDoorActionCollapsed
from aims.objects import Victim, Wall2
from matrxs.utils.message import Message


class Robot(AgentBrain):
    def __init__(self, energy=0.0):
        super().__init__()
        self.energy = energy

    def filter_observations(self, state):
        new_state = {}
        own_location = self.agent_properties['location']
        adjacent_locations = get_adjacent_locations(state, own_location)

        # The agent can't perceive the collapsed status of and victims in a room unless it is next to the room
        for obj_id, obj_properties in state.items():
            new_state[obj_id] = obj_properties

            if 'location' in obj_properties:
                if 'Room' in obj_properties['class_inheritance']:
                    if not obj_properties['location'] in adjacent_locations:
                        new_state[obj_id]['collapsed_status'] = ''
                        new_state[obj_id]['victims'] = ''

                if 'Victim' in obj_properties['class_inheritance']:
                    if not obj_properties['location'] in adjacent_locations:
                        del new_state[obj_id]

        return new_state

    def decide_on_action(self, state):
        action = None
        action_arguments = None
        goal = 'room2'  # TODO define real goal function
        goal_location = state[goal]['location']
        own_location = self.agent_properties['location']

        goal_adjacent_locations = get_adjacent_locations(state, goal_location)

        if not own_location in goal_adjacent_locations:
            own_adjacent_locations = get_adjacent_locations(state, own_location)
            adjacent_overlap = list(set(own_adjacent_locations) & set(goal_adjacent_locations))
            if adjacent_overlap:  # If own adjacent locations overlap with goal adjacent locations
                action = MoveToLocation.__name__
                action_arguments = {'location': adjacent_overlap[0]}  # Move to first overlapping location

        return action, action_arguments


class RescueWorker(HumanAgentBrain):
    def __init__(self):
        super().__init__()

        # Memory (i.e., list of rooms/victims the agent has perceived)
        # self.memory = {}

        self.exchanged_info = []

    def filter_observations(self, state):
        new_state = {}
        own_location = self.agent_properties['location']
        adjacent_locations = get_adjacent_locations(state, own_location)
        earthquake = False

        for obj_id, obj_properties in state.items():

            new_state[obj_id] = obj_properties

            # Observe if there was an earthquake
            if 'location' in obj_properties:
                if 'AreaTile' in obj_properties['class_inheritance']:
                    earthquake = True

                # Store adjacent objects in memory (only applies to victims, not rooms because the human can't perceive the room status)
                if obj_properties['location'] in adjacent_locations:
                    if 'Victim' in obj_properties['class_inheritance']:
                        victim = obj_properties['name']

                        # If the victim was not already stored in memory, add it
                        if victim not in self.agent_properties[ 'memory']:
                            self.agent_properties['memory'][victim] = obj_properties
                            self.agent_properties['memory'][victim]['alive'] = 'unknown'
                            self.agent_properties['memory'][victim]['treatment_need'] = 'unknown'
                            self.agent_properties['memory'][victim]['img_name'] = "/static/images/victim_status_unknown.png"

                # Filter state
                if 'Wall2' in obj_properties['class_inheritance']:
                    if obj_properties['room'] not in self.agent_properties[
                        'memory']:  # If the room to which this wall belongs is not in memory, the agent can't perceive its collapsed status
                        new_state[obj_id]['collapsed'] = ''
                        new_state[obj_id]['visualization']['colour'] = '#000000'

                if 'RoomAgent' in obj_properties['class_inheritance']:
                    if obj_properties['name'] not in self.agent_properties[
                        'memory']:  # If the room that this RoomAgent represents is not in memory, the agent can't perceive the room's properties
                        # del new_state[obj_id]
                        new_state[obj_id]['collapsed'] = 'unknown'

                if 'Victim' in obj_properties['class_inheritance']:
                    # If the victim is not in memory, the agent can't perceive it
                    if obj_properties['name'] not in self.agent_properties['memory']:
                        del new_state[obj_id]
                    # If the status of the victim is unknown, the agent can't perceive it
                    elif self.agent_properties['memory'][obj_id]['alive'] == 'unknown':
                        new_state[obj_id]['alive'] = 'unknown'
                        new_state[obj_id]['treatment_need'] = 'unknown'
                        new_state[obj_id]['visualization']['colour'] = '#5B9BD5'
                        new_state[obj_id]['img_name'] = "/static/images/victim_status_unknown.png"
                    # otherwise if the victim is in memory, we perceive the victims state as we memorized
                    elif obj_properties['name'] in self.agent_properties['memory']:
                        new_state[obj_id]['alive'] = self.agent_properties['memory'][obj_id]
                        new_state[obj_id]['treatment_need'] = self.agent_properties['memory'][obj_id]['alive']
                        new_state[obj_id]['visualization']['colour'] = self.agent_properties['memory'][obj_id][
                            'treatment_need']
                        new_state[obj_id]['img_name'] = self.agent_properties['memory'][obj_id]['img_name']

                if 'Score' in obj_properties['class_inheritance']:  # The human can't perceive some score items
                    new_state[obj_id]['victims_total'] = ''
                    new_state[obj_id]['victims_alive'] = ''

                if 'Explorer' in obj_properties[
                    'class_inheritance']:  # The human can't perceive the explorer's energy level
                    new_state[obj_id]['energy'] = ''

        # loop through exchanged info
        for i, mssg_content in enumerate(copy.copy(self.exchanged_info)):

            if mssg_content['id'] not in self.agent_properties['memory']:
                self.agent_properties['memory'][mssg_content['id']] = mssg_content['properties']

            try:
                del self.exchanged_info[i]
            except:
                print("Failed to delete exchanged information.")
                pass



        # If there was an earthquake, the agents no longer knows the status of rooms it previously knew were safe
        memory = copy.deepcopy(self.agent_properties['memory'])
        if earthquake:
            for obj_id, obj_properties in memory.items():
                if 'Wall2' in obj_properties['class_inheritance'] and not obj_properties['collapsed']:
                    del self.agent_properties['memory'][obj_id]

        return new_state

    def decide_on_action(self, state, usrinput):
        action_kwargs = {}
        agent_id = self.agent_properties["obj_id"]

        # if there was no userinput do nothing
        if usrinput is None or usrinput == []:
            return None, {}

        # take the last usrinput (for now), and fetch the action associated with that key
        usrinput = usrinput[-1]
        action = self.key_action_map[usrinput]

        # if the user chose a xxxVictim action, choose the object the agent is standing on
        if action == PickUpVictim.__name__ or action == InspectVictim.__name__ or action == TreatVictim.__name__:
            # Assign it to the arguments list
            action_kwargs['max_objects'] = 1  # Set max amount of objects
            action_kwargs['object_id'] = None

            # Get all perceived objects
            objects = list(state.keys())

            # Remove all humans, robots, gods. The command post and world.
            objects = [obj for obj in objects if 'explorer' not in obj.lower()]
            objects = [obj for obj in objects if 'rescue_worker' not in obj.lower()]
            objects = [obj for obj in objects if 'god' not in obj.lower()]
            objects = [obj for obj in objects if 'command_post' not in obj.lower()]
            objects = [obj for obj in objects if 'world' not in obj.lower()]

            # find objects that are located at the same location as the agent
            for object_id in objects:
                if state[agent_id]['location'] == state[object_id]['location']:
                    # object_in_range.append(object_id)
                    action_kwargs['object_id'] = object_id

        # if the user chose to do a open or close door action, find a door to open/close within 1 block
        elif action == OpenDoorAimsAction.__name__ or action == CloseDoorAction.__name__:
            action_kwargs['door_range'] = 1
            action_kwargs['object_id'] = None

            # Get all doors from the perceived objects
            objects = list(state.keys())
            doors = [obj for obj in objects if 'is_open' in state[obj]]

            # get all doors within range
            doors_in_range = []
            for object_id in doors:
                # Select range as just enough to grab that object
                dist = int(np.ceil(np.linalg.norm(
                    np.array(state[object_id]['location']) - np.array(
                        state[self.agent_properties["name"]]['location']))))
                if dist <= action_kwargs['door_range']:
                    doors_in_range.append(object_id)

            # choose a random door within range
            if len(doors_in_range) > 0:
                action_kwargs['object_id'] = self.rnd_gen.choice(doors_in_range)

        elif action == ReplaceBattery.__name__:
            # Assign it to the arguments list
            action_kwargs['max_objects'] = 1  # Set max amount of objects
            action_kwargs['object_id'] = None

            # check if explorer is at the same location as the agent
            if state[agent_id]['location'] == state['explorer']['location']:
                # object_in_range.append(object_id)
                action_kwargs['object_id'] = 'explorer'

        return action, action_kwargs

    def _set_messages(self, messages=None):
        """
        This method is called by the GridWorld.
        It sets all messages intended for this agent to a list that it can access and read.

        Note; This method should NOT be overridden!

        :param messages: A list of dictionaries that contain a 'from_id', 'to_id' and 'content.
        If messages is set to None (or no messages are used as input), only the previous messages are removed
        """

        # We empty all received messages as this is from the previous tick
        # self.received_messages = []

        # Loop through all messages and create a Message object out of the dictionaries.
        for mssg in messages:

            if mssg.message_type == "info_exchange":
                self.exchanged_info.append(mssg.content)

            else:

                # Since each message is secretly wrapped inside a Message (as its content), we unpack its content and
                # set that as the actual received message.
                received_message = mssg.content

                # Add the message object to the received messages
                self.received_messages.append(received_message)

class Explorer(HumanAgentBrain):
    def __init__(self, earthquake_flashes=1):
        super().__init__()

        # Memory (i.e., list of rooms/victims the agent has perceived)
        # self.memory = {}
        # whether an earthquake was triggered and still going on
        self.earthquake_triggered = False
        # number of flashes to show after earthquake, minimun of 1
        self.earthquake_flashes = earthquake_flashes
        # how many ticks earthquake is going on
        self.earthquake_ticks = 0
        # note if we are currently working on opening a door, so that we can send a global message
        # after we are done
        self.opening_door = {"WIP": False, "room": -1}


    def filter_observations(self, state):
        new_state = {}
        own_location = self.agent_properties['location']
        adjacent_locations = get_adjacent_locations(state, own_location)
        earthquake = False

        for obj_id, obj_properties in state.items():
            new_state[obj_id] = obj_properties

            # Observe if there was an earthquake
            if 'location' in obj_properties:
                if 'AreaTile' in obj_properties['class_inheritance']:
                    earthquake = True

            # Store adjacent objects in memory
            if 'location' in obj_properties:
                if obj_properties['location'] in adjacent_locations:

                    if 'Victim' in obj_properties['class_inheritance']:
                        victim = obj_properties['name']
                        # If the victim was not already stored in memory, add it
                        if victim not in self.agent_properties['memory']:
                            self.agent_properties['memory'][victim] = obj_properties
                            self.agent_properties['memory'][victim]['alive'] = 'unknown'
                            self.agent_properties['memory'][victim]['treatment_need'] = 'unknown'

                            # send this info to the rescue worker
                            content = {"id": victim, "properties": obj_properties}
                            self.send_message(Message(content=content, from_id=self.agent_id, to_id="rescue_worker",
                                    type="info_exchange"))

            # Filter state
            if 'location' in obj_properties:
                if 'Wall2' in obj_properties['class_inheritance']:
                    if obj_properties['room'] not in self.agent_properties[
                        'memory']:  # If the room to which this wall belongs is not in memory, the agent can't perceive its collapsed status
                        new_state[obj_id]['collapsed'] = ''
                        new_state[obj_id]['visualization']['colour'] = '#000000'

                if 'RoomAgent' in obj_properties['class_inheritance']:
                    if obj_properties['name'] not in self.agent_properties[
                        'memory']:  # If the room that this RoomAgent represents is not in memory, the agent can't perceive the room's properties
                        # del new_state[obj_id]
                        new_state[obj_id]['collapsed'] = 'unknown'

                if 'Victim' in obj_properties['class_inheritance']:
                    # If the victim is not in memory, the agent can't perceive it
                    if obj_properties['name'] not in self.agent_properties['memory']:
                        del new_state[obj_id]

                    # If the victim's status is not in memory, the agent can't perceive it
                    elif self.agent_properties['memory'][obj_id]['alive'] == 'unknown':
                        new_state[obj_id]['alive'] = 'unknown'
                        new_state[obj_id]['treatment_need'] = 'unknown'
                        new_state[obj_id]['visualization']['colour'] = '#5B9BD5'
                        new_state[obj_id]['img_name'] = "/static/images/victim_status_unknown.png"

                if 'Score' in obj_properties['class_inheritance']:  # The human can't perceive some score items
                    new_state[obj_id]['victims_total'] = ''
                    new_state[obj_id]['victims_alive'] = ''

        # If there was an earthquake, the agents no longer knows the status of rooms it previously knew were safe
        memory = copy.deepcopy(self.agent_properties['memory'])
        if earthquake:
            for obj_id, obj_properties in memory.items():
                if 'Wall2' in obj_properties['class_inheritance'] and not obj_properties['collapsed']:
                    del self.agent_properties['memory'][obj_id]

        return new_state


    def decide_on_action(self, state, usrinput):
        action_kwargs = {}
        agent_id = self.agent_properties["obj_id"]

        # check if we have been opening a door (and thus are now done). If that is the case, send
        # a global message that the door is now opened
        if self.opening_door['WIP']:
            content = f"De ingang van gebouw {self.opening_door['room']} is vrij van puin."
            self.send_message(Message(content=content, from_id=self.agent_id, to_id=None))
            self.opening_door = {'WIP': False, "room": -1}

        # when we triggered an earthquake manually, flash the screen a couple times
        if self.earthquake_triggered is not False:
            # count number of ticks since earthquake
            self.earthquake_ticks += 1

            # stop flashing if we reached the desired number of flashes
            if self.earthquake_ticks >= self.earthquake_flashes * 2 - 1:
                self.earthquake_triggered = False

            # remove flash
            if (self.earthquake_ticks % 2) == 0:
                return StartEarthquake.__name__, {}
            # flash screen
            else:
                return EndEarthquake.__name__, {}

        # if there was no usrinput do nothing
        if usrinput is None or usrinput == []:
            return None, {}

        # take the last usrinput (for now), and fetch the action associated with that key
        usrinput = usrinput[-1]
        action = self.key_action_map[usrinput]

        # If the explorer performs a move action while carrying a person, we move slower
        # Gekozen om dit uit te zetten voor het experiment.
        if "move" in action.lower() and self.agent_properties["is_carrying"] != []:
           action_kwargs["action_duration"] = state["settings"]["explorer_victim_carry_move_ticks"]

        # if the user chose a xxxVictim action, choose the object the agent is standing on
        elif action == PickUpVictim.__name__ or action == InspectVictim.__name__ or action == TreatVictim.__name__:
            # the explorer has more difficulty with picking up a person
            action_kwargs["action_duration"] = state["settings"]["explorer_victim_pickup_ticks"]

            # Assign it to the arguments list
            action_kwargs['max_objects'] = 1  # Set max amount of objects
            action_kwargs['object_id'] = None

            # Get all perceived objects
            objects = list(state.keys())

            # Remove all humans, robots, gods. The command post and world.
            objects = [obj for obj in objects if 'explorer' not in obj.lower()]
            objects = [obj for obj in objects if 'rescue_worker' not in obj.lower()]
            objects = [obj for obj in objects if 'god' not in obj.lower()]
            objects = [obj for obj in objects if 'command_post' not in obj.lower()]
            objects = [obj for obj in objects if 'world' not in obj.lower()]

            # find objects that are located at the same location as the agent
            for object_id in objects:
                if state[agent_id]['location'] == state[object_id]['location']:
                    # object_in_range.append(object_id)
                    action_kwargs['object_id'] = object_id

            # Give the user's memory to be updated by the inspect action
            if action == InspectVictim.__name__:
                action_kwargs['memory'] = self.agent_properties['memory']

        # if the user chose to do a open or close door action, find a door to open/close within 1 block
        elif action == OpenDoorAimsAction.__name__ or action == CloseDoorAction.__name__:
            action_kwargs['door_range'] = 1
            action_kwargs['object_id'] = None

            # Get all doors from the perceived objects
            objects = list(state.keys())
            doors = [obj for obj in objects if 'is_open' in state[obj]]

            # get all doors within range
            doors_in_range = []
            for object_id in doors:
                # Select range as just enough to grab that object
                dist = int(np.ceil(np.linalg.norm(
                    np.array(state[object_id]['location']) - np.array(
                        state[self.agent_properties["name"]]['location']))))
                if dist <= action_kwargs['door_range']:
                    doors_in_range.append(object_id)

            # choose a random door within range
            if len(doors_in_range) > 0:
                action_kwargs['object_id'] = self.rnd_gen.choice(doors_in_range)

                # If the door belongs to a collapsed room, do an action with a longer duration
                if state[action_kwargs['object_id']]['collapsed']:
                    action = OpenDoorActionCollapsed.__name__

                self.opening_door = {"WIP": True, "room": state[action_kwargs['object_id']]['room']}

        # track when we triggered the earthquake
        elif action == ManualEarthquake.__name__:
            self.earthquake_triggered = True
            self.earthquake_ticks = 0

        elif action == "battery_status":
            print("Requesting battery status message")
            self.send_message(Message(content=f"Resterende batterij: {self.agent_properties['energy']}", from_id=self.agent_id, to_id=None))
            return None, {}

        elif action == InspectBuilding.__name__:

            action_kwargs['object_id'] = None
            max_inspect_range = 1

            # Get all walls from the perceived objects
            objects = list(state.keys())
            walls = [obj for obj in objects if 'class_inheritance' in state[obj] and \
                Wall2.__name__ in state[obj]['class_inheritance']]

            # get all walls within range
            walls_in_range = []
            for object_id in walls:
                # Select range as just enough to grab that object
                dist = int(np.ceil(np.linalg.norm(
                    np.array(state[object_id]['location']) - np.array(
                        state[self.agent_properties["name"]]['location']))))

                # select any wall within range
                if dist <= max_inspect_range:
                    action_kwargs['object_id'] = object_id
                    break


        # If the battery is empty, do nothing
        if self.agent_properties['energy'] == 0 and action != ManualEarthquake.__name__:

            # if the explorer is in a collapsed building with no battery, actions are not disabled
            for ra_id, ra_obj in state.items():
                if 'isAgent' in ra_obj \
                        and ra_obj['isAgent'] \
                        and "RoomAgent" in ra_obj['class_inheritance'] \
                        and ra_obj['collapsed'] and self.agent_id in ra_obj['agents']:
                    action_arguments = {
                        'agent': self.agent_id,
                        'energy': 250
                    }
                    return UpdateEnergy.__name__, action_arguments


            return None, {}

        # otherwise check which action is mapped to that key and return it
        return action, action_kwargs



# TODO make separate version of this function in which corners are removed
def get_adjacent_locations(state, location):
    grid_size = state['World']['grid_shape']
    x_max = grid_size[0] - 1
    y_max = grid_size[1] - 1
    adjacent_locations = []
    x_possible = [location[0]]
    y_possible = [location[1]]

    if 0 < location[0] <= x_max:
        x_possible.append(location[0] - 1)
    if 0 <= location[0] < x_max:
        x_possible.append(location[0] + 1)
    if 0 < location[1] <= y_max:
        y_possible.append(location[1] - 1)
    if 0 <= location[1] < y_max:
        y_possible.append(location[1] + 1)

    for x in x_possible:
        for y in y_possible:
            adjacent_locations.append((x, y))

    # Romy: the line below is commented, so the agent can perceive objects where the agent is standing on top
    # adjacent_locations.remove((location[0], location[1]))  # Remove goal location

    return adjacent_locations


# Agent that represents a room
class RoomAgent(AgentBrain):
    def __init__(self, top_left, bottom_right, collapsed=False, victims=[], agents=[]):
        super().__init__()

        # Top left coordinate of the room
        self.top_left = top_left

        # Bottom right coordinate of the room
        self.bottom_right = bottom_right

        # Collapsed (boolean)
        self.collapsed = collapsed

        # Victim list
        self.victims = victims

        # Agent list
        self.agents = agents

    def filter_observations(self, state):
        new_state = {}
        top_left = self.top_left
        bottom_right = self.bottom_right

        # A room agent can perceive the victims and agents in its room
        for obj_id, obj_properties in state.items():
            if 'location' in obj_properties:
                location = obj_properties['location']
            if bottom_right[0] > location[0] >= top_left[0] and bottom_right[1] > location[1] >= top_left[1]:
                new_state[obj_id] = obj_properties

        new_state['settings'] = state['settings']  # It can also perceive the settings object

        return new_state

    def decide_on_action(self, state):
        action = None
        action_arguments = None
        victims = []
        agents = []
        earthquake = False

        for obj_id, obj_properties in state.items():
            if 'location' in obj_properties:
                if 'Victim' in obj_properties['class_inheritance']:
                    victims.append(obj_id)
                if 'AgentBrain' in obj_properties['class_inheritance'] and not obj_properties[
                                                                                   'name'] == self.agent_name:
                    agents.append(obj_id)
                if 'AreaTile' in obj_properties['class_inheritance']:  # Check if room was hit by an earthquake
                    earthquake = True

        # ignore earthquakes if this building is not specified as being affected
        # if not earthquake or earthquake and not self.agent_name in state['settings']['affected_buildings']:
        action = UpdateRoomContent.__name__
        action_arguments = {
            'victims': victims,
            'agents': agents
        }

        # If the room was hit by an earthquake, and it is specified as being affected, it has a chance of collapsing
        # else:
        #     p_total = state['settings']['p_collapse_after_earthquake']
        #     earthquake_flashes = state['settings']['earthquake_flashes']
        #
        #     # The earthquake lasts x ticks and the building has a chance of collapsing at each tick. So for a 0.8
        #     # chance of collapsing, the probability of not collapsing is the fifth root of 0.2 for each tick
        #     p = (1 - p_total) ** (1. / earthquake_flashes)
        #     collapse = np.random.choice([True, False], p=[1 - p, p])
        #     if collapse:
        #         walls = []
        #         for obj_id, obj_properties in state.items():
        #             if 'location' in obj_properties:
        #                 if 'Wall2' in obj_properties['class_inheritance']:
        #                     walls.append(obj_id)
        #         action = Collapse.__name__
        #         action_arguments = {
        #             'walls': walls,
        #             'victims': victims
        #         }

        return action, action_arguments


# God agent that manages the status of victims
class VictimGod(AgentBrain):
    def __init__(self):
        super().__init__()

        self.victims_saved = []

    def filter_observations(self, state):
        new_state = {}

        # The agent perceives all living victims and the world (to get the number of ticks that have expired)
        for obj_id, obj_properties in state.items():
            if 'location' in obj_properties:
                if 'Victim' in obj_properties['class_inheritance'] and obj_properties['alive']:
                    new_state[obj_id] = obj_properties

            if 'nr_ticks' in obj_properties:
                new_state[obj_id] = obj_properties

            # keep track of which victims have been saved
            if obj_id == 'command_post':
                self.victims_saved = obj_properties['victims']

        return new_state

    def decide_on_action(self, state):
        action = None
        action_arguments = None

        ticks = state['World']['nr_ticks']
        victims = []

        # Get all victims for whom the treatment_need should be increased
        for obj_id, obj_properties in state.items():
            # check victims
            if 'location' in obj_properties and Victim.__name__ in obj_properties['class_inheritance']:

                # check how often they should worsen in health, and if that moment is now
                increase_time = obj_properties['need_increase_time']
                if increase_time > 0:
                    # check if the victim is already in the CP or completely health, if so,
                    # the victim does not worsen in health over time
                    if ticks % increase_time == 0 and \
                            not obj_properties['obj_id'] in self.victims_saved and \
                            not obj_properties['treatment_need'] == 0 and \
                            ticks != 0:
                        action = HurtVictim.__name__
                        victims.append(obj_id)

        if action is not None:
            action_arguments = {
                'victims': victims
            }

        return action, action_arguments


# God agent that manages earthquakes
class EarthquakeGod(AgentBrain):
    def __init__(self, time, epicenter, radius):
        super().__init__()

        # Start time of earthquake (ticks)
        self.time = time

        # Epicenter (start location)
        self.epicenter = epicenter

        # Radius (excluding epicenter) (int)
        self.radius = radius

        # Calculate area
        area = []
        y_size = radius + 1  # Current size on y axis, decreases each loop in order to create a diamond shape
        for i in range(0, radius + 1):
            x = epicenter[0] + i
            for j in range(0, y_size):
                y = epicenter[1] + j
                area.append([x, y])

                if j > 0:
                    y = epicenter[1] - j
                    area.append([x, y])

            if i > 0:
                x = epicenter[0] - i
                for j in range(0, y_size):
                    y = epicenter[1] + j
                    area.append([x, y])

                    if j > 0:
                        y = epicenter[1] - j
                        area.append([x, y])

            y_size -= 1

        self.area = area

    def decide_on_action(self, state):
        action = None
        action_arguments = None

        # If earthquake start time (ticks) has been reached, start the earthquake
        ticks = state['World']['nr_ticks']
        if ticks == self.time:
            action = StartEarthquake.__name__
            action_arguments = {
                'area': self.area,
            }

        # 5 ticks after start of the earthquake, end it
        if ticks == self.time + 5:
            action = EndEarthquake.__name__
            action_arguments = {
                'area': self.area,
            }

        return action, action_arguments


# God agent that keeps score
class ScoreGod(AgentBrain):
    def __init__(self):
        super().__init__()

    def decide_on_action(self, state):
        victims_total = state['score']['victims_total']
        # victims_retrieved from the previous tick. Needed because otherwise the trial ends before the score is
        # updated on the screen
        victims_retrieved_prev = state['score']['victims_retrieved']
        victims_alive = 0

        for obj_id, obj_properties in state.items():
            if 'location' in obj_properties:
                if 'Victim' in obj_properties['class_inheritance']:
                    if obj_properties['alive']:
                        victims_alive += 1

            if obj_id == 'command_post':
                victims_retrieved = len(obj_properties['victims'])

            if 'nr_ticks' in obj_properties:
                ticks_elapsed = obj_properties['nr_ticks']

        if victims_retrieved_prev == victims_total:  # End trial if all victims have been retrieved
            action = EndTrial.__name__
            action_arguments = {}

        else:
            action = UpdateScore.__name__
            action_arguments = {
                'victims_alive': victims_alive,
                'victims_retrieved': victims_retrieved,
                'ticks_elapsed': ticks_elapsed
            }

        return action, action_arguments


# God agent that updates energy levels
class EnergyGod(AgentBrain):
    def __init__(self):
        super().__init__()

    def decide_on_action(self, state):
        action = None
        action_arguments = None

        batteries_replaced = state['score']['batteries_replaced']
        max_battery_replacements = self.agent_properties['max_battery_replacements']
        if batteries_replaced < max_battery_replacements:  # After x battery replacements, the energy doesn't decline anymore
            agent = state['explorer']
            energy = agent['energy']
            if energy > 0:
                energy_new = energy - 1
                action = UpdateEnergy.__name__
                action_arguments = {
                    'agent': agent['name'],
                    'energy': energy_new
                }

        return action, action_arguments
