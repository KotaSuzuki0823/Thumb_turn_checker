# Thumb_turn_checker
## pip
実行時に必要となるパッケージは以下のコマンドでインストール

`pip3 install -r requirements.txt`

## OpenCV
OpenCVに必要な外部パッケージが無い（エラーが出た）場合はラズパイへインストール

`sudo apt-get install libatlas-base-dev`

`sudo apt-get install libjasper-dev`

`sudo apt-get install libqt4-test`

[ラズパイでpython3にopencvを入れたらエラーが出た【対処法】](https://qiita.com/XM03/items/48463fd910470b226f22)

## 環境変数
### Azure App Service
設定が必要なものは以下の3つ

LINE_CHANNEL_ACCESS_TOKEN：LINE Massaging API用

LINE_CHANNEL_SECRET：LINE Massaging API用

IMG_THRESHOLD：鍵の施錠状態を判定するしきい値．任意の値でOK．値を下げると解錠判定が厳しくなる．

### Raspberry Pi
Azureへログイン

`az login`

#### Azure IoT Hubの接続文字列取得
IotHub用拡張パッケージの導入（初回のみ）

`az extension add --name azure-iot`

接続文字列の取得

`az iot hub device-identity show-connection-string --device-id [device id] --hub-name [hub name]`

[device id]：IotHubに登録しているデバイスのID（名前） camera<br>
[hub name]：IoTHubアカウントの名前 RaspberryPi-Camera<br>

#### Azure Storage Containerの接続文字列取得
`az storage account show-connection-string --name [storage name]`

[storage name]：ストレージアカウントの名前

#### 環境変数の設定
`./bash_profile`を編集<br>
新規ファイルを作成（.bash_profileが存在しない場合）<br>
`touch ~/.bash_profile`

.bash_profileに以下を追記

`ASC_CONNECTION_STRING={Azure Storage account connection_string}`<br>
`CONNECTION_STRING={IoT Hub connection_string}`<br>
`CONTAINER_NAME={your_container_name}`<br>

.bash_profileの再読み込み

`source ~/.bash_profile`









