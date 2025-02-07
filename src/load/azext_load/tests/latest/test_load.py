# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#
# Code generated by aaz-dev-tools
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer, KeyVaultPreparer, JMESPathCheck


class LoadScenario(ScenarioTest):
    location = 'westus2'
    identity_name1 = 'clitestid1'
    identity_name2 = 'clitestid2'
    cmk_key1_name = 'testkey1'
    cmk_key2_name = 'testkey2'

    @ResourceGroupPreparer(name_prefix='cli_test_azure_load_testing', location=location)
    @KeyVaultPreparer(location=location)
    def test_load_scenarios(self, resource_group, key_vault):
        # Set-up variables
        loadtest_resource_name = self.create_random_name('load-test', 24)
        loadtest_resource_name_cmk = self.create_random_name('load-test', 24)
        self.kwargs.update({
            'subscription_id': self.get_subscription_id(),
            'resource_name': loadtest_resource_name,
            'resource_name_cmk': loadtest_resource_name_cmk,
            'location': self.location,
            'kv': key_vault,
            'identity_name1': self.identity_name1,
            'identity_name2': self.identity_name2,
            'cmk_key1_name': self.cmk_key1_name
        })

        # Create Managed identity
        uami1 = self.cmd('az identity create -n {identity_name1} -g {rg}').get_output_in_json()
        uami2 = self.cmd('az identity create -n {identity_name2} -g {rg}').get_output_in_json()
        
        #Set-up variables for Identity
        self.kwargs['uami1ResourceId'] = uami1['id']
        self.kwargs['uami1PrincipalId'] = uami1['principalId']
        self.kwargs['uami1TenantId'] = uami1['tenantId']
        self.kwargs['uami2ResourceId'] = uami2['id']
        self.kwargs['uami2PrincipalId'] = uami2['principalId']
        self.kwargs['uami2TenantId'] = uami2['tenantId']

        checks = [JMESPathCheck('name', loadtest_resource_name),
                    JMESPathCheck('location', self.location),
                    JMESPathCheck('resourceGroup', resource_group),
                    JMESPathCheck('provisioningState', 'Succeeded'),
                    JMESPathCheck('type', 'microsoft.loadtestservice/loadtests'),
                    JMESPathCheck('identity.type', 'None')]

        # Create basic Load Test resource
        self.cmd('az load create --name {resource_name} '
                '--location {location} '
                '--resource-group {rg}',
                checks=checks)

        checks = [JMESPathCheck('name', loadtest_resource_name),
                    JMESPathCheck('location', self.location),
                    JMESPathCheck('resourceGroup', resource_group),
                    JMESPathCheck('provisioningState', 'Succeeded'),
                    JMESPathCheck('type', 'microsoft.loadtestservice/loadtests'),
                    JMESPathCheck('identity.type', 'SystemAssigned, UserAssigned')]

        # Create Load Test resource with Managed Identity
        self.cmd('az load create --name {resource_name} '
                '--location {location} '
                '--resource-group {rg} '
                '--identity-type SystemAssigned,UserAssigned '
                '--user-assigned \"{{{uami1ResourceId}}}\"',
                checks=checks)

        # Set keyvault properties
        self.cmd('az keyvault update --name {kv} '
                '--resource-group {rg} '
                '--set properties.enableSoftDelete=true')
        
        self.cmd('az keyvault update --name {kv} '
                '--resource-group {rg} '
                '--set properties.enablePurgeProtection=true')
        
        # Set keyvault access policy for user assigned identity
        self.cmd('az keyvault set-policy --name {kv} '
                '--resource-group {rg} '
                '--object-id {uami1PrincipalId} '
                '--key-permissions get wrapKey unwrapKey')

        # Create a new Key for CMK encryption
        key = self.cmd('az keyvault key create -n {cmk_key1_name} '
                '-p software '
                '--vault-name {kv}').get_output_in_json()

        self.kwargs['cmk_key1'] = key['key']['kid']
        
        checks = [JMESPathCheck('name', loadtest_resource_name_cmk),
                    JMESPathCheck('location', self.location),
                    JMESPathCheck('resourceGroup', resource_group),
                    JMESPathCheck('provisioningState', 'Succeeded'),
                    JMESPathCheck('type', 'microsoft.loadtestservice/loadtests'),
                    JMESPathCheck('identity.type', 'UserAssigned'),
                    JMESPathCheck('encryption.keyUrl', key['key']['kid']),
                    JMESPathCheck('encryption.identity.type', 'UserAssigned'),
                    JMESPathCheck('encryption.identity.resourceId', uami1['id'])]
        
        # Create Load Test resource with CMK encryption
        self.cmd('az load create --name {resource_name_cmk} '
                '--location {location} '
                '--resource-group {rg} '
                '--identity-type UserAssigned '
                '--user-assigned \"{{{uami1ResourceId}}}\" '
                '--encryption-key {cmk_key1} '
                '--encryption-identity {uami1ResourceId}',
                checks=checks)
        
        checks = [JMESPathCheck('name', loadtest_resource_name),
                    JMESPathCheck('location', self.location),
                    JMESPathCheck('resourceGroup', resource_group),
                    JMESPathCheck('provisioningState', 'Succeeded'),
                    JMESPathCheck('type', 'microsoft.loadtestservice/loadtests'),
                    JMESPathCheck('identity.type', 'None'),
                    JMESPathCheck('tags', {"test": "test"})]

        # Update Load Test resource
        self.cmd('az load update --name {resource_name} '
                '--resource-group {rg} '
                '--tags test=test '
                '--identity-type None',
                checks=checks)
        
        checks = [JMESPathCheck('name', loadtest_resource_name_cmk),
                    JMESPathCheck('location', self.location),
                    JMESPathCheck('resourceGroup', resource_group),
                    JMESPathCheck('provisioningState', 'Succeeded'),
                    JMESPathCheck('type', 'microsoft.loadtestservice/loadtests'),
                    JMESPathCheck('identity.type', 'SystemAssigned, UserAssigned'),
                    JMESPathCheck('encryption.keyUrl', key['key']['kid']),
                    JMESPathCheck('encryption.identity.type', 'UserAssigned'),
                    JMESPathCheck('encryption.identity.resourceId', uami1['id'])]
        
        # Update Load Test resource with CMK encryption and managed identity
        loadtest_resource_with_cmk = self.cmd('az load update --name {resource_name_cmk} '
                '--resource-group {rg} '
                '--identity-type SystemAssigned,UserAssigned',
                checks=checks).get_output_in_json()
        
        self.kwargs['systemAssignedIdentityPrincipalId'] = loadtest_resource_with_cmk['identity']['principalId']

        # Set keyvault access policy for system assigned identity
        self.cmd('az keyvault set-policy --name {kv} '
                '--resource-group {rg} '
                '--object-id {systemAssignedIdentityPrincipalId} '
                '--key-permissions get wrapKey unwrapKey')

        checks = [JMESPathCheck('name', loadtest_resource_name_cmk),
                    JMESPathCheck('location', self.location),
                    JMESPathCheck('resourceGroup', resource_group),
                    JMESPathCheck('provisioningState', 'Succeeded'),
                    JMESPathCheck('type', 'microsoft.loadtestservice/loadtests'),
                    JMESPathCheck('identity.type', 'SystemAssigned, UserAssigned'),
                    JMESPathCheck('encryption.keyUrl', key['key']['kid']),
                    JMESPathCheck('encryption.identity.type', 'SystemAssigned'),
                    JMESPathCheck('encryption.identity.resourceId', None)]
        
        # Update Load Test resource with system managed identity
        self.cmd('az load update --name {resource_name_cmk} '
                '--resource-group {rg} '
                '--encryption-identity SystemAssigned',
                checks=checks)

        # Get Load Test resource
        self.cmd('az load show --name {resource_name_cmk} '
                '--resource-group {rg}',
                checks=checks)

        checks = [JMESPathCheck('name', loadtest_resource_name),
                    JMESPathCheck('location', self.location),
                    JMESPathCheck('resourceGroup', resource_group),
                    JMESPathCheck('provisioningState', 'Succeeded'),
                    JMESPathCheck('type', 'microsoft.loadtestservice/loadtests'),
                    JMESPathCheck('identity.type', 'None'),
                    JMESPathCheck('tags', {"test": "test"})]
        
        self.cmd('az load show --name {resource_name} '
                '--resource-group {rg}',
                checks=checks)

        # List Load Test resources
        self.cmd('az load list '
                '--resource-group {rg}',
                checks=self.check('length(@)', 2))
        
        # Delete Load Test resource
        self.cmd('az load delete --name {resource_name} '
                '--resource-group {rg} --yes')
        
        self.cmd('az load delete --name {resource_name_cmk} '
                '--resource-group {rg} --yes')