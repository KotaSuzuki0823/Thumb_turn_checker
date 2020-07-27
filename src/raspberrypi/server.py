import subprocess
import datetime
import os
import asyncio
import schedule
import time
import sys
import json

from azure.iot.device.aio import IoTHubDeviceClient
from azure.core.exceptions import AzureError
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient

from logscreen import screen
#from opencheck import check as oc

HOME = os.environ['HOME']#ホームディレクトリのパス

#Azure IoT Hubの接続文字列
CONNECTION_STRING = os.getenv('CONNECTION_STRING', None)
#Azure Storage Containerの名前
CONTAINER_NAME = os.getenv('CONTAINER_NAME', None)
#Azure Storage Containerの接続文字列
AZURE_STORAGE_CONTAINER_CONNECTION_STRING = os.getenv('ASC_CONNECTION_STRING', None)

async def store_blob(blob_info, file_name):
    '''
    Azure Iot Hub用
    アップロード先の変更はAzure Iot Hubポータルから行う
    '''
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
            screen.logOK("Upload succeeded. Result is:")
            screen.logOK(result)

            await device_client.notify_blob_upload_status(
                storage_info["correlationId"], True, 200, "OK: {}".format(imgPath)
            )

        else :
            screen.logFatal("Upload failed. Exception is:")
            screen.logFatal(result)

            await device_client.notify_blob_upload_status(
                storage_info["correlationId"], False, result.status_code, str(result)
            )

    except Exception:
        screen.logFatal("Exception(connectAndUploadToAzure)")

    finally:
        # Finally, disconnect the client
        await device_client.disconnect()
        screen.logOK("Disconnect the client")
    
async def UploadToAzureStrageContainer(filepath):
    '''
    Azure Storage Containerへファイルをアップロード
    filepath:アップロードするローカルファイルパス
    '''
    screen.logOK("Uploading file to AzureStrageContainer")
    try:
        blob_service_client = BlobServiceClient.from_connection_string(AZURE_STORAGE_CONTAINER_CONNECTION_STRING)
        container_client = blob_service_client.get_container_client(CONTAINER_NAME)
        # Upload the created file, use local_file_name for the blob name
        blob_client = blob_service_client.get_blob_client(
            container=CONTAINER_NAME, blob='pretdata.json')
        with open(filepath, "rb") as data:
            blob_client.upload_blob(data)

        screen.logOK("Uploaded file("+ filepath +") to AzureStrageContainer")

    except Exception as e:
        screen.logFatal(e)

def getPhoto(photopath):
    '''
    写真の撮影
    '''
    cmd = ["raspistill", "-t", "3000", "-o", photopath]
    screen.logOK("Run raspistill...")
    try:
        subprocess.check_call(cmd)
        takePhotoTime = datetime.datetime.now()
    except Exception as e:
        screen.logFatal("subprocess.check_call() failed:"+ e)
        return
    
    screen.logOK("Successful photo shoot. time:" + takePhotoTime.strftime('%Y/%m/%d %H:%M:%S')+"file:"+photopath)


def WritePhotoDataJSON(jsonpath,photopath):
    '''
    写真の書き込み時間（時，分）を出力
    '''
    try:
        with open(jsonpath, mode='w') as fp:
            time_now = datetime.datetime.now()
            dic = {'path': str(photopath),
                   'time': {'hour': str(time_now.hour), 'min': str(time_now.minute), 'sec': str(time_now.second)}}

            fp.write(json.dumps(dic))

    except Exception as e:
        screen.logFatal(e)

def main():
    photopath = HOME + "/photo.jpg"
    getPhoto(photopath)

    #pret = oc.PhotoImageMatching(photopath)
    #screen.logOK("Successful photoImageMatching. (" + str(pret) + ")")

    jsonpath = HOME + "/pretdata.json"
    WritePhotoDataJSON(jsonpath,photopath)
    screen.logOK("wrote json.")

    #pretdatapath = HOME + "/pretdata.json"
    #oc.WritePret(pret, pretdatapath)
    #screen.logOK("Saved pretdata at "+pretdatapath)

    loop = asyncio.get_event_loop()
    loop.run_until_complete(connectAndUploadToAzure(photopath))
    loop.run_until_complete(UploadToAzureStrageContainer(jsonpath))

    screen.logOK("finish")

if __name__ == "__main__":
    # run every 5min
    args = sys.argv
    try:
        screen.logOK( "Running System, press Ctrl-C to exit" )

        if "-t" in args:
            screen.logWarning("Running TEST")
            main()
            exit(0)
        else:
            schedule.every(5).minutes.do(main)

        while True:
            schedule.run_pending()
            time.sleep(5)

    except KeyboardInterrupt:
        print("\n")
        screen.logWarning("system stop:"+str(KeyboardInterrupt))
