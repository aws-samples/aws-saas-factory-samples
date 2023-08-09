import os

from auth0.management import Auth0

import constants


def main() -> None:
    mgmt_api_token = os.environ["AUTH0_MGMT_API_TOKEN"]
    auth0 = Auth0(constants.OIDC_PROVIDER_DOMAIN, mgmt_api_token)

    client = auth0.clients.create(
        {
            "name": "UI",
            "callbacks": ["https://localhost"],
            "grant_types": ["implicit"],
            "jwt_configuration": {
                "alg": "RS256",
            },
        }
    )
    print(client["client_id"])


if __name__ == "__main__":
    main()
