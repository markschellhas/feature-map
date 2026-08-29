import argparse
import sys
from pathlib import Path

from featuremap._version import __version__
from featuremap.commands.check_cmd import run_check
from featuremap.commands.find_cmd import run_find
from featuremap.commands.graph_cmd import run_graph
from featuremap.commands.impact_cmd import run_impact
from featuremap.commands.init_cmd import run_bootstrap, run_init_map
from featuremap.commands.install_cmd import run_install
from featuremap.commands.list_cmd import run_list
from featuremap.commands.search_cmd import run_search
from featuremap.commands.show_cmd import run_show
from featuremap.commands.stats_cmd import run_stats
from featuremap.commands.validate_cmd import run_validate
from featuremap.config import load_config
from featuremap.discover import find_features_dir, find_repo_root
from featuremap.errors import CliError, FeaturesNotFoundError
from featuremap.output import emit, emit_error

COMMANDS = {
    "list",
    "show",
    "search",
    "find",
    "graph",
    "validate",
    "check",
    "impact",
    "stats",
    "init",
    "install",
}

OPTIONAL_FEATURES_COMMANDS = {"init", "install"}


def build_parser():
    parser = argparse.ArgumentParser(
        prog="featuremap",
        description="Feature Map CLI — cross-app architecture research tool",
    )
    parser.add_argument("--json", action="store_true", help="Machine-readable JSON output")
    parser.add_argument("--version", action="version", version=__version__)

    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("list", help="List all feature slugs")
    subparsers.add_parser("install", help="Verify install and repo setup")

    show_parser = subparsers.add_parser("show", help="Show a feature map")
    show_parser.add_argument("name", help="Feature slug")
    show_parser.add_argument("--section", help="Show a single top-level section")

    search_parser = subparsers.add_parser("search", help="Full-text search across maps")
    search_parser.add_argument("query", help="Search query")

    find_parser = subparsers.add_parser("find", help="Find maps referencing a path fragment")
    find_parser.add_argument("fragment", help="Path or file fragment")

    graph_parser = subparsers.add_parser("graph", help="Related-features graph")
    graph_parser.add_argument("name", nargs="?", help="Optional root feature for subgraph")
    graph_parser.add_argument(
        "--format",
        choices=["mermaid", "json", "dot"],
        default="mermaid",
        help="Output format",
    )

    validate_parser = subparsers.add_parser("validate", help="Validate feature maps")
    validate_parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat warnings as failures (exit 2)",
    )

    subparsers.add_parser("check", help="Check entry-point path staleness")

    impact_parser = subparsers.add_parser("impact", help="Features referencing a file")
    impact_parser.add_argument("file", help="File path fragment")
    impact_parser.add_argument(
        "--transitive",
        action="store_true",
        help="Include transitive related_features",
    )

    subparsers.add_parser("stats", help="Coverage statistics")

    init_parser = subparsers.add_parser(
        "init",
        help="Bootstrap this repo, or scaffold a feature map when <name> is given",
    )
    init_parser.add_argument(
        "name",
        nargs="?",
        help="Feature slug to scaffold (omit to bootstrap the repo)",
    )
    init_parser.add_argument("--force", action="store_true", help="Overwrite existing files")
    init_parser.add_argument(
        "--upgrade-skill",
        action="store_true",
        help="Refresh the agent skill from this package version",
    )
    init_parser.add_argument(
        "--no-agents",
        dest="agents",
        action="store_false",
        help="Do not write or update AGENTS.md",
    )
    init_parser.add_argument(
        "--no-shim",
        dest="shim",
        action="store_false",
        help="Do not write bin/feature-map",
    )
    init_parser.set_defaults(agents=True, shim=True)

    parser.add_argument(
        "bare_name",
        nargs="?",
        help="Feature name (show alias when no subcommand)",
    )

    return parser


def resolve_context(optional=False):
    start = Path.cwd()
    repo_root = find_repo_root(start)
    config = load_config(repo_root)
    try:
        features_dir = find_features_dir(start)
    except FeaturesNotFoundError:
        if optional:
            features_dir = repo_root / config.get("features_dir", ".features")
        else:
            raise
    return features_dir, repo_root, config


def dispatch(args):
    command = args.command
    as_json = args.json
    optional = command in OPTIONAL_FEATURES_COMMANDS
    features_dir, repo_root, config = resolve_context(optional=optional)

    if command is None and args.bare_name:
        if args.bare_name in COMMANDS:
            parser = build_parser()
            parser.error(f'command "{args.bare_name}" requires explicit subcommand syntax')
        command = "show"
        args.name = args.bare_name

    if command == "list":
        return 0, run_list(features_dir, as_json=as_json)

    if command == "install":
        return 0, run_install(repo_root, as_json=as_json)

    if command == "show":
        return 0, run_show(features_dir, args.name, section=args.section, as_json=as_json)

    if command == "search":
        return 0, run_search(features_dir, args.query, as_json=as_json)

    if command == "find":
        return 0, run_find(features_dir, args.fragment, as_json=as_json)

    if command == "graph":
        result = run_graph(
            features_dir,
            name=getattr(args, "name", None),
            fmt=getattr(args, "format", "mermaid"),
            as_json=as_json,
        )
        return 0, result

    if command == "validate":
        result, exit_code = run_validate(features_dir, strict=args.strict, as_json=as_json)
        return exit_code, result

    if command == "check":
        return 0, run_check(features_dir, repo_root, config.get("apps", []), as_json=as_json)

    if command == "impact":
        return 0, run_impact(
            features_dir,
            args.file,
            transitive=args.transitive,
            as_json=as_json,
        )

    if command == "stats":
        return 0, run_stats(features_dir, as_json=as_json)

    if command == "init":
        if getattr(args, "name", None):
            return 0, run_init_map(
                features_dir,
                args.name,
                force=args.force,
                as_json=as_json,
            )
        return 0, run_bootstrap(
            repo_root,
            upgrade_skill=args.upgrade_skill,
            agents=args.agents,
            shim=args.shim,
            force=args.force,
            as_json=as_json,
        )

    parser = build_parser()
    parser.print_help()
    return 1, None


def preprocess_argv(argv):
    argv = list(argv)
    if not argv:
        return argv

    json_flag = False
    cleaned = []
    for arg in argv:
        if arg == "--json":
            json_flag = True
        else:
            cleaned.append(arg)
    if json_flag:
        cleaned.insert(0, "--json")
    argv = cleaned

    idx = 0
    while idx < len(argv) and argv[idx].startswith("-"):
        idx += 1
    if idx < len(argv) and argv[idx] not in COMMANDS:
        argv.insert(idx, "show")
    return argv


def main(argv=None):
    argv = preprocess_argv(argv or sys.argv[1:])
    parser = build_parser()
    args = parser.parse_args(argv)
    as_json = args.json

    if args.command is None and not args.bare_name:
        parser.print_help()
        return 1

    try:
        exit_code, result = dispatch(args)
        if result is not None:
            graph_json = (
                args.command == "graph" and getattr(args, "format", None) == "json"
            )
            if as_json or graph_json:
                emit(result, as_json=True)
            elif isinstance(result, str):
                sys.stdout.write(result)
                if not result.endswith("\n"):
                    sys.stdout.write("\n")
            elif args.command == "list":
                emit(result, as_json=False)
        return exit_code
    except (CliError, FeaturesNotFoundError) as exc:
        return emit_error(exc, as_json=as_json)


if __name__ == "__main__":
    sys.exit(main())
