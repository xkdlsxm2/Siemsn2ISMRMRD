from collections import Counter
import matplotlib.pyplot as plt
import numpy as np


def coordinate_separate(coord):
    coord_sep = dict()
    for k, v, in coord.items():
        single = list(set(v))
        dupl = [k for k, v in Counter(v).items() if v > 1]
        for i in dupl:
            single.remove(i)
        coord_sep[k] = [single, dupl]

    return coord_sep


def plot_coord(coord_sep):
    kz_list = np.array(list(coord_sep.keys())).astype(int)
    ky_single = np.array([i[0] for i in coord_sep.values()])
    ky_dupl = np.array([i[1] for i in coord_sep.values()])

    dot_size = 5
    for idx, kz in enumerate(kz_list):
        kzz = [kz] * len(ky_single[idx])
        plt.scatter(ky_single[idx], kzz, color='black', s=dot_size)
        kzz = [kz] * len(ky_dupl[idx])
        plt.scatter(ky_dupl[idx], kzz, color='red', marker='x', s=dot_size)

    plt.xlabel("ky")
    plt.ylabel("kz")
    plt.show()


def is_readout_os(header):
    return header.encoding[0].encodedSpace.fieldOfView_mm.x == header.encoding[0].reconSpace.fieldOfView_mm.x

def pad(encoding):
    max = encoding.maximum
    center = encoding.center

    max_center = max/2
    pad = abs(max_center - center) * 2
    pad = pad if pad % 2 == 0 else pad + 1
    pad = pad + 1 if max % 2 == 0 else pad
    return int(pad)

#
# def save_header(header):
#     from collections import defaultdict
#
#     ismrmrd_header = defaultdict()
#     ismrmrd_header['acquisitionSystemInformation']['deviceID'] = header.acquisitionSystemInformation.deviceID
#     ismrmrd_header['acquisitionSystemInformation']['receiverChannels'] =header.acquisitionSystemInformation.receiverChannels
#     ismrmrd_header['acquisitionSystemInformation']['FieldStrength_T'] = header.acquisitionSystemInformation.systemFieldStrength_T
#     ismrmrd_header['acquisitionSystemInformation']['Scanner'] = header.acquisitionSystemInformation.systemModel
#
#     ismrmrd_header['measurementInformation']['protocolName'] = header.measurementInformation.protocolName
#
#     ismrmrd_header['sequenceParameters']['TE'] = header.sequenceParameters.TE
#     ismrmrd_header['sequenceParameters']['TI'] = header.sequenceParameters.TI
#     ismrmrd_header['sequenceParameters']['TR'] = header.sequenceParameters.TR
#     ismrmrd_header['sequenceParameters']['echo_spacing'] = header.sequenceParameters.echo_spacing
#     ismrmrd_header['sequenceParameters']['flipAngle_deg'] = header.sequenceParameters.flipAngle_deg
#     ismrmrd_header['sequenceParameters']['sequence_type'] = header.sequenceParameters.sequence_type
#
#     return ismrmrd_header