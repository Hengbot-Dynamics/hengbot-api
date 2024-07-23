import bluetooth_constants
import bluetooth_gatt
import bluetooth_utils
import bluetooth_exceptions
import dbus
import dbus.exceptions
import dbus.service
import dbus.mainloop.glib
import sys
import random
from gi.repository import GObject
from gi.repository import GLib
import os
sys.path.insert(0, '.')

bus = None
adapter_path = None
adv_mgr_interface = None
connected = 0

connect_failed = False

threadrunflag = False
runthread = None

class Advertisement(dbus.service.Object):
    PATH_BASE = '/org/bluez/ldsg/advertisement'

    def __init__(self, bus, index, advertising_type):
        self.path = self.PATH_BASE + str(index)
        self.bus = bus
        self.ad_type = advertising_type
        self.service_uuids = None
        self.manufacturer_data = None
        self.solicit_uuids = None
        self.service_data = None
        self.local_name = 'Sparky '+get_bd_address()[-5:]
        self.include_tx_power = False
        self.data = None
        self.discoverable = True
        dbus.service.Object.__init__(self, bus, self.path)

    def get_properties(self):
        properties = dict()
        properties['Type'] = self.ad_type
        if self.service_uuids is not None:
            properties['ServiceUUIDs'] = dbus.Array(self.service_uuids,
                                                    signature='s')
        if self.solicit_uuids is not None:
            properties['SolicitUUIDs'] = dbus.Array(self.solicit_uuids,
                                                    signature='s')
        if self.manufacturer_data is not None:
            properties['ManufacturerData'] = dbus.Dictionary(
                self.manufacturer_data, signature='qv')
        if self.service_data is not None:
            properties['ServiceData'] = dbus.Dictionary(self.service_data,
                                                        signature='sv')
        if self.local_name is not None:
            properties['LocalName'] = dbus.String(self.local_name)
        if self.discoverable is not None and self.discoverable == True:
            properties['Discoverable'] = dbus.Boolean(self.discoverable)
        if self.include_tx_power:
            properties['Includes'] = dbus.Array(["tx-power"], signature='s')

        if self.data is not None:
            properties['Data'] = dbus.Dictionary(
                self.data, signature='yv')
        print(properties)
        return {bluetooth_constants.ADVERTISING_MANAGER_INTERFACE: properties}

    def get_path(self):
        return dbus.ObjectPath(self.path)

    @dbus.service.method(bluetooth_constants.DBUS_PROPERTIES,
                         in_signature='s',
                         out_signature='a{sv}')
    def GetAll(self, interface):
        if interface != bluetooth_constants.ADVERTISEMENT_INTERFACE:
            raise bluetooth_exceptions.InvalidArgsException()
        return self.get_properties()[bluetooth_constants.ADVERTISING_MANAGER_INTERFACE]

    @dbus.service.method(bluetooth_constants.ADVERTISING_MANAGER_INTERFACE,
                         in_signature='',
                         out_signature='')
    def Release(self):
        print('%s: Released' % self.path)


class Application(dbus.service.Object):
    """
    org.bluez.GattApplication1 interface implementation
    """
    def __init__(self, bus):
        self.path = '/'
        self.services = []
        dbus.service.Object.__init__(self, bus, self.path)
        self.add_service(Service(bus, '/org/bluez/ldsg', 0))

    def get_path(self):
        return dbus.ObjectPath(self.path)

    def add_service(self, service):
        self.services.append(service)

    @dbus.service.method(bluetooth_constants.DBUS_OM_IFACE, out_signature='a{oa{sa{sv}}}')
    def GetManagedObjects(self):
        response = {}
        print('GetManagedObjects')

        for service in self.services:
            print("GetManagedObjects: service="+service.get_path())
            response[service.get_path()] = service.get_properties()
            chrcs = service.get_characteristics()
            for chrc in chrcs:
                response[chrc.get_path()] = chrc.get_properties()
                descs = chrc.get_descriptors()
                for desc in descs:
                    response[desc.get_path()] = desc.get_properties()

        return response


class Service(bluetooth_gatt.Service):

     def __init__(self, bus, path_base, index):
        print("Initialising LedService object")
        bluetooth_gatt.Service.__init__(self, bus, path_base, index, bluetooth_constants.SVC_UUID, True)
        print("Adding LedTextharacteristic to the service")
        self.add_characteristic(RxCharacteristic(bus, 0, self))
        self.add_characteristic(TxCharacteristic(bus, 1, self))


class TxCharacteristic(bluetooth_gatt.Characteristic):
    
    def __init__(self, bus, index, service):
        global timer_id
        bluetooth_gatt.Characteristic.__init__(
                self, bus, index,
                bluetooth_constants.TX_CHR_UUID,
                ['read','notify'],
                service)
        self.notifying = False

    # note this overrides the same method in bluetooth_gatt.Characteristic where it is exported to 
    # make it visible over DBus
    def StartNotify(self):
        print("starting notifications")
        self.notifying = True

    def StopNotify(self):
        print("stopping notifications")
        self.notifying = False


class RxCharacteristic(bluetooth_gatt.Characteristic):

    def __init__(self, bus, index, service):
        bluetooth_gatt.Characteristic.__init__(
                self, bus, index,
                bluetooth_constants.RX_CHR_UUID,
                ['write'],
                service)

    def WriteValue(self, value, options):
        global runthread, threadrunflag
        ascii_bytes = bluetooth_utils.dbus_to_python(value)
        senddata(ascii_bytes)
        byte_string = bytes(ascii_bytes)

        if ascii_bytes[0] == 0xff and ascii_bytes[1] == 0xff:
            if ascii_bytes[2] == 0x12:
                text = byte_string[3:].decode('utf-8')
                print(str(byte_string) + " = " + text)
                if not threadrunflag:
                    import threading
                    from maix import display, camera 
                    runthread = threading.Thread(target=run_file, args=(text,))
                    threadrunflag = True
                    runthread.start()
            elif ascii_bytes[2] == 0x82:
                if not get_wifi_ip_ssid():
                    senddata('geterr, wifi not connected'.encode())
            elif ascii_bytes[2] == 0x14:
                try:
                    result = subprocess.run(['nmcli', 'device', 'disconnect', 'wlan0'], check=True, capture_output=True, text=True)
                    senddata(result.stdout.encode())
                except subprocess.CalledProcessError as e:
                    senddata(e.stderr.encode())
        else:
            text = byte_string.decode('utf-8')
            print(str(byte_string) + " = " + text)
            get_wifi_info(text)


def register_ad_cb():
    print('Advertisement registered OK')

def register_ad_error_cb(error):
    print('Error: Failed to register advertisement: ' + str(error))
    mainloop.quit()

def register_app_cb():
    print('GATT application registered')

def register_app_error_cb(error):
    print('Failed to register application: ' + str(error))
    mainloop.quit()

def set_connected_status(status):
    global threadrunflag
    if (status == 1):
        print("connected")
        connected = 1
        stop_advertising()
    else:
        print("disconnected")
        connected = 0
        threadrunflag = False
        start_advertising()

def properties_changed(interface, changed, invalidated, path):
    if (interface == bluetooth_constants.DEVICE_INTERFACE):
        if ("Connected" in changed):
            set_connected_status(changed["Connected"])

def interfaces_added(path, interfaces):
    if bluetooth_constants.DEVICE_INTERFACE in interfaces:
        properties = interfaces[bluetooth_constants.DEVICE_INTERFACE]
        if ("Connected" in properties):
            set_connected_status(properties["Connected"])

def stop_advertising():
    global adv
    global adv_mgr_interface
    print("Unregistering advertisement",adv.get_path())
    adv_mgr_interface.UnregisterAdvertisement(adv.get_path())

def start_advertising():
    global adv
    global adv_mgr_interface
    # we're only registering one advertisement object so index (arg2) is hard coded as 0
    print("Registering advertisement",adv.get_path())
    adv_mgr_interface.RegisterAdvertisement(adv.get_path(), {},
                                        reply_handler=register_ad_cb,
                                        error_handler=register_ad_error_cb)

import subprocess
import re

def connect_to_wifi(ssid, password):
    global connect_failed
    connect_failed = False
    senddata('Connecting to wifi'.encode())

    connect_command = [
        "nmcli", "device", "wifi", "connect", ssid, "password", password
    ]
    
    result = subprocess.run(connect_command, capture_output=True, text=True)

    if result.returncode == 0 and 'successfully activated' in result.stdout.lower():
        get_wifi_ip_ssid()
    else:
        senddata("Failed to connect to WiFi.".encode())
        connect_failed = True
        def detect():
            global connect_failed
            if connect_failed:
                if get_wifi_ip_ssid(add_msg='Error, reset previous connection\n'):
                    connect_failed = False
                    return True
            else:
                return True
            GLib.timeout_add(300, detect)
        GLib.timeout_add(300, detect)

def get_wifi_info(wifi_string):

    ssid_match = re.search(r'S:"(.*?)";', wifi_string)
    password_match = re.search(r'P:(\d+);', wifi_string)

    if ssid_match and password_match:
        ssid = ssid_match.group(1)
        password = password_match.group(1)

        print(f"SSID: {ssid}")
        print(f"Password: {password}")
        connect_to_wifi(ssid, password)
        return True
    else:
        senddata('Wrong QR code'.encode())
        return False

def get_threadrunflag():
    global threadrunflag
    return threadrunflag

def get_wifi_ip_ssid(interface='wlan0', add_msg=''):
    try:
        result = subprocess.run(['ifconfig', interface], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode == 0:
            output = result.stdout
            for line in output.split('\n'):
                if 'inet ' in line and 'netmask' in line:
                    ip_address = line.split()[1]
                    print(line)
                    senddata((add_msg + subprocess.check_output(['iwgetid', '--raw'], text=True).strip() + ' ' + ip_address).encode())
                    return True
        else:
            print(f"Error getting IP address: {result.stderr}")
    except Exception as e:
        print(f"Exception occurred: {e}")
    return False

def get_bd_address():
    try:
        # 运行 hciconfig 命令
        output = subprocess.check_output(['hciconfig'], text=True)
        
        # 使用正则表达式匹配 BD Address
        match = re.search(r'BD Address: ([0-9A-F:]+)', output, re.I)
        
        if match:
            bd_address = match.group(1)
            return bd_address
        else:
            return None
    except subprocess.CalledProcessError as e:
        print(f"Failed to run hciconfig: {e}")
        return None

def run_file(file_path):
    global app,threadrunflag
    print(file_path)
    os.path.exists(file_path)
    with open(file_path, 'r') as file:
        file_content = file.read()
    file.close()
    try:
        exec(file_content, globals(), globals())
    except SystemExit:
        threadrunflag = False
    app.services[0].characteristics[0].threadrunflag = False

command = ['hciconfig', 'hci0', 'reset']
subprocess.run(command, capture_output=True, text=True)

dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
bus = dbus.SystemBus()
# we're assuming the adapter supports advertising
adapter_path = bluetooth_constants.BLUEZ_NAMESPACE + bluetooth_constants.ADAPTER_NAME
adv_mgr_interface = dbus.Interface(bus.get_object(bluetooth_constants.BLUEZ_SERVICE_NAME,adapter_path), bluetooth_constants.ADVERTISING_MANAGER_INTERFACE)

service_manager = dbus.Interface(
        bus.get_object(bluetooth_constants.BLUEZ_SERVICE_NAME, adapter_path),
        bluetooth_constants.GATT_MANAGER_INTERFACE)

bus.add_signal_receiver(properties_changed,
        dbus_interface = bluetooth_constants.DBUS_PROPERTIES,
        signal_name = "PropertiesChanged",
        path_keyword = "path")

bus.add_signal_receiver(interfaces_added,
        dbus_interface = bluetooth_constants.DBUS_OM_IFACE,
        signal_name = "InterfacesAdded")


# we're only registering one advertisement object so index (arg2) is hard coded as 0
adv_mgr_interface = dbus.Interface(bus.get_object(bluetooth_constants.BLUEZ_SERVICE_NAME,adapter_path), bluetooth_constants.ADVERTISING_MANAGER_INTERFACE)
adv = Advertisement(bus, 0, 'peripheral')
start_advertising()

app = Application(bus)


def senddata(msg):
    value = []
    for data in msg:
        value.append(dbus.Byte(data))
    app.services[0].characteristics[1].PropertiesChanged(bluetooth_constants.GATT_CHARACTERISTIC_INTERFACE, { 'Value': value }, [])

mainloop = GLib.MainLoop()

print('Registering GATT application...')

service_manager.RegisterApplication(app.get_path(), {},
                                reply_handler=register_app_cb,
                                error_handler=register_app_error_cb)

mainloop.run()

