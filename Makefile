PREFIX ?= /usr/local
SYSTEMD_DIR ?= /etc/systemd/system
CONFIG_DIR ?= /etc
LOG_DIR ?= /var/log
RUN_DIR ?= /var/run

.PHONY: all install uninstall clean test

all: nickickerd.py

install: all
	@echo "Installing nickickerd..."
	install -d $(PREFIX)/bin
	install -m 755 nickickerd.py $(PREFIX)/bin/nickickerd
	
	@echo "Installing systemd service..."
	install -d $(SYSTEMD_DIR)
	install -m 644 nickickerd.service $(SYSTEMD_DIR)/
	
	@echo "Creating log directory..."
	install -d $(LOG_DIR)
	touch $(LOG_DIR)/nickickerd.log
	chmod 644 $(LOG_DIR)/nickickerd.log
	
	@echo "Creating run directory..."
	install -d $(RUN_DIR)
	
	@echo "Reloading systemd..."
	systemctl daemon-reload
	
	@echo "Installation complete!"
	@echo "To start the service, run: systemctl --now enable nickickerd"

uninstall:
	@echo "Uninstalling nickickerd..."
	systemctl stop nickickerd || true
	systemctl disable nickickerd || true
	
	rm -f $(PREFIX)/bin/nickickerd
	rm -f $(SYSTEMD_DIR)/nickickerd.service
	rm -f $(LOG_DIR)/nickickerd.log
	rm -f $(RUN_DIR)/nickickerd.pid
	
	systemctl daemon-reload
	
	@echo "Uninstallation complete!"

clean:
	rm -f *.pyc
	rm -f __pycache__/*
	rm -rf __pycache__

test:
	@echo "Testing nickickerd in foreground mode..."
	python3 nickickerd.py --foreground --config /etc/nickicker.conf

status:
	@echo "Service status:"
	systemctl status nickickerd || echo "Service not running"
	@echo ""
	@echo "Recent logs:"
	journalctl -u nickickerd -n 20 --no-pager || echo "No logs found"
