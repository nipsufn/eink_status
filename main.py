#!/usr/bin/env python3

import logging
import argparse
import json
import classes.Airly
import classes.CRoJazz
import classes.OpenWeatherMap

import matplotlib
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as ticker
from datetime import datetime, timedelta
import time
from signal import SIGINT, signal
import traceback
from io import BytesIO
import gc

from PIL import Image,ImageDraw,ImageFont

matplotlib.use('Agg')
config = None
with open("config.json", 'r') as configFile:
    config = json.load(configFile)

def stop(singalNumber, frame):
    epd.init();
    epd.sleep();
    exit();

signal(SIGINT, stop)

if __name__ == "__main__":
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
    if not args.no_eink:
        import epd7in5b
        epd = epd7in5b.Epd()
        epd.init()
        epd.Clear("white")
    PaletteImage = Image.open('palette_bwr_bodge.bmp')

    #persist less frequent requests
    weatherJson = None
    cro_jazz = classes.CRoJazz.CRoJazz()
    weather_forecast = classes.OpenWeatherMap.OpenWeatherMap(
        config["forecastLocation"],
        config["forecastToken"]
        )
    smog_status = classes.Airly.Airly(
        config["weatherLocations"],
        config["weatherToken"]
        )
    forecastPlotImage = Image.new('RGB', (720, 200), (0xFF, 0xFF, 0xFF))

    while True:
        cro_jazz.update()
            
        if counter % 10 == 0:
            #those are updated infrequently, no point spamming APIs
            weather_forecast.update()
            smog_status.update()

            #process forecast data
            xAxisTimestamps = []
            xAxisHours = []
            yAxisTemperature =[]
            yAxisPrecipitation = []
            for timestamp in weather_forecast.json['list']:
                xAxisTimestamps.append(timestamp['dt'])
                xAxisHours.append(datetime.fromtimestamp(timestamp['dt']))
                yAxisTemperature.append(timestamp['main']['temp']-273.15)
                precipitationTmp = 0
                if 'rain' in timestamp:
                    precipitationTmp += timestamp['rain']['3h']
                if 'snow' in timestamp:
                    precipitationTmp += timestamp['snow']['3h']
                yAxisPrecipitation.append(precipitationTmp)
            
            tempAndPercipPlot = plt.figure(figsize=(720/80,200/80),dpi=80)
            #plot percipitation
            ax1 = tempAndPercipPlot.add_subplot()
            xfmt1 = mdates.DateFormatter('%a')
            locator1 = mdates.HourLocator(byhour=11)
            ax1.plot(xAxisHours, yAxisPrecipitation, color='black')
            ax1.fill_between(xAxisHours, 0, yAxisPrecipitation, color='black')
            ax1.set_ylim(bottom=0)

            #plot tempertatures
            xfmt2 = mdates.DateFormatter('%H')
            locator2 = mdates.HourLocator(byhour=range(0,24,6))
            ax2 = ax1.twinx()
            ax2.yaxis.tick_left()
            ax2.plot(xAxisHours, yAxisTemperature, color='red')
            ax2.xaxis.set_major_formatter(xfmt2)
            ax2.xaxis.set_major_locator(locator2)

            #grid lines for temperatures
            ax2.grid(True, 'major', 'y', color="black")

            #mark nights
            nightTimestamps = []
            i = 0
            while True:
                breakout = False
                tmpSunset = weather_forecast.sunset + i*86400
                tmpSunrise = weather_forecast.sunrise + (i+1)*86400
                sunset = 0
                if (tmpSunset < xAxisTimestamps[-1] 
                    and tmpSunset > xAxisTimestamps[0]):
                    sunset = tmpSunset
                else:
                    if tmpSunset > xAxisTimestamps[-1]:
                        sunset = xAxisTimestamps[-1]
                        breakout = True
                    if tmpSunset < xAxisTimestamps[0]:
                        sunset = xAxisTimestamps[0]

                sunrise = 0
                if (tmpSunrise < xAxisTimestamps[-1] 
                    and tmpSunrise > xAxisTimestamps[0]):
                    sunrise = tmpSunrise
                else:
                    if tmpSunrise > xAxisTimestamps[-1]:
                        sunrise = xAxisTimestamps[-1]
                        breakout = True
                    if tmpSunrise < xAxisTimestamps[0]:
                        sunrise = xAxisTimestamps[0]


                nightTimestamps.append([sunset, sunrise])
                i += 1
                if breakout:
                    break 

            for nightTimestamp in nightTimestamps:
                ax2.axvspan(
                    datetime.fromtimestamp(nightTimestamp[0]),
                    datetime.fromtimestamp(nightTimestamp[1]),
                    facecolor="none",
                    edgecolor="black",
                    hatch='....'
                    )

            for xAxisHour in xAxisHours:
                if xAxisHour.hour == 1:
                    ax2.axvline(xAxisHour-timedelta(hours=1),
                        ls=':',
                        color="red")

            ax1.xaxis.set_minor_formatter(xfmt1)
            #ax2.xaxis.set_minor_formatter(ticker.NullFormatter())
            ax1.xaxis.set_minor_locator(locator1)
            ax1.tick_params(axis='x',
                which='minor',
                top=False,
                labeltop=True,
                bottom=False,
                labelbottom=False)
            ax1.yaxis.tick_right()
            #fix margins
            plt.margins(x=0)

            #display
            #plt.savefig('figure.png')
            #canvas = plt.get_current_fig_manager().canvas
            forecastCanvas = tempAndPercipPlot.canvas
            forecastCanvas.draw()
            forecastPlotImage = Image.frombytes('RGB', 
                forecastCanvas.get_width_height(),
                forecastCanvas.tostring_rgb())
            #clean up
            plt.close(tempAndPercipPlot)
            gc.collect(2)


        framebufferFont30 = ImageFont.truetype('SourceCodePro-Regular.ttf', 30)
        framebufferFont20 = ImageFont.truetype('SourceCodePro-Regular.ttf', 20)

        framebufferImage = Image.new('RGB', (640, 385), (0xFF, 0xFF, 0xFF))
        framebufferImage.paste(forecastPlotImage, (-50, 185))
        framebufferDraw = ImageDraw.Draw(framebufferImage)
        framebufferDraw.text((10, 0),
            datetime.now().strftime('%Y-%m-%d %H:%M'),
            font=framebufferFont30,
            fill=0)

        jazzString1 = (
            'ČRoJazz: '
            + cro_jazz.programme_title
            + ": "
            + cro_jazz.programme_start
            + " - "
            + cro_jazz.programme_stop
            )
        framebufferDraw.text(
            (10, 40),
            jazzString1,
            font=framebufferFont20,
            fill=0
            )

        jazzString2 = (
            '         '
            + cro_jazz.track_artist
            + " - "
            + cro_jazz.track_title
            )
        framebufferDraw.text(
            (10, 70),
            jazzString2,
            font=framebufferFont20,
            fill=0
            )

        dustString = (
            'Dust:    '
            + str(smog_status.pm001)
            + "/"
            + str(smog_status.pm025)
            + "/"
            + str(smog_status.pm100)
            )
        dustColor = (0,0,0) if smog_status.isAirOK() else (255,0,0)
        framebufferDraw.text(
            (10, 100),
            dustString,
            font=framebufferFont20,
            fill=dustColor
            )
        framebufferDraw.text(
            (10, 130),
            'Temp:    '+str(smog_status.temp)+"°",
            font=framebufferFont20,
            fill=0)

        #sanitize image palette
        framebufferImage = framebufferImage.quantize(palette=PaletteImage)
        
        if args.image:
            framebufferImage.save(args.image);
        if not args.no_eink:
            epd.Display(framebufferImage)
            epd.sleep()
        counter = counter + 1
        time.sleep(60)

