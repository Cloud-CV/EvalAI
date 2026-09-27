'use strict';

describe('ChallengeCtrl submission metadata editing', function() {
    beforeEach(angular.mock.module('evalai'));

    var $controller, $mdDialog, $rootScope, $scope, utilities, vm;

    beforeEach(inject(function(
        _$controller_,
        _$mdDialog_,
        _$rootScope_,
        _utilities_
    ) {
        $controller = _$controller_;
        $mdDialog = _$mdDialog_;
        $rootScope = _$rootScope_;
        utilities = _utilities_;

        spyOn(utilities, 'getData').and.returnValue(null);
        spyOn(utilities, 'sendRequest').and.callFake(function() {});
        spyOn($mdDialog, 'show');

        $scope = $rootScope.$new();
        vm = $controller('ChallengeCtrl', { $scope: $scope });
    }));

    it('loads phase metadata attributes when submission has no metadata', function() {
        var submissionId = 1;
        var phaseAttributes = [
            {
                name: 'TextAttribute',
                type: 'text',
                value: null,
                description: 'Sample'
            }
        ];
        vm.submissionResult = {
            count: 1,
            results: [
                {
                    id: submissionId,
                    challenge_phase: 2,
                    method_name: 'method name',
                    method_description: 'method description',
                    project_url: 'project url',
                    publication_url: 'publication url',
                    submission_metadata: null
                }
            ]
        };
        vm.submissionMetaAttributes = [
            {
                phaseId: 2,
                attributes: phaseAttributes
            }
        ];

        vm.showMdDialog(new Event('click'), submissionId);

        expect(vm.currentSubmissionMetaData).toEqual(phaseAttributes);
        expect(vm.currentSubmissionMetaData).not.toBe(phaseAttributes);
        expect($mdDialog.show).toHaveBeenCalled();
    });

    it('keeps saved submission metadata when present', function() {
        var submissionId = 1;
        var savedMetadata = [
            {
                name: 'TextAttribute',
                type: 'text',
                value: 'saved value',
                description: 'Sample'
            }
        ];
        vm.submissionResult = {
            count: 1,
            results: [
                {
                    id: submissionId,
                    challenge_phase: 2,
                    method_name: 'method name',
                    method_description: 'method description',
                    project_url: 'project url',
                    publication_url: 'publication url',
                    submission_metadata: savedMetadata
                }
            ]
        };
        vm.submissionMetaAttributes = [
            {
                phaseId: 2,
                attributes: [
                    {
                        name: 'TextAttribute',
                        type: 'text',
                        value: null,
                        description: 'Sample'
                    }
                ]
            }
        ];

        vm.showMdDialog(new Event('click'), submissionId);

        expect(vm.currentSubmissionMetaData).toEqual(savedMetadata);
        expect(vm.currentSubmissionMetaData).not.toBe(savedMetadata);
    });
});
