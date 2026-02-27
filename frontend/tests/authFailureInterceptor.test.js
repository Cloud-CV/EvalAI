'use strict';

describe('Unit tests for authFailureInterceptor', function () {
    beforeEach(angular.mock.module('evalai'));

    var authFailureInterceptor, $q, $state, $rootScope, utilities, $httpBackend;

    beforeEach(inject(function (
        _authFailureInterceptor_,
        _$q_,
        _$state_,
        _$rootScope_,
        _utilities_,
        _$httpBackend_
    ) {
        authFailureInterceptor = _authFailureInterceptor_;
        $q = _$q_;
        $state = _$state_;
        $rootScope = _$rootScope_;
        utilities = _utilities_;
        $httpBackend = _$httpBackend_;

        $httpBackend.whenGET(/\.html/).respond('');
    }));

    afterEach(function () {
        $httpBackend.resetExpectations();
    });

    describe('responseError', function () {
        it('on 401 always clears auth state regardless of current route', function () {
            spyOn(utilities, 'resetStorage');
            spyOn($state, 'go');
            spyOn($rootScope, 'notify');

            $rootScope.isAuth = true;
            $state.current = { name: 'web.challenge-main.challenge-list', authenticate: undefined };

            var response = { status: 401, data: { detail: 'Invalid token' } };
            var rejected = authFailureInterceptor.responseError(response);
            rejected.catch(angular.noop);

            expect(utilities.resetStorage).toHaveBeenCalled();
            expect($rootScope.isAuth).toBe(false);
        });

        it('on 401 redirects to auth.login when current route requires authentication', function () {
            spyOn(utilities, 'resetStorage');
            spyOn($state, 'go');
            spyOn($rootScope, 'notify');

            $rootScope.isAuth = true;
            $state.current = { name: 'web.dashboard', authenticate: true };

            var response = { status: 401, data: { detail: 'Invalid token' } };
            var rejected = authFailureInterceptor.responseError(response);
            rejected.catch(angular.noop);

            expect(utilities.resetStorage).toHaveBeenCalled();
            expect($rootScope.isAuth).toBe(false);
            expect($state.go).toHaveBeenCalledWith('auth.login');
            expect($rootScope.notify).toHaveBeenCalledWith('error', 'Timeout, Please login again to continue!');
        });

        it('on 401 does NOT redirect when current route is public', function () {
            spyOn(utilities, 'resetStorage');
            spyOn($state, 'go');
            spyOn($rootScope, 'notify');

            $rootScope.isAuth = true;
            $state.current = { name: 'web.challenge-main.challenge-list', authenticate: undefined };

            var response = { status: 401, data: { detail: 'Invalid token' } };
            var rejected = authFailureInterceptor.responseError(response);
            rejected.catch(angular.noop);

            expect(utilities.resetStorage).toHaveBeenCalled();
            expect($rootScope.isAuth).toBe(false);
            expect($state.go).not.toHaveBeenCalled();
            expect($rootScope.notify).not.toHaveBeenCalled();
        });

        it('on 401 does NOT redirect when $state.current has authenticate set to false', function () {
            spyOn(utilities, 'resetStorage');
            spyOn($state, 'go');
            spyOn($rootScope, 'notify');

            $rootScope.isAuth = true;
            $state.current = { name: 'home', authenticate: false };

            var response = { status: 401 };
            var rejected = authFailureInterceptor.responseError(response);
            rejected.catch(angular.noop);

            expect(utilities.resetStorage).toHaveBeenCalled();
            expect($rootScope.isAuth).toBe(false);
            expect($state.go).not.toHaveBeenCalled();
            expect($rootScope.notify).not.toHaveBeenCalled();
        });

        it('on 401 returns a rejected promise with the response', function () {
            spyOn(utilities, 'resetStorage');
            spyOn($state, 'go');
            spyOn($rootScope, 'notify');

            var response = { status: 401 };
            var rejected = authFailureInterceptor.responseError(response);

            expect(rejected.then).toBeDefined();

            var result;
            rejected.then(
                function () { result = 'resolved'; },
                function (rej) { result = rej; }
            );
            $rootScope.$digest();
            $httpBackend.flush();

            expect(result).toBe(response);
            expect(result.status).toBe(401);
        });

        it('on non-401 does not call resetStorage, go, or notify', function () {
            spyOn(utilities, 'resetStorage');
            spyOn($state, 'go');
            spyOn($rootScope, 'notify');

            $rootScope.isAuth = true;

            var response = { status: 403 };
            var rejected = authFailureInterceptor.responseError(response);
            rejected.catch(angular.noop);

            expect(utilities.resetStorage).not.toHaveBeenCalled();
            expect($state.go).not.toHaveBeenCalled();
            expect($rootScope.notify).not.toHaveBeenCalled();
            expect($rootScope.isAuth).toBe(true);
        });

        it('on non-401 still returns a rejected promise with the response', function () {
            var response = { status: 500 };
            var rejected = authFailureInterceptor.responseError(response);

            var result;
            rejected.then(
                function () { result = 'resolved'; },
                function (rej) { result = rej; }
            );
            $rootScope.$digest();
            $httpBackend.flush();

            expect(result).toBe(response);
            expect(result.status).toBe(500);
        });
    });
});
