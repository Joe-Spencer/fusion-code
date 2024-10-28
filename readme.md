# Fusion Scripts and Post Processor

This a collection of some of the Python scripts I use in Autodesk Fusion as well as the post processor I use to send g-code to a CNC machine. 


**Spiral**:
Creates a custom UI element that lets you adjust a parametric spiral staircase model in real time. This model is basic, only showing the treads but it can be used as the basis for a complete 3D model.

**ParameterMaker**:
Creates a preset list of parameters to use as a starting point for experimenting with parametric modelng techniques. This shows how passing in a string can create a function and how a while loop can be used to create a collection of parameters.

**Triangulator**:
Generates a series of triangles from a CSV file. This is useful for measuring a compound radius.

**Spheres**:
Makes randomly sized non-intersecting spheres.

To use these scripts you will need an up-to-date Fusion license. To use the scripts drop them in your scripts folder, usually "user\AppData\Roaming\Autodesk\Autodesk Fusion 360\API\Scripts" You may also need to create a settings.json file with the following paths:

```json
{
  "python.autoComplete.extraPaths": [],
  "python.analysis.extraPaths": [],
  "python.defaultInterpreterPath": ""
}

**CustomThermwoodPostProcessor**:
This post processor is specifically intended for a machine that has been modified such that the axes are rotated 270 degrees causing the long side of the table to point in the negative x direction. It also includes presets values for offset blocks.

