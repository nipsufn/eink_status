#!/usr/bin/env python3
"""Draw information on e-ink"
"""
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
    """Handle interrupt signal
    Args:
        signal_id (int)
        frame (:object:)
    """
    # pylint: disable-msg=unused-argument
    # signal handler has to take two arguments
    # pylint: disable-msg=import-outside-toplevel
    # this module has RPI-specific module dependencies
    # and should not be loaded in save-to-image mode
    global NO_EINK
    if NO_EINK:
        sys.exit()
    else:
        import epd7in5b
        epd = epd7in5b.Epd()
        epd.init()
        epd.sleep()
        sys.exit()

def draw(config, epd, args, logger):
    """Draw information
    Args:
        args (:object:): argparse object
        logger (:object:): logger object
    """

    # persist less frequent requests
    cro_jazz = classes.c_ro_jazz.CRoJazz()
    weather_forecast = classes.open_weather_map.OpenWeatherMap(
        config["forecastLocation"],
        config["forecastToken"]
        )
    smog_status = classes.airly.Airly(
        config["smogLocations"],
        config["smogToken"]
        )

    counter = 0
    while True:
        cro_jazz.update()
        update_display = cro_jazz.changed
        if counter % 60 == 0:
            # those are updated infrequently, no point spamming APIs
            weather_forecast.update()
            smog_status.update()
            forecast_plot_image = weather_forecast.plot(430, 200)
            update_display = True

        framebuffer_font_big = ImageFont.truetype('SourceCodePro-Regular.ttf',
                                                  20)
        framebuffer_font_small = ImageFont.truetype('SourceCodePro-Regular.ttf',
                                                    12)

        framebuffer_image = Image.new('RGB', (385, 640), (0xFF, 0xFF, 0xFF))
        framebuffer_image.paste(forecast_plot_image, (-25, 430))
        framebuffer_draw = ImageDraw.Draw(framebuffer_image)
        framebuffer_draw.text((10, 0),
                              datetime.now().strftime('%Y-%m-%d'),
                              font=framebuffer_font_big, fill=0)

        text_line = ('ČRoJazz: '+ cro_jazz.programme_title + ": "
                     + cro_jazz.programme_start + " - "
                     + cro_jazz.programme_stop)
        framebuffer_draw.text((10, 25), text_line,
                              font=framebuffer_font_small, fill=0)

        text_line = ('    ' + cro_jazz.track_artist + " - "
                     + cro_jazz.track_title)
        framebuffer_draw.text((10, 25+16), text_line,
                              font=framebuffer_font_small, fill=0)

        text_line = ('Smog:    ' + str(smog_status.pm001) + "/"
                     + str(smog_status.pm025) + "/" + str(smog_status.pm100))

        dust_string_color = (0, 0, 0) if smog_status.is_air_ok() else (255, 0, 0)
        framebuffer_draw.text((10, 25+16*2), text_line,
                              font=framebuffer_font_small,
                              fill=dust_string_color)
        text_line = 'Temp:    '+str(smog_status.temp)+"°"
        framebuffer_draw.text((10, 25+16*3), text_line,
                              font=framebuffer_font_small, fill=0)

        # sanitize image palette
        framebuffer_image = framebuffer_image.quantize(
            palette=Image.open('palette_bwr_bodge.bmp'))
        if update_display:
            if args.image:
                framebuffer_image.save(args.image)
            if not args.no_eink:
                epd.Display(framebuffer_image.rotate(90))
                #epd.sleep()
        counter = counter + 1
        time.sleep(60)

def main():
    """Main function
    """
    # pylint: disable-msg=import-outside-toplevel
    # epd7in5b module has RPI-specific module dependencies
    # and should not be loaded in save-to-image mode

    config = None
    with open("config.json", 'r') as config_file:
        config = json.load(config_file)

    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--image", type=str,
                        help="save to image")
    parser.add_argument("-n", "--no-eink", action="store_true",
                        help="don't use e-ink display")
    parser.add_argument("-d", "--debug", "-v", "--verbose", action="store_true",
                        help="debug mode")
    args = parser.parse_args()

    logger = logging.getLogger('eink_status')
    log_handler = logging.StreamHandler()
    log_handler.setFormatter(
        logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
        )
    logger.addHandler(log_handler)
    if args.debug:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    epd = None
    if args.no_eink:
        global NO_EINK
        NO_EINK = True
    else:
        import epd7in5b
        epd = epd7in5b.Epd()
        epd.init()
        epd.Clear("white")

    signal(SIGINT, stop)

    draw(config, epd, args, logger)

if __name__ == "__main__":
    main()
