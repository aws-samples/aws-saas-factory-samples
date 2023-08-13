import os
import pathlib

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
    trigger_file_path = (
        pathlib.Path(__file__).parent.joinpath("auth0_post_login_trigger.js").resolve()
    )
    with open(trigger_file_path, encoding="utf-8") as trigger_file:
        trigger_code_template = trigger_file.read()
    trigger_code = trigger_code_template.replace("TENANT_ID", constants.TENANT_ID)
    return trigger_code


if __name__ == "__main__":
    main()
