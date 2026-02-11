'use strict';

describe('Unit tests for authFailureInterceptor', function () {
    beforeEach(angular.mock.module('evalai'));

    var authFailureInterceptor, $q, $state, $rootScope, utilities;

    beforeEach(inject(function (
        _authFailureInterceptor_,
        _$q_,
        _$state_,
        _$rootScope_,
        _utilities_
    ) {
        authFailureInterceptor = _authFailureInterceptor_;
        $q = _$q_;
        $state = _$state_;
        $rootScope = _$rootScope_;
        utilities = _utilities_;
    }));

    describe('responseError', function () {
        it('on 401 calls resetStorage, sets isAuth false, redirects to auth.login, shows alert', function () {
            spyOn(utilities, 'resetStorage');
            spyOn($state, 'go');
            spyOn(window, 'alert');

            $rootScope.isAuth = true;

            var response = { status: 401, data: { detail: 'Invalid token' } };
            authFailureInterceptor.responseError(response);

            expect(utilities.resetStorage).toHaveBeenCalled();
            expect($rootScope.isAuth).toBe(false);
            expect($state.go).toHaveBeenCalledWith('auth.login');
            expect(window.alert).toHaveBeenCalledWith('Timeout, Please login again to continue!');
        });

        it('on 401 returns a rejected promise with the response', function (done) {
            spyOn(utilities, 'resetStorage');
            spyOn($state, 'go');
            spyOn(window, 'alert');

            var response = { status: 401 };
            var rejected = authFailureInterceptor.responseError(response);

            expect(rejected.then).toBeDefined();
            rejected.then(
                function () {
                    done.fail('Expected promise to be rejected');
                },
                function (rej) {
                    expect(rej).toBe(response);
                    expect(rej.status).toBe(401);
                    done();
                }
            );
        });

        it('on non-401 does not call resetStorage, go, or alert', function () {
            spyOn(utilities, 'resetStorage');
            spyOn($state, 'go');
            spyOn(window, 'alert');

            $rootScope.isAuth = true;

            var response = { status: 403 };
            authFailureInterceptor.responseError(response);

            expect(utilities.resetStorage).not.toHaveBeenCalled();
            expect($state.go).not.toHaveBeenCalled();
            expect(window.alert).not.toHaveBeenCalled();
            expect($rootScope.isAuth).toBe(true);
        });

        it('on non-401 still returns a rejected promise with the response', function (done) {
            var response = { status: 500 };
            var rejected = authFailureInterceptor.responseError(response);

            rejected.then(
                function () {
                    done.fail('Expected promise to be rejected');
                },
                function (rej) {
                    expect(rej).toBe(response);
                    expect(rej.status).toBe(500);
                    done();
                }
            );
        });
    });
});
