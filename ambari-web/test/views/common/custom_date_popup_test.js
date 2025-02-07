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

describe('CustomDatePopup', function() {
  var customDatePopup = require('views/common/custom_date_popup');

  describe('#showCustomDatePopup', function() {
    var context = Em.Object.create({
      cancel: sinon.spy(),
      actualValues: Em.Object.create()
    });
    var popup = customDatePopup.showCustomDatePopup(context);
    
    it('`onSecondary` should call `cancel` method in passed context', function() {
      popup.onSecondary();
      expect(context.cancel.calledOnce).to.ok;
    });

    describe('empty values passed for end and start dates, validation should fail with appropriate message', function () {
      it('onPrimary is false', function () {
        expect(popup.onPrimary()).to.false;
      });
      it('isStartDateError is true', function () {
        expect(customDatePopup.get('errors.isStartDateError')).to.ok;
      });
      it('isEndDateError is true', function () {
        expect(customDatePopup.get('errors.isEndDateError')).to.ok;
      });
      it('startDate invalid', function () {
        expect(customDatePopup.get('errorMessages.startDate')).to.equal(Em.I18n.t('jobs.customDateFilter.error.required'));
      });
      it('endDate invalid', function () {
        expect(customDatePopup.get('errorMessages.endDate')).to.equal(Em.I18n.t('jobs.customDateFilter.error.required'));
      });
    });

    describe('passed start date is greater then end data, validation should fail with apporpriate message', function () {
      beforeEach(function () {
        customDatePopup.set('customDateFormFields.startDate', '11/11/11');
        customDatePopup.set('customDateFormFields.endDate', '11/10/11');
      });

      it('onPrimary is false', function () {
        expect(popup.onPrimary()).to.false;
      });
      it('isStartDateError is false', function () {
        expect(customDatePopup.get('errors.isStartDateError')).to.false;
      });
      it('isEndDateError is true', function () {
        expect(customDatePopup.get('errors.isEndDateError')).to.ok;
      });
      it('endDate invalid', function () {
        expect(customDatePopup.get('errorMessages.endDate')).to.equal(Em.I18n.t('jobs.customDateFilter.error.date.order'));
      });
    });

    describe('valid values passed, `valueObject` should contain `endTime` and `startTime`', function () {

      beforeEach(function () {
        customDatePopup.set('customDateFormFields.startDate', '11/11/11');
        customDatePopup.set('customDateFormFields.endDate', '11/12/11');
        popup.onPrimary();
      });

      it('startTime is valid', function() {
        expect(context.get('actualValues.startTime')).to.equal(new Date('11/11/11 01:00 AM').getTime());
      });
      it('endTime is valid', function() {
        expect(context.get('actualValues.endTime')).to.equal(new Date('11/12/11 01:00 AM').getTime());
      });

    });

  });
});
