import os
import numpy as np
import rasterio
import matplotlib.pyplot as plt
from skimage import exposure
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

# Google Drive authentication
current_dir = os.path.dirname(os.path.abspath(__file__))
client_secrets_path = os.path.join(current_dir, 'client_secrets.json')
credentials_path = os.path.join(current_dir, 'credentials.json')
gauth = GoogleAuth(settings_file=client_secrets_path)
gauth.LoadCredentialsFile(credentials_path)
if gauth.credentials is None:
    gauth.LocalWebserverAuth()
elif gauth.access_token_expired:
    gauth.Refresh()
else:
    gauth.Authorize()
gauth.SaveCredentialsFile(credentials_path)

# Search for the file 'Sentinel1_Charlestown.tif'
drive = GoogleDrive(gauth)
folder_id = ''
file_id = ''
file_list = drive.ListFile({'q': "'root' in parents and trashed=false"}).GetList()
for file in file_list:
    if file['title'] == 'SatInsights' and file['mimeType'] == 'application/vnd.google-apps.folder':
        folder_id = file['id']
        break

if folder_id:
    file_list = drive.ListFile({'q': f"'{folder_id}' in parents and trashed=false"}).GetList()
    for file in file_list:
        if file['title'] == 'Sentinel1_Charlestown.tif':
            file_id = file['id']
            break

# Download the file if found
if file_id:
    file = drive.CreateFile({'id': file_id})
    file.GetContentFile('data/Sentinel1_Charlestown.tif')

    # Open the image and read the bands
    with rasterio.open('data/Sentinel1_Charlestown.tif') as src:
        HH = src.read(1)
        VH = src.read(2)
        angle = src.read(3)

    # Apply a contrast stretch to the data
    HH_stretched = exposure.rescale_intensity(HH, in_range=tuple(np.percentile(HH, (-50, 1))))
    VH_stretched = exposure.rescale_intensity(VH, in_range=tuple(np.percentile(VH, (-50, 1))))
    angle_stretched = exposure.rescale_intensity(angle, in_range=tuple(np.percentile(angle, (37, 38))))

    # Combine the bands into an RGB image
    rgb_image = np.dstack((HH_stretched, angle_stretched, VH_stretched))

    # Display the images
    fig, axs = plt.subplots(2, 2, figsize=(15, 10))

    axs[0, 0].imshow(HH_stretched, cmap='gray')
    axs[0, 0].set_title('HH (Contrast Stretched)')
    axs[0, 0].axis('off')

    axs[0, 1].imshow(VH_stretched, cmap='gray')
    axs[0, 1].set_title('VH (Contrast Stretched)')
    axs[0, 1].axis('off')

    axs[1, 0].imshow(angle_stretched, cmap='gray')
    axs[1, 0].set_title('Angle (Contrast Stretched)')
    axs[1, 0].axis('off')

    axs[1, 1].imshow(rgb_image)
    axs[1, 1].set_title('Sentinel1_Charlestown (RGB)')
    axs[1, 1].axis('off')

    # Remove any unused subplots
    for i in range(axs.shape[0]):
        for j in range(axs.shape[1]):
            if not axs[i, j].has_data():
                fig.delaxes(axs[i, j])

    plt.tight_layout()
    plt.show()

else:
    print("The file 'Sentinel1_Charlestown.tif' was not found in the 'SatInsights' folder.")
