from skimage import measure
from skimage.color import rgb2gray
from skimage.filters import threshold_otsu
from PIL import Image
import numpy as np
from os.path import split, join, splitext


def create_mask(im_arr):

    if im_arr.shape[2] == 3:
        im_arr = rgb2gray(im_arr)

    thresh = threshold_otsu(im_arr)
    inv_bin = np.invert(im_arr > thresh)
    all_labels = measure.label(inv_bin)

    seg_arr = np.invert(all_labels == 1).astype(np.uint8)
    return seg_arr


if __name__ == "__main__":

    import sys

    im_path = sys.argv[1]
    im = np.asarray(Image.open(im_path))
    seg = create_mask(im) * 255

    dir_name, file_name = split(im_path)
    name, ext = splitext(file_name)

    Image.fromarray(seg).save(join(dir_name, name + '_seg' + ext))