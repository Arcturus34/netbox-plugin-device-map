from packaging import version

from dcim.models import Device
from django.db.models import QuerySet, Q
from ipam.models import VLAN
from netbox.settings import VERSION

from .settings import plugin_settings


LOCATION_CF_NAME = plugin_settings['device_geolocation_cf']
NETBOX_VERSION = version.parse(VERSION)
LatLon = tuple[float, float]


def get_device_location(device: Device) -> LatLon | None:
    """If netbox latitude and longitude fields are populated for a device then use them."""
    if device.latitude and device.longitude:
        return (device.latitude, device.longitude)
    """... Otherwise extract device geolocation from special custom field"""
    if location_cf := device.custom_field_data.get(LOCATION_CF_NAME):
        return tuple(map(float, location_cf.replace(' ', '').split(',', maxsplit=1)))


def get_connected_devices(device: Device, vlan: VLAN = None) -> QuerySet[Device]:
    peer_devices = Device.objects.none()
    interfaces = device.interfaces.exclude(cable=None)

    if vlan is not None:
        interfaces = interfaces.filter(Q(untagged_vlan=vlan) | Q(tagged_vlans=vlan))

    for interface in interfaces:
        for connected_endpoint in interface.connected_endpoints:
            if hasattr(connected_endpoint, 'device'):
                peer_device = connected_endpoint.device
                if peer_device.id != device.id:
                    peer_devices |= Device.objects.filter(id=peer_device.id)

    return peer_devices.distinct()





def are_devices_connected(device_a: Device, device_b: Device) -> bool:
    return get_connected_devices(device_a).filter(id=device_b.id).exists()
