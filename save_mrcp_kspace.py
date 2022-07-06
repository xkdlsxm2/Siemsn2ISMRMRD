import h5py, pathlib
import matplotlib.pyplot as plt
import matplotlib.colors as colors
import os

DPATH = pathlib.Path(r"X:\data\mrcp\data")
SAVEPATH = pathlib.Path(r"C:\Users\z0048drc\Desktop\CS_recon\Results\DGX\kspace\PF_x")
fnames = [pathlib.Path(i) for i in os.listdir(DPATH) if '' in i]

for fname in fnames:
    PATH = SAVEPATH / fname.stem
    with h5py.File(DPATH / fname, "r") as hf:
        kspace = hf["kspace"][:]
    for dataslice in range(kspace.shape[-1]):
        PATH.mkdir(exist_ok=True, parents=True)
        filename = PATH / f'mrcp_kspace_{dataslice}.png'
        plt.imshow(abs(kspace[10,:,:,dataslice]), cmap='gray', norm=colors.PowerNorm(gamma=0.3))
        plt.axis('off')
        figure = plt.gcf()  # get current figure
        figure.set_size_inches(28, 14)
        plt.savefig(filename, bbox_inches='tight', pad_inches=0)
        plt.close()
