TESTS_FOLDER := "tests/"
SRC_FOLDER := "main.py"

run-unittest:
	coverage run -m pytest ${TESTS_FOLDER} && coverage report -m

run-static-analysis:
	pylint ${TESTS_FOLDER} ${SRC_FOLDER} && mypy ${TESTS_FOLDER}
