UNIT_TEST_FOLDER := "tests/unit/"
SOURCE_DIR := "src/"
UNIT_TESTS_FAIL_UNDER := 95

run-unit-tests:
	python3 -m pytest \
	-v \
	--cov-report term-missing \
	--cov-fail-under="${UNIT_TESTS_FAIL_UNDER}" \
	--cov="${SOURCE_DIR}" \
	"${UNIT_TEST_FOLDER}"


run-static-analysis:
	pylint ${UNIT_TEST_FOLDER} ${SOURCE_DIR} && mypy ${UNIT_TEST_FOLDER}
