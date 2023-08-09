# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
# the Software, and to permit persons to whom the Software is furnished to do so.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
# FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
# COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
# IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

from typing import Any

import aws_cdk as cdk
import aws_cdk.aws_iam as iam
import aws_cdk.aws_s3 as s3
import cdk_nag as nag
from constructs import Construct

import constants


class ServiceStack(cdk.Stack):
    def __init__(self, scope: Construct, id_: str, **kwargs: Any):
        super().__init__(scope, id_, **kwargs)

        iam_oidc_principal = self._create_iam_oidc_provider()
        s3_bucket = s3.Bucket(
            self,
            "S3Bucket",
            enforce_ssl=True,
            removal_policy=cdk.RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )
        iam_policy_document = self._create_iam_policy_document(s3_bucket)
        iam_role = iam.Role(
            self,
            "IAMRole",
            assumed_by=iam_oidc_principal,
            inline_policies={s3_bucket.bucket_name: iam_policy_document},
        )

        self._manage_nag_suppresions(iam_role=iam_role, s3_bucket=s3_bucket)

        cdk.CfnOutput(self, "S3BucketName", value=s3_bucket.bucket_name)
        cdk.CfnOutput(self, "IAMRoleARN", value=iam_role.role_arn)

    @staticmethod
    def _manage_nag_suppresions(*, iam_role: iam.Role, s3_bucket: s3.Bucket) -> None:
        nag.NagSuppressions.add_resource_suppressions(
            iam_role,
            suppressions=[
                nag.NagPackSuppression(
                    id="AwsSolutions-IAM5",
                    reason="Role scopes access to specific tenant ID",
                )
            ],
        )
        nag.NagSuppressions.add_resource_suppressions(
            s3_bucket,
            suppressions=[
                nag.NagPackSuppression(
                    id="AwsSolutions-S1",
                    reason="Bucket is not public",
                )
            ],
        )

    def _create_iam_oidc_provider(self) -> iam.PrincipalBase:
        iam_oidc_provider = iam.OpenIdConnectProvider(
            self,
            "IAMOIDCProvider",
            url=constants.OIDC_PROVIDER_URL,
            client_ids=[constants.CLIENT_ID],
        )
        iam_oidc_principal = iam.OpenIdConnectPrincipal(
            open_id_connect_provider=iam_oidc_provider,
            conditions={
                "StringEquals": {
                    f"{constants.OIDC_PROVIDER_URI}:aud": constants.CLIENT_ID
                }
            },
        ).with_session_tags()
        return iam_oidc_principal

    def _create_iam_policy_document(self, s3_bucket: s3.Bucket) -> iam.PolicyDocument:
        s3_bucket_resource = cdk.Stack.of(self).format_arn(
            service="s3",
            region="",
            account="",
            resource=s3_bucket.bucket_name,
            resource_name="${aws:PrincipalTag/TenantID}/*",
        )
        iam_policy_document = iam.PolicyDocument(
            statements=[
                iam.PolicyStatement(
                    actions=["s3:GetObject"],
                    resources=[s3_bucket_resource],
                )
            ],
        )
        return iam_policy_document
