from mkt_allocator.interactive_prompt import *
from mkt_allocator.model import *
import argparse, sys
import time

__version__ = "0.0.1"

def main(argv=None):
    argv = sys.argv if argv is None else argv
    argparser = argparse.ArgumentParser()
    argparser.add_argument(
        "-x",
        "--skip_interactive",
        help="Enter interactive document selector",
        dest="skip_interactive",
        action="store_true",
    )

    argparser.add_argument(
        "-d",
        "--datafile",
        type=str,
        help="Full path to data file"
    )
    argparser.add_argument(
        "-dp",
        "--documents_path",
        help="Full Path to directory holding marketing documents"
    )
    argparser.add_argument(
        "-f",
        "--filter_column",
        help="The column name in header of data file to filter on."
    )
    argparser.add_argument(
        "-skip",
        "--skip_intro",
        help="Skip introduction",
        dest="skip_intro",
        action="store_true",
    )
    args = argparser.parse_args()

    context = {
        'documents': None,
        'datafile': None,
        'output_dir': None,
        'output': dict(),
        'filter_column': None,
    }

    if not args.skip_interactive:
        print("Welcome to Marketing Allocator!\n--- :) ----\n")
        
        if not args.skip_intro:
            print_intro()

        run = True
        while run:
            opt = prompt_menu(context)
            if -1 == opt:
                print("Shutting down...")
                run = False
                break
            # returns a function or None
            handler = handle_option(opt)
            if handler == None:
                print("Invalid selection, try again.")
            else:
                handler(context)
                time.sleep(1)
        print("Goodbye!")
    else:
        print("non interactive mode")

if __name__ == '__main__':
    main()