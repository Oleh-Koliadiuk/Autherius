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

Select options `1` through `4` from the menu and then enter the requested search term. At a target prompt, enter `B` to return to the menu. Press `Q` in the main menu to quit. Autherius does not start a search until you select an option and enter a target. For phone searches, enter an international number beginning with `+`, such as `+380501234567`.

SpiderFoot stores its database, cache, and logs in the current user's application data directory. On macOS, this is `~/Library/Application Support/Autherius/SpiderFoot`. Optional SpiderFoot modules may report that API keys are missing; those modules cannot return results until configured with their respective keys.

Phone searches use a small set of relevant modules to avoid starting unrelated scans. Offline checks can identify country and, when available, carrier information. SpiderFoot's built-in CallerName lookup only supports US `+1` numbers; richer international reverse lookups require configuring third-party modules and their API credentials.

Full-name searches use SpiderFoot's Account Finder module rather than its entire passive module set. Autherius also raises SpiderFoot's soft open-file limit when the operating system permits it, and the Account Finder is capped at three internal workers to reduce file descriptor exhaustion.

After a SpiderFoot scan, Autherius displays every related finding with its type, data, source module, related event, and any URL included by the source. It omits the seed event, which only repeats the original search target, and summarizes missing API keys or storage errors separately.

Username searches print each claimed profile with its URL, account type, extracted data fields, and source site. A full JSON report is saved under the user's Autherius application data directory in `MaigretReports/`.

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
