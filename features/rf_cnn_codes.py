from learning.retina_net import RetiNet
from sklearn.ensemble import RandomForestClassifier
from sklearn.externals import joblib
from utils.metrics import calculate_metrics
import numpy as np
from os.path import join
from tsne import tsne
import matplotlib.pyplot as plt

LABELS = {0: 'No', 1: 'Plus', 2: 'Pre-Plus'}


def main(model_conf, train_data, test_data, out_dir):

    # Load model and set last layer
    print "Loading model..."
    net = RetiNet(model_conf)
    net.set_intermediate('flatten_3')

    # Get CNN codes
    print "Getting features..."
    train_codes = net.predict(train_data)

    # Create random forest
    rf = RandomForestClassifier(n_estimators=100, class_weight='balanced_subsample')
    X_train = train_codes['probabilities']
    y_train = np.asarray(train_codes['y_true'])

    print "Training RF..."
    rf.fit(X_train, y_train)

    joblib.dump(rf, join(out_dir, 'rf.pkl'))

    # Load test data
    test_codes = net.predict(test_data)
    X_test = test_codes['probabilities']

    # Predict
    print "Getting predictions..."
    y_pred = rf.predict(X_test)
    calculate_metrics(test_codes, out_dir, y_pred=y_pred)

    # T-SNE embedding
    print "T-SNE visualisation of training features"
    np.save(join(out_dir, 'cnn_train_features.npy'), X_train)
    make_tsne(X_train, y_train, out_dir)


def make_tsne(X, y, out_dir):

    T = tsne(X, 2, 50, 20.0)
    fig, ax = plt.subplots()
    ax.scatter(T[y == 0, 0], T[y == 0, 1], 20, label=LABELS[0], alpha=0.6)
    ax.scatter(T[y == 1, 0], T[y == 1, 1], 20, label=LABELS[1], alpha=0.6)
    ax.scatter(T[y == 2, 0], T[y == 2, 1], 20, label=LABELS[2], alpha=0.6)
    ax.legend()
    plt.savefig(join(out_dir, 'tsne.png'))


if __name__ == '__main__':

    from argparse import ArgumentParser
    parser = ArgumentParser()

    parser.add_argument('-c', '--config', dest='model_config', help="YAML file for model to test", required=True)
    parser.add_argument('-tr', '--train', dest='training_data', help="HDF5 file for training data", required=True)
    parser.add_argument('-te', '--test', dest='test_data', help="HDF5 file for test data", required=True)
    parser.add_argument('-o', '--out-dir', dest='out_dir', help="Output directory for results", required=True)


    args = parser.parse_args()
    main(args.model_config, args.training_data, args.test_data, args.out_dir)
