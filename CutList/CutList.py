"""This file acts as the main module for this script."""

import traceback
import adsk.core
import adsk.fusion
import csv
import os
from datetime import datetime
from collections import defaultdict
# import adsk.cam

# Initialize the global variables for the Application and UserInterface objects.
app = adsk.core.Application.get()
ui  = app.userInterface

def mm_to_inches(mm_value):
    """Convert millimeters to inches and round to 4 decimal places."""
    return round(mm_value / 2.54, 4)

def get_body_dimensions(body):
    """Calculate the dimensions of a body and return them sorted by length."""
    # Get the bounding box of the body
    bbox = body.boundingBox
    
    # Calculate dimensions in mm
    width = bbox.maxPoint.x - bbox.minPoint.x
    height = bbox.maxPoint.y - bbox.minPoint.y
    depth = bbox.maxPoint.z - bbox.minPoint.z
    
    # Convert to inches and sort dimensions (length will be the longest)
    dimensions = [mm_to_inches(width), mm_to_inches(height), mm_to_inches(depth)]
    dimensions.sort(reverse=True)
    
    return dimensions

def run(_context: str):
    """This function is called by Fusion when the script is run."""

    try:
        # Get the active design
        design = app.activeProduct
        if not design:
            ui.messageBox('No active design found.')
            return
            
        # Get all components in the design
        components = design.allComponents
        
        # Use defaultdict to count identical cuts
        cut_counts = defaultdict(int)
        cut_details = {}
        
        # Process each component
        for component in components:
            # Get all bodies in the component
            bodies = component.bRepBodies
            
            for body in bodies:
                # Get dimensions
                dimensions = get_body_dimensions(body)
                length = dimensions[0]  # Longest dimension
                width = dimensions[1]   # Second longest
                height = dimensions[2]  # Shortest
                
                # Create a key for identical cuts (only using dimensions)
                cut_key = (width, height, length)
                
                # Store the details for this cut (only if we haven't seen these dimensions before)
                if cut_key not in cut_details:
                    cut_details[cut_key] = {
                        'Material Width': width,
                        'Material Height': height,
                        'Length to Cut': length,
                        'Body Name': body.name,
                        'Component Name': component.name
                    }
                
                # Increment the count for this cut
                cut_counts[cut_key] += 1
        
        # Create CSV file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'cut_list_{timestamp}.csv'
        
        # Get the script directory
        script_dir = os.path.dirname(os.path.abspath(__file__))
        filepath = os.path.join(script_dir, filename)
        
        # Write to CSV
        with open(filepath, 'w', newline='') as csvfile:
            fieldnames = ['QTY', 'Material Width', 'Material Height', 'Body Name', 'Component Name', 'Length to Cut']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for cut_key, count in cut_counts.items():
                row = cut_details[cut_key].copy()
                row['QTY'] = count
                writer.writerow(row)
        
        ui.messageBox(f'Cut list has been created successfully!\nSaved as: {filename}')
        
    except:  #pylint:disable=bare-except
        # Write the error message to the TEXT COMMANDS window.
        app.log(f'Failed:\n{traceback.format_exc()}')
        ui.messageBox('Failed to create cut list. Check the TEXT COMMANDS window for details.')
