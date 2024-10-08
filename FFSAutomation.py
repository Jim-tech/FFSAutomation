import argparse
import uiautomator2 as u2
import logging
import traceback
import time

# Constants
ANDROID_SERIAL = "4fe9718b"
SAVED_WIFI_SSID = "test-xxzhkcgj"
DEFAULT_DEVICE_NAME = "Second plug"
MAXIMUM_TEST_COUNT = 30
ALEXA_APP_PACKAGE_NAME = "com.amazon.dee.app"

# Logger setup
logger = logging.getLogger(__name__)

def setup_logging(mode):
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    time_str = time.strftime("%Y-%m-%d_%H_%M_%S", time.localtime())
    handler = logging.FileHandler(f"log_{mode}_{time_str}.txt")
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
        logger.error(traceback.format_exc())

def log_error_info_for_matter(device):
    try:
        error_info = device(resourceId="mosaic.base_text").get_text()
        logger.error(f'Info about last page: {error_info}')
    except Exception:
        logger.error("Could not retrieve error info")
        logger.error(traceback.format_exc())

def handle_lts_card(device):
    try:
        if device.exists(resourceId="FullScreenTakeover::PrimaryButton"):
            device(resourceId="FullScreenTakeover::PrimaryButton").click()
            device(resourceId="FullScreenTakeover::PrimaryButton").wait_gone(2)
        if device.exists(text="LATER"):
            device(text="LATER").click()
            device(text="LATER").wait_gone(2)
        pass
    except Exception:
        logger.error("Could not handle lts card")
        logger.error(traceback.format_exc())

# Test functions
def execute_test_ugs(device, saved_wifi_ssid):
    try:
        logger.info("Starting UGS test...")
        restart_alexa_app(device)
        handle_lts_card(device)
        
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

def execute_test_bcs(device, saved_wifi_ssid):
    try:
        logger.info("Starting BCS test...")
        restart_alexa_app(device)
        handle_lts_card(device)
        
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

def execute_device_discovering(device):
    try:
        logger.info("Starting discovering...")        
        restart_alexa_app(device)
        logger.info("Switching to device page...")
        device.xpath('//*[@resource-id="com.amazon.dee.app:id/tab_channels_device_icon"]').click()
        time.sleep(3)
        handle_lts_card(device)

        device(resourceId="com.amazon.dee.app:id/fab").wait(10)
        device(resourceId="com.amazon.dee.app:id/fab").click()
        device.clear_text()
        device.send_keys("discover device")
        device.send_action()

        return True
    except Exception:
        logger.error("Exception happened")
        logger.error(traceback.format_exc())
        return False

def execute_test_zts(device, device_name):
    try:
        logger.info("Starting ZTS test...")
        if execute_device_discovering(device) is True:
            time.sleep(2)
        else:
            logger.error(f"failed to start device discovering.")
            return False
        
        restart_alexa_app(device)
        logger.info("Switching to device page...")
        device.xpath('//*[@resource-id="com.amazon.dee.app:id/tab_channels_device_icon"]').click()
        time.sleep(3)
        handle_lts_card(device)

        time_passed = 0
        while time_passed < 60:
            device.swipe_ext("down")
            time.sleep(2)
            time_passed = time_passed + 2

            handle_lts_card(device)

            if device.exists(resourceId="mosaic.text", text=device_name):
                logger.info(f"Target device {device_name} found!")
                return True

        logger.error(f"Target device {device_name} not found during 60s.")
        return False
    except Exception:
        logger.error("Exception happened")
        logger.error(traceback.format_exc())
        return False

def execute_test_matter(device, saved_wifi_ssid, pairing_code_11d):
    try:
        logger.info("Starting Matter setup test...")
        restart_alexa_app(device)
        logger.info("Clicking button '+' ...")
        if not ui_click(device, "com.amazon.dee.app:id/home_header_quick_add", "1-primary", 10):
            logger.error("Unable to see the add device menu.")
            return False

        time.sleep(1)

        logger.info("Clicking button 'Add Device' ...")
        if not ui_click(device, "1-primary", "AddDevicesLandingPage", 10):
            logger.error("Unable to see the AddDevicesLandingPage.")
            return False

        logger.info("Scrolling down to find 'Other' ...")
        # device(scrollable=True).scroll.to(steps=20, text="Other")
        device(scrollable=True).scroll.toEnd()
        time.sleep(3)
        logger.info("Clicking 'Other' ...")
        if not ui_click(device, "DeviceTypeRow_Other-primary", "mosaic-tiles_grid_0_genericMatter", 10):
            logger.error("Unable to see the Generic Matter icon.")
            return False
        time.sleep(1)

        logger.info("Clicking 'Matter' ...")
        device(resourceId="mosaic-tiles_grid_0_genericMatter").click()
        device(resourceId="mosaic.base_text", text="Does your device have a Matter logo?").wait(10)
        if not ui_click_id_with_text(device, "mosaic.base_text", "YES", "power-on-check-footer-primary-btn", 10):
            logger.error("Unable to see the InstructionalPage.")
            return False

        logger.info("Clicking 'Yes' to confirm device is powered on ...")
        if not ui_click(device, "power-on-check-footer-primary-btn", "locate-qr-code-page-footer-secondary-btn", 10):
            logger.error("Unable to see the InstructionalPage (Locate QR code).")
            return False

        logger.info("Clicking 'Try Numeric Code Instead?' to confirm using digital pairing code ...")
        if not ui_click(device, "locate-qr-code-page-footer-secondary-btn", "locate-numerical-code-page-footer-primary-btn", 10):
            logger.error("Unable to see the InstructionalPage (Locate the numeric code).")
            return False

        logger.info("Clicking 'Enter Code' to continue ...")
        if not ui_click(device, "locate-numerical-code-page-footer-primary-btn", "input-numeric-code-page-BodyText", 10):
            logger.error("Unable to see the page containing the input box for the numeric code.")
            return False

        # input the code
        device.xpath('//android.widget.ScrollView/android.view.ViewGroup[1]/android.view.ViewGroup[1]').click()
        device.clear_text()
        logger.info(f"The 11-digits pairing code is: {pairing_code_11d}")
        device.send_keys(f"{pairing_code_11d}")
        device.send_action()
        time.sleep(1)

        logger.info("Clicking 'Next' to continue ...")
        device(resourceId="input-numeric-code-page-footer-primary-btn").click()
        device(resourceId="input-numeric-code-page-footer-primary-btn").wait_gone(2)

        logger.info("Looking for the device ...")
        device(resourceId="mosaic.base_text", text="Looking for your device").wait(timeout=10)
        if not device(resourceId="mosaic.base_text", text="Looking for your device").wait_gone(timeout=30):
            logger.error("Unable to find the device.")
            log_error_info_for_matter(device)
            return False

        if device.exists(resourceId="mosaic.base_text", text="Still looking for your device"):
            logger.info("Still looking for the device ...")
            if not device(resourceId="mosaic.base_text", text="Still looking for your device").wait_gone(timeout=30):
                logger.error("Unable to find the device after long retry.")
                log_error_info_for_matter(device)
                return False
            else:
                logger.info("Looking for the device ended...")
                if device.exists(resourceId="mosaic.base_text", text="Is this device set up for control with another assistant or app?"):
                    logger.error("Unable to find the device after final retry.")
                    log_error_info_for_matter(device)
                    return False

        logger.info("Connecting to the device...")
        if not device(resourceId="mosaic.base_text", text="Connecting to your device").wait_gone(timeout=30):
            logger.error("Unable to connect to the device.")
            log_error_info_for_matter(device)
            return False

        logger.info("Connecting the device to the network...")
        if not device(resourceId="mosaic.base_text", text="Connecting your device to the network").wait_gone(timeout=30):
            logger.error("Unable to connect the device to the network.")
            log_error_info_for_matter(device)
            return False

        logger.info("Waiting for the msg `Alexa is getting your device ready` ...")
        if not device(resourceId="mosaic.base_text", text="Alexa is getting your device ready").wait_gone(timeout=30):
            logger.error("Unable to see the msg `Alexa is getting your device ready`.")
            log_error_info_for_matter(device)
            return False

        logger.info("Waiting for completion ...")
        if not device(resourceId="commissioning-complete-page").wait(60):
            logger.error("Connecting to the device failed!")
            log_error_info_for_matter(device)
            return False

        logger.info("Matter setup is successful!")
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

def main():
    parser = argparse.ArgumentParser(description="Run FFS tests on an Android device.")
    parser.add_argument('--mode', type=str, default="UGS", help='Test mode. Valid values are: UGS, BCS, ZTS and Matter. Here: 1)UGS and BCS are for non-Matter ACK devices. 2)ZTS is for both Matter and non-Matter. 3)Matter is only for Matter device')
    parser.add_argument('--serial', type=str, default=ANDROID_SERIAL, help='The serial number of the Android device.')
    parser.add_argument('--wifi_ssid', type=str, default=SAVED_WIFI_SSID, help='The SSID of the WiFi network to connect to.')
    parser.add_argument('--device_name', type=str, default=DEFAULT_DEVICE_NAME, help='The name of the device on Alexa App.')
    parser.add_argument('--test_count', type=int, default=MAXIMUM_TEST_COUNT, help='The maximum number of tests to run.')
    parser.add_argument('--pairing_code_11d', type=int, default=None, help='The 11-digits Matter pairing code')

    args = parser.parse_args()

    setup_logging(args.mode)

    if args.mode not in ['UGS', 'BCS', 'ZTS', 'Matter']:
        logger.error("Please input valid test mode. Valid values are: UGS, BCS, ZTS and Matter.")
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
            test_result = execute_test_zts(device, args.device_name)
        elif args.mode == 'Matter':
            test_result = execute_test_matter(device, args.wifi_ssid, args.pairing_code_11d)

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
