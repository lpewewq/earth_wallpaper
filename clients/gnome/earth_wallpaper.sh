#!/bin/bash

WD=${HOME}/.config/earth_wallpaper

source ${WD}/earth_wallpaper.config

retries=0
earth_wallpaper=${WD}/earth_wallpaper.png
tmp_earth_wallpaper=${WD}/.earth_wallpaper.png

while [ $retries -lt 60 ]
do
    wget -t 1 -T 10 -O $tmp_earth_wallpaper ${DOMAIN}/?width=${WIDTH}\&height=${HEIGHT}\&zoom=${ZOOM}\&timezone=${TIMEZONE}\&fov=${FOV}\&stars=${STARS}\&constellations=${CONSTELLATIONS}
    if test "$?" == 0 && test "$(file -b --mime-typ $tmp_earth_wallpaper)" == 'image/png'; then
        mv $tmp_earth_wallpaper $earth_wallpaper
        /usr/bin/gsettings set org.gnome.desktop.background picture-uri file:///${earth_wallpaper}
        let "retries=0"
    else
        rm $tmp_earth_wallpaper
        let "retries++"
    fi
    sleep 600
done
