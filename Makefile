DELETE_ON_ERROR:

env:
	python -m virtualenv env

requirements:
	pip install -r requirements.txt

lint:
	python -m pylint runcmd_on_file_changed
	black runcmd_on_file_changed

test:
	PYTHONPATH=. pytest --cov runcmd_on_file_changed --cov-fail-under=100 -v tests

install-hooks:
	pre-commit install

apkg:
	rm -rf dist
	flit build
	atakama-pkg.exe --pkg dist/change_notify-1.0.0-py3-none-any.whl --key ../openssl/key.pem --crt ../openssl/cert.pem --self-signed

.PHONY: test requirements lint publish install-hooks
