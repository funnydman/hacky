TESTS_FOLDER := "tests/"
SRC_FOLDER := "*.py"

run-unit-tests:
	coverage run -m pytest -v ${TESTS_FOLDER} && coverage report -m

run-static-analysis:
	pylint ${TESTS_FOLDER} ${SRC_FOLDER} && mypy ${TESTS_FOLDER}
