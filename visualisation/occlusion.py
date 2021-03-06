import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from os.path import join, isfile
import cv2
import numpy as np
from learning.retina_net import RetiNet
from utils.common import find_images_by_class, make_sub_dir

CLASSES = {0: 'No', 1: 'Plus', 2: 'Pre-Plus'}


def occlusion_heatmaps(model_config, test_data, out_dir, no_imgs=None, window_size=12):

    # Load model
    model = RetiNet(model_config).model
    imgs_by_class = find_images_by_class(test_data)

    for class_, img_list in imgs_by_class.items():

        class_dir = make_sub_dir(out_dir, class_)

        no_imgs = len(img_list) if no_imgs is None else int(no_imgs)
        img_arr = []

        for img_path in img_list[:no_imgs]:  # TODO use full set, just one test img for now

            # Load and prepare image
            img = cv2.imread(img_path)
            img = img.transpose((2, 0, 1))
            img_arr.append(img)

        # Create single array of inputs
        img_arr = np.stack(img_arr, axis=0)
        print img_arr.shape

        # Get raw predictions
        raw_probabilities = model.predict_on_batch(img_arr)
        raw_predictions = [np.argmax(y_pred) for y_pred in raw_probabilities]

        # Occlude overlapping windows in the image
        x_dim = img_arr.shape[2]
        y_dim = img_arr.shape[3]
        hw = window_size / 2

        hmaps_out = join(class_dir, 'heatmaps.npy')

        if not isfile(hmaps_out):

            heatmaps = np.zeros(shape=(no_imgs, x_dim, y_dim))

            for x in range(0, x_dim):
                for y in range(0, y_dim):

                    x_range = np.clip(np.arange(x-hw, x+hw), 0, x_dim-1)
                    y_range = np.clip(np.arange(y-hw, y+hw), 0, y_dim-1)
                    img_arr[:, :, x_range, y_range] = 0

                    # Get predictions for current occluded region
                    occ_probabilites = model.predict_on_batch(img_arr)

                    # Assign heatmap value as probability of class, as predicted without occlusion
                    for i, occ_prob, raw_pred in enumerate(zip(occ_probabilites, raw_predictions)):
                        heatmaps[i, x, y] = occ_prob[raw_pred]

            np.save(hmaps_out, heatmaps)

        else:
            heatmaps = np.load(hmaps_out)

        plot_heatmaps(img_arr, heatmaps, class_dir)


def plot_heatmaps(img_arr, heatmaps, out_dir):
    for j, (img, h_map) in enumerate(zip(img_arr, heatmaps)):
        f = plt.figure()

        img = np.transpose(img, (1, 2, 0))
        plt.imshow(img, cmap='gray')
        plt.imshow(h_map, cmap=plt.cm.viridis, alpha=0.7, interpolation='bilinear')
        plt.savefig(join(out_dir, '{}.png'.format(j)))

if __name__ == '__main__':

    from argparse import ArgumentParser
    parser = ArgumentParser()

    parser.add_argument('-m', '--model-config', dest='model_config', help='Model config (YAML) file', required=True)
    parser.add_argument('-t', '--test-data', dest='test_data', help='Test data', required=True)
    parser.add_argument('-w', '--window-size', dest='window_size', help='Size of occluded patch', default=12)
    parser.add_argument('-n', '--no-imgs', dest='no_imgs', help='Number of images to test with', default=None)
    parser.add_argument('-o', '--out-dir', dest='out_dir', help='Output directory', required=True)

    args = parser.parse_args()

    occlusion_heatmaps(args.model_config, args.test_data, args.out_dir, no_imgs=args.no_imgs, window_size=args.window_size)
