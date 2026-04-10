from locust import HttpUser, between, task, events


@events.init_command_line_parser.add_listener
def add_arguments(parser, **kwargs):
    parser.add_argument(
        "--endpoint",
        default="/no-pool",
        help="Endpoint to hit: /no-pool or /with-pool",
    )


class User(HttpUser):
    wait_time = between(0.5, 1.5)

    @task
    def hit(self):
        self.client.get(self.environment.parsed_options.endpoint)
