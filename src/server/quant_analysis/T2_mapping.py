import argparse
import matplotlib.pyplot as plt
import numpy as np
import pydicom
from scipy.optimize import curve_fit
import os


def main(dicom_file_path: str, TE: np = None, TR: np = None): # TI should be in second
    """
    Return T2 mapping of a series of SE images with variable TE.

    Parameters
    ----------
    dicom_file_path: folder path where all dicom files are
    TE: TI values used in SE experiments
    TR: TR values used in SE experiments, should be constant

    Returns
    -------
    T2_map: T2 map generated based on input images and TE TR values

    """
    lstFilesDCM = []  # create an empty list
    for dirName, subdirList, fileList in os.walk(dicom_file_path):
        for filename in fileList:
            if ".dcm" in filename.lower():  # check whether the file's DICOM
                lstFilesDCM.append(os.path.join(dirName, filename))

    ref_image = pydicom.read_file(lstFilesDCM[0])  # Get ref file
    image_size = (int(ref_image.Rows), int(ref_image.Columns), len(lstFilesDCM))  # Load dimensions
    image_data_final = np.zeros(image_size, dtype=ref_image.pixel_array.dtype)

    for filenameDCM in lstFilesDCM:
        ds = pydicom.read_file(filenameDCM)  # read the file
        image_data_final[:, :, lstFilesDCM.index(filenameDCM)] = ds.pixel_array  # store the raw image data

    T2_map = np.zeros([image_size[0], image_size[1]])
    p0 = (0.8002804688888, 0.141886338627215, 0.421761282626275, 0.915735525189067)  # initial guess for parameters
    plt.figure()
    plt.imshow(image_data_final[:, :, 3], cmap='gray')
    plt.show()
    for n2 in range(image_size[0]):
        for n3 in range(image_size[1]):
            y_data = image_data_final[n2, n3, :]
            popt, pcov = curve_fit(T2_sig_eq, (TE, TR), y_data, p0, bounds=(0, 6))
            T2_map[n2, n3] = popt[2]

    plt.figure()
    plt.imshow(T2_map, cmap='hot')
    plt.show()

    return T2_map


def T2_sig_eq(X, a, b, c, d):
    """
    Generate an exponential function for curve fitting

    Parameters
    ----------
    x: independent variables
    y: independent variables
    a: curve fitting parameters
    b: curve fitting parameters
    c: curve fitting parameters
    d: curve fitting parameters

    Returns
    -------
    exponential function used for T1 curve fitting

    """
    x, y = X
    return a * (1 - np.exp(-y / b)) * np.exp(-x / c) + d

