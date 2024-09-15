MAKEFLAGS += --always-make


create_network:
	sudo docker network create --driver=bridge --subnet=10.0.0.0/16 --ip-range=10.0.0.0/24 --gateway=10.0.0.1 process_monitor

start:
	sudo docker-compose up -d --build