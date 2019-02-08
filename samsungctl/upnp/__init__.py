# -*- coding: utf-8 -*-
import requests
import six
from xml.sax import saxutils
from lxml import etree
from .UPNP_Device.upnp_class import UPNPObject
from .UPNP_Device.instance_singleton import InstanceSingleton
from .UPNP_Device.xmlns import strip_xmlns

import logging
logger = logging.getLogger('samsungctl')


class UPNPTV(UPNPObject):

    def __init__(self, ip, locations):
        if locations is None:
            locations = []

        self.ip_address = ip
        self._dtv_information = None
        self._tv_options = None
        self.name = self.__class__.__name__
        self._locations = locations

        if self.power:
            super(UPNPTV, self).__init__(ip, locations)
        else:
            super(UPNPTV, self).__init__(ip, [])

    def __getattr__(self, item):
        if item in self.__dict__:
            return self.__dict__[item]

        if item in self._devices:
            return self._devices[item]

        if item in self._services:
            return self._services[item]

        if item in self.__class__.__dict__:
            if hasattr(self.__class__.__dict__[item], 'fget'):
                return self.__class__.__dict__[item].fget(self)

        if item in UPNPTV.__dict__:
            if hasattr(UPNPTV.__dict__[item], 'fget'):
                return UPNPTV.__dict__[item].fget(self)

        if item in UPNPObject.__dict__:
            if hasattr(UPNPObject.__dict__[item], 'fget'):
                return UPNPObject.__dict__[item].fget(self)

        raise AttributeError(item)

    def __setattr__(self, key, value):
        if (
            key in self.__class__.__dict__ and
            hasattr(self.__class__.__dict__[key], 'fset')
        ):
            self.__class__.__dict__[key].fset(self, value)

        elif (
            key in UPNPTV.__dict__ and
            hasattr(UPNPTV.__dict__[key], 'fset')
        ):
            UPNPTV.__dict__[key].fset(self, value)

        elif (
            key in UPNPObject.__dict__ and
            hasattr(UPNPObject.__dict__[key], 'fset')
        ):
            UPNPObject.__dict__[key].fset(self, value)

        else:
            self.__dict__[key] = value

    @property
    def power(self):
        return True

    def connect(self):
        super(UPNPTV, self).__init__(self.ip_address, self._locations)

    def disconnect(self):
        super(UPNPTV, self).__init__(self.ip_address, [])

    @property
    def tv_options(self):
        if self._tv_options is None:
            try:
                url = 'http://{0}:8001/api/v2'.format(self.ip_address)
                response = requests.get(url)
                response = response.json()

                if 'device' in response:
                    response = response['device']
                    if 'isSupport' in response:
                        import json
                        response['isSupport'] = json.loads(
                            response['isSupport']
                        )
                else:
                    response = None
            except (
                requests.HTTPError,
                requests.exceptions.ConnectTimeout,
                requests.exceptions.ConnectionError
            ):
                response = None

            if response is None:
                return {}

            self._tv_options = response
        return self._tv_options

    @property
    def is_support(self):
        return self.tv_options.get('isSupport', {})

    def get_audio_selection(self):
        try:
            audio_pid, audio_encoding = (
                self.RenderingControl.X_GetAudioSelection(0)
            )
            return audio_pid, audio_encoding
        except AttributeError:
            pass
        return None, None

    def set_audio_selection(self, audio_encoding, audio_pid=0):
        try:
            self.RenderingControl.X_UpdateAudioSelection(
                0,
                audio_pid,
                audio_encoding
            )
        except AttributeError:
            pass

    def get_channel_mute(self, channel):
        try:
            current_mute = self.RenderingControl.GetMute(0, channel)[0]
            return current_mute
        except AttributeError:
            pass

    def set_channel_mute(self, channel, desired_mute):
        try:
            self.RenderingControl.SetMute(0, channel, desired_mute)
        except AttributeError:
            pass

    def get_channel_volume(self, channel):
        try:
            current_volume = self.RenderingControl.GetVolume(0, channel)[0]
            return current_volume
        except AttributeError:
            pass

    def set_channel_volume(self, channel, desired_volume):
        try:
            self.RenderingControl.SetVolume(0, channel, desired_volume)
        except AttributeError:
            pass
    # ===============================

    def add_schedule(self, reservation_type, remind_info):
        try:
            return self.MainTVAgent2.AddSchedule(
                reservation_type,
                remind_info
            )[1]
        except AttributeError:
            pass

    @property
    def antenna_mode(self):
        raise NotImplementedError

    @antenna_mode.setter
    def antenna_mode(self, value):
        try:
            self.MainTVAgent2.SetAntennaMode(value)
        except AttributeError:
            pass

    @property
    def aspect_ratio(self):
        try:
            aspect_ratio = self.RenderingControl.X_GetAspectRatio(0)
            return aspect_ratio
        except AttributeError:
            pass

    @aspect_ratio.setter
    def aspect_ratio(self, aspect_ratio='Default'):
        try:
            self.RenderingControl.X_SetAspectRatio(0, aspect_ratio)
        except AttributeError:
            pass

    @property
    def av_off(self):
        raise NotImplementedError

    @av_off.setter
    def av_off(self, value):
        try:
            self.MainTVAgent2.SetAVOff(value)
        except AttributeError:
            pass

    @property
    def banner_information(self):
        try:
            return self.MainTVAgent2.GetBannerInformation()[1]
        except AttributeError:
            pass

    @property
    def brightness(self):
        try:
            brightness = self.RenderingControl.GetBrightness(0)[0]
            return brightness
        except AttributeError:
            raise

    @brightness.setter
    def brightness(self, desired_brightness):
        try:
            self.RenderingControl.SetBrightness(0, desired_brightness)
        except AttributeError:
            pass

    @property
    def byte_position_info(self):
        try:
            (
                track_size,
                relative_byte,
                absolute_byte
            ) = self.AVTransport.X_DLNA_GetBytePositionInfo(0)

            return track_size, relative_byte, absolute_byte
        except AttributeError:
            pass

        return None, None, None

    @property
    def caption_state(self):
        try:
            captions, enabled_captions = (
                self.RenderingControl.X_GetCaptionState(0)
            )
            return captions, enabled_captions
        except AttributeError:
            pass

        return None, None

    def change_schedule(self, reservation_type, remind_info):
        try:
            return self.MainTVAgent2.ChangeSchedule(
                reservation_type,
                remind_info
            )[0]
        except AttributeError:
            pass

    @property
    def channels(self):
        try:
            supported_channels = (
                self.MainTVAgent2.GetChannelListURL()[2]
            )

            channels = saxutils.unescape(supported_channels)
            channels = etree.fromstring(channels)

            supported_channels = []

            for channel in channels:
                channel_num = (
                    channel.find('MajorCh').text,
                    channel.find('MinorCh').text
                )

                supported_channels += [Channel(channel_num, channel, self)]

            return supported_channels

        except AttributeError:
            pass

    @property
    def channel(self):
        try:
            channel = self.MainTVAgent2.GetCurrentMainTVChannel()[1]
            channel = saxutils.unescape(channel)
            channel = etree.fromstring(channel)
            channel_num = (
                channel.find('MajorCh').text,
                channel.find('MinorCh').text
            )

            return Channel(channel_num, channel, self)
        except AttributeError:
            pass

    @channel.setter
    def channel(self, channel):
        """
        can be a string with '.'s separating the
        major/minor/micro for digital. or it can be a tuple of numbers.
        or a Channel instance gotten from instance.channels.
        """
        try:
            for chnl in self.channels:
                if chnl == channel:
                    chnl.activate()
                    break
            else:
                raise ValueError(
                    'Channel not found ({0})'.format(channel)
                )
        except AttributeError:
            pass

    def check_pin(self, pin):
        try:
            return self.MainTVAgent2.CheckPIN(pin)[0]
        except AttributeError:
            pass

    @property
    def color_temperature(self):
        try:
            color_temperature = self.RenderingControl.GetColorTemperature(0)[0]
            return color_temperature
        except AttributeError:
            pass

    @color_temperature.setter
    def color_temperature(self, desired_color_temperature):
        try:
            self.RenderingControl.SetColorTemperature(
                0,
                desired_color_temperature
            )
        except AttributeError:
            pass

    def connection_complete(self, connection_id=0):
        try:
            self.ConnectionManager.ConnectionComplete(connection_id)
        except AttributeError:
            pass

    @property
    def contrast(self):
        try:
            contrast = self.RenderingControl.GetContrast(0)[0]
            return contrast
        except AttributeError:
            pass

    @contrast.setter
    def contrast(self, desired_contrast):
        try:
            self.RenderingControl.SetContrast(0, desired_contrast)
        except AttributeError:
            pass

    def control_caption(
        self,
        operation,
        name,
        resource_uri,
        caption_uri,
        caption_type,
        language,
        encoding
    ):
        try:
            self.RenderingControl.X_ControlCaption(
                0,
                operation,
                name,
                resource_uri,
                caption_uri,
                caption_type,
                language,
                encoding
            )
        except AttributeError:
            pass

    @property
    def current_connection_ids(self):
        try:
            connection_ids = self.ConnectionManager.GetCurrentConnectionIDs()
            return connection_ids
        except AttributeError:
            pass

    def current_connection_info(self, connection_id):
        try:
            (
                rcs_id,
                av_transport_id,
                protocol_info,
                peer_connection_manager,
                peer_connection_id,
                direction,
                status
            ) = self.ConnectionManager.GetCurrentConnectionInfo(connection_id)

            return (
                rcs_id,
                av_transport_id,
                protocol_info,
                peer_connection_manager,
                peer_connection_id,
                direction,
                status
            )
        except AttributeError:
            pass
        return None, None, None, None, None, None, None

    @property
    def current_time(self):
        try:
            return self.MainTVAgent2.GetCurrentTime()[1]
        except AttributeError:
            pass

    @property
    def current_transport_actions(self):
        try:
            actions = self.AVTransport.GetCurrentTransportActions(0)
            return actions
        except AttributeError:
            pass

    def delete_channel_list(self, antenna_mode, channel_list):
        try:
            return self.MainTVAgent2.DeleteChannelList(
                antenna_mode,
                channel_list
            )[0]
        except AttributeError:
            pass

    def delete_channel_list_pin(self, antenna_mode, channel_list, pin):
        try:
            return self.MainTVAgent2.DeleteChannelListPIN(
                antenna_mode,
                channel_list,
                pin
            )[0]
        except AttributeError:
            pass

    def delete_recorded_item(self, uid):
        try:
            return self.MainTVAgent2.DeleteRecordedItem(uid)[0]
        except AttributeError:
            pass

    def delete_schedule(self, uid):
        try:
            return self.MainTVAgent2.DeleteSchedule(uid)[0]
        except AttributeError:
            pass

    @property
    def device_capabilities(self):
        try:
            play_media, rec_media, rec_quality_modes = (
                self.AVTransport.GetDeviceCapabilities(0)
            )

            return play_media, rec_media, rec_quality_modes
        except AttributeError:
            pass
        return None, None, None

    @property
    def dtv_information(self):
        try:
            if self._dtv_information is None:
                response, data = self.MainTVAgent2.GetDTVInformation()
                data = saxutils.unescape(data)
                self._dtv_information = etree.fromstring(data.encode('utf-8'))
            return self._dtv_information
        except AttributeError:
            pass

    def enforce_ake(self):
        try:
            return self.MainTVAgent22.EnforceAKE()[0]
        except AttributeError:
            pass

    def get_all_program_information_url(self, antenna_mode, channel):
        try:
            return self.MainTVAgent2.GetAllProgramInformationURL(
                antenna_mode,
                channel
            )[1]
        except AttributeError:
            pass

    def get_channel_lock_information(self, channel, antenna_mode):
        try:
            lock, start_time, end_time = (
                self.MainTVAgent2.GetChannelLockInformation(
                    channel,
                    antenna_mode
                )[1:]
            )

            return lock, start_time, end_time
        except AttributeError:
            pass
        return None, None, None

    def get_detail_channel_information(self, channel, antenna_mode):
        try:
            return self.MainTVAgent2.GetDetailChannelInformation(
                channel,
                antenna_mode
            )[1]
        except AttributeError:
            pass

    def get_detail_program_information(
        self,
        antenna_mode,
        channel,
        start_time
    ):
        try:
            return self.MainTVAgent2.GetDetailProgramInformation(
                antenna_mode,
                channel,
                start_time
            )[1]
        except AttributeError:
            pass

    def list_presets(self):
        try:
            current_preset_list = self.RenderingControl.ListPresets(0)
            return current_preset_list
        except AttributeError:
            pass

    @property
    def media_info(self):
        try:
            (
                num_tracks,
                media_duration,
                current_uri,
                current_uri_metadata,
                next_uri,
                next_uri_metadata,
                play_medium,
                record_medium,
                write_status
            ) = self.AVTransport.GetMediaInfo(0)

            return (
                num_tracks,
                media_duration,
                current_uri,
                current_uri_metadata,
                next_uri,
                next_uri_metadata,
                play_medium,
                record_medium,
                write_status
            )
        except AttributeError:
            pass

        return None, None, None, None, None, None, None, None, None

    def modify_favorite_channel(self, antenna_mode, favorite_ch_list):
        try:
            return self.MainTVAgent2.ModifyFavoriteChannel(
                antenna_mode,
                favorite_ch_list
            )[0]
        except AttributeError:
            pass

    def move_360_view(self, latitude_offset=0.0, longitude_offset=0.0):
        try:
            self.RenderingControl.X_Move360View(
                0,
                latitude_offset,
                longitude_offset
            )
        except AttributeError:
            pass

    @property
    def mute(self):
        try:
            status = self.MainTVAgent2.GetMuteStatus()[1]
        except AttributeError:
            status = self.get_channel_mute('Master')

        return status

    @mute.setter
    def mute(self, desired_mute):
        try:
            self.MainTVAgent2.SetMute(desired_mute)
        except AttributeError:
            self.set_channel_mute('Master', desired_mute)

    @property
    def network_information(self):
        try:
            return self.MainTVAgent2.GetNetworkInformation()[1]
        except AttributeError:
            pass

    def next(self):
        try:
            self.AVTransport.Next(0)
        except AttributeError:
            pass

    def origin_360_view(self):
        try:
            self.RenderingControl.X_Origin360View(0)
        except AttributeError:
            pass

    def pause(self):
        try:
            self.AVTransport.Pause(0)
        except AttributeError:
            pass

    def play(self, speed='1'):
        try:
            self.AVTransport.Play(0, speed)
        except AttributeError:
            pass

    @property
    def play_mode(self):
        return self.transport_settings[0]

    @play_mode.setter
    def play_mode(self, new_play_mode='NORMAL'):
        try:
            self.AVTransport.SetPlayMode(0, new_play_mode)
        except AttributeError:
            pass

    def player_app_hint(self, upnp_class):
        try:
            self.AVTransport.X_PlayerAppHint(0, upnp_class)
        except AttributeError:
            pass

    def play_recorded_item(self, uid):
        try:
            return self.MainTVAgent2.PlayRecordedItem(uid)[0]
        except AttributeError:
            pass

    @property
    def position_info(self):
        try:
            (
                track,
                track_duration,
                track_metadata,
                track_uri,
                relative_time,
                absolute_time,
                relative_count,
                absolute_count
            ) = self.AVTransport.GetPositionInfo(0)

            return (
                track,
                track_duration,
                track_metadata,
                track_uri,
                relative_time,
                absolute_time,
                relative_count,
                absolute_count
            )
        except AttributeError:
            pass

        return None, None, None, None, None, None, None, None

    def prefetch_uri(self, prefetch_uri, prefetch_uri_meta_data):
        try:
            self.AVTransport.X_PrefetchURI(
                0,
                prefetch_uri,
                prefetch_uri_meta_data
            )
        except AttributeError:
            pass

    def prepare_for_connection(
        self,
        remote_protocol_info,
        peer_connection_manager,
        direction,
        peer_connection_id=0
    ):
        try:
            connection_id, av_transport_id, rcs_id = (
                self.ConnectionManager.PrepareForConnection(
                    remote_protocol_info,
                    peer_connection_manager,
                    peer_connection_id,
                    direction
                )
            )

            return connection_id, av_transport_id, rcs_id
        except AttributeError:
            pass

        return None, None, None

    def previous(self):
        try:
            self.AVTransport.Previous(0)
        except AttributeError:
            pass

    @property
    def program_information_url(self):
        try:
            return (
                self.MainTVAgent2.GetCurrentProgramInformationURL()[1]
            )
        except AttributeError:
            pass

    @property
    def protocol_info(self):
        try:
            source, sink = self.ConnectionManager.GetProtocolInfo()
            return source, sink
        except AttributeError:
            pass

        return None, None

    def regional_variant_list(self, antenna_mode, channel):
        try:
            return self.MainTVAgent2.GetRegionalVariantList(
                antenna_mode,
                channel
            )[1]
        except AttributeError:
            pass

    def reorder_satellite_channel(self):
        try:
            return self.MainTVAgent2.ReorderSatelliteChannel()[0]
        except AttributeError:
            pass

    def run_app(self, application_id):
        try:
            return self.MainTVAgent2.RunApp(application_id)[0]
        except AttributeError:
            pass

    def run_browser(self, browser_url):
        try:
            return self.MainTVAgent2.RunBrowser(browser_url)[0]
        except AttributeError:
            pass

    def run_widget(self, widget_title, payload):
        try:
            return self.MainTVAgent2.RunWidget(widget_title, payload)[0]
        except AttributeError:
            pass

    def set_record_duration(self, channel, record_duration):
        try:
            return self.MainTVAgent2.SetRecordDuration(
                channel,
                record_duration
            )[0]
        except AttributeError:
            pass

    def set_regional_variant(self, antenna_mode, channel):
        try:
            return self.MainTVAgent2.SetRegionalVariant(
                antenna_mode,
                channel
            )[1]
        except AttributeError:
            pass

    def send_room_eq_data(
        self,
        total_count,
        current_count,
        room_eq_id,
        room_eq_data
    ):
        try:
            return self.MainTVAgent2.SendRoomEQData(
                total_count,
                current_count,
                room_eq_id,
                room_eq_data
            )[0]
        except AttributeError:
            pass

    def set_room_eq_test(self, room_eq_id):
        try:
            return self.MainTVAgent2.SetRoomEQTest(
                room_eq_id
            )[0]
        except AttributeError:
            pass

    @property
    def schedule_list_url(self):
        try:
            return self.MainTVAgent2.GetScheduleListURL()[1]
        except AttributeError:
            pass

    def seek(self, target, unit='REL_TIME'):
        try:
            self.AVTransport.Seek(0, unit, target)
        except AttributeError:
            pass

    def select_preset(self, preset_name):
        try:
            self.RenderingControl.SelectPreset(0, preset_name)
        except AttributeError:
            pass

    def send_key_code(self, key_code, key_description):
        try:
            self.TestRCRService.SendKeyCode(key_code, key_description)
        except AttributeError:
            pass

        try:
            self.MultiScreenService.SendKeyCode(key_code, key_description)
        except AttributeError:
            pass

    @property
    def service_capabilities(self):
        try:
            service_capabilities = (
                self.RenderingControl.X_GetServiceCapabilities(0)
            )
            return service_capabilities
        except AttributeError:
            pass

    def set_av_transport_uri(self, current_uri, current_uri_metadata):
        try:
            self.AVTransport.SetAVTransportURI(
                0,
                current_uri,
                current_uri_metadata
            )
        except AttributeError:
            pass

    def set_break_aux_stream_playlist(
        self,
        break_splice_out_position,
        expiration_time,
        aux_stream_playlist,
        break_id=0
    ):
        try:
            self.StreamSplicing.SetBreakAuxStreamPlaylist(
                break_id,
                break_splice_out_position,
                expiration_time,
                aux_stream_playlist
            )
        except AttributeError:
            pass

    def set_break_aux_stream_trigger(
        self,
        break_id=0,
        break_trigger_high=0,
        break_trigger_low=0
    ):
        try:
            self.StreamSplicing.SetBreakAuxStreamTrigger(
                break_id,
                break_trigger_high,
                break_trigger_low
            )
        except AttributeError:
            pass

    def set_channel_list_sort(self, channel_list_type, satellite_id, sort):
        try:
            return self.MainTVAgent2.SetChannelListSort(
                channel_list_type,
                satellite_id,
                sort
            )[0]
        except AttributeError:
            pass

    def set_clone_view_channel(self, channel_up_down):
        try:
            return self.MainTVAgent2.SetCloneViewChannel(
                channel_up_down
            )[0]
        except AttributeError:
            pass

    def set_next_av_transport_uri(self, next_uri, next_uri_metadata):
        try:
            self.AVTransport.SetNextAVTransportURI(
                0,
                next_uri,
                next_uri_metadata
            )
        except AttributeError:
            pass

    def set_zoom(self, x, y, w, h):
        try:
            self.RenderingControl.X_SetZoom(0, x, y, w, h)
        except AttributeError:
            pass

    @property
    def sharpness(self):
        try:
            sharpness = self.RenderingControl.GetSharpness(0)[0]
            return sharpness
        except AttributeError:
            pass

    @sharpness.setter
    def sharpness(self, desired_sharpness):
        try:
            self.RenderingControl.SetSharpness(0, desired_sharpness)
        except AttributeError:
            pass

    @property
    def source(self):
        try:
            source_id = self.MainTVAgent2.GetCurrentExternalSource()[2]
            for source in self.sources:
                if source.id == int(source_id):
                    return source
        except AttributeError:
            pass

    @source.setter
    def source(self, source):
        try:
            if isinstance(source, int):
                source_id = source
                for source in self.sources:
                    if source.id == source_id:
                        break
                else:
                    raise ValueError(
                        'Source id not found ({0})'.format(source_id))

            elif not isinstance(source, Source):
                source_name = source
                for source in self.sources:
                    if source_name in (
                        source.name,
                        source.label,
                        source.device_name
                    ):
                        break

                else:
                    raise ValueError(
                        'Source name not found ({0})'.format(source_name)
                    )

            source.activate()
        except AttributeError:
            pass

    @property
    def sources(self):
        try:
            source_list = self.MainTVAgent2.GetSourceList()[1]
            source_list = saxutils.unescape(source_list)
            root = etree.fromstring(source_list)

            sources = []

            for src in root:
                if src.tag == 'Source':
                    source_name = src.find('SourceType').text
                    source_id = int(src.find('ID').text)
                    source_editable = src.find('Editable').text == 'Yes'
                    sources += [
                        Source(
                            source_id,
                            source_name,
                            self,
                            source_editable
                        )
                    ]

            return sources
        except AttributeError:
            pass

    def start_ext_source_view(self, source, id):
        try:
            forced_flag, banner_info, ext_source_view_url = (
                self.MainTVAgent2.StartExtSourceView(source, id)[1:]
            )

            return forced_flag, banner_info, ext_source_view_url
        except AttributeError:
            pass
        return None, None, None

    def start_clone_view(self, forced_flag):
        try:
            banner_info, clone_view_url, clone_info = (
                self.MainTVAgent2.StartCloneView(forced_flag)[1:]
            )
            return banner_info, clone_view_url, clone_info
        except AttributeError:
            pass
        return None, None, None

    def start_instant_recording(self, channel):
        try:
            return self.MainTVAgent2.StartInstantRecording(channel)[1]
        except AttributeError:
            pass

    def start_iperf_client(self, time, window_size):
        try:
            return self.MainTVAgent2.StartIperfClient(
                time,
                window_size
            )[0]
        except AttributeError:
            pass

    def start_iperf_server(self, time, window_size):
        try:
            return self.MainTVAgent2.StartIperfServer(
                time,
                window_size
            )[0]
        except AttributeError:
            pass

    def start_second_tv_view(
        self,
        antenna_mode,
        channel_list_type,
        satellite_id,
        channel,
        forced_flag
    ):
        try:
            banner_info, second_tv_url = (
                self.MainTVAgent2.StartSecondTVView(
                    antenna_mode,
                    channel_list_type,
                    satellite_id,
                    channel,
                    forced_flag
                )[1:]
            )

            return banner_info, second_tv_url
        except AttributeError:
            pass

        return None, None

    def stop(self):
        try:
            self.AVTransport.Stop(0)
        except AttributeError:
            pass

    @property
    def stopped_reason(self):
        try:
            (
                stopped_reason,
                stopped_reason_data
            ) = self.AVTransport.X_GetStoppedReason(0)

            return stopped_reason, stopped_reason_data
        except AttributeError:
            pass

        return None, None

    def stop_iperf(self):
        try:
            return self.MainTVAgent2.StopIperf()[0]
        except AttributeError:
            pass

    def stop_record(self, channel):
        try:
            return self.MainTVAgent2.StopRecord(channel)[0]
        except AttributeError:
            pass

    def stop_view(self, view_url):
        try:
            return self.MainTVAgent2.StopView(view_url)[0]
        except AttributeError:
            pass

    def sync_remote_control_pannel(self, channel):
        try:
            return self.MainTVAgent2.SyncRemoteControlPannel(channel)[1]
        except AttributeError:
            pass

    @property
    def transport_info(self):
        try:
            (
                current_transport_state,
                current_transport_status,
                current_speed
            ) = self.AVTransport.GetTransportInfo(0)
            return (
                current_transport_state,
                current_transport_status,
                current_speed
            )
        except AttributeError:
            pass

        return None, None, None

    @property
    def transport_settings(self):
        try:
            play_mode, rec_quality_mode = (
                self.AVTransport.GetTransportSettings(0)
            )
            return play_mode, rec_quality_mode
        except AttributeError:
            pass
        return None, None

    @property
    def tv_slide_show(self):
        try:
            (
                current_show_state,
                current_theme_id,
                total_theme_number
            ) = self.RenderingControl.X_GetTVSlideShow(0)

            return current_show_state, current_theme_id, total_theme_number
        except AttributeError:
            pass

        return None, None, None

    @tv_slide_show.setter
    def tv_slide_show(self, value):
        try:
            current_show_state, current_show_theme = value
            self.RenderingControl.X_SetTVSlideShow(
                0,
                current_show_state,
                current_show_theme
            )
        except AttributeError:
            pass

    @property
    def video_selection(self):
        try:
            video_pid, video_encoding = (
                self.RenderingControl.X_GetVideoSelection(0)
            )
            return video_pid, video_encoding
        except AttributeError:
            pass

        return None, None

    @video_selection.setter
    def video_selection(self, value):
        try:
            if isinstance(value, tuple):
                video_encoding, video_pid = value
            else:
                video_pid = 0
                video_encoding = value

            self.RenderingControl.X_UpdateVideoSelection(
                0,
                video_pid,
                video_encoding
            )
        except AttributeError:
            pass

    @property
    def volume(self):
        try:
            current_volume = self.MainTVAgent2.GetVolume()[1]
        except AttributeError:
            current_volume = self.get_channel_volume('Master')

        return current_volume

    @volume.setter
    def volume(self, desired_volume):
        try:
            self.MainTVAgent2.SetVolume(desired_volume)
        except AttributeError:
            self.set_channel_volume('Master', desired_volume)

    @property
    def watching_information(self):
        try:
            tv_mode, information = (
                self.MainTVAgent2.GetWatchingInformation()[1:]
            )
            return tv_mode, information
        except AttributeError:
            pass

        return None, None

    def zoom_360_view(self, scale_factor_offset=1.0):
        try:
            self.RenderingControl.X_Zoom360View(0, scale_factor_offset)
        except AttributeError:
            pass

    # ** END UPNP FUNCTIONS ***************************************************

    def destory_group_owner(self):
        try:
            self.MainTVAgent2.DestoryGroupOwner()
        except AttributeError:
            pass

    @property
    def acr_current_channel_name(self):
        try:
            channel_name = self.MainTVAgent2.GetACRCurrentChannelName()[1]
            return channel_name
        except AttributeError:
            pass

    @property
    def acr_current_program_name(self):
        try:
            program_name = self.MainTVAgent2.GetACRCurrentProgramName()[1]
            return program_name
        except AttributeError:
            pass

    @property
    def acr_message(self):
        try:
            message = self.MainTVAgent2.GetACRMessage()[1]
            return message
        except AttributeError:
            pass

    @property
    def ap_information(self):
        try:
            ap_information = self.MainTVAgent2.GetAPInformation()[1]
            return ap_information
        except AttributeError:
            pass

    @property
    def available_actions(self):
        try:
            available_actions = self.MainTVAgent2.GetAvailableActions()[1]
            return available_actions
        except AttributeError:
            pass

    @property
    def channel_list_url(self):
        try:
            (
                channel_list_version,
                support_channel_list,
                channel_list_url,
                channel_list_type,
                satellite_id
            ) = self.MainTVAgent2.GetChannelListURL()[1:]

            return (
                channel_list_version,
                support_channel_list,
                channel_list_url,
                channel_list_type,
                satellite_id
            )
        except AttributeError:
            pass

        return None, None, None, None, None

    @property
    def browser_mode(self):
        try:
            browser_mode = self.MainTVAgent2.GetCurrentBrowserMode()[1]
            return browser_mode
        except AttributeError:
            pass

    @property
    def browser_url(self):
        try:
            browser_url = self.MainTVAgent2.GetCurrentBrowserURL()[1]
            return browser_url
        except AttributeError:
            pass

    @property
    def hts_speaker_layout(self):
        try:
            speaker_layout = self.MainTVAgent2.GetCurrentHTSSpeakerLayout()[1]
            return speaker_layout
        except AttributeError:
            pass

    def filtered_progarm_url(self, key_word):
        try:
            filtered_program_url = (
                self.MainTVAgent2.GetFilteredProgarmURL(key_word)[1]
            )
            return filtered_program_url
        except AttributeError:
            pass

    @property
    def hts_all_speaker_distance(self):
        try:

            (
                max_distance,
                all_speaker_distance
            ) = self.MainTVAgent2.GetHTSAllSpeakerDistance()[1:]
            return max_distance, all_speaker_distance
        except AttributeError:
            pass

    @hts_all_speaker_distance.setter
    def hts_all_speaker_distance(self, all_speaker_distance):
        try:
            self.MainTVAgent2.SetHTSAllSpeakerDistance(all_speaker_distance)
        except AttributeError:
            pass

    @property
    def hts_all_speaker_level(self):
        try:
            (
                max_level,
                all_speaker_level
            ) = self.MainTVAgent2.GetHTSAllSpeakerLevel()[1:]
            return max_level, all_speaker_level
        except AttributeError:
            pass
        return None, None

    @hts_all_speaker_level.setter
    def hts_all_speaker_level(self, all_speaker_level):
        try:
            self.MainTVAgent2.SetHTSAllSpeakerLevel(all_speaker_level)
        except AttributeError:
            pass

    @property
    def hts_sound_effect(self):
        try:
            (
                sound_effect,
                sound_effect_list
            ) = self.MainTVAgent2.GetHTSSoundEffect()[1:]
            return sound_effect, sound_effect_list
        except AttributeError:
            pass

        return None, None

    @hts_sound_effect.setter
    def hts_sound_effect(self, sound_effect):
        try:
            self.MainTVAgent2.SetHTSSoundEffect(sound_effect)
        except AttributeError:
            pass

    @property
    def hts_speaker_config(self):
        try:
            (
                speaker_channel,
                speaker_lfe
            ) = self.MainTVAgent2.GetHTSSpeakerConfig()[1:]
            return speaker_channel, speaker_lfe
        except AttributeError:
            pass
        return None, None

    @property
    def mbr_device_list(self):
        try:
            mbr_device_list = self.MainTVAgent2.GetMBRDeviceList()[1]
            return mbr_device_list
        except AttributeError:
            pass

    @property
    def mbr_dongle_status(self):
        try:
            mbr_dongle_status = self.MainTVAgent2.GetMBRDongleStatus()[1]
            return mbr_dongle_status
        except AttributeError:
            pass

    @property
    def record_channel(self):
        try:
            (
                record_channel,
                record_channel_2
            ) = self.MainTVAgent2.GetRecordChannel()[1:]
            return record_channel, record_channel_2
        except AttributeError:
            pass

        return None, None

    def send_browser_command(self, browser_command):
        try:
            self.MainTVAgent2.SendBrowserCommand(browser_command)
        except AttributeError:
            pass

    def send_mbrir_key(self, activity_index, mbr_device, mbr_ir_key):
        try:
            self.MainTVAgent2.SendMBRIRKey(
                activity_index,
                mbr_device,
                mbr_ir_key
            )
        except AttributeError:
            pass

    def stop_browser(self):
        try:
            self.MainTVAgent2.StopBrowser()
        except AttributeError:
            pass

    def set_auto_slide_show_mode(self, auto_slide_show_mode='ON'):
        try:
            self.AVTransport.X_SetAutoSlideShowMode(0, auto_slide_show_mode)
        except AttributeError:
            pass

    def set_slide_show_effect_hint(self, slide_show_effect_hint='ON'):
        try:
            self.AVTransport.X_SetSlideShowEffectHint(
                0,
                slide_show_effect_hint
            )
        except AttributeError:
            pass

    # *************************************************************************

    @property
    def operating_system(self):
        if 'OS' in self._tv_options:
            return self._tv_options['OS']
        return 'Unknown'

    @property
    def frame_tv_support(self):
        if 'FrameTVSupport' in self._tv_options:
            return self._tv_options['FrameTVSupport']
        return 'Unknown'

    @property
    def game_pad_support(self):
        if 'GamePadSupport' in self._tv_options:
            return self._tv_options['GamePadSupport']
        return 'Unknown'

    @property
    def dmp_drm_playready(self):
        if 'DMP_DRM_PLAYREADY' in self.is_support:
            return self.is_support['DMP_DRM_PLAYREADY']
        return False

    @property
    def dmp_drm_widevine(self):
        if 'DMP_DRM_WIDEVINE' in self.is_support:
            return self.is_support['DMP_DRM_WIDEVINE']
        return False

    @property
    def dmp_available(self):
        if 'DMP_available' in self.is_support:
            return self.is_support['DMP_available']
        return False

    @property
    def eden_available(self):
        if 'EDEN_available' in self.is_support:
            return self.is_support['EDEN_available']
        return False

    @property
    def apps_list_available(self):
        if self._tv_options:
            return True
        return False

    @property
    def ime_synced_support(self):
        if 'ImeSyncedSupport' in self.is_support:
            return self.is_support['ImeSyncedSupport']
        return False

    @property
    def remote_four_directions(self):
        if 'remote_fourDirections' in self.is_support:
            return self.is_support['remote_fourDirections']
        return False

    @property
    def remote_touch_pad(self):
        if 'remote_touchPad' in self.is_support:
            return self.is_support['remote_touchPad']
        return False

    @property
    def voice_support(self):
        if 'VoiceSupport' in self.tv_options:
            return self.tv_options['VoiceSupport']
        return 'Unknown'

    @property
    def firmware_version(self):
        if 'firmwareVersion' in self.tv_options:
            return self.tv_options['firmwareVersion']

        return 'Unknown'

    @property
    def network_type(self):
        if 'networkType' in self.tv_options:
            return self.tv_options['networkType']
        return 'Unknown'

    @property
    def resolution(self):
        if 'resolution' in self.tv_options:
            return self.tv_options['resolution']
        return 'Unknown'

    @property
    def token_auth_support(self):
        if 'TokenAuthSupport' in self.tv_options:
            return self.tv_options['TokenAuthSupport']
        return 'Unknown'

    @property
    def wifi_mac(self):
        if 'wifiMac' in self.tv_options:
            return self.tv_options['wifiMac']
        return 'Unknown'

    @property
    def device_id(self):
        try:
            return self.MainTVAgent2.deviceID
        except AttributeError:
            for service in self.services:
                if hasattr(service, 'deviceId'):
                    return service.deviceId

    @property
    def panel_technology(self):
        technology_mapping = dict(
            Q='QLED',
            U='LED',
            P='Plasma',
            L='LCD',
            H='DLP',
            K='OLED',
        )

        try:
            return technology_mapping[self.model[0]]
        except KeyError:
            return 'Unknown'

    @property
    def panel_type(self):
        model = self.model
        if model[0] == 'Q' and model[4] == 'Q':
            return 'UHD'
        if model[5].isdigit():
            return 'FullHD'

        panel_mapping = dict(
            S='Slim' if self.year == 2012 else 'SUHD',
            U='UHD',
            P='Plasma',
            H='Hybrid',
        )

        return panel_mapping[model[5]]

    @property
    def size(self):
        return int(self.model[2:][:2])

    @property
    def model(self):
        try:
            return self.AVTransport.modelName
        except AttributeError:
            pass

        return 'Unknown'

    @property
    def year(self):
        dtv_information = self.dtv_information
        if dtv_information is None:
            if 'RemoteControlReceiver' in self._services:
                year = self.RemoteControlReceiver.ProductCap.split(',')[0]
            else:
                year = '0'
        else:
            year = dtv_information.find('SupportTVVersion').text

        return int(year)

    @property
    def region(self):
        dtv_information = self.dtv_information
        if dtv_information is None:
            return 'Unknown'

        location = dtv_information.find('TargetLocation')
        return location.text.replace('TARGET_LOCATION_', '')

    @property
    def tuner_count(self):
        dtv_information = self.dtv_information
        if dtv_information is None:
            return 'Unknown'

        tuner_count = dtv_information.find('TunerCount')
        return int(tuner_count.text)

    @property
    def dtv_support(self):
        dtv_information = self.dtv_information
        if dtv_information is None:
            return 'Unknown'

        dtv = dtv_information.find('SupportDTV')
        return True if dtv.text == 'Yes' else False

    @property
    def pvr_support(self):
        dtv_information = self.dtv_information
        if dtv_information is None:
            return 'Unknown'

        pvr = dtv_information.find('SupportPVR')
        return True if pvr.text == 'Yes' else False


@six.add_metaclass(InstanceSingleton)
class Channel(object):

    def __init__(self, channel_num, node, parent):
        self._channel_num = channel_num
        self._node = node
        self._parent = parent

    def __getattr__(self, item):

        if item in self.__dict__:
            return self.__dict__[item]

        for child in self._node:
            if child.tag == item:
                value = child.text
                if value.isdigit():
                    value = int(value)

                return value

        raise AttributeError(item)

    @property
    def number(self):
        return self._channel_number

    @number.setter
    def number(self, channel_number=(0, 0)):
        """ channel_number = (major, minor)
        return self.MainTVAgent2.EditChannelNumber(
            antenna_mode,
            source,
            destination,
            forced_flag
        )[0]
        """

        raise NotImplementedError

    @property
    def lock(self):
        raise NotImplementedError

    @lock.setter
    def lock(self, value):
        """
        return self.MainTVAgent2.SetChannelLock(
            antenna_mode,
            channel_list,
            lock,
            pin,
            start_time,
            end_time
        )[0]
        """
        raise NotImplementedError

    @property
    def pin(self):
        raise NotImplementedError

    @pin.setter
    def pin(self, value):
        """
        return self.MainTVAgent2.SetMainTVChannelPIN(
            antenna_mode,
            channel_list_type,
            pin,
            satellite_id,
            channel
        )[0]
        """
        raise NotImplementedError

    @property
    def name(self):
        return self._node.find('PTC').text

    @name.setter
    def name(self, value):
        """
        return self.MainTVAgent2.ModifyChannelName(
            antenna_mode,
            channel,
            channel_name
        )[1]
        """
        raise NotImplementedError

    @property
    def is_recording(self):
        channel = self._parent.MainTVAgent2.GetRecordChannel()[1]
        channel_num = (
            channel.find('MajorCh').text,
            channel.find('MinorCh').text
        )
        return self._channel_num == channel_num

    @property
    def is_active(self):
        return self._parent.channel == self

    def activate(self):
        antenna_mode = 1
        channel_list_type, satellite_id = (
            self._parent.MainTVAgent2.GetChannelListURL()[4:1]
        )

        channel = etree.tostring(self._node)
        channel = saxutils.escape(channel)

        self._parent.MainTVAgent2.SetMainTVChannel(
            antenna_mode,
            channel_list_type,
            satellite_id,
            channel
        )


@six.add_metaclass(InstanceSingleton)
class Source(object):

    def __init__(
        self,
        id,
        name,
        parent,
        editable,
    ):
        self._id = id
        self.__name__ = name
        self._parent = parent
        self._editable = editable

    @property
    def id(self):
        return self._id

    @property
    def name(self):
        return self.__name__

    @property
    def is_viewable(self):
        source = self.__source
        return source.find('SupportView').text == 'Yes'

    @property
    def is_editable(self):
        return self._editable

    @property
    def __source(self):
        source_list = self._parent.MainTVAgent2.GetSourceList()[1]
        source_list = saxutils.unescape(source_list)
        root = etree.fromstring(source_list)

        for src in root:
            if src.tag == 'Source':
                if int(src.find('ID').text) == self.id:
                    return src

    @property
    def is_connected(self):
        source = self.__source

        connected = source.find('Connected')
        if connected is not None:
            if connected.text == 'Yes':
                return True
            if connected.text == 'No':
                return False

    @property
    def label(self):
        if self.is_editable:
            source = self.__source

            label = source.find('EditNameType')
            if label is not None:
                label = label.text
                if label != 'NONE':
                    return label

        return self.name

    @label.setter
    def label(self, value):
        if self.is_editable:
            self._parent.MainTVAgent2.EditSourceName(self.name, value)

    @property
    def device_name(self):
        source = self.__source
        device_name = source.find('DeviceName')
        if device_name is not None:
            return device_name.text

    @property
    def is_active(self):
        source_list = self._parent.MainTVAgent2.GetSourceList()[1]
        source_list = saxutils.unescape(source_list)
        root = etree.fromstring(source_list)
        return int(root.find('ID').text) == self.id

    def activate(self):
        if self.is_connected:
            self._parent.MainTVAgent2.SetMainTVSource(
                self.name,
                str(self.id),
                str(self.id)
            )

    def __str__(self):
        return self.label
