#!/bin/bash

source ${HOME}/.config/earth_wallpaper/earth_wallpaper.config

retries=0
while [ $retries -lt 60 ]
do
    earth_wallpaper=${HOME}/.config/earth_wallpaper/wallpaper.png
    wget -qO $earth_wallpaper ${DOMAIN}/?resolution=${RESOLUTION}
    if [ $? -eq 0 ]; then
        let "retries=0"
        /usr/bin/gsettings set org.gnome.desktop.background picture-uri file:///${earth_wallpaper}
        sleep 600
    else
        let "retries++"
        sleep 10
    fi
done
