import os

from auth0.management import Auth0

import constants


def main() -> None:
    mgmt_api_token = os.environ["AUTH0_MGMT_API_TOKEN"]
    auth0 = Auth0(constants.OIDC_PROVIDER_DOMAIN, mgmt_api_token)

    action_name = "Tags Claim"
    trigger_id = "post-login"
    trigger_version = "v3"

    action = auth0.actions.create_action(  # type: ignore[attr-defined]
        {
            "name": action_name,
            "supported_triggers": [
                {
                    "id": trigger_id,
                    "version": trigger_version,
                    "compatible_triggers": [
                        {"id": trigger_id, "version": trigger_version}
                    ],
                }
            ],
            "code": get_trigger_code(),
        }
    )
    auth0.actions.deploy_action(action["id"])  # type: ignore[attr-defined]
    auth0.actions.update_trigger_bindings(  # type: ignore[attr-defined]
        trigger_id,
        {
            "bindings": [
                {
                    "ref": {"type": "action_name", "value": action_name},
                    "display_name": action_name,
                }
            ]
        },
    )


def get_trigger_code() -> str:
    code = f"""
        exports.onExecutePostLogin = async (event, api) => {{
          api.idToken.setCustomClaim("https://aws.amazon.com/tags", {{
            "principal_tags": {{
              "TenantID": ["{constants.TENANT_ID}"]
            }}
          }});
        }};
    """
    return code


if __name__ == "__main__":
    main()
