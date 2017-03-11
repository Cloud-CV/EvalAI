// define directives here
(function() {
    'use strict';
    // dynamic header directive
    angular
        .module('evalai')
        .directive('dynHeader', dynHeader);

    function dynHeader() {
        var directive = {
            link: link,
            templateUrl: 'dist/views/web/partials/dyn-header.html',
            transclude: true,
            restrict: 'EA'
        };
        return directive;

        function link(scope, element, attrs) {
            function headerComp() {
                /* jshint validthis: true */
                var self = this;
                this.init();
            }
            headerComp.prototype = {
                init: function() {
                    var self = this;
                    // initialized mobile sidebar
                    angular.element(".button-collapse").sideNav({
                        menuWidth: 200,
                        closeOnClick: true,
                        draggable: true
                    });
                }
            };
            var headerObj = new headerComp();
        }
    }
})();
// define directives here
(function() {
    'use strict';
    // dynamic header directive
    angular
        .module('evalai')
        .directive('mainHeader', dynHeader);

    function dynHeader($document) {
        var directive = {
            link: link,
            templateUrl: 'dist/views/web/partials/main-header.html',
            transclude: true,
            restrict: 'EA',
            controller: controller,
            controllerAs: 'header'
        };
        return directive;

        function controller($scope, $element, $attrs, $http, utilities, $window) {
            /* jshint validthis: true */
            var vm = this;

            vm.user = {};

            // get token
            var userKey = utilities.getData('userKey');

            if (userKey) {
                var parameters = {};
                parameters.url = 'auth/user/';
                parameters.method = 'GET';
                parameters.token = userKey;
                parameters.callback = {
                    onSuccess: function(response) {
                        var status = response.status;
                        var data = response.data;
                        if (status == 200) {
                            vm.user.name = data.username;
                        }
                    },
                    onError: function(response) {

                        var status = response.status;
                        var error = response.data;
                        if (status == 401) {
                            utilities.resetStorage();
                            $state.go("auth.login");
                            $rootScope.isAuth = false;
                        }
                    }
                };

                utilities.sendRequest(parameters);
            }
            vm.profileDropdown = function(ev) {
                angular.element(".dropdown-button").dropdown();

            };

        }

        function link(scope, element, attrs, $window) {
            function headerComp() {
                /* jshint validthis: true */
                var self = this;
                this.init();
            }
            headerComp.prototype = {
                init: function() {
                    var self = this;
                    // initialized mobile sidebar
                    angular.element(".button-collapse").sideNav({
                        menuWidth: 200,
                        closeOnClick: true,
                        draggable: true
                    });

                    // initialized shadow to main header
                    angular.element(window).bind('scroll', function() {

                        if (this.pageYOffset >= 10) {
                            angular.element(" nav").addClass('grad-shadow-1');
                        } else {
                            angular.element(" nav").removeClass('grad-shadow-1');
                        }
                        scope.$apply();
                    });
                }
            };
            var headerObj = new headerComp();
        }
    }
})();
//Landing Footer directive
(function() {
    'use strict';
    angular.module('evalai').directive('landingFooter', landingFooter);

    function landingFooter() {
        var directive = {
            templateUrl: 'dist/views/web/partials/footer.html',
            transclude: true,
            restrict: 'EA',
            controller: controller
        };
        return directive;

        function controller($scope, $element, $attrs, $http) {
            var githubRepoUrl = "https://api.github.com/repos/Cloud-CV/EvalAI";
            $http.get(githubRepoUrl).then(function(res) {
                $scope.githubStats = {
                    forksCount: res.data.forks_count,
                    starsCount: res.data.stargazers_count,
                    htmlUrl: res.data.html_url
                };
            });
        }
    }
})();
//Dashboard Footer directive
(function() {
    'use strict';
    // dynamic header directive
    angular.module('evalai').directive('dashboardFooter', dashboardFooter);

    function dashboardFooter() {
        var directive = {
            templateUrl: 'dist/views/web/partials/dashboard-footer.html',
            transclude: true,
            restrict: 'EA',
            controller: controller
        };
        return directive;

        function controller($scope, $element, $attrs, $http) {
            var githubRepoUrl = "https://api.github.com/repos/Cloud-CV/EvalAI";
            $http.get(githubRepoUrl).then(function(res) {
                $scope.githubStats = {
                    forksCount: res.data.forks_count,
                    starsCount: res.data.stargazers_count,
                    htmlUrl: res.data.html_url
                };
            });
        }
    }
})();
// loader directive
(function() {
    'use strict';
    angular.module('evalai').directive('evalLoader', evalLoader);

    function evalLoader() {
        var directive = {
            link: link,
            templateUrl: 'dist/views/web/partials/loader.html',
            transclude: true,
            restrict: 'EA'
        };
        return directive;

        function link(scope, element, attrs) {
            function evalLoader() {
                /* jshint validthis: true */
                var self = this;
                this.init();
            }
            evalLoader.prototype = {
                init: function() {}
            };
            var evalLoaderObj = new evalLoader();
        }
    }
})();
// simple loader directive
(function() {
    'use strict';
    angular.module('evalai').directive('simLoader', simLoader);

    function simLoader() {
        var directive = {
            link: link,
            templateUrl: 'dist/views/web/partials/sim-loader.html',
            transclude: true,
            restrict: 'EA'
        };
        return directive;

        function link(scope, element, attrs) {
            function loaderComp() {
                /* jshint validthis: true */
                var self = this;
                this.init();
            }
            loaderComp.prototype = {
                init: function() {
                    angular.element("#sim-loader").hide();
                }
            };
            var loaderCompObj = new loaderComp();
        }
    }
})();
//Sidebar in Dashboard      
(function() {
    'use strict';
    // dynamic header directive       
    angular.module('evalai').directive('sideBar', sideBar);

    function sideBar() {
        var directive = {
            link: function() {
                //do nothing      
            },
            templateUrl: 'dist/views/web/partials/sidebar.html',
            transclude: true,
            restrict: 'EA'
        };
        return directive;
    }
})();
//Dashboard header
(function() {
    'use strict';
    // dynamic header directive
    angular.module('evalai').directive('simHeader', simHeader);

    function simHeader() {
        var directive = {
            link: link,
            templateUrl: 'dist/views/web/partials/sim-header.html',
            transclude: true,
            restrict: 'EA'
        };
        return directive;

        function link(scope, element, attrs) {
            function headerComp() {
                /* jshint validthis: true */
                var self = this;
                this.init();
            }
            headerComp.prototype = {
                init: function() {
                    var self = this;
                    // initialized mobile sidebar
                    angular.element(".button-collapse").sideNav({
                        menuWidth: 200,
                        closeOnClick: true,
                        draggable: true
                    });
                }
            };
            var headerObj = new headerComp();
        }
    }
})();
// scroll directive
(function() {
    'use strict';
    // dynamic header directive
    angular.module('evalai').directive('scrollShadow', scrollShadow);

    function scrollShadow() {
        var directive = {
            link: link,
            // template : ' <div class="w-400 side-logo">EvalAI</div><div class="w-300 text-light-gray">{{web.name}} <i class="fa fa-caret-down"></i></div>',
            transclude: true,
            restrict: 'EA'
        };
        return directive;

        function link(scope, element, attrs) {
            function shadowComp() {
                /* jshint validthis: true */
                var self = this;
                this.init();
            }
            shadowComp.prototype = {
                init: function() {
                    var self = this;
                    // initialized mobile sidebar
                    angular.element(".links-section-outer").bind('scroll', function() {
                        if (this.scrollTop >= 5) {
                            angular.element(".side-intro").addClass('z-depth-3');
                        } else {
                            angular.element(".side-intro").removeClass('z-depth-3');
                        }
                        scope.$apply();
                    });
                }
            };
            var shadowCompObj = new shadowComp();
        }
    }
})();
// profile directive slider component
(function() {
    'use strict';
    // dynamic header directive
    angular.module('evalai').directive('slideProfile', slideProfile);

    function slideProfile() {
        var directive = {
            link: link,
            transclude: true,
            restrict: 'EA'
        };
        return directive;

        function link(scope, element, attrs) {
            function slideComp() {
                /* jshint validthis: true */
                var self = this;
                this.init();
            }
            slideComp.prototype = {
                init: function() {
                    /* jshint validthis: true */
                    var self = this;
                    // initialized mobile sidebar
                    angular.element(".profile-sidebar").animate({
                        'left': '219px'
                    }, 200);
                }
            };
            var slideCompObj = new slideComp();
        }
    }
})();
