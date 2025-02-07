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

require('mixins/common/kdc_credentials_controller_mixin');

var App = require('app');
var credentialsUtils = require('utils/credentials');

var mixedObject;

describe('App.KDCCredentialsControllerMixin', function() {

  beforeEach(function() {
    mixedObject = Em.Object.create(App.KDCCredentialsControllerMixin);
  });

  afterEach(function() {
    mixedObject.destroy();
  });

  describe('#initilizeKDCStoreProperties', function() {
    [
      {
        isStorePersisted: true,
        e: {
          isEditable: true,
          hintMessage: Em.I18n.t('admin.kerberos.credentials.store.hint.supported')
        },
        message: 'Persistent store available, config should be editable, and appropriate hint shown'
      },
      {
        isStorePersisted: false,
        e: {
          isEditable: false,
          hintMessage: Em.I18n.t('admin.kerberos.credentials.store.hint.not.supported')
        },
        message: 'Only temporary store available, config should be disabled, and appropriate hint shown'
      }
    ].forEach(function(test) {
      it(test.message, function() {
        var configs = [],
            config;
        mixedObject.reopen({
          isStorePersisted: function() {
            return test.isStorePersisted;
          }.property()
        });
        mixedObject.initilizeKDCStoreProperties(configs);
        config = configs.findProperty('name', 'persist_credentials');
        Em.keys(test.e).forEach(function(key) {
          assert.equal(Em.get(config, key), test.e[key], 'validate attribute: ' + key);
        });
      });
    });
  });

  describe('#createKDCCredentials', function() {

    beforeEach(function () {
      sinon.stub(App, 'get').withArgs('clusterName').returns('testName');
      sinon.stub(credentialsUtils, 'createCredentials', function() {
        return resolveWith();
      });
      sinon.stub(credentialsUtils, 'updateCredentials', function() {
        return resolveWith();
      });
      mixedObject.reopen({
        isStorePersisted: true
      });
    });

    afterEach(function () {
      App.get.restore();
      credentialsUtils.createCredentials.restore();
      credentialsUtils.updateCredentials.restore();
    });

    var createConfig = function(name, value) {
      return App.ServiceConfigProperty.create({
        name: name,
        value: value
      });
    };
    var resolveWith = function(data) {
      return $.Deferred().resolve(data).promise();
    };
    var rejectWith = function(data) {
      return $.Deferred().reject(data).promise();
    };
    [
      {
        configs: [
          createConfig('admin_password', 'admin'),
          createConfig('admin_principal', 'admin/admin'),
          createConfig('persist_credentials', 'true')
        ],
        credentialsExists: false,
        createCredentialFnCalled: true,
        updateCredentialFnCalled: false,
        e: [
          'testName',
          'kdc.admin.credential',
          {
            type: 'persisted',
            key: 'admin',
            principal: 'admin/admin'
          }
        ],
        message: 'Save Admin credentials checkbox checked, credentials already stored and should be updated as `persisted`'
      },
      {
        configs: [
          createConfig('admin_password', 'admin'),
          createConfig('admin_principal', 'admin/admin'),
          createConfig('persist_credentials', 'true')
        ],
        credentialsExists: true,
        createCredentialFnCalled: false,
        updateCredentialFnCalled: true,
        e: [
          'testName',
          'kdc.admin.credential',
          {
            type: 'persisted',
            key: 'admin',
            principal: 'admin/admin'
          }
        ],
        message: 'Save Admin credentials checkbox checked, no stored credentials, should be created as `persisted`'
      },
      {
        configs: [
          createConfig('admin_password', 'admin'),
          createConfig('admin_principal', 'admin/admin'),
          createConfig('persist_credentials', 'false')
        ],
        credentialsExists: true,
        createCredentialFnCalled: false,
        updateCredentialFnCalled: true,
        e: [
          'testName',
          'kdc.admin.credential',
          {
            type: 'temporary',
            key: 'admin',
            principal: 'admin/admin'
          }
        ],
        message: 'Save Admin credentials checkbox unchecked, credentials already stored and should be updated as `temporary`'
      },
      {
        configs: [
          createConfig('admin_password', 'admin'),
          createConfig('admin_principal', 'admin/admin'),
          createConfig('persist_credentials', 'false')
        ],
        credentialsExists: false,
        createCredentialFnCalled: true,
        updateCredentialFnCalled: false,
        e: [
          'testName',
          'kdc.admin.credential',
          {
            type: 'temporary',
            key: 'admin',
            principal: 'admin/admin'
          }
        ],
        message: 'Save Admin credentials checkbox unchecked, credentials already stored and should be updated as `temporary`'
      }
    ].forEach(function(test) {
      describe(test.message, function() {
        beforeEach(function () {
          sinon.stub(credentialsUtils, 'getCredential', function() {
            return test.credentialsExists ? resolveWith() : rejectWith();
          });
          mixedObject.createKDCCredentials(test.configs);
        });

        afterEach(function () {
          credentialsUtils.getCredential.restore();
        });

        it('credentialsUtils#createCredentials called', function () {
          expect(credentialsUtils.createCredentials.calledOnce).to.equal(test.createCredentialFnCalled);
        });

        if (test.createCredentialFnCalled) {
          it('credentialsUtils#createCredentials called with correct arguments', function () {
            expect(credentialsUtils.createCredentials.args[0]).to.eql(test.e);
          });
        }
        it('credentialUtils#updateCredentials called', function () {
          expect(credentialsUtils.updateCredentials.calledOnce).to.equal(test.updateCredentialFnCalled);
        });

        if (test.updateCredentialFnCalled) {
          it('credentialUtils#updateCredentials called with correct arguments', function () {
            expect(credentialsUtils.updateCredentials.args[0]).to.eql(test.e);
          });
        }
      });
    });
  });

});
