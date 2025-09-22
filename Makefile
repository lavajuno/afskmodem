.PHONY: format

format:
	isort --profile black .
	black .
