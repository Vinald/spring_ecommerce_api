import datetime
import os
import sys
import uuid
from prettytable import PrettyTable

sys.path.append('..')

from src.AppDatabase import AppDatabase
from src.Config import Config
from src.Hash import Hash
from src.Logger import Logger

working_dir = os.path.dirname(os.path.realpath(__file__))

logger = Logger(working_dir)
config = Config(working_dir, logger)
database = AppDatabase(config)


def clear_screen():
    os.system('clear')


def exit_application():
    clear_screen()
    exit(0)


def token_generator():
    unique_id = str(uuid.uuid1())
    return Hash.hash(unique_id)


def main_menu():
    clear_screen()
    message = """

    -----------------------------------------    
                    IVR Menu
    -----------------------------------------
            1. Add a new application
            2. Show applications
            3. Delete application
            q. Exit
    -----------------------------------------

"""
    print(message)
    option = str(input("    > ")).lower()

    if option == '1':
        return add_new_application()
    elif option == '2':
        return show_applications()
    elif option == '3':
        return delete_application()
    elif option == 'q':
        exit_application()
    else:
        return main_menu()


def sub_menu():
    message = """

    -----------------------------------------    
                    IVR Sub Menu
    -----------------------------------------
            1. Go to main menu
            q. Exit
    -----------------------------------------

"""
    print(message)
    option = str(input("    > ")).lower()

    if option == '1':
        return main_menu()
    elif option == 'q':
        exit_application()
    else:
        clear_screen()
        return sub_menu()


def add_new_application():
    clear_screen()
    message = """

    ------------------------------------------------  
                    New IVR Application
    ------------------------------------------------

    """
    print(message)
    token = token_generator()
    app_name = str(input("    Application name: "))
    app_voice_url = str(input("    Application Voice URL: "))
    app_status_url = str(input("    Application Status URL: "))

    data = {
        'name': app_name,
        'token': token,
        'voice_url': app_voice_url,
        'status_url': app_status_url,
        'date_created': datetime.datetime.now()
    }

    try:
        cursor = database.get_cursor()
        cursor.execute('SELECT name FROM apps WHERE name="{}"'.format(app_name))
        if int(cursor.rowcount) > 0:
            clear_screen()
            print("    Application already exists\n")
            return sub_menu()
        database.insert(data, AppDatabase.APPS_TABLE)
        clear_screen()
        print("    Application added successfully\n")
        print("    Please use this outbound token to make calls: {}\n".format(token))
        return sub_menu()
    except Exception as e:
        clear_screen()
        print("    An error occurred while adding application: {}\n".format(str(e)))
        return sub_menu()


def display_applications(results):
    if not results or results is None:
        clear_screen()
        print("    No applications in the database")
        return sub_menu()

    cols = ['App name', 'Token', 'Voice URL', 'Status URL', 'Date Created']
    pretty_table = PrettyTable(cols)

    for result in results:
        pretty_table.add_row([
            result['name'],
            result['token'],
            result['voice_url'],
            result['status_url'],
            result['date_created'],
        ])

    print("\n")
    print(pretty_table)
    print("\n")


def show_applications():
    try:
        cursor = database.get_cursor()
        cursor.execute('SELECT * FROM apps')
        clear_screen()
        display_applications(cursor.fetchall())
        return sub_menu()
    except Exception as e:
        clear_screen()
        print("    An error occurred while fetching results: {}\n".format(str(e)))
        return sub_menu()


def delete_application():
    cursor = database.get_cursor()
    cursor.execute('SELECT * FROM apps')
    display_applications(cursor.fetchall())
    print("\n")
    token = str(input("Enter the token of the app you want to delete: ")).lower()
    print("\n")
    try:
        conn = database.get_conn()
        cursor = database.get_cursor()
        cursor.execute('DELETE FROM apps WHERE token="{}" LIMIT 1'.format(token))
        conn.commit()
        clear_screen()
        print("    Application deleted successfully")
        return sub_menu()
    except Exception as e:
        clear_screen()
        print("    An error occurred while deleting app: {}\n".format(str(e)))
        return sub_menu()


main_menu()
