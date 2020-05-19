import os
import textwrap

introduction = textwrap.dedent("""\
Recommended Usage:
---------------------------

* Its recommended run the log-rotation.sh script and have a logs directory in your repo.

* You however can also specify the IVR directory path and search against 'app.log' itself.
""")


print("\n|     Welcome to the In House IVR Log_Searcher     |\n")
print(introduction)
log_dir = input("Enter your IVR logs directory: ")

if log_dir[-1] != "/":
    log_dir = str(log_dir + "/")


file = ""


def init_display():
    print("\nWhat do you want to do?")
    print("  1) List available log files in the logs dir")
    print("  2) Search a particular log file")
    print("  3) View all contents of a particular log file")
    print("  4) Exit the Program")
    option_input = input("")
    return option_input


def how_to():
    how_to_guide = textwrap.dedent("""\
    
    ***** A Quick how-to Guide *******
    
    * You must at least enter a PHONE_NUMBER for a valid search.
      Its advisable not to include the '+' character into your phone number search.
      
    * The other fields should be left blank if not required in your search. Simply press
      enter and continue. 
      
    * If you wish to search for the specified phone number on a particular DATE, enter the
      date when prompted in the format provided. Use a CORRECT format. Leave the timestamp
      fields empty.
      
    * If you wish to search for the occurrence of a phone number in a particular duration, 
      enter the start and stop time when prompted. Use a CORRECT format, example provided.
      Leave the date field empty.
    
    * You can have a combined search including a phone number and either a date, timestamp 
      duration or both.
      NOTE: In a combined search with date and timestamp, the DATE is searched for first 
            then in those results, the timestamp parameter is applied.
      
    """)
    return how_to_guide


def search_params():
    print(how_to())
    phone_number = input("Enter phone number to search [format: 256701234567]: ")
    date = input("Enter date to search [format: mm/dd/yyyy]: ")
    time_stamp1 = input("Enter start timestamp to query by [format: hh:mm:ss PM/AM]: ")
    time_stamp2 = input("Enter stop timestamp to query by [format: hh:mm:ss PM/AM]: ")
    return phone_number, date, time_stamp1, time_stamp2


def search(log_file: str, phone_number: str, date: str = None, timestamp1: str = None, timestamp2: str = None):
    search_by_phone = os.popen("cat {} | grep {}".format(log_file, phone_number))
    if date is not "":
        print("using date")
        search_by_date = os.popen("cat {} | grep {} | grep {}".format(log_file, phone_number, date))
        return search_by_date.read()
    if timestamp1 and timestamp2 is not "":
        print('using time')
        tmp_file = "temp.txt"
        os.popen("cat {} | grep {} >> {}".format(file, phone_number, tmp_file))
        search_by_time = os.popen("awk -v from='{}' -v to='{}' '$2>=from && $2<=to' {}".format(timestamp1, timestamp2, tmp_file))
        me = search_by_time.read()
        os.system("rm {}".format(tmp_file))
        return me
    if date and timestamp1 and timestamp2 is not "":
        print("using date and time")
        tmp_file = "temp.txt"
        os.popen("cat {} | grep {} | grep {} >> {}".format(file, phone_number, date, tmp_file))
        search_by_date_time = os.popen("awk -v from='{}' -v to='{}' '$2>=from && $2<=to' {} ".format(timestamp1, timestamp2, tmp_file))
        os.system("rm {}".format(tmp_file))
        return search_by_date_time.read()
    else:
        return search_by_phone.read()


if os.path.exists(log_dir):
    option_1 = init_display()
else:
    print("{} is not a valid directory. Check the path and try again. Exiting...".format(log_dir))
    exit()


while option_1:
    if str(option_1) == "1":
        print("\nThe available files in {} are: ".format(log_dir))
        dir_list = os.popen('ls {}'.format(log_dir)).read()
        print(dir_list)
        option_1 = init_display()

    elif str(option_1) == "2":
        query_file = input("\nEnter the file to query e.g app.log.2020-05-17: ")
        if os.path.exists("{}{}".format(log_dir, query_file)) and query_file != "":
            file = str(log_dir + query_file)
            phone, date_to_search, start_time, stop_time = search_params()
            print(search(file, phone, date_to_search, start_time, stop_time))
            option_1 = init_display()
        else:
            print("File: {} doesnt exist".format(query_file))
            option_1 = init_display()

    elif str(option_1) == "3":
        query_file = input("\nEnter the file to view e.g app.log.2020-05-17: ")
        log_file = str(log_dir + query_file)
        if os.path.exists(log_file) and query_file != "":
            print("\n****** Start of File****\n")
            os.system("cat {}".format(log_file))
            print("\n****** End of File****\n")
            option_1 = init_display()
        else:
            print("File: {} doesnt exist".format(query_file))
            option_1 = init_display()

    elif str(option_1) == "4":
        print("Exiting Program...")
        exit()

    else:
        print("Invalid Option Entered, Try again...")
        option_1 = init_display()




