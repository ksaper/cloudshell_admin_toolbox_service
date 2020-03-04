from cloudshell.shell.core.resource_driver_interface import ResourceDriverInterface
from cloudshell.shell.core.driver_context import InitCommandContext, ResourceCommandContext, AutoLoadResource, \
    AutoLoadAttribute, AutoLoadDetails, CancellationContext
# from data_model import *  # run 'shellfoundry generate' to generate data model classes
from cloudshell.api.cloudshell_api import CloudShellAPISession as cs_api
from cloudshell.api.cloudshell_api import SandboxDataKeyValue
from cloudshell.api.common_cloudshell_api import CloudShellAPIError as cs_error
import time

MAX_RANGE = (30 * 24 * 60 * 60)  # 30 days, in seconds
RESOURCE_LIVE_STATUS = {
            'none': '',
            'online': 'Online',
            'offline': 'Offline',
            'info': 'Info',
            'error': 'Error',
            'public': 'Public',
            'private': 'Private',
            '00%': 'Progress 0',
            '10%': 'Progress 10',
            '20%': 'Progress 20',
            '30%': 'Progress 30',
            '40%': 'Progress 40',
            '50%': 'Progress 50',
            '60%': 'Progress 60',
            '70%': 'Progress 70',
            '80%': 'Progress 80',
            '90%': 'Progress 90',
            '100%': 'Progress 100'
        }

RESERVATION_LIVE_STATUS = {
            'downloading': 'Downloading',
            'installing': 'Installing',
            'configuring': 'Configuring',
            'gen_report': 'Generating Report',
            'complete_good': 'Completed successfully',
            'complete_bad': 'Completed unsuccessfully',
            'error': 'Error',
            'in_prog': 'In Progress',
            '00%': 'Progress 0',
            '10%': 'Progress 10',
            '20%': 'Progress 20',
            '30%': 'Progress 30',
            '40%': 'Progress 40',
            '50%': 'Progress 50',
            '60%': 'Progress 60',
            '70%': 'Progress 70',
            '80%': 'Progress 80',
            '90%': 'Progress 90',
            '100%': 'Progress 100'
        }


class CloudshellAdminToolboxDriver (ResourceDriverInterface):

    def __init__(self):
        """
        ctor must be without arguments, it is created with reflection at run time
        """
        self.connection_list = list()
        self.child_list = list()

    def initialize(self, context):
        """
        Initialize the driver session, this function is called everytime a new instance of the driver is created
        This is a good place to load and cache the driver configuration, initiate sessions etc.
        :param InitCommandContext context: the context the command runs on
        """
        pass

    def cleanup(self):
        """
        Destroy the driver session, this function is called everytime a driver instance is destroyed
        This is a good place to close any open sessions, finish writing to log files
        """
        pass

    def _open_cloudshell_session(self, context):
        """

        :param ResourceCommandContext context:
        :return: CloudShellAPISession
        """
        return cs_api(context.connectivity.server_address,
                      domain=context.reservation.domain,
                      port=context.connectivity.cloudshell_api_port,
                      token_id=context.connectivity.admin_auth_token)

    def _get_resoruces_in_res(self, cs_session, res_id):
        return cs_session.GetReservationDetails(res_id).ReservationDescription.Resources

    def _get_apps_in_res(self, cs_session, res_id):
        return cs_session.GetReservationDetails(res_id).ReservationDescription.Apps

    def _inner_children(self, dev_details):
        self.child_list.append(dev_details.Name)
        for child in dev_details.ChildResources:
            self._inner_children(child)

    def _inner_connections(self, dev_details):
        temp = [dev_details.Name, '']
        for each in dev_details.Connections:
            if each.FullPath:
                temp[1] = each.FullPath
            else:
                temp[1] = 'Not Connected'

        self.connection_list.append(temp)
        for child in dev_details.ChildResources:
            self._inner_connections(child)

    def _time_to_ISO8601(self, dts_in):
        # in_tup = time.strptime(dts_in, '%m/%d/%Y %H:%M')
        # return time.strftime('%Y-%m-%d %H:%M', time.localtime(time.mktime(in_tup) - time.timezone))
        #
        date, time = dts_in.split(' ', 1)
        MM, DD, YYYY = date.split('/')
        return '%s-%s-%s %s UTC' % (YYYY, MM, DD, time)

    def _validate_in_reservation(self, cs_session, res_id, target):
        """

        :param CloudShellAPISession cs_session:
        :param str res_id: Current Reservation ID
        :param str target: Device Name or Address (Address should only be parent)
        :return: bool
        """
        found = False
        item_name = None
        resources = self._get_resoruces_in_res(cs_session, res_id)
        apps = self._get_apps_in_res(cs_session, res_id)

        for resource in resources:
            if target == resource.Name or target == resource.FullAddress:
                item_name = resource.Name
                found = 'Resource'
                break

        if not found:
            for app in apps:
                if target in app.Name:
                    item_name = app.Name
                    found = 'App'
                    break

        return found, item_name

    def _get_current_reservations(self, cs_session, name):
        """

        :param CloudShellAPISession cs_session:
        :param str name:
        :return:
        """
        start_time = time.strftime('%d/%m/%Y %H:%M',
                                   time.localtime(time.mktime(time.localtime()) + time.timezone))
        stop_time = time.strftime('%d/%m/%Y %H:%M',
                                  time.localtime(time.mktime(time.localtime()) + time.timezone + MAX_RANGE))

        reservations = cs_session.GetResourceAvailabilityInTimeRange(resourcesNames=[name],
                                                                     startTime=start_time,
                                                                     endTime=stop_time,
                                                                     showAllDomains=True
                                                                     ).Resources[0].Reservations
        return sorted(reservations, key=lambda x: x.StartTime)

    def get_attributes(self, context, target, decrypt_passwords):
        """

        :param ResourceCommandContext context:
        :param target:
        :param decrypt_passwords:
        :return: None
        """
        if decrypt_passwords.upper() == 'TRUE':
            open_k = True
        else:
            open_k = False
        cs_session = self._open_cloudshell_session(context)

        res_id = context.reservation.reservation_id
        w2out = cs_session.WriteMessageToReservationOutput

        t_type, t_name = self._validate_in_reservation(cs_session, res_id, target)

        attributes = dict()
        if t_type == 'Resource':
            aa = cs_session.GetResourceDetails(t_name).ResourceAttributes
            for a in aa:
                if open_k and a.Type == 'Password':
                    attributes[a.Name.split('.')[-1]] = cs_session.DecryptPassword(a.Value).Value
                elif not open_k and a.Type == 'Password':
                    attributes[a.Name.split('.')[-1]] = '-=+++++=-'
                else:
                    attributes[a.Name.split('.')[-1]] = a.Value

            w2out(res_id, '\n> Attributes for {}'.format(t_name))
            for key in sorted(attributes.keys()):
                # w2out(res_id, '  - {:.<35} {}'.format(key, attributes[key]))
                # w2out(res_id, '  - {}: {}'.format(key, attributes[key]))
                w2out(res_id, '  - {:>35}: {}'.format(key, attributes[key]))
            w2out(res_id, '{}='.format('=-'*36))

        elif t_type == 'App':
            w2out(res_id, '{} is a non deployed-app, no information to retrieve'.format(t_name))

        else:
            w2out(res_id, '\n!! - Unable to locate {} in this reservation'.format(target))

    def set_attribute_value(self, context, target, attribute_name, attribute_value):
        """

        :param context:
        :param target:
        :param attribute_name:
        :param attribute_value:
        :return:
        """
        cs_session = self._open_cloudshell_session(context)
        w2out = cs_session.WriteMessageToReservationOutput
        res_id = context.reservation.reservation_id

        if self._validate_in_reservation(cs_session, res_id, target):
            attributes = cs_session.GetResourceDetails(target).ResourceAttributes
            long_list = list()
            short_list = list()
            for a in attributes:
                long_list.append(a.Name)
                short_list.append(a.Name.split('.')[-1])

            if attribute_name in long_list:
                try:
                    cs_session.SetAttributeValue(target, attribute_name, attribute_value)
                    w2out(res_id, '\n> Attribute {} on {} set to:  {}'.format(attribute_name, target, attribute_value))
                except cs_error as e:
                    w2out(res_id, '\n!! - Error: Updating Attribute {} on {} \n   {}'.format(attribute_name,
                                                                                             target, e.message))
            elif attribute_name in short_list:
                full_att_name = long_list[short_list.index(attribute_name)]
                try:
                    cs_session.SetAttributeValue(target, full_att_name, attribute_value)
                    w2out(res_id, '\n> Attribute {} on {} set to:  {}'.format(full_att_name, target, attribute_value))
                except cs_error as e:
                    w2out(res_id, '\n!! - Error: {}'.format(e.message))
            else:
                w2out(res_id, '\n!! - Unable to locate an attribute named {} for {}'.format(attribute_name, target))

            w2out(res_id, '{}='.format('=-' * 36))
        else:
            w2out(res_id, '\n!! - Unable to locate {} in this reservation'.format(target))

    def get_summary(self, context, target):
        """

        :param ResourceCommandContext context:
        :param str target:
        :return: None
        """
        cs_session = self._open_cloudshell_session(context)
        w2out = cs_session.WriteMessageToReservationOutput
        res_id = context.reservation.reservation_id

        t_type, t_name = self._validate_in_reservation(cs_session, res_id, target)
        summary = ''

        if t_type == 'Resource':
            resource_details = cs_session.GetResourceDetails(t_name)

            doms = ['Global']
            if len(resource_details.Domains) > 0:
                for d in resource_details.Domains:
                    doms.append(d.Name)

            status = []
            if resource_details.Excluded:
                status.append('!! Excluded')
            if resource_details.ResourceLiveStatusName:
                status.append('Live Status: {}({})'.format(resource_details.ResourceLiveStatusName,
                                                           resource_details.ResourceLiveStatusDescription))

            w2out(res_id, '\n> Summary for {}:'.format(resource_details.Name))
            msg = ' - {:.<16} {}'.format('Address', resource_details.Address)
            msg += '\n - {:.<16} {}'.format('Full Address', resource_details.FullAddress)
            msg += '\n - {:.<16} {}'.format('Family', resource_details.ResourceFamilyName)
            msg += '\n - {:.<16} {}'.format('Model', resource_details.ResourceModelName)
            msg += '\n - {:.<16} {}'.format('Domains', ', '.join(doms))
            msg += '\n - {:.<16} {}'.format('Folder Path', resource_details.FolderFullPath)
            if status:
                msg += '\n - {:.<16}\n   {}'.format('Current Status', '\n   '.join(status))
            else:
                msg += '\n - {:.<16} None'.format('Current Status')
            w2out(res_id, msg)
            w2out(res_id, '{}='.format('=-' * 36))

        elif t_type == 'App':
            pass
        else:
            w2out(res_id, '\n > {} Is neither fish nor fowl (Resource or App) - No info to get'.format(target))

    def get_all_reservations(self, context):
        """

        :param ResourceCommandContext context:
        :return:
        """
        cs_session = self._open_cloudshell_session(context)
        w2out = cs_session.WriteMessageToReservationOutput
        res_id = context.reservation.reservation_id

        w2out(res_id, '\n')
        for resource in cs_session.GetReservationDetails(res_id).ReservationDescription.Resources:
            if '/' not in resource.Name:
                reservations = self._get_current_reservations(cs_session, resource.Name)
                w2out(res_id, '> {} Used in {} Reservations:'.format(resource.Name, len(reservations)))
                for r in reservations:
                    r_status = cs_session.GetReservationDetails(r.ReservationId).ReservationDescription.Status
                    if r_status != 'Pending':
                        r_status = 'Reserved'
                    msg = ' - ID: {}'.format(r.ReservationId)
                    msg += '\n   Name: {:<26}  Owner: {}'.format(r.ReservationName, r.Owner)
                    msg += '\n   Status: {}'.format(r_status)
                    msg += '\n   Start Time:    {}'.format(self._time_to_ISO8601(r.StartTime))
                    msg += '\n   Scheduled End: {}'.format(self._time_to_ISO8601(r.EndTime))
                    w2out(res_id, msg)
        w2out(res_id, '{}='.format('=-' * 36))

    def get_reservations(self, context, target):
        """

        :param ResourceCommandContext context:
        :param str target:
        :return:
        """
        cs_session = self._open_cloudshell_session(context)
        res_id = context.reservation.reservation_id
        self.connection_list = list()

        w2out = cs_session.WriteMessageToReservationOutput

        t_type, t_name = self._validate_in_reservation(cs_session, res_id, target)

        if t_type == 'Resource':
            reservations = self._get_current_reservations(cs_session, t_name)
            w2out(res_id, '\n> {} Used in {} Reservations:'.format(t_name, len(reservations)))
            for r in reservations:
                r_status = cs_session.GetReservationDetails(r.ReservationId).ReservationDescription.Status
                if r_status != 'Pending':
                    r_status = 'Reserved'
                msg = ' - ID: {}'.format(r.ReservationId)
                msg += '\n   Name: {:<26}  Owner: {}'.format(r.ReservationName, r.Owner)
                msg += '\n   Status: {}'.format(r_status)
                msg += '\n   Start Time:    {}'.format(self._time_to_ISO8601(r.StartTime))
                msg += '\n   Scheduled End: {}'.format(self._time_to_ISO8601(r.EndTime))
                w2out(res_id, msg)
            w2out(res_id, '{}='.format('=-' * 36))

        elif t_type:
            w2out(res_id, '\n!! - {} is not a Resource, reservations are a non-issue'.format(t_name))
        else:
            w2out(res_id, '\n!! - {} is not in the current reservation'.format(target))

    def get_children(self, context, target):
        """

        :param ResourceCommandContext context:
        :param str target:
        :return:
        """
        cs_session = self._open_cloudshell_session(context)
        res_id = context.reservation.reservation_id
        self.connection_list = list()

        w2out = cs_session.WriteMessageToReservationOutput

        t_type, t_name = self._validate_in_reservation(cs_session, res_id, target)

        if t_type == 'Resource':
            children = cs_session.GetResourceDetails(t_name).ChildResources

            for child in children:
                self._inner_children(child)

            w2out(res_id, '\n> Children for {}'.format(t_name))
            if self.child_list:
                for kid in sorted(self.child_list):
                    # w2out(res_id, '  - {}'.format(kid.split('/')[-1]))
                    w2out(res_id, '  - {}'.format(kid))
            else:
                w2out(res_id, '  - None')

            w2out(res_id, '{}='.format('=-' * 36))

        elif t_type == 'App':
            w2out(res_id, '!! - {} is an App, and has no Children'.format(t_name))
        else:
            w2out(res_id, '!! - {} Not found in this reservation'.format(target))

    def get_connections(self, context, target):
        """

        :param ResourceCommandContext context:
        :param str target:
        :return:
        """
        cs_session = self._open_cloudshell_session(context)
        res_id = context.reservation.reservation_id
        self.connection_list = list()

        w2out = cs_session.WriteMessageToReservationOutput

        t_type, t_name = self._validate_in_reservation(cs_session, res_id, target)

        if t_type == 'Resource':
            children = cs_session.GetResourceDetails(t_name).ChildResources

            for child in children:
                self._inner_connections(child)

            w2out(res_id, '\n> Connections for {}'.format(t_name))
            if self.connection_list:
                for kid in self.connection_list:
                    w2out(res_id, '  - {}'.format(': '.join(kid)))
            else:
                w2out(res_id, '  - None')

            w2out(res_id, '{}='.format('=-' * 36))

        elif t_type == 'App':
            w2out(res_id, '\n!! - {} is an App, and has no Children'.format(t_name))
        else:
            w2out(res_id, '\n!! - {} Not found in this reservation'.format(target))

    def set_resource_status(self, context, target, status):
        """

        :param str target:
        :param ResourceCommandContext context:
        :param str status:
        :return:
        """
        cs_session = self._open_cloudshell_session(context)
        res_id = context.reservation.reservation_id
        w2out = cs_session.WriteMessageToReservationOutput

        t_type, t_name = self._validate_in_reservation(cs_session, res_id, target)

        if t_type == 'Resource':
            if status == 'none':
                result = cs_session.SetResourceLiveStatus(resourceFullName=t_name)
            else:
                result = cs_session.SetResourceLiveStatus(resourceFullName=t_name,
                                                          liveStatusName=RESOURCE_LIVE_STATUS[status]
                                                          )
            w2out(res_id, '\n> Set {} status to {}\n'.format(t_name, status))
            w2out(res_id, '{}='.format('=-' * 36))
        elif t_type == 'App':
            w2out(res_id, '\n!! - {} is an App, cannot set a live status to before deployment'.format(t_name))
        else:
            w2out(res_id, '\n!! - {} Not found in this reservation'.format(target))

    def get_reservation_information(self, context):
        """

        :param ResourceCommandContext context:
        :return:
        """
        cs_session = self._open_cloudshell_session(context)
        res_id = context.reservation.reservation_id
        w2out = cs_session.WriteMessageToReservationOutput

        details = cs_session.GetReservationDetails(res_id).ReservationDescription

        w2out(res_id, '\n> Current Reservation Information:')
        w2out(res_id, ' - {:.<16} : {}'.format('ReservationID', res_id))
        w2out(res_id, ' - {:.<16} : {}'.format('Domain', context.reservation.domain))
        w2out(res_id, ' - {:.<16} : {}'.format('Status', details.Status))
        w2out(res_id, ' - {:.<16} : {}'.format('Start Time', self._time_to_ISO8601(details.StartTime)))
        w2out(res_id, ' - {:.<16} : {}'.format('Scheduled End', self._time_to_ISO8601(details.EndTime)))
        w2out(res_id, ' - {:.<16} : {}'.format('Owner', details.Owner))
        w2out(res_id, ' - {:.<16} : {}'.format('Permitted Users', ', '.join(details.PermittedUsers)))
        w2out(res_id, '{}='.format('=-' * 36))

    def set_reservation_status(self, context, status):
        """

        :param ResourceCommandContext context:
        :param str status:
        :return:
        """
        cs_session = self._open_cloudshell_session(context)
        res_id = context.reservation.reservation_id
        w2out = cs_session.WriteMessageToReservationOutput
        if status != 'none':
            result = cs_session.SetReservationLiveStatus(reservationId=res_id,
                                                         liveStatusName=RESERVATION_LIVE_STATUS[status]
                                                         )
        else:
            result = cs_session.SetReservationLiveStatus(reservationId=res_id)
        w2out(res_id, '\n> Set Reservation Status to {}\n{}'.format(status, result))
        w2out(res_id, '{}='.format('=-' * 36))

    def list_all_reservation_assets(self, context):
        """

        :param ResourceCommandContext context:
        :return:
        """
        cs_session = self._open_cloudshell_session(context)
        res_id = context.reservation.reservation_id
        w2out = cs_session.WriteMessageToReservationOutput

        res_details = cs_session.GetReservationDetails(res_id).ReservationDescription
        apps = res_details.Apps
        resources = res_details.Resources
        services = res_details.Services

        if apps or resources or services:
            w2out(res_id, '\n** Items in this Reservation')
            if apps:
                a_list = []
                w2out(res_id, '> Apps:')
                for a in apps:
                    a_list.append(a.Name)
                a_list.sort()
                for aa in a_list:
                    w2out(res_id, '  - {}'.format(aa))

            if resources:
                r_list = list()
                w2out(res_id, '> Resources:')
                for r in sorted(resources):
                    r_list.append(r.Name)
                r_list.sort()
                for rr in r_list:
                    x = rr.count('/')
                    w2out(res_id, '{}- {}'.format(' '*(1+x), rr))

            if services:
                s_list = list()
                w2out(res_id, '> Services')
                for s in services:
                    s_list.append(s.ServiceName)
                s_list.sort()
                for ss in s_list:
                    w2out(res_id, ' - {}'.format(ss))
            w2out(res_id, '{}='.format('=-' * 36))

        else:
            w2out(res_id, '!* Empty Reservation, no items to display')

    def read_sandbox_data(self, context):
        """

        :param ResourceCommandContext context:
        :return:
        """
        cs_session = self._open_cloudshell_session(context)
        res_id = context.reservation.reservation_id
        w2out = cs_session.WriteMessageToReservationOutput

        sandbox_data = cs_session.GetSandboxData(context.reservation.reservation_id).SandboxDataKeyValues

        w2out(res_id, '\n> Sandbox Data (internal field)')

        if sandbox_data:
            w2out(res_id, '\n')
            for each in sandbox_data:
                w2out(res_id, '- {}: {}'.format(each.Key, each.Value))
            w2out(res_id, '{}='.format('=-' * 36))
        else:
            w2out(res_id, '- No current Sandbox Data')


    def set_sandbox_data_by_key(self, context, key, value):
        cs_session = self._open_cloudshell_session(context)
        res_id = context.reservation.reservation_id
        w2out = cs_session.WriteMessageToReservationOutput

        w2out(res_id, '\n> Adding to Sandbox Data')

        try:
            cs_session.SetSandboxData(res_id, [SandboxDataKeyValue(key, value)])
            w2out(res_id, '- Success')
        except cs_error as err:
            w2out(res_id, '!! Error: {}'.format(err.message))

    def clear_sandbox_data(self, context, check):
        cs_session = self._open_cloudshell_session(context)
        res_id = context.reservation.reservation_id
        w2out = cs_session.WriteMessageToReservationOutput

        if check.upper() == 'YES':

            w2out(res_id, '\n> Clearing Sandbox Data')
            try:
                cs_session.ClearSandboxData(res_id)
                w2out(res_id, ' - Success')
            except cs_error as err:
                w2out(res_id, '!! Error: {}'.format(err.message))
