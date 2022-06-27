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
    r"C:\Users\z0048drc\Desktop\data_fm\MRCP\phantom")
# filename = pathlib.Path("meas_MID00059_FID01994_t2_space_cor_p3_trig_384_iso.h5")
filenames = [pathlib.Path(i) for i in os.listdir(filepath) if '.h5' in i]
savepath = pathlib.Path(r'C:\Users\z0048drc\Desktop\data_fm\MRCP\phantom\processed')

headerDict = defaultdict(list)

for filename in filenames:
    h5path = filepath / filename
    if not os.path.isfile(h5path):
        print("%s is not a valid file" % h5path)
        raise SystemExit
    dset = ismrmrd.Dataset(h5path, 'dataset', create_if_needed=False)

    header = ismrmrd.xsd.CreateFromDocument(dset.read_xml_header())
    enc = header.encoding[0]

    headerDict['fname'].append(filename.stem)
    headerDict['encodingLimit_y'].append(enc.encodingLimits.kspace_encoding_step_1)
    headerDict['encodingLimit_z'].append(enc.encodingLimits.kspace_encoding_step_2)
    headerDict['encodingSpace_matrix'].append(enc.encodedSpace.matrixSize)
    headerDict['encodingSpace_FoV'].append(enc.encodedSpace.fieldOfView_mm)
    headerDict['ReconSpace_FoV'].append(enc.reconSpace.fieldOfView_mm)
    headerDict['Number_of_acquisition'].append(dset.number_of_acquisitions())


for key, value in headerDict.items():
    print(f"{key}: {value}")

import pandas as pd

df = pd.DataFrame(headerDict)
df.to_csv("header.csv", index=False)