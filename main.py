from matrxs.API import api
from aims import aims_experiment
from time import sleep

if __name__ == "__main__":

    # By creating scripts that return a factory, we can define infinite number of use cases and select them (in the
    # future) through a UI.

    factory = aims_experiment.create_factory(mirror_scenario=False)

    # startup world-overarching MATRXS scripts, such as the API and/or visualizer if requested
    factory.startup()

    # run the experiment
    world = factory.get_world()
    world.run(factory.api_info)

    print("Task completed, showing end screen")
    # compile information to send to clients once the task is completed
    task_completed_info = {}
    task_completed_info['world_completion_message'] = world.environment_objects['settings'].properties['task_completed_message']
    # task_completed_info['score'] = world.environment_objects['score']

    # make the world completion information available
    api.world_completed(task_completed_info)

    # show the screen for x seconds before exiting
    print("Showing end screen for 5 seconds..")
    sleep(5)

    # stop MATRXS scripts such as the API and visualizer (if used)
    factory.stop()
