from mash.exceptions import UserCancelled


class ListFlow:
    def __init__(
        self,
        console,
        disambiguator,
        browse_mode,
        action_menu,
        list_scope,
        run_with_args_fn,
        directory_context: str,
    ):
        self.console = console
        self.disambiguator = disambiguator
        self.browse_mode = browse_mode
        self.action_menu = action_menu
        self.list_scope = list_scope
        self.run_with_args_fn = run_with_args_fn
        self.directory_context = directory_context

    def run(self, intent) -> None:
        scope = self.list_scope.list_target_from_arguments(
            intent.args, self.directory_context
        )
        if self.console.dry_run:
            self.console.confirm_and_run(f"ls -la {self.list_scope.scope_label(scope)}")
            return
        try:
            self.browse_mode.run(scope, self.directory_context, self.run_with_args_fn)
        except UserCancelled:
            self.console.print_info("Cancelled.")
