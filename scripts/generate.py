from argparse import RawTextHelpFormatter
from argparse import ArgumentParser
import os
import gen_pdsc
import shutil

DATA_DIR = "data"
SCRIPTS_DIR = "scripts"

# Specify directory names to be added to pack base directory
PACK_DIRS = {
    "threadx": "./common ./ports ./utility ./examples",
    "netxduo": "./common ./addons ./nx_secure ./crypto_libraries ./ports ./utility",
    "filex":   "./common ./ports",
    "usbx":    "./common ./ports",
    "guix":    "./common ./ports",
    "levelx":  "./common ./ports"
}

def process_module(module):
    # Construct the directory path
    module_source_path = os.path.join(root_path, module)
    module_data_path = os.path.join(data_path, module)

    if not os.path.exists(module_source_path):
        print(module_source_path + " not found!")
        exit(1)

    if not os.path.exists(module_data_path):
        print(module_data_path + " not found!")
        exit(1)

    # create the cmsis_pack_working folder at {module_source_path}/cmsis_pack
    print("Copy data/" + module + " to " + module_source_path)
    cmsis_pack_working_path = os.path.join(module_source_path + '/cmsis_pack')
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
    if args.f and (module != "threadx" and module != "netxduo"):
        print("Generate package description file for module: " + module)
        # process pdsc_template.xml in cmsis_pack_working_path
        shutil.copyfile(os.path.join(module_data_path, "pdsc_template.xml"), os.path.join(cmsis_pack_working_path, "pdsc_template.xml"))
        os.chdir(cmsis_pack_working_path)
        gen_pdsc.generate_pdsc_file(module_source_path, module_data_path, cmsis_pack_working_path)
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
        exit(1)

    # goto module_source_path, call "./gen_pack.sh" bash there.
    os.chdir(module_source_path)

    # run gen_pack.sh with argument PACK_DIRS[module]
    print("Call ./gen_pack.sh to generate cmsis_pack")
    cmd = "./gen_pack.sh " + "\"" + PACK_DIRS[module] + "\""
    os.system(cmd)

    # copy generated cmsis-pack file to root_path
    for file in os.listdir(os.path.join(cmsis_pack_working_path, "output")):
        if file.endswith(".pack"):
            shutil.copy(os.path.join(cmsis_pack_working_path, "output", file), root_path)
    
    # remove copied items and cmsis_pack_working_path
    os.remove(copied_gen_pack_sh)
    os.remove(copied_pdsc_file)
    shutil.rmtree(cmsis_pack_working_path)
    for item in copied_folders:
        shutil.rmtree(item)

parser = ArgumentParser(description='Python script to generate cmsis-packs for Azure RTOS', formatter_class=RawTextHelpFormatter)

parser.add_argument("-a", "--all", action="store_true", help="Generate CMSIS-Packs for all Azure RTOS modules.\n"
                                    "Example: python ./generate.py -a \n")
parser.add_argument("-m", type=str, help="Generate specific CMSIS-Packs for individual Azure RTOS modules, their names are separated by comma. \n"
                                    "Example: python ./generate.py -m \"threadx, usbx\" \n")
parser.add_argument("-f", action="store_true", help="Force to (re)generate package description files(*.pdsc). \n"
                                    "Example: python ./generate.py -a -f \n"
                                    "         python ./generate.py -f \"threadx, usbx\" \n")
args = parser.parse_args()

if (not args.all and not args.m) or args.all:
    modules = "threadx, netxduo, usbx, filex, guix, levelx"
elif args.m:
    modules = args.m

print("*******************************************************************************************")
if args.f:
    print("Generate package description files first, and then")
print("Generate cmsis-packs for Azure RTOS modules: " + modules)
print("*******************************************************************************************")

cwd = os.getcwd()
print("current working directory: " + cwd)

if os.path.exists(os.path.join(cwd, DATA_DIR)):
    root_path = cwd
elif os.path.exists(os.path.join(cwd, "..", DATA_DIR)):
    root_path = os.path.normpath(os.path.join(cwd, ".."))
else:
    print("data folder not found!")
    exit(1)

data_path = os.path.join(root_path, DATA_DIR)
scripts_path = os.path.join(root_path, SCRIPTS_DIR)
print("root folder:    " + root_path)
print("data folder:    " + data_path)
print("scripts folder: " + scripts_path)


if modules:
    #split modules into a list
    modules = modules.replace(",", " ").split()
    #process each module
    for module in modules:
        print("--------------------------------------------------------------------------------------")
        print("process_module: " + module)
        process_module(module)
