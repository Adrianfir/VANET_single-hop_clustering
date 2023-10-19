"""
This .py file is for adding RSUs to dataset and creating a new .xml file
"""
__author__: str = "Pouya 'Adrian' Firouzmakan"

import xml.etree.ElementTree as ET


def add_vehicle_to_xml(input_file, output_file, vehicle_element):
    # Parse the input XML file
    tree = ET.parse(input_file)
    root = tree.getroot()
    for i in vehicle_element:
        # Iterate through all <timestep> elements
        for timestep in root.findall(".//timestep"):
            # Create a copy of the vehicle_element
            new_vehicle = ET.Element(i.tag, i.attrib)

            # Append the new vehicle element to the timestep
            timestep.append(new_vehicle)

    # Write the modified XML to the output file
    tree.write(output_file)


# Define the vehicle element to add
new_vehicle_element = [
    # ET.fromstring('''
    # <vehicle id="busrsu1" x="-79.437512" y="43.871043" angle="71.93" type="veh_passenger"
    # speed="0.00" pos="5.10" lane="35349093_0" slope="0.00"/>''')
                       ET.fromstring('''
                           <vehicle id="busrsu2" x="-79.448788" y="43.868880" angle="71.93" type="veh_passenger"
                           speed="0.00" pos="5.10" lane="35349093_0" slope="0.00"/>'''),
                       ET.fromstring('''
                           <vehicle id="busrsu3" x="-79.435327" y="43.863937" angle="71.93" type="veh_passenger"
                           speed="0.00" pos="5.10" lane="35349093_0" slope="0.00"/>''')
                       ]

input_file = "/Users/pouyafirouzmakan/Desktop/VANET/final_data_Richmondhill/sumoTrace.xml"
output_file = "/Users/pouyafirouzmakan/Desktop/VANET/final_data_Richmondhill/sumoTrace_rsu.xml"

# Call the function to add the vehicle element to all timesteps
add_vehicle_to_xml(input_file, output_file, new_vehicle_element)
