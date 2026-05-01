[code-of-conduct]: CODE_OF_CONDUCT.md
[fork]: https://github.com/pkjmesra/PKScreener/fork
[pr]: https://github.com/pkjmesra/PKScreener/compare

# Contributing

Hi there! We're thrilled that you'd like to contribute to this project. Your help is essential for keeping it great.

Please note that this project is released with a [Contributor Code of Conduct][code-of-conduct]. By participating in this project you agree to abide by its terms.

## Issues and PRs

If you have suggestions for how this project could be improved, or want to report a bug, open an issue! We'd love all and any contributions. If you have questions, too, we'd love to hear them.

We'd also love PRs. If you're thinking of a large PR, we advise opening up an issue first to talk about it, though! Look at the links below if you're not sure how to open a PR.

## 1. Keep your Fork up to date
* Before statrting development of any new feature, Always check if this repo is ahead in commits as compared to your fork.
* It is a good practice to always keep your fork up-to-date before starting development of features/fixes to avoid merge conflicts.
* Update your fork using following code snippet.
```
# Add a new remote repo called as pkscreener_upstream
git remote add pkscreener_upstream https://github.com/pkjmesra/PKScreener.git

# Sync your fork before starting work
git fetch pkscreener_upstream
git checkout <BRANCH_YOU_ARE_WORKING_ON>
git merge pkscreener_upstream/<BRANCH_FROM_THIS_REPO_YOU_WANT_TO_MERGE_IN_YOUR_BRANCH>
```

## 2. Install Project Dependencies

* This project uses [**TA-Lib**](https://github.com/mrjbq7/ta-lib). Please visit the hyperlink for the official guide of installation.
* This Project requires Python 3.12 or above environment setup. [Click Here to Download](https://www.python.org/downloads/)
* Install python dependencies by running `pip install -r requirements.txt` in the root directory of this project. If you would also like to have technical indicators evaluated from ta-lib, install ta-lib as well :`pip3 install ta-lib`

## 3. Create Dependency Requirements

1. Install [**pip-chill**](https://pypi.org/project/pip-chill/) by running `pip install pip-chill` which is a developer friendly version of classic `pip freeze`.
2. Update the `requirements.txt` file by running `pip-chill --all --no-version -v > requirements.txt`.
3. Ensure to **uncomment** all the dependency modules from the `requirements.txt`

## 4. Testing Code Locally

1. Update the test-cases as per the new features from `test/pkscreener_test.py` if required.
2. Run a test locally with `pytest -v` and ensure that all tests are passed.
3. In case of a failure, Rectify code or Consider opening an issue for further discussion.

## 5. Pull Request Process

1. Ensure that dependecy list have been generated in the `requirements.txt` using above section.
2. Ensure that all test-cases are passed locally.
3. If you are contributing new feature or a bug-fix, Always create a Pull Request to `new-features` branch as it have workflows to test the source before merging with the `main`.
4. Keep your changes as focused as possible. If there are multiple changes you would like to make that are not dependent upon each other, consider submitting them as separate pull requests.
5. Work in Progress pull requests are also welcome to get feedback early on, or if there is something blocked you.

## 6. Submitting a pull request

1. [Fork][fork] and clone the repository.
1. Configure and install the dependencies: `pip3 install -r requirements.txt` and `pip3 install -r requirements-dev.txt`.
1. Make sure the tests pass on your machine: `python3 -m pytest -vv --durations-min=0.005 --cov-config=.coveragerc --durations=0`. Use `Flake8` as linter: `flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics` and `flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics`
1. Create a new branch: `git checkout -b my-branch-name`.
1. Make your change, add tests, and make sure the tests still pass.
1. Push to your fork and [submit a pull request][pr].
1. Pat your self on the back and wait for your pull request to be reviewed and merged.

## Resources

- [How to Contribute to Open Source](https://opensource.guide/how-to-contribute/)
- [Using Pull Requests](https://help.github.com/articles/about-pull-requests/)
- [GitHub Help](https://help.github.com)
