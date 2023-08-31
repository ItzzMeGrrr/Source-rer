# Source-rer

Source-rer is a tool to save source code from JavaScript sourcemap files. You can provide a file containing links to js files or it can find JavaScript files from a given url.

## Installation

```bash
git clone
cd source-rer
pip install -r requirements.txt # or python3 -m pip install -r requirements.txt
```

## Usage

```txt
usage: download_src.py [-h] (-l LINKS | -u URL) -o OUTPUT [-knm] [-X {GET,POST}] [-H HEADER] [-q] [-v]


▒█▀▀▀█ █▀▀█ █░░█ █▀▀█ █▀▀ █▀▀ ░░ █▀▀█ █▀▀ █▀▀█
░▀▀▀▄▄ █░░█ █░░█ █▄▄▀ █░░ █▀▀ ▀▀ █▄▄▀ █▀▀ █▄▄▀
▒█▄▄▄█ ▀▀▀▀ ░▀▀▀ ▀░▀▀ ▀▀▀ ▀▀▀ ░░ ▀░▀▀ ▀▀▀ ▀░▀▀

Download source code from JavaScript sourcemaps

options:
  -h, --help            show this help message and exit
  -l LINKS, --links LINKS
                        File containing js file links to download source code from
  -u URL, --url URL     Link to page find js links from
  -o OUTPUT, --output OUTPUT
                        Output directory to save source code
  -knm, --keep          Keep node_modules as well, (default: skip)
  -X {GET,POST}, --method {GET,POST}
                        HTTP method to use (default: GET)
  -H HEADER, --header HEADER
                        HTTP header to add to request (multiple -H flags are accepted)
  -q, --quiet           Don't print any output except errors
  -v, --verbose         Print verbose output

Examples:
    python download_src.py -l js_links.txt -o output_dir
    python3 download_src.py -u https://example.com -o output_dir -H 'Cookie: SESSION=1234567890'
```

## Examples

#### Download source code from a url

```bash
python3 download_src.py -u https://example.com -o output_dir -H 'Cookie: SESSION=1234567890'
```

#### Provide a file containing links to js files

```bash
python3 download_src.py -l js_links.txt -o output_dir
```
