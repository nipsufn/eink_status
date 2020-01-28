#!/usr/bin/env python3

import requests
import json
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as ticker
from datetime import datetime, timedelta
import time
from signal import SIGINT, signal
import traceback
from io import BytesIO
import epd7in5b
import gc

from PIL import Image,ImageDraw,ImageFont

matplotlib.use('Agg')
config = None
with open("config.json", 'r') as configFile:
    config = json.load(configFile)

kelvinOffset = float(config["kelvinOffset"])
forecastLocation = config["forecastLocation"]
forecastToken = config["forecastToken"]
weatherLocations = config["weatherLocations"]
weatherToken = config["weatherToken"]

epd = epd7in5b.Epd()

def elvis(a, b):
    if a:
        return a
    return b

def getJsonFromUrl(url, timeout=10):
    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
    except requests.exceptions.ConnectionError as error:
        print("HTTP connection error!\n"+str(error))
        return None
    except requests.exceptions.Timeout as error:
        print("HTTP timeout!\n"+str(error))
        return None
    except requests.exceptions.HTTPError as error:
        print("HTTP timeout!\n"+str(error))
        return None
    if response.content == None:
        print("Undefined error!\n")
        return None
    return json.loads(response.content)

def stop():
    epd.init();
    epd.sleep();
    exit();

signal(SIGINT, stop)
if __name__ == "__main__":
    counter = 0
    epd.init()
    epd.Clear("white")
    PaletteImage = Image.open('palette_bwr_bodge.bmp')

    #persist less frequent requests
    forecastJson = None
    weatherJson = None
    jazzJson1 = None
    jazzJson2 = None
    forecastPlotImage = Image.new('RGB', (720, 200), (0xFF, 0xFF, 0xFF))

    while True:
        epd.init()
        jazzJson1 = elvis(getJsonFromUrl("https://croapi.cz/data/v2/schedule/now/1/jazz.json"), jazzJson1)
        jazzJson2 = elvis(getJsonFromUrl("https://croapi.cz/data/v2/playlist/now/jazz.json"), jazzJson2)
            
        if counter % 10 == 0:
            #those are updated infrequently, no point spamming APIs
            forecastUrl = "http://api.openweathermap.org/data/2.5/forecast?q=" \
                + forecastLocation \
                + "&APPID=" \
                + forecastToken
            forecastJson = elvis(getJsonFromUrl(forecastUrl), forecastJson)
            for weatherLocation in weatherLocations:
                weatherUrl = "https://airapi.airly.eu/v2/measurements/installation?installationId=" \
                    + weatherLocation \
                    + "&apikey=" \
                    + weatherToken
                weatherJsonTmp = getJsonFromUrl(weatherUrl)
                if weatherJsonTmp is not None and weatherJsonTmp['current']['indexes'][0]['value'] is not None:
                    weatherJson = weatherJsonTmp
                    break

            #process forecast data
            xAxisTimestamps = []
            xAxisHours = []
            yAxisTemperature =[]
            yAxisPrecipitation = []
            for timestamp in forecastJson['list']:
                xAxisTimestamps.append(timestamp['dt'])
                xAxisHours.append(datetime.fromtimestamp(timestamp['dt']))
                yAxisTemperature.append(timestamp['main']['temp']-kelvinOffset)
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
                tmpSunset  = forecastJson['city']['sunset']  + i*86400
                tmpSunrise = forecastJson['city']['sunrise'] + (i+1)*86400
                sunset = 0
                if tmpSunset < xAxisTimestamps[-1] and tmpSunset > xAxisTimestamps[0]:
                    sunset = tmpSunset
                else:
                    if tmpSunset > xAxisTimestamps[-1]:
                        sunset = xAxisTimestamps[-1]
                        breakout = True
                    if tmpSunset < xAxisTimestamps[0]:
                        sunset = xAxisTimestamps[0]

                sunrise = 0
                if tmpSunrise < xAxisTimestamps[-1] and tmpSunrise > xAxisTimestamps[0]:
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
                ax2.axvspan(datetime.fromtimestamp(nightTimestamp[0]), datetime.fromtimestamp(nightTimestamp[1]), facecolor="none", edgecolor="black", hatch='....', )

            for xAxisHour in xAxisHours:
                if xAxisHour.hour == 1:
                    ax2.axvline(xAxisHour-timedelta(hours=1), ls=':', color="red")

            ax1.xaxis.set_minor_formatter(xfmt1)
            #ax2.xaxis.set_minor_formatter(ticker.NullFormatter())
            ax1.xaxis.set_minor_locator(locator1)
            ax1.tick_params(axis='x', which='minor', top=False, labeltop=True, bottom=False, labelbottom=False)
            ax1.yaxis.tick_right()
            #fix margins
            plt.margins(x=0)

            #display
            #plt.savefig('figure.png')
            #canvas = plt.get_current_fig_manager().canvas
            forecastCanvas = tempAndPercipPlot.canvas
            forecastCanvas.draw()
            forecastPlotImage = Image.frombytes('RGB', forecastCanvas.get_width_height(), forecastCanvas.tostring_rgb())
            #clean up
            plt.close(tempAndPercipPlot)
            gc.collect(2)


        framebufferFont30 = ImageFont.truetype('SourceCodePro-Regular.ttf', 30)
        framebufferFont20 = ImageFont.truetype('SourceCodePro-Regular.ttf', 20)

        framebufferImage = Image.new('RGB', (640, 385), (0xFF, 0xFF, 0xFF))
        framebufferImage.paste(forecastPlotImage, (-50, 185))
        framebufferDraw = ImageDraw.Draw(framebufferImage)
        framebufferDraw.text((10, 0), datetime.now().strftime('%Y-%m-%d %H:%M'), font=framebufferFont30, fill=0)


        jazzString1 = 'ČRoJazz: '+jazzJson1['data'][0]['title']+": "+jazzJson1['data'][0]['since'][11:16]+" - "+jazzJson1['data'][0]['till'][11:16]
        framebufferDraw.text((10, 40), jazzString1, font=framebufferFont20, fill=0)

        jazzString2 = '         '+jazzJson2['data']['interpret']+" - "+jazzJson2['data']['track'] if 'interpret' in jazzJson2['data'] else '         N\A'
        framebufferDraw.text((10, 70), jazzString2, font=framebufferFont20, fill=0)


        dustString = 'Dust:    '+str(weatherJson['current']['values'][0]['value'])+"/"+str(weatherJson['current']['values'][1]['value'])+"/"+str(weatherJson['current']['values'][2]['value'])
        dustColor = 0 if (weatherJson['current']['standards'][0]['percent']+weatherJson['current']['standards'][1]['percent'])/2 < 100 else (255,0,0)
        framebufferDraw.text((10, 100), dustString, font=framebufferFont20, fill=dustColor)
        framebufferDraw.text((10, 130), 'Temp:    '+str(weatherJson['current']['values'][5]['value'])+"°", font=framebufferFont20, fill=0)

        #sanitize image palette
        framebufferImage = framebufferImage.quantize(palette=PaletteImage)

        epd.Display(framebufferImage)
        counter = counter + 1
        epd.sleep()
        time.sleep (60)

