#!/usr/bin/env python
import os
from difflib import Differ

folder_one = "../../AscendanceGeotabBills"
folder_two = "../../AscendanceGeotabBills2"

# loop through each company directory in each folder and look at files that match this regex: "*_05_2024_itemized_receipt.csv"
# if the file matches the regex, compare it with the file in the other folder, and store the file names if they are different
different_files = []
for root, dirs, files in os.walk(folder_one):
    for file in files:
        if file.endswith("_05_2024_itemized_receipt.csv"):
            file_path_one = os.path.join(root, file)
            file_path_two = file_path_one.replace(folder_one, folder_two)
            if not os.path.exists(file_path_two):
                print(f"File {file_path_two} does not exist")
            else:
                with open(file_path_one, 'r') as file_one:
                    with open(file_path_two, 'r') as file_two:
                        if file_one.read() != file_two.read():
                            different_files.append((file_path_one, file_path_two))

# use difflib to compare the contents of the different files
differ = Differ()
for file_one, file_two in different_files:
    with open(file_one, 'r') as file_one:
        with open(file_two, 'r') as file_two:
            diff = differ.compare(file_one.readlines(), file_two.readlines())
            print(f"Differences between {file_one} and {file_two}:")
            # only print differences that are not the same
            diff = [line for line in diff if not line.startswith('  ')]
            # print('\n'.join(diff))
            # print()
            # put added files and removed files into separate lists and check to see if they are the same
            added_lines = [line[2:] for line in diff if line.startswith('+ ')]
            removed_lines = [line[2:] for line in diff if line.startswith('- ')]
            added_lines_set = set(added_lines)
            removed_lines_set = set(removed_lines)

            if added_lines_set == removed_lines_set:
                print("The files have the same differences")
                print()
            else:
                print("The files have different differences")
                print('\n'.join(added_lines))
                print('\n'.join(removed_lines))
            