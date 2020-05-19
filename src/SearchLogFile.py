from Logger import Logger
import sys
import os


class SearchLogFile:

    def __init__(self, log_dir: str ):
        print("Init search object")
        self.log_dir = log_dir
        self.arguments = sys.argv
        self.search_text = ""
        self.file_name = ""
        self.log_dir = "/home/fmm/ivr/"
        self.log_file_path = ""
        self.number_of_args = len(self.arguments)-1
        print("{0} Arguments provided".format(self.number_of_args))

    def get_args(self):
        print("get args")
        if self.number_of_args > 0:
            if self.number_of_args == 1:
                self.file_name = self.arguments[1]
                print("File name: {0}".format(self.file_name))
            elif self.number_of_args == 2:
                self.file_name = self.arguments[1]
                self.search_text = self.arguments[2]
                print("File name: {0}".format(self.file_name))
                print("Search text: {0}".format(self.search_text))
            else:
                    print("ERROR:Invalid number of search options provided".format(self.number_of_args))
                    print("Please provide a log file name and search text".format(self.number_of_args))
        else:
            print("ERROR:No search options provided. Please provide text with which to search".format(self.number_of_args))
                   
     # Read log file for search text
    def find_text_in_file(self, log_dir):
        print("Begin search for {0} in {1} at {2}".format(self.search_text, self.file_name, self.log_dir))
                
        log_file_path = self.log_dir +  self.file_name
        print("Full File path is {0} ".format(log_file_path))
               
        with open(log_file_path) as file:
            print("Finding lines")

            file = file.readlines()
            phrase = self.search_text

            lines_mentioning_text = []
            for line in file:
                if phrase in line:
                    print(line)
                    lines_mentioning_text.append('\t' + line)

            if len(lines_mentioning_text) == 0:
                print("NO MATCH found")

            return lines_mentioning_text  
    
    # def process_results(lines)
            
search = SearchLogFile()
search.get_args()
search.find_text_in_file(search.log_dir)
    
    