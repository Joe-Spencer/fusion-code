import adsk.core, adsk.fusion, adsk.cam, traceback
import os
from . import terrainGeneratorCommand

# Global variables to maintain references to the command and event handlers
command = None
handlers = []

def start():
    try:
        # Get the necessary UI components
        ui = adsk.core.Application.get().userInterface
        
        # Get the current directory
        current_dir = os.path.dirname(os.path.abspath(__file__))
        resources_dir = os.path.join(current_dir, 'resources')
        
        # Create the command definition
        cmdDef = ui.commandDefinitions.addButtonDefinition(
            'Bryce3DTerrainGenerator',
            'Terrain Generator',
            'Generate Bryce 3D style terrain',
            os.path.join(resources_dir, 'terrain.svg')
        )
        
        # Add the command to the Create panel in the Model workspace
        createPanel = ui.allToolbarPanels.itemById('SolidCreatePanel')
        createPanel.controls.addCommand(cmdDef)
        
        # Connect to the command created event
        onCommandCreated = terrainGeneratorCommand.TerrainGeneratorCommandCreatedHandler()
        cmdDef.commandCreated.add(onCommandCreated)
        handlers.append(onCommandCreated)
        
        # Keep the command definition referenced
        global command
        command = cmdDef
        
    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

def stop():
    try:
        # Get the necessary UI components
        ui = adsk.core.Application.get().userInterface
        
        # Clean up the UI
        if command:
            command.deleteMe()
            
        # Remove the command from the panel
        createPanel = ui.allToolbarPanels.itemById('SolidCreatePanel')
        cntrl = createPanel.controls.itemById('Bryce3DTerrainGenerator')
        if cntrl:
            cntrl.deleteMe()
            
    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc())) 