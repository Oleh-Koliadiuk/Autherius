# Autherius

Autherius is a terminal OSINT application that combines username discovery from [Maigret](https://github.com/soxoj/maigret) with passive target searches from [SpiderFoot](https://github.com/smicallef/spiderfoot).

## Search options

- **Username:** Maigret checks the username against its site database.
- **Phone, full name, and email:** SpiderFoot runs its passive modules for the supplied target.

SpiderFoot has many modules, and some data sources require API keys. Results depend on the enabled modules and available public sources; a match is not proof that two accounts or records belong to the same person.

## Requirements

- Python 3.12
- Poetry
- Git

## Installation

From the project directory, install Autherius and its dependencies:

```bash
poetry env use python3.12
poetry install
```

Or use `requirements.txt` with a virtual environment:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pip install -e .
```

Set up SpiderFoot in its own virtual environment. This keeps its dependencies separate from Maigret's:

```bash
sh scripts/setup_spiderfoot.sh
```

The setup script installs the requirements listed by the vendored SpiderFoot repository.

## Run

Start the interactive menu:

```bash
poetry run autherius
```

Select options `1` through `4` from the menu and then enter the requested search term. Press `Q` to quit. Autherius does not start a search until you select an option and enter a target. For phone searches, enter an international number beginning with `+`, such as `+380501234567`.

Advanced Maigret CLI options are available with:

```bash
poetry run autherius --help
```

## Upstream projects and licenses

- [Maigret](https://github.com/soxoj/maigret) provides the username search engine and site database. Its source is retained in `maigret/`.
- [SpiderFoot](https://github.com/smicallef/spiderfoot) provides the phone, full-name, and email search engine. Its source is retained in `integrations/spiderfoot/`.

Both upstream projects are MIT licensed. Their license and copyright notices are preserved with their source. Autherius' original launcher, branding, and integration changes are copyright Oleh Koliadiuk. See [LICENSE](LICENSE) and `integrations/spiderfoot/LICENSE`.

## Responsible use

Use Autherius only for lawful, authorized research. Search public information, respect applicable laws and website terms, and handle reports as sensitive personal data.
