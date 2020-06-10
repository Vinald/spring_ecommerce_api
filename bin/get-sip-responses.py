import os
import time
import sys
import ast
import json

asterisk_log_file = "/var/log/asterisk/test_log"
# current = open(asterisk_log_file, "r")
# curino = os.fstat(current.fileno()).st_ino
# while True:
#     while True:
#         file_content = current.read(1024)
#         # file_content = current.readlines()
#         if file_content == "":
#             break
#         sys.stdout.write(file_content)
#
#
#     try:
#         if os.stat(asterisk_log_file).st_ino != curino:
#             new = open(asterisk_log_file, "r")
#             current.close()
#             current = new
#             curino = os.fstat(current.fileno()).st_ino
#             continue
#     except IOError:
#         pass
#     time.sleep(1)

# trying = current.readlines()[20]
# box = ast.literal_eval(trying)
# print(type(box))

file = open(asterisk_log_file, "r")
mylist = []
dict = {}
trunk = "staging-trunk"

file_content = file.readlines()
for i in range(len(file_content)):
    if file_content[i] is not "":
        box = ast.literal_eval(file_content[i])
        mylist.append(box)

statuses = ["busy", "congested"]
for i in range(len(mylist)):
    if "Called" in mylist[i]["logmsg"]["message"]:
        id_number = mylist[i]["identifiers"]["lwp"]
        time_stamp = mylist[i]["timestamp"]
        dialed_number = mylist[i]["logmsg"]["message"].split("/+")[1]
        dict.update({str(id_number): "{}, {}".format(time_stamp, dialed_number)})
    # for key in dict.keys():
    #     if key in mylist[i]["identifiers"]["lwp"] and statuses in mylist[i]["logmsg"]["message"]:
    #         print(mylist[i])
    res = [ele for ele in statuses if(ele in mylist[i]["logmsg"]["message"])]
    if bool(res) is True:
        print(mylist[i]["logmsg"]["message"].split(''))
        print(mylist[i-1]["logmsg"]["message"])

# print(dict.keys())
