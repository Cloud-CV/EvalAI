build_and_push() {
    python3 -m pip install --upgrade setuptools wheel twine
    python3 setup.py sdist bdist_wheel
    python3 -m twine upload --repository-url https://test.pypi.org/legacy/ dist/* -u ${TEST_PYPI_USERNAME}  -p ${TEST_PYPI_PASSWORD}

}

if [ "${TRAVIS_PULL_REQUEST}" != "false" ]; then
    echo "Skipping deploy to https://test-pypi.org; The commit is not on staging branch"
    exit 0
elif [ "${TRAVIS_BRANCH}" == "staging" ]; then
    build_and_push $TRAVIS_BRANCH
    exit 0
else
    echo "Skipping deploy!"
    exit 0
fi
