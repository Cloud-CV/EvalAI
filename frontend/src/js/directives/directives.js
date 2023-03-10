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

        function link() {
            function headerComp() {
                this.init();
            }
            headerComp.prototype = {
                init: function() {
                    // initialized mobile sidebar
                    angular.element(".button-collapse").sideNav({
                        menuWidth: 200,
                        closeOnClick: true,
                        draggable: true
                    });
                }
            };
            new headerComp();
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

    function dynHeader() {
        var directive = {
            link: link,
            templateUrl: 'dist/views/web/partials/main-header.html',
            transclude: true,
            restrict: 'EA',
            controller: dynHeaderController,
            controllerAs: 'header',
            bindToController: true
        };
        return directive;

        function link(scope) {
            function headerComp() {
                this.init();
            }
            headerComp.prototype = {
                init: function() {
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
            new headerComp();
        }
    }
})();
dynHeaderController.$inject = ["utilities"];

function dynHeaderController(utilities) {
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
            onSuccess: function (response) {
                var status = response.status;
                var data = response.data;
                if (status == 200) {
                    vm.user.name = data.username;
                }
            },
            onError: function (response) {

                var status = response.status;
                if (status == 401) {
                    utilities.resetStorage();
                }
            }
        };

        utilities.sendRequest(parameters);
    }
    vm.profileDropdown = function () {
        angular.element(".dropdown-button").dropdown();

    };

}
//Landing Footer directive
(function() {
    'use strict';
    angular.module('evalai').directive('landingFooter', landingFooter);

    function landingFooter() {
        var directive = {
            templateUrl: 'dist/views/web/partials/footer.html',
            transclude: true,
            restrict: 'EA',
            controller: landingFooterController
        };
        return directive;
    }
})();
landingFooterController.$inject = ["$scope"];
function landingFooterController($scope) {
    $scope.year = new Date().getFullYear();
    var js = document.createElement("script");
    js.src = (/^http:/.test(document.location) ? "http" : "https") + "://buttons.github.io/buttons.js";
    document.getElementsByTagName("head")[0].appendChild(js);
}
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
            controller: dashboardFooterController
        };
        return directive;
    }
})();
dashboardFooterController.$inject = ["$scope"];
function dashboardFooterController($scope) {
    $scope.year = new Date().getFullYear();
    var js = document.createElement("script");
    js.src = (/^http:/.test(document.location) ? "http" : "https") + "://buttons.github.io/buttons.js";
    document.getElementsByTagName("head")[0].appendChild(js);
}
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

        function link() {
            function evalLoader() {
                this.init();
            }
            evalLoader.prototype = {
                init: function() {}
            };
            new evalLoader();
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

        function link() {
            function loaderComp() {
                this.init();
            }
            loaderComp.prototype = {
                init: function() {
                    angular.element("#sim-loader").hide();
                }
            };
            new loaderComp();
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

        function link() {
            function headerComp() {
                this.init();
            }
            headerComp.prototype = {
                init: function() {
                    // initialized mobile sidebar
                    angular.element(".button-collapse").sideNav({
                        menuWidth: 200,
                        closeOnClick: true,
                        draggable: true
                    });
                }
            };
            new headerComp();
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

        function link(scope) {
            function shadowComp() {
                this.init();
            }
            shadowComp.prototype = {
                init: function() {
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
            new shadowComp();
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

        function link() {
            function slideComp() {
                this.init();
            }
            slideComp.prototype = {
                init: function() {
                    // initialized mobile sidebar
                    angular.element(".profile-sidebar").animate({
                        'left': '219px'
                    }, 200);
                }
            };
            new slideComp();
        }
    }
})();
// Cookie Consent
(function() {
    angular.module('evalai')
  .directive('cookieConsent', function() {
    return {
      restrict: 'E',
      template: `
        <div class="cookie-consent" ng-show="!accepted">
          This website uses cookies to ensure you get the best experience on our website.
          <button class="btn ev-btn-dark waves-effect waves-dark grad-btn grad-btn-dark fs-14" ng-click="accept()" >Accept</button>
        </div>
      `,
      link: function(scope, element) {
        var acceptedCookieName = 'cookieConsentAccepted';

        // check if the user has already accepted the consent
        scope.accepted = document.cookie.includes(acceptedCookieName);

        // set a cookie when the user accepts the consent and hide it
        scope.accept = function() {
          var now = new Date();
          var expirationDate = new Date(now.getFullYear() + 1, now.getMonth(), now.getDate());
          document.cookie = `${acceptedCookieName}=true;expires=${expirationDate.toUTCString()}`;
          scope.accepted = true;
		  element.hide();
        };

        // position the consent message at the bottom of the screen and make it stick
        element.addClass('cookie-consent-wrapper');
      }
    };
  });
})();

