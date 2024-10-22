from .sdk import GeniSDK, GeniEvent

__version__ = '0.2.1'

# Make GeniSDK the default import
__all__ = ['GeniSDK', 'GeniEvent']

# Create global instance for easier access as shown in the original code
Geni = GeniSDK