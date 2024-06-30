# coding: utf-8
#

import uiautomator2 as u2
import logging
import traceback
import time

ANDROID_SERIAL = "4fe9718b"
DEFAULT_DEVICE_NAME = "First light"
MAXIMUM_TEST_COUNT = 60

ALEXA_APP_PACKAGE_NAME = "com.amazon.dee.app"

logger = logging.getLogger(__name__)

def ui_click(device, resId, expected_resId=None, timeout_sec=10):
    device(resourceId=resId).click()
    logger.info(f"click on resourceId={resId}, expect={expected_resId}, timeout={timeout_sec}")
    if device(resourceId=expected_resId).wait(timeout=timeout_sec) is not True:
        logger.error("failed to get the expected page")
        return False
    return True

def ui_click_id_with_text(device, resId, textstr, expected_resId=None, timeout_sec=10):
    device(resourceId=resId, text=textstr).click()
    logger.info(f"click on resourceId={resId}, text={textstr}, expect={expected_resId}, timeout={timeout_sec}")
    if device(resourceId=expected_resId).wait(timeout=timeout_sec) is not True:
        logger.error("failed to get the expected page")
        return False
    return True

def TEST_BCS():
    try:
        logger.info("starting BCS test...")
        d = u2.connect_usb(ANDROID_SERIAL)
        logger.info(d.info)
        logger.info("connected to phone")

        # start Alexa App
        logger.info("Restarting Alexa App...")
        d.app_stop(ALEXA_APP_PACKAGE_NAME) 
        d.app_start(ALEXA_APP_PACKAGE_NAME)

        #TODO: worth adding a little bit more
        logger.info("waiting for Alexa App to load...")
        time.sleep(6)

        # close GD/AD
        # if d(resourceId="gd-cancel-icon") is not None:
        #     d(resourceId="gd-cancel-icon").click()
        #     time.sleep(2)
        #     d.swipe_ext("down")
        #     time.sleep(2)        
        # if d(resourceId="FullScreenTakeover::PrimaryImage") is not None:
        #     if d(text="LATER") is not None:
        #         d(text="LATER").click()
        #     if d(resourceId="FullScreenTakeover::SecondaryButton") is not None:
        #         d(resourceId="FullScreenTakeover::SecondaryButton").click()
        #     time.sleep(2)
        #     d.swipe_ext("down")
        #     time.sleep(2)

        # add device
        #TODO: adjust the timeout
        logger.info("clicking button '+' ...")
        if ui_click(d, "com.amazon.dee.app:id/home_header_quick_add", "1-primary", 10) is not True:
            logger.error("Unable to see the add device menu. Please make sure you have logged in Alexa App and the network is in good condition.")
            return False

        # test UGS with development device
        time.sleep(2)
        logger.info("clicking button 'Add Device' ...")
        if ui_click(d, "1-primary", "AddDevicesLandingPage", 10) is not True:
            logger.error("Unable to see the AddDevicesLandingPage. Please make sure you have logged in Alexa App and the network is in good condition.")
            return False    

        logger.info("scrolling down to find 'Development Device' ...")
        d(scrollable=True).scroll.to(text="Development Device")
        logger.info("clicking 'Development Device' ...")
        if ui_click(d, "DeviceTypeRow_Development Device-primary", "DiscoveryBrandSelectionPage", 10) is not True:
            logger.error("Unable to see the DiscoveryBrandSelectionPage. Please make sure you have logged in Alexa App and the network is in good condition.")
            return False

        logger.info("clicking 'ACK' ...")
        if ui_click(d, "DeviceBrandRow_ACK=0-primary", "mosaic.pages.InstructionalPage-title", 10) is not True:
            logger.error("Unable to see the InstructionalPage. Please make sure you have logged in Alexa App and the network is in good condition.")
            return False

        logger.info("clicking 'Yes' to confirm device is powered on ...")
        if ui_click_id_with_text(d, "mosaic.base_text", "Yes", "mosaic.pages.InstructionalPage-title", 10) is not True:
            logger.error("Unable to see the InstructionalPage(UGS/BCS). Please make sure you have logged in Alexa App and the network is in good condition.")
            return False

        logger.info("clicking 'Scan Code' to start BCS ...")
        d(resourceId="mosaic.pages.InstructionalPage-footer-primary-btn").click()
        d(resourceId="mosaic.text", text="Scan the 2D barcode for your development device").wait(10)
        time.sleep(2)

        #TODO: adjust the timeout
        # Looking for the device
        logger.info("Looking for the device ...")
        if d(resourceId="mosaic.base_text", text="Looking for your ACK development device").wait_gone(timeout=150) is not True:
            logger.error("Unable to find the device. Please make sure the device is in setup mode.")
            logger.error(f'Error info: {d(resourceId="UGS_ErrorPage").get_text()}')
            return False

        # connecting to the device
        logger.info("Connecting to the device ...")
        if d(resourceId="mosaic.base_text", text="Connecting to your ACK development device").wait_gone(timeout=150) is not True:
            logger.error("Unable to connect to the device. Please make sure the device is in setup mode.")
            logger.error(f'Error info: {d(resourceId="UGS_ErrorPage").get_text()}')
            return False
        
        logger.info("Waiting for the device to register ...")
        if d(resourceId="mosaic.base_text", text="Connecting your ACK development device to ").wait_gone(timeout=150) is not True:
            logger.error("Unable to connect the device to WiFI. Please check if you have saved the WiFi credentials to Amazon.")
            logger.error(f'Error info: {d(resourceId="UGS_ErrorPage").get_text()}')
            return False            

        #TODO: adjust the timeout
        logger.info("Waiting for completion ...")
        if d.xpath('//*[@resource-id="NewDeviceFoundPage"]').wait(60) is not True:
            logger.error("Connecting to the device failed! Please check your network and make sure you are using the Alexa account which matches the target marketplace.")
            logger.error(f'Error info: {d(resourceId="UGS_ErrorPage").get_text()}')
            return False

        logger.info("BCS is successful!")
        return True

    except Exception as e:
        logger.error("exception happened")
        logger.error(traceback.format_exc())
        return False

def TEST_FactoryReset():
    try:
        logger.info("Factory reset the device")
        d = u2.connect_usb(ANDROID_SERIAL)
        logger.info(d.info)
        logger.info("connected to phone")

        # start Alexa App
        logger.info("Restarting Alexa App ...")
        d.app_stop(ALEXA_APP_PACKAGE_NAME) 
        d.app_start(ALEXA_APP_PACKAGE_NAME)

        #TODO: worth adding a little bit more
        logger.info("waiting for Alexa App to load...")
        time.sleep(5)

        # close GD/AD
        # if d(resourceId="gd-cancel-icon") is not None:
        #     d(resourceId="gd-cancel-icon").click()
        #     time.sleep(2)
        #     d.swipe_ext("down")
        #     time.sleep(2)        
        # if d(resourceId="FullScreenTakeover::PrimaryImage") is not None:
        #     if d(text="LATER") is not None:
        #         d(text="LATER").click()
        #     if d(resourceId="FullScreenTakeover::SecondaryButton") is not None:
        #         d(resourceId="FullScreenTakeover::SecondaryButton").click()
        #     time.sleep(2)
        #     d.swipe_ext("down")
        #     time.sleep(2)

        logger.info("switching to device page...")
        d.xpath('//*[@resource-id="com.amazon.dee.app:id/tab_channels_device_icon"]').click()
        time.sleep(3)

        d.swipe_ext("down")
        time.sleep(2)
        d.swipe_ext("down")
        time.sleep(3)

        logger.info(f"locating the device '{DEFAULT_DEVICE_NAME}' ...")
        d(scrollable=True).scroll.to(text=DEFAULT_DEVICE_NAME)

        logger.info(f"click into the GUI page of the device '{DEFAULT_DEVICE_NAME}' ...")
        d(resourceId="mosaic.text", text=DEFAULT_DEVICE_NAME).click()

        logger.info(f"loading the GUI page of the device '{DEFAULT_DEVICE_NAME}' ...")
        #TODO: adjust the timeout
        d.xpath('//*[@content-desc="Settings"]/android.widget.ImageView[1]').wait(60)

        logger.info(f"clicking the setting button of the device '{DEFAULT_DEVICE_NAME}' ...")
        d.xpath('//*[@content-desc="Settings"]/android.widget.ImageView[1]').click()
        d.xpath('//*[@resource-id="SettingPageShowAliasCellDisplayName::Second light-primary"]').wait(10)

        logger.info(f"clicking the delete button of the device '{DEFAULT_DEVICE_NAME}' ...")
        d.xpath('//*[@content-desc="Delete"]/android.widget.ImageView[1]').click()

        logger.info(f"confirm the deletion of the device '{DEFAULT_DEVICE_NAME}' ...")
        d.xpath('//*[@resource-id="android:id/button1"]').click()
        time.sleep(2)
        logger.info(f"Device {DEFAULT_DEVICE_NAME} is removed from Alexa!")

        return True
    except Exception as e:
        logger.error("exception happened")
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    logger.setLevel(level = logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    time_str = time.strftime("%Y-%m-%d_%H_%M_%S", time.localtime())
    handler = logging.FileHandler(f"log_{time_str}.txt")
    handler.setLevel(logging.INFO)
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    logger.addHandler(console)

    success_cnt = 0
    failure_cnt = 0
    for i in range(MAXIMUM_TEST_COUNT):
        logger.info(f"=================== BCS test {i+1}/{MAXIMUM_TEST_COUNT} ===================")
        if TEST_BCS() == True:
            success_cnt = success_cnt + 1

            # cleanup for the next test
            time.sleep(5)
            TEST_FactoryReset()            
        else:
            failure_cnt = failure_cnt + 1

        logger.info(f"=======================================================")
        logger.info(f" Execute Summary:")
        logger.info(f" Total executed BCS times: {success_cnt + failure_cnt} / {MAXIMUM_TEST_COUNT}")
        logger.info(f" Total successful BCS: {success_cnt}")
        logger.info(f" Total failed BCS: {failure_cnt}")
        logger.info(f"=======================================================")