#!/usr/bin/python3

ADAPTER_NAME = "hci0"

BLUEZ_SERVICE_NAME = "org.bluez"
BLUEZ_NAMESPACE = "/org/bluez/"
DBUS_PROPERTIES="org.freedesktop.DBus.Properties"
DBUS_OM_IFACE = 'org.freedesktop.DBus.ObjectManager'

ADAPTER_INTERFACE = BLUEZ_SERVICE_NAME + ".Adapter1"
DEVICE_INTERFACE = BLUEZ_SERVICE_NAME + ".Device1"
GATT_MANAGER_INTERFACE = BLUEZ_SERVICE_NAME + ".GattManager1"
GATT_SERVICE_INTERFACE = BLUEZ_SERVICE_NAME + ".GattService1"
GATT_CHARACTERISTIC_INTERFACE = BLUEZ_SERVICE_NAME + ".GattCharacteristic1"
GATT_DESCRIPTOR_INTERFACE = BLUEZ_SERVICE_NAME + ".GattDescriptor1"
ADVERTISEMENT_INTERFACE = BLUEZ_SERVICE_NAME + ".LEAdvertisement1"
ADVERTISING_MANAGER_INTERFACE = BLUEZ_SERVICE_NAME + ".LEAdvertisingManager1"


SVC_UUID = "0000fff0-0000-1000-8000-00805f9b34fb"
RX_CHR_UUID = "0000fff1-0000-1000-8000-00805f9b34fb"
TX_CHR_UUID = "0000fff2-0000-1000-8000-00805f9b34fb"
