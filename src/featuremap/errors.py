class FeaturesNotFoundError(Exception):
    def __init__(self, message=None, suggestion=None):
        self.message = message or (
            "No .features/ found. Run `featuremap init` from the repo root."
        )
        self.suggestion = suggestion or (
            'Run "featuremap init" to scaffold .features/, the agent skill, and a bin shim.'
        )
        super().__init__(self.message)


class CliError(Exception):
    def __init__(self, message, suggestion=None, exit_code=1):
        self.message = message
        self.suggestion = suggestion
        self.exit_code = exit_code
        super().__init__(message)
