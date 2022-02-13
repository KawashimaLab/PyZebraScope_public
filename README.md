This is a repository for PyZebrascope, an open-source Python platform for brain-wide neural activity imaging in zebrafish.

Light-sheet microscopy for whole-brain neural activity imaging in zebrafish requires specific features not available in commercially distributed microscopes. Such features include scanning of two orthogonal excitation beams and eye damage prevention. These particular requirements, as well as numerous device parameters required for the experimenter to manipulate, have been the main bottlenecks of performing experiments and disseminating/developing technology. We developed PyZebrascope to address this issue by taking advantage of other open-source microscopy projects such as μManager and additional modules for device control, signal processing, computer vision, and machine learning.

![PyZebrascope_structure](https://user-images.githubusercontent.com/61713599/153410661-dba6a690-caa8-4bfd-ae97-e86001c326c8.png)

A list of hardware that we used to develop PyZebrascope is described in detail in our manuscript (Barbara, Kantharaju et al, link).

PyZebrascope requires the preinstallation of following hardware drivers and low-level interfaces:

- Hardware drivers from manufacturers for miscellaneous devices including cameras
- DAQmx driver from National Instruments (https://www.ni.com/en-il/support/downloads/drivers/download.ni-daqmx.html
- μManager (https://micro-manager.org/) for camera interface
- CUDA toolkit (https://developer.nvidia.com/cuda-toolkit) for fast autofocusing based on nVidia GPU

Then, it is necessary to install the below Python packages

- Anaconda package (https://anaconda.org/anaconda/python)
- PyQt5 (https://pypi.org/project/PyQt5/)
- pyqtgraph (https://www.pyqtgraph.org/)
- pymmcore (https://github.com/micro-manager/pymmcore, need to match its version with μManager)
- ni-daqmx for Python (https://nidaqmx-python.readthedocs.io/)
- h5py (https://www.h5py.org/)
- CuPy (https://cupy.dev/, need to match its version with CUDA toolkit)





