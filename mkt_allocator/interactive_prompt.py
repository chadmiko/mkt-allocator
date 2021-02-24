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

from .model import Datafile, DocumentList, allocate

# subroutine to Option 1: Select Documents from Path
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
    new_docs = True
    if context['documents']:
        new_docs = False

    if new_docs:
        doc_filepath_prompt(context)

    complete = False
    values = []
    labels = context['documents'].keys()

    while not complete:
        selected_doc = select_document_prompt(labels)
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
                    context['documents'][selected_doc].expect(value)
                print("Values assigned ok!")
                complete = True
            else:
                print("Invalid entry.")

    return values

# Option 2:  Print mappings
def print_mappings(context):
    if len(context['documents']) < 1:
        print("No mappings to print.")
        return 

    tpl = "{}: {}"

    print("Filter Mappings:\n" + ('-'*20))
    for doc in context['documents'].values():
        print(tpl.format(doc.label, ', '.join(sorted(list(doc.expectations)))))


# subroutine on Option 5
def output_dir_prompt(context):
    newdir = True

    if context['output_dir'] and os.path.exists(context['output_dir']):
        print("Use existing output directory: %s?" % context['output_dir'])
        answer = prompt("Type 'Y' to use existing directory, 'N' to enter new directory: ", \
            completer=WordCompleter(['Y', 'N']))

        if answer == 'Y':
            newdir = False
           

    if newdir:
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

    return context['output_dir']

# subroutine to Option 5: Select Data file
def data_filepath_prompt(context):
    newfile = True

    if context['datafile']:
        completer = WordCompleter(['Y', 'N'])
        print('Found datafile:  %s' % context['datafile'].path)
        reuse = prompt("Type 'Y' to use existing datafile, 'N' to select other datafile:", completer=completer)

        if reuse != 'Y':
            newfile = True
        else:
            newfile = False

    if newfile:
        path_completer = PathCompleter(only_directories=False)
        selected_datafile_path = prompt(
            "Select Input Data file: ", completer=path_completer
        )
        context['datafile'] = Datafile(selected_datafile_path)
    
    return context['datafile']

# Option 5
def allocate_datafile_prompt(context):
    # Todo consider getting datafile at runtime to allow
    # For one configuration to apply to multiple data files
    datafile = data_filepath_prompt(context)
    output_dir = output_dir_prompt(context)
    
    # TODO test documents for mappings

    column = False
    header = context['datafile'].header

    while not column:
        print("Column choices are: " + ', '.join(header) + "\n")
        column_completer = FuzzyWordCompleter(header)
        column = prompt(
            "Enter a Column to filter on: ", completer=column_completer
        )
        if column in header:
            break
        column = False
        print("Invalid entry, try again (must choose an item from the list).")

    writer = csv.writer
    nobody = allocate(datafile, context['documents'], column)
    nobody.save_buffer(output_dir, writer)
    # TODO iterate on documents, not documents.values
    [doc.save_buffer(output_dir, writer, header) for doc in context['documents'].values()]
    
    print("Done.  Files saved to {}".format(output_dir))

def prompt_menu(context):
    menu = """
Select one:
1: Map Filter Criteria to Document
2: Print Filter Mappings
3: Allocate a Datafile to Documents
Q: Quit 

Enter number or Q to quit:  """
        
    option = -1

    while True:
        selected_item = prompt(menu)
        if selected_item in ['q', 'Q']:
            break
        try:
            option = int(selected_item)
            if option in [1,2,3]:
                break
        except ValueError:
            pass #trap it

        print_formatted_text(HTML('<ansired>Invalid option, try again :(</ansired>'))
        
    return option

def handle_option(opt):
    choices = {
        1: assign_document_filters_prompt,
        2: print_mappings,
        3: allocate_datafile_prompt,
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