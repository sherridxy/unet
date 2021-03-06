...
Lab3 Improve the accuracy of Lab2
Tips:
Try to change the training parameters: learning rate, epoch, batch size, etc.
Try to augment the image samples using the last example of https://keras.io/preprocessing/image/#imagedatagenerator
Try to replace the uppooling layer with deconvolution layer (ref. https://github.com/k3nt0w/FCN_via_keras )
Try to increase receptive fields by replace convolution2D with AtrousConvolution2D (is it same as reduce running resolution?)
Transfer learning

from data import create_train_data, create_test_data
create_train_data()
create_test_data()

from __future__ import print_function

from scipy import misc
import numpy as np
from keras.models import Model
from keras.layers import Input, merge, Convolution2D, MaxPooling2D, UpSampling2D, AtrousConvolution2D
from keras.optimizers import Adam
from keras.callbacks import ModelCheckpoint, LearningRateScheduler
from keras import backend as K
import os

from data import load_train_data, load_test_data

K.set_image_dim_ordering('th')  # Theano dimension ordering in this code

original_img_rows = 1024
original_img_cols = 1024
running_img_rows = 256
running_img_cols = 256

print('1')


smooth = 1.


def dice_coef(y_true, y_pred):
    y_true_f = K.flatten(y_true)
    y_pred_f = K.flatten(y_pred)
    intersection = K.sum(y_true_f * y_pred_f)
    return (2. * intersection + smooth) / (K.sum(y_true_f) + K.sum(y_pred_f) + smooth)


def dice_coef_loss(y_true, y_pred):
    return -dice_coef(y_true, y_pred)

print('11111')


def get_unet():
    inputs = Input((1, running_img_rows, running_img_cols))
    conv1 = AtrousConvolution2D(32, 3, 3, activation='relu', border_mode='same')(inputs)
    conv1 = AtrousConvolution2D(32, 3, 3, activation='relu', border_mode='same')(conv1)
    pool1 = MaxPooling2D(pool_size=(2, 2))(conv1)

    conv2 = AtrousConvolution2D(64, 3, 3, activation='relu', border_mode='same')(pool1)
    conv2 = AtrousConvolution2D(64, 3, 3, activation='relu', border_mode='same')(conv2)
    pool2 = MaxPooling2D(pool_size=(2, 2))(conv2)

    conv3 = AtrousConvolution2D(128, 3, 3, activation='relu', border_mode='same')(pool2)
    conv3 = AtrousConvolution2D(128, 3, 3, activation='relu', border_mode='same')(conv3)
    pool3 = MaxPooling2D(pool_size=(2, 2))(conv3)

    conv4 = AtrousConvolution2D(256, 3, 3, activation='relu', border_mode='same')(pool3)
    conv4 = AtrousConvolution2D(256, 3, 3, activation='relu', border_mode='same')(conv4)
    pool4 = MaxPooling2D(pool_size=(2, 2))(conv4)

    conv5 = AtrousConvolution2D(512, 3, 3, activation='relu', border_mode='same')(pool4)
    conv5 = AtrousConvolution2D(512, 3, 3, activation='relu', border_mode='same')(conv5)

    up6 = merge([UpSampling2D(size=(2, 2))(conv5), conv4], mode='concat', concat_axis=1)
    conv6 = AtrousConvolution2D(256, 3, 3, activation='relu', border_mode='same')(up6)
    conv6 = AtrousConvolution2D(256, 3, 3, activation='relu', border_mode='same')(conv6)

    up7 = merge([UpSampling2D(size=(2, 2))(conv6), conv3], mode='concat', concat_axis=1)
    conv7 = AtrousConvolution2D(128, 3, 3, activation='relu', border_mode='same')(up7)
    conv7 = AtrousConvolution2D(128, 3, 3, activation='relu', border_mode='same')(conv7)

    up8 = merge([UpSampling2D(size=(2, 2))(conv7), conv2], mode='concat', concat_axis=1)
    conv8 = AtrousConvolution2D(64, 3, 3, activation='relu', border_mode='same')(up8)
    conv8 = AtrousConvolution2D(64, 3, 3, activation='relu', border_mode='same')(conv8)

    up9 = merge([UpSampling2D(size=(2, 2))(conv8), conv1], mode='concat', concat_axis=1)
    conv9 = AtrousConvolution2D(32, 3, 3, activation='relu', border_mode='same')(up9)
    conv9 = AtrousConvolution2D(32, 3, 3, activation='relu', border_mode='same')(conv9)

    conv10 =AtrousConvolution2D(1, 1, 1, activation='sigmoid')(conv9)

    model = Model(input=inputs, output=conv10)
#改变learningrate原来是e-5,原定值最好。
    model.compile(optimizer=Adam(lr=1e-5), loss=dice_coef_loss, metrics=[dice_coef])

    return model


print('11111')

def preprocess(imgs):
    imgs_p = np.ndarray((imgs.shape[0], imgs.shape[1], running_img_rows, running_img_cols), dtype=np.uint8)
    for i in range(imgs.shape[0]):
        imgs_p[i, 0] = misc.imresize(imgs[i, 0], (running_img_rows, running_img_cols), 'cubic')
    return imgs_p

print('11111')

def postprocess(imgs):
    imgs_p = np.ndarray((imgs.shape[0], imgs.shape[1], original_img_rows, original_img_cols), dtype=np.float)
    for i in range(imgs.shape[0]):
        imgs_p[i, 0] = misc.imresize(imgs[i, 0], (original_img_rows, original_img_cols), 'cubic')
    return imgs_p
print('11111')

print('-'*30)
print('Loading and preprocessing train data...')
print('-'*30)
imgs_train, imgs_mask_train = load_train_data()

imgs_train = preprocess(imgs_train)
imgs_mask_train = preprocess(imgs_mask_train)

imgs_train = imgs_train.astype('float32')
mean = np.mean(imgs_train)  # mean for data centering
std = np.std(imgs_train)  # std for data normalization

imgs_train -= mean
imgs_train /= std

imgs_mask_train = imgs_mask_train.astype('float32')
imgs_mask_train /= 255.  # scale masks to [0, 1]

print(imgs_train.shape)



print('11111')


def schedule(epoch):
    lrate = 1
    inc= 2
    lr=float(lrate/inc*(epoch+1))
    return lr
    
print('-'*30)
print('Creating and compiling model...')
print('-'*30)
model = get_unet()
model_checkpoint = ModelCheckpoint('unet.hdf5', monitor='loss', save_best_only=True)
#from numpy import math
#def schedule(epoch):
 #   initial_lrate  = 1
#  drop = 0.5
#    epochs_drop = 10
 #   lrate = initial_lrate * math.pow(drop, math.floor((1+epoch)/epochs_drop))
#  return lrate




model_learningrt = LearningRateScheduler(schedule)


print('-'*30)
print('Fitting model...')
print('-'*30)

model.fit(imgs_train, imgs_mask_train, batch_size=1, nb_epoch=35,verbose=1, shuffle=True,
          callbacks=[model_checkpoint])
print('11111')

print('-'*30)
print('Loading and preprocessing test data...')
print('-'*30)
imgs_test, imgs_mask_test_truth = load_test_data()
imgs_test = preprocess(imgs_test)

imgs_test = imgs_test.astype('float32')
imgs_test -= mean
imgs_test /= std

print('-'*30)
print('Loading saved weights...')
print('-'*30)
model.load_weights('unet.hdf5')

print('-'*30)
print('Predicting masks on test data...')
print('-'*30)
imgs_mask_test_result = model.predict(imgs_test, verbose=1)
print(imgs_mask_test_result.max())
print('11')

imgs_mask_test_result = postprocess(imgs_mask_test_result)
#test results is converted to 0-255 due to resizing
print(imgs_mask_test_result.max())

imgs_mask_test_result = imgs_mask_test_result.astype('float32')
imgs_mask_test_result /= 255
print(imgs_mask_test_truth.shape)



imgs_mask_test_truth = imgs_mask_test_truth.astype('float32')
imgs_mask_test_truth /= 255

test_truth = imgs_mask_test_truth.flatten()
test_result = imgs_mask_test_result.flatten()

print(test_result.shape)
print(test_truth.shape)
intersect = test_result * test_truth
dice_score = (2. * intersect.sum()) / (test_truth.sum() + test_result.sum())
print('Dice coefficient on testing data is : {0:.3f}.'.format(dice_score))

result_path = './eval/'
for index in range(0, 10):
    result = imgs_mask_test_result[index,0]
    truth = imgs_mask_test_truth[index,0]
    difference = result - truth
        
    difference *= 127
    difference += 127
    
    difference = difference.astype(np.uint8)
    diffname = "diff_{}.jpg".format(index)
    misc.imsave(os.path.join(result_path, diffname),difference)
    
# uncomment these lines if you want the output masks    
result *= 255
truth *= 255
result = result.astype(np.uint8)
truth = truth.astype(np.uint8)
truthname = "truth_{}.jpg".format(index)
misc.imsave(os.path.join(result_path, truthname),truth)
resultname = "result_{}.jpg".format(index)
misc.imsave(os.path.join(result_path, resultname),result)
print('1')
