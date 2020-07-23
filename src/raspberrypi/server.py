'''
Need to use "sudo"
'''
import subprocess
import datetime
import os
import asyncio
import schedule
import time

from azure.iot.device.aio import IoTHubDeviceClient
from azure.core.exceptions import AzureError
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient

from logscreen import screen
import opencheck.opencheck

#Azure IoT Hubの接続文字列
CONNECTION_STRING = os.getenv('CONNECTION_STRING', None)

HOME = os.environ['HOME']#ホームディレクトリのパス

CONTAINER_NAME = "raspberrypi-camera"
#Azure Storage Containerの接続文字列
AZURE_STORAGE_CONTAINER_CONNECTION_STRING = os.getenv('ASC_CONNECTION_STRING', None)
'''
Azure Iot Hub用
Azure Storageの「$web」へアップロード
アップロード先の変更はAzure Iot Hubポータルから行う
'''
async def store_blob(blob_info, file_name):
    try:
        sas_url = "https://{}/{}/{}{}".format(
            blob_info["hostName"],
            blob_info["containerName"],
            blob_info["blobName"],
            blob_info["sasToken"]
        )

        screen.logOK("Uploading file: {} to Azure Storage as blob: {} in container {}\n".format(file_name, blob_info["blobName"], blob_info["containerName"]))

        # Upload the image file
        with BlobClient.from_blob_url(sas_url) as blob_client:
            with open(file_name, "rb") as f:
                result = blob_client.upload_blob(f, overwrite=True)
                return (True, result)

    except FileNotFoundError as ex:
        ex.status_code = 404
        screen.logFatal(ex)
        return (False, ex)

    except AzureError as ex:
        # catch Azure errors that might result from the upload operation
        screen.logFatal(ex)
        return (False, ex)

async def connectAndUploadToAzure(imgPath):
    try:
        screen.logOK( "IoT Hub file upload." )
        conn_str = CONNECTION_STRING
        device_client = IoTHubDeviceClient.create_from_connection_string(conn_str)
        blob_name = os.path.basename(imgPath)
        await device_client.connect()

        # Get the storage info for the blob
        storage_info = await device_client.get_storage_info_for_blob(blob_name)

        # Upload to blob
        success, result = await store_blob(storage_info, imgPath)

        if success == True:
            screen.logOK("Upload succeeded. Result is: \n")
            screen.logOK(" ")
            print(result)

            await device_client.notify_blob_upload_status(
                storage_info["correlationId"], True, 200, "OK: {}".format(imgPath)
            )

        else :
            screen.logFatal("Upload failed. Exception is: \n") 
            screen.logFatal(" ")
            print(result)

            await device_client.notify_blob_upload_status(
                storage_info["correlationId"], False, result.status_code, str(result)
            )

    except Exception:
        screen.logFatal("Exception(connectAndUploadToAzure)")

    finally:
        # Finally, disconnect the client
        await device_client.disconnect()
        screen.logOK("Disconnect the client")

def getPhoto():
    cmd = ["raspistill", "-t", "3000", "-o", "photo.jpg"]
    screen.logOK("Run raspistill...")
    try:
        subprocess.check_call(cmd)
        takePhotoTime = datetime.datetime.now()
    except:
        screen.logFatal("subprocess.check_call() failed")
        return
    
    screen.logOK("Successful photo shoot. time:" + takePhotoTime.strftime('%Y/%m/%d %H:%M:%S'))

    pret = opencheck.PhotoImageMatching(f"./photo.jpg")
    screen.logOK("Successful photoImageMatching. (" + str(pret) +")")

    pretdatapass = HOME + "pretdata"
    WritePret(pret,pretdatapass)

    return os.path.abspath("./photo.jpg"), pretdatapass ,pret

def WritePret(pret, path):
    with open(path, mode='w') as fp:
        time_now = datetime.datetime.now()
        msg = str(pret) + "\n" + str(time_now.hour) + "\n" + str(time_now.minute) + "\n"
        fp.write(msg)

'''
Azure Storage Containerへファイルをアップロード
'''
def UploadToAzureStrageContainer(filepath):
    blob_service_client = BlobServiceClient.from_connection_string(CONNECTION_STRING)
    container_client = blob_service_client.get_container_client(CONTAINER_NAME)
    blob_client = container_client.get_blob_client(filepath)
    blob_client.delete_blob()#クラウド上のファイルを削除
    with open(filepath, "rb") as data:
        blob_client.upload_blob(data, blob_type="AppendBlob")#アップロード

def main():
    photopath, datapass, pret = getPhoto()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(connectAndUploadToAzure(photopath))
    UploadToAzureStrageContainer(datapass)

if __name__ == "__main__":
    # run every 5min
    try:
        screen.logOK( "Running System, press Ctrl-C to exit" )
        schedule.every(5).minutes.do(main)
    except KeyboardInterrupt:
        screen.logFatal( "System stopped." )
