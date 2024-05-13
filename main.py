from colorama import init, Style
from prompt_toolkit.shortcuts import checkboxlist_dialog, input_dialog, radiolist_dialog
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.styles import Style as PromptStyle

from prompt_toolkit.formatted_text import HTML
import requests
import click
from colorama import Fore
import datetime

timer = None
static_text = FormattedTextControl(text=f"Time: {datetime.datetime.now().strftime('%H:%M:%S')}")
search_results = {}
SEARCH = "/search"
GET_INFO = "/get_info"
SEARCH_API = "http://uidorm.gladov.ru"
TORRENT_API = "http://127.0.0.1:5000"
flag = False
init()

prompt_style = PromptStyle.from_dict({
    "prompt": "ansiblue",
    "button": "#ffffff bg:#333333",
    "button.arrow": "#000000",
    "dialog shadow": "bg:#888888",
    "frame.label": "#ff00ff",
})


def show_results_of_search(query):
    print(123)
    global search_results
    search_results = requests.get(SEARCH_API + SEARCH, params={"query": query}).json()
    t = f"Found {len(search_results['items'])} results"
    matched_items = [(index, print_item(item)) for index, item in enumerate(search_results['items'], start=1)]

    if matched_items:
        click.echo(Fore.GREEN + "Found matching items:")
        click.echo(Style.RESET_ALL)

        choices = checkboxlist_dialog(
            title=t,
            values=matched_items,
            text="Choose variants using arrow keys (press 'Space' to select,"
                 " 'Tab' to go in section with confirmation or 'Back' to return):",
            style=prompt_style, cancel_text="Back"
        ).run()
        if choices is None:
            click.echo(Fore.RED + "Action cancelled.")
            search()
        else:
            selected_indices = [choice for choice in choices]
            selected_items = [search_results['items'][index - 1] for index in selected_indices]
            click.clear()
            final_items = [requests.get(SEARCH_API + GET_INFO, params={"link": item['link']}).json() for item in
                           selected_items]
            for item in final_items:
                print(item)
                link = item['magnetLink']
                print(link)
                if flag == 1:
                    response = requests.post(TORRENT_API + '/add_torrent', json={'link': '"' + link + '" --vlc'})
                else:
                    response = requests.post(TORRENT_API + '/add_torrent', json={'link': '"' + link + '"'})
                if response.status_code == 200:
                    click.echo(Fore.GREEN + f"Torrent '{item['name']}' added successfully!")
                else:
                    click.echo(Fore.RED + f"Failed to add torrent '{item['name']}'")
            show_torrent_dialog()

    else:
        click.echo(Fore.RED + "No matching items found.")
        main_menu()


def print_table(data):
    # Calculate column widths
    col_widths = [max(len(str(row[i])) for row in data) for i in range(len(data[0]))]

    # Print header
    header = " ".join(f"{str(cell):<{col_widths[i]}}" for i, cell in enumerate(data[0]))
    print(HTML(f"<b>{header}</b>"))

    # Print separator
    separator = "-" * (sum(col_widths) + len(col_widths) - 1)
    print(HTML(f"<b>{separator}</b>"))

    # Print rows
    for row in data[1:]:
        row_str = " ".join(f"{str(cell):<{col_widths[i]}}" for i, cell in enumerate(row))
        print(HTML(row_str))


def print_item(item):
    return f"Name: {item['name']}, " \
           f"Seeders: {item['seeders']}, Leechers: {item['leechers']}, " \
           f"Size: {item['size']}"


def refresh(app):
    static_text.text = f"Time: {datetime.datetime.now().strftime('%H:%M:%S')}"


@click.command()
def main_menu():
    global search_results
    choices = [
        ("Search", "Search for a new query"),
        ("Watch", "Watch while downloading"),
        ("List Existing", "List existing items")
    ]
    choice = radiolist_dialog(
        title="Main Menu",
        text="Choose an option:",
        values=choices, cancel_text="Exit"
    ).run()
    if choice == "Search":
        search()
    elif choice == "List Existing":
        show_torrent_dialog()
    elif choice == "Watch":
        global flag
        flag = 1
        search()
    else:
        return


@click.command()
def show_torrent_dialog():
    try:  # Acquire lock
        response = requests.get(TORRENT_API + "/list_torrents")
        if response.status_code == 200:
            torrents = response.json()['data']
            if not torrents:
                click.echo(Fore.YELLOW + "No existing torrents.")
                main_menu()
                return

            torrent_list = []
            for index, torrent in enumerate(torrents, start=1):
                torrent_info = (
                    index,
                    f"Torrent Name: {torrent['torrent name']}\n"
                    f"Downloaded: {torrent['downloaded']}\n"
                    f"Path: {torrent['path']}\n"
                    f"Peers: {torrent['peers']}\n"
                    f"Remaining Time: {' '.join(torrent['remaining_time'])}\n"
                    f"Running Time: {torrent['running_time']}\n"
                    f"Speed: {torrent['speed']}\n"
                    f"Uploaded: {torrent['uploaded']}\n"
                )
                torrent_list.append(torrent_info)

            choices = checkboxlist_dialog(
                title="Existing Torrents",
                values=torrent_list,
                text="Choose torrents:",
                style=prompt_style,
                cancel_text="Menu"
            ).run()

            if choices is None:
                main_menu()
            else:
                selected_torrents = [torrents[index - 1] for index in choices]
                for torrent in selected_torrents:
                    click.echo(Fore.GREEN + f"Selected Torrent: {torrent['torrent name']}")

        else:
            click.echo(Fore.RED + "Failed to retrieve existing torrents.")
            main_menu()

    except Exception as e:
        click.echo(Fore.RED + f"Error occurred: {e}")
        main_menu()


@click.command()
def search():
    global search_results
    query = ""
    try:
        query = input_dialog(
            title="Search query", text="Enter your search query.", cancel_text="Back", ok_text="Search"
        ).run()
    except Exception as e:
        print("Error occurred:", e)
    if query is None:
        main_menu()
        return
    else:
        show_results_of_search(query)


if __name__ == '__main__':
    main_menu()
