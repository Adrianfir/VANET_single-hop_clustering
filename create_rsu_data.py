import xml.etree.ElementTree as ET

def add_vehicle_to_xml(input_file, output_file, vehicle_elements):
    # Parse the input XML file
    tree = ET.parse(input_file)

    # Iterate through each timestep
    for timestep in tree.findall(".//timestep"):
        for vehicle_element in vehicle_elements:
            # Create a new vehicle element and add it to the timestep
            new_vehicle = ET.SubElement(timestep, vehicle_element.tag, vehicle_element.attrib)
            new_vehicle.tail = "\n        "  # Add proper indentation

    # Write the modified XML to the output file
    tree.write(output_file, encoding='utf-8', xml_declaration=True)

# Define the vehicle elements to add
new_vehicle_elements = [
    ET.fromstring('''
        <vehicle angle="71.93" id="busrsu2" lane="35349093_0" pos="5.10" slope="0.00" speed="0.00" type="veh_passenger" x="-79.448788" y="43.868880" />'''),
    ET.fromstring('''
        <vehicle angle="71.93" id="busrsu3" lane="35349093_0" pos="5.10" slope="0.00" speed="0.00" type="veh_passenger" x="-79.435327" y="43.863937" />''')
]

input_file = "/Users/pouyafirouzmakan/Desktop/VANET/final_data_Richmondhill/sumoTrace.xml"
output_file = "/Users/pouyafirouzmakan/Desktop/VANET/final_data_Richmondhill/sumoTrace_rsu.xml"

# Call the function to add the vehicle elements to all timesteps
add_vehicle_to_xml(input_file, output_file, new_vehicle_elements)
