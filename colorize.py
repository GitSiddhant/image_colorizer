import argparse 
import numpy as np
import cv2
import os

def color_image():

    # construct the argument parser and parse the arguments so that 
    # the image can be uploaded at runtime through the command line

        ap = argparse.ArgumentParser()
        ap.add_argument("-i", "--image", type=str, required=True,
            help="path to input black and white image")
  
        args = vars(ap.parse_args())
        # load our serialized black and white colorizer model and cluster
    # center points from disk
        
        prototxt_path = os.path.sep.join(["model", "colorization_deploy_v2.prototxt"])
        model_path = "colorization_release_v2.caffemodel"
        pts_path = os.path.sep.join(["model", "pts_in_hull.npy"])
        net = cv2.dnn.readNetFromCaffe(prototxt_path, model_path)
        pts = np.load(pts_path)

    # add the cluster centers as 1x1 convolutions to the model
        class8 = net.getLayerId("class8_ab")
        conv8 = net.getLayerId("conv8_313_rh")
        pts = pts.transpose().reshape(2, 313, 1, 1)
        net.getLayer(class8).blobs = [pts.astype("float32")]
        net.getLayer(conv8).blobs = [np.full([1, 313], 2.606, dtype="float32")]

    # load the input image from disk, scale the pixel intensities to the
    # range [0, 1], and then convert the image from the BGR to Lab color
    # space
        image = cv2.imread(args["image"])
        scaled = image.astype("float32") / 255.0
        lab = cv2.cvtColor(scaled, cv2.COLOR_BGR2LAB)
         # resize the Lab image to 224x224 (the dimensions the colorization
    # network accepts), split channels, extract the 'L' channel, and then
    # perform mean centering
        resized = cv2.resize(lab, (224, 224))
        L = cv2.split(resized)[0]
        L -= 50
    # pass the L channel through the network which will *predict* the 'a'
    # and 'b' channel values
        
        net.setInput(cv2.dnn.blobFromImage(L))
        ab = net.forward()[0, :, :, :].transpose((1, 2, 0))
    # resize the predicted 'ab' volume to the same dimensions as our
    # input image
        ab = cv2.resize(ab, (image.shape[1], image.shape[0]))

    # grab the 'L' channel from the *original* input image (not the
    # resized one) and concatenate the original 'L' channel with the
    # predicted 'ab' channels
        L = cv2.split(lab)[0]
        colorized = np.concatenate((L[:, :, np.newaxis], ab), axis=2)
    # convert the output image from the Lab color space to RGB, then
    # clip any values that fall outside the range [0, 1]
        colorized = cv2.cvtColor(colorized, cv2.COLOR_LAB2BGR)
        colorized = np.clip(colorized, 0, 1)
    # the current colorized image is represented as a floating point
    # data type in the range [0, 1] -- let's convert to an unsigned
    # 8-bit integer representation in the range [0, 255]
        colorized = (255 * colorized).astype("uint8")
        # show the original and output colorized images
        cv2.imshow("Original", image)
        cv2.imshow("Colorized", colorized)
        cv2.waitKey(0)

if __name__ == "__main__":
    color_image()
