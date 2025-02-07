/**
 * Licensed to the Apache Software Foundation (ASF) under one
 * or more contributor license agreements.  See the NOTICE file
 * distributed with this work for additional information
 * regarding copyright ownership.  The ASF licenses this file
 * to you under the Apache License, Version 2.0 (the
 * "License"); you may not use this file except in compliance
 * with the License.  You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

var App = require('app');
var numberUtils = require('utils/number_utils');
require('mixins/common/localStorage');
require('controllers/wizard/step7_controller');

var installerStep7Controller,
  issuesFilterCases = [
    {
      isSubmitDisabled: true,
      submitButtonClicked: true,
      isIssuesFilterActive: true,
      issuesFilterText: '',
      issuesFilterLinkText: Em.I18n.t('installer.step7.showAllProperties'),
      title: 'issues filter on, submit button clicked'
    },
    {
      isSubmitDisabled: true,
      submitButtonClicked: false,
      isIssuesFilterActive: true,
      issuesFilterText: Em.I18n.t('installer.step7.showingPropertiesWithIssues'),
      issuesFilterLinkText: Em.I18n.t('installer.step7.showAllProperties'),
      title: 'issues filter on, submit button disabled'
    },
    {
      isSubmitDisabled: true,
      submitButtonClicked: true,
      isIssuesFilterActive: false,
      issuesFilterText: '',
      issuesFilterLinkText: '',
      title: 'issues filter off, submit button clicked'
    },
    {
      isSubmitDisabled: true,
      submitButtonClicked: false,
      isIssuesFilterActive: false,
      issuesFilterText: '',
      issuesFilterLinkText: Em.I18n.t('installer.step7.showPropertiesWithIssues'),
      title: 'issues filter off, submit button disabled'
    },
    {
      isSubmitDisabled: false,
      submitButtonClicked: false,
      isIssuesFilterActive: true,
      issuesFilterText: '',
      issuesFilterLinkText: Em.I18n.t('installer.step7.showAllProperties'),
      title: 'issues filter on, submit button enabled'
    },
    {
      isSubmitDisabled: false,
      submitButtonClicked: false,
      isIssuesFilterActive: false,
      issuesFilterText: '',
      issuesFilterLinkText: '',
      title: 'issues filter off, submit button enabled'
    },
    {
      isSubmitDisabled: false,
      submitButtonClicked: false,
      isIssuesFilterActive: true,
      issuesFilterText: '',
      issuesFilterLinkText: Em.I18n.t('installer.step7.showAllProperties'),
      title: 'issues filter on, submit button not clicked but active'
    },
    {
      isSubmitDisabled: false,
      submitButtonClicked: true,
      isIssuesFilterActive: true,
      issuesFilterText: '',
      issuesFilterLinkText: Em.I18n.t('installer.step7.showAllProperties'),
      title: 'issues filter on, submit button clicked and active'
    }
  ],
  issuesFilterTestSetup = function (controller, testCase) {
    controller.set('submitButtonClicked', testCase.submitButtonClicked);
    controller.reopen({
      isSubmitDisabled: testCase.isSubmitDisabled
    });
    controller.get('filterColumns').findProperty('attributeName', 'hasIssues').set('selected', testCase.isIssuesFilterActive);
  };

function getController() {
  return App.WizardStep7Controller.create({
    content: Em.Object.create({
      services: [],
      advancedServiceConfig: [],
      serviceConfigProperties: []
    })
  });
}

describe('App.InstallerStep7Controller', function () {

  beforeEach(function () {
    sinon.stub(App.ajax, 'send', Em.K);
    sinon.stub(App.config, 'setPreDefinedServiceConfigs', Em.K);
    installerStep7Controller = getController();
  });

  afterEach(function() {
    App.ajax.send.restore();
    App.config.setPreDefinedServiceConfigs.restore();
    installerStep7Controller.destroy();
  });

  App.TestAliases.testAsComputedAlias(getController(), 'masterComponentHosts', 'content.masterComponentHosts', 'array');

  App.TestAliases.testAsComputedAlias(getController(), 'slaveComponentHosts', 'content.slaveGroupProperties', 'array');

  App.TestAliases.testAsComputedAnd(getController(), 'isConfigsLoaded', ['wizardController.stackConfigsLoaded', 'isAppliedConfigLoaded']);

  describe('#installedServiceNames', function () {

    var tests = Em.A([
      {
        content: Em.Object.create({
          controllerName: 'installerController',
          services: Em.A([
            Em.Object.create({
              isInstalled: true,
              serviceName: 'SQOOP'
            }),
            Em.Object.create({
              isInstalled: true,
              serviceName: 'HDFS'
            })
          ])
        }),
        e: ['SQOOP', 'HDFS'],
        m: 'installerController with SQOOP'
      },
      {
        content: Em.Object.create({
          controllerName: 'installerController',
          services: Em.A([
            Em.Object.create({
              isInstalled: true,
              serviceName: 'HIVE'
            }),
            Em.Object.create({
              isInstalled: true,
              serviceName: 'HDFS'
            })
          ])
        }),
        e: ['HIVE', 'HDFS'],
        m: 'installerController without SQOOP'
      },
      {
        content: Em.Object.create({
          controllerName: 'addServiceController',
          services: Em.A([
            Em.Object.create({
              isInstalled: true,
              serviceName: 'HIVE'
            }),
            Em.Object.create({
              isInstalled: true,
              serviceName: 'HDFS'
            })
          ])
        }),
        e: ['HIVE', 'HDFS'],
        m: 'addServiceController without SQOOP'
      }
    ]);

    tests.forEach(function (test) {
      it(test.m, function () {
        installerStep7Controller.set('content', test.content);
        expect(installerStep7Controller.get('installedServiceNames')).to.include.members(test.e);
        expect(test.e).to.include.members(installerStep7Controller.get('installedServiceNames'));
      });
    });

  });

  describe('#isSubmitDisabled', function () {
    it('should be true if miscModalVisible', function () {
      installerStep7Controller.reopen({miscModalVisible: true});
      expect(installerStep7Controller.get('isSubmitDisabled')).to.equal(true);
    });
    it('should be true if some of stepConfigs has errors', function () {
      installerStep7Controller.reopen({
        miscModalVisible: false,
        stepConfigs: [
          {
            showConfig: true,
            errorCount: 1
          }
        ]
      });
      expect(installerStep7Controller.get('isSubmitDisabled')).to.equal(true);
    });
    it('should be false if all of stepConfigs don\'t have errors and miscModalVisible is false', function () {
      installerStep7Controller.reopen({
        miscModalVisible: false,
        stepConfigs: [
          {
            showConfig: true,
            errorCount: 0
          }
        ]
      });
      expect(installerStep7Controller.get('isSubmitDisabled')).to.equal(false);
    });
  });

  describe('#selectedServiceNames', function () {
    it('should use content.services as source of data', function () {
      installerStep7Controller.set('content', {
        services: [
          {isSelected: true, isInstalled: false, serviceName: 's1'},
          {isSelected: false, isInstalled: false, serviceName: 's2'},
          {isSelected: true, isInstalled: true, serviceName: 's3'},
          {isSelected: false, isInstalled: false, serviceName: 's4'},
          {isSelected: true, isInstalled: false, serviceName: 's5'},
          {isSelected: false, isInstalled: false, serviceName: 's6'},
          {isSelected: true, isInstalled: true, serviceName: 's7'},
          {isSelected: false, isInstalled: false, serviceName: 's8'}
        ]
      });
      var expected = ['s1', 's5'];
      expect(installerStep7Controller.get('selectedServiceNames')).to.eql(expected);
    });
  });

  describe('#allSelectedServiceNames', function () {
    it('should use content.services as source of data', function () {
      installerStep7Controller.set('content', {
        services: [
          Em.Object.create({isSelected: true, isInstalled: false, serviceName: 's1'}),
          Em.Object.create({isSelected: false, isInstalled: false, serviceName: 's2'}),
          Em.Object.create({isSelected: true, isInstalled: true, serviceName: 's3'}),
          Em.Object.create({isSelected: false, isInstalled: false, serviceName: 's4'}),
          Em.Object.create({isSelected: true, isInstalled: false, serviceName: 's5'}),
          Em.Object.create({isSelected: false, isInstalled: false, serviceName: 's6'}),
          Em.Object.create({isSelected: true, isInstalled: true, serviceName: 's7'}),
          Em.Object.create({isSelected: false, isInstalled: false, serviceName: 's8'})
        ]
      });
      var expected = ['s1', 's3', 's5', 's7'];
      expect(installerStep7Controller.get('allSelectedServiceNames')).to.eql(expected);
    });
  });

  describe('#_createSiteToTagMap', function () {
    it('should return filtered map', function () {
      var desired_configs = {
        site1: {
          tag: "tag1"
        },
        site2: {
          tag: "tag2"
        },
        site3: {
          tag: "tag3"
        }
      };
      var sites = {
        site1: true,
        site3: true
      };
      var siteToTagMap = installerStep7Controller._createSiteToTagMap(desired_configs,sites);
      expect(siteToTagMap).to.eql({
        site1: "tag1",
        site3: "tag3"
      });
    });
  });

  describe('#checkDatabaseConnectionTest', function () {
    it('should return promise in process', function () {
      installerStep7Controller.set('content', {
        services: Em.A([
          Em.Object.create({isSelected: true, isInstalled: false, serviceName: 'OOZIE', ignored: []}),
          Em.Object.create({isSelected: false, isInstalled: false, serviceName: 'HIVE', ignored: []}),
          Em.Object.create({isSelected: true, isInstalled: true, serviceName: 's3', ignored: []}),
          Em.Object.create({isSelected: false, isInstalled: false, serviceName: 's4', ignored: []}),
          Em.Object.create({isSelected: true, isInstalled: false, serviceName: 's5', ignored: []}),
          Em.Object.create({isSelected: false, isInstalled: false, serviceName: 's6', ignored: []}),
          Em.Object.create({isSelected: true, isInstalled: true, serviceName: 's7', ignored: []}),
          Em.Object.create({isSelected: false, isInstalled: false, serviceName: 's8', ignored: []})
        ])
      });
      var obj = Em.Object.create({name:'oozie_database',value:"aa"});
      installerStep7Controller.set('stepConfigs',Em.A([Em.Object.create({serviceName: 'OOZIE', configs: Em.A([obj]) })]));
      var deffer = installerStep7Controller.checkDatabaseConnectionTest();
      expect(deffer.isResolved()).to.equal(false);
      deffer.resolve(true);
      deffer.done(function(data) {
        expect(data).to.equal(true);
      });
    });
  });

  describe.skip('#submit', function () {

    beforeEach(function () {
      sinon.stub(App, 'get').withArgs('supports.preInstallChecks').returns(false);
    });

    afterEach(function () {
      App.get.restore();
    });

    it('should return false if submit disabled', function () {
      installerStep7Controller.set('isSubmitDisabled',true);
      expect(installerStep7Controller.submit()).to.be.false;
    });
    it('sumbit button should be unclicked if no configs', function () {
      installerStep7Controller.set('isSubmitDisabled',false);
      installerStep7Controller.submit();
      expect(installerStep7Controller.get('submitButtonClicked')).to.be.false;
    });
  });

  describe('#getConfigTagsSuccess', function () {
    beforeEach(function(){
      sinon.stub(App.StackService, 'find', function () {
        return [
          Em.Object.create({
            serviceName: 's0',
            isInstalled: true,
            configTypes: {
              site3: true,
              site1: true
            }
          }),
          Em.Object.create({
            serviceName: 's1',
            isInstalled: true,
            configTypes: {
              site1: true,
              site2: true
            }
          })
        ];
      });
    });
    afterEach(function(){
      App.StackService.find.restore();
    });

    it('should return serviceConfigTags', function () {
      var desired_configs = {
        site1: {
          tag: "tag1"
        },
        site2: {
          tag: "tag2"
        },
        site3: {
          tag: "tag3"
        }
      };
      var data = {
        Clusters: {
          desired_configs: desired_configs
        }
      };
      var siteToTagMap = installerStep7Controller.getConfigTagsSuccess(data);
      expect(installerStep7Controller.get('serviceConfigTags')).to.eql([
        {
          "siteName": "site1",
          "tagName": "tag1",
          "newTagName": null
        },
        {
          "siteName": "site2",
          "tagName": "tag2",
          "newTagName": null
        },
        {
          "siteName": "site3",
          "tagName": "tag3",
          "newTagName": null
        }
      ]);
      expect(installerStep7Controller.get('isAppliedConfigLoaded')).to.equal(true);
    });
  });

  describe('#clearStep', function () {
    it('should clear stepConfigs', function () {
      installerStep7Controller.set('stepConfigs', [
        {},
        {}
      ]);
      installerStep7Controller.clearStep();
      expect(installerStep7Controller.get('stepConfigs.length')).to.equal(0);
    });
    it('should clear filter', function () {
      installerStep7Controller.set('filter', 'filter');
      installerStep7Controller.clearStep();
      expect(installerStep7Controller.get('filter')).to.equal('');
    });
    it('should set for each filterColumns "selected" false', function () {
      installerStep7Controller.set('filterColumns', [
        {selected: true},
        {selected: false},
        {selected: true}
      ]);
      installerStep7Controller.clearStep();
      expect(installerStep7Controller.get('filterColumns').everyProperty('selected', false)).to.equal(true);
    });
  });

  describe('#loadInstalledServicesConfigGroups', function () {
    it('should do ajax request for each received service name', function () {
      var serviceNames = ['s1', 's2', 's3'];
      installerStep7Controller.loadInstalledServicesConfigGroups(serviceNames);
      expect(App.ajax.send.callCount).to.equal(serviceNames.length);
    });
  });

  describe('#getConfigTags', function () {
    it('should do ajax-request', function () {
      installerStep7Controller.getConfigTags();
      expect(App.ajax.send.calledOnce).to.equal(true);
    });
  });

  describe('#setGroupsToDelete', function () {
    beforeEach(function () {
      installerStep7Controller.set('wizardController', Em.Object.create(App.LocalStorage, {name: 'tdk'}));
    });
    it('should add new groups to groupsToDelete', function () {
      var groupsToDelete = [
          {id: '1'},
          {id: '2'}
        ],
        groups = [
          Em.Object.create({id: '3'}),
          Em.Object.create(),
          Em.Object.create({id: '5'})
        ],
        expected = [
          {id: "1"},
          {id: "2"},
          {id: "3"},
          {id: "5"}
        ];
      installerStep7Controller.set('groupsToDelete', groupsToDelete);
      installerStep7Controller.setGroupsToDelete(groups);
      expect(installerStep7Controller.get('groupsToDelete')).to.eql(expected);
      expect(installerStep7Controller.get('wizardController').getDBProperty('groupsToDelete')).to.eql(expected);
    });
  });

  describe('#checkMySQLHost', function () {
    it('should send query', function () {
      installerStep7Controller.checkMySQLHost();
      expect(App.ajax.send.calledOnce).to.be.true;
    });
  });

  describe('#selectConfigGroup', function () {
    beforeEach(function () {
      installerStep7Controller.reopen({content: {services: []}});
      sinon.stub(installerStep7Controller, 'switchConfigGroupConfigs', Em.K);
    });
    afterEach(function () {
      installerStep7Controller.switchConfigGroupConfigs.restore();
    });
    it('should set selectedConfigGroup', function () {
      var group = {':': []};
      installerStep7Controller.selectConfigGroup({context: group});
      expect(installerStep7Controller.get('selectedConfigGroup')).to.eql(group);
    });
  });

  describe('#selectedServiceObserver', function () {
    beforeEach(function () {
      installerStep7Controller.reopen({content: {services: []}});
      sinon.stub(installerStep7Controller, 'switchConfigGroupConfigs', Em.K);
    });
    afterEach(function () {
      installerStep7Controller.switchConfigGroupConfigs.restore();
    });
    it('shouldn\'t do nothing if App.supports.hostOverridesInstaller is false', function () {
      App.set('supports.hostOverridesInstaller', false);
      var configGroups = [
          {},
          {}
        ],
        selectedConfigGroup = {};
      installerStep7Controller.reopen({configGroups: configGroups, selectedConfigGroup: selectedConfigGroup});
      installerStep7Controller.selectedServiceObserver();
      expect(installerStep7Controller.get('configGroups')).to.eql(configGroups);
      expect(installerStep7Controller.get('selectedConfigGroup')).to.eql(selectedConfigGroup);
    });
    it('shouldn\'t do nothing if selectedService is null', function () {
      App.set('supports.hostOverridesInstaller', true);
      var configGroups = [
          {},
          {}
        ],
        selectedConfigGroup = {};
      installerStep7Controller.reopen({selectedService: null, configGroups: configGroups, selectedConfigGroup: selectedConfigGroup});
      installerStep7Controller.selectedServiceObserver();
      expect(installerStep7Controller.get('configGroups')).to.eql(configGroups);
      expect(installerStep7Controller.get('selectedConfigGroup')).to.eql(selectedConfigGroup);
    });
    it('shouldn\'t do nothing if selectedService.serviceName is MISC', function () {
      App.set('supports.hostOverridesInstaller', true);
      var configGroups = [
          {},
          {}
        ],
        selectedConfigGroup = {};
      installerStep7Controller.reopen({selectedService: {serviceName: 'MISC'}, configGroups: configGroups, selectedConfigGroup: selectedConfigGroup});
      installerStep7Controller.selectedServiceObserver();
      expect(installerStep7Controller.get('configGroups')).to.eql(configGroups);
      expect(installerStep7Controller.get('selectedConfigGroup')).to.eql(selectedConfigGroup);
    });
    it('should update configGroups and selectedConfigGroup', function () {
      App.set('supports.hostOverridesInstaller', true);
      var defaultGroup = {isDefault: true, n: 'n2'},
        configGroups = [
          {isDefault: false, n: 'n1'},
          defaultGroup,
          {n: 'n3'}
        ],
        selectedConfigGroup = {};
      installerStep7Controller.reopen({selectedService: {serviceName: 's1', configGroups: configGroups}});
      installerStep7Controller.selectedServiceObserver();
      expect(installerStep7Controller.get('configGroups').mapProperty('n')).to.eql(['n2', 'n1', 'n3']);
      expect(installerStep7Controller.get('selectedConfigGroup')).to.eql(defaultGroup);
    });
  });

  describe('#loadConfigGroups', function () {
    beforeEach(function () {
      installerStep7Controller.reopen({
        wizardController: Em.Object.create({
          allHosts: [
            {hostName: 'h1'},
            {hostName: 'h2'},
            {hostName: 'h3'}
          ]
        })
      });
    });
    afterEach(function () {
      App.ServiceConfigGroup.find().clear();
    });
    it('shouldn\'t do nothing if only MISC available', function () {
      var configGroups = [
        {}
      ];
      installerStep7Controller.reopen({
        stepConfigs: [Em.Object.create({serviceName: 'MISC', configGroups: configGroups})]
      });
      installerStep7Controller.loadConfigGroups([]);
      expect(installerStep7Controller.get('stepConfigs.firstObject.configGroups')).to.eql(configGroups);
    });
  });

  describe('#_getDisplayedConfigGroups', function () {
    it('should return [] if no selected group', function () {
      installerStep7Controller.reopen({
        content: {services: []},
        selectedConfigGroup: null
      });
      expect(installerStep7Controller._getDisplayedConfigGroups()).to.eql([]);
    });
    it('should return default config group if another selected', function () {
      var defaultGroup = Em.Object.create({isDefault: false});
      installerStep7Controller.reopen({
        content: {services: []},
        selectedConfigGroup: defaultGroup
      });
      expect(installerStep7Controller._getDisplayedConfigGroups()).to.eql([defaultGroup]);
    });
    it('should return other groups if default selected', function () {
      var defaultGroup = Em.Object.create({isDefault: true}),
        cfgG = Em.Object.create({isDefault: true}),
        configGroups = Em.A([
          Em.Object.create({isDefault: false}),
          Em.Object.create({isDefault: false}),
          cfgG,
          Em.Object.create({isDefault: false})
        ]);
      installerStep7Controller.reopen({
        content: {services: []},
        selectedConfigGroup: defaultGroup,
        selectedService: {configGroups: configGroups}
      });
      expect(installerStep7Controller._getDisplayedConfigGroups()).to.eql(configGroups.without(cfgG));
    });
  });

  describe('#_setEditableValue', function () {
    it('shouldn\'t update config if no selectedConfigGroup', function () {
      installerStep7Controller.reopen({
        selectedConfigGroup: null
      });
      var config = Em.Object.create({isEditable: null});
      var updatedConfig = installerStep7Controller._setEditableValue(config);
      expect(updatedConfig.get('isEditable')).to.be.null;
    });
    it('should set isEditable equal to selectedGroup.isDefault if service not installed', function () {
      var isDefault = true;
      installerStep7Controller.reopen({
        installedServiceNames: [],
        selectedService: {serviceName: 'abc'},
        selectedConfigGroup: Em.Object.create({isDefault: isDefault})
      });
      var config = Em.Object.create({isEditable: null});
      var updatedConfig = installerStep7Controller._setEditableValue(config);
      expect(updatedConfig.get('isEditable')).to.equal(isDefault);
      installerStep7Controller.toggleProperty('selectedConfigGroup.isDefault');
      updatedConfig = installerStep7Controller._setEditableValue(config);
      expect(updatedConfig.get('isEditable')).to.equal(!isDefault);
    });
    Em.A([
        {
          isEditable: false,
          isReconfigurable: false,
          isDefault: true,
          e: false
        },
        {
          isEditable: true,
          isReconfigurable: true,
          isDefault: true,
          e: true
        },
        {
          isEditable: false,
          isReconfigurable: true,
          isDefault: false,
          e: false
        },
        {
          isEditable: true,
          isReconfigurable: false,
          isDefault: false,
          e: false
        }
      ]).forEach(function (test) {
        it('service installed, isEditable = ' + test.isEditable.toString() + ', isReconfigurable = ' + test.isReconfigurable.toString(), function () {
          var config = Em.Object.create({
            isReconfigurable: test.isReconfigurable,
            isEditable: test.isEditable
          });
          installerStep7Controller.reopen({
            installedServiceNames: Em.A(['a']),
            selectedService: Em.Object.create({serviceName: 'a'}),
            selectedConfigGroup: Em.Object.create({isDefault: test.isDefault})
          });
          var updateConfig = installerStep7Controller._setEditableValue(config);
          expect(updateConfig.get('isEditable')).to.equal(test.e);
        });
      });
  });

  describe('#_setOverrides', function () {

    it('shouldn\'t update config if no selectedConfigGroup', function () {
      installerStep7Controller.reopen({
        selectedConfigGroup: null
      });
      var config = Em.Object.create({overrides: null});
      var updatedConfig = installerStep7Controller._setOverrides(config, []);
      expect(updatedConfig.get('overrides')).to.be.null;
    });

    it('no overrideToAdd', function () {
      var isDefault = true,
        name = 'n1',
        config = Em.Object.create({overrides: null, name: name, flag: 'flag'}),
        overrides = Em.A([
          Em.Object.create({name: name, value: 'v1'}),
          Em.Object.create({name: name, value: 'v2'}),
          Em.Object.create({name: 'n2', value: 'v3'})
        ]);
      installerStep7Controller.reopen({
        overrideToAdd: null,
        selectedConfigGroup: Em.Object.create({
          isDefault: isDefault
        })
      });
      var updatedConfig = installerStep7Controller._setOverrides(config, overrides);
      expect(updatedConfig.get('overrides.length')).to.equal(2);
      expect(updatedConfig.get('overrides').everyProperty('isEditable', !isDefault)).to.equal(true);
      expect(updatedConfig.get('overrides').everyProperty('parentSCP.flag', 'flag')).to.equal(true);
    });

    it('overrideToAdd exists', function () {
      var isDefault = true,
        name = 'n1',
        config = Em.Object.create({overrides: null, name: name, flag: 'flag'}),
        overrides = Em.A([
          Em.Object.create({name: name, value: 'v1'}),
          Em.Object.create({name: name, value: 'v2'}),
          Em.Object.create({name: 'n2', value: 'v3'})
        ]);
      installerStep7Controller.reopen({
        overrideToAdd: Em.Object.create({name: name}),
        selectedService: {configGroups: [Em.Object.create({name: 'n', properties: []})]},
        selectedConfigGroup: Em.Object.create({
          isDefault: isDefault,
          name: 'n'
        })
      });
      var updatedConfig = installerStep7Controller._setOverrides(config, overrides);
      expect(updatedConfig.get('overrides.length')).to.equal(3);
      expect(updatedConfig.get('overrides').everyProperty('isEditable', !isDefault)).to.equal(true);
      expect(updatedConfig.get('overrides').everyProperty('parentSCP.flag', 'flag')).to.equal(true);
    });
  });

  describe('#switchConfigGroupConfigs', function () {

    it('if selectedConfigGroup is null, serviceConfigs shouldn\'t be changed', function () {
      installerStep7Controller.reopen({
        selectedConfigGroup: null,
        content: {services: []},
        serviceConfigs: {configs: [
          {overrides: []},
          {overrides: []}
        ]}
      });
      installerStep7Controller.switchConfigGroupConfigs();
      expect(installerStep7Controller.get('serviceConfigs.configs').everyProperty('overrides.length', 0)).to.equal(true);
    });

    describe('should set configs for serviceConfigs', function () {

      var configGroups = [
        Em.Object.create({
          properties: [
            {name: 'g1', value: 'v1'},
            {name: 'g2', value: 'v2'}
          ]
        })
      ];

      beforeEach(function () {
        sinon.stub(installerStep7Controller, '_getDisplayedConfigGroups', function () {
          return configGroups;
        });
        sinon.stub(installerStep7Controller, '_setEditableValue', function (config) {
          config.set('isEditable', true);
          return config;
        });
        installerStep7Controller.reopen({
          selectedConfigGroup: Em.Object.create({isDefault: true, name: 'g1'}),
          content: {services: []},
          selectedService: {configs: Em.A([Em.Object.create({name: 'g1', overrides: [], properties: []}), Em.Object.create({name: 'g2', overrides: []})])},
          serviceConfigs: {configs: [Em.Object.create({name: 'g1'})]}
        });
        installerStep7Controller.switchConfigGroupConfigs();
        this.configs = installerStep7Controller.get('selectedService.configs');
      });

      afterEach(function () {
        installerStep7Controller._getDisplayedConfigGroups.restore();
        installerStep7Controller._setEditableValue.restore();
      });

      it('g1 has 1 override', function () {
        expect(this.configs.findProperty('name', 'g1').get('overrides').length).to.equal(1);
      });

      it('g2 has 1 override', function () {
        expect(this.configs.findProperty('name', 'g2').get('overrides').length).to.equal(1);
      });

      it('all configs are editable', function () {
        expect(this.configs.everyProperty('isEditable', true)).to.equal(true);
      });

    });

  });

  describe('#selectProperService', function () {
    Em.A([
        {
          name: 'addServiceController',
          stepConfigs: [
            {selected: false, name: 'n1'},
            {selected: true, name: 'n2'},
            {selected: true, name: 'n3'}
          ],
          e: 'n2'
        },
        {
          name: 'installerController',
          stepConfigs: [
            {showConfig: false, name: 'n1'},
            {showConfig: false, name: 'n2'},
            {showConfig: true, name: 'n3'}
          ],
          e: 'n3'
        }
      ]).forEach(function (test) {
        describe(test.name, function () {

          beforeEach(function () {
            sinon.stub(installerStep7Controller, 'selectedServiceObserver', Em.K);
            installerStep7Controller.reopen({
              wizardController: Em.Object.create({
                name: test.name
              }),
              stepConfigs: test.stepConfigs
            });
            installerStep7Controller.selectProperService();
          });

          afterEach(function () {
            installerStep7Controller.selectedServiceObserver.restore();
          });

          it('selected service name is valid', function () {
            expect(installerStep7Controller.get('selectedService.name')).to.equal(test.e);
          });
        });
      });
  });

  describe.skip('#setStepConfigs', function () {
    var serviceConfigs;
    beforeEach(function () {
      installerStep7Controller.reopen({
        content: {services: []},
        wizardController: Em.Object.create({
          getDBProperty: function (key) {
            return this.get(key);
          }
        })
      });
      sinon.stub(installerStep7Controller, 'renderConfigs', function () {
        return serviceConfigs;
      });
      this.stub = sinon.stub(App, 'get');
    });

    afterEach(function () {
      installerStep7Controller.renderConfigs.restore();
      App.get.restore();
    });

    it('if wizard isn\'t addService, should set output of installerStep7Controller.renderConfigs', function () {
      serviceConfigs = Em.A([
        {serviceName:'HDFS', configs: []},
        {}
      ]);
      installerStep7Controller.set('wizardController.name', 'installerController');
      installerStep7Controller.setStepConfigs([], []);
      expect(installerStep7Controller.get('stepConfigs')).to.eql(serviceConfigs);
    });

    it('addServiceWizard used', function () {
      serviceConfigs = Em.A([Em.Object.create({serviceName: 'HDFS', configs: []}), Em.Object.create({serviceName: 's2'})]);
      installerStep7Controller.set('wizardController.name', 'addServiceController');
      installerStep7Controller.reopen({selectedServiceNames: ['s2']});
      installerStep7Controller.setStepConfigs([], []);
      expect(installerStep7Controller.get('stepConfigs').everyProperty('showConfig', true)).to.equal(true);
      expect(installerStep7Controller.get('stepConfigs').findProperty('serviceName', 's2').get('selected')).to.equal(true);
    });

    it('addServiceWizard used, HA enabled', function () {
      this.stub.withArgs('isHaEnabled').returns(true);
      serviceConfigs = Em.A([
        Em.Object.create({
          serviceName: 'HDFS',
          configs: [
            Em.Object.create({category: 'SECONDARY_NAMENODE'}),
            Em.Object.create({category: 'SECONDARY_NAMENODE'}),
            Em.Object.create({category: 'NameNode'}),
            Em.Object.create({category: 'NameNode'}),
            Em.Object.create({category: 'SECONDARY_NAMENODE'})
          ]
        }),
        Em.Object.create({serviceName: 's2'})]
      );
      installerStep7Controller.set('wizardController.name', 'addServiceController');
      installerStep7Controller.reopen({selectedServiceNames: ['HDFS', 's2']});
      installerStep7Controller.setStepConfigs([], []);
      expect(installerStep7Controller.get('stepConfigs').everyProperty('showConfig', true)).to.equal(true);
      expect(installerStep7Controller.get('stepConfigs').findProperty('serviceName', 'HDFS').get('selected')).to.equal(true);
      expect(installerStep7Controller.get('stepConfigs').findProperty('serviceName', 'HDFS').get('configs').length).to.equal(5);
    });

    it('not windows stack', function () {

      this.stub.withArgs('isHadoopWindowsStack').returns(false);
      this.stub.withArgs('isHaEnabled').returns(false);

      serviceConfigs = Em.A([
        Em.Object.create({
          serviceName: 'HDFS',
          configs: [
            {category: 'NameNode'},
            {category: 'NameNode'}
          ]
        }),
        Em.Object.create({serviceName: 's2'})]
      );
      installerStep7Controller.reopen({selectedServiceNames: ['HDFS', 's2']});
      installerStep7Controller.setStepConfigs([], []);
      expect(installerStep7Controller.get('stepConfigs').findProperty('serviceName', 'HDFS').get('configs').length).to.equal(2);
    });

    it('windows stack', function () {

      this.stub.withArgs('isHadoopWindowsStack').returns(true);
      this.stub.withArgs('isHaEnabled').returns(false);

      serviceConfigs = Em.A([
        Em.Object.create({
          serviceName: 'HDFS',
          configs: [
            {category: 'NameNode'},
            {category: 'NameNode'}
          ]
        }),
        Em.Object.create({serviceName: 's2'})]
      );

      installerStep7Controller.reopen({selectedServiceNames: ['HDFS', 's2']});
      installerStep7Controller.set('installedServiceNames',['HDFS', 's2', 's3']);
      installerStep7Controller.setStepConfigs([], []);

      expect(installerStep7Controller.get('stepConfigs').findProperty('serviceName', 'HDFS').get('configs').length).to.equal(2);

    });

  });

  describe('#checkHostOverrideInstaller', function () {
    beforeEach(function () {
      sinon.stub(installerStep7Controller, 'loadConfigGroups', Em.K);
      sinon.stub(installerStep7Controller, 'loadInstalledServicesConfigGroups', Em.K);
      sinon.stub(App, 'get', function (k) {
        if (k === 'supports.hostOverridesInstaller') return false;
        return Em.get(App, k);
      });
    });
    afterEach(function () {
      installerStep7Controller.loadConfigGroups.restore();
      installerStep7Controller.loadInstalledServicesConfigGroups.restore();
      App.get.restore();
    });
    Em.A([
        {
          installedServiceNames: [],
          m: 'installedServiceNames is empty',
          e: {
            loadConfigGroups: true,
            loadInstalledServicesConfigGroups: false
          }
        },
        {
          installedServiceNames: ['s1', 's2', 's3'],
          areInstalledConfigGroupsLoaded: false,
          m: 'installedServiceNames isn\'t empty, config groups not yet loaded',
          e: {
            loadConfigGroups: true,
            loadInstalledServicesConfigGroups: true
          }
        },
        {
          installedServiceNames: ['s1', 's2', 's3'],
          areInstalledConfigGroupsLoaded: true,
          m: 'installedServiceNames isn\'t empty, config groups already loaded',
          e: {
            loadConfigGroups: true,
            loadInstalledServicesConfigGroups: false
          }
        }
      ]).forEach(function (test) {
        describe(test.m, function () {

          beforeEach(function () {
            installerStep7Controller.reopen({
              installedServiceNames: test.installedServiceNames,
              wizardController: {
                areInstalledConfigGroupsLoaded: test.areInstalledConfigGroupsLoaded
              }
            });
            installerStep7Controller.checkHostOverrideInstaller();
          });

          if (test.e.loadConfigGroups) {
            it('loadConfigGroups is called once', function () {
              expect(installerStep7Controller.loadConfigGroups.calledOnce).to.equal(true);
            });
          }
          else {
            it('loadConfigGroups is not called', function () {
              expect(installerStep7Controller.loadConfigGroups.called).to.equal(false);
            });
          }
          if (test.e.loadInstalledServicesConfigGroups) {
            it('loadInstalledServicesConfigGroups is called once', function () {
              expect(installerStep7Controller.loadInstalledServicesConfigGroups.calledOnce).to.equal(true);
            });
          }
          else {
            it('loadInstalledServicesConfigGroups is not called', function () {
              expect(installerStep7Controller.loadInstalledServicesConfigGroups.called).to.equal(false);
            });
          }
        });
      });
  });

  describe('#loadStep', function () {
    beforeEach(function () {
      installerStep7Controller.reopen({
        content: {services: []},
        wizardController: Em.Object.create({
          getDBProperty: function (k) {
            return this.get(k);
          },
          stackConfigsLoaded: true
        })
      });
      sinon.stub(App.config, 'fileConfigsIntoTextarea', Em.K);
      sinon.stub(installerStep7Controller, 'clearStep', Em.K);
      sinon.stub(installerStep7Controller, 'getConfigTags', Em.K);
      sinon.stub(installerStep7Controller, 'setInstalledServiceConfigs', Em.K);
      sinon.stub(installerStep7Controller, 'checkHostOverrideInstaller', Em.K);
      sinon.stub(installerStep7Controller, 'selectProperService', Em.K);
      sinon.stub(installerStep7Controller, 'applyServicesConfigs', Em.K);
      sinon.stub(App.router, 'send', Em.K);
    });
    afterEach(function () {
      App.config.fileConfigsIntoTextarea.restore();
      installerStep7Controller.clearStep.restore();
      installerStep7Controller.getConfigTags.restore();
      installerStep7Controller.setInstalledServiceConfigs.restore();
      installerStep7Controller.checkHostOverrideInstaller.restore();
      installerStep7Controller.selectProperService.restore();
      installerStep7Controller.applyServicesConfigs.restore();
      App.router.send.restore();
    });
    it('should call clearStep', function () {
      installerStep7Controller.loadStep();
      expect(installerStep7Controller.clearStep.calledOnce).to.equal(true);
    });
    it('shouldn\'t do nothing if isAdvancedConfigLoaded is false', function () {
      installerStep7Controller.set('wizardController.stackConfigsLoaded', false);
      installerStep7Controller.loadStep();
      expect(installerStep7Controller.clearStep.called).to.equal(false);
    });
    it('should call setInstalledServiceConfigs for addServiceController', function () {
      installerStep7Controller.set('wizardController.name', 'addServiceController');
      installerStep7Controller.loadStep();
      expect(installerStep7Controller.setInstalledServiceConfigs.calledOnce).to.equal(true);
    });
  });

  describe('#applyServicesConfigs', function() {
    beforeEach(function() {
      installerStep7Controller.reopen({
        allSelectedServiceNames: []
      });
      sinon.stub(App.config, 'fileConfigsIntoTextarea', function(configs) {
        return configs;
      });
      sinon.stub(installerStep7Controller, 'loadServerSideConfigsRecommendations', function() {
        return $.Deferred().resolve();
      });
      sinon.stub(installerStep7Controller, 'checkHostOverrideInstaller', Em.K);
      sinon.stub(installerStep7Controller, 'selectProperService', Em.K);
      sinon.stub(App.router, 'send', Em.K);
      sinon.stub(App.StackService, 'find', function () {
        return {
          findProperty: function () {
            return Em.Object.create({
              isInstalled: true,
              isSelected: false
            });
          },
          filterProperty: function () {
            return [];
          }
        }
      });
      installerStep7Controller.applyServicesConfigs([{name: 'configs'}]);
    });

    afterEach(function () {
      App.config.fileConfigsIntoTextarea.restore();
      installerStep7Controller.loadServerSideConfigsRecommendations.restore();
      installerStep7Controller.checkHostOverrideInstaller.restore();
      installerStep7Controller.selectProperService.restore();
      App.router.send.restore();
      App.StackService.find.restore();
    });

    it('loadServerSideConfigsRecommendations is called once' , function () {
     expect(installerStep7Controller.loadServerSideConfigsRecommendations.calledOnce).to.equal(true);
    });
    it('isRecommendedLoaded is true' , function () {
     expect(installerStep7Controller.get('isRecommendedLoaded')).to.equal(true);
    });
    it('checkHostOverrideInstalleris called once' , function () {
     expect(installerStep7Controller.checkHostOverrideInstaller.calledOnce).to.equal(true);
    });
    it('selectProperServiceis called once' , function () {
     expect(installerStep7Controller.selectProperService.calledOnce).to.equal(true);
    });

    Em.A([
      {
        allSelectedServiceNames: ['YARN'],
        fileConfigsIntoTextarea: true,
        m: 'should run fileConfigsIntoTextarea'
      }
    ]).forEach(function(t) {
      it(t.m, function () {
        installerStep7Controller.reopen({
          allSelectedServiceNames: t.allSelectedServiceNames
        });
        installerStep7Controller.applyServicesConfigs([{name: 'configs'}]);
        if (t.fileConfigsIntoTextarea) {
          expect(App.config.fileConfigsIntoTextarea.calledWith([{name: 'configs'}], 'capacity-scheduler.xml')).to.equal(true);
        } else {
          expect(App.config.fileConfigsIntoTextarea.calledOnce).to.equal(false);
        }
      });
    });
  });

  describe('#_updateIsEditableFlagForConfig', function () {
    Em.A([
        {
          isAdmin: false,
          isReconfigurable: false,
          isHostsConfigsPage: true,
          defaultGroupSelected: false,
          m: 'false for non-admin users',
          e: false
        },
        {
          isAdmin: true,
          isReconfigurable: false,
          isHostsConfigsPage: true,
          defaultGroupSelected: false,
          m: 'false if defaultGroupSelected is false and isHostsConfigsPage is true',
          e: false
        },
        {
          isAdmin: true,
          isReconfigurable: false,
          isHostsConfigsPage: true,
          defaultGroupSelected: true,
          m: 'false if defaultGroupSelected is true and isHostsConfigsPage is true',
          e: false
        },
        {
          isAdmin: true,
          isReconfigurable: false,
          isHostsConfigsPage: false,
          defaultGroupSelected: false,
          m: 'false if defaultGroupSelected is false and isHostsConfigsPage is false',
          e: false
        }
      ]).forEach(function (test) {
        it(test.m, function () {
          installerStep7Controller.reopen({isHostsConfigsPage: test.isHostsConfigsPage});
          var serviceConfigProperty = Em.Object.create({
            isReconfigurable: test.isReconfigurable
          });
          installerStep7Controller._updateIsEditableFlagForConfig(serviceConfigProperty, test.defaultGroupSelected);
          expect(serviceConfigProperty.get('isEditable')).to.equal(test.e);
        });
      });
  });

  describe('#_updateOverridesForConfig', function () {

    it('should set empty array', function () {
      var serviceConfigProperty = Em.Object.create({
        overrides: null
      }), component = Em.Object.create();
      installerStep7Controller._updateOverridesForConfig(serviceConfigProperty, component);
      expect(serviceConfigProperty.get('overrides')).to.eql(Em.A([]));
    });

    describe('host overrides not supported', function () {
      var serviceConfigProperty = Em.Object.create({
        overrides: [
          {value: 'new value'}
        ]
      });
      var component = Em.Object.create({selectedConfigGroup: {isDefault: false}});

      beforeEach(function () {
        installerStep7Controller._updateOverridesForConfig(serviceConfigProperty, component);
      });
      it('there is 1 override', function () {
        expect(serviceConfigProperty.get('overrides').length).to.equal(1);
      });
      it('override value is valid', function () {
        expect(serviceConfigProperty.get('overrides.firstObject.value')).to.equal('new value');
      });
      it('override is not original SCP', function () {
        expect(serviceConfigProperty.get('overrides.firstObject.isOriginalSCP')).to.equal(false);
      });
      it('override is linked to parent', function () {
        expect(serviceConfigProperty.get('overrides.firstObject.parentSCP')).to.eql(serviceConfigProperty);
      });
    });

    describe('host overrides supported', function () {
      var serviceConfigProperty;
      var component;
      beforeEach(function () {
        sinon.stub(App, 'get', function (k) {
          if (k === 'supports.hostOverrides') return true;
          return Em.get(App, k);
        });
        serviceConfigProperty = Em.Object.create({
          overrides: [
            {value: 'new value', group: Em.Object.create({name: 'n1'})}
          ]
        });
        component = Em.Object.create({
          selectedConfigGroup: {isDefault: true},
          configGroups: Em.A([
            Em.Object.create({name: 'n1', properties: []})
          ])
        });
        installerStep7Controller._updateOverridesForConfig(serviceConfigProperty, component);
      });

      afterEach(function () {
        App.get.restore();
      });
      it('there is 1 override', function () {
        expect(serviceConfigProperty.get('overrides').length).to.equal(1);
      });
      it('override.value is valid', function () {
        expect(serviceConfigProperty.get('overrides.firstObject.value')).to.equal('new value');
      });
      it('override is not original SCP', function () {
        expect(serviceConfigProperty.get('overrides.firstObject.isOriginalSCP')).to.equal(false);
      });
      it('override.parentSCP is valid', function () {
        expect(serviceConfigProperty.get('overrides.firstObject.parentSCP')).to.eql(serviceConfigProperty);
      });
      it('there is 1 property in the config group', function () {
        expect(component.get('configGroups.firstObject.properties').length).to.equal(1);
      });
      it('property in the config group is not editable', function () {
        expect(component.get('configGroups.firstObject.properties.firstObject.isEditable')).to.equal(false);
      });
      it('property in the config group is linked to it', function () {
        expect(component.get('configGroups.firstObject.properties.firstObject.group')).to.be.object;
      });
    });

  });

  describe('#setInstalledServiceConfigs', function () {

    var controller = App.WizardStep7Controller.create({
        installedServiceNames: ['HBASE', 'AMBARI_METRICS']
      }),
      configs = [
        {
          name: 'hbase.client.scanner.caching',
          value: '1000',
          serviceName: 'HBASE',
          filename: 'hbase-site.xml'
        },
        {
          name: 'hbase.client.scanner.caching',
          value: '2000',
          serviceName: 'AMBARI_METRICS',
          filename: 'ams-hbase-site.xml'
        }
      ],
      configsByTags = [
        {
          type: 'hbase-site',
          tag: 'version2',
          properties: {
            'hbase.client.scanner.caching': '1500'
          }
        },
        {
          type: 'ams-hbase-site',
          tag: 'version2',
          properties: {
            'hbase.client.scanner.caching': '2500'
          }
        },
        {
          type: 'site-without-properties',
          tag: 'version1'
        }
      ],
      installedServiceNames = ['HBASE', 'AMBARI_METRICS'];

    describe('should handle properties with the same name', function () {
      var properties;
      beforeEach(function () {
        controller.setInstalledServiceConfigs(configs, configsByTags, installedServiceNames);
        properties = configs.filterProperty('name', 'hbase.client.scanner.caching');
      });
      it('there are 2 properties', function () {
        expect(properties).to.have.length(2);
      });
      it('hbase-site/ value is valid', function () {
        expect(properties.findProperty('filename', 'hbase-site.xml').value).to.equal('1500');
      });
      it('hbase-site/ savedValue is valid', function () {
        expect(properties.findProperty('filename', 'hbase-site.xml').savedValue).to.equal('1500');
      });
      it('ams-hbase-site/ value is valid', function () {
        expect(properties.findProperty('filename', 'ams-hbase-site.xml').value).to.equal('2500');
      });
      it('ams-hbase-site/ savedValue is valid', function () {
        expect(properties.findProperty('filename', 'ams-hbase-site.xml').savedValue).to.equal('2500');
      });
    });

  });

  describe('#getAmbariDatabaseSuccess', function () {

    var controller = App.WizardStep7Controller.create({
        stepConfigs: [
          {
            serviceName: 'HIVE',
            configs: [
              {
                name: 'hive_hostname',
                value: 'h0'
              }
            ]
          }
        ]
      }),
      cases = [
        {
          data: {
            hostComponents: []
          },
          mySQLServerConflict: false,
          title: 'no Ambari Server host components'
        },
        {
          data: {
            hostComponents: [
              {
                RootServiceHostComponents: {
                  properties: {
                    'server.jdbc.url': 'jdbc:mysql://h0/db0?createDatabaseIfNotExist=true'
                  }
                }
              }
            ]
          },
          mySQLServerConflict: true,
          title: 'Ambari MySQL Server and Hive Server are on the same host'
        },
        {
          data: {
            hostComponents: [
              {
                RootServiceHostComponents: {
                  properties: {
                    'server.jdbc.url': 'jdbc:mysql://h1/db1?createDatabaseIfNotExist=true'
                  }
                }
              }
            ]
          },
          mySQLServerConflict: false,
          title: 'Ambari MySQL Server and Hive Server are on different hosts'
        }
      ];

    cases.forEach(function (item) {
      it(item.title, function () {
        controller.getAmbariDatabaseSuccess(item.data);
        expect(controller.get('mySQLServerConflict')).to.equal(item.mySQLServerConflict);
      });
    });

  });

  describe('#showDatabaseConnectionWarningPopup', function () {

    var cases = [
        {
          method: 'onSecondary',
          submitButtonClicked: false,
          isRejected: true,
          title: 'Cancel button clicked'
        },
        {
          method: 'onPrimary',
          submitButtonClicked: true,
          isResolved: true,
          title: 'Proceed Anyway button clicked'
        }
      ],
      dfd,
      testObject,
      serviceNames = ['HIVE', 'OOZIE'],
      bodyMessage = 'HIVE, OOZIE';

    beforeEach(function () {
      installerStep7Controller.set('submitButtonClicked', true);
      dfd = $.Deferred(function (d) {
        d.done(function () {
          testObject.isResolved = true;
        });
        d.fail(function () {
          testObject.isRejected = true;
        })
      });
      testObject = {};
    });

    cases.forEach(function (item) {
      describe(item.title, function () {
        var popup;
        beforeEach(function () {
          popup = installerStep7Controller.showDatabaseConnectionWarningPopup(serviceNames, dfd);
        });

        it('popup body is valid', function () {
          expect(popup.get('body')).to.equal(Em.I18n.t('installer.step7.popup.database.connection.body').format(bodyMessage));
        });

        it('after ' + item.method + ' execution', function () {
          popup[item.method]();
          expect(testObject.isResolved).to.equal(item.isResolved);
          expect(testObject.isRejected).to.equal(item.isRejected);
          expect(installerStep7Controller.get('submitButtonClicked')).to.equal(item.submitButtonClicked);
        });
      });
    });

  });

  describe('#issuesFilterText', function () {

    issuesFilterCases.forEach(function (item) {
      it(item.title, function () {
        issuesFilterTestSetup(installerStep7Controller, item);
        expect(installerStep7Controller.get('issuesFilterText')).to.equal(item.issuesFilterText);
      })
    });

  });

  describe.skip('#loadServiceTagsSuccess', function () {
    it('should create ClusterSiteToTagMap', function () {
      var params = Em.Object.create({
        serviceName: "OOZIE",
        serviceConfigsDef: Em.Object.create({
          configTypes: Em.Object.create({
            site3: true,
            site2: true,
            site1: true
          })
        })
      });
      var wizardController = Em.Object.create({
          allHosts: [
            {hostName: 'h1'},
            {hostName: 'h2'},
            {hostName: 'h3'}
          ]
      });
      installerStep7Controller.set('wizardController', wizardController);
      installerStep7Controller.set('stepConfigs', Em.A([Em.Object.create({serviceName: 'OOZIE', configs: Em.A([]) })]));
      var desired_configs = {
        site1: {
          tag: "tag1"
        },
        site2: {
          tag: "tag2"
        },
        site3: {
          tag: "tag3"
        }
      };
      var data = {
        config_groups: Em.A([Em.Object.create({
          ConfigGroup: Em.Object.create({
            tag: 'OOZIE',
            hosts: Em.A([Em.Object.create({host_name: 'h1'})]),
            id: 1,
            group_name: "",
            description: "",
            desired_configs: Em.A([Em.Object.create({
              type: '1',
              tag: 'h1'
            })])
          })
        })]),
        Clusters: {
          desired_configs: desired_configs
        }
      };
      installerStep7Controller.loadServiceTagsSuccess(data, {}, params);
      var result = installerStep7Controller.get("loadedClusterSiteToTagMap");
      expect(JSON.parse(JSON.stringify(result))).to.eql(JSON.parse(JSON.stringify({"site1":"tag1","site2":"tag2","site3":"tag3"})));
    })
  });

  describe('#issuesFilterLinkText', function () {

    issuesFilterCases.forEach(function (item) {
      it(item.title, function () {
        issuesFilterTestSetup(installerStep7Controller, item);
        expect(installerStep7Controller.get('issuesFilterLinkText')).to.equal(item.issuesFilterLinkText);
      })
    });

  });

  describe('#toggleIssuesFilter', function () {
    it('should toggle issues filter', function () {
      var issuesFilter = installerStep7Controller.get('filterColumns').findProperty('attributeName', 'hasIssues');
      issuesFilter.set('selected', false);
      installerStep7Controller.toggleIssuesFilter();
      expect(issuesFilter.get('selected')).to.be.true;
      installerStep7Controller.toggleIssuesFilter();
      expect(issuesFilter.get('selected')).to.be.false;
    });
    it('selected service should be changed', function () {
      installerStep7Controller.setProperties({
        selectedService: {
          errorCount: 0,
          configGroups: []
        },
        stepConfigs: [
          {
            errorCount: 1,
            configGroups: []
          },
          {
            errorCount: 2,
            configGroups: []
          }
        ]
      });
      installerStep7Controller.toggleIssuesFilter();
      expect(installerStep7Controller.get('selectedService')).to.eql({
        errorCount: 1,
        configGroups: []
      });
    });
  });

  describe('#addKerberosDescriptorConfigs', function() {
    var configs = [
      { name: 'prop1', displayName: 'Prop1' },
      { name: 'prop2', displayName: 'Prop2' },
      { name: 'prop3', displayName: 'Prop3' }
    ];
    var descriptor = [
      Em.Object.create({ name: 'prop4', filename: 'file-1'}),
      Em.Object.create({ name: 'prop1', filename: 'file-1'})
    ];
    var propertiesAttrTests = [
      {
        attr: 'isUserProperty', val: false,
        m: 'descriptor properties should not be marked as custom'
      },
      {
        attr: 'category', val: 'Advanced file-1',
        m: 'descriptor properties should be added to Advanced category'
      },
      {
        attr: 'isOverridable', val: false,
        m: 'descriptor properties should not be overriden'
      }
    ];

    propertiesAttrTests.forEach(function(test) {
      it(test.m, function() {
        installerStep7Controller.addKerberosDescriptorConfigs(configs, descriptor);
        expect(configs.findProperty('name', 'prop1')[test.attr]).to.be.eql(test.val);
      });
    });
  });

  describe('#errorsCount', function () {

    it('should ignore configs with widgets (enhanced configs)', function () {

      installerStep7Controller.reopen({selectedService: Em.Object.create({
          configsWithErrors: Em.A([
            Em.Object.create({widget: {}}),
            Em.Object.create({widget: null})
          ])
        })
      });

      expect(installerStep7Controller.get('errorsCount')).to.equal(1);

    });

  });

  describe('#_reconfigureServicesOnNnHa', function () {

    var dfsNameservices = 'some_cluster';

    Em.A([
      {
        serviceName: 'HBASE',
        configToUpdate: 'hbase.rootdir',
        oldValue: 'hdfs://nameserv:8020/apps/hbase/data',
        expectedNewValue: 'hdfs://' + dfsNameservices + '/apps/hbase/data'
      },
      {
        serviceName: 'ACCUMULO',
        configToUpdate: 'instance.volumes',
        oldValue: 'hdfs://localhost:8020/apps/accumulo/data',
        expectedNewValue: 'hdfs://' + dfsNameservices + '/apps/accumulo/data'
      },
      {
        serviceName: 'HAWQ',
        configToUpdate: 'hawq_dfs_url',
        oldValue: 'localhost:8020/hawq_data',
        expectedNewValue: dfsNameservices + '/hawq_data'
      }
    ]).forEach(function (test) {
      it(test.serviceName + ' ' + test.configToUpdate, function () {
        var serviceConfigs = [App.ServiceConfig.create({
          serviceName: test.serviceName,
          configs: [
            Em.Object.create({
              name: test.configToUpdate,
              value: test.oldValue
            })
          ]
        }),
          App.ServiceConfig.create({
            serviceName: 'HDFS',
            configs: [
              Em.Object.create({
                name: 'dfs.nameservices',
                value: dfsNameservices
              })
            ]
          })];
        installerStep7Controller.reopen({
          selectedServiceNames: [test.serviceName, 'HDFS']
        });
        serviceConfigs = installerStep7Controller._reconfigureServicesOnNnHa(serviceConfigs);
        expect(serviceConfigs.findProperty('serviceName', test.serviceName).configs.findProperty('name', test.configToUpdate).get('value')).to.equal(test.expectedNewValue);
      });
    });

  });

  describe('#showOozieDerbyWarning', function() {
    var controller;

    beforeEach(function() {
      controller = App.WizardStep7Controller.create({});
      sinon.stub(App.ModalPopup, 'show', Em.K);
    });

    afterEach(function() {
      App.ModalPopup.show.restore();
    });

    Em.A([
      {
        selectedServiceNames: ['HDFS', 'OOZIE'],
        databaseType: Em.I18n.t('installer.step7.oozie.database.new'),
        e: true,
        m: 'Oozie selected with derby database, warning popup should be shown'
      },
      {
        selectedServiceNames: ['HDFS'],
        databaseType: Em.I18n.t('installer.step7.oozie.database.new'),
        e: false,
        m: 'Oozie not selected warning popup should be skipped'
      },
      {
        selectedServiceNames: ['HDFS', 'OOZIE'],
        databaseType: 'New Mysql Database',
        e: false,
        m: 'Oozie selected, mysql database used, warning popup should be sk'
      }
    ]).forEach(function(test) {
      describe(test.m, function() {

        beforeEach(function () {
          sinon.stub(controller, 'findConfigProperty').returns(Em.Object.create({ value: test.databaseType}));
          controller.reopen({
            selectedServiceNames: test.selectedServiceNames
          });
          controller.showOozieDerbyWarningPopup(Em.K);
        });

        afterEach(function () {
          controller.findConfigProperty.restore();
        });

        it('modal popup is shown needed number of times', function () {
          expect(App.ModalPopup.show.calledOnce).to.equal(test.e);
        });
      });
    });
  });

  describe('#addHostNamesToConfigs', function() {

    beforeEach(function () {
      sinon.stub(App.StackServiceComponent, 'find', function () {
        return Em.Object.create({
          id: 'NAMENODE',
          displayName: 'NameNode'
        });
      });
    });

    afterEach(function () {
      App.StackServiceComponent.find.restore();
    });

    it('should not create duplicate configs', function () {
      var serviceConfig = Em.Object.create({
        configs: [],
        serviceName: 'HDFS',
        configCategories: [
          {
            showHost: true,
            name: 'NAMENODE'
          }
        ]
      });
      var masterComponents = [
        {component: 'NAMENODE', hostName: 'h1'}
      ];
      var slaveComponents = [];
      installerStep7Controller.addHostNamesToConfigs(serviceConfig, masterComponents, slaveComponents);
      expect(serviceConfig.get('configs').filterProperty('name', 'namenode_host').length).to.equal(1);
      installerStep7Controller.addHostNamesToConfigs(serviceConfig, masterComponents, slaveComponents);
      expect(serviceConfig.get('configs').filterProperty('name', 'namenode_host').length).to.equal(1);
    });

  });

  describe('#resolveHiveMysqlDatabase', function () {

    beforeEach(function () {
      installerStep7Controller.get('content').setProperties({
        services: Em.A([
          Em.Object.create({serviceName: 'HIVE', isSelected: true, isInstalled: false})
        ])
      });
      installerStep7Controller.setProperties({
        stepConfigs: Em.A([
          Em.Object.create({serviceName: 'HIVE', configs: [{name: 'hive_database', value: 'New MySQL Database'}]})
        ]),
        mySQLServerConflict: true
      });
      sinon.stub(installerStep7Controller, 'moveNext', Em.K);
      sinon.stub(installerStep7Controller, 'checkMySQLHost', function () {
        return $.Deferred().resolve();
      });
      sinon.spy(App.ModalPopup, 'show');
    });

    afterEach(function () {
      installerStep7Controller.moveNext.restore();
      installerStep7Controller.checkMySQLHost.restore();

      App.ModalPopup.show.restore();
    });

    it('no HIVE service', function () {
      installerStep7Controller.set('content.services', Em.A([]));
      installerStep7Controller.resolveHiveMysqlDatabase();
      expect(installerStep7Controller.moveNext.calledOnce).to.be.true;
      expect(App.ModalPopup.show.called).to.be.false;
    });

    it('if mySQLServerConflict, popup is shown', function () {
      installerStep7Controller.resolveHiveMysqlDatabase();
      expect(installerStep7Controller.moveNext.called).to.be.false;
      expect(App.ModalPopup.show.calledOnce).to.be.true;
    });

  });

  describe('#mySQLWarningHandler', function () {

    beforeEach(function () {
      installerStep7Controller.set('mySQLServerConflict', true);
      sinon.spy(App.ModalPopup, 'show');
      sinon.stub(App.router, 'get').returns({gotoStep: Em.K});
      sinon.stub(App.router.get(), 'gotoStep', Em.K);
    });

    afterEach(function () {
      App.ModalPopup.show.restore();
      App.router.get().gotoStep.restore();
      App.router.get.restore();
    });

    it('warning popup is shown', function () {
      installerStep7Controller.mySQLWarningHandler();
      expect(App.ModalPopup.show.calledOnce).to.be.true;
    });

    it('submitButtonClicked is set to false on primary click', function () {
      installerStep7Controller.mySQLWarningHandler().onPrimary();
      expect(installerStep7Controller.get('submitButtonClicked')).to.be.false;
    });

    it('second popup is shown on secondary click', function () {
      installerStep7Controller.mySQLWarningHandler().onSecondary();
      expect(App.ModalPopup.show.calledTwice).to.be.true;
    });

    it('submitButtonClicked is set to false on secondary click on the second popup', function () {
      installerStep7Controller.mySQLWarningHandler().onSecondary().onSecondary();
      expect(installerStep7Controller.get('submitButtonClicked')).to.be.false;
    });

    it('user is moved to step5 on primary click on the second popup (installerController)', function () {
      installerStep7Controller.set('content.controllerName', 'installerController');
      installerStep7Controller.mySQLWarningHandler().onSecondary().onPrimary();
      expect(App.router.get('installerController').gotoStep.calledWith(5, true)).to.be.true;
    });

    it('user is moved to step2 on primary click on the second popup (addSeviceController)', function () {
      installerStep7Controller.set('content.controllerName', 'addServiceController');
      installerStep7Controller.mySQLWarningHandler().onSecondary().onPrimary();
      expect(App.router.get('addSeviceController').gotoStep.calledWith(2, true)).to.be.true;
    });

  });

});
