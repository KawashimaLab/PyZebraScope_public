## PyZebraScope: an open-source platform for brain-wide neural activity imaging in zebrafish

This is a repository for PyZebrascope, an open-source Python platform for brain-wide neural activity imaging in zebrafish.

Light-sheet microscopy for whole-brain neural activity imaging in zebrafish requires specific features not available in commercially distributed microscopes. Such features include scanning of two orthogonal excitation beams and eye damage prevention. These particular requirements, as well as numerous device parameters required for the experimenter to manipulate, have been the main bottlenecks for disseminating / developing technology and performing daily experiments. We developed PyZebrascope to address these issues.

PyZebrascope is a high-level interface designed for neural activity imaging experiments based on light-sheet microsscopy in zebrafish. It incorporates functionalities from other open-source microscopy projects such as μManager and additional modules for device control, signal processing, computer vision, and machine learning.

![PyZebrascope_structure](https://user-images.githubusercontent.com/61713599/153410661-dba6a690-caa8-4bfd-ae97-e86001c326c8.png)

A list of hardware that we used to develop PyZebrascope is described in detail in our manuscript
https://www.biorxiv.org/content/10.1101/2022.02.13.480249v1

### Installation requirements

PyZebrascope requires the preinstallation of following hardware drivers and low-level interfaces:

- Hardware drivers from manufacturers for miscellaneous devices including cameras
- DAQmx driver from National Instruments (https://www.ni.com/en-il/support/downloads/drivers/download.ni-daqmx.html)
- μManager (https://micro-manager.org/) for camera interface
- CUDA toolkit (https://developer.nvidia.com/cuda-toolkit) for fast autofocusing based on nVidia GPU

The below Python packages are required to run PyZebrascope

- Anaconda package (https://anaconda.org/anaconda/python)
- PyQt5 (https://pypi.org/project/PyQt5/)
- pyqtgraph (https://www.pyqtgraph.org/)
- pymmcore (https://github.com/micro-manager/pymmcore, need to match its version with μManager)
- ni-daqmx for Python (https://nidaqmx-python.readthedocs.io/)
- h5py (https://www.h5py.org/)
- CuPy (https://cupy.dev/, need to match its version with CUDA toolkit)

Note that nVidia GPU board, CUDA toolkit and CuPy are only necessary for speeding up the computation time for the autofocusing feature. We still have CPU-based codes in auto_focusing.py

### Software interface

PyZebrascope have two main tabbed interface with a camera view window. Additionally, it has an interface to set a laser exclusion area for eye damage prevention.

![Fig2](https://user-images.githubusercontent.com/61713599/154578417-47b0ecab-eab1-4cc5-8db5-1e57805124d1.png)


### File writing

Image data from cameras are processed like below. Three Qthreads (Reader, Writer, CamView) runs in parallel for each camera to support file writing and data preview. This structure achieved over 800 MB/s writing performances on a fast NVMe drive (Micron 9300) or SSD RAID system.

![Figure_file_writing](https://user-images.githubusercontent.com/61713599/158383851-e8de09d3-9b34-4724-ae18-ada36b1585fb.png)



