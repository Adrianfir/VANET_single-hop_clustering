import sys
import xml.etree.ElementTree as ET


def remove_bus_vehicles(xml_file_path, output_file_path):
    # Parse the XML file
    tree = ET.parse(xml_file_path)
    root = tree.getroot()

    # Find and remove vehicles with "bus" in their IDs
    for timestep in root.findall(".//timestep"):
        for vehicle in timestep.findall(".//vehicle"):
            vehicle_id = vehicle.get("id", "")
            if "bus" in vehicle_id:
                timestep.remove(vehicle)

    # Save the modified XML to a new file
    tree.write(output_file_path)


input_xml_file = '/Users/pouyafirouzmakan/Desktop/VANET_single-hop_clustering/final_data_Richmondhill/sumoTrace.xml'
output_xml_file = ('/Users/pouyafirouzmakan/Desktop/VANET_single-hop_clustering/final_data_Richmondhill/'
                   'sumoTrace_no_bus_and_rsu.xml')

remove_bus_vehicles(input_xml_file, output_xml_file)

