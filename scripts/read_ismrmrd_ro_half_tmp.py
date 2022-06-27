import os
import ismrmrd
import ismrmrd.xsd
import numpy as np
from collections import defaultdict
import utils
import h5py
import pathlib
from tqdm import tqdm
from ismrmrdtools import show, transform

filepath = pathlib.Path(
    r"B:\Jinho\MRCP\Measurements\Data_collection\20220314_Volunteer_1\meas_MID00062_FID07837_t2_space_cor_p3_trig_384_iso")
filename = pathlib.Path("meas_MID00062_FID07837_t2_space_cor_p3_trig_384_iso.h5")
h5path = filepath / filename
savepath = pathlib.Path(r'C:\Users\z0048drc\Desktop\data_fm\MRCP')
savename = pathlib.Path("meas_MID00062_FID07837_t2_space_cor_p3_trig_384_iso-RO_half.h5")

if not os.path.isfile(h5path):
    print("%s is not a valid file" % h5path)
    raise SystemExit
dset = ismrmrd.Dataset(h5path, 'dataset', create_if_needed=False)

header = ismrmrd.xsd.CreateFromDocument(dset.read_xml_header())
enc = header.encoding[0]
ncoils = header.acquisitionSystemInformation.receiverChannels
kx = enc.encodedSpace.matrixSize.x if utils.is_readout_os(header) else enc.encodedSpace.matrixSize.x // 2
ky = enc.encodingLimits.kspace_encoding_step_1.maximum + 1
kz = enc.encodingLimits.kspace_encoding_step_2.maximum + 1
y_pad = utils.pad(enc.encodingLimits.kspace_encoding_step_1)
z_pad = utils.pad(enc.encodingLimits.kspace_encoding_step_2)

meta = dict()
for k in ['ncoils', 'kx', 'ky', 'kz', 'y_pad', 'z_pad']:
    meta[k] = locals()[k]


h5f = h5py.File(savepath / savename, 'r')
all_data = h5f['kspace'][:]
h5f.close()

all_data_center = np.zeros((ncoils, kx, ky+y_pad, kz+z_pad)).astype(complex)
all_data_center[:, :, y_pad:, z_pad:] = all_data

all_data_z = transform.transform_kspace_to_image(all_data_center, [3])
h5f = h5py.File(savepath / f"{savename.stem}_center_FTz{savename.suffix}", 'w')
h5f.create_dataset('kspace', data=all_data_z)
for k in meta.keys():
    h5f.attrs[k] = meta[k]
h5f.close()

# todo: ky and kz => automatically calcauation using parameters.

