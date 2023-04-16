# AzureRTOS-CMSIS-Packs

This repository contains Azure RTOS CMSIS-Packs for ThreadX, NetXDuo, Filex, USBX, GUIX and Levelx.

It also provides the scripts, data and source codes used to generate CMSIS-Packs and pack description files.

Pack description files (*.pdsc) are required to generate CMSIS-Packs.

* For FileX, USBX, GUIX and LevelX, their pack description files are generated automatically based on their source codes and a template xml file (pdsc_template.xml). 
The pdsc_template.xml defines data used to generate pdsc file, including pack's metadata, source file and porting file dictories, supported porting devices, release info, component decription, etc.

* For ThreadX and NetXDuo, their pack description files are currently manually written, but plans are in place to support automatic generation in the near future.

# Generate CMSIS-Packs on Ubuntu 20.4 or higher

## clone this reop recursively with azure-rtos as submodules
```
    git clone --recursive https://github.com/azure-rtos/cmsis-packs.git
    cd cmsis-packs
```

## Setup environment and install tools

Requirements: Python 3.9 or higher. 

```
    sudo apt-get update
    sudo apt-get install p7zip-full curl libxml2-utils unzip
    mkdir -p $HOME/Arm/Packs/ARM/CMSIS/5.9.0
    wget https://github.com/ARM-software/CMSIS_5/releases/download/5.9.0/ARM.CMSIS.5.9.0.pack
    unzip -q ARM.CMSIS.5.9.0.pack -d $HOME/Arm/Packs/ARM/CMSIS/5.9.0
    rm ARM.CMSIS.5.9.0.pack
    export CMSIS_PACK_ROOT=$HOME/Arm/Packs
    export PATH=$PATH:$HOME/Arm/Packs/ARM/CMSIS/5.9.0/CMSIS/Utilities/Linux64

```        
## Generate cmsis-packs
```
    # generate packs for all Azure RTOS modules using the existing pack description files (*.pdsc).
    python3 ./scripts/generate.py

    # Generate CMSIS-Packs for specific Azure RTOS modules
    python3 ./scripts/generate.py -m "threadx, usbx"

    # Force to (re)generate pack description files (*.pdsc) before generating CMSIS-Packs
    python3 ./scripts/generate.py -f
    python3 ./scripts/generate.py -f -m "threadx, usbx"

```
## Repository Structure
This repo add all Azure RTOS modules repo as submodules.

```
.
    ├── scripts                                         # All script files used to generate cmsis-packs and pack description files
    │   │
    │   ├── generate.py                                 # top level python script to generate cmsis-packs and pack description files
    │   ├── gen_pdsc.py                                 # python module to generate pack description file from azure-rtos source code and pdsc_template.xml
    │   └── gen_pack.sh                                 # bash script to generate cmsis-pack
    │
    ├── data                                            # Each module's pack description file, pdsc_template.xml, and any additional files to be added to CMSIS-Pack, such as example projects
    │   │
    │   ├── filex
    │   │   ├── Microsoft.AzureRTOS-FileX.pdsc
    │   │   └── pdsc_template.xml
    │   ├── guix
    │   │   ├── Microsoft.AzureRTOS-GUIX.pdsc
    │   │   └── pdsc_template.xml
    │   ├── levelx
    │   │   ├── Microsoft.AzureRTOS-LevelX.pdsc
    │   │   └── pdsc_template.xml
    │   ├── netxduo
    │   │   └── Microsoft.AzureRTOS-NetXDuo.pdsc
    │   ├── threadx
    │   │   ├── Microsoft.AzureRTOS-ThreadX.pdsc
    │   │   └── examples                                # Threadx CMSIS-Pack example projects
    │   └── usbx
    │       ├── Microsoft.AzureRTOS-USBX.pdsc
    │       └── pdsc_template.xml
    │
    ├── filex                                           # Azure RTOS source code from submodules
    ├── guix
    ├── levelx
    ├── netxduo
    ├── threadx
    └── usbx
