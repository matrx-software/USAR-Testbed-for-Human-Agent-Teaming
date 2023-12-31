import collections

import numpy as np

from matrxs.actions.action import Action, ActionResult
from matrxs.utils.utils import get_distance
from matrxs.objects.agent_body import AgentBody
from matrxs.objects.simple_objects import AreaTile


class RemoveObject(Action):

    def __init__(self, duration_in_ticks=0):
        """ Removes an object from the world.

        An Action that permanently removes an EnvObject from the world, which can be any object except the agent
        performing the action.

        Parameters
        ----------
        duration_in_ticks : int (default=1)
            The default duration of RemoveObject in ticks during which the GridWorld blocks the Agent performing other
            actions. By default this is 1, meaning that the RemoveObject will take both the tick in which it was
            decided upon and the subsequent tick. Should be zero or larger.

        """
        super().__init__(duration_in_ticks)

    def mutate(self, grid_world, agent_id, **kwargs):
        """ Removes the specified object.

        Removes a specific EnvObject from the GridWorld. Can be any object except for the agent performing the action.

        Parameters
        ----------
        grid_world : GridWorld
            The GridWorld instance in which the object is sought according to the object_id parameter.
        agent_id : string
            The string representing the unique identified that represents the agent performing this action.
        object_id : string, optional (default=None)
            The string representing the unique identifier of the EnvObject that should be removed.
        remove_range : int, optional (default=1)
            The range in which the to be removed EnvObject should be in.

        Returns
        -------
        RemoveObjectResult
            The ActionResult depicting the action's success or failure and reason for that result.
            Returns the following results:
            RemoveObjectResult.OBJECT_REMOVED               : If the object was successfully removed.
            RemoveObjectResult.REMOVAL_FAILED               : If the object could not be removed by the GridWorld.
            RemoveObjectResult.OBJECT_ID_NOT_WITHIN_RANGE   : If the object is not within specified range.

        """
        assert 'object_id' in kwargs.keys()  # assert if object_id is given.
        object_id = kwargs['object_id']  # assign
        remove_range = 1  # default remove range
        if 'remove_range' in kwargs.keys():  # if remove range is present
            assert isinstance(kwargs['remove_range'], int)  # should be of integer
            assert kwargs['remove_range'] >= 0  # should be equal or larger than 0
            remove_range = kwargs['remove_range']  # assign

        # get the current agent (exists, otherwise the is_possible failed)
        agent_avatar = grid_world.registered_agents[agent_id]
        agent_loc = agent_avatar.location  # current location

        # Get all objects in the remove_range
        objects_in_range = grid_world.get_objects_in_range(agent_loc, object_type="*", sense_range=remove_range)

        # You can't remove yourself
        objects_in_range.pop(agent_id)

        for obj in objects_in_range:  # loop through all objects in range
            if obj == object_id:  # if object is in that list
                success = grid_world.remove_from_grid(object_id)  # remove it, success is whether GridWorld succeeded
                if success:  # if we succeeded in removal return the appriopriate ActionResult
                    return RemoveObjectResult(RemoveObjectResult.OBJECT_REMOVED \
                                              .replace('object_id'.upper(), str(object_id)), True)
                else:  # else we return a failure due to the GridWorld removal failed
                    return RemoveObjectResult(RemoveObjectResult.REMOVAL_FAILED \
                                              .replace('object_id'.upper(), str(object_id)), False)

        # If the object was not in range, or no objects were in range we return that the object id was not in range
        return RemoveObjectResult(RemoveObjectResult.OBJECT_ID_NOT_WITHIN_RANGE \
                                  .replace('remove_range'.upper(), str(remove_range)) \
                                  .replace('object_id'.upper(), str(object_id)), False)

    def is_possible(self, grid_world, agent_id, **kwargs):
        """ Checks if an object can be removed.

        Parameters
        ----------
        grid_world : GridWorld
            The GridWorld instance in which the object is sought according to the object_id parameter.
        agent_id : string
            The string representing the unique identified that represents the agent performing this action.
        object_id : string, optional (default=None)
            The string representing the unique identifier of the EnvObject that should be removed.
        remove_range : int, optional (default=1)
            The range in which the to be removed EnvObject should be in.

        Returns
        -------
        RemoveObjectResult
            The ActionResult depicting the action's expected success or failure and reason for that result.
            Returns the following results:
            RemoveObjectResult.ACTION_SUCCEEDED     : If the object was successfully removed.
            RemoveObjectResult.NO_OBJECTS_IN_RANGE  : If no objects are within range.

        """
        agent_avatar = grid_world.get_env_object(agent_id, obj_type=AgentBody)  # get ourselves
        assert agent_avatar is not None  # check if we actually exist
        agent_loc = agent_avatar.location  # get our location

        remove_range = np.inf  # we do not know the intended range, so assume infinite
        # get all objects within infinite range
        objects_in_range = grid_world.get_objects_in_range(agent_loc, object_type="*", sense_range=remove_range)

        # You can't remove yourself
        objects_in_range.pop(agent_avatar.obj_id)

        if len(objects_in_range) == 0:  # if there are no objects in infinite range besides ourselves, we return fail
            return RemoveObjectResult(RemoveObjectResult.NO_OBJECTS_IN_RANGE.replace('remove_range'.upper(),
                                                                                     str(remove_range)), False)

        # otherwise some instance of RemoveObject is possible, although we do not know yet IF the intended removal is
        # possible.
        return RemoveObjectResult(RemoveObjectResult.ACTION_SUCCEEDED, True)


class RemoveObjectResult(ActionResult):
    NO_OBJECTS_IN_RANGE = "No objects were in `REMOVE_RANGE`."
    OBJECT_ID_NOT_WITHIN_RANGE = "The object with id `OBJECT_ID` is not within the range of `REMOVE_RANGE`."
    OBJECT_REMOVED = "The object with id `OBJECT_ID` is removed."
    REMOVAL_FAILED = "The object with id `OBJECT_ID` failed to be removed by the environment for some reason."

    def __init__(self, result, succeeded):
        """ActionResult for a RemoveObjectAction

        The results uniquely for RemoveObjectAction are (as class constants):
            RemoveObjectResult.OBJECT_REMOVED               : If the object was successfully removed.
            RemoveObjectResult.REMOVAL_FAILED               : If the object could not be removed by the GridWorld.
            RemoveObjectResult.OBJECT_ID_NOT_WITHIN_RANGE   : If the object is not within specified range.
            RemoveObjectResult.NO_OBJECTS_IN_RANGE          : If no objects are within range.

        Parameters
        ----------
        result : string
            A string representing the reason for a RemoveObjectAction's (expected) success or fail.
        succeeded : boolean
            A boolean representing the (expected) success or fail of a RemoveObjectAction.

        See Also
        --------
        RemoveObjectAction

        """
        super().__init__(result, succeeded)


class GrabObject(Action):

    def __init__(self, duration_in_ticks=0):
        """ Grab and hold objects.

        The Action that can pick up / grab and hold EnvObjects. Cannot be performed on agents (including the agent
        performing the action). After grabbing / picking up, the object is automatically added to the agent's inventory.

        Parameters
        ----------
        duration_in_ticks : int (default=1)
            The default duration of GrabObject in ticks during which the GridWorld blocks the Agent performing other
            actions. By default this is 1, meaning that the GrabObject will take both the tick in which it was
            decided upon and the subsequent tick. Should be zero or larger.

        Notes
        -----
        The actual carrying mechanism of objects is implemented in the Move actions: whenever an agent moves who holds
        objects, those objects it is holding are also moved with it.

        """
        super().__init__(duration_in_ticks)

    def is_possible(self, grid_world, agent_id, **kwargs):
        """ Checks if the object can be grabbed.

        Parameters
        ----------
        grid_world : GridWorld
            The GridWorld instance in which the object is sought according to the object_id parameter.
        agent_id : string
            The string representing the unique identified that represents the agent performing this action.
        object_id : string, optional (default=None)
            The string representing the unique identifier of the EnvObject that should be grabbed. When not given, a
            random object within range is selected.
        grab_range : int, optional (default=np.inf)
            The range in which the to be grabbed EnvObject should be in.
        max_objects : int, optional (default=np.inf)
            The maximum of objects the agent can carry.

        Returns
        -------
        GrabObjectResult
            The ActionResult depicting the action's expected success or failure and reason for that result.
            Returns the following results:
            GrabObjectResult.RESULT_SUCCESS                 : When the object can be successfully grabbed.
            GrabObjectResult.RESULT_NO_OBJECT               : When object_id is not given.
            GrabObjectResult.RESULT_CARRIES_OBJECT          : When the agent already carries the maximum nr. objects.
            GrabObjectResult.NOT_IN_RANGE                   : When object_id not within range.
            GrabObjectResult.RESULT_AGENT                   : If the object_id is that of an agent.
            GrabObjectResult.RESULT_OBJECT_CARRIED          : When the object is already carried by another agent.
            GrabObjectResult.RESULT_OBJECT_UNMOVABLE        : When the object is not movable.
            GrabObjectResult.RESULT_UNKNOWN_OBJECT_TYPE     : When the object_id does not exists in the GridWorld.

        """
        # Set default values check
        object_id = None if 'object_id' not in kwargs else kwargs['object_id']
        grab_range = np.inf if 'grab_range' not in kwargs else kwargs['grab_range']
        max_objects = np.inf if 'max_objects' not in kwargs else kwargs['max_objects']

        return self._is_possible_grab(grid_world, agent_id=agent_id, object_id=object_id, grab_range=grab_range,
                                      max_objects=max_objects)

    def mutate(self, grid_world, agent_id, **kwargs):
        """ Grabs an object.

        Alters the properties of the agent doing the grabbing, and the object being grabbed (and carried), such that
        the agent's inventory contains the entire object and the object being carried properties contains the agent's
        id.

        The grabbed object is removed from the world, and will only exist inside of the agent's inventory.

        Parameters
        ----------
        grid_world : GridWorld
            The GridWorld instance in which the object is sought according to the object_id parameter.
        agent_id : string
            The string representing the unique identified that represents the agent performing this action.
        object_id : string, optional (default=None)
            The string representing the unique identifier of the EnvObject that should be grabbed. When not given, a
            random object within range is selected.
        grab_range : int, optional (default=np.inf)
            The range in which the to be grabbed EnvObject should be in.
        max_objects : int, optional (default=np.inf)
            The maximum of objects the agent can carry.

        Returns
        -------
        GrabObjectResult
            The ActionResult depicting the action's expected success or failure and reason for that result.
            Returns the following results:
            GrabObjectResult.RESULT_SUCCESS                         : When the grab succeeded.
            GrabObjectResult.FAILED_TO_REMOVE_OBJECT_FROM_WORLD     : When the grabbed object cannot be removed from the
                                                                      GridWorld.

        Notes
        -----
        A grabbed object resides inside the inventory of an agent, not directly in the world any longer. Hence, if the
        agent is removed, so is its inventory and all objects herein.

        """

        # Additional check
        assert 'object_id' in kwargs.keys()
        assert 'grab_range' in kwargs.keys()
        assert 'max_objects' in kwargs.keys()

        # if possible:
        object_id = kwargs['object_id']  # assign

        # Loading properties
        reg_ag = grid_world.registered_agents[agent_id]  # Registered Agent
        env_obj = grid_world.environment_objects[object_id]  # Environment object

        # Updating properties
        env_obj.carried_by.append(agent_id)
        reg_ag.is_carrying.append(env_obj)  # we add the entire object!

        # Remove it from the grid world (it is now stored in the is_carrying list of the AgentAvatar
        succeeded = grid_world.remove_from_grid(object_id=env_obj.obj_id, remove_from_carrier=False)
        if not succeeded:
            return GrabObjectResult(GrabObjectResult.FAILED_TO_REMOVE_OBJECT_FROM_WORLD.replace("{OBJECT_ID}",
                                                                                                env_obj.obj_id), False)

        # Updating Location (done after removing from grid, or the grid will search the object on the wrong location)
        env_obj.location = reg_ag.location

        return GrabObjectResult(GrabObjectResult.RESULT_SUCCESS, True)

    def _is_possible_grab(self, grid_world, agent_id, object_id, grab_range, max_objects):
        """ Private MATRX method.

        Checks if an EnvObject can be grabbed by an agent.

        Parameters
        ----------
        grid_world : GridWorld
            The GridWorld instance in which the object is sought according to the object_id parameter.
        agent_id : string
            The string representing the unique identified that represents the agent performing this action.
        object_id : string, optional (default=None)
            The string representing the unique identifier of the EnvObject that should be grabbed. When not given, a
            random object within range is selected.
        grab_range : int, optional (default=np.inf)
            The range in which the to be grabbed EnvObject should be in.
        max_objects : int, optional (default=np.inf)
            The maximum of objects the agent can carry.

        Returns
        -------
        GrabObjectResult
            The ActionResult depicting the action's expected success or failure and reason for that result.
            Returns the following results:
            GrabObjectResult.RESULT_SUCCESS                 : When the object can be successfully grabbed.
            GrabObjectResult.RESULT_NO_OBJECT               : When object_id is not given.
            GrabObjectResult.RESULT_CARRIES_OBJECT          : When the agent already carries the maximum nr. objects.
            GrabObjectResult.NOT_IN_RANGE                   : When object_id not within range.
            GrabObjectResult.RESULT_AGENT                   : If the object_id is that of an agent.
            GrabObjectResult.RESULT_OBJECT_CARRIED          : When the object is already carried by another agent.
            GrabObjectResult.RESULT_OBJECT_UNMOVABLE        : When the object is not movable.
            GrabObjectResult.RESULT_UNKNOWN_OBJECT_TYPE     : When the object_id does not exists in the GridWorld.


        """
        reg_ag = grid_world.registered_agents[agent_id]  # Registered Agent
        loc_agent = reg_ag.location  # Agent location

        if object_id is None:
            return GrabObjectResult(GrabObjectResult.RESULT_NO_OBJECT, False)

        # Already carries an object
        if len(reg_ag.is_carrying) >= max_objects:
            return GrabObjectResult(GrabObjectResult.RESULT_CARRIES_OBJECT, False)

        # Go through all objects at the desired locations
        objects_in_range = grid_world.get_objects_in_range(loc_agent, object_type="*", sense_range=grab_range)
        objects_in_range.pop(agent_id)

        # Set random object in range
        if not object_id:
            # Remove all non objects from the list
            for obj in list(objects_in_range.keys()):
                if obj not in grid_world.environment_objects.keys():
                    objects_in_range.pop(obj)

            # Select a random object
            if objects_in_range:
                object_id = grid_world.rnd_gen.choice(list(objects_in_range.keys()))
            else:
                return GrabObjectResult(GrabObjectResult.NOT_IN_RANGE, False)

        # Check if object is in range
        if object_id not in objects_in_range:
            return GrabObjectResult(GrabObjectResult.NOT_IN_RANGE, False)

        # Check if object_id is the id of an agent
        if object_id in grid_world.registered_agents.keys():
            # If it is an agent at that location, grabbing is not possible
            return GrabObjectResult(GrabObjectResult.RESULT_AGENT, False)

        # Check if it is an object
        if object_id in grid_world.environment_objects.keys():
            env_obj = grid_world.environment_objects[object_id]  # Environment object
            # Check if the object is not carried by another agent
            if len(env_obj.carried_by) != 0:
                return GrabObjectResult(GrabObjectResult.RESULT_OBJECT_CARRIED.replace("{AGENT_ID}",
                                                                                              str(env_obj.carried_by)),
                                               False)
            elif not env_obj.properties["is_movable"]:
                return GrabObjectResult(GrabObjectResult.RESULT_OBJECT_UNMOVABLE, False)
            else:
                # Success
                return GrabObjectResult(GrabObjectResult.RESULT_SUCCESS, False)
        else:
            return GrabObjectResult(GrabObjectResult.RESULT_UNKNOWN_OBJECT_TYPE, False)


class GrabObjectResult(ActionResult):
    FAILED_TO_REMOVE_OBJECT_FROM_WORLD = 'Grab action failed; could not remove object with id {OBJECT_ID} from grid.'
    RESULT_SUCCESS = 'Grab action success'
    NOT_IN_RANGE = 'Object not in range'
    RESULT_AGENT = 'This is an agent, cannot be picked up'
    RESULT_NO_OBJECT = 'No Object specified'
    RESULT_CARRIES_OBJECT = 'Agent already carries the maximum amount of objects'
    RESULT_OBJECT_CARRIED = 'Object is already carried by {AGENT_ID}'
    RESULT_UNKNOWN_OBJECT_TYPE = 'obj_id is no Agent and no Object, unknown what to do'
    RESULT_OBJECT_UNMOVABLE = 'Object is not movable'

    def __init__(self, result, succeeded):
        """ActionResult for a GrabObjectAction

        The results uniquely for GrabObjectAction are (as class constants):
            GrabObjectResult.RESULT_SUCCESS                     : When the object can be successfully grabbed.
            GrabObjectResult.RESULT_NO_OBJECT                   : When object_id is not given.
            GrabObjectResult.RESULT_CARRIES_OBJECT              : When the agent already carries the maximum nr. objects.
            GrabObjectResult.NOT_IN_RANGE                       : When object_id not within range.
            GrabObjectResult.RESULT_AGENT                       : If the object_id is that of an agent.
            GrabObjectResult.RESULT_OBJECT_CARRIED              : When the object is already carried by another agent.
            GrabObjectResult.RESULT_OBJECT_UNMOVABLE            : When the object is not movable.
            GrabObjectResult.RESULT_UNKNOWN_OBJECT_TYPE         : When the object_id does not exists in the GridWorld.
            GrabObjectResult.FAILED_TO_REMOVE_OBJECT_FROM_WORLD : When the grabbed object cannot be removed from the
                                                                  GridWorld.

        Parameters
        ----------
        result : string
            A string representing the reason for a GrabObjectAction's (expected) success or fail.
        succeeded : boolean
            A boolean representing the (expected) success or fail of a GrabObjectAction.

        See Also
        --------
        GrabObjectAction

        """
        super().__init__(result, succeeded)


class DropObject(Action):

    def __init__(self, duration_in_ticks=0):
        """ Drop objects that are being carried.

        The Action that can drop EnvObjects that are in an agent's inventory. After dropping, the object is added to the
        GridWorld directly (instead of remaining in the agent's inventory).

        Parameters
        ----------
        duration_in_ticks : int (default=1)
            The default duration of DropObject in ticks during which the GridWorld blocks the Agent performing other
            actions. By default this is 1, meaning that the DropObject will take both the tick in which it was
            decided upon and the subsequent tick. Should be zero or larger.

        Notes
        -----
        The actual carrying mechanism of objects is implemented in the Move actions: whenever an agent moves who holds
        objects, those objects it is holding are also moved with it.

        """
        super().__init__(duration_in_ticks)

    def is_possible(self, grid_world, agent_id, **kwargs):
        """ Checks if the object can be grabbed.

        Parameters
        ----------
        grid_world : GridWorld
            The GridWorld instance in which the object is dropped.
        agent_id : string
            The string representing the unique identified that represents the agent performing this action.
        object_id : string, optional (default=None)
            The string representing the unique identifier of the EnvObject that should be dropped. When not given the
            last object that was grabbed is dropped.
        drop_range : int, optional (default=np.inf)
            The range in which the object can be dropped.

        Returns
        -------
        DropObjectResult
            The ActionResult depicting the action's expected success or failure and reason for that result.
            Returns the following results:
            GrabObjectResult.RESULT_SUCCESS     : When the object can be successfully dropped.
            DropObjectResult.RESULT_NO_OBJECT   : When there is no object in the agent's inventory.
            GrabObjectResult.RESULT_NONE_GIVEN  : When the given obj_id is not being carried by the agent.
            GrabObjectResult.RESULT_NO_OBJECT   : When no obj_id is given.

        """
        reg_ag = grid_world.registered_agents[agent_id]

        drop_range = 1 if not 'drop_range' in kwargs else kwargs['drop_range']

        # If no object id is given, the last item is dropped
        if 'object_id' in kwargs:
            obj_id = kwargs['object_id']
        elif len(reg_ag.is_carrying) > 0:
            obj_id = reg_ag.is_carrying[-1]
        else:
            return DropObjectResult(DropObjectResult.RESULT_NO_OBJECT, False)

        return self._possible_drop(grid_world, agent_id=agent_id, obj_id=obj_id, drop_range=drop_range)

    def mutate(self, grid_world, agent_id, **kwargs):
        """ Drops the carried object.

        Parameters
        ----------
        grid_world : GridWorld
            The GridWorld instance in which the object is dropped.
        agent_id : string
            The string representing the unique identified that represents the agent performing this action.
        object_id : string, optional (default=None)
            The string representing the unique identifier of the EnvObject that should be dropped. When not given the
            last object that was grabbed is dropped.
        drop_range : int, optional (default=np.inf)
            The range in which the object can be dropped.

        Returns
        -------
        DropObjectResult
            The ActionResult depicting the action's expected success or failure and reason for that result.
            Returns the following results:
            GrabObjectResult.RESULT_SUCCESS             : When the object is successfully dropped.
            GrabObjectResult.RESULT_NO_OBJECT_CARRIED   : When no objects are carried by the agent.
            GrabObjectResult.RESULT_OBJECT              : When the object was intended to drop on the agent's location
                                                          and this was not possible or when no suitable drop location
                                                          could be found.

        Raises
        ------
        Exception
            When the object is said to be dropped inside the agent's location, but the agent and object are
            intraversable. No other intraversable objects can be on the same location.

        """
        reg_ag = grid_world.registered_agents[agent_id]

        # fetch range from kwargs
        drop_range = 1 if not 'drop_range' in kwargs else kwargs['drop_range']

        # If no object id is given, the last item is dropped
        if 'object_id' in kwargs:
            env_obj = kwargs['object_id']
        elif len(reg_ag.is_carrying) > 0:
            env_obj = reg_ag.is_carrying[-1]
        else:
            return DropObjectResult(DropObjectResult.RESULT_NO_OBJECT_CARRIED, False)

        # check that it is even possible to drop this object somewhere
        if not env_obj.is_traversable and not reg_ag.is_traversable and drop_range == 0:
            raise Exception(
                f"Intraversable agent {reg_ag.obj_id} can only drop the intraversable object {env_obj.obj_id} at its "
                f"own location (drop_range = 0), but this is impossible. Enlarge the drop_range for the DropAction to "
                f"atleast 1")

        # check if we can drop it at our current location
        curr_loc_drop_poss = self._is_drop_poss(grid_world, env_obj, reg_ag.location)

        # drop it on the agent location if possible
        if curr_loc_drop_poss:
            return self._act_drop(grid_world, agent=reg_ag, env_obj=env_obj, drop_loc=reg_ag.location)

        # if the agent location was the only within range, return a negative action result
        elif not curr_loc_drop_poss and drop_range == 0:
            return DropObjectResult(DropObjectResult.RESULT_OBJECT, False)

        # Try finding other drop locations from close to further away around the agent
        drop_loc = self._find_drop_loc(grid_world, reg_ag, env_obj, drop_range, reg_ag.location)

        # If we didn't find a valid drop location within range, return a negative action result
        if not drop_loc:
            return DropObjectResult(DropObjectResult.RESULT_OBJECT, False)

        return self._act_drop(grid_world, agent=reg_ag, env_obj=env_obj, drop_loc=drop_loc)

    def _act_drop(self, grid_world, agent, env_obj, drop_loc):
        """ Private MATRX method.

        Drops the carried object.

        Parameters
        ----------
        grid_world : GridWorld
            The GridWorld instance in which the object is dropped.
        agent : AgentBody
            The AgentBody of the agent who drops the object.
        env_obj : EnvObject
            The EnvObject to be dropped.
        drop_loc : [x, y]
            The drop location.

        Returns
        -------
        DropObjectResult
            The ActionResult depicting the action's expected success or failure and reason for that result.
            Returns the following results:
            GrabObjectResult.RESULT_SUCCESS     : When the object is successfully dropped.

        """

        # Updating properties
        agent.is_carrying.remove(env_obj)
        env_obj.carried_by.remove(agent.obj_id)

        # We return the object to the grid location we are standing at
        env_obj.location = drop_loc
        grid_world._register_env_object(env_obj)

        return DropObjectResult(DropObjectResult.RESULT_SUCCESS, True)

    def _find_drop_loc(self, grid_world, agent, env_obj, drop_range, start_loc):
        """ Private MATRX method.

        A breadth first search starting from the agent's location to find the closest valid drop location.

        Parameters
        ----------
        grid_world : GridWorld
            The GridWorld instance in which the object is dropped.
        agent : AgentBody
            The AgentBody of the agent who drops the object.
        env_obj : EnvObject
            The EnvObject to be dropped.
        drop_range : int
            The range in which the object can be dropped.
        start_loc : [x, y]
            The location of the agent from which to start the search.

        Returns
        -------
        boolean
            False if no valid drop location can be found, otherwise the [x,y] coordinates of the closest drop location.
        """
        queue = collections.deque([[start_loc]])
        seen = {start_loc}

        width = grid_world.shape[0]
        height = grid_world.shape[1]

        while queue:
            path = queue.popleft()
            x, y = path[-1]

            # check if we are still within drop_range
            if get_distance([x, y], start_loc) > drop_range:
                return False

            # check if we can drop at this location
            if self._is_drop_poss(grid_world, env_obj, [x, y]):
                return [x, y]

            # queue unseen neighbouring tiles
            for x2, y2 in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                if 0 <= x2 < width and 0 <= y2 < height and (x2, y2) not in seen:
                    queue.append(path + [(x2, y2)])
                    seen.add((x2, y2))
        return False

    def _is_drop_poss(self, grid_world, env_obj, dropLocation):
        """ Private MATRX method.


        Check if the object can be dropped at a specific location by checking if there are any intraversable objects at
        that location, and if the object to be dropped is intraversable

        Parameters
        ----------
        grid_world : GridWolrd
            The grid_world object
        env_obj : EnvObject
            The object to be dropped
        dropLocation: [x, y]
            Location to check if it is possible to drop the env_obj there.

        Returns
        -------
        boolean
            True when the location is a valid drop location, False otherwise.
        """

        # Count the intraversable objects at the current location if we would drop the
        # object here
        objs_at_loc = grid_world.get_objects_in_range(dropLocation, object_type="*", sense_range=0)

        # Remove area objects from the list
        for key in list(objs_at_loc.keys()):
            if AreaTile.__name__ in objs_at_loc[key].class_inheritance:
                objs_at_loc.pop(key)

        in_trav_objs_count = 1 if not env_obj.is_traversable else 0
        in_trav_objs_count += len([obj for obj in objs_at_loc if not objs_at_loc[obj].is_traversable])

        # check if we would have an in_traversable object and other objects in
        # the same location (which is impossible)
        if in_trav_objs_count >= 1 and (len(objs_at_loc) + 1) >= 2:
            return False
        else:
            return True

    def _possible_drop(self, grid_world, agent_id, obj_id, drop_range):
        """ Private MATRX method.

        Checks if an EnvObject can be dropped by an agent.

        Parameters
        ----------
        grid_world : GridWorld
            The GridWorld instance in which the object is dropped.
        agent_id : string
            The string representing the unique identified that represents the agent performing this action.
        obj_id : string, optional (default=None)
            The string representing the unique identifier of the EnvObject that should be dropped.
        drop_range : int, optional (default=np.inf)
            The range in which the EnvObject should be dropped in.

        Returns
        -------
        DropObjectResult
            The ActionResult depicting the action's expected success or failure and reason for that result.
            Returns the following results:
            GrabObjectResult.RESULT_SUCCESS     : When the object can be successfully dropped.
            GrabObjectResult.RESULT_NONE_GIVEN  : When the given obj_id is not being carried by the agent.
            GrabObjectResult.RESULT_NO_OBJECT   : When no obj_id is given.


        """
        reg_ag = grid_world.registered_agents[agent_id]  # Registered Agent
        loc_agent = reg_ag.location
        loc_obj_ids = grid_world.grid[loc_agent[1], loc_agent[0]]

        # No object given
        if not obj_id:
            return DropObjectResult(DropObjectResult.RESULT_NONE_GIVEN, False)

        # No object with that name
        if not (obj_id in reg_ag.is_carrying):
            return DropObjectResult(DropObjectResult.RESULT_NO_OBJECT, False)

        if len(loc_obj_ids) == 1:
            return DropObjectResult(DropObjectResult.RESULT_SUCCESS, True)

        # TODO: incorporate is_possible check from DropAction.mutate is_possible here

        return DropObjectResult(DropObjectResult.RESULT_SUCCESS, True)


class DropObjectResult(ActionResult):
    RESULT_SUCCESS = 'Drop action success'
    RESULT_NO_OBJECT = 'The item is not carried'
    RESULT_NONE_GIVEN = "'None' used as input id"
    RESULT_AGENT = 'Cannot drop item on an agent'
    RESULT_OBJECT = 'Cannot drop item on another intraversable object'
    RESULT_UNKNOWN_OBJECT_TYPE = 'Cannot drop item on an unknown object'
    RESULT_NO_OBJECT_CARRIED = 'Cannot drop object when none carried'

    def __init__(self, result, succeeded, obj_id=None):
        """ActionResult for a DropObjectAction.

        The results uniquely for GrabObjectAction are (as class constants):
            GrabObjectResult.RESULT_SUCCESS             : When the object is successfully dropped.
            DropObjectAction.RESULT_NO_OBJECT           : When there is no object in the agent's inventory.
            DropObjectAction.RESULT_NONE_GIVEN          : When the given obj_id is not being carried by the agent.
            GrabObjectResult.RESULT_OBJECT              : When the object was intended to drop on the agent's location
                                                          and this was not possible or when no suitable drop location
                                                          could be found.
            DropObjectAction.RESULT_UNKNOWN_OBJECT_TYPE :
            GrabObjectResult.RESULT_NO_OBJECT_CARRIED   : When no objects are carried by the agent.

        Parameters
        ----------
        result : string
            A string representing the reason for a DropObjectAction's (expected) success or fail.
        succeeded : boolean
            A boolean representing the (expected) success or fail of a DropObjectAction.

        See Also
        --------
        GrabObjectAction

        """
        super().__init__(result, succeeded)
        self.obj_id = obj_id
