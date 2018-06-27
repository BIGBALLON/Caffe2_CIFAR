#!/usr/bin/env python
# -*- coding:utf-8 -*-  

import os
import sys
import time
import pickle
import random
import numpy as np

CLASS_NUM      = 10
IMAGE_SIZE     = 32
IMG_CHANNELS   = 3

def next_batch(batch_size, data, labels):
    idx = np.arange(0 , len(data))
    np.random.shuffle(idx)
    idx = idx[:batch_size]
    data_shuffle = data[idx]
    labels_shuffle = labels[idx]
    labels_shuffle = np.asarray(labels_shuffle).reshape([-1])
    return np.array(data_shuffle, dtype='float32'), np.array(labels_shuffle, dtype='int32')

def try_to_download():
    dirname  = 'cifar-10-batches-py'
    origin   = 'http://www.cs.toronto.edu/~kriz/cifar-10-python.tar.gz'
    fname    = 'cifar-10-python.tar.gz'
    fpath    = './' + dirname

    download = True
    if os.path.exists(fpath) or os.path.isfile(fname):
        download = False
        print("DataSet aready exist!")
    if download:
        print('Downloading data from', origin)
        import urllib.request
        import tarfile

        def reporthook(count, block_size, total_size):
            global start_time
            if count == 0:
                start_time = time.time()
                return
            duration = time.time() - start_time
            progress_size = int(count * block_size)
            speed = int(progress_size / (1024 * duration))
            percent = min(int(count*block_size*100/total_size),100)
            sys.stdout.write("\r...%d%%, %d MB, %d KB/s, %d seconds passed" %
                            (percent, progress_size / (1024 * 1024), speed, duration))
            sys.stdout.flush()

        urllib.request.urlretrieve(origin, fname, reporthook)
        print('Download finished. Start extract!', origin)
        if (fname.endswith("tar.gz")):
            tar = tarfile.open(fname, "r:gz")
            tar.extractall()
            tar.close()
        elif (fname.endswith("tar")):
            tar = tarfile.open(fname, "r:")
            tar.extractall()
            tar.close()

def unpickle(file):
    with open(file, 'rb') as fo:
        dict = pickle.load(fo, encoding='bytes')
    return dict

def load_data_one(file):
    batch  = unpickle(file)
    data   = batch[b'data']
    labels = batch[b'labels']
    print("Loading %s : %d." %(file, len(data)))
    return data, labels

def load_data(files, data_dir, label_count):
    global IMAGE_SIZE, IMG_CHANNELS
    data, labels = load_data_one(data_dir + '/' + files[0])
    for f in files[1:]:
        data_n, labels_n = load_data_one(data_dir + '/' + f)
        data = np.append(data,data_n,axis=0)
        labels = np.append(labels,labels_n,axis=0)
    # NCHW 
    data = data.reshape([-1,IMG_CHANNELS, IMAGE_SIZE, IMAGE_SIZE])
    labels = np.asarray(labels).astype('int32')
    # BGR
    data = data[:, (2, 1, 0), :, :]
    return data, labels

def prepare_data():
    print("======Loading data======")
    try_to_download()
    data_dir = './cifar-10-batches-py'
    image_dim = IMAGE_SIZE * IMAGE_SIZE * IMG_CHANNELS
    meta = unpickle( data_dir + '/batches.meta')

    label_names = meta[b'label_names']
    label_count = len(label_names)
    train_files = [ 'data_batch_%d' % d for d in range(1,6) ]
    train_data, train_labels = load_data(train_files, data_dir, label_count)
    test_data, test_labels = load_data([ 'test_batch' ], data_dir, label_count)

    print("Train data:",np.shape(train_data), np.shape(train_labels))
    print("Test data :",np.shape(test_data), np.shape(test_labels))
    print("======Load finished======")

    print("======Shuffling data======")
    indices = np.random.permutation(len(train_data))
    train_data = train_data[indices]
    train_labels = train_labels[indices]
    print("======Prepare Finished======")

    return train_data, train_labels, test_data, test_labels

def _random_crop(batch, crop_shape, padding=None):
        oshape = np.shape(batch[0])
        
        if padding:
            oshape = (oshape[1] + 2*padding, oshape[2] + 2*padding)
        new_batch = []
        npad = ((padding, padding), (padding, padding), (0, 0))
        for i in range(len(batch)):
            new_batch.append(batch[i])
            if padding:
                new_batch[i] = np.lib.pad(batch[i], pad_width=npad,
                                          mode='constant', constant_values=0)
            nh = random.randint(0, oshape[0] - crop_shape[0])
            nw = random.randint(0, oshape[1] - crop_shape[1])
            new_batch[i] = new_batch[i][nh:nh + crop_shape[0],
                                        nw:nw + crop_shape[1]]
        return new_batch

def _random_flip_leftright(batch):
        for i in range(batch.shape[0]):
            if bool(random.getrandbits(1)):
                batch[i] = np.fliplr(batch[i])
        return batch

def color_preprocessing(x_train,x_test):
    x_train = x_train.astype('float32')
    x_test = x_test.astype('float32')
    # BGR 
    mean = [113.865, 122.95, 125.307]
    std  = [66.7048, 62.0887, 62.9932]
    for i in range(3):
        x_train[:,i,:,:] = (x_train[:,i,:,:] - mean[i]) / std[i]
        x_test[:,i,:,:]  = (x_test[:,i,:,:]  - mean[i]) / std[i]
    return x_train, x_test

def data_augmentation(batch):
    batch = _random_flip_leftright(batch)
    batch = _random_crop(batch, [IMAGE_SIZE,IMAGE_SIZE], 4)
