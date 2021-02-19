from prompt_toolkit import prompt
from prompt_toolkit.completion import (
    WordCompleter,
    Completer, 
    FuzzyWordCompleter,
)
from prompt_toolkit.completion.filesystem import PathCompleter
from prompt_toolkit import print_formatted_text, HTML
import pathlib
import os
import csv
import time

from .model import Datafile, DocumentList

# subroutine to Option 5: Select Data file
def data_filepath_prompt(context):
    path_completer = PathCompleter(only_directories=False)
    selected_datafile_path = prompt(
        "Select Input Data file: ", completer=path_completer
    )
    print("%s...done." % selected_datafile_path)
   
    context['datafile'] = Datafile(selected_datafile_path)
    return selected_datafile_path

# subroutine to Option 1: Select Documents
def doc_filepath_prompt(context):
    path_completer = PathCompleter(only_directories=True)
    selected_doc_path = prompt(
        "Select Path to Documents: ", completer=path_completer
    )
    print("Path to docs: %s" % selected_doc_path)
    context['documents'] = DocumentList(selected_doc_path)
    return selected_doc_path

# This is part of Option 1 but not called from main menu
def select_document_prompt(docs):    
    while True:
        print("Documents to choose from: ")
        [print(doc) for doc in docs]
        print(docs)
        document_completer = FuzzyWordCompleter(docs)
        selected_document = prompt(
            "Select Document: ", completer=document_completer
        )
        if selected_document in docs:
            return selected_document
        else:
            print("Invalid choice, try again.")
    

# Option 1:  map zipcode criteria to a document
def assign_document_filters_prompt(context):
    if len(context['documents']) < 1:
        doc_filepath_prompt(context)

    complete = False
    values = []
    documents = context['documents'].items

    while not complete:
        selected_doc = select_document_prompt(documents)
        valid_values = False
        
        while not valid_values:
            selected_values = prompt("""
Associate '%s' with rows in the Datafile 
using filter criteria.
Enter criteria (i.e. zipcodes) separated by commas: """ % (selected_doc)
            )
            values = list(map(str.strip, selected_values.split(',')))
            if len(values) > 0:
                #TODO Remove existing doc mappings?
                valid_values = True
                for value in values:
                    context['database'].add(value, selected_doc)
                print("Values assigned ok!")
                complete = True
            else:
                print("Invalid entry.")

    return values

# Option 4:  Print mappings
def print_mappings(context):
    tpl = "{}: {}"
    items = context['database'].db.items()

    if len(items) < 1:
        print("No mappings to print.")
        return 

    print("Filter Mappings:\n" + ('-'*20))
    for k, v in items:
        print(tpl.format(k, ', '.join(list(v))))


# subroutine on Option 5
def output_dir_prompt(context):
    path_completer = PathCompleter(only_directories=True)
    output_dir = None

    while True:
        output_dir = prompt(
            "Select an Output Directory to store output files:", completer=path_completer
        )
        path_obj = pathlib.Path(output_dir)
        if os.path.exists(path_obj):
            context['output_dir'] = path_obj
            print("Output directory is %s" % path_obj)
            break
        print("Invalid directory, try again.")

    return path_obj

# Option 5
def write_filtered_files_prompt(context):
    if not context['datafile']:
        data_filepath_prompt(context)
    
    if not context['output_dir']:
        output_dir_prompt(context)
    
    if len(context['database']) < 1:
        print("No mappings configured, abort. (HINT: try option 3)")
        return

    column = False
    header = context['datafile'].header

    while not column:
        print("Column choices are: " + ', '.join(header) + "\n")
        column_completer = FuzzyWordCompleter(header)
        column = prompt(
            "Enter a Column to filter on: ", completer=column_completer
        )
        if column and column in header:
            context['filter_column'] = column
            break
        column = False
        print("Invalid entry, try again (must choose an item from the list).")

    groups = {}

    context['datafile'].rewind()
    csv_file = csv.reader(context['datafile'].fh)
    _ = next(csv_file) # skip header
    i = context['datafile'].header.index(column)
    
    for row in csv_file:
        value = row[i]  # e.g. 15601
        if value not in groups:
            groups[value] = []
        groups[value].append(row)
    
    # write separate files for each group
    unassigned = list()
    result = dict()

    for value, rows in groups.items():
        #path = os.path.join(context['output_dir'], f"{filter_val}.csv"
        docs = context['database'].get(value)
        num_recipients = len(docs)

        if num_recipients == 1:
            doc = docs.pop()
            result[doc] = rows 
        else: 
            #TODO THIS DOESN'T WORK
            if docs_length > 0:
                if docs_length < num_recipients:
                    print("WARN: {} has more documents than data available." % value)
                bucket_size = max(math.floor(len(rows)/num_recipients), 1)
                
                for bucket in split_by_n(rows, bucket_size):
                

            # check for odd lot last bucket
            else:
                print("{} is unallocated and will be saved to nobody.csv" % value)

        
    

def prompt_menu(context):
    menu = """
Select one:
1: Map Filter Criteria to Document
2: Print Filter Mappings
5: Write Filtered Files
9: Generate Output Files
Q: Quit 

Enter number or Q to quit:  """
        
    option = -1

    while True:
        selected_item = prompt(menu)
        if selected_item in ['q', 'Q']:
            break
        try:
            option = int(selected_item)
            if option in [1,2,5,9]:
                break
        except ValueError:
            pass #trap it

        print_formatted_text(HTML('<ansired>Invalid option, try again :(</ansired>'))
        
    return option

def handle_option(opt):
    choices = {
        1: assign_document_filters_prompt,
        2: print_mappings,
        5: write_filtered_files_prompt,
    }
    return choices.get(opt, None)

def print_intro():
    print("Tell me a datafile (i.e. list of T65s, etc)...")

    time.sleep(2)
    print("then give me a directory containing documents (i.e. flyers)...")

    time.sleep(2)
    print("""
And I'll give you a way to associate each flyer 
with a list of zipcodes (or other criteria)...""")

    time.sleep(6)
    print("""
Once you've mapped your documents to criteria, 
I'll split up the datafile into output files that 
go with each document.""")

    time.sleep(9)
    print("\nLet's get started!")
    time.sleep(1)