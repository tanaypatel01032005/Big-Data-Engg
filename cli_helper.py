import argparse

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
