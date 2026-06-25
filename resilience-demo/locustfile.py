from locust import HttpUser, between, events, task


@events.init_command_line_parser.add_listener
def add_arguments(parser, **kwargs):
    parser.add_argument(
        "--strategy",
        choices=["direct", "naive", "backoff", "circuit"],
        default="naive",
        help="Resilience strategy to test",
    )


class ProfileUser(HttpUser):
    wait_time = between(0, 0)

    @task
    def fetch_profile(self):
        strategy = self.environment.parsed_options.strategy
        self.client.get(f"/profile?strategy={strategy}")
