# OpenRadioss Tools

## What is OpenRadioss?

****Simcenter(TM) Radioss(R)** i** is an industry-proven analysis solution that helps users evaluate and optimize product performance for highly nonlinear problems under dynamic loading. For more than 30 years, organizations have used Simcenter Radioss to streamline and optimize the digital design process, replace costly physical tests with quick and efficient simulation, and speed up design optimization iterations.

**OpenRadioss** is the publicly available open-source code base that a worldwide community of researchers, software developers, and industry leaders are enhancing every day. OpenRadioss is changing the game by empowering users to make rapid contributions that tackle the latest challenges brought on by rapidly evolving technologies like battery development, lightweight materials and composites, human body models and biomaterials, autonomous driving and flight, as well as the desire to give passengers the safest environment possible via virtual testing.

With OpenRadioss, scientists and technologists can focus their research on a stable code base under professional maintenance that benefits from the large library of existing finite element capabilities and the continuous integration and continuous development tools provided to contributors.

For more information on OpenRadioss project, please visit the OpenRadioss GitHub at [https://github.com/OpenCourant/OpenCourant](https://github.com/OpenCourant/OpenCourant) or the OpenRadioss web page [opencourant.org](https://opencourant.org)
If you have any questions about OpenRadioss, please feel free to contact <hello@opencourant.org>.

## What is OpenRadioss Tools

Tools Repository is dedicated to hosts tools for OpenRadioss:

## OpenRadioss GUI

OpenRadioss GUI is a graphical launcher for OpenRadioss

[https://github.com/OpenCourant/Tools/tree/main/openradioss_gui](https://github.com/OpenCourant/Tools/tree/main/openradioss_gui)

## Input converters

* [inp2rad](https://github.com/OpenCourant/Tools/tree/main/input_converters/inp2rad) : converts .inp format to Radioss (.rad) format.

## Output converter

* anim_to_csv : converts OpenRadioss animation files to csv format.
* th_to_nms   : converts OpenRadioss time history files to nms format.

[https://github.com/OpenCourant/Tools/tree/main/output_converters](https://github.com/OpenCourant/Tools/tree/main/output_converters)

* Animation to d3plot converter can be found on [Vortex-CAE GitHub repository](https://github.com/Vortex-CAE/Vortex-Radioss)

## userlib_sdk : Radioss user library SDK

**Simcenter Radioss®** and **OpenRadioss** have a user interface to create libraries containing user routines and use them in Radioss.
The user library is generated using the userlib_sdk. The userlib_sdk is a collection of different platforms and compilers to create libraries.
Each platform/compiler set has a `build_script`, a static library and Fortran Module files. Those will permit to generate the user library.

[https://github.com/OpenCourant/Tools/tree/main/userlib_sdk](https://github.com/OpenCourant/Tools/tree/main/userlib_sdk)

## How to contribute in Tools

[How to contribute in Tools](Contributing.md)
