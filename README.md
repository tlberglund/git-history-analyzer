# Git History Analyzer

A small hack to help summarize how files have changed in a Git repo over time, with the option to show them as a marginally useless treemap.

## Setup

* Install Python 3
* `pip install matplotlib`
* `pip install squarify`
* `python git-history.py --help`

## Examples

```bash
$ python git-history.py ~/code/dev.startree.ai --begin=20230901T0000 --end=20230930T2359 --format=treemap
$ python git-history.py ~/code/dev.startree.ai --begin=20230901T0000 --end=20230930T2359 --format=json
$ python git-history.py ~/code/dev.startree.ai --begin=20230901T0000 --end=20230930T2359 --format=csv --summary
```

