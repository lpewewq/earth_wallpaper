#!/bin/bash

source ${HOME}/.config/earth_wallpaper/earth_wallpaper.config

while [ 1 ]
do
    temp_file=${HOME}/.config/earth_wallpaper/wallpaper.png
    wget -qO $temp_file ${DOMAIN}/wallpaper.png
    /usr/bin/gsettings set org.gnome.desktop.background picture-uri $temp_file
    sleep 600
done
