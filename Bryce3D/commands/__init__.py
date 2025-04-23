# Here you define the commands that will be added to your add-in.

# Import the modules corresponding to the Bryce 3D features
from .terrainGenerator import entry as terrainGenerator

# List of all Bryce 3D features
# Add new features here as they are implemented
commands = [
    terrainGenerator,  # Terrain generation and editing
    # skyRenderer,     # Atmospheric effects and sky rendering
    # materialEditor,  # Material and texture management
    # objectPlacer,    # Object placement and manipulation
    # cameraControl,   # Camera controls and scene management
]

# Assumes you defined a "start" function in each of your modules.
# The start function will be run when the add-in is started.
def start():
    for command in commands:
        command.start()

# Assumes you defined a "stop" function in each of your modules.
# The stop function will be run when the add-in is stopped.
def stop():
    for command in commands:
        command.stop()