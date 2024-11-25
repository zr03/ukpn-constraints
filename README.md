# UKPN Constraints

This package includes functionality to scrape constraint data from UK Power Network's Open Data Portal via API and visualise data in real-time.

## Installation

Installing your repo adds it to your virtual environment, just like any other package downloaded from pip, conda etc. It's recommended that you install your repo in a virtual environment (e.g. conda).

First, clone the repo using your git client.
```
git clone https://github.com/zr03/ukpn-constraints.git
```

1. Navigate to this repo on the command line.
2. Create a virtual environment with a setup of python 3.10 and git.
3. Install the package your new virtual environment with:

```
pip install -e .
```

## Testing

We are using pytest for tests. You should therefore make sure that pytest is installed while developing and run your tests regularly. Good tests should be small and readable.

By default, pytest looks for any file that begins with `test_` and any function within those files that also begins with `test_` and runs them. The test functions should assert something, to check expected functionality.

From the root of your repo, run all tests with:

```
python -m pytest -v
```

## ENV Setup

The following variables should be setup in a .env file placed in the top level of the repo:

ODP_API_KEY = \<\<Your ODP API key\>\>, to be provided by the Data Team

