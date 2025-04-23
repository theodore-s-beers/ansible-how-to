# Ansible How-to

I've been writing this documentation in the form of a
[marimo](https://marimo.io/) notebook, as a way of exploring this promising
alternative to Jupyter notebooks.

## Instructions

Set up virtual environment:

```sh
uv venv
```

Activate virtual environment:

```sh
source .venv/bin/activate
```

Install dependencies:

```sh
uv sync
```

View notebook in read-only mode:

```sh
marimo run how_to.py
```

Or edit the notebook, create new notebooks, etc.:

```sh
marimo edit
```
