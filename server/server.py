'''
Need to use "sudo"
'''
import subprocess
import time
import os
import asyncio
import schedule
from logscreen import screen 
from azure.iot.device.aio import IoTHubDeviceClient
from azure.core.exceptions import AzureError
from azure.storage.blob import BlobClient

CONNECTION_STRING = "[Device Connection String]"

'''
Azure Iot Hub 接続用関数
ファイルを BLOB ストレージにアップロードする
'''
async def store_blob(blob_info, file_name):
    try:
        sas_url = "https://{}/{}/{}{}".format(
            blob_info["hostName"],
            blob_info["containerName"],
            blob_info["blobName"],
            blob_info["sasToken"]
        )

        screen.logOK("\nUploading file: {} to Azure Storage as blob: {} in container {}\n".format(file_name, blob_info["blobName"], blob_info["containerName"]))

        # Upload the specified file
        with BlobClient.from_blob_url(sas_url) as blob_client:
            with open(file_name, "rb") as f:
                result = blob_client.upload_blob(f, overwrite=True)
                return (True, result)

    except FileNotFoundError as ex:
        # catch file not found and add an HTTP status code to return in notification to IoT Hub
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
        blob_name = os.path.basename(imgPath)

        device_client = IoTHubDeviceClient.create_from_connection_string(conn_str)

        # Connect the client
        await device_client.connect()

        # Get the storage info for the blob
        storage_info = await device_client.get_storage_info_for_blob(blob_name)

        # Upload to blob
        success, result = await store_blob(storage_info, imgPath)

        if success == True:
            screen.logOK("Upload succeeded. Result is: \n") 
            screen.logOK(result)
            print()

            await device_client.notify_blob_upload_status(
                storage_info["correlationId"], True, 200, "OK: {}".format(imgPath)
            )

        else :
            # If the upload was not successful, the result is the exception object
            screen.logFatal("Upload failed. Exception is: \n") 
            screen.logFatal(result)
            print()

            await device_client.notify_blob_upload_status(
                storage_info["correlationId"], False, result.status_code, str(result)
            )

    except Exception as ex:
        screen.logFatal(ex)

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
    return os.path.abspath("./photo.jpg")

def main():
    photopath = getPhoto()
    connectAndUploadToAzure(photopath)


if __name__ == "__main__":
    # 5分ごとに実行
    try:
        screen.logOK( "Running System, press Ctrl-C to exit" )
        schedule.every(5).minutes.do(main)
    except KeyboardInterrupt:
        screen.logFatal( "System stopped." )

