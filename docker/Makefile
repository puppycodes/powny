docker-%: %
	docker build -t nikicat/gns-$< $<

docker-all: docker-api docker-collector docker-fetcher docker-reinit docker-rules docker-splitter docker-worker
