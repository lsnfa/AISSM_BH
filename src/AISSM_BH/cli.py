"""
Command-line interface for AISSM_BH
"""

import os
import sys
import argparse
import logging

from AISSM_BH.core.baihong_mdagent import BHMDAgent
from AISSM_BH.utils.terminal import Colors, print_message
from AISSM_BH.utils.logging_utils import setup_logging
from AISSM_BH.config import DEFAULT_WORKSPACE, DEFAULT_MODEL, DEFAULT_OPENAI_URL


def parse_arguments():
    """
    Parse command-line arguments.

    Returns
    -------
    argparse.Namespace
        Parsed arguments
    """
    parser = argparse.ArgumentParser(description="AISSM_BH")
    parser.add_argument("--api-key", help="API key for LLM service")
    parser.add_argument("--url",
                        help=(
                            "The url of the LLM service, "
                            "\ndeepseek: https://api.deepseek.com/chat/completions"
                            "\nopenai: https://api.openai.com/v1/chat/completions"
                        ),
                        default=DEFAULT_OPENAI_URL)
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Model to use for LLM")
    parser.add_argument("--workspace", default=DEFAULT_WORKSPACE, help="Workspace directory")
    parser.add_argument("--prompt", help="Starting prompt for the LLM")
    parser.add_argument("--no-color", action="store_true", help="Disable colored output")
    parser.add_argument("--log-file", default="baihong_mdagent.log", help="Log file path")
    parser.add_argument("--log-level", default="INFO",
                        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                        help="Logging level")
    parser.add_argument("--mode", default="copilot", choices=['copilot', 'agent'],
                        help="The copilot mode or agent mode, copilot will be more like a advisor."
                        )
    parser.add_argument(
        "--config",
        help="Path to a YAML configuration file. Options in CLI override those in the file."
    )

    args = parser.parse_args()

    # ---- 加载 YAML 配置文件（若指定）----
    config_api_key = None
    if args.config:
        import yaml
        try:
            with open(args.config, "r") as f:
                config = yaml.safe_load(f)
            if not isinstance(config, dict):
                print("Config file must contain a YAML mapping.")
                sys.exit(1)

            known_opts = set()
            for action in parser._actions:
                if action.dest not in ("help", "config"):
                    known_opts.add(action.dest)

            for key, value in config.items():
                if key == "config":
                    continue
                if key == "api_key":
                    config_api_key = value
                    continue
                if key not in known_opts:
                    print(f"Warning: Unknown option in config file: '{key}'. Ignored.")
                    continue
                default = parser.get_default(key)
                if getattr(args, key) == default:
                    setattr(args, key, value)

            logging.info(f"Loaded configuration from {args.config}")
        except FileNotFoundError:
            print(f"Config file not found: {args.config}")
            sys.exit(1)
        except yaml.YAMLError as e:
            print(f"Error parsing config file: {e}")
            sys.exit(1)
    # ------------------------------------

    args.config_api_key = config_api_key
    return args


def main():
    """
    Main entry point for the CLI
    """
    from AISSM_BH.core.enums import MessageType

    args = parse_arguments()

    # Setup logging
    log_level = getattr(logging, args.log_level)
    setup_logging(args.log_file, level=log_level)

    # Disable colors if requested or if not in a terminal
    if args.no_color or not sys.stdout.isatty():
        Colors.disable_colors()

    # Display splash screen
    print_message("", style="divider")
    print_message("AISSM_BH", MessageType.TITLE, style="box")
    print_message("A molecular dynamics simulation assistant powered by AI, created by BHAI Team.", MessageType.INFO)
    print_message("", style="divider")

    try:
        # Check for API key
        if args.url == "https://api.openai.com/v1/chat/completions":
            api_key = args.api_key or os.environ.get("OPENAI_API_KEY") or args.config_api_key
        elif args.url == "https://api.deepseek.com/chat/completions":
            api_key = args.api_key or os.environ.get("DEEPSEEK_API_KEY") or args.config_api_key
        else:
            api_key = args.api_key or args.config_api_key

        if not api_key:
            print_message(
                "API key not found. Please provide an API key using --api-key or set the "
                "OPENAI_API_KEY or DEEPSEEK_API_KEY environment variable.",
                MessageType.ERROR
            )
            sys.exit(1)

        # Create and run BH MD agent
        print_message(f"Initializing with model: {args.model}", MessageType.INFO)
        print_message(f"Using workspace: {args.workspace}", MessageType.INFO)

        agent = BHMDAgent(
            api_key=api_key,
            model=args.model,
            workspace=args.workspace,
            url=args.url,
            mode=args.mode
        )
        agent.run(starting_prompt=args.prompt)

    except KeyboardInterrupt:
        print_message("\nExiting the BH MD agent. Thank you for using AISSM_BH!",
                     MessageType.SUCCESS, style="box")
    except Exception as e:
        error_msg = str(e)
        logging.error(f"Error running BH MD agent: {error_msg}")
        print_message(f"Error running BH MD agent: {error_msg}",
                     MessageType.ERROR, style="box")


if __name__ == "__main__":
    main()
