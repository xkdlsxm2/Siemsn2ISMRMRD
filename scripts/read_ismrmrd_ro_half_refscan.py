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

meta = dict()
for k in ['ncoils', 'kx', 'ky', 'kz']:
    meta[k] = locals()[k]

dupl_check = np.zeros((ky, kz)).astype(int)
dupl_check_ref = np.zeros((ky, kz)).astype(int)
coord = defaultdict(list)
all_data = np.zeros((ncoils, kx, ky, kz), dtype=np.complex64)  # (ncoil,x,y,z)
ref_scan = np.zeros((ncoils, kx, ky, kz), dtype=np.complex64)  # (ncoil,x,y,z)

for acqnum in tqdm(range(dset.number_of_acquisitions())):
    acq = dset.read_acquisition(acqnum)

    if acq.isFlagSet(ismrmrd.ACQ_IS_NOISE_MEASUREMENT) \
            or acq.isFlagSet(ismrmrd.ACQ_IS_RTFEEDBACK_DATA):
        # Noise scan / navigator / refscan => skip
        continue
    elif acq.isFlagSet(ismrmrd.ACQ_IS_PARALLEL_CALIBRATION):
        y = acq.idx.kspace_encode_step_1
        z = acq.idx.kspace_encode_step_2

        if y < ky and z < kz:
            coord[str(z)].append(y)
            dupl_check_ref[y, z] += 1

            xline = transform.transform_kspace_to_image(acq.data, [1])
            x0 = int(acq.data.shape[1] * 0.25)
            x1 = int(acq.data.shape[1] * 0.75)
            xline = xline[:, x0:x1]
            ref_scan[:, :, y, z] += transform.transform_image_to_kspace(xline, [1])
            ref_scan[:, :, y, z] /= dupl_check_ref[y, z]
    else:
        y = acq.idx.kspace_encode_step_1
        z = acq.idx.kspace_encode_step_2

        if y < ky and z < kz:
            coord[str(z)].append(y)
            dupl_check[y, z] += 1

            xline = transform.transform_kspace_to_image(acq.data, [1])
            x0 = int(acq.data.shape[1] * 0.25)
            x1 = int(acq.data.shape[1] * 0.75)
            xline = xline[:, x0:x1]
            all_data[:, :, y, z] += transform.transform_image_to_kspace(xline, [1])
            all_data[:, :, y, z] /= dupl_check[y, z]

h5f = h5py.File(savepath / savename, 'w')
h5f.create_dataset('kspace', data=all_data)
h5f.close()

all_data = transform.transform_kspace_to_image(all_data, [3])
h5f = h5py.File(savepath / f"{savename.stem}_FTz{savename.suffix}", 'w')
h5f.create_dataset('kspace', data=all_data)
h5f.close()

# todo: ky and kz => automatically calcauation using parameters.
all_data_center = np.zeros((42, 384, 481, 57)).astype(complex)
all_data_center[:, :, 103:, 6:] = all_data
h5f = h5py.File(savepath / f"{savename.stem}_FTz_center{savename.suffix}", 'w')
h5f.create_dataset('kspace', data=all_data_center)
h5f.close()
