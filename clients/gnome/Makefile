SYSTEMD_USER_DIR=${HOME}/.config/systemd/user/
CONFIG_DIR=$(HOME)/.config/earth_wallpaper/
USER_BIN=${HOME}/.local/bin/

uninstall:
	systemctl --user stop earth_wallpaper.service
	systemctl --user disable earth_wallpaper.service
	rm -rf $(CONFIG_DIR)
	rm -f $(USER_BIN)earth_wallpaper.sh
	rm -f $(SYSTEMD_USER_DIR)earth_wallpaper.service
	systemctl --user daemon-reload

install:
	mkdir -p $(USER_BIN)
	mkdir -p $(SYSTEMD_USER_DIR)
	mkdir -p $(CONFIG_DIR)
	cp earth_wallpaper.sh $(USER_BIN)
	cp earth_wallpaper.service $(SYSTEMD_USER_DIR)
	cp earth_wallpaper.config "$(CONFIG_DIR)"
	systemctl --user daemon-reload
	systemctl --user start earth_wallpaper.service
	systemctl --user enable earth_wallpaper.service

clean_install: uninstall install

.PHONY: install uninstall clean_install