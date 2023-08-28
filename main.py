import time
import pywinauto
import mss
import cv2
import os
import argparse
from screeninfo import get_monitors


def capture_main_screen_mss():
    main_monitor = None
    for monitor in get_monitors():
        if monitor.x == 0 and monitor.y == 0:
            main_monitor = monitor
            break

    if main_monitor is None:
        print("Main monitor not found. Using the first monitor.")
        main_monitor = get_monitors()[0]

    with mss.mss() as sct:
        monitor = {
            'top': main_monitor.y,
            'left': main_monitor.x,
            'width': main_monitor.width,
            'height': main_monitor.height
        }
        screenshot = sct.grab(monitor)
        mss.tools.to_png(screenshot.rgb, screenshot.size, output='images/screen.png')


def find_subimage_in_image(main_image_path, sub_image_path):
    # Read the main image and sub-image
    main_image = cv2.imread(main_image_path, cv2.IMREAD_COLOR)
    sub_image = cv2.imread(sub_image_path, cv2.IMREAD_COLOR)

    # Check if the images exist
    if main_image is None:
        return "Main image not found."
    if sub_image is None:
        return "Sub-image not found."

    # Convert images to grayscale
    main_image_gray = cv2.cvtColor(main_image, cv2.COLOR_BGR2GRAY)
    sub_image_gray = cv2.cvtColor(sub_image, cv2.COLOR_BGR2GRAY)

    # Apply smoothing
    main_image_gray = cv2.GaussianBlur(main_image_gray, (5, 5), 0)
    sub_image_gray = cv2.GaussianBlur(sub_image_gray, (5, 5), 0)

    # Perform template matching
    result = cv2.matchTemplate(main_image_gray, sub_image_gray, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

    # Thresholding (optional)
    threshold = 0.8
    print(f"Max value: {max_val}, Threshold: {threshold}")
    if max_val < threshold:
        print("No match found.")
        return None, None

    # Get the top-left corner of the matched area
    top_left = max_loc
    h, w = sub_image_gray.shape

    # Calculate the center of the matched area
    center_x = top_left[0] + w // 2
    center_y = top_left[1] + h // 2

    return center_x, center_y


def find_btn(btn_name, index=0) -> tuple:
    if index > 9:
        return None, None
    capture_main_screen_mss()
    main_image_path = "images/screen.png"
    btn_image_path = f"images/{btn_name}.png"
    if not os.path.exists(main_image_path):
        print("Main image path does not exist.")
    elif not os.path.exists(btn_image_path):
        print("Sub image path does not exist.")
    else:
        center_x, center_y = find_subimage_in_image(main_image_path, btn_image_path)
        if center_x is None or center_y is None:
            print(f"Low match value for {btn_name} retrying...")
            time.sleep(5)
            return find_btn(btn_name, index + 1)
        print(f"The center of the {btn_name} is located at ({center_x}, {center_y}).")
        return center_x, center_y


def wait_and_click(w, btn, delay=1, repeat_after=-1):
    time.sleep(delay)
    w.set_focus()
    coords = find_btn(btn)
    if coords is None:
        return False
    w.click_input(coords=coords)
    if repeat_after > 0:
        time.sleep(repeat_after)
        w.click_input(coords=coords)
    return True


def get_window() -> pywinauto.application.WindowSpecification:
    app = pywinauto.Application(backend='win32').connect(title_re="Grand Fantasia")
    window = app.window(title_re="Grand Fantasia")
    window.set_focus()
    return window


def train_sprite(window, times, train_delay):
    for i in range(times):
        check = wait_and_click(window, 'train_btn', 2)
        if not check:
            break
        check = wait_and_click(window, 'train_ok_btn', 2)
        if not check:
            break
        wait_and_click(window, 'finish_ok_btn', train_delay, repeat_after=5)
        if not check:
            break


def collect_sprite(window, times, collect_delay):
    for i in range(times):
        check = wait_and_click(window, 'collect_btn', 2)
        if not check:
            break
        check = wait_and_click(window, 'train_ok_btn', 2)
        if not check:
            break
        wait_and_click(window, 'finish_ok_btn', collect_delay, repeat_after=5)
        if not check:
            break


def main(times, delay, mode):
    window = get_window()
    if mode == 'train':
        train_sprite(window, times, delay)
    elif mode == 'collect':
        wait_and_click(window, 'collect_btn', 2)
        wait_and_click(window, 'collect_ok_btn', 2)
    else:
        print("Invalid mode.")
    print("Done.")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Train your scripts in Grand Fantasia.')
    parser.add_argument('--times', type=int, default=1, help='Number of times to repeat the process.')
    parser.add_argument('--delay', type=int, default=45, help='Delay between training and collecting.')
    parser.add_argument('--mode', type=str, default='train', help='Mode of the script.')

    args = parser.parse_args()

    main(times=args.times, delay=args.delay, mode=args.mode)
