DELETE_ON_ERROR:

env:
	python -m virtualenv env

requirements:
	pip install -r requirements.txt

lint:
	python -m pylint file_changed_command_runner
	black file_changed_command_runner

test:
	PYTHONPATH=. pytest --cov file_changed_command_runner --cov-fail-under=100 -v tests

install-hooks:
	pre-commit install

apkg:
	rm -rf dist
	flit build
	atakama-pkg.exe --pkg dist/file_changed_command_runner-1.0.0-py3-none-any.whl --key ../keys/key.pem --crt ../keys/cert.pem --self-signed

.PHONY: test requirements lint publish install-hooks
