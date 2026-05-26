import numpy as np
import pydicom
from skimage.filters import threshold_otsu
import asyncio

def thread_load_dicom(dicom_path: str):
    ds = pydicom.dcmread(dicom_path)
    pixel_array = ds.pixel_array.astype(float)
     # https://pydicom.github.io/pydicom/1.1/working_with_pixel_data.html
    # this is from the DICOM image metadata that has the scaling, slope, and intercept 
    # for the linear transformation (default is 1 and 0)
    if pixel_array.ndim == 3:
        pixel_array = pixel_array[pixel_array.shape[0] // 2]
    slope = float(getattr(ds, 'RescaleSlope', 1))
    intercept = float(getattr(ds, 'RescaleIntercept', 0))
    pixel_array = pixel_array * slope + intercept
    return ds, pixel_array
    
def thread_segment_dicom(dicom_path: str) -> dict:
    # https://scikit-image.org/docs/stable/auto_examples/segmentation/plot_thresholding.html
    # gets the optimal threshold by maximizing the variance between two classes of pixels, 
    # which are separated by the threshold (pixel intensity)
    ds, pixel_array = thread_load_dicom(dicom_path)
    thresh = threshold_otsu(pixel_array)
    mask = pixel_array > thresh
    spacing = getattr(ds, 'PixelSpacing', [1.0, 1.0])
    thickness = float(getattr(ds, 'SliceThickness', 1.0))
    vox_vol = float(spacing[0]) * float(spacing[1]) * thickness
    n_voxels = int(np.sum(mask))
    volume_mL = round(n_voxels * vox_vol / 1000.0, 4)
    return {
        'lesion_volume_mL': volume_mL,
        'voxel_volume': round(vox_vol, 3),
        'slice_thickness_mm': thickness,
        'otsu_threshold': round(float(thresh), 3)
    }

async def load_dicom(dicom_path: str):
    return await asyncio.to_thread(thread_load_dicom, dicom_path)

async def segment_dicom(dicom_path: str) -> dict:
    return await asyncio.to_thread(thread_segment_dicom, dicom_path)
    
    