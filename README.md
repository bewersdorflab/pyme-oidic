# pyme-oidic
Microscope controls and reconstruction algorithms for OIDIC microscopy. This is designed to work with
the instrument described in

M. Shribak, K. G. Larkin, and D. Biggs, “Mapping optical path length and image enhancement using quantitative orientation-independent differential interference contrast microscopy,” J. Biomed. Opt., vol. 22, no. 1, p. 016006, 2017.

## Requirements
1. `python-microscopy`
2. `xlrd` (needed to read xls liquid crystal calibration files)
## Installation

1. Clone the repository. 
2. `cd pyme-oidic`
3. `python setup.py develop`
4. Add the path to your liquid crystal calibration file under 
   `lc_cal_file` in `~/.PYME/config.yaml`.
5. Modify `init_oidic.py` to point to the correct COM ports/devices on your
   computer and copy to `~/.PYME/init_scripts`.

## Usage
`pymeacquire -i init_oidic.py`
