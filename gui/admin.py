from gui.admin_dashboards import BoothDashboard


class AdminScreen(BoothDashboard):

    def __init__(
        self,
        root,
        on_logout=None
    ):

        super().__init__(
            root,
            on_logout=on_logout
        )