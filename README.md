# CSTLint
`cstlint` is a Python code style checker that leverages `libcst`. It helps enforce specific style rules in a Python file.
It currently checks for the following rules:
- use of eval/exec/getattr/setattr
- nested functions
- lambdas
- mutable default args
- assignment to function inputs

## Installation
```
git clone https://github.com/horacepan/cstlint.git
cd cstlint
```

2) Setup a virtual environment
```
python3 -m venv venv
source venv/bin/activate
```

3) Install `cslint`
```
pip install .
```

Or install in editable mode if you are doing active development:
```
pip install -e .
```


## Sample Usage
```
cstlint {path/to/file}
```

To see the offending lines, set the `--verbose` flag:
```
cstlint {path/to/file} --verbose
```

## Tests
To run the unit tests:
```
python -m unittest discover -s tests -v
```
