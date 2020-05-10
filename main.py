#!/usr/bin/env python3

import sys
import logging
import argparse
import json
from datetime import datetime
import time
from signal import SIGINT, signal
from PIL import Image, ImageDraw, ImageFont

import classes.airly
import classes.c_ro_jazz
import classes.open_weather_map

NO_EINK = False

def stop(singal_id, frame):
    # pylint: disable-msg=unused-argument
    # signal handler has to take two arguments
    # pylint: disable-msg=import-outside-toplevel
    # this module has RPI-specific module dependencies
    # and should not be loaded in save-to-image mode
    
    global NO_EINK
    if NO_EINK:
        import epd7in5b
        epd = epd7in5b.Epd()
        epd.init()
        epd.sleep()
        sys.exit()

signal(SIGINT, stop)

def main():
    # pylint: disable-msg=import-outside-toplevel
    # epd7in5b module has RPI-specific module dependencies
    # and should not be loaded in save-to-image mode

    config = None
    with open("config.json", 'r') as config_file:
        config = json.load(config_file)
    logger = logging.getLogger('eink_status')
    log_handler = logging.StreamHandler()
    log_handler.setFormatter(
        logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
        )
    logger.addHandler(log_handler)
    logger.setLevel(logging.DEBUG)
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--image", type=str,
                        help="save to image")
    parser.add_argument("-n", "--no-eink", action="store_true",
                        help="don't use e-ink display")
    args = parser.parse_args()
    counter = 0
    if args.no_eink:
        global NO_EINK
        NO_EINK = True
    else:
        import epd7in5b
        epd = epd7in5b.Epd()
        epd.init()
        epd.Clear("white")
    palette_image = Image.open('palette_bwr_bodge.bmp')

    # persist less frequent requests
    cro_jazz = classes.c_ro_jazz.CRoJazz()
    weather_forecast = classes.open_weather_map.OpenWeatherMap(
        config["forecastLocation"],
        config["forecastToken"]
        )
    smog_status = classes.airly.Airly(
        config["dustLocations"],
        config["dustToken"]
        )
    forecast_plot_image = Image.new('RGB', (720, 200), (0xFF, 0xFF, 0xFF))

    while True:
        cro_jazz.update()
        update_display = cro_jazz.changed
        if counter % 60 == 0:
            # those are updated infrequently, no point spamming APIs
            weather_forecast.update()
            smog_status.update()
            forecast_plot_image = weather_forecast.plot(720, 200)
            update_display = True

        framebuffer_font_30 = ImageFont.truetype('SourceCodePro-Regular.ttf',
                                                 30)
        framebuffer_font_20 = ImageFont.truetype('SourceCodePro-Regular.ttf',
                                                 20)

        framebuffer_image = Image.new('RGB', (640, 385), (0xFF, 0xFF, 0xFF))
        framebuffer_image.paste(forecast_plot_image, (-50, 185))
        framebuffer_draw = ImageDraw.Draw(framebuffer_image)
        framebuffer_draw.text((10, 0),
                              datetime.now().strftime('%Y-%m-%d'),
                              font=framebuffer_font_30, fill=0)

        jazz_string_1 = ('ČRoJazz: '+ cro_jazz.programme_title + ": "
                          + cro_jazz.programme_start + " - "
                          + cro_jazz.programme_stop)
        framebuffer_draw.text((10, 40), jazz_string_1,
                              font=framebuffer_font_20, fill=0)

        jazz_string_2 = ('         ' + cro_jazz.track_artist + " - "
                         + cro_jazz.track_title)
        framebuffer_draw.text((10, 70), jazz_string_2, font=framebuffer_font_20,
                              fill=0)

        dust_string = ('Dust:    ' + str(smog_status.pm001) + "/"
                       + str(smog_status.pm025) + "/" + str(smog_status.pm100))

        dust_string_color = (0, 0, 0) if smog_status.isAirOK() else (255, 0, 0)
        framebuffer_draw.text((10, 100), dust_string, font=framebuffer_font_20,
                              fill=dust_string_color)
        framebuffer_draw.text((10, 130), 'Temp:    '+str(smog_status.temp)+"°",
                              font=framebuffer_font_20, fill=0)

        # sanitize image palette
        framebuffer_image = framebuffer_image.quantize(palette=palette_image)
        if update_display:
            if args.image:
                framebuffer_image.save(args.image)
            if not args.no_eink:
                epd.Display(framebuffer_image)
                #epd.sleep()
        counter = counter + 1
        time.sleep(60)

if __name__ == "__main__":
    main()
