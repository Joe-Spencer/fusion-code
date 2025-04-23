import adsk.core, adsk.fusion, adsk.cam, traceback
import random
import math

# Global list to maintain references to event handlers
handlers = []

# Event handler for the command creation event
class TerrainGeneratorCommandCreatedHandler(adsk.core.CommandCreatedEventHandler):
    def __init__(self):
        super().__init__()
    
    def notify(self, args):
        try:
            cmd = args.command
            cmd.isExecutedWhenPreEmpted = False
            
            # Get the CommandInputs collection to create command inputs
            inputs = cmd.commandInputs
            
            # Create value inputs for terrain parameters
            inputs.addValueInput('terrainSize', 'Terrain Size', 'mm', adsk.core.ValueInput.createByReal(100))
            inputs.addValueInput('heightScale', 'Height Scale', 'mm', adsk.core.ValueInput.createByReal(10))
            
            # Create slider inputs for terrain parameters
            detailLevelInput = inputs.addIntegerSliderCommandInput('detailLevel', 'Detail Level', 1, 6)
            detailLevelInput.valueOne = 4
            
            roughnessInput = inputs.addIntegerSliderCommandInput('roughness', 'Roughness', 1, 10)
            roughnessInput.valueOne = 5
            
            seedInput = inputs.addIntegerSpinnerCommandInput('seed', 'Random Seed', 0, 10000, 1, 42)
            
            # Connect to the execute event
            onExecute = TerrainGeneratorCommandExecuteHandler()
            cmd.execute.add(onExecute)
            handlers.append(onExecute)
            
        except:
            app = adsk.core.Application.get()
            ui = app.userInterface
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

# Event handler for the command execution event
class TerrainGeneratorCommandExecuteHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()
    
    def notify(self, args):
        try:
            command = args.command
            inputs = command.commandInputs
            
            # Get the input values
            terrainSize = inputs.itemById('terrainSize').value
            heightScale = inputs.itemById('heightScale').value
            detailLevel = inputs.itemById('detailLevel').valueOne
            roughness = inputs.itemById('roughness').valueOne
            seed = inputs.itemById('seed').value
            
            # Set the random seed for reproducible terrain
            random.seed(seed)
            
            # Get the active design
            app = adsk.core.Application.get()
            design = app.activeProduct
            
            # Create a new component for the terrain
            rootComp = design.rootComponent
            terrainComp = rootComp.occurrences.addNewComponent(adsk.core.Matrix3D.create()).component
            terrainComp.name = 'Bryce Terrain'
            
            # Generate the terrain mesh
            self._generateTerrain(terrainComp, terrainSize, heightScale, detailLevel, roughness)
            
        except:
            app = adsk.core.Application.get()
            ui = app.userInterface
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
    
    def _generateTerrain(self, component, size, heightScale, detailLevel, roughness):
        try:
            app = adsk.core.Application.get()
            ui = app.userInterface
            
            # Calculate the number of vertices based on detail level
            numVertices = int(math.pow(2, detailLevel) + 1)
            
            # Progress dialog
            progressDialog = ui.createProgressDialog()
            progressDialog.cancelButtonText = 'Cancel'
            progressDialog.isBackgroundTranslucent = False
            progressDialog.isCancelButtonShown = True
            progressDialog.show('Terrain Generator', 'Generating height map...', 0, numVertices)
            
            # Generate height map
            heightMap = []
            for i in range(numVertices):
                if progressDialog.wasCancelled:
                    progressDialog.hide()
                    return
                    
                progressDialog.progressValue = i
                
                row = []
                for j in range(numVertices):
                    x = (j / (numVertices - 1)) * size
                    y = (i / (numVertices - 1)) * size
                    z = self._generateHeight(x, y, size, heightScale, roughness)
                    row.append(z)
                heightMap.append(row)
            
            progressDialog.progressMessage = 'Creating terrain...'
            progressDialog.progressValue = 0
            
            # Create the terrain using built-in spline-based loft
            # Create a new sketch for each row of points
            sketches = []
            splines = []
            
            for i in range(numVertices):
                if progressDialog.wasCancelled:
                    progressDialog.hide()
                    return
                    
                progressDialog.progressValue = i
                
                # Create a sketch for this row
                sketch = component.sketches.add(component.xZConstructionPlane)
                sketches.append(sketch)
                
                # Create points for this row
                points = adsk.core.ObjectCollection.create()
                for j in range(numVertices):
                    x = (j / (numVertices - 1)) * size
                    y = (i / (numVertices - 1)) * size
                    z = heightMap[i][j]
                    points.add(adsk.core.Point3D.create(x, z, y))  # Note: Y and Z are swapped due to sketch orientation
                
                # Create a spline through the points
                spline = sketch.sketchCurves.sketchFittedSplines.add(points)
                splines.append(spline)
            
            # Create a loft feature
            loftFeats = component.features.loftFeatures
            
            # Create a loft input
            loftInput = loftFeats.createInput(adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
            
            # Add all profiles to the loft
            for spline in splines:
                loftInput.loftSections.add(spline)
            
            # Set loft options
            loftInput.isSolid = False  # Create a surface
            
            # Create the loft
            loftFeat = loftFeats.add(loftInput)
            
            # Use thickening with correct parameters
            thickenFeatures = component.features.thickenFeatures
            
            # Create a collection of the faces to thicken
            facesToThicken = adsk.core.ObjectCollection.create()
            for face in loftFeat.bodies.item(0).faces:
                facesToThicken.add(face)
            
            # Create the thicken input with the correct parameters
            thickness = adsk.core.ValueInput.createByReal(heightScale * 0.01)
            thickenInput = thickenFeatures.createInput(facesToThicken, thickness, False, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
            
            # Create the thickened solid
            thickenFeature = thickenFeatures.add(thickenInput)
            
            # Rename the body
            if thickenFeature.bodies.count > 0:
                terrainBody = thickenFeature.bodies.item(0)
                terrainBody.name = 'Bryce Terrain'
            
            # Hide the original surface
            loftFeat.bodies.item(0).isLightBulbOn = False
            
            # Hide all sketches in the component
            for sketch in sketches:
                sketch.isVisible = False
            
            # Hide construction geometry
            component.isConstructionFolderLightBulbOn = False
            
            # Hide origin geometry
            component.isOriginFolderLightBulbOn = False
            
            progressDialog.hide()
            
            ui.messageBox('Terrain generated with size: {} mm, {} x {} grid points.'.format(
                size, numVertices, numVertices))
            
        except Exception as e:
            app = adsk.core.Application.get()
            ui = app.userInterface
            progressDialog.hide() if 'progressDialog' in locals() else None
            ui.messageBox('Error in _generateTerrain: {}'.format(str(e)))
        
    def _generateHeight(self, x, y, size, heightScale, roughness):
        # Advanced noise function for terrain generation using multiple octaves
        noise = 0
        frequency = 1.0
        amplitude = 1.0
        maxValue = 0
        
        for i in range(roughness):
            noise += amplitude * self._improvedNoise2D(x * frequency / size, y * frequency / size)
            maxValue += amplitude
            frequency *= 2
            amplitude *= 0.5
        
        # Normalize the noise to be in range [0, 1]
        noise = (noise / maxValue + 1) * 0.5
        
        # Apply height scale
        return noise * heightScale
    
    def _improvedNoise2D(self, x, y):
        # Improved noise function with smoothing and interpolation
        # Get grid cell coordinates
        x0 = math.floor(x)
        y0 = math.floor(y)
        x1 = x0 + 1
        y1 = y0 + 1
        
        # Get relative position within cell
        sx = x - x0
        sy = y - y0
        
        # Smooth interpolation weights
        sx = self._smoothstep(sx)
        sy = self._smoothstep(sy)
        
        # Get random values for each corner
        n00 = self._random2D(x0, y0)
        n01 = self._random2D(x0, y1)
        n10 = self._random2D(x1, y0)
        n11 = self._random2D(x1, y1)
        
        # Interpolate
        nx0 = self._lerp(n00, n10, sx)
        nx1 = self._lerp(n01, n11, sx)
        n = self._lerp(nx0, nx1, sy)
        
        return n * 2 - 1  # Scale to range [-1, 1]
    
    def _random2D(self, x, y):
        # Generate reproducible random value for a point
        value = math.sin(x * 12.9898 + y * 78.233) * 43758.5453
        return value - math.floor(value)
    
    def _smoothstep(self, t):
        # Smoothstep function for smoother interpolation
        return t * t * (3 - 2 * t)
    
    def _lerp(self, a, b, t):
        # Linear interpolation
        return a + t * (b - a) 