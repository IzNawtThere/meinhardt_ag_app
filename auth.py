import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader

def load_auth():
    config = {
        'credentials': {
            'usernames': {
                'admin': {
                    'name': 'Admin User',
                    'password': stauth.Hasher(['admin123']).generate()[0]
                },
                'devco': {
                    'name': 'DevCo Analyst',
                    'password': stauth.Hasher(['devco123']).generate()[0]
                }
            }
        },
        'cookie': {
            'name': 'meinhardt_cookie',
            'key': 'meinhardt_secret_key',
            'expiry_days': 1
        },
        'preauthorized': {}
    }
    return stauth.Authenticate(
        config['credentials'],
        config['cookie']['name'],
        config['cookie']['key'],
        config['cookie']['expiry_days']
    )