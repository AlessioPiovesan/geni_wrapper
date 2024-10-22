from geni_wrapper import GeniSDK

# Initialize the SDK with your app ID
geni = GeniSDK(app_id='your_app_id_here')

# Handle authentication status changes
def on_status_change(status):
    print(f"Auth status changed to: {status}")

geni.Event.bind('auth:statusChange', on_status_change)

# Connect to Geni
def auth_callback(response):
    if response['status'] == 'authorized':
        print("Successfully connected!")
        # Make API calls here
    else:
        print("Authorization failed:", response.get('error'))

geni.connect(callback=auth_callback)