"""
Channel Encoder Utility

This module provides functions to encode and decode channel identifiers
to prevent exposing actual channel names in the codebase.
"""

import base64
import os
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


def generate_key(salt=None):
    """Generate a key for encryption/decryption"""
    if salt is None:
        # Use a fixed salt for reproducibility
        salt = b'telegram_osint_salt'
    
    # Use a fixed password derived from environment or a default
    password = os.environ.get('CHANNEL_ENCODER_KEY', 'default_encoder_key').encode()
    
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    
    key = base64.urlsafe_b64encode(kdf.derive(password))
    return key


def encode_channel(channel_name):
    """
    Encode a channel name to hide it in the codebase
    
    Args:
        channel_name: The actual channel name/ID to encode
        
    Returns:
        An encoded string that can be safely stored in the code
    """
    key = generate_key()
    f = Fernet(key)
    
    # Add a prefix to identify the type of channel
    if channel_name.startswith('+'):
        # For private channels that start with +
        encoded = f.encrypt(channel_name.encode())
    else:
        # For public channels
        encoded = f.encrypt(channel_name.encode())
    
    # Convert to a URL-safe string
    return base64.urlsafe_b64encode(encoded).decode()


def decode_channel(encoded_channel):
    """
    Decode an encoded channel name back to its original form
    
    Args:
        encoded_channel: The encoded channel string
        
    Returns:
        The original channel name/ID
    """
    key = generate_key()
    f = Fernet(key)
    
    # Decode from URL-safe string
    decoded = base64.urlsafe_b64decode(encoded_channel.encode())
    
    # Decrypt the channel name
    original = f.decrypt(decoded).decode()
    
    return original 