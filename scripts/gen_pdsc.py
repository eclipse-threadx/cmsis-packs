"""
Generate cmsis-pack pdsc file from pdsc_template.xml
"""

import os
import shutil
import xml.etree.ElementTree as ET

PDSC_TEMPLATE_FILE_NAME = "pdsc_template.xml"


def get_component_from_cmake_file(cmake_file):
    """
    Get component from common/CMakeLists.txt

    Args:
        cmake_file(string) : CMakeLists.txt for this azure-rtos component
    """
    # Open the CMakeLists.txt file
    contents = ""
    with open(cmake_file, "r", encoding="utf-8") as file:
        for line in file:
            # Remove leading/trailing whitespaces
            line = line.strip()
            # Ignore comment lines or empty lines
            if line.startswith("#") or not line:
                continue
            contents += line

    current_dir = os.path.dirname(cmake_file)
    current_dir = os.path.normpath(current_dir)

    # Find all occurrences of add_subdirectory() directives
    subdirs = []
    pos = 0
    while True:
        pos = contents.find("add_subdirectory(", pos)
        if pos == -1:
            break
        end_pos = contents.find(")", pos)
        subdir_line = contents[pos +
                               len("add_subdirectory("):end_pos].strip("")
        subdir = subdir_line.split("/")
        subdirs.append(subdir[-1])
        pos = end_pos

    return subdirs


def get_file_from_cmake_file(cmake_file, files_element):
    """
    Parse CMakeLists.txt to get source file names and put into files_element

    Args:
        cmake_file(string): CMakeLists.txt to be parsed
        files_element(Element): files elements in pdsc file

    """
    # Open the CMakeLists.txt file
    contents = ""
    with open(cmake_file, "r", encoding="utf-8") as file:
        for line in file:
            # Remove leading/trailing whitespaces
            line = line.strip()
            # Ignore comment lines or empty lines
            if line.startswith("#") or not line:
                continue
            contents += line

    current_dir = os.path.dirname(cmake_file)
    current_dir = os.path.normpath(current_dir)

    # check for the presence of target_include_directories()
    if "target_include_directories(" in contents:
        # Extract source files from target_include_directories() directive
        start_pos = contents.find("target_include_directories(")
        include_list = contents[start_pos + len("target_include_directories("):
                                contents.find(")", start_pos)]
        # Parse the source files
        c_incs = [
            source for source in include_list.split("$")
            if source.endswith("inc") or source.endswith("include")
        ]
        if c_incs:
            for inc in c_incs:
                output_str = inc.replace("{CMAKE_CURRENT_LIST_DIR}",
                                         current_dir)
                output_str = output_str[3:]
                output_str = output_str.replace("\\", "/")
                file_element = ET.SubElement(files_element, "file")
                file_element.set("category", "include")
                file_element.set("name", output_str + "/")

    # Check for the presence of target_sources() directives
    if "target_sources(" in contents:
        # Extract the source files from the target_sources() directive
        start_pos = contents.find("target_sources(")
        source_list = contents[start_pos + len("target_sources("):
                                contents.find(")", start_pos)]

        # Parse the source files
        c_sources = [source for source in source_list.split("$") if source.endswith(".c")]
        if c_sources:
            for c_source in c_sources:
                output_str = c_source.replace("{CMAKE_CURRENT_LIST_DIR}",
                                              current_dir)
                output_str = output_str[3:]
                output_str = output_str.replace("\\", "/")
                file_element = ET.SubElement(files_element, "file")
                file_element.set("category", "source")
                file_element.set("name", output_str)


def update_conditions(root, port_devices, ports_dir):
    """
    check each ports_device and its compiler variants,
    then add TCompiler and DCore conditions to pdsc

    Args:
        root: the root object of psdc_template.xml file
        port_devices: supported porting devices defined in psdc_template.xml
        ports_dir: ports_dir defined in psdc_template.xml

    Returns:
        porting_files: device and compiler specific porting files
    """
    # dictionary to save supported device porting files
    # such as {"CA5 GNU Condition": "ports/cortex_a5/gnu/"}
    porting_files = {}
    conditions_subcomponent = root.find("conditions")
    for device in port_devices:
        core = "-".join([part[0].upper() + part[1:] for part in device.split("_")])

        # check the subdir of ports + device
        ports_device_dir = os.path.join(ports_dir, device)
        if not os.path.isdir(ports_device_dir):
            print(f"No {device} folder found in {ports_dir}")
            os.system("pwd")
            continue

        # check the compiler variants
        for subdir in os.listdir(ports_device_dir):
            if subdir == "gnu":
                compiler = "GCC"
                condition_id = "C" + device[-2:].upper() + " GNU Condition"
                desc = core + " / GNU Compiler"
            elif subdir == "iar":
                compiler = "IAR"
                condition_id = "C" + device[-2:].upper() + " IAR Condition"
                desc = core + " / IAR Compiler"
            elif subdir in ("keil", "ac6"):
                compiler = "ARMCC"
                condition_id = "C" + device[-2:].upper() + " ARMC6 Condition"
                desc = core + " / ARM Compiler 6"
            elif subdir == "ac5":
                compiler = "ARMCC"
                condition_id = "C" + device[-2:].upper() + " ARMC5 Condition"
                desc = core + " / ARM Compiler 5"
            else:
                print(f"Not supported compiler variant for {subdir}")
                continue

            porting_files[condition_id] = os.path.join(
                                            ports_device_dir, subdir)[3:].replace("\\", "/")
            condition_element = ET.SubElement(conditions_subcomponent,
                                              "condition")
            condition_element.attrib["id"] = condition_id
            description_element = ET.SubElement(condition_element,
                                                "description")
            description_element.text = desc

            # Create the require elements and add them to the root element
            ET.SubElement(condition_element, "require", Tcompiler=compiler)
            ET.SubElement(condition_element, "require", Dcore=core)

    condition_subcomponent = conditions_subcomponent.findall("condition")
    if not condition_subcomponent:
        print("No <condition> found, remove <conditions>")
        root.remove(conditions_subcomponent)

    return porting_files

def update_pack_component(component, bundle_subcomponent, azrtos_component_name,
                     porting_files):
    """
    update pack component element with description, RTE_Components_h, porting files

    Args:
        component(string): pack component name
        bundle_subcomponent: bundle subcomponent in pdsc file
        azrtos_component_name(string): azrtos component name
        porting_files: porting files for specific device and compiler

    """
    component_element = ET.SubElement(bundle_subcomponent, "component")
    component_element.attrib["Cgroup"] = azrtos_component_name
    component_element.attrib["Csub"] = component
    component_element.attrib["maxInstances"] = "1"
    description_element = ET.SubElement(component_element, "description")
    description_element.text = ("Azure RTOS " + azrtos_component_name
                                + " " + component)
    rte_element = ET.SubElement(component_element, "RTE_Components_h")
    if component in ("core", "common"):
        rte_element.text = ("#define AZURE_RTOS_"
                            + azrtos_component_name.upper() + "_ENABLED")
    else:
        rte_element.text = ("#define AZURE_RTOS_"
                            + component.upper() + "_ENABLED")

    files_element = ET.SubElement(component_element, "files")

    # add Cortex porting files into core or common component
    if component in ("core", "common"):
        for condition in porting_files:
            file_element = ET.SubElement(files_element, "file")
            file_element.set("category", "include")
            file_element.set("condition", condition)
            file_element.set("name", porting_files[condition] + "/")

    return files_element


def update_pack_components(root, common_dir_subcomponent, azrtos_component_name, porting_files):
    """
    update pack components with component and files

    Args:
        root: the root object of psdc_template.xml file
        common_dir_subcomponent: common_dir_subcomponent object of psdc_template.xml
        azrtos_component_name: this azure rtos component name
        porting_files: device and compiler specific porting files
    """
    components_subcomponent = root.find("components")
    bundle_subcomponent = components_subcomponent.find("bundle")

    cmake_file = os.path.join(common_dir_subcomponent.text, "CMakeLists.txt")

    if not os.path.isfile(cmake_file):
        print(f"No CMakeLists.txt file found in {common_dir_subcomponent.text}")

    components_list = get_component_from_cmake_file(cmake_file)

    if components_list:
        for component in components_list:
            # print(f"components {component} found in {cmake_file}")
            files_element = update_pack_component(component, bundle_subcomponent,
                                             azrtos_component_name, porting_files)
            sub_cmake_file = os.path.join(common_dir_subcomponent.text, component,
                                          "CMakeLists.txt")
            # add source and inc into each component
            get_file_from_cmake_file(sub_cmake_file, files_element)
    else:
        # No individual components, add all files into one "common" component
        # print(f"Add all files into one common component")
        component = "common"
        files_element = update_pack_component(component, bundle_subcomponent,
                                         azrtos_component_name, porting_files)
        # add source and inc into each component
        get_file_from_cmake_file(cmake_file, files_element)


def generate_pdsc_file(azrtos_component_data_path, cmsis_pack_working_path):
    """
    generate package description file from this azrtos component's pdsc_template.xml

    Args:
        azrtos_component_data_path(string): data path where the generated pdsc is saved to
        cmsis_pack_working_path(string): the working path where pdsc_template.xml is located

    """
    # pdsc template file name
    tree = ET.parse(os.path.join(cmsis_pack_working_path, PDSC_TEMPLATE_FILE_NAME))
    root = tree.getroot()

    # set root attributes
    root.set("schemaVersion", "1.7.7")
    root.set("xmlns:xs", "http://www.w3.org/2001/XMLSchema-instance")
    root.set(
    "xs:noNamespaceSchemaLocation",
    "https://raw.githubusercontent.com/Open-CMSIS-Pack/Open-CMSIS-Pack-Spec/v1.7.7/schema/PACK.xsd",
    )

    # get common dir, porting dir, component name
    # and supported porting devices from template
    common_dir_subcomponent = root.find("common_dir")

    ports_dir_subcomponent = root.find("ports_dir")
    if ports_dir_subcomponent is not None:
        ports_dir = ports_dir_subcomponent.text
    else:
        ports_dir = ""

    azrtos_component_name_subcomponent = root.find("azrtos_component_name")
    azrtos_component_name = azrtos_component_name_subcomponent.text

    port_devices = [elem.text for elem in root.iter("port_device")]
    port_devices_subcomponent = root.find("port_devices")

    # remove these component from xml
    root.remove(common_dir_subcomponent)
    root.remove(azrtos_component_name_subcomponent)
    if ports_dir_subcomponent is not None:
        root.remove(ports_dir_subcomponent)
    if port_devices_subcomponent is not None:
        root.remove(port_devices_subcomponent)

    # get pack vendor and name from template
    pack_vendor_subcomponent = root.find("vendor")
    pack_name_subcomponent = root.find("name")

    # output psdc file name
    output_file = pack_vendor_subcomponent.text + "." + pack_name_subcomponent.text + ".pdsc"
    output_file = os.path.join(cmsis_pack_working_path, output_file)

    # update conditions in pdsc
    porting_files = update_conditions(root, port_devices, ports_dir)

    # update components in pdsc
    update_pack_components(root, common_dir_subcomponent, azrtos_component_name, porting_files)

    tree = ET.ElementTree(root)
    ET.indent(tree, "   ")
    ET.ElementTree(root).write(output_file,
                               encoding="utf-8",
                               xml_declaration=True)

    # save the generated pdsc file
    shutil.copy(output_file, azrtos_component_data_path)
    print(f"{output_file} is generated successfully")
