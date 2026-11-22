# INP to Rad converter

## Description

This Python script converts .inp format to Radioss (.rad) format.
It can be used as a standalone tool or as a plugin to the [OpenCourant gui tool](https://github.com/OpenCourant/Tools/tree/main/openradioss_gui).
It is provided “as is”, and should be considered as 'beta' today, but has been successfully tested on a wide range of explicit models and already supports most commonly used element formulations, material laws, loadings and boundary conditions.
Through provision of this tool, we hope to further enhance the accessibility of OpenCourant by enabling the use of open-source pre-processors supporting the .inp format such as [PrePoMax](https://prepomax.fs.um.si).

## Installation

You need to have a python3 installation on Linux or Windows.

* On ***Windows*** : check [python.org](https://www.python.org/) web site to install Python
* On ***Linux***, install python from your OS Repository.

  * On RedHat, CentOS, Rocky Linux

          dnf install python3
          dnf install python3-tkinter

  * On Debian, Ubuntu

          apt-get install python3
          apt install python3-tk

 
 ## Use With OpenCourant Gui if self compiling

 inp2rad is packaged with comiled distributed OpenCourant releases, these steps are needed only when self compiling OpenCourant

 install openradioss_gui from tools

 add inp2rad.py to the openradioss_gui folder in your installation

 
 ## Following only needed for Installation as commandline executable

  install the pyinstaller package

  * On Linux as root

          pip3 install pyinstaller
  
  * On Windows

          pip install pyinstaller

Apply the command:

* On ***Windows*** launch

        install.bat

* On ***Linux*** launch as root

        install.sh

This will install the inp2rad.py into Python library collection and inp2rad[.exe] into execution directory


## Supported .inp keywords and Syntax

The convertor aims to support .inp format with a good degree of flexibility, case, spacing and most special characters should be ok, use of ELSET, NSET names inside other ELSET, NSET is supported

Supported keywords: (not all sub-options necessarily supported):

*AMPLITUDE (only TABULAR, default form)

*BOUNDARY (default, SPC type and TYPE=DISPLACEMENT, TYPE=VELOCITY)

*BOUNDARY condition mappings ENCASTR, PINNED, XSYMM, YSYMM, ZSYMM
    
*CLOAD

*COHESIVE SECTION

*CONTACT

*CONTACT PAIR

*CONTACT PROPERTY ASSIGNMENT

*COUPLING, *DISTRIBUTING or *KINEMATIC

*DAMAGE INITIATION, CRITERION = JOHNSON COOK

*DAMPING,( with ALPHA =, BETA =, for material damping)

*DENSITY

*DISTRIBUTING

*DISTRIBUTING COUPLING

*DLOAD (only GRAV type)

*DSLOAD, (Pressure Load Types P, P1, P2, P3, P4, P5, P6)

*ELEMENT, *TYPE=

Supported Abaqus 3D element families (aliases share the same conversion):

* shells: S3/S3R/M3D3/R3D3/SFM3D3/S3RS, S4/S4R/S4RS/S4RSW/S4RT/S4R5/
  M3D4/M3D4R/R3D4/SFM3D4/SFM3D4R, S6/S6R, S8/S8R/S8RT
  -> /SH3N (3 node), /SHELL (4 node); quadratic shells are degraded to
  their linear counterparts with a warning
* tetrahedra: C3D4/DC3D4 -> /TETRA4,
  C3D10/C3D10M/C3D10H/C3D10MH/C3D10MT/C3D10MHT/DC3D10 -> /TETRA10
* prisms: C3D6/DC3D6/SC6R/COH3D6, C3D15/C3D15V/DC3D15
  -> degenerate /BRICK (no quadratic pentahedron exists in Radioss)
* hexahedra: C3D8/C3D8R/C3D8I/C3D8RH/DC3D8/COH3D8/SC8R -> /BRICK,
  C3D20/C3D20R/C3D20H/C3D20HT/C3D20RT/DC3D20 -> /BRIC20,
  C3D27/C3D27R/C3D27H/C3D27RH -> /BRIC20 with the extra nodes dropped
* masses/connectors: MASS, DCOUP3D, CONN3D2, SPRINGA

Radioss has no `/BRIC27` keyword (even in the 2026 reference guide): the
quadratic hexahedron offering is `/BRIC20` only.  C3D27 face-centre and
centroid nodes are therefore dropped.  The Abaqus and Radioss midside-node
orders differ, so the converter remaps nodes 13-20 of quadratic hexahedra.
The generated `/PROP/SOLID` uses `Isolid=16` whenever a quadratic solid is
present, as required by `/BRIC20`.

Surface-based contact surfaces are built from the corner nodes of the
converted elements.

*ELSET, ELSET (GENERATE supported)

*FRICTION (with coefficient on next line)

*FRICTION, ROUGH

*HYPERELASTIC (MOONEY-RIVLIN, OGDEN, NEO HOOKE, POLYNOMIAL, REDUCED POLYNOMIAL and MARLOW (only with *UNIAXIAL TEST DATA version) forms only)

*HYPERFOAM, (with either TEST DATA or MU ALPHA PR parameters)

*INCLUDE (include files supported for input, the output .rad file will be a single merged file)

*INITIAL CONDITIONS (VELOCITY only)

*KINEMATIC COUPLING

*MASS

*MATERIAL

*MEMBRANE SECTION

*MPC (generates spring beams)

*NODE

*NSET, NSET (GENERATE supported)

*PLASTIC

*RIGID BODY

*SHELL SECTION

*SOLID SECTION

*SUPERELASTIC

*SURFACE, TYPE=ELEMENT or TYPE=NODE

*SURFACE INTERACTION

*SURFACE INTERACTION, NAME=RADIOSS_GENERAL (special usecase to ease PrePoMax usage, existence of this will result in a global general contact)

*SYSTEM

*TIE (TYPE = NODE TO SURFACE or TYPE = SURFACE TO SURFACE)

*UNIAXIAL TEST DATA

*VISCOELASTIC, TIME = PRONY
