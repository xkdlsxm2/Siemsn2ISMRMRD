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

filepath = pathlib.Path(r"B:\Jinho\MRCP\Measurements\Data_collection\20220314_Volunteer_1\meas_MID00062_FID07837_t2_space_cor_p3_trig_384_iso")
filename = pathlib.Path("meas_MID00062_FID07837_t2_space_cor_p3_trig_384_iso.h5")
h5path = filepath / filename
savepath = pathlib.Path(r'C:\Users\z0048drc\Desktop\data_fm\MRCP')

if not os.path.isfile(h5path):
    print("%s is not a valid file" % h5path)
    raise SystemExit
dset = ismrmrd.Dataset(h5path, 'dataset', create_if_needed=False)

header = ismrmrd.xsd.CreateFromDocument(dset.read_xml_header())
enc = header.encoding[0]
ncoils = header.acquisitionSystemInformation.receiverChannels
lines = enc.encodingLimits.kspace_encoding_step_1.maximum + 1
partitions = enc.encodingLimits.kspace_encoding_step_2.maximum + 1
read_out = enc.encodedSpace.matrixSize.x

dupl_check = np.zeros((lines, partitions)).astype(int)
coord = defaultdict(list)
all_data = np.zeros((ncoils, read_out, lines, partitions), dtype=np.complex64)  # (ncoil,x,y,z)

for acqnum in tqdm(range(dset.number_of_acquisitions())):
    acq = dset.read_acquisition(acqnum)

    if acq.isFlagSet(ismrmrd.ACQ_IS_NOISE_MEASUREMENT) \
            or acq.isFlagSet(ismrmrd.ACQ_IS_RTFEEDBACK_DATA) \
            or acq.isFlagSet(ismrmrd.ACQ_IS_PARALLEL_CALIBRATION):
        # Noise scan / navigator / refscan => skip
        continue
    else:
        y = acq.idx.kspace_encode_step_1
        z = acq.idx.kspace_encode_step_2

        if y < lines and z < partitions:
            coord[str(z)].append(y)
            dupl_check[y, z] += 1
            all_data[:, :, y, z] += acq.data
            all_data[:, :, y, z] /= dupl_check[y, z]

coord_sep = utils.coordinate_separate(coord)
h5f = h5py.File(savepath / filename, 'w')
h5f.create_dataset('kspace', data=all_data)
h5f.close()
