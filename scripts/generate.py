"""
This Python script generates cmsis-packs for Azure RTOS modules.

Usage:
--  Generate CMSIS-Packs for all Azure RTOS modules.
    $ python3 /path/to/generate.py

--  Generate CMSIS-Packs for specific Azure RTOS modules.
    $ python3 /path/to/generate.py -m "threadx, usbx"

--  Force to (re)generate pack description files(*.pdsc) before generating CMSIS-Packs.
    Note: The pdsc files of filex, usbx, guix and levelx are generated automatically based on
          their source codes and pdsc_template.xml.
          This version doesn't supports generating pdsc for threadx and netxduo.
          Their pdsc files are still manually updated.
    $ python3 /path/to/generate.py -f
    $ python3 /path/to/generate.py -f -m "filex, usbx"

"""
from argparse import RawTextHelpFormatter
from argparse import ArgumentParser
import os
import shutil
import sys
import gen_pdsc

DATA_DIR = "data"
SCRIPTS_DIR = "scripts"

# Specify directory names to be added to pack base directory
PACK_DIRS = {
    "threadx": "./common ./ports ./utility ./examples",
    "netxduo": "./common ./addons ./nx_secure ./crypto_libraries ./ports ./utility",
    "filex": "./common ./ports",
    "usbx": "./common ./ports",
    "guix": "./common ./ports",
    "levelx": "./common",
}


def process_module(azrtos_module_name):
    """
    This function generates cmsis-pack for specified Azure-RTOS module.
    It can generate cmsis-pack from pdsc file directly if without "-f" option;
    or it will first generate pdsc file from pdsc_template.xml if "-f" is present.

    Args:
        azrtos_module_name (string): threadx, netxduo, filex, usbx, guix, or levelx.

    """
    # Construct the directory path
    module_source_path = os.path.join(root_path, azrtos_module_name)
    module_data_path = os.path.join(data_path, azrtos_module_name)

    if not os.path.exists(module_source_path):
        print(module_source_path + " not found!")
        sys.exit(1)

    if not os.path.exists(module_data_path):
        print(module_data_path + " not found!")
        sys.exit(1)

    # create the cmsis_pack_working folder at {module_source_path}/cmsis_pack
    print("Copy data/" + azrtos_module_name + " to " + module_source_path)
    cmsis_pack_working_path = os.path.join(module_source_path + "/cmsis_pack")
    if not os.path.exists(cmsis_pack_working_path):
        os.mkdir(cmsis_pack_working_path)

    # copy every folder in module_data_path to cmsis_pack_working_path
    copied_folders = []
    for item in os.listdir(module_data_path):
        item_path = os.path.join(module_data_path, item)
        if os.path.isdir(item_path):
            shutil.copytree(item_path, os.path.join(module_source_path, item))
            copied_folders.append(os.path.join(module_source_path, item))

    # if arg.f, generate pdsc file, but not for threadx or netxduo
    if args.f and azrtos_module_name not in ("threadx", "netxduo"):
        print("Generate pack description file for module: " + azrtos_module_name)
        # process pdsc_template.xml in cmsis_pack_working_path
        shutil.copyfile(
            os.path.join(module_data_path, "pdsc_template.xml"),
            os.path.join(cmsis_pack_working_path, "pdsc_template.xml"),
        )
        os.chdir(cmsis_pack_working_path)
        gen_pdsc.generate_pdsc_file(
            module_data_path, cmsis_pack_working_path
        )
        os.remove(os.path.join(cmsis_pack_working_path, "pdsc_template.xml"))

    copied_gen_pack_sh = os.path.join(module_source_path, "gen_pack.sh")
    shutil.copy(os.path.join(scripts_path, "gen_pack.sh"), copied_gen_pack_sh)

    src_pdsc_file = ""
    copied_pdsc_file = ""
    for file in os.listdir(module_data_path):
        if file.endswith(".pdsc"):
            src_pdsc_file = os.path.join(module_data_path, file)
            copied_pdsc_file = os.path.join(module_source_path, file)
            shutil.copyfile(src_pdsc_file, copied_pdsc_file)

    if copied_pdsc_file == "":
        print("Error: no pdsc file")
        sys.exit(1)

    # goto module_source_path, call "./gen_pack.sh" bash there.
    os.chdir(module_source_path)

    # run gen_pack.sh with argument PACK_DIRS[azrtos_module_name]
    print("Call ./gen_pack.sh to generate cmsis_pack")
    cmd = "./gen_pack.sh " + '"' + PACK_DIRS[azrtos_module_name] + '"'
    os.system(cmd)

    # copy generated cmsis-pack file to root_path
    for file in os.listdir(os.path.join(cmsis_pack_working_path, "output")):
        if file.endswith(".pack"):
            shutil.copy(
                os.path.join(cmsis_pack_working_path, "output", file),
                root_path
            )

    # remove copied items and cmsis_pack_working_path
    os.remove(copied_gen_pack_sh)
    os.remove(copied_pdsc_file)
    shutil.rmtree(cmsis_pack_working_path)
    for item in copied_folders:
        shutil.rmtree(item)


parser = ArgumentParser(
    description="Generate CMSIS-Packs for Azure RTOS modules.\n\n"
    "Requirement: Python 3.9 or higher.\n\n"
    "By default it generate packs for all Azure RTOS modules "
    "using the existing pack description files (*.pdsc).\n"
    "$ python3 ./scripts/generate.py",
    formatter_class=RawTextHelpFormatter,
)

parser.add_argument(
    "-m",
    type=str,
    help="Generate CMSIS-Packs for specific Azure RTOS modules, "
    "their names are separated by comma. \n"
    'Example: $ python3 ./scripts/generate.py -m "threadx, usbx" \n',
)
parser.add_argument(
    "-f",
    action="store_true",
    help="Force to (re)generate pack description files (*.pdsc) before generating CMSIS-Packs. \n"
    "Example: $ python3 ./scripts/generate.py -f \n"
    '         $ python3 ./scripts/generate.py -f -m "threadx, usbx" \n',
)

args = parser.parse_args()

if args.m:
    MODULES = args.m
else:
    MODULES = "threadx, netxduo, usbx, filex, guix, levelx"

print("*******************************************************************")
if args.f:
    print("Generate pack description files first, and then")
print("Generate cmsis-packs for Azure RTOS modules: " + MODULES)
print("*******************************************************************")

cwd = os.getcwd()
print("current working directory: " + cwd)

if os.path.exists(os.path.join(cwd, DATA_DIR)):
    root_path = cwd
elif os.path.exists(os.path.join(cwd, "..", DATA_DIR)):
    root_path = os.path.normpath(os.path.join(cwd, ".."))
else:
    print("data folder not found!")
    sys.exit(1)

data_path = os.path.join(root_path, DATA_DIR)
scripts_path = os.path.join(root_path, SCRIPTS_DIR)
print("root folder:    " + root_path)
print("data folder:    " + data_path)
print("scripts folder: " + scripts_path)

if MODULES:
    # split modules into a list
    modules = MODULES.replace(",", " ").split()
    # process each module
    for module in modules:
        print("**************************************************************")
        print("process_module: " + module)
        process_module(module)
