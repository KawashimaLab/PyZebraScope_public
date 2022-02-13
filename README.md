This is a repository for PyZebrascope, an open-source Python platform for brain-wide neural activity imaging in zebrafish.

Light-sheet microscopy for whole-brain neural activity imaging in zebrafish requires specific features not available in commercially distributed microscopes. Such features include scanning of two orthogonal excitation beams and eye damage prevention. These particular requirements and the overwhelming number of device parameters that the users need to manipulate during experiments were the main bottlenecks of performing experiments and disseminating/developing technology. We developed PyZebrascope to address this issue by taking advantage of other open-source microscopy projects such as μManager and additional modules for device control, image processing, and machine learning.

![PyZebrascope_structure](https://user-images.githubusercontent.com/61713599/153410661-dba6a690-caa8-4bfd-ae97-e86001c326c8.png)

A list of hardware that we used to develop PyZebrascope is described in detail in our manuscript (Barbara, Kantharaju et al, link).

PyZebrascope requires the preinstallation of μManager (https://micro-manager.org/) and DAQmx driver from National Instruments (https://www.ni.com/en-il/support/downloads/drivers/download.ni-daqmx.html) for camera control and analog/digital outputs, respectively. In addition, it is necessary to install the below Python packages:

- Anaconda package (https://anaconda.org/anaconda/python)
- PyQt5 (https://pypi.org/project/PyQt5/)
- pyqtgraph (https://www.pyqtgraph.org/)
- pymmcore (https://github.com/micro-manager/pymmcore, need to match its version with μManager)
- ni-daqmx for Python (https://nidaqmx-python.readthedocs.io/)
- h5py (https://www.h5py.org/)


Installation of CUDA toolkit (https://developer.nvidia.com/cuda-toolkit) and below Python package is necessary to enable fast autofocusing based on GPU, although we still left CPU-based code in auto_focusing.py

- CuPy (https://cupy.dev/, need to match version with CUDA toolkit)





