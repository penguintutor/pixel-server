# Testing pixel-server

To run tests with logging:
    pytest-3 -p no:logging

The default log is /tmp/pytest-of-<username>/pytest-current/log?/pixelserver.log
    
## Debug messages

To add messages to the log include debug=True in create_app()
Then use logging.debug after creating the app

Console messages are not normally shown. To also show console messages use the -s option.


# Limitations

The automated testing has some limitations due to network configuration etc. The following are not included in the testing and can instead be tested manually.

## CSRF

CSRF is excluded from the testing. To test CSRF manually:

* run the server
* login as a user
* restart the server
* receive a session expired message

## Network addresses

When performing testing then the network address used is 127.0.0.1. The automated tests take account of this by allowing and disallowing that address, but it does not fully test different network ranges / addresses. These should be tested manually using an appropriate network setup and suitable auth.cfg files.

