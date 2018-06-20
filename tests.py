from engine import *
import pytest

google_maps_service = GoogleMapsService()

def test_remove_local_number():
    google_maps_service.remove_local_number("Foo 12/123")
    assert google_maps_service.address == "Foo 12"
    google_maps_service.remove_local_number("Foo 12/123 bar")
    assert google_maps_service.address == "Foo 12 bar"
    google_maps_service.remove_local_number("Foo 12a/123 bar")
    assert google_maps_service.address == "Foo 12a bar"
    google_maps_service.remove_local_number("Foo 12/ 123")
    assert google_maps_service.address == "Foo 12"
    google_maps_service.remove_local_number("Foo 12 /123")
    assert google_maps_service.address == "Foo 12"
    google_maps_service.remove_local_number("Foo 12 / 123")
    assert google_maps_service.address == "Foo 12"
    google_maps_service.remove_local_number("Foo 12 /  123")
    assert google_maps_service.address == "Foo 12"
    google_maps_service.remove_local_number("Foo 12/")
    assert google_maps_service.address == "Foo 12"
    google_maps_service.remove_local_number("Foo 12")
    assert google_maps_service.address == "Foo 12"