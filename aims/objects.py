from matrxs.objects.env_object import EnvObject


# Victim
class Victim(EnvObject):
    def __init__(self, location, name='victim', alive=True, treatment_need=None, need_increase_time=0):
        super().__init__(name=name, location=location, is_traversable=True, visualize_shape='img',
                         class_callable=Victim, img_name="/static/images/victim_status_unknown.png")

        # Victim is alive or not
        self.alive = alive
        self.add_property('alive', self.alive)

        # Treatment need (0=none, 1=low, 2=moderate, 3=high)
        self.treatment_need = treatment_need
        self.add_property('treatment_need', self.treatment_need)

        # Number of ticks until treatment_need increases
        self.need_increase_time = need_increase_time
        self.add_property('need_increase_time', need_increase_time)

        # Color is based on properties
        if alive:
            if treatment_need == 0:
                self.visualize_colour = '#70AD47'
                self.change_property('img_name', "/static/images/victim_status_healthy.png")
            elif treatment_need == 1:
                self.visualize_colour = '#FFC000'
                self.change_property('img_name', "/static/images/victim_status_injured.png")
            elif treatment_need == 2:
                self.visualize_colour = '#ED7D31'
                self.change_property('img_name', "/static/images/victim_status_badly_injured.png")
            elif treatment_need == 3:
                self.visualize_colour = '#FF0000'
                self.change_property('img_name', "/static/images/victim_status_extremely_injured.png")
        else:
            self.visualize_colour = '#3F0101'
            self.change_property('img_name', "/static/images/victim_status_dead.png")


class EpiCenter(EnvObject):

    def __init__(self, location, name="AreaTile", visualize_colour="#8ca58c", visualize_depth=None,
                 visualize_opacity=1.0, visualize_shape="1", **custom_properties):
        """
        A simple AreaTile object. Is always traversable, not movable, the colour can be set but has otherwise the default EnvObject
        property values. Can be used to define different areas in the GridWorld.
        :param location: The location of the area.
        :param name: The name, default "AreaTile".
        :param visualize_colour: hex colour code for tile
        """
        super().__init__(name=name, location=location, visualize_colour=visualize_colour,
                         is_traversable=True, is_movable=False, class_callable=EpiCenter,
                         visualize_depth=visualize_depth, visualize_opacity=visualize_opacity,
                         visualize_shape=visualize_shape, **custom_properties)


# Abstract object that represents a room
class RoomObject(EnvObject):
    def __init__(self, location, name='RoomObject', top_left=0, bottom_right=0, collapsed=False):
        super().__init__(name=name, location=location, visualize_opacity=0,
                         is_traversable=True, class_callable=RoomObject)

        # Top left coordinate of the room
        self.top_left = top_left
        self.add_property('top_left', self.top_left)

        # Bottom right coordinate of the room
        self.bottom_right = bottom_right
        self.add_property('bottom_right', self.bottom_right)

        # Collapsed (boolean)
        self.collapsed = collapsed
        self.add_property('collapsed', self.collapsed)


# Wall (custom)
class Wall2(EnvObject):
    def __init__(self, location, name="Wall2", visualize_colour="#000000", room=None, collapsed=False):
        super().__init__(name=name, location=location, visualize_colour=visualize_colour,
                         is_traversable=False, class_callable=Wall2)

        # The room to which the wall belongs
        self.room = room
        self.add_property('room', self.room)

        # Collapsed (boolean)
        self.collapsed = collapsed
        self.add_property('collapsed', self.collapsed)


# Door (custom)
class Door2(EnvObject):

    def __init__(self, location, is_open, name="Door2", open_colour="#006400", closed_colour="#640000", room=None, collapsed=False):
        # Whether the door is by default open or closed is stored in the defaults.json and obtained like this;
        self.is_open = is_open

        # We save the colours for open and close and assign the appriopriate value based on current state
        self.open_colour = open_colour
        self.closed_colour = closed_colour
        current_color = self.closed_colour
        if self.is_open:
            current_color = self.open_colour

        # If the door is open or closed also determines its is_traversable property
        is_traversable = self.is_open



        super().__init__(location=location, name=name, is_traversable=is_traversable, visualize_colour=current_color,
                         is_open=self.is_open, class_callable=Door2)

        # The room to which the door belongs
        self.room = room
        self.add_property('room', self.room)

        # Collapsed (boolean)
        self.collapsed = collapsed
        self.add_property('collapsed', self.collapsed)

    def open_door(self):
        """
        Opens the door, changes the colour and sets the properties as such.
        """

        # Set the attribute
        self.is_open = True
        # Set the appropriate property
        self.change_property("is_open", self.is_open)
        # Traversable depends on this as well
        self.is_traversable = self.is_open

        # if a door of a collapsed building has been cleared, the door becomes less red
        if self.collapsed:
            self.visualize_colour = "#d07474"

        # if the door is open and the human can enter (non-collapsed building), the door is green
        else:
            # Also change the colour
            self.visualize_colour = self.open_colour

    def close_door(self):
        """
        Closes the door, changes the colour and sets the properties as such.
        """

        # Set the attribute
        self.is_open = False
        # Set the appropriate property
        self.change_property("is_open", self.is_open)
        # Traversable depends on this as well
        self.is_traversable = self.is_open
        # Also change the colour
        self.visualize_colour = self.closed_colour


# Score
class Score(EnvObject):
    def __init__(self, location, name="score", victims_total=0, score_vis_placement='right'):
        super().__init__(name=name, location=location, visualize_opacity=0,
                         is_traversable=True, class_callable=Score)

        self.victims_total = victims_total
        self.add_property('victims_total', self.victims_total)

        self.victims_alive = 0
        self.add_property('victims_alive', self.victims_alive)

        self.victims_retrieved = 0
        self.add_property('victims_retrieved', self.victims_retrieved)

        self.ticks_elapsed = 0
        self.add_property('ticks_elapsed', self.ticks_elapsed)

        self.batteries_replaced = 0
        self.add_property('batteries_replaced', self.batteries_replaced)

        self.add_property('score_vis_placement', score_vis_placement)



# Settings (this object is there so that the json config file is only read in one place)
class Settings(EnvObject):
    def __init__(self, location, name="settings", config={}, **kwargs):
        super().__init__(name=name, location=location, visualize_opacity=0,
                         is_traversable=True, class_callable=Settings)

        # # Probability that a room collapses after an automatic earthquake
        # self.p_collapse_after_earthquake = config['p_collapse_after_earthquake']
        # self.add_property('p_collapse_after_earthquake', self.p_collapse_after_earthquake)
        #
        # # Probability that a victim in a room gets hurt if the room collapses after an automatic earthquake
        # self.p_victim_gets_hurt_after_room_collapse = config['p_victim_gets_hurt_after_room_collapse']
        # self.add_property('p_victim_gets_hurt_after_room_collapse', self.p_victim_gets_hurt_after_room_collapse)

        # Maximum number of battery replacements allowed
        self.max_battery_replacements = config['max_battery_replacements']
        self.add_property('max_battery_replacements', self.max_battery_replacements)

        # Energy cost per move action
        self.energy_cost_move = config['energy_cost_move']
        self.add_property('energy_cost_move', self.energy_cost_move)

        # Energy cost per open door action
        self.energy_cost_door = config['energy_cost_door']
        self.add_property('energy_cost_door', self.energy_cost_door)

        # Energy cost per open collapsed door action
        self.energy_cost_door_collapsed = config['energy_cost_door_collapsed']
        self.add_property('energy_cost_door_collapsed', self.energy_cost_door_collapsed)

        # Energy cost when earthquake occurs
        self.energy_cost_earthquake = config['energy_cost_earthquake']
        self.add_property('energy_cost_earthquake', self.energy_cost_earthquake)

        # Epicenter of manual earthquake
        self.epicenter = config['manual_earthquake']['epicenter']
        self.add_property('epicenter', self.epicenter)

        # radius of the earthquake
        self.earthquake_radius = config['manual_earthquake']['radius']
        self.add_property('earthquake_radius', self.earthquake_radius)

        # List of affected buildings affected by manual earthquake
        self.affected_buildings = config['manual_earthquake']['affected_buildings']
        self.add_property('affected_buildings', self.affected_buildings)

        # List of affected victims affected by manual earthquake
        self.affected_victims = config['manual_earthquake']['affected_victims']
        self.add_property('affected_victims', self.affected_victims)

        self.explorer_victim_pickup_ticks = config['explorer_victim_pickup_ticks']
        self.add_property('explorer_victim_pickup_ticks', self.explorer_victim_pickup_ticks)

        self.explorer_victim_carry_move_ticks = config['explorer_victim_carry_move_ticks']
        self.add_property('explorer_victim_carry_move_ticks', self.explorer_victim_carry_move_ticks)

        self.task_completed_message = config['task_completed_message']
        self.add_property('task_completed_message', self.task_completed_message)
