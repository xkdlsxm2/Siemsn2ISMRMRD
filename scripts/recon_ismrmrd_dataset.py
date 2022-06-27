# coding: utf-8

import os
import ismrmrd
import ismrmrd.xsd
import numpy as np

from ismrmrdtools import show, transform

# Load file
# filename = r"B:\Jinho\_temp\meas_MID00125_FID00360_liver_diff_b50_avg5_b800_avg20_tra_p2.h5"
filename = r"\\mr-fst27-02.wurmloch.siemens.de\MR-T27-01\Jinho\MRCP\Measurements\Data_collection\20220314_Volunteer_1\tmp\meas_MID00058_FID07833_t2_space_cor_cs23_bh_352_FoV380.h5"
# filename = r"C:\Users\z0048drc\Desktop\New folder\aa\meas_MID00017_FID05235_localizer2.h5"

if not os.path.isfile(filename):
    print("%s is not a valid file" % filename)
    raise SystemExit
dset = ismrmrd.Dataset(filename, 'dataset', create_if_needed=False)

header = ismrmrd.xsd.CreateFromDocument(dset.read_xml_header())
enc = header.encoding[0]

# Matrix size
eNx = enc.encodedSpace.matrixSize.x # <ParamLong."fullCol">{ 704 } in dat
eNy = enc.encodedSpace.matrixSize.y # <ParamLong."fullLin">{ 688 }
eNz = enc.encodedSpace.matrixSize.z
rNx = enc.reconSpace.matrixSize.x
rNy = enc.reconSpace.matrixSize.y
rNz = enc.reconSpace.matrixSize.z
# rNx = 240
# rNy = 240
# rNz = 1

# Field of View
eFOVx = enc.encodedSpace.fieldOfView_mm.x
eFOVy = enc.encodedSpace.fieldOfView_mm.y
eFOVz = enc.encodedSpace.fieldOfView_mm.z
rFOVx = enc.reconSpace.fieldOfView_mm.x
rFOVy = enc.reconSpace.fieldOfView_mm.y
rFOVz = enc.reconSpace.fieldOfView_mm.z

# Number of Slices, Reps, Contrasts, etc.
ncoils = header.acquisitionSystemInformation.receiverChannels
if enc.encodingLimits.slice != None:
    nslices = enc.encodingLimits.slice.maximum + 1
else:
    nslices = 1

if enc.encodingLimits.repetition != None:
    nreps = enc.encodingLimits.repetition.maximum + 1
else:
    nreps = 1

if enc.encodingLimits.contrast != None:
    ncontrasts = enc.encodingLimits.contrast.maximum + 1
else:
    ncontrasts = 1

# TODO loop through the acquisitions looking for noise scans
firstacq=0
for acqnum in range(dset.number_of_acquisitions()):
    acq = dset.read_acquisition(acqnum)
    
    # TODO: Currently ignoring noise scans
    if acq.isFlagSet(ismrmrd.ACQ_IS_NOISE_MEASUREMENT):
        print("Found noise scan at acq ", acqnum)
        continue
    else:
        firstacq = acqnum
        print("Imaging acquisition starts acq ", acqnum)
        break


# Initialiaze a storage array
all_data = np.zeros((nreps, ncontrasts, nslices, ncoils, eNz, eNy, eNx), dtype=np.complex64)

# Loop through the rest of the acquisitions and stuff
for acqnum in range(firstacq,dset.number_of_acquisitions()):
    acq = dset.read_acquisition(acqnum)

    # TODO: this is where we would apply noise pre-whitening

    # # Remove oversampling if needed
    # if eNx != rNx:
    #     xline = transform.transform_kspace_to_image(acq.data, [1])
    #     x0 = int((eNx - rNx) / 2)
    #     x1 = int((eNx - rNx) / 2 + rNx)
    #     xline = xline[:,x0:x1]
    #     acq.resize(rNx,acq.active_channels,acq.trajectory_dimensions)
    #     acq.center_sample = rNx//2
    #     # need to use the [:] notation here to fill the data
    #     acq.data[:] = transform.transform_image_to_kspace(xline, [1])
  
    # Stuff into the buffer
    rep = acq.idx.repetition
    contrast = acq.idx.contrast
    slice = acq.idx.slice
    y = acq.idx.kspace_encode_step_1
    z = acq.idx.kspace_encode_step_2
    try:
        all_data[rep, contrast, slice, :, z, y, :] = acq.data # 42 * 128
    except:
        pass

# Reconstruct images
images = np.zeros((nreps, ncontrasts, nslices, eNz, eNy, eNx), dtype=np.float32)
for rep in range(nreps):
    for contrast in range(ncontrasts):
        for slice in range(nslices):
            # FFT
            if eNz>1:
                #3D
                im = transform.transform_kspace_to_image(all_data[rep,contrast,slice,:,:,:,:], [1,2,3])
            else:
                #2D
                im = transform.transform_kspace_to_image(all_data[rep,contrast,slice,:,0,:,:], [1,2])

            # Sum of squares
            im = np.sqrt(np.sum(np.abs(im) ** 2, 0))
            
            # Stuff into the output
            if eNz>1:
                #3D
                images[rep,contrast,slice,:,:,:] = im
            else:
                #2D
                images[rep,contrast,slice,0,:,:] = im

# Show an image
show.imshow(np.squeeze(images[0,0,0,:,:,:]), cmap='gray')
show.imshow(np.squeeze(images[0,0,1,:,:,:]), cmap='gray')
show.imshow(np.squeeze(images[0,0,2,:,:,:]), cmap='gray')
