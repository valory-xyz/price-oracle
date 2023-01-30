.PHONY: clean
clean: clean-test clean-build clean-pyc clean-docs

.PHONY: clean-build
clean-build:
	rm -fr build/
	rm -fr dist/
	rm -fr .eggs/
	rm -fr pip-wheel-metadata
	find . -name '*.egg-info' -exec rm -fr {} +
	find . -name '*.egg' -exec rm -fr {} +
	find . -type d -name __pycache__ -exec rm -rv {} +
	rm -fr Pipfile.lock

.PHONY: clean-docs
clean-docs:
	rm -fr site/

.PHONY: clean-pyc
clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +
	find . -name '.DS_Store' -exec rm -fr {} +

.PHONY: clean-test
clean-test:
	rm -fr .tox/
	rm -f .coverage
	find . -name ".coverage*" -not -name ".coveragerc" -exec rm -fr "{}" \;
	rm -fr coverage.xml
	rm -fr htmlcov/
	rm -fr .hypothesis
	rm -fr .pytest_cache
	rm -fr .mypy_cache/
	rm -fr .hypothesis/
	find . -name 'log.txt' -exec rm -fr {} +
	find . -name 'log.*.txt' -exec rm -fr {} +
	rm -rf leak_report

# isort: fix import orders
# black: format files according to the pep standards
.PHONY: formatters
formatters:
	tox -e isort
	tox -e black

# black-check: check code style
# isort-check: check for import order
# flake8: wrapper around various code checks, https://flake8.pycqa.org/en/latest/user/error-codes.html
# mypy: static type checker
# pylint: code analysis for code smells and refactoring suggestions
# vulture: finds dead code
# darglint: docstring linter
.PHONY: code-checks
code-checks:
	tox -p -e black-check -e isort-check -e flake8 -e mypy -e pylint -e vulture -e darglint

# safety: checks dependencies for known security vulnerabilities
# bandit: security linter
# gitleaks: checks for sensitive information
.PHONY: security
security:
	tox -p -e safety -e bandit
	gitleaks detect --report-format json --report-path leak_report

# generate abci docstrings
# update copyright headers
# generate latest hashes for updated packages
.PHONY: generators
generators:
	tox -e abci-docstrings
	tox -e fix-copyright
	autonomy hash all
	autonomy packages lock

.PHONY: common-checks-1
common-checks-1:
	tox -p -e check-copyright -e check-hash -e check-packages -e check-doc-links-hashes

.PHONY: common-checks-2
common-checks-2:
	tox -e check-abci-docstrings
	tox -e check-abciapp-specs
	tox -e check-handlers

.PHONY: all-checks
all-checks: clean formatters code-checks security generators common-checks-1 common-checks-2

.PHONY: test-skill
test-skill:
	make test-sub-p tdir=skills/test_$(skill)/ dir=skills.$(skill)

# how to use:
#
#     make test-sub-p tdir=$TDIR dir=$DIR
#
# where:
# - TDIR is the path to the test module/directory (but without the leading "test_")
# - DIR is the *dotted* path to the module/subpackage whose code coverage needs to be reported.
#
# For example, to run the ABCI connection tests (in tests/test_connections/test_abci.py)
# and check the code coverage of the package packages.valory.connections.abci:
#
#     make test-sub-p tdir=connections/test_abci.py dir=connections.abci
#
# Or, to run tests in tests/test_skills/test_counter/ directory and check the code coverage
# of the skill packages.valory.skills.counter:
#
#     make test-sub-p tdir=skills/test_counter/ dir=skills.counter
#
.PHONY: test-sub-p
test-sub-p:
	pytest -rfE tests/test_$(tdir) --cov=packages.valory.$(dir) --cov-report=html --cov-report=xml --cov-report=term-missing --cov-report=term  --cov-config=.coveragerc
	find . -name ".coverage*" -not -name ".coveragerc" -exec rm -fr "{}" \;

.PHONY: test-all
test-all:
	tox

v := $(shell pip -V | grep virtualenvs)

.PHONY: new_env
new_env: clean
	if [ ! -z "$(which svn)" ];\
	then\
		echo "The development setup requires SVN, exit";\
		exit 1;\
	fi;\

	if [ -z "$v" ];\
	then\
		pipenv --rm;\
		pipenv --clear;\
		pipenv --python 3.10;\
		pipenv install --dev --skip-lock;\
		echo "Enter virtual environment with all development dependencies now: 'pipenv shell'.";\
	else\
		echo "In a virtual environment! Exit first: 'exit'.";\
	fi

.PHONY: install-hooks
install-hooks:
	@echo "Installing pre-push"
	cp scripts/pre-push .git/hooks/pre-push

.PHONY: fix-abci-app-specs
fix-abci-app-specs:
	autonomy analyse fsm-specs --update --app-class OracleAbciApp --package packages/valory/skills/oracle_abci || (echo "Failed to check oracle_abci consistency" && exit 1)
	autonomy analyse fsm-specs --update --app-class OracleDeploymentAbciApp --package packages/valory/skills/oracle_deployment_abci || (echo "Failed to check oracle_deployment_abci consistency" && exit 1)
	autonomy analyse fsm-specs --update --app-class PriceAggregationAbciApp --package packages/valory/skills/price_estimation_abci || (echo "Failed to check price_estimation_abci consistency" && exit 1)
	echo "Successfully validated abcis!"

PACKAGES_PATH := packages/packages.json
RELEASE_VERSION := latest
PRICE_ORACLE_AGENT_NAME := valory/oracle
PRICE_ORACLE_IMAGE_NAME := valory/oar-oracle
release-image:
	$(eval PRICE_ORACLE_AGENT_HASH := $(shell cat ${PACKAGES_PATH} | grep "agent/${PRICE_ORACLE_AGENT_NAME}" | cut -d "\"" -f4 ))
	$(eval PRICE_ORACLE_AGENT_PUBLIC_ID := ${PRICE_ORACLE_AGENT_NAME}:${RELEASE_VERSION}:${PRICE_ORACLE_AGENT_HASH})
	# we first need to push all the packages in order to be able to build the image,
	# because the command pulls the agent from the registry.
	# Please make sure to run this command only from a release branch.
	autonomy push-all
	autonomy build-image ${PRICE_ORACLE_AGENT_PUBLIC_ID} --pull
	docker push ${PRICE_ORACLE_IMAGE_NAME}:${PRICE_ORACLE_AGENT_HASH}
