import re
from dataclasses import asdict
from random import randrange
from typing import Any, Dict, Optional

from browserforge.fingerprints import Fingerprint, FingerprintGenerator, Screen

from camoufox.pkgman import load_yaml

# Load the browserforge.yaml file
BROWSERFORGE_DATA = load_yaml('browserforge.yml')

FP_GENERATOR = FingerprintGenerator(browser='firefox', os=('linux', 'macos', 'windows'))


def _cast_to_properties(
    camoufox_data: dict, cast_enum: dict, bf_dict: dict, ff_version: Optional[str] = None
) -> None:
    """
    Casts Browserforge fingerprints to Camoufox config properties.
    """
    for key, data in bf_dict.items():
        # Ignore non-truthy values
        if not data:
            continue
        # Get the associated Camoufox property
        type_key = cast_enum.get(key)
        if not type_key:
            continue
        # If the value is a dictionary, recursively recall
        if isinstance(data, dict):
            _cast_to_properties(camoufox_data, type_key, data, ff_version)
            continue
        # Fix values that are out of bounds
        if type_key.startswith("screen.") and isinstance(data, int) and data < 0:
            data = 0
        # Replace the Firefox versions with ff_version
        if ff_version and isinstance(data, str):
            data = re.sub(r'(?<!\d)(1[0-9]{2})(\.0)(?!\d)', rf'{ff_version}\2', data)
        camoufox_data[type_key] = data


def handle_screenXY(camoufox_data: Dict[str, Any], fp_screen: Screen) -> None:
    """
    Helper method to set window.screenY based on Browserforge's screenX value.
    """
    # Default screenX to 0 if not provided
    screenX = fp_screen.screenX
    if not screenX:
        camoufox_data['window.screenX'] = 0
        camoufox_data['window.screenY'] = 0
        return

    # If screenX is within [-50, 50], use the same value for screenY
    if screenX in range(-50, 51):
        camoufox_data['window.screenY'] = screenX
        return

    # Browserforge thinks the browser is windowed. # Randomly generate a screenY value.
    screenY = fp_screen.availHeight - fp_screen.outerHeight
    if screenY == 0:
        camoufox_data['window.screenY'] = 0
    elif screenY > 0:
        camoufox_data['window.screenY'] = randrange(0, screenY)  # nosec
    else:
        camoufox_data['window.screenY'] = randrange(screenY, 0)  # nosec


def from_browserforge(fingerprint: Fingerprint, ff_version: Optional[str] = None) -> Dict[str, Any]:
    """
    Converts a Browserforge fingerprint to a Camoufox config.
    """
    camoufox_data: Dict[str, Any] = {}
    _cast_to_properties(
        camoufox_data,
        cast_enum=BROWSERFORGE_DATA,
        bf_dict=asdict(fingerprint),
        ff_version=ff_version,
    )
    handle_screenXY(camoufox_data, fingerprint.screen)

    return camoufox_data


def generate_fingerprint(**config) -> Fingerprint:
    """
    Generates a Firefox fingerprint with Browserforge.
    """
    return FP_GENERATOR.generate(**config)


if __name__ == "__main__":
    from pprint import pprint

    fp = generate_fingerprint()
    pprint(from_browserforge(fp))
