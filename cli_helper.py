import argparse
import ast
import sys

def check_help(description):
    """
    Checks if --help is passed and displays custom file info, then exits.
    """
    if "--help" in sys.argv:
        import inspect
        frame = inspect.currentframe()
        caller_file = frame.f_back.f_code.co_filename
        try:
            with open(caller_file, 'r', encoding='utf-8') as f:
                code = f.read()
        except UnicodeDecodeError:
            with open(caller_file, 'r', encoding='latin1') as f:
                code = f.read()
        tree = ast.parse(code)
        variables = []
        functions = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        variables.append(target.id)
            elif isinstance(node, ast.FunctionDef):
                functions.append(node.name)
        print(f"File: {caller_file}")
        print(f"Description: {description}")
        print("Variables:", variables)
        print("Functions:", functions)
        sys.exit(0)

def setup_cli(description, arguments):
    """
    Sets up a command-line interface using argparse.

    Args:
        description (str): A description of what the script does.
        arguments (list of dict): A list of argument definitions. Each dict should have:
            - 'name' (str): The argument name (e.g., '--input').
            - 'kwargs' (dict): Keyword arguments for parser.add_argument().

    Returns:
        argparse.Namespace: Parsed command-line arguments.

    Example:
        args = setup_cli(
            "This script processes data.",
            [
                {'name': '--input', 'kwargs': {'type': str, 'default': 'input.csv', 'help': 'Input file path'}},
                {'name': '--output', 'kwargs': {'type': str, 'default': 'output.csv', 'help': 'Output file path'}}
            ]
        )
        print(args.input, args.output)
    """
    parser = argparse.ArgumentParser(description=description)
    for arg in arguments:
        parser.add_argument(arg['name'], **arg['kwargs'])
    return parser.parse_args()
