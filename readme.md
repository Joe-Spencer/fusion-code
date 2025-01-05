# Fusion Scripts and Post Processor

This a collection of some of the Python scripts I use in Autodesk Fusion as well as the post processor I use to send g-code to a CNC machine. 

### TemplateMaker:
Add in that Automates DXF import and CAM for standard luan templates by assuming all outlines and holes are on layer "0" and that all traced lines are on layer "Scribe". Asks the user for the output file name and material thickness then prompts them to select an input file. When the CAM processing is done asks the user to select an output folder for the G-code file. A machine operator can then use the G-code to cut the template. This allows a user to create a luan template from Autocad without having to directly interact with any of Fusion's CAM tools.

### Spiral:
Script that creates a custom UI element allowing the user to adjust a parametric spiral staircase model in real time. This model is basic but it can be used as the basis for a more complex 3D model.

### ParameterMaker:
Script that creates a preset list of parameters to use as a starting point for experimenting with parametric modeling techniques. This shows how passing in a string can create a function and how a loop can be used to create a collection of parameters.

### Triangulator:
Script that generates a series of triangles from a CSV file. This is useful for measuring a compound radius.

### Spheres:
Just for fun. Makes 100 randomly sized non-intersecting spheres.

To use the scripts just drop them in your scripts folder, usually "user\AppData\Roaming\Autodesk\Autodesk Fusion 360\API\Scripts" You may also need to create a settings.json file with the following paths:

```json
{
  "python.autoComplete.extraPaths": [],
  "python.analysis.extraPaths": [],
  "python.defaultInterpreterPath": ""
}

```
### CustomThermwoodPostProcessor:
This post processor is specifically intended for a machine that has been modified such that the axes are rotated 270 degrees causing the long side of the table to point in the negative x direction. It also includes preset values for offset blocks.

### Examples:
Also included in this repo is an "Examples" file with links to some of my projects in the Fusion web viewer.
