import argparse
import uiautomator2 as u2
import logging
import traceback
import time

# Constants
ANDROID_SERIAL = "4fe9718b"
SAVED_WIFI_SSID = "test-xxzhkcgj"
DEFAULT_DEVICE_NAME = "First light"
MAXIMUM_TEST_COUNT = 30
ALEXA_APP_PACKAGE_NAME = "com.amazon.dee.app"

# Logger setup
logger = logging.getLogger(__name__)

def setup_logging():
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    time_str = time.strftime("%Y-%m-%d_%H_%M_%S", time.localtime())
    handler = logging.FileHandler(f"log_{time_str}.txt")
    handler.setLevel(logging.INFO)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    logger.addHandler(console)

# UI interaction functions
def ui_click(device, resId, expected_resId=None, timeout_sec=10):
    device(resourceId=resId).click()
    logger.info(f"Clicked on resourceId={resId}, expecting={expected_resId}, timeout={timeout_sec}")
    if not device(resourceId=expected_resId).wait(timeout=timeout_sec):
        logger.error("Failed to get the expected page")
        return False
    return True

def ui_click_id_with_text(device, resId, textstr, expected_resId=None, timeout_sec=10):
    device(resourceId=resId, text=textstr).click()
    logger.info(f"Clicked on resourceId={resId}, text={textstr}, expecting={expected_resId}, timeout={timeout_sec}")
    if not device(resourceId=expected_resId).wait(timeout=timeout_sec):
        logger.error("Failed to get the expected page")
        return False
    return True

def connect_device(serial):
    logger.info("Connecting to device...")
    device = u2.connect_usb(serial)
    logger.info(device.info)
    logger.info("Connected to phone")
    return device

def restart_alexa_app(device):
    logger.info("Restarting Alexa App...")
    device.app_stop(ALEXA_APP_PACKAGE_NAME)
    device.app_start(ALEXA_APP_PACKAGE_NAME)
    logger.info("Waiting for Alexa App to load...")
    time.sleep(6)

def log_error_info(device):
    try:
        error_info = device(resourceId="UGS_ErrorPage").get_text()
        logger.error(f'Error info: {error_info}')
    except Exception:
        logger.error("Could not retrieve error info")

# Test functions
def execute_test_ugs(device, saved_wifi_ssid):
    try:
        logger.info("Starting UGS test...")
        restart_alexa_app(device)
        logger.info("Clicking button '+' ...")
        if not ui_click(device, "com.amazon.dee.app:id/home_header_quick_add", "1-primary", 10):
            logger.error("Unable to see the add device menu.")
            return False

        logger.info("Clicking button 'Add Device' ...")
        if not ui_click(device, "1-primary", "AddDevicesLandingPage", 10):
            logger.error("Unable to see the AddDevicesLandingPage.")
            return False

        logger.info("Scrolling down to find 'Development Device' ...")
        device(scrollable=True).scroll.to(text="Development Device")
        logger.info("Clicking 'Development Device' ...")
        if not ui_click(device, "DeviceTypeRow_Development Device-primary", "DiscoveryBrandSelectionPage", 10):
            logger.error("Unable to see the DiscoveryBrandSelectionPage.")
            return False

        logger.info("Clicking 'ACK' ...")
        if not ui_click(device, "DeviceBrandRow_ACK=0-primary", "mosaic.pages.InstructionalPage-title", 10):
            logger.error("Unable to see the InstructionalPage.")
            return False

        logger.info("Clicking 'Yes' to confirm device is powered on ...")
        if not ui_click_id_with_text(device, "mosaic.base_text", "Yes", "mosaic.pages.InstructionalPage-title", 10):
            logger.error("Unable to see the InstructionalPage (UGS/BCS).")
            return False

        logger.info("Clicking 'Don't Have A Code?' to confirm using UGS ...")
        if not ui_click_id_with_text(device, "mosaic.base_text", "Don't Have A Code?", "mosaic.pages.InstructionalPage-title", 10):
            logger.error("Unable to see the InstructionalPage (pairing mode prompt).")
            return False

        logger.info("Clicking 'Next' to continue ...")
        if not ui_click(device, "mosaic.pages.InstructionalPage-footer-primary-btn", "mosaic.pages.ConfirmationPage-title", 10):
            logger.error("Unable to see the ConfirmationPage.")
            return False

        logger.info("Looking for the device ...")
        if not device(resourceId="mosaic.base_text", text="Looking for your ACK development device").wait_gone(timeout=150):
            logger.error("Unable to find the device.")
            log_error_info(device)
            return False

        logger.info("Connecting to the device ...")
        if not device(resourceId="mosaic.base_text", text="Connecting to your ACK development device").wait_gone(timeout=150):
            logger.error("Unable to connect to the device.")
            log_error_info(device)
            return False

        logger.info("Selecting WiFi ...")
        time.sleep(2)
        device(resourceId="Mosaic.radio_list_item-primary", text=saved_wifi_ssid).click()
        device.xpath('//*[@text="Next"]').click()

        logger.info("Waiting for the device to register ...")
        if not device(resourceId="mosaic.base_text", text="Connecting your ACK development device to ").wait_gone(timeout=150):
            logger.error("Unable to connect the device to WiFi.")
            log_error_info(device)
            return False

        logger.info("Waiting for completion ...")
        if not device.xpath('//*[@resource-id="NewDeviceFoundPage"]').wait(60):
            logger.error("Connecting to the device failed!")
            log_error_info(device)
            return False

        logger.info("UGS is successful!")
        return True

    except Exception:
        logger.error("Exception happened")
        logger.error(traceback.format_exc())
        return False

def execute_factory_reset(device, device_name):
    try:
        logger.info("Factory resetting the device")
        restart_alexa_app(device)
        logger.info("Switching to device page...")
        device.xpath('//*[@resource-id="com.amazon.dee.app:id/tab_channels_device_icon"]').click()
        time.sleep(3)

        device.swipe_ext("down")
        time.sleep(2)
        device.swipe_ext("down")
        time.sleep(3)

        logger.info(f"Locating the device '{device_name}' ...")
        device(scrollable=True).scroll.to(text=device_name)

        logger.info(f"Clicking into the GUI page of the device '{device_name}' ...")
        device(resourceId="mosaic.text", text=device_name).click()

        logger.info(f"Loading the GUI page of the device '{device_name}' ...")
        device.xpath('//*[@content-desc="Settings"]/android.widget.ImageView[1]').wait(60)

        logger.info(f"Clicking the setting button of the device '{device_name}' ...")
        device.xpath('//*[@content-desc="Settings"]/android.widget.ImageView[1]').click()
        device.xpath('//*[@content-desc="Delete"]/android.widget.ImageView[1]').wait(10)

        logger.info(f"Clicking the delete button of the device '{device_name}' ...")
        device.xpath('//*[@content-desc="Delete"]/android.widget.ImageView[1]').click()
        device.xpath('//*[@resource-id="android:id/button1"]').wait(10)

        logger.info(f"Confirming the deletion of the device '{device_name}' ...")
        device.xpath('//*[@resource-id="android:id/button1"]').click()
        time.sleep(2)
        logger.info(f"Device {device_name} is removed from Alexa!")
        return True
    except Exception:
        logger.error("Exception happened")
        logger.error(traceback.format_exc())
        return False

def execute_test_bcs(device, saved_wifi_ssid):
    try:
        logger.info("Starting BCS test...")
        restart_alexa_app(device)
        logger.info("Clicking button '+' ...")
        if not ui_click(device, "com.amazon.dee.app:id/home_header_quick_add", "1-primary", 10):
            logger.error("Unable to see the add device menu.")
            return False

        logger.info("Clicking button 'Add Device' ...")
        if not ui_click(device, "1-primary", "AddDevicesLandingPage", 10):
            logger.error("Unable to see the AddDevicesLandingPage.")
            return False

        logger.info("Scrolling down to find 'Development Device' ...")
        device(scrollable=True).scroll.to(text="Development Device")
        logger.info("Clicking 'Development Device' ...")
        if not ui_click(device, "DeviceTypeRow_Development Device-primary", "DiscoveryBrandSelectionPage", 10):
            logger.error("Unable to see the DiscoveryBrandSelectionPage.")
            return False

        logger.info("Clicking 'ACK' ...")
        if not ui_click(device, "DeviceBrandRow_ACK=0-primary", "mosaic.pages.InstructionalPage-title", 10):
            logger.error("Unable to see the InstructionalPage.")
            return False

        logger.info("Clicking 'Yes' to confirm device is powered on ...")
        if not ui_click_id_with_text(device, "mosaic.base_text", "Yes", "mosaic.pages.InstructionalPage-title", 10):
            logger.error("Unable to see the InstructionalPage (UGS/BCS).")
            return False

        logger.info("Clicking 'Scan Code' to start BCS ...")
        device(resourceId="mosaic.pages.InstructionalPage-footer-primary-btn").click()
        device(resourceId="mosaic.text", text="Scan the 2D barcode for your development device").wait(10)
        time.sleep(2)

        logger.info("Looking for the device ...")
        if not device(resourceId="mosaic.base_text", text="Looking for your ACK development device").wait_gone(timeout=150):
            logger.error("Unable to find the device.")
            log_error_info(device)
            return False

        logger.info("Connecting to the device ...")
        if not device(resourceId="mosaic.base_text", text="Connecting to your ACK development device").wait_gone(timeout=150):
            logger.error("Unable to connect to the device.")
            log_error_info(device)
            return False

        logger.info("Waiting for the device to register ...")
        if not device(resourceId="mosaic.base_text", text="Connecting your ACK development device to ").wait_gone(timeout=150):
            logger.error("Unable to connect the device to WiFi.")
            log_error_info(device)
            return False

        logger.info("Waiting for completion ...")
        if not device.xpath('//*[@resource-id="NewDeviceFoundPage"]').wait(60):
            logger.error("Connecting to the device failed!")
            log_error_info(device)
            return False

        logger.info("BCS is successful!")
        return True

    except Exception:
        logger.error("Exception happened")
        logger.error(traceback.format_exc())
        return False

def execute_test_zts(device, saved_wifi_ssid):
    pass

def main():
    parser = argparse.ArgumentParser(description="Run UGS tests on an Android device.")
    parser.add_argument('--mode', type=str, default="UGS", help='Test mode. Valid values are: UGS, BCS and ZTS.')
    parser.add_argument('--serial', type=str, default=ANDROID_SERIAL, help='The serial number of the Android device.')
    parser.add_argument('--wifi_ssid', type=str, default=SAVED_WIFI_SSID, help='The SSID of the WiFi network to connect to.')
    parser.add_argument('--device_name', type=str, default=DEFAULT_DEVICE_NAME, help='The name of the device on Alexa App.')
    parser.add_argument('--test_count', type=int, default=MAXIMUM_TEST_COUNT, help='The maximum number of tests to run.')

    args = parser.parse_args()

    setup_logging()

    if args.mode not in ['UGS', 'BCS', 'ZTS']:
        logger.error("Please input valid test mode. Valid values are: UGS, BCS and ZTS.")
        return

    success_cnt = 0
    failure_cnt = 0
    for i in range(args.test_count):
        logger.info(f"=================== {args.mode} test {i+1}/{args.test_count} ===================")
        device = connect_device(args.serial)

        if args.mode == 'UGS':
            test_result = execute_test_ugs(device, args.wifi_ssid)
        elif args.mode == 'BCS':
            test_result = execute_test_bcs(device, args.wifi_ssid)
        elif args.mode == 'ZTS':
            test_result = execute_test_zts(device, args.wifi_ssid)

        if test_result:
            success_cnt += 1
            time.sleep(3)
            execute_factory_reset(device, args.device_name)
            time.sleep(3)
        else:
            failure_cnt += 1

        logger.info(f"=======================================================")
        logger.info(f" Execute Summary:")
        logger.info(f" Total executed {args.mode} times: {success_cnt + failure_cnt} / {args.test_count}")
        logger.info(f" Total successful {args.mode}: {success_cnt}")
        logger.info(f" Total failed {args.mode}: {failure_cnt}")
        logger.info(f"=======================================================")

if __name__ == "__main__":
    main()
