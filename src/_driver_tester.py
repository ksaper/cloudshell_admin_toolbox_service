from driver import CloudshellAdminToolboxDriver
from cloudshell.shell.core.driver_context import InitCommandContext, ResourceCommandContext
import cloudshell.api.cloudshell_api

if __name__ == "__main__":
    import mock
    shell_name = "DebuggingExample"

    # cancellation_context = mock.create_autospec(CancellationContext)
    context = mock.create_autospec(ResourceCommandContext)
    context.resource = mock.MagicMock()
    context.reservation = mock.MagicMock()
    context.connectivity = mock.MagicMock()
    context.reservation.reservation_id = "05f1e4d3-0e39-4fbd-a67f-226349823f71"
    context.resource.address = "10.0.1.10"
    context.resource.name = "CloudShell Admin Toolbox"
    context.resource.attributes = dict()
    # context.resource.attributes['User'] = 'admin'
    # context.resource.attributes['Password'] = 'DxTbqlSgAVPmrDLlHvJrsA=='  # 'admin'
    # context.resource.attributes['Password'] = 'fCg3/CAb78GJjbJ+YHP14Q=='  # other

    context.reservation.domain = "Global"
    context.connectivity.server_address = "10.0.1.10"
    context.connectivity.cloudshell_api_port = '8029'
    temp_api = cloudshell.api.cloudshell_api.CloudShellAPISession(host=context.connectivity.server_address,
                                                                  username="admin",
                                                                  password="theCS_@dm1n?",
                                                                  domain=context.reservation.domain)
    context.connectivity.admin_auth_token = temp_api.token_id

    services = temp_api.GetReservationDetails(context.reservation.reservation_id).ReservationDescription.Services
    for service in services:
        for attr in service.Attributes:
            if attr.Name == 'Eggplant Functional Service.Password':
                print(attr.Name, attr.Value, temp_api.DecryptPassword(attr.Value).Value)
            else:
                print(attr.Name, attr.Value)

    driver = CloudshellAdminToolboxDriver()
    driver.initialize(context)
    driver.list_all_reservation_assets(context)