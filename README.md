This is a repository for PyZebrascope, an open-source Python platform for brain-wide neural activity imaging in behaving zebrafish.

Light-sheet microscopy for whole-brain neural activity imaging in zebrafish requires specific features not available in commercially distributed microscopes. Such features include scanning of two orthogonal excitation beams and eye damage prevention. These particular requirements and the overwhelming number of device parameters that the users need to manipulate during experiments were the main bottlenecks of performing experiments and disseminating/developing technology. We developed PyZebrascope to address this issue by taking advantage of other open-source microscopy projects such as μManager and additional modules for device control, image processing, and machine learning.

![PyZebrascope_architecture](https://user-images.githubusercontent.com/61713599/153392017-dcd0c76f-5e3b-49e4-8be2-1653cf5d43ad.png)

A list of hardware that we used to develop PyZebrascope is described in detail in our manuscript (Barbara, Kantharaju et al, link).

PyZebrascope requires the preinstallation of μManager (https://micro-manager.org/) and DAQmx driver from National Instruments (https://www.ni.com/en-il/support/downloads/drivers/download.ni-daqmx.html) for camera control and analog/digital outputs, respectively. In addition, it is necessary to install the below Python features:

Anaconda package (https://anaconda.org/anaconda/python)

PyQt5 (https://pypi.org/project/PyQt5/)

pyqtgraph (https://www.pyqtgraph.org/)

pymmcore (https://github.com/micro-manager/pymmcore)

ni-daqmx for Python (https://nidaqmx-python.readthedocs.io/)

h5py (https://www.h5py.org/)

CuPy (https://cupy.dev/)



