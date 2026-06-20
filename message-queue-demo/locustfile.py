from locust import HttpUser, between, events, task


@events.init_command_line_parser.add_listener
def add_arguments(parser, **kwargs):
    parser.add_argument(
        "--mode",
        choices=["sync", "async", "async-backpressure"],
        default="sync",
        help="Job mode: sync, async, or async-backpressure (set MAX_QUEUE_SIZE=50 before running)",
    )


class ImageUploadUser(HttpUser):
    wait_time = between(0, 0)

    @task
    def submit_job(self):
        mode = self.environment.parsed_options.mode
        path = "/jobs/sync" if mode == "sync" else "/jobs/async"
        self.client.post(path, json={"image_name": "test.jpg"})
