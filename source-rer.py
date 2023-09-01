import base64
import os
from urllib.parse import urljoin, urlparse
from pathlib import Path
import re
import shutil
import argparse

try:
    from bs4 import BeautifulSoup
    from colorama import Fore
    import requests
    import sourcemaps  # python-sourcemaps
except ImportError:
    print("Required module(s) not found. Please install them using:")
    print("\033[32mpip install -r requirements.txt\033[0m")
    exit(1)

parser = argparse.ArgumentParser(
    formatter_class=argparse.RawDescriptionHelpFormatter,
    description="""
    
▒█▀▀▀█ █▀▀█ █░░█ █▀▀█ █▀▀ █▀▀ ░░ █▀▀█ █▀▀ █▀▀█ 
░▀▀▀▄▄ █░░█ █░░█ █▄▄▀ █░░ █▀▀ ▀▀ █▄▄▀ █▀▀ █▄▄▀ 
▒█▄▄▄█ ▀▀▀▀ ░▀▀▀ ▀░▀▀ ▀▀▀ ▀▀▀ ░░ ▀░▀▀ ▀▀▀ ▀░▀▀
                - By github.com/ItzzMeGrrr
Download source code from JavaScript sourcemaps
""",
    epilog="""
Examples:
    python source-rer.py -l js_links.txt -o output_dir 
    python3 source-rer.py -u https://example.com -o output_dir -H 'Cookie: SESSION=1234567890' 
""",
)
args_input = parser.add_mutually_exclusive_group(required=True)
args_input.add_argument(
    "-l",
    "--links",
    help="File containing js file links to download source code from",
)
args_input.add_argument("-u", "--url", help="Link to page find js links from")

parser.add_argument(
    "-o", "--output", help="Output directory to save source code", required=True
)
parser.add_argument(
    "-knm",
    "--keep",
    help="Keep node_modules as well, (default: skip)",
    action="store_true",
)
parser.add_argument(
    "-X",
    "--method",
    help="HTTP method to use (default: GET)",
    default="GET",
    choices=["GET", "POST"],
)
parser.add_argument(
    "-H",
    "--header",
    help="HTTP header to add to request (multiple -H flags are accepted)",
    action="append",
    default=[],
)
parser.add_argument(
    "-q",
    "--quiet",
    help="Don't print any output except errors",
    action="store_true",
)
parser.add_argument(
    "-v", "--verbose", help="Print  verbose output", action="store_true"
)
args = parser.parse_args()

VERBOSE = args.verbose
QUIET = args.quiet


def print_custom(text, color, override=False):
    global VERBOSE, QUIET
    if (override or VERBOSE) and not QUIET:
        print(f"{color}{text}{Fore.RESET}")
        return


KEEP_NODE_MODULES = args.keep
js_links = args.links
url = args.url

method = args.method
headers = {}
if args.header:
    for header in args.header:
        if header.count(":") < 1:
            print_custom(
                f"Invalid header {header}, header name and value should be separated by a colon ':' Ex. {Fore.CYAN}-H 'HeaderName: HeaderValue'",
                Fore.YELLOW,
                override=True,
            )
        header_split = header.split(":")
        headers.update(
            {f"{header_split[0].strip()}": f"{''.join(header_split[1:]).strip()}"}
        )

output_directory = args.output


links = []
source_mapping_urls = []


def sanatize_filename(filename):
    # remove multiple slashes and replace .. with .
    filename = re.sub(r"(/)+", "/", filename.replace("..", "."))
    # remove all characters except a-z, A-Z, 0-9, -, /, . and _
    pattern = r"[^a-zA-Z0-9\-/._]"
    return re.sub(pattern, "", filename)


def fetch(url):
    global method, headers
    try:
        if method == "POST":
            res = requests.post(url, headers=headers)
            if not res.status_code == 200:
                print_custom(
                    f"  ^-- Got status code: {Fore.RED}{res.status_code}{Fore.YELLOW} from '{url}'",
                    Fore.YELLOW,
                    override=True,
                )
            return res
        else:
            res = requests.get(url, headers=headers)
            if not res.status_code == 200:
                print_custom(
                    f"  ^-- Got status code: {Fore.RED}{res.status_code}{Fore.YELLOW} from '{url}'",
                    Fore.YELLOW,
                    override=True,
                )
            return res
    except Exception as e:
        print(f"{Fore.RED}Exception:", e)
        print(f"{Fore.RESET}")
        return None


def extract_sourcemap(js_content):
    # Pattern for sourcemap URL
    sourcemap_url_pattern = r"\/\/# sourceMappingURL=(.+\.map)"

    # Pattern for embedded base64 sourcemap
    base64_sourcemap_pattern = r"\/\/# sourceMappingURL=data:application\/json;(.+)"

    url_match = re.search(sourcemap_url_pattern, js_content)
    base64_match = re.search(base64_sourcemap_pattern, js_content)

    if url_match:
        return ("url", url_match.group(1))
    elif base64_match:
        base64_sourcemap_data = base64_match.group(1)
        return ("data", base64_sourcemap_data)
    else:
        return ("not-found", None)


def dump_content(content, out_dir):
    global KEEP_NODE_MODULES
    for source in content:
        if not KEEP_NODE_MODULES and "node_modules" in source:
            print_custom(f"Skipping {source}", Fore.YELLOW)
            continue
        filtered_source = sanatize_filename(source)
        print_custom(f"Saving file {filtered_source}", Fore.GREEN)
        fileName = os.path.basename(filtered_source)
        path = os.path.dirname(urlparse(filtered_source).path)
        try:
            out_path = os.path.join(out_dir, path)
            path = Path(f"{out_path}")
            path.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            print(f"{Fore.RED}Exception:", e)
            print(f"{Fore.RESET}")
            continue
        file_path = os.path.join(path, fileName)
        try:
            with open(f"{file_path}", "w", encoding="utf-8") as file:
                file.write(content.get(source))
        except Exception as e:
            print(f"{Fore.RED}Exception:", e)
            print(f"{Fore.RESET}")
            continue


def get_sourcemap_content(source_type, src, link):
    if source_type == "url":
        url = urljoin(link, src)
        res = fetch(url)
        if res.status_code == 200:
            return res.text
        else:
            print_custom(
                f"  ^-- Got status code: {Fore.RED}{res.status_code}{Fore.YELLOW} for map link '{url}'",
                Fore.YELLOW,
                override=True,
            )
            return None
    elif source_type == "data":
        try:
            return base64.b64decode(src).decode("utf-8")
        except:
            print_custom(
                f"  ^-- Failed to decode base64 sourcemap for {Fore.RED}{link}",
                Fore.RED,
                override=True,
            )
            return None
    return None


def save_original_source(sourcemap_data, output_directory):
    link = sourcemap_data["link"]
    source_type = sourcemap_data["source_type"]
    src = sourcemap_data["src"]
    source_content = get_sourcemap_content(source_type, src, link)
    if not source_content:
        if source_type == "not-found":
            print_custom(
                f"  ^-- SourceMappingURL not found in {Fore.RED}{link}",
                Fore.WHITE,
                override=True,
            )
        else:
            print_custom(
                f"  ^-- Failed to download source for {Fore.RED}{link}",
                Fore.RED,
                override=True,
            )
        return
    source_map_content = sourcemaps.decode(source_content).sources_content
    dump_content(source_map_content, output_directory)


def find_js_links(url):
    # validate url using urlparse
    parsed_url = urlparse(url)
    if not parsed_url.scheme or not parsed_url.netloc:
        print_custom(f"Invalid URL: {url}", Fore.RED, override=True)
        exit(1)

    res = fetch(parsed_url.geturl())
    soup = BeautifulSoup(res.text, "html.parser")

    script_tags = soup.find_all("script", src=True)
    # Extract the 'src' attribute values (JS file URLs)
    js_file_urls = []
    for tag in script_tags:
        js_file_urls.append(tag["src"])

    # Join relative URLs with the base URL
    final_js_file_urls = []
    for js_url in js_file_urls:
        if not js_url.startswith("http"):
            final_js_file_urls.append(urljoin(url, js_url))
        else:
            final_js_file_urls.append(js_url)

    print_custom(
        f"Found {Fore.CYAN}{len(final_js_file_urls)}{Fore.WHITE} JS files",
        Fore.WHITE,
        override=True,
    )
    return final_js_file_urls


def load_js_links(filename):
    unique_lines = set()
    uniques = 0
    invalid = 0
    with open(filename, "r") as file:
        for line in file:
            cleaned_line = line.strip()
            try:
                parsed_url = urlparse(cleaned_line)
                path = parsed_url.path
                file_extension = os.path.splitext(path)[1]
                if not file_extension.lower() == ".js":
                    print_custom(
                        f"Ignoring non js link: {Fore.CYAN}{cleaned_line}",
                        Fore.YELLOW,
                    )
                    invalid += 1
                    continue
            except:
                print_custom(
                    f"Invalid URL: {Fore.RED}{cleaned_line}",
                    Fore.RED,
                    override=True,
                )
                invalid += 1
                continue

            if cleaned_line not in unique_lines:
                unique_lines.add(cleaned_line)
                uniques += 1
            else:
                invalid += 1
                print_custom(
                    f"Ignoring duplicate line: {Fore.CYAN}{cleaned_line}", Fore.YELLOW
                )

    print_custom(
        f"Loaded {Fore.CYAN}{uniques}{Fore.WHITE} unique and ignored {Fore.CYAN}{invalid}{Fore.WHITE} duplicate/invalid links",
        Fore.WHITE,
        override=True,
    )
    unique_lines_list = list(unique_lines)
    return unique_lines_list


def main():
    global KEEP_NODE_MODULES, js_links, url, output_directory, VERBOSE
    banner()
    if js_links:
        if not os.path.exists(js_links):
            print_custom(f"File not found: {js_links}", Fore.RED, override=True)
            exit(1)

    # Validate output directory
    if os.path.exists(output_directory):
        if os.listdir(output_directory):
            print_custom(
                f"Output directory {output_directory} is not empty.",
                Fore.YELLOW,
                override=True,
            )
            overwrite = input("Do you want to overwrite the existing files? (y/n): ")
            if overwrite.lower() == "y":
                shutil.rmtree(output_directory)
                os.makedirs(output_directory, exist_ok=True)
                pass
            else:
                exit(1)
    else:
        os.makedirs(output_directory, exist_ok=True)

    # Load js links
    if js_links:
        source_mapping_urls = load_js_links(js_links)
    if url:
        source_mapping_urls = find_js_links(url)

    if not source_mapping_urls:
        print(f"{Fore.RED}No JS files found.{Fore.RESET}")
        exit(1)
    # Save original source
    for url in source_mapping_urls:
        print_custom(
            f"Saving original source for {Fore.CYAN}{url}{Fore.RESET}",
            Fore.WHITE,
            override=True,
        )
        src = extract_sourcemap(fetch(url).text)
        data = {
            "link": url,
            "source_type": src[0],
            "src": src[1],
        }
        save_original_source(data, output_directory)


def banner():
    global QUIET
    if not QUIET:
        print(
            f"""{Fore.YELLOW}            

▒█▀▀▀█ █▀▀█ █░░█ █▀▀█ █▀▀ █▀▀ ░░ █▀▀█ █▀▀ █▀▀█ 
░▀▀▀▄▄ █░░█ █░░█ █▄▄▀ █░░ █▀▀ ▀▀ █▄▄▀ █▀▀ █▄▄▀ 
▒█▄▄▄█ ▀▀▀▀ ░▀▀▀ ▀░▀▀ ▀▀▀ ▀▀▀ ░░ ▀░▀▀ ▀▀▀ ▀░▀▀
              {Fore.GREEN}- By github.com/ItzzMeGrrr{Fore.RESET}\n"""
        )


try:
    main()
except KeyboardInterrupt:
    print_custom("\nExiting...", Fore.RED)
    exit(1)
