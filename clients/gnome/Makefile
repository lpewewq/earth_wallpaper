SYSTEMD_USER_DIR=${HOME}/.config/systemd/user/
DIR=$(HOME)/.config/earth_wallpaper/

uninstall:
	# remove script directory
	rm -rf $(DIR)
	# remove unit file
	systemctl --user --now disable earth_wallpaper.service || true
	rm -f $(SYSTEMD_USER_DIR)earth_wallpaper.service
	systemctl --user daemon-reload

install:
	# install update script
	mkdir -p $(DIR)
	cp earth_wallpaper.sh $(DIR)
	cp earth_wallpaper.config "$(DIR)"
	# install unit file
	mkdir -p $(SYSTEMD_USER_DIR)
	cp earth_wallpaper.service $(SYSTEMD_USER_DIR)
	systemctl --user daemon-reload
	systemctl --user --now enable earth_wallpaper.service

clean_install: uninstall install

.PHONY: install uninstall clean_install