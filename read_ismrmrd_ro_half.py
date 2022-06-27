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

filepath = pathlib.Path(r"C:\Users\z0048drc\Desktop\data_fm\MRCP\extracted")
# filename = pathlib.Path("meas_MID00059_FID01994_t2_space_cor_p3_trig_384_iso.h5")
filenames = [pathlib.Path(i) for i in os.listdir(filepath) if 'meas_MID00052_FID02811_t2_space_cor_p3_trig_384_iso.h5' in i]
savepath = pathlib.Path(r'X:\data\mrcp\data')

for filename in filenames:
    h5path = filepath / filename
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

    dupl_check = np.zeros((ky, kz)).astype(int)
    coord = defaultdict(list)
    all_data = np.zeros((ncoils, kx, ky, kz), dtype=np.complex64)  # (ncoil,x,y,z)
    ref_min_idx, ref_max_idx = 99999, -1

    for acqnum in tqdm(range(dset.number_of_acquisitions())):
        acq = dset.read_acquisition(acqnum)

        if acq.isFlagSet(ismrmrd.ACQ_IS_NOISE_MEASUREMENT) \
                or acq.isFlagSet(ismrmrd.ACQ_IS_RTFEEDBACK_DATA) \
                or acq.data.size == 0:
            '''Noise scan / navigator => skip'''
            continue
        else:
            '''ref_scan (ismrmrd.ACQ_IS_PARALLEL_CALIBRATION) & kdata acquisition'''
            y = acq.idx.kspace_encode_step_1
            z = acq.idx.kspace_encode_step_2

            if y < ky and z < kz:
                coord[str(z)].append(y)
                dupl_check[y, z] += 1
                if acq.isFlagSet(ismrmrd.ACQ_IS_PARALLEL_CALIBRATION):
                    ref_max_idx = y if y > ref_max_idx else ref_max_idx
                    ref_min_idx = y if y <= ref_min_idx else ref_min_idx

                # Readout undersample by a factor of 2
                xline = transform.transform_kspace_to_image(acq.data, [1])
                x0 = int(acq.data.shape[1] * 0.25)
                x1 = int(acq.data.shape[1] * 0.75)
                xline = xline[:, x0:x1]
                all_data[:, :, y, z] += transform.transform_image_to_kspace(xline, [1])

    dupl_check = np.where(dupl_check == 0, 1, dupl_check)  # replace 0 to 1 to divide with.
    all_data[:, :] /= dupl_check

    num_low_freq = ref_max_idx - ref_min_idx + 1
    meta = dict()
    for k in ['ncoils', 'kx', 'ky', 'kz', 'y_pad', 'z_pad', 'num_low_freq']:
        meta[k] = locals()[k]

    # h5f = h5py.File(savepath / savename, 'w')
    # h5f.create_dataset('kspace', data=all_data)
    # h5f.close()

    all_data_center = np.zeros((ncoils, kx, ky + y_pad, kz + z_pad)).astype(complex)
    all_data_center[:, :, y_pad:, z_pad:] = all_data

    all_data_z = transform.transform_kspace_to_image(all_data_center, [3])
    h5f = h5py.File(savepath / f"{'_'.join(filename.stem.split('_')[1:3])}{filename.suffix}", 'w')
    h5f.create_dataset('kspace', data=all_data_z)
    for k in meta.keys():
        h5f.attrs[k] = meta[k]
    h5f.close()
